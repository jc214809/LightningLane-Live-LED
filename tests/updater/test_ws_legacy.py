import asyncio
import copy
from unittest.mock import patch

import pytest

from updater.ws_common import WS_ENTITY_TYPES, WS_URL, _WS_CLOSE_TIMEOUT_SECS
from updater.ws_legacy import (WS_SUBPROTOCOLS, _WS_HEARTBEAT_SECS, _WS_RECEIVE_TIMEOUT_SECS, _apply_live_update,
                               _ws_loop)
from tests.updater.ws_support import _FakeSession, _FakeWS, _RefusingSession


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
    with patch("updater.ws_legacy.update_parks_operating_status"):
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
    with patch("updater.ws_legacy.update_parks_operating_status") as mock_update:
        _apply_live_update(msg, parks)
    mock_update.assert_called_once_with([parks[0]], fetch_schedules=False)


def test_operating_status_not_updated_when_status_unchanged():
    parks = _parks_with_attr({"status": "OPERATING"})
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 99}}})
    with patch("updater.ws_legacy.update_parks_operating_status") as mock_update:
        _apply_live_update(msg, parks)
    mock_update.assert_not_called()


# --- OPERATING update ---

def test_operating_update_sets_wait_time_and_timestamp():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 45}}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    attr = parks[0]["attractions"][0]
    assert attr["waitTime"] == 45
    assert attr["status"] == "OPERATING"
    assert attr["down_since"] == ""
    assert attr["lastUpdatedTs"] != "old"


def test_timestamp_is_utc_iso_string():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 10}}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    ts = parks[0]["attractions"][0]["lastUpdatedTs"]
    assert ts.endswith("Z")
    assert "T" in ts


# --- DOWN status ---

def test_down_status_sets_down_since():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    attr = parks[0]["attractions"][0]
    assert attr["status"] == "DOWN"
    assert attr["down_since"] != ""


def test_down_status_preserves_existing_down_since():
    parks = _parks_with_attr({"status": "DOWN", "down_since": "2026-01-01T00:00:00Z"})
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["down_since"] == "2026-01-01T00:00:00Z"


def test_down_wait_time_uses_down_since_not_current_time():
    """down_since set 30 min ago — waitTime should reflect ~30 min, not 0."""
    from datetime import datetime, timezone, timedelta
    down_since = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    parks = _parks_with_attr({"status": "DOWN", "down_since": down_since})
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    wait = parks[0]["attractions"][0]["waitTime"]
    assert wait.startswith("Down ")
    minutes = int(wait.split(" ")[1])
    assert 28 <= minutes <= 32  # allow a couple seconds of drift


def test_down_wait_time_is_zero_on_first_down_message():
    """Ride just went down — down_since not set yet, so elapsed time should be ~0."""
    parks = _parks_with_attr({"status": "OPERATING", "down_since": ""})
    msg = _make_livedata_msg(data={"status": "DOWN", "queue": {"STANDBY": {"waitTime": None}}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
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
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == "Groups 1-50"


def test_boarding_group_open_ended():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={
        "status": "OPERATING",
        "queue": {"BOARDING_GROUP": {"currentGroupStart": 10, "currentGroupEnd": None}},
    })
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == "Group 10+"


def test_no_queue_data_sets_wait_none():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {}})
    with patch("updater.ws_legacy.update_parks_operating_status"):
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
    with patch("updater.ws_legacy.parks_data_lock", spy), \
         patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    assert spy.acquisitions == 1


def test_apply_live_update_skips_lock_for_non_livedata_events():
    spy = _SpyLock()
    parks = _parks_with_attr()
    with patch("updater.ws_legacy.parks_data_lock", spy):
        _apply_live_update({"event": "heartbeat"}, parks)
    assert spy.acquisitions == 0


# --- event timestamps ---

def test_receive_time_stamps_the_update():
    # The feed sends no lastUpdated, so the receive time is the update's timestamp.
    from datetime import datetime, timezone
    parks = _parks_with_attr()
    msg = _make_livedata_msg(data={"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 10}}})
    before = datetime.now(timezone.utc).replace(microsecond=0)
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(msg, parks)
    stamped = datetime.strptime(parks[0]["attractions"][0]["lastUpdatedTs"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    assert 0 <= (stamped - before).total_seconds() <= 2


def test_down_since_is_the_first_down_message_and_later_ones_keep_it():
    from datetime import datetime, timezone, timedelta
    went_down = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    parks = _parks_with_attr({"status": "OPERATING", "down_since": ""})
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update(_make_livedata_msg(data={"status": "DOWN"}), parks)
        attr = parks[0]["attractions"][0]
        assert attr["down_since"] == attr["lastUpdatedTs"]  # the first DOWN's receive time
        assert attr["waitTime"] == "Down 0"

        attr["down_since"] = went_down  # as if that first DOWN came 30 minutes ago
        _apply_live_update(_make_livedata_msg(data={"status": "DOWN"}), parks)
    assert attr["down_since"] == went_down
    assert 28 <= int(attr["waitTime"].split(" ")[1]) <= 32


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

    with patch("updater.ws_legacy.aiohttp.ClientSession", lambda: _YieldingSession(captured)), \
         patch("updater.ws_legacy._watchdog", parked_watchdog), \
         patch("updater.ws_legacy.asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("dummy-key", parks))

    assert started == [True]
    assert cancelled == [True]


def test_ws_loop_connects_with_heartbeat_and_receive_timeout():
    # The receive timeout goes through ClientWSTimeout (the float receive_timeout= is deprecated),
    # with the close timeout set too, since leaving it out would drop aiohttp's 10s default.
    captured = {}
    parks = [{"id": "park-1", "name": "MK", "destination_id": "dest-1", "attractions": []}]

    async def cancel_sleep(_delay):
        raise asyncio.CancelledError

    with patch("updater.ws_legacy.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.ws_legacy.asyncio.sleep", cancel_sleep):
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

    with patch("updater.ws_legacy.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.ws_legacy.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("real-key", parks))

    assert WS_ENTITY_TYPES == ("ATTRACTION", "SHOW")
    assert sorted((m["entityId"], m["entityTypeFilter"]) for m in captured["sent"]) == [
        ("cp", "ATTRACTION"), ("cp", "SHOW"), ("wdw", "ATTRACTION"), ("wdw", "SHOW")]
    assert all(m["event"] == "subscribe" for m in captured["sent"])


def test_server_error_frames_are_logged_as_warnings():
    parks = _parks_with_attr()
    with patch("updater.ws_legacy.debug.warning") as warning:
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

    with patch("updater.ws_legacy.aiohttp.ClientSession", lambda: _FakeSession(captured)), \
         patch("updater.ws_legacy.asyncio.sleep", cancel_sleep):
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

    with patch("updater.ws_legacy.aiohttp.ClientSession", session_factory), \
         patch("updater.ws_legacy.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_ws_loop("dummy-key", parks))


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
    with patch("updater.ws_legacy.update_parks_operating_status"):
        _apply_live_update({"event": "subscribed", "entityId": "attr-1"}, parks)
        assert parks[0]["attractions"][0]["updateSource"] == "rest"  # only livedata writes rides
        _apply_live_update(_make_livedata_msg(), parks)
    assert parks[0]["attractions"][0]["updateSource"] == "websocket"
