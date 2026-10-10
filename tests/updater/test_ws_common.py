import asyncio
from unittest.mock import patch

import pytest

from updater.ws_common import (_RECONNECT_DELAY_INITIAL, _RECONNECT_DELAY_MAX, _WsStats, _next_delay,
                               _should_force_reconnect, _watchdog)


# --- watchdog ---

def test_should_force_reconnect_silent_and_operating():
    assert _should_force_reconnect(0, [{"operating": True}]) is True


def test_should_force_reconnect_tolerates_overnight_silence():
    assert _should_force_reconnect(0, [{"operating": False}, {"operating": False}]) is False


def test_should_force_reconnect_not_when_messages_flow():
    assert _should_force_reconnect(12, [{"operating": True}]) is False


def test_should_force_reconnect_empty_parks():
    assert _should_force_reconnect(0, []) is False


def test_ws_stats_snapshot_resets_counter():
    stats = _WsStats()
    stats.note_message()
    stats.note_message()
    count, elapsed = stats.snapshot_and_reset()
    assert count == 2
    assert elapsed >= 0
    count2, _ = stats.snapshot_and_reset()
    assert count2 == 0


class _WatchdogFakeWS:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def test_watchdog_forces_reconnect_when_silent_while_operating():
    ws = _WatchdogFakeWS()

    async def instant_sleep(_delay):
        pass

    with patch("updater.ws_common.asyncio.sleep", instant_sleep):
        asyncio.run(_watchdog(ws, _WsStats(), [{"operating": True}]))
    assert ws.closed is True


def test_watchdog_does_not_reconnect_while_messages_flow():
    ws = _WatchdogFakeWS()
    stats = _WsStats()
    sleeps = []

    async def traffic_then_stop(_delay):
        sleeps.append(1)
        if len(sleeps) >= 3:
            raise asyncio.CancelledError
        stats.note_message()  # traffic arrives during each window

    with patch("updater.ws_common.asyncio.sleep", traffic_then_stop):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_watchdog(ws, stats, [{"operating": True}]))
    assert ws.closed is False


def test_watchdog_tolerates_silence_when_parks_closed():
    ws = _WatchdogFakeWS()
    sleeps = []

    async def two_windows(_delay):
        sleeps.append(1)
        if len(sleeps) >= 2:
            raise asyncio.CancelledError

    with patch("updater.ws_common.asyncio.sleep", two_windows):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_watchdog(ws, _WsStats(), [{"operating": False}]))
    assert ws.closed is False


# --- reconnect backoff ---

def test_next_delay_resets_after_stable_connection():
    assert _next_delay(40, 3600) == _RECONNECT_DELAY_INITIAL
    assert _next_delay(40, 60) == _RECONNECT_DELAY_INITIAL


def test_next_delay_doubles_after_quick_death():
    assert _next_delay(5, 2) == 10
    assert _next_delay(10, 2) == 20


def test_next_delay_doubles_when_never_connected():
    assert _next_delay(5, None) == 10


def test_next_delay_caps_at_max():
    assert _next_delay(40, 1) == _RECONNECT_DELAY_MAX
    assert _next_delay(_RECONNECT_DELAY_MAX, None) == _RECONNECT_DELAY_MAX
