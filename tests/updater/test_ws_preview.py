import asyncio
import json
from unittest.mock import patch

import aiohttp
import pytest

from updater import shared
from updater.ws_common import WS_URL, _RECONNECT_DELAY_INITIAL
from updater.ws_preview import (WS_PREVIEW_SUBPROTOCOLS, _PREVIEW_RECEIVE_TIMEOUT_SECS, _REFUSED_RETRY_SECS,
                                _SUBSCRIBE_RETRY_SECS, _PreviewFeed, _preview_ws_loop)
from tests.updater.ws_support import _FakeSession, _FakeWS, _RefusingSession


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
    with patch("updater.ws_preview.update_parks_operating_status") as check:
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
    with patch("updater.ws_preview.update_parks_operating_status") as check:
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
    with patch("updater.ws_preview.debug.warning") as warning:
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

    with patch("updater.ws_preview.aiohttp.ClientSession", lambda: _ScriptedSession(captured, connections)), \
         patch("updater.ws_preview.asyncio.sleep", fake_sleep), \
         patch("updater.ws_preview.update_parks_operating_status"):
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
    with patch("updater.ws_preview.random.uniform", lambda a, b: 1.0):
        _, delays = _run_preview([([], 4029)])
    assert delays == [_REFUSED_RETRY_SECS] == [600]


def test_preview_loop_backs_off_with_jitter_after_a_quick_drop():
    with patch("updater.ws_preview.random.uniform", lambda a, b: 1.25):
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

    with patch("updater.ws_preview.aiohttp.ClientSession", lambda: _SilentSession({}, [])), \
         patch("updater.ws_preview.asyncio.sleep", fake_sleep), \
         patch("updater.ws_preview.debug.warning") as warning:
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

    with patch("updater.ws_preview.aiohttp.ClientSession",
               lambda: _HoldingSession(captured, [([WELCOME, refusal], 1000)])), \
         patch("updater.ws_preview.asyncio.sleep", fake_sleep):
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
    with patch("updater.ws_preview.aiohttp.ClientSession",
               lambda: _JunkSession({}, [(["not json", "[1, 2]", update], 1000)])), \
         patch("updater.ws_preview.asyncio.sleep", cancel_sleep), \
         patch("updater.ws_preview.update_parks_operating_status"):
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

    with patch("updater.ws_preview.aiohttp.ClientSession", lambda: _ErrorSession({}, [])), \
         patch("updater.ws_preview.asyncio.sleep", cancel_sleep), \
         patch("updater.ws_preview.debug.warning") as warning:
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

    with patch("updater.ws_preview.aiohttp.ClientSession", lambda: _RefusingSession(error)), \
         patch("updater.ws_preview.asyncio.sleep", cancel_sleep):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop("real-key", _preview_parks()))
    assert shared.network_issues() is network_issue


def test_preview_welcome_without_destinations_subscribes_to_nothing():
    feed = _PreviewFeed([{"id": "mk", "name": "MK", "attractions": []}])
    with patch("updater.ws_preview.debug.warning") as warning:
        assert feed.handle(WELCOME) == []
    assert "No destination IDs" in warning.call_args[0][0]
