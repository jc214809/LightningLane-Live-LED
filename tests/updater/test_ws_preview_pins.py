"""
Pins for the preview WebSocket handlers, call by call: every log line, send, delayed send, task
cancel, feed-health note and backoff sleep, in order. They exist so _PreviewFeed.handle and
_preview_ws_loop can be split into named steps with no change in behaviour; each case here passed on
the code before the split.
"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import aiohttp
import pytest

from updater import ws_preview
from updater.ws_preview import _PreviewFeed, _preview_ws_loop, _send_later

TEXT, ERROR, BINARY = aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.BINARY


class _Debug:
    def __init__(self, log):
        self._log = log

    def log(self, msg, *args):
        self._log.append(("log", msg))

    def info(self, msg, *args):
        self._log.append(("info", msg))

    def warning(self, msg, *args):
        self._log.append(("warning", msg))

    def error(self, msg, *args):
        self._log.append(("error", msg))


@pytest.fixture
def trace():
    log = []
    patches = [
        patch.object(ws_preview, "debug", _Debug(log)),
        patch.object(ws_preview, "note_live_feed_synced", lambda: log.append("synced")),
        patch.object(ws_preview, "note_live_feed_frame", lambda: log.append("frame")),
        patch.object(ws_preview, "note_live_feed_down", lambda: log.append("down")),
        patch.object(ws_preview, "note_network_result", lambda ok: log.append(("net", ok))),
    ]
    for p in patches:
        p.start()
    yield log
    for p in patches:
        p.stop()


# --- _PreviewFeed.handle ---

def _parks():
    return [{"id": "p1", "destination_id": "d1", "attractions": []}, {"id": "p2", "destination_id": "d2"}]


def _feed(trace):
    feed = _PreviewFeed(_parks())
    feed.applied = []

    def apply(entries, from_snapshot=False):
        trace.append(("apply", entries, from_snapshot))

    feed._apply = apply
    return feed


def test_pin_welcome_subscribes_with_a_snapshot_and_logs_the_limits(trace):
    feed = _feed(trace)
    replies = feed.handle({"type": "welcome", "data": {"limits": {"maxSubscriptions": 15}}, "cursor": "c-ignored"})
    ids = ["d1:ATTRACTION", "d1:SHOW", "d2:ATTRACTION", "d2:SHOW"]
    assert [r[1]["reqId"] for r in replies] == ids and all(r[0] == 0 for r in replies)
    assert trace == [
        ("log", "WS frame: welcome"),
        ("info", "WebSocket connected to ThemeParks.wiki (preview); key limits: {'maxSubscriptions': 15}"),
        ("info", f"Subscribing with a snapshot: {ids}"),
    ]
    assert feed.cursor is None  # a welcome's cursor isn't saved


def test_pin_welcome_with_a_cursor_says_resuming_and_without_limits_logs_empty(trace):
    feed = _feed(trace)
    feed.cursor = "saved"
    replies = feed.handle({"type": "welcome", "data": None})
    assert all(r[1]["since"] == "saved" for r in replies)
    assert trace[1] == ("info", "WebSocket connected to ThemeParks.wiki (preview); key limits: {}")
    assert trace[2][1].startswith("Resuming: ")


def test_pin_welcome_without_destinations_warns_and_sends_nothing(trace):
    feed = _PreviewFeed([{"id": "p"}])
    assert feed.handle({"type": "welcome"}) == []
    assert trace[2:] == [("warning", "No destination IDs in parks_data; nothing to subscribe to."),
                         ("info", "Subscribing with a snapshot: []")]


def test_pin_subscribed_clears_the_pending_request_and_logs_the_name(trace):
    feed = _feed(trace)
    feed.subscribe_frames()
    feed.handle({"type": "subscribed", "data": {"reqId": "d1:SHOW", "name": "MK", "filter": "SHOW"}})
    feed.handle({"type": "subscribed", "data": {"entityId": "e"}})
    feed.handle({"type": "subscribed"})
    assert feed.pending == {"d1:ATTRACTION", "d2:ATTRACTION", "d2:SHOW"}
    assert [t for t in trace if t[0] == "info"] == [
        ("info", "WebSocket subscribed to: MK (SHOW)"),
        ("info", "WebSocket subscribed to: e (all)"),
        ("info", "WebSocket subscribed to: None (all)"),
    ]


@pytest.mark.parametrize("data, entries", [
    ([{"id": 1}, "junk", {"id": 2}, None], [{"id": 1}, {"id": 2}]),
    ({"id": 1}, []),
    (None, []),
])
def test_pin_snapshot_applies_only_dict_entries_then_syncs(trace, data, entries):
    feed = _feed(trace)
    assert feed.handle({"type": "snapshot", "data": data, "cursor": "c1", "total": 9}) == []
    assert trace == [("log", "WS frame: snapshot"), ("apply", entries, True),
                     ("info", "WebSocket snapshot: 9 entities"), "synced"]
    assert feed.cursor == "c1"


def test_pin_snapshot_total_falls_back_to_the_entry_count_and_a_chunk_does_not_sync(trace):
    feed = _feed(trace)
    feed.handle({"type": "snapshot", "data": [{"id": 1}, {"id": 2}]})
    assert ("info", "WebSocket snapshot: 2 entities") in trace
    trace.clear()
    feed.handle({"type": "snapshot", "data": [{"id": 3}], "final": False})
    assert trace == [("log", "WS frame: snapshot"), ("apply", [{"id": 3}], True)]
    assert feed.cursor is None  # no cursor on the frame, none saved


def test_pin_update_counts_and_applies_a_dict_and_ignores_anything_else(trace):
    feed = _feed(trace)
    feed.handle({"type": "update", "data": {"id": 1}, "cursor": "c2"})
    assert (feed.stats.msg_count, feed.cursor) == (1, "c2")
    assert trace == [("log", "WS frame: update"), ("apply", [{"id": 1}], False)]
    trace.clear()
    feed.handle({"type": "update", "data": [1]})
    assert (feed.stats.msg_count, trace) == (1, [("log", "WS frame: update")])


def test_pin_resumed_logs_and_syncs_and_saves_the_cursor(trace):
    feed = _feed(trace)
    assert feed.handle({"type": "resumed", "cursor": "c3"}) == []
    assert trace == [("log", "WS frame: resumed"),
                     ("info", "WebSocket resumed: caught up on the updates missed while disconnected."), "synced"]
    assert feed.cursor == "c3"


def test_pin_ping_replies_with_a_pong_and_saves_the_cursor_without_counting(trace):
    feed = _feed(trace)
    assert feed.handle({"type": "ping", "cursor": "c4"}) == [(0, {"type": "pong"})]
    assert (feed.cursor, feed.stats.msg_count, trace) == ("c4", 0, [("log", "WS frame: ping")])


@pytest.mark.parametrize("data, passed", [({"message": "m", "reqId": "r"}, {"message": "m", "reqId": "r"}),
                                          ("text", {"message": "text"}), (None, {"message": None})])
def test_pin_error_hands_a_dict_to_the_error_handler_and_returns_its_replies(trace, data, passed):
    feed = _feed(trace)
    seen = []
    feed._error = lambda d: (seen.append(d), [(3, {"x": 1})])[1]
    assert feed.handle({"type": "error", "data": data, "cursor": "ignored"}) == [(3, {"x": 1})]
    assert seen == [passed] and feed.cursor is None


@pytest.mark.parametrize("frame", [{"type": "unsubscribed", "cursor": "no"}, {"data": 1}, {},
                                   {"type": ["update"], "cursor": "no"}])  # malformed: not a string
def test_pin_unknown_frames_are_only_logged(trace, frame):
    feed = _feed(trace)
    assert feed.handle(frame) == []
    assert trace == [("log", f"WS frame: {frame.get('type')}")] and feed.cursor is None


def test_pin_the_cursor_is_not_saved_when_applying_the_frame_fails(trace):
    feed = _feed(trace)

    def boom(entries, from_snapshot=False):
        raise ValueError("x")

    feed._apply = boom
    with pytest.raises(ValueError):
        feed.handle({"type": "update", "data": {"id": 1}, "cursor": "c9"})
    assert feed.cursor is None


# --- _send_later ---

@pytest.mark.parametrize("closed, sent", [(False, [{"f": 1}]), (True, [])])
def test_pin_send_later_sleeps_then_sends_only_while_open(trace, closed, sent):
    out = []

    async def sleep(delay):
        trace.append(("sleep", delay))

    class WS:
        async def send_json(self, frame):
            out.append(frame)

    ws = WS()
    ws.closed = closed
    with patch.object(ws_preview.asyncio, "sleep", sleep):
        asyncio.run(_send_later(ws, 5, {"f": 1}))
    assert trace == [("sleep", 5)] and out == sent


# --- _preview_ws_loop ---

class _Script:
    def __init__(self, log, messages=(), close_code=1006, exc=None, raises_after=None):
        self.log, self.messages = log, list(messages)
        self.close_code, self._exc, self.raises_after = close_code, exc, raises_after
        self.closed = False

    async def __aenter__(self):
        self.log.append("ws open")
        return self

    async def __aexit__(self, *args):
        self.log.append("ws close")

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        if self.raises_after is not None:
            raise self.raises_after
        raise StopAsyncIteration

    async def send_json(self, payload):
        self.log.append(("send", payload))

    def exception(self):
        return self._exc


class _Session:
    def __init__(self, log, connections):
        self.log, self.connections = log, connections

    async def __aenter__(self):
        self.log.append("session open")
        return self

    async def __aexit__(self, *args):
        self.log.append("session close")

    def ws_connect(self, url, **kwargs):
        self.log.append(("connect", url, kwargs["protocols"], kwargs["headers"], kwargs["timeout"].ws_receive,
                         kwargs["timeout"].ws_close, "heartbeat" in kwargs))
        conn = self.connections.pop(0)
        if isinstance(conn, BaseException):
            raise conn
        return conn


class _Task:
    def __init__(self, log, name):
        self.log, self.name, self.callbacks = log, name, []

    def cancel(self):
        self.log.append(("cancel", self.name))

    def add_done_callback(self, cb):
        self.callbacks.append(cb)


class _Feed:
    """Stands in for _PreviewFeed: replies are looked up by frame type."""
    instances = []

    def __init__(self, parks_data):
        self.parks_data, self.cursor, self.stats = parks_data, None, None
        self.replies = {}
        self.log = None
        _Feed.instances.append(self)

    def handle(self, frame):
        self.log.append(("handle", frame))
        return self.replies.get(frame.get("type"), [])


def _text(frame):
    return aiohttp.WSMessage(TEXT, json.dumps(frame), None)


CONNECT = ("connect", ws_preview.WS_URL, ws_preview.WS_PREVIEW_SUBPROTOCOLS, {"X-API-Key": "key"},
           ws_preview._PREVIEW_RECEIVE_TIMEOUT_SECS, ws_preview._WS_CLOSE_TIMEOUT_SECS, False)


def _run(trace, connections, sleeps=1, monotonic=(10.0, 12.0), **opts):
    """Run _preview_ws_loop until sleep number `sleeps` cancels it. Returns (tasks, feed).
    opts: replies= ({frame type: replies}), cursor= (the feed's saved cursor), handle= (replaces feed.handle)."""
    log, tasks, ticks, count = trace, [], list(monotonic), {"n": 0}
    _Feed.instances = []

    async def fake_sleep(delay):
        log.append(("sleep", delay))
        count["n"] += 1
        if count["n"] >= sleeps:
            raise asyncio.CancelledError

    def create_task(coro):
        name = "_send_later" if coro.__qualname__ == "_send_later" else "watchdog"
        if name == "_send_later":
            local = coro.cr_frame.f_locals
            log.append(("task", name, local["delay_s"], local["frame"]))
        else:
            log.append(("task", name))
        coro.close()
        task = _Task(log, name)
        tasks.append(task)
        return task

    def watchdog(ws, stats, parks_data):
        log.append(("watchdog args", type(stats).__name__, parks_data is parks))

        async def noop():
            pass
        return noop()

    def feed_factory(parks_data):
        feed = _Feed(parks_data)
        feed.log, feed.replies, feed.cursor = log, opts.get("replies") or {}, opts.get("cursor")
        if opts.get("handle"):
            feed.handle = opts["handle"]
        return feed

    parks = [{"id": "p1"}]
    ns_time = SimpleNamespace(monotonic=lambda: ticks.pop(0) if len(ticks) > 1 else ticks[0])
    ns_random = SimpleNamespace(uniform=lambda a, b: log.append(("jitter", a, b)) or 1.25)
    with patch.object(ws_preview.aiohttp, "ClientSession", lambda: _Session(log, connections)), \
         patch.object(ws_preview.asyncio, "sleep", fake_sleep), \
         patch.object(ws_preview.asyncio, "create_task", create_task), \
         patch.object(ws_preview, "_watchdog", watchdog), \
         patch.object(ws_preview, "_PreviewFeed", feed_factory), \
         patch.object(ws_preview, "time", ns_time), \
         patch.object(ws_preview, "random", ns_random):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(_preview_ws_loop(" key ", parks))
    return tasks, _Feed.instances[0]


def test_pin_a_connection_handles_each_frame_sends_replies_and_backs_off_with_jitter(trace):
    pong, sub = {"type": "pong"}, {"type": "subscribe"}
    ws = _Script(trace, [_text({"type": "welcome"}), _text({"type": "ping"}), _text({"type": "x"})], close_code=1001)
    tasks, feed = _run(trace, [ws], replies={"welcome": [(0, sub), (2, {"type": "later"})], "ping": [(0, pong)]},
                       cursor="cur")
    assert trace == [
        "session open", CONNECT, "ws open",
        ("watchdog args", "_WsStats", True), ("task", "watchdog"),
        ("net", True), "frame", ("handle", {"type": "welcome"}),
        ("send", sub),
        ("task", "_send_later", 2, {"type": "later"}),
        ("net", True), "frame", ("handle", {"type": "ping"}), ("send", pong),
        ("net", True), "frame", ("handle", {"type": "x"}),
        ("cancel", "watchdog"), ("cancel", "_send_later"), "down",
        ("warning", "WebSocket receive loop ended: close_code=1001, exception=None"),
        "ws close", "session close",
        ("info", "WebSocket disconnected; reconnecting in about 10s (resuming from the last cursor)"),
        ("jitter", 1.0, 1.5), ("sleep", 12.5),
    ]
    assert feed.stats.__class__.__name__ == "_WsStats"
    # The delayed send forgets itself when done.
    delayed = tasks[1]
    assert len(delayed.callbacks) == 1


def test_pin_a_new_stats_window_is_made_for_every_connection(trace):
    _, feed = _run(trace, [_Script(trace), _Script(trace)], sleeps=2)
    assert feed.stats is not None
    assert trace.count(("task", "watchdog")) == 2


@pytest.mark.parametrize("frame_text", ["not json", "[1, 2]", '"str"', "3"])
def test_pin_non_json_and_non_object_frames_are_skipped_after_the_health_notes(trace, frame_text):
    msg = aiohttp.WSMessage(TEXT, frame_text, None)
    _run(trace, [_Script(trace, [msg])])
    body = trace[trace.index(("net", True)):trace.index(("cancel", "watchdog"))]
    expected = [("net", True), "frame"]
    if frame_text == "not json":
        expected.append(("warning", "Non-JSON WS message: not json"))
    assert body == expected


def test_pin_other_message_types_only_note_health(trace):
    _run(trace, [_Script(trace, [aiohttp.WSMessage(BINARY, b"", None)])])
    assert trace[trace.index(("net", True)):trace.index(("cancel", "watchdog"))] == [("net", True), "frame"]


def test_pin_an_error_message_stops_reading_and_a_delayed_send_is_cancelled(trace):
    ws = _Script(trace, [_text({"type": "welcome"}), aiohttp.WSMessage(ERROR, None, None), _text({"type": "x"})],
                 exc=RuntimeError("boom"))
    _run(trace, [ws], replies={"welcome": [(5, {"type": "later"})]})
    tail = trace[trace.index(("warning", "WebSocket error message: boom")):]
    assert tail[:5] == [("warning", "WebSocket error message: boom"), ("cancel", "watchdog"),
                        ("cancel", "_send_later"), "down",
                        ("warning", "WebSocket receive loop ended: close_code=1006, exception=boom")]
    assert len(ws.messages) == 1


@pytest.mark.parametrize("code, why", [
    (3000, "authentication failed (check websocket.api_key)"),
    (3001, "credentials were sent in the URL"),
    (3003, "the key's plan doesn't allow this"),
    (4029, "the key's connection limit is reached (other boards or an emulator are using it)"),
])
def test_pin_a_refusal_waits_ten_minutes_with_jitter_and_skips_the_backoff(trace, code, why):
    _run(trace, [_Script(trace, close_code=code)])
    assert trace[-3:] == [
        ("warning", f"WebSocket refused: {why}. Retrying in 10 min; REST polls meanwhile."),
        ("jitter", 1.0, 1.5), ("sleep", 750.0)]


def test_pin_after_a_refusal_the_next_normal_drop_doubles_from_the_ten_minute_delay_to_the_cap(trace):
    conns = [_Script(trace), _Script(trace, close_code=4029), _Script(trace)]
    _run(trace, conns, sleeps=3, monotonic=(0.0, 1.0, 2.0, 3.0, 4.0, 5.0))
    assert [e[1] for e in trace if isinstance(e, tuple) and e[0] == "sleep"] == [12.5, 750.0, 75.0]


def test_pin_a_timeout_logs_the_silence_and_backs_off(trace):
    _run(trace, [TimeoutError()])
    assert trace[3:] == [
        ("warning", f"WebSocket silent for {ws_preview._PREVIEW_RECEIVE_TIMEOUT_SECS}s; reconnecting."),
        ("info", "WebSocket disconnected; reconnecting in about 10s"),
        ("jitter", 1.0, 1.5), ("sleep", 12.5)]


def test_pin_a_timeout_mid_stream_still_cleans_up_the_connection(trace):
    _run(trace, [_Script(trace, raises_after=TimeoutError())], monotonic=(0.0, 100.0))
    assert trace.index(("cancel", "watchdog")) < trace.index("down") < trace.index("ws close")
    assert ("warning", f"WebSocket silent for {ws_preview._PREVIEW_RECEIVE_TIMEOUT_SECS}s; reconnecting.") in trace
    assert ("info", "WebSocket disconnected; reconnecting in about 5s") in trace  # a stable connection resets the delay


@pytest.mark.parametrize("error, flagged", [(OSError("dns"), True), (RuntimeError("rejected"), False)])
def test_pin_a_connect_failure_logs_the_traceback_and_flags_only_socket_errors(trace, error, flagged):
    _run(trace, [error])
    assert trace[:3] == ["session open", CONNECT, "session close"]
    level, text = trace[3]
    assert level == "error" and text.startswith(f"WebSocket error: {error}\nTraceback")
    assert trace[4:] == ([("net", False)] if flagged else []) + [
        ("info", "WebSocket disconnected; reconnecting in about 10s"), ("jitter", 1.0, 1.5), ("sleep", 12.5)]


def test_pin_an_error_after_connecting_is_not_a_network_flag(trace):
    _run(trace, [_Script(trace, raises_after=OSError("reset"))])
    assert ("net", False) not in trace
    assert trace.index("down") < trace.index("ws close")


def test_pin_a_failing_frame_handler_ends_the_connection_and_cleans_up(trace):
    def broken(frame):
        raise ValueError("handler broke")

    _run(trace, [_Script(trace, [_text({"type": "welcome"})])], handle=broken)
    assert any(e[0] == "error" and e[1].startswith("WebSocket error: handler broke")
               for e in trace if isinstance(e, tuple))
    assert trace.index(("cancel", "watchdog")) < trace.index("down") < trace.index("ws close")


def test_pin_the_feed_is_shared_across_connections_so_the_cursor_survives(trace):
    _, feed = _run(trace, [_Script(trace), _Script(trace)], sleeps=2, cursor="kept")
    assert feed.cursor == "kept" and len(_Feed.instances) == 1
    assert [e for e in trace if isinstance(e, tuple) and e[0] == "info"][-1] == (
        "info", "WebSocket disconnected; reconnecting in about 20s (resuming from the last cursor)")
