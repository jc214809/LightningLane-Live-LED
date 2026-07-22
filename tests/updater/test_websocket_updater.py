import asyncio
import copy
from unittest.mock import patch

import pytest

from updater.websocket_updater import (
    _RECONNECT_DELAY_INITIAL,
    _RECONNECT_DELAY_MAX,
    _WS_HEARTBEAT_SECS,
    _WS_RECEIVE_TIMEOUT_SECS,
    _WsStats,
    _apply_live_update,
    _next_delay,
    _should_force_reconnect,
    _watchdog,
    _ws_loop,
)

DUMMY_ATTRACTION = {
    "id": "attr-1",
    "name": "Space Mountain",
    "waitTime": 20,
    "status": "OPERATING",
    "lastUpdatedTs": "old",
    "down_since": "",
}

DUMMY_PARKS = [{
    "id": "park-1",
    "name": "Magic Kingdom",
    "attractions": [copy.deepcopy(DUMMY_ATTRACTION)],
}]


def _parks_with_attr(attr_override=None):
    attr = copy.deepcopy(DUMMY_ATTRACTION)
    if attr_override:
        attr.update(attr_override)
    return [{"id": "park-1", "name": "Magic Kingdom", "attractions": [attr]}]


def _make_livedata_msg(entity_id="attr-1", entity_type="ATTRACTION", data=None):
    return {
        "event": "livedata",
        "entityId": entity_id,
        "entityType": entity_type,
        "data": data or {"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 30}}},
    }


# --- event filtering ---

def test_ignores_non_livedata_event():
    parks = _parks_with_attr()
    _apply_live_update({"event": "heartbeat"}, parks)
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "old"


def test_ignores_unknown_entity_type():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(entity_type="RESTAURANT")
    _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "old"


def test_accepts_show_entity_type():
    parks = [{"id": "park-1", "name": "MK", "attractions": [{
        "id": "show-1", "name": "Festival of Fantasy", "waitTime": None,
        "status": "OPERATING", "lastUpdatedTs": "old", "down_since": "",
    }]}]
    msg = {
        "event": "livedata",
        "entityId": "show-1",
        "entityType": "SHOW",
        "data": {"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 0}}},
    }
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["lastUpdatedTs"] != "old"


def test_subscribed_event_does_not_raise():
    parks = _parks_with_attr()
    _apply_live_update({"event": "subscribed", "entityId": "dest-1"}, parks)
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "old"


# --- operating status update gating ---

def test_operating_status_updated_on_status_change():
    parks = _parks_with_attr({"status": "DOWN"})
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 10}}})
    with patch("updater.websocket_updater.update_parks_operating_status") as mock_update:
        _apply_live_update(msg, parks)
    mock_update.assert_called_once_with([parks[0]], fetch_schedules=False)


def test_operating_status_not_updated_when_status_unchanged():
    parks = _parks_with_attr({"status": "OPERATING"})
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 99}}})
    with patch("updater.websocket_updater.update_parks_operating_status") as mock_update:
        _apply_live_update(msg, parks)
    mock_update.assert_not_called()


# --- OPERATING update ---

def test_operating_update_sets_wait_time_and_timestamp():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 45}}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    attr = parks[0]["attractions"][0]
    assert attr["waitTime"] == 45
    assert attr["status"] == "OPERATING"
    assert attr["down_since"] == ""
    assert attr["lastUpdatedTs"] != "old"


def test_timestamp_is_utc_iso_string():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 10}}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    ts = parks[0]["attractions"][0]["lastUpdatedTs"]
    assert ts.endswith("Z")
    assert "T" in ts


# --- DOWN status ---

def test_down_status_sets_down_since():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    attr = parks[0]["attractions"][0]
    assert attr["status"] == "DOWN"
    assert attr["down_since"] != ""


def test_down_status_preserves_existing_down_since():
    parks = _parks_with_attr({"status": "DOWN", "down_since": "2026-01-01T00:00:00Z"})
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["down_since"] == "2026-01-01T00:00:00Z"


def test_down_wait_time_uses_down_since_not_current_time():
    """down_since set 30 min ago — waitTime should reflect ~30 min, not 0."""
    from datetime import datetime, timezone, timedelta
    down_since = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    parks = _parks_with_attr({"status": "DOWN", "down_since": down_since})
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    wait = parks[0]["attractions"][0]["waitTime"]
    assert wait.startswith("Down ")
    minutes = int(wait.split(" ")[1])
    assert 28 <= minutes <= 32  # allow a couple seconds of drift


def test_down_wait_time_is_zero_on_first_down_message():
    """Ride just went down — down_since not set yet, so elapsed time should be ~0."""
    parks = _parks_with_attr({"status": "OPERATING", "down_since": ""})
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    wait = parks[0]["attractions"][0]["waitTime"]
    assert wait.startswith("Down ")
    minutes = int(wait.split(" ")[1])
    assert 0 <= minutes <= 1


# --- boarding group ---

def test_boarding_group_range():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={
        "status": "OPERATING",
        "queue": {"BOARDING_GROUP": {"currentGroupStart": 1, "currentGroupEnd": 50}},
    })
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == "Groups 1-50"


def test_boarding_group_open_ended():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={
        "status": "OPERATING",
        "queue": {"BOARDING_GROUP": {"currentGroupStart": 10, "currentGroupEnd": None}},
    })
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == "Group 10+"


def test_no_queue_data_sets_wait_none():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {}})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] is None


# --- thread safety ---

class _SpyLock:
    def __init__(self):
        self.acquisitions = 0

    def __enter__(self):
        self.acquisitions += 1
        return self

    def __exit__(self, *args):
        return False


def test_apply_live_update_holds_parks_data_lock():
    spy = _SpyLock()
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 30}}})
    with patch("updater.websocket_updater.parks_data_lock", spy), \
         patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert spy.acquisitions == 1


def test_apply_live_update_skips_lock_for_non_livedata_events():
    spy = _SpyLock()
    parks = _parks_with_attr()
    with patch("updater.websocket_updater.parks_data_lock", spy):
        _apply_live_update({"event": "heartbeat"}, parks)
    assert spy.acquisitions == 0


# --- event timestamps ---

def test_event_timestamp_used_when_present():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={
        "status": "OPERATING",
        "lastUpdated": "2026-07-19T18:00:00Z",
        "queue": {"STANDBY": {"waitTime": 10}},
    })
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "2026-07-19T18:00:00Z"


def test_down_since_uses_event_timestamp():
    """A DOWN event replayed after a reconnect carries the real outage start —
    the display should show 'Down 30', not 'Down 0'."""
    from datetime import datetime, timezone, timedelta
    went_down = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    parks = _parks_with_attr({"status": "OPERATING", "down_since": ""})
    msg = _make_livedata_msg(data={"status": "DOWN", "lastUpdated": went_down})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    attr = parks[0]["attractions"][0]
    assert attr["down_since"] == went_down
    minutes = int(attr["waitTime"].split(" ")[1])
    assert 28 <= minutes <= 32


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

    with patch("updater.websocket_updater.asyncio.sleep", instant_sleep):
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

    with patch("updater.websocket_updater.asyncio.sleep", traffic_then_stop):
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

    with patch("updater.websocket_updater.asyncio.sleep", two_windows):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_watchdog(ws, _WsStats(), [{"operating": False}]))
    assert ws.closed is False


def test_ws_loop_cancels_watchdog_on_disconnect():
    started = []
    cancelled = []
    real_sleep = asyncio.sleep

    async def parked_watchdog(ws, stats, parks):
        started.append(True)
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.append(True)
            raise

    captured = {}
    parks = [{"id": "park-1", "name": "MK", "destination_id": "dest-1", "attractions": []}]

    async def fake_sleep(delay):
        # The reconnect backoff sleep ends the test; zero-delay yields run for real
        # so the watchdog task gets scheduled before the receive loop finishes.
        if delay:
            raise asyncio.CancelledError
        await real_sleep(0)

    class _YieldingWS(_FakeWS):
        def __init__(self):
            self._yielded = False

        async def __anext__(self):
            if not self._yielded:
                self._yielded = True
                await real_sleep(0)  # let the watchdog task start
            raise StopAsyncIteration

    class _YieldingSession(_FakeSession):
        def ws_connect(self, url, **kwargs):
            return _YieldingWS()

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _YieldingSession(captured)), \
         patch("updater.websocket_updater._watchdog", parked_watchdog), \
         patch("updater.websocket_updater.asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("dummy-key", parks))

    assert started == [True]
    assert cancelled == [True]


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


# --- connection settings ---

class _FakeWS:
    """Minimal stand-in for aiohttp's ClientWebSocketResponse: connects,
    accepts subscriptions, yields no messages, then closes."""

    close_code = 1000

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    async def send_json(self, payload):
        pass

    def exception(self):
        return None


class _FakeSession:
    def __init__(self, captured):
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def ws_connect(self, url, **kwargs):
        self._captured.update(kwargs, url=url)
        return _FakeWS()


def test_ws_loop_connects_with_heartbeat_and_receive_timeout():
    captured = {}
    parks = [{"id": "park-1", "name": "MK", "destination_id": "dest-1", "attractions": []}]

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("dummy-key", parks))

    assert captured["heartbeat"] == _WS_HEARTBEAT_SECS
    assert captured["receive_timeout"] == _WS_RECEIVE_TIMEOUT_SECS


# --- no match ---

def test_unknown_entity_id_is_ignored():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(entity_id="unknown-id")
    _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == 20
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "old"
