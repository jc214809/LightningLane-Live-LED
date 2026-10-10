"""
What both WebSocket protocols share: the address, the entity types we subscribe to, the
reconnect backoff and the watchdog that reconnects a connection that's up but silent.
The loops are in ws_legacy.py and ws_preview.py; websocket_updater.py picks one.
"""
import asyncio
import time

from utils import debug

# The only address ThemeParks.wiki supports (ws. is a hosting hostname).
WS_URL = "wss://api.themeparks.wiki/v1/live"
# The entity types we display. A destination subscription takes one entityTypeFilter
# (a list or "A,B" is rejected), so each destination gets one subscription per type.
# Unfiltered, restaurants were two thirds of the messages. Each uses one of the
# key's 15 subscriptions (the welcome frame's subscriptionsLimit).
WS_ENTITY_TYPES = ("ATTRACTION", "SHOW")
_RECONNECT_DELAY_INITIAL = 5
_RECONNECT_DELAY_MAX = 60
_WS_CLOSE_TIMEOUT_SECS = 10  # aiohttp's own default, which a ClientWSTimeout given only ws_receive drops
_STABLE_CONNECTION_SECS = 60


def _next_delay(current_delay, connection_duration):
    """Reset backoff only after a stable connection; otherwise keep doubling so a
    connect-then-immediately-die loop can't hammer the server every 5s."""
    if connection_duration is not None and connection_duration >= _STABLE_CONNECTION_SECS:
        return _RECONNECT_DELAY_INITIAL
    return min(max(current_delay, _RECONNECT_DELAY_INITIAL) * 2, _RECONNECT_DELAY_MAX)

_WATCHDOG_INTERVAL_SECS = 300


class _WsStats:
    """Per-connection message counter for the watchdog's health window."""

    def __init__(self):
        self.msg_count = 0
        self.window_started = time.monotonic()

    def note_message(self):
        self.msg_count += 1

    def snapshot_and_reset(self):
        elapsed = time.monotonic() - self.window_started
        count = self.msg_count
        self.msg_count = 0
        self.window_started = time.monotonic()
        return count, elapsed


def _should_force_reconnect(msg_count, parks_data):
    """Silence is only suspicious while something is open and should be streaming."""
    if msg_count > 0:
        return False
    return any(p.get("operating") for p in parks_data)


async def _watchdog(ws, stats, parks_data):
    """Log a periodic health summary and force a reconnect if the connection is
    alive at the protocol level but no data flows while parks are operating."""
    while True:
        await asyncio.sleep(_WATCHDOG_INTERVAL_SECS)
        count, elapsed = stats.snapshot_and_reset()
        debug.info(f"WS heartbeat: {count} messages received in last {int(elapsed)}s")
        if _should_force_reconnect(count, parks_data):
            debug.warning("WS watchdog: no messages while parks operating — forcing reconnect.")
            await ws.close()
            return
