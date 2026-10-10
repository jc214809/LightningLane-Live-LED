import asyncio
import copy
import json
from unittest.mock import patch

import aiohttp
import pytest

from updater import shared
from updater.websocket_updater import (
    WS_PREVIEW_SUBPROTOCOLS,
    _PREVIEW_RECEIVE_TIMEOUT_SECS,
    _REFUSED_RETRY_SECS,
    _SUBSCRIBE_RETRY_SECS,
    _PreviewFeed,
    _preview_ws_loop,
    _RECONNECT_DELAY_INITIAL,
    _RECONNECT_DELAY_MAX,
    _WS_CLOSE_TIMEOUT_SECS,
    _WS_HEARTBEAT_SECS,
    _WS_RECEIVE_TIMEOUT_SECS,
    _WsStats,
    _apply_live_update,
    _next_delay,
    _should_force_reconnect,
    _watchdog,
    WS_SUBPROTOCOLS,
    WS_ENTITY_TYPES,
    WS_URL,
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

def test_receive_time_stamps_the_update():
    # The feed sends no lastUpdated, so the receive time is the update's timestamp.
    from datetime import datetime, timezone
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 10}}})
    before = datetime.now(timezone.utc).replace(microsecond=0)
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    stamped = datetime.strptime(parks[0]["attractions"][0]["lastUpdatedTs"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    assert 0 <= (stamped - before).total_seconds() <= 2


def test_down_since_is_the_first_down_message_and_later_ones_keep_it():
    from datetime import datetime, timezone, timedelta
    went_down = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    parks = _parks_with_attr({"status": "OPERATING", "down_since": ""})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update(_make_livedata_msg(data={"status": "DOWN"}), parks)
        attr = parks[0]["attractions"][0]
        assert attr["down_since"] == attr["lastUpdatedTs"]  # the first DOWN's receive time
        assert attr["waitTime"] == "Down 0"

        attr["down_since"] = went_down  # as if that first DOWN came 30 minutes ago
        _apply_live_update(_make_livedata_msg(data={"status": "DOWN"}), parks)
    assert attr["down_since"] == went_down
    assert 28 <= int(attr["waitTime"].split(" ")[1]) <= 32


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

    sent_frames = None  # ws_connect hands it the captured list

    async def send_json(self, payload):
        if self.sent_frames is not None:
            self.sent_frames.append(payload)

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
        ws = _FakeWS()
        ws.sent_frames = self._captured.setdefault("sent", [])
        return ws


def test_ws_loop_connects_with_heartbeat_and_receive_timeout():
    # The receive timeout goes through ClientWSTimeout (the float receive_timeout= is deprecated),
    # with the close timeout set too, since leaving it out would drop aiohttp's 10s default.
    captured = {}
    parks = [{"id": "park-1", "name": "MK", "destination_id": "dest-1", "attractions": []}]

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("dummy-key", parks))

    assert captured["heartbeat"] == _WS_HEARTBEAT_SECS
    assert "receive_timeout" not in captured
    assert captured["timeout"].ws_receive == _WS_RECEIVE_TIMEOUT_SECS
    assert captured["timeout"].ws_close == _WS_CLOSE_TIMEOUT_SECS == 10


def test_ws_loop_subscribes_each_destination_once_per_displayed_entity_type():
    # One filter per subscription (the server rejects a list), so restaurants never arrive.
    captured = {}
    parks = [{"id": "p1", "name": "MK", "destination_id": "wdw", "attractions": []},
             {"id": "p2", "name": "EPCOT", "destination_id": "wdw", "attractions": []},
             {"id": "p3", "name": "Cedar Point", "destination_id": "cp", "attractions": []}]

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("real-key", parks))

    assert WS_ENTITY_TYPES == ("ATTRACTION", "SHOW")
    assert sorted((m["entityId"], m["entityTypeFilter"]) for m in captured["sent"]) == [
        ("cp", "ATTRACTION"), ("cp", "SHOW"), ("wdw", "ATTRACTION"), ("wdw", "SHOW")]
    assert all(m["event"] == "subscribe" for m in captured["sent"])


def test_server_error_frames_are_logged_as_warnings():
    parks = _parks_with_attr()
    with patch("updater.websocket_updater.debug.warning") as warning:
        _apply_live_update({"event": "error", "message": "Invalid entityTypeFilter"}, parks)
    warning.assert_called_once()
    assert "Invalid entityTypeFilter" in warning.call_args[0][0]
    assert parks[0]["attractions"][0]["waitTime"] == 20


def test_ws_loop_uses_the_documented_url_legacy_subprotocol_and_key():
    # api.themeparks.wiki is the only supported host; "legacy" keeps the {"event": ...}
    # frames _apply_live_update parses after the server's default moves to "preview".
    captured = {}
    parks = [{"id": "park-1", "name": "MK", "destination_id": "dest-1", "attractions": []}]

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop(" real-key ", parks))

    assert captured["url"] == WS_URL == "wss://api.themeparks.wiki/v1/live"
    assert captured["protocols"] == WS_SUBPROTOCOLS == ("legacy",)
    assert captured["headers"] == {"X-API-Key": "real-key"}


# --- no match ---

def test_unknown_entity_id_is_ignored():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(entity_id="unknown-id")
    _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == 20
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "old"


def test_ws_update_stores_forecast_and_keeps_it_when_absent():
    parks = _parks_with_attr()
    raw = [{"time": "2026-09-25T10:00:00-04:00", "waitTime": 20, "percentage": 17}, {"bad": 1}]
    _apply_live_update(_make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 30}},
                                                "forecast": raw}), parks)
    attr = parks[0]["attractions"][0]
    assert attr["forecast"] == [{"time": "2026-09-25T10:00:00-04:00", "waitTime": 20}]
    _apply_live_update(_make_livedata_msg(), parks)
    assert attr["forecast"] == [{"time": "2026-09-25T10:00:00-04:00", "waitTime": 20}]


def test_ws_update_stores_showtimes_and_keeps_them_when_absent():
    from datetime import datetime, timezone
    parks = _parks_with_attr()
    raw = [{"type": "Performance Time", "startTime": "2026-09-26T21:30:00-04:00"}, {"startTime": "bad"}]
    _apply_live_update(_make_livedata_msg(data={"status": "OPERATING", "showtimes": raw}), parks)
    attr = parks[0]["attractions"][0]
    assert attr["showtimes"] == [datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc)]
    _apply_live_update(_make_livedata_msg(), parks)
    assert attr["showtimes"] == [datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc)]

# --- network badge flag ---

def _run_ws_loop_once(session_factory):
    parks = [{"id": "park-1", "name": "MK", "destination_id": "dest-1", "attractions": []}]

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", session_factory), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("dummy-key", parks))


class _RefusingSession(_FakeSession):
    def __init__(self, error):
        super().__init__({})
        self._error = error

    def ws_connect(self, url, **kwargs):
        raise self._error


def test_ws_connect_failing_at_the_socket_level_flags_a_network_issue():
    from updater.shared import network_issues
    # aiohttp's ClientConnectorError (DNS failure, refused, unreachable) is an OSError.
    _run_ws_loop_once(lambda: _RefusingSession(OSError("Temporary failure in name resolution")))
    assert network_issues() is True


def test_ws_server_rejection_is_not_a_network_issue():
    from updater.shared import network_issues
    _run_ws_loop_once(lambda: _RefusingSession(RuntimeError("handshake rejected: 429")))
    assert network_issues() is False


def test_ws_message_arriving_clears_the_network_issue():
    from updater.shared import network_issues, note_network_result
    note_network_result(False)

    class _OneMessageWS(_FakeWS):
        sent = False

        async def __anext__(self):
            if self.sent:
                raise StopAsyncIteration
            self.sent = True
            return type("Msg", (), {"type": None, "data": ""})()

    class _OneMessageSession(_FakeSession):
        def ws_connect(self, url, **kwargs):
            return _OneMessageWS()

    _run_ws_loop_once(lambda: _OneMessageSession({}))
    assert network_issues() is False


def test_livedata_marks_the_ride_as_last_written_by_the_websocket():
    parks = _parks_with_attr({"updateSource": "rest"})
    with patch("updater.websocket_updater.update_parks_operating_status"):
        _apply_live_update({"event": "subscribed", "entityId": "attr-1"}, parks)
        assert parks[0]["attractions"][0]["updateSource"] == "rest"  # only livedata writes rides
        _apply_live_update(_make_livedata_msg(), parks)
    assert parks[0]["attractions"][0]["updateSource"] == "websocket"


# --- preview protocol ---


def _preview_parks():
    return [{"id": "mk", "name": "Magic Kingdom", "destination_id": "wdw", "operating": True,
             "attractions": [{"id": "attr-1", "name": "Space Mountain", "status": "OPERATING", "waitTime": 20,
                              "lastUpdatedTs": "2026-10-04T16:00:00Z", "down_since": "", "updateSource": "rest"}]}]


def _entry(status="OPERATING", wait=45, last_updated="2026-10-04T16:10:00Z", entity_id="attr-1", park_id="mk"):
    entry = {"id": entity_id, "parkId": park_id, "entityType": "ATTRACTION", "name": "Space Mountain",
             "status": status, "lastUpdated": last_updated}
    if wait is not None:
        entry["queue"] = {"STANDBY": {"waitTime": wait}}
    return entry


@pytest.fixture
def no_status_check():
    with patch("updater.websocket_updater.update_parks_operating_status") as check:
        yield check


def test_preview_welcome_subscribes_each_destination_per_entity_type_with_a_snapshot():
    feed = _PreviewFeed(_preview_parks())
    replies = feed.handle({"type": "welcome", "data": {"limits": {"maxConnections": 2, "maxSubscriptions": 15}}})
    assert [delay for delay, _ in replies] == [0, 0]
    assert [frame for _, frame in replies] == [
        {"type": "subscribe", "channel": "wdw", "filter": "ATTRACTION", "snapshot": True, "since": None,
         "reqId": "wdw:ATTRACTION"},
        {"type": "subscribe", "channel": "wdw", "filter": "SHOW", "snapshot": True, "since": None,
         "reqId": "wdw:SHOW"},
    ]


def test_preview_reconnect_resumes_from_the_saved_cursor():
    feed = _PreviewFeed(_preview_parks())
    feed.cursor = "c-41"
    replies = feed.handle({"type": "welcome", "data": {}})
    assert {frame["since"] for _, frame in replies} == {"c-41"}


def test_preview_falls_back_to_one_unfiltered_subscription_when_the_key_allows_too_few():
    feed = _PreviewFeed(_preview_parks())
    replies = feed.handle({"type": "welcome", "data": {"limits": {"maxSubscriptions": 1}}})
    assert [(f["channel"], f["filter"]) for _, f in replies] == [("wdw", None)]


def test_preview_snapshot_applies_rest_shaped_entries_and_syncs_the_feed():
    parks = _preview_parks()
    feed = _PreviewFeed(parks)
    with patch("updater.websocket_updater.update_parks_operating_status") as check:
        feed.handle({"type": "snapshot", "cursor": "c-1", "final": True, "data": [_entry()]})
    attr = parks[0]["attractions"][0]
    assert attr["waitTime"] == 45
    assert attr["lastUpdatedTs"] == "2026-10-04T16:10:00Z"  # the ride's real change time
    assert attr["updateSource"] == "websocket"
    check.assert_called_once_with([parks[0]], fetch_schedules=False)
    assert shared._live_feed_synced.is_set()
    assert feed.cursor == "c-1"


def test_preview_snapshot_chunk_before_the_final_one_does_not_sync(no_status_check):
    feed = _PreviewFeed(_preview_parks())
    feed.handle({"type": "snapshot", "cursor": "c-1", "final": False, "total": 900, "data": [_entry()]})
    assert not shared._live_feed_synced.is_set()


def test_preview_update_uses_the_rides_real_change_time_for_down_since(no_status_check):
    parks = _preview_parks()
    feed = _PreviewFeed(parks)
    feed.handle({"type": "update", "cursor": "c-2", "data": _entry("DOWN", None, "2026-10-04T16:20:00Z")})
    attr = parks[0]["attractions"][0]
    assert attr["status"] == "DOWN"
    assert attr["down_since"] == "2026-10-04T16:20:00Z"
    no_status_check.assert_called_once_with([parks[0]], fetch_schedules=False)


def test_preview_update_without_a_status_change_skips_the_operating_check(no_status_check):
    feed = _PreviewFeed(_preview_parks())
    feed.handle({"type": "update", "data": _entry("OPERATING", 50)})
    no_status_check.assert_not_called()


def test_preview_replayed_older_update_does_not_overwrite_newer_data(no_status_check):
    parks = _preview_parks()
    feed = _PreviewFeed(parks)
    feed.handle({"type": "update", "data": _entry(wait=60, last_updated="2026-10-04T16:30:00Z")})
    feed.handle({"type": "update", "data": _entry(wait=45, last_updated="2026-10-04T16:10:00Z")})
    assert parks[0]["attractions"][0]["waitTime"] == 60


def test_preview_update_for_an_unknown_ride_or_park_is_ignored(no_status_check):
    parks = _preview_parks()
    feed = _PreviewFeed(parks)
    feed.handle({"type": "update", "data": _entry(entity_id="restaurant-9")})
    feed.handle({"type": "update", "data": _entry(park_id="epcot")})
    assert parks[0]["attractions"][0]["waitTime"] == 20


@pytest.mark.parametrize("frame", [
    {"type": "update", "data": "not a dict"},
    {"type": "snapshot", "data": {"not": "a list"}},
    {"type": "snapshot", "data": ["junk", None]},
    {"type": "unsubscribed", "data": {}},
    {"type": "something-new", "cursor": "c-9"},
    {},
])
def test_preview_malformed_or_unknown_frames_are_ignored(frame, no_status_check):
    parks = _preview_parks()
    feed = _PreviewFeed(parks)
    assert feed.handle(frame) == []
    assert parks[0]["attractions"][0]["waitTime"] == 20
    assert feed.cursor is None


@pytest.mark.parametrize("kind", ["snapshot", "update", "resumed", "ping"])
def test_preview_cursor_is_saved_from_applied_frames(kind, no_status_check):
    feed = _PreviewFeed(_preview_parks())
    data = [_entry()] if kind == "snapshot" else _entry() if kind == "update" else {}
    feed.handle({"type": kind, "cursor": "c-7", "data": data})
    assert feed.cursor == "c-7"


@pytest.mark.parametrize("kind", ["subscribed", "error", "welcome"])
def test_preview_cursor_is_not_taken_from_other_frames(kind):
    feed = _PreviewFeed(_preview_parks())
    feed.handle({"type": kind, "cursor": "c-7", "data": {}})
    assert feed.cursor is None


def test_preview_ping_is_answered_with_a_pong_and_does_not_count_as_an_update(no_status_check):
    feed = _PreviewFeed(_preview_parks())
    assert feed.handle({"type": "ping", "cursor": "c-3"}) == [(0, {"type": "pong"})]
    assert feed.stats.msg_count == 0
    feed.handle({"type": "update", "data": _entry()})
    assert feed.stats.msg_count == 1


def test_preview_resumed_syncs_the_feed():
    feed = _PreviewFeed(_preview_parks())
    feed.handle({"type": "resumed", "cursor": "c-5"})
    assert shared._live_feed_synced.is_set()


def _subscribed_feed():
    feed = _PreviewFeed(_preview_parks())
    feed.cursor = "c-10"
    feed.handle({"type": "welcome", "data": {}})
    return feed


def test_preview_retryable_refusal_resends_the_same_subscribe_with_growing_waits():
    feed = _subscribed_feed()
    error = {"type": "error", "data": {"code": 4290, "message": "busy", "retryable": True, "reqId": "wdw:SHOW"}}
    delays = []
    for _ in range(len(_SUBSCRIBE_RETRY_SECS)):
        [(delay, frame)] = feed.handle(error)
        delays.append(delay)
        assert frame == feed.frames["wdw:SHOW"]
    assert delays == list(_SUBSCRIBE_RETRY_SECS)
    assert feed.handle(error) == []  # gives up until the next reconnect


def test_preview_retryable_refusal_after_the_ack_is_not_resent():
    feed = _subscribed_feed()
    feed.handle({"type": "subscribed", "data": {"reqId": "wdw:SHOW", "subscriptionId": "s-1"}})
    assert feed.handle({"type": "error", "data": {"retryable": True, "reqId": "wdw:SHOW"}}) == []


def test_preview_refusal_that_is_not_retryable_is_only_logged():
    feed = _subscribed_feed()
    with patch("updater.websocket_updater.debug.warning") as warning:
        assert feed.handle({"type": "error", "data": {"message": "Invalid filter", "retryable": False,
                                                      "reqId": "wdw:SHOW"}}) == []
    assert "Invalid filter" in warning.call_args[0][0]


def test_preview_resume_incomplete_starts_that_channel_over_with_a_snapshot():
    feed = _subscribed_feed()
    [(delay, frame)] = feed.handle({"type": "error", "data": {"message": "Resume incomplete", "retryable": False,
                                                              "reqId": "wdw:ATTRACTION"}})
    assert delay == 0
    assert frame["since"] is None and frame["snapshot"] is True and frame["filter"] == "ATTRACTION"
    assert feed.cursor is None


def test_preview_error_for_an_unknown_request_is_only_logged():
    feed = _subscribed_feed()
    assert feed.handle({"type": "error", "data": "oops"}) == []


# --- preview connection loop ---

def _text(frame):
    return aiohttp.WSMessage(aiohttp.WSMsgType.TEXT, json.dumps(frame), None)


class _ScriptedWS(_FakeWS):
    """Yields the given frames, then ends with close_code (the server's close)."""

    closed = False

    def __init__(self, frames, close_code=1000, sent=None):
        self._frames = list(frames)
        self.close_code = close_code
        self.sent_frames = sent

    async def __anext__(self):
        if not self._frames:
            raise StopAsyncIteration
        return _text(self._frames.pop(0))


class _ScriptedSession(_FakeSession):
    def __init__(self, captured, connections):
        super().__init__(captured)
        self._connections = connections

    def ws_connect(self, url, **kwargs):
        self._captured.setdefault("connects", []).append(dict(kwargs, url=url))
        frames, close_code = self._connections.pop(0)
        return _ScriptedWS(frames, close_code, self._captured.setdefault("sent", []))


def _run_preview(connections, parks=None, sleeps_allowed=0):
    """Run _preview_ws_loop over scripted connections; returns (captured, sleep delays)."""
    captured, delays = {}, []
    parks = parks if parks is not None else _preview_parks()

    async def fake_sleep(delay):
        delays.append(delay)
        if len(delays) > sleeps_allowed:
            raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _ScriptedSession(captured, connections)), \
         patch("updater.websocket_updater.asyncio.sleep", fake_sleep), \
         patch("updater.websocket_updater.update_parks_operating_status"):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop(" real-key ", parks))
    return captured, delays


WELCOME = {"type": "welcome", "data": {"limits": {"maxConnections": 2, "maxSubscriptions": 15}}}


def test_preview_loop_connects_with_the_preview_subprotocol_and_a_90s_silence_timeout():
    captured, _ = _run_preview([([WELCOME], 1000)])
    connect = captured["connects"][0]
    assert connect["url"] == WS_URL
    assert connect["protocols"] == WS_PREVIEW_SUBPROTOCOLS == ("preview",)
    assert connect["headers"] == {"X-API-Key": "real-key"}
    assert connect["timeout"].ws_receive == _PREVIEW_RECEIVE_TIMEOUT_SECS == 90
    assert connect["timeout"].ws_close == 10


def test_preview_loop_subscribes_after_the_welcome_and_answers_pings():
    captured, _ = _run_preview([([WELCOME, {"type": "ping", "cursor": "c-1"}], 1000)])
    assert [f["type"] for f in captured["sent"]] == ["subscribe", "subscribe", "pong"]


def test_preview_loop_resumes_from_the_last_cursor_after_a_drop():
    parks = _preview_parks()
    first = [WELCOME, {"type": "snapshot", "cursor": "c-1", "final": True, "data": [_entry()]},
             {"type": "update", "cursor": "c-2", "data": _entry(wait=50, last_updated="2026-10-04T16:15:00Z")}]
    second = [WELCOME, {"type": "update", "cursor": "c-3", "data": _entry(wait=55, last_updated="2026-10-04T16:16:00Z")},
              {"type": "resumed", "cursor": "c-3"}]
    captured, _ = _run_preview([(first, 1006), (second, 1000)], parks, sleeps_allowed=1)
    subscribes = [f for f in captured["sent"] if f["type"] == "subscribe"]
    assert [f["since"] for f in subscribes] == [None, None, "c-2", "c-2"]
    assert parks[0]["attractions"][0]["waitTime"] == 55  # the missed update was replayed


def test_preview_loop_marks_the_feed_down_when_the_connection_ends():
    _run_preview([([WELCOME, {"type": "resumed", "cursor": "c-1"}], 1000)])
    assert not shared._live_feed_synced.is_set()


def test_preview_loop_waits_ten_minutes_when_the_connection_cap_is_reached():
    with patch("updater.websocket_updater.random.uniform", lambda a, b: 1.0):
        _, delays = _run_preview([([], 4029)])
    assert delays == [_REFUSED_RETRY_SECS] == [600]


def test_preview_loop_backs_off_with_jitter_after_a_quick_drop():
    with patch("updater.websocket_updater.random.uniform", lambda a, b: 1.25):
        _, delays = _run_preview([([WELCOME], 1006)])
    assert delays == [_RECONNECT_DELAY_INITIAL * 2 * 1.25]


def test_preview_loop_treats_silence_as_a_dead_connection():
    class _SilentWS(_ScriptedWS):
        async def __anext__(self):
            raise asyncio.TimeoutError

    class _SilentSession(_ScriptedSession):
        def ws_connect(self, url, **kwargs):
            return _SilentWS([], 1006, [])

    async def fake_sleep(delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _SilentSession({}, [])), \
         patch("updater.websocket_updater.asyncio.sleep", fake_sleep), \
         patch("updater.websocket_updater.debug.warning") as warning:
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop("real-key", _preview_parks()))
    assert any("silent for 90s" in call.args[0] for call in warning.call_args_list)


def test_preview_loop_resends_a_retryable_refusal_after_its_wait():
    refusal = {"type": "error", "data": {"retryable": True, "reqId": "wdw:SHOW", "message": "busy"}}
    captured, delays = {}, []
    real_sleep = asyncio.sleep

    async def fake_sleep(delay):
        delays.append(delay)
        if delay == _SUBSCRIBE_RETRY_SECS[0]:
            return  # the retry's wait: let it send
        raise asyncio.CancelledError  # the reconnect backoff ends the test

    class _HoldingWS(_ScriptedWS):
        async def __anext__(self):
            if not self._frames:
                await real_sleep(0)  # let the retry task run before the connection ends
                await real_sleep(0)
                raise StopAsyncIteration
            return _text(self._frames.pop(0))

    class _HoldingSession(_ScriptedSession):
        def ws_connect(self, url, **kwargs):
            frames, close_code = self._connections.pop(0)
            return _HoldingWS(frames, close_code, self._captured.setdefault("sent", []))

    with patch("updater.websocket_updater.aiohttp.ClientSession",
               lambda: _HoldingSession(captured, [([WELCOME, refusal], 1000)])), \
         patch("updater.websocket_updater.asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop("real-key", _preview_parks()))
    assert [f["reqId"] for f in captured["sent"]] == ["wdw:ATTRACTION", "wdw:SHOW", "wdw:SHOW"]
    assert _SUBSCRIBE_RETRY_SECS[0] in delays  # the watchdog sleeps too


def test_preview_loop_skips_messages_that_are_not_json_objects():
    parks = _preview_parks()

    class _JunkWS(_ScriptedWS):
        async def __anext__(self):
            if not self._frames:
                raise StopAsyncIteration
            raw = self._frames.pop(0)
            return aiohttp.WSMessage(aiohttp.WSMsgType.TEXT, raw, None)

    class _JunkSession(_ScriptedSession):
        def ws_connect(self, url, **kwargs):
            frames, close_code = self._connections.pop(0)
            return _JunkWS(frames, close_code, self._captured.setdefault("sent", []))

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    update = json.dumps({"type": "update", "data": _entry(wait=50)})
    with patch("updater.websocket_updater.aiohttp.ClientSession",
               lambda: _JunkSession({}, [(["not json", "[1, 2]", update], 1000)])), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep), \
         patch("updater.websocket_updater.update_parks_operating_status"):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop("real-key", parks))
    assert parks[0]["attractions"][0]["waitTime"] == 50  # the good frame after the junk still applied


def test_preview_loop_stops_reading_on_an_error_message():
    class _ErrorWS(_ScriptedWS):
        async def __anext__(self):
            return aiohttp.WSMessage(aiohttp.WSMsgType.ERROR, None, None)

    class _ErrorSession(_ScriptedSession):
        def ws_connect(self, url, **kwargs):
            return _ErrorWS([], 1006, [])

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _ErrorSession({}, [])), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep), \
         patch("updater.websocket_updater.debug.warning") as warning:
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop("real-key", _preview_parks()))
    assert any("WebSocket error message" in call.args[0] for call in warning.call_args_list)


@pytest.mark.parametrize("error, network_issue", [
    (OSError("Temporary failure in name resolution"), True),  # no internet: the badge
    (RuntimeError("handshake rejected"), False),              # the server said no: not the network
])
def test_preview_loop_connect_failure_flags_the_network_only_at_the_socket_level(error, network_issue):
    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.websocket_updater.aiohttp.ClientSession", lambda: _RefusingSession(error)), \
         patch("updater.websocket_updater.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop("real-key", _preview_parks()))
    assert shared.network_issues() is network_issue


def test_preview_welcome_without_destinations_subscribes_to_nothing():
    feed = _PreviewFeed([{"id": "mk", "name": "MK", "attractions": []}])
    with patch("updater.websocket_updater.debug.warning") as warning:
        assert feed.handle(WELCOME) == []
    assert "No destination IDs" in warning.call_args[0][0]


@pytest.mark.parametrize("protocol, loop_name", [("preview", "_preview_ws_loop"), ("legacy", "_ws_loop")])
def test_websocket_live_updater_runs_the_configured_protocol(protocol, loop_name):
    from updater import websocket_updater
    ran = []

    async def fake_loop(api_key, parks):
        ran.append((loop_name, api_key))

    with patch.object(websocket_updater, loop_name, fake_loop):
        websocket_updater.websocket_live_updater("real-key", [{"id": "mk"}], protocol)
    assert ran == [(loop_name, "real-key")]
