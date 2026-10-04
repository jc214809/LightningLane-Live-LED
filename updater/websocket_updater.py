import asyncio
import json
import ssl
import time
import traceback
from datetime import datetime, timezone

import aiohttp
import certifi

from api.disney_api import (fetch_park_live_data, get_down_time, parse_forecast, parse_queue_wait,
                            parse_showtimes, update_parks_operating_status)
from updater.data_updater import merge_live_data
from updater.shared import note_network_result, parks_data_lock
from utils import debug

# The only address ThemeParks.wiki supports (ws. is a hosting hostname).
WS_URL = "wss://api.themeparks.wiki/v1/live"
# The frame shape _apply_live_update parses ({"event": ...}). No subprotocol gets it today, but the
# default is moving to "preview", and "legacy" stays selected after it does.
WS_SUBPROTOCOLS = ("legacy",)
# The entity types we display. A destination subscription takes one entityTypeFilter
# (a list or "A,B" is rejected), so each destination gets one subscription per type.
# Unfiltered, restaurants were two thirds of the messages. Each uses one of the
# key's 15 subscriptions (the welcome frame's subscriptionsLimit).
WS_ENTITY_TYPES = ("ATTRACTION", "SHOW")
_RECONNECT_DELAY_INITIAL = 5
_RECONNECT_DELAY_MAX = 60
_WS_HEARTBEAT_SECS = 30
_WS_RECEIVE_TIMEOUT_SECS = 120
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


def _apply_live_update(data, parks_data):
    """Apply a single WebSocket live-data event to the shared parks_data list."""
    event = data.get("event")
    debug.log(f"WS message: {data}")

    if event == "subscribed":
        debug.info(f"WebSocket subscribed to: {data.get('name') or data.get('entityId')}"
                   f" ({data.get('entityTypeFilter', 'all')})")
        return

    if event == "error":
        debug.warning(f"WebSocket server error: {data.get('message') or data}")
        return

    if event != "livedata":
        return

    entity_type = data.get("entityType")
    if entity_type not in ("ATTRACTION", "SHOW"):
        return

    entity_id = data.get("entityId")
    live = data.get("data") or {}
    status = live.get("status")
    # The feed sends no lastUpdated (REST does), so the receive time stamps the update:
    # it's seconds behind the change. down_since takes it from the first DOWN message.
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with parks_data_lock:
        for park in parks_data:
            for attr in park.get("attractions", []):
                if attr.get("id") != entity_id:
                    continue

                prev_status = attr.get("status")
                attr["status"] = status
                attr["lastUpdatedTs"] = last_updated
                attr["updateSource"] = "websocket"  # only "livedata" events get here
                if live.get("forecast"):
                    attr["forecast"] = parse_forecast(live["forecast"])
                if "showtimes" in live:
                    attr["showtimes"] = parse_showtimes(live["showtimes"])

                if status == "DOWN":
                    if not attr.get("down_since"):
                        attr["down_since"] = last_updated
                        debug.info(f"DOWN (WS): {attr['name']} ({park['name']}) — down_since set to {last_updated}")
                    down_time = get_down_time(attr["down_since"])
                    attr["waitTime"] = f"Down {down_time}" if down_time is not None else "Down"
                elif status in ("CLOSED", "REFURBISHMENT"):
                    attr["down_since"] = ""
                else:
                    attr["down_since"] = ""
                    attr["waitTime"] = parse_queue_wait(live.get("queue") or {})

                if prev_status != status:
                    debug.info(
                        f"WS update: {attr['name']} ({park['name']}) "
                        f"{prev_status} → {status}, wait={attr.get('waitTime')}"
                    )
                    # fetch_schedules=False: we're on the WS event loop — schedule
                    # fetching is blocking HTTP and is deferred to the REST thread.
                    update_parks_operating_status([park], fetch_schedules=False)
                return


def has_api_key(api_key):
    """True for a real ThemeParks key. The WebSocket needs one: without it the
    server accepts the handshake, then closes with 3000 "Authentication timeout"."""
    return isinstance(api_key, str) and bool(api_key.strip()) and not api_key.startswith("<")


def websocket_settings(config):
    """(use_websocket, api_key) from config.json's "websocket" section:
    {"enabled": true, "api_key": "..."}. Runs only when enabled with a real key.
    A config without the section falls back to the old top-level themeparks_api_key."""
    section = config.get("websocket")
    if section is None:
        api_key = config.get("themeparks_api_key")
        if has_api_key(api_key):
            debug.info('Using the top-level "themeparks_api_key"; move it to "websocket": {"api_key": ...} in config.json.')
        return has_api_key(api_key), api_key
    if not isinstance(section, dict):
        debug.warning('config.json "websocket" should be {"enabled": true, "api_key": "..."}; using REST polling only.')
        return False, None

    enabled = section.get("enabled", True)
    api_key = section.get("api_key")
    if not isinstance(enabled, bool):
        debug.warning(f'config.json "websocket.enabled" should be true or false, not {enabled!r}; using REST polling only.')
        return False, api_key
    if not enabled:
        return False, api_key
    if not has_api_key(api_key):
        debug.warning('config.json "websocket.enabled" is true but "websocket.api_key" is not set; using REST polling only.')
        return False, api_key
    return True, api_key


async def _ws_loop(api_key, parks_data):
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    delay = _RECONNECT_DELAY_INITIAL
    is_reconnect = False

    while True:
        connected_at = None
        try:
            headers = {"X-API-Key": api_key.strip()}
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    WS_URL,
                    protocols=WS_SUBPROTOCOLS,
                    headers=headers,
                    ssl=ssl_ctx,
                    heartbeat=_WS_HEARTBEAT_SECS,
                    # receive_timeout= is deprecated (aiohttp 3.14 warns); this is its replacement.
                    timeout=aiohttp.ClientWSTimeout(
                        ws_receive=_WS_RECEIVE_TIMEOUT_SECS, ws_close=_WS_CLOSE_TIMEOUT_SECS),
                ) as ws:
                    connected_at = time.monotonic()
                    if is_reconnect:
                        debug.info("WebSocket reconnected — refreshing live data via REST.")
                        for park in parks_data:
                            if park.get("attractions"):
                                new_live_data = await fetch_park_live_data(park)
                                if new_live_data is None:
                                    park["live_data_stale"] = True
                                    debug.warning(
                                        f"Live data refresh failed for {park.get('name')} after reconnect; "
                                        "keeping existing data."
                                    )
                                else:
                                    with parks_data_lock:
                                        park["live_data_stale"] = False
                                        merge_live_data(park["attractions"], new_live_data)
                        update_parks_operating_status(list(parks_data), fetch_schedules=False)
                        debug.info("REST refresh after reconnect complete.")
                    else:
                        debug.info("WebSocket connected to ThemeParks.wiki")
                    is_reconnect = True

                    destination_ids = list({
                        p["destination_id"] for p in parks_data
                        if p.get("destination_id")
                    })
                    if not destination_ids:
                        debug.warning("No destination IDs in parks_data; will retry")
                        break

                    for dest_id in destination_ids:
                        for entity_type in WS_ENTITY_TYPES:
                            await ws.send_json({
                                "event": "subscribe",
                                "entityId": dest_id,
                                "entityTypeFilter": entity_type,
                            })
                    debug.info(f"Subscribed to destinations: {destination_ids}")

                    stats = _WsStats()
                    watchdog = asyncio.create_task(_watchdog(ws, stats, parks_data))
                    try:
                        async for msg in ws:
                            stats.note_message()
                            note_network_result(True)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                debug.log(f"WS raw: {msg.data}")
                                try:
                                    _apply_live_update(json.loads(msg.data), parks_data)
                                except json.JSONDecodeError:
                                    debug.warning(f"Non-JSON WS message: {msg.data}")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                debug.warning(f"WebSocket error message: {ws.exception()}")
                                break
                    finally:
                        # Without this, every reconnect leaks a watchdog task
                        # holding a reference to a dead connection.
                        watchdog.cancel()

                    # aiohttp ends the async-for on close rather than yielding
                    # a CLOSED message; surface why the connection ended.
                    debug.warning(
                        f"WebSocket receive loop ended: close_code={ws.close_code}, "
                        f"exception={ws.exception()}"
                    )

        except Exception as e:
            debug.error(f"WebSocket error: {e}\n{traceback.format_exc()}")
            # A connect that fails at the socket level (DNS, refused, timeout — aiohttp's
            # connector errors are OSErrors) means no internet; a server rejection doesn't.
            if connected_at is None and isinstance(e, OSError):
                note_network_result(False)

        duration = (time.monotonic() - connected_at) if connected_at is not None else None
        delay = _next_delay(delay, duration)
        debug.info(f"WebSocket disconnected; reconnecting in {delay}s")
        await asyncio.sleep(delay)


def websocket_live_updater(api_key, parks_data):
    """
    Background thread entry point. Waits for parks_data to be populated, then
    maintains a persistent WebSocket connection for real-time attraction updates.
    Falls back gracefully if the connection cannot be established.
    """
    while not parks_data:
        time.sleep(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_ws_loop(api_key, parks_data))
    finally:
        loop.close()
