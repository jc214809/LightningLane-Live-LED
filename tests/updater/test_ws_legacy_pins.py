"""
Pins for the legacy WebSocket handlers, call by call: every log line, lock entry and exit,
parks_data write, REST refresh, send and backoff sleep, in order. They exist so the functions can be
split into named steps with no change in behaviour; each case here passed on the code before the split.
"""
import asyncio
import copy
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import aiohttp
import pytest

from updater import ws_legacy
from updater.ws_legacy import _apply_live_update, _ws_loop

NOW = datetime(2026, 11, 20, 15, 30, 0, tzinfo=timezone.utc)
STAMP = "2026-11-20T15:30:00Z"


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


class _Lock:
    def __init__(self, log):
        self._log = log

    def __enter__(self):
        self._log.append("lock+")
        return self

    def __exit__(self, *args):
        self._log.append("lock-")
        return False


class _FixedDatetime:
    @staticmethod
    def now(tz=None):
        return NOW


@pytest.fixture
def trace():
    """Everything _apply_live_update and _ws_loop call, recorded into one ordered list."""
    log = []

    def op_status(parks, **kwargs):
        log.append(("op_status", [p["id"] for p in parks], kwargs))

    def net(ok):
        log.append(("net", ok))

    patches = [
        patch.object(ws_legacy, "debug", _Debug(log)),
        patch.object(ws_legacy, "parks_data_lock", _Lock(log)),
        patch.object(ws_legacy, "datetime", _FixedDatetime),
        patch.object(ws_legacy, "update_parks_operating_status", op_status),
        patch.object(ws_legacy, "note_network_result", net),
        patch.object(ws_legacy, "parse_forecast", lambda raw: ("forecast", raw)),
        patch.object(ws_legacy, "parse_showtimes", lambda raw: ("showtimes", raw)),
        patch.object(ws_legacy, "parse_queue_wait", lambda queue: ("wait", queue)),
        patch.object(ws_legacy, "get_down_time", lambda since: ("down_time", since)),
    ]
    for p in patches:
        p.start()
    yield log
    for p in patches:
        p.stop()


def _parks():
    return [
        {"id": "p1", "name": "Magic Kingdom", "attractions": [
            {"id": "other", "name": "Other", "status": "OPERATING"},
            {"id": "a1", "name": "Space Mountain", "status": "OPERATING", "waitTime": 20, "down_since": ""},
        ]},
        {"id": "p2", "name": "EPCOT", "attractions": [
            {"id": "a1", "name": "Twin", "status": "OPERATING", "waitTime": 5, "down_since": ""},
        ]},
    ]


def _msg(data, entity_type="ATTRACTION", entity_id="a1"):
    return {"event": "livedata", "entityType": entity_type, "entityId": entity_id, "data": data}


# --- _apply_live_update ---

@pytest.mark.parametrize("data, line", [
    ({"event": "subscribed", "name": "MK", "entityId": "x", "entityTypeFilter": "SHOW"}, "WebSocket subscribed to: MK (SHOW)"),
    ({"event": "subscribed", "entityId": "x"}, "WebSocket subscribed to: x (all)"),
])
def test_pin_subscribed_logs_and_touches_nothing(trace, data, line):
    parks = _parks()
    before = copy.deepcopy(parks)
    _apply_live_update(data, parks)
    assert trace == [("log", f"WS message: {data}"), ("info", line)]
    assert parks == before


@pytest.mark.parametrize("data, shown", [
    ({"event": "error", "message": "bad key"}, "bad key"),
    ({"event": "error"}, "{'event': 'error'}"),
])
def test_pin_server_error_logs_a_warning(trace, data, shown):
    _apply_live_update(data, _parks())
    assert trace == [("log", f"WS message: {data}"), ("warning", f"WebSocket server error: {shown}")]


@pytest.mark.parametrize("data", [
    {"event": "heartbeat"},
    {},
    {"event": "livedata", "entityType": "RESTAURANT", "entityId": "a1", "data": {"status": "OPERATING"}},
    {"event": "livedata", "entityId": "a1", "data": {"status": "OPERATING"}},
    {"event": ["livedata"], "entityType": "ATTRACTION", "entityId": "a1"},  # malformed: not a string
])
def test_pin_ignored_events_only_log_the_message(trace, data):
    parks = _parks()
    before = copy.deepcopy(parks)
    _apply_live_update(data, parks)
    assert trace == [("log", f"WS message: {data}")]
    assert parks == before


def test_pin_unknown_entity_takes_the_lock_and_writes_nothing(trace):
    parks = _parks()
    before = copy.deepcopy(parks)
    _apply_live_update(_msg({"status": "DOWN"}, entity_id="zzz"), parks)
    assert trace[1:] == ["lock+", "lock-"]
    assert parks == before


def test_pin_operating_update_mutates_in_place_and_stops_at_the_first_match(trace):
    parks = _parks()
    park_list, attr_list = parks, parks[0]["attractions"]
    target, twin = attr_list[1], parks[1]["attractions"][0]
    data = {"status": "OPERATING", "queue": {"STANDBY": {"waitTime": 30}}, "forecast": [1], "showtimes": [2]}
    _apply_live_update(_msg(data), parks)
    assert parks is park_list and parks[0]["attractions"] is attr_list and attr_list[1] is target
    assert target == {"id": "a1", "name": "Space Mountain", "status": "OPERATING", "waitTime": ("wait", data["queue"]),
                      "down_since": "", "lastUpdatedTs": STAMP, "updateSource": "websocket",
                      "forecast": ("forecast", [1]), "showtimes": ("showtimes", [2])}
    assert twin["waitTime"] == 5 and "lastUpdatedTs" not in twin  # the loop returns at the first match
    # Same status: no log, no operating check; the lock covers just the writes.
    assert trace == [("log", f"WS message: {_msg(data)}"), "lock+", "lock-"]


def test_pin_empty_forecast_and_missing_showtimes_keep_the_old_values(trace):
    parks = _parks()
    attr = parks[0]["attractions"][1]
    attr["forecast"], attr["showtimes"] = "old-f", "old-s"
    _apply_live_update(_msg({"status": "OPERATING", "forecast": [], "queue": None}), parks)
    assert (attr["forecast"], attr["showtimes"]) == ("old-f", "old-s")
    assert attr["waitTime"] == ("wait", {})
    assert _apply_live_update(_msg({"status": "OPERATING", "showtimes": []}), parks) is None
    assert attr["showtimes"] == ("showtimes", [])


def test_pin_missing_data_key_is_an_empty_update(trace):
    parks = _parks()
    attr = parks[0]["attractions"][1]
    _apply_live_update({"event": "livedata", "entityType": "SHOW", "entityId": "a1", "data": None}, parks)
    assert attr["status"] is None
    assert attr["waitTime"] == ("wait", {})


def test_pin_first_down_sets_down_since_logs_and_checks_operating_status_under_the_lock(trace):
    parks = _parks()
    _apply_live_update(_msg({"status": "DOWN"}), parks)
    attr = parks[0]["attractions"][1]
    assert attr["status"] == "DOWN" and attr["down_since"] == STAMP
    assert attr["waitTime"] == f"Down {('down_time', STAMP)}"
    assert trace[1:] == [
        "lock+",
        ("info", f"DOWN (WS): Space Mountain (Magic Kingdom) — down_since set to {STAMP}"),
        ("info", f"WS update: Space Mountain (Magic Kingdom) OPERATING → DOWN, wait=Down {('down_time', STAMP)}"),
        ("op_status", ["p1"], {"fetch_schedules": False}),
        "lock-",
    ]


def test_pin_a_later_down_keeps_down_since_and_logs_nothing_when_the_status_holds(trace):
    parks = _parks()
    attr = parks[0]["attractions"][1]
    attr.update(status="DOWN", down_since="earlier")
    _apply_live_update(_msg({"status": "DOWN"}), parks)
    assert attr["down_since"] == "earlier"
    assert attr["waitTime"] == "Down ('down_time', 'earlier')"
    assert trace[1:] == ["lock+", "lock-"]


def test_pin_down_without_a_computable_time_is_just_down(trace):
    parks = _parks()
    with patch.object(ws_legacy, "get_down_time", lambda since: None):
        _apply_live_update(_msg({"status": "DOWN"}), parks)
    assert parks[0]["attractions"][1]["waitTime"] == "Down"


@pytest.mark.parametrize("status", ["CLOSED", "REFURBISHMENT"])
def test_pin_closed_clears_down_since_and_leaves_the_wait_alone(trace, status):
    parks = _parks()
    attr = parks[0]["attractions"][1]
    attr["down_since"] = "earlier"
    _apply_live_update(_msg({"status": status}), parks)
    assert attr["down_since"] == "" and attr["waitTime"] == 20 and attr["status"] == status
    assert trace[1:] == [
        "lock+",
        ("info", f"WS update: Space Mountain (Magic Kingdom) OPERATING → {status}, wait=20"),
        ("op_status", ["p1"], {"fetch_schedules": False}),
        "lock-",
    ]


def test_pin_a_status_change_to_operating_sets_the_wait_and_checks_the_park(trace):
    parks = _parks()
    parks[0]["attractions"][1]["status"] = "DOWN"
    _apply_live_update(_msg({"status": "OPERATING", "queue": {"q": 1}}), parks)
    assert trace[1:] == [
        "lock+",
        ("info", "WS update: Space Mountain (Magic Kingdom) DOWN → OPERATING, wait=('wait', {'q': 1})"),
        ("op_status", ["p1"], {"fetch_schedules": False}),
        "lock-",
    ]


def test_pin_a_match_in_the_second_park_is_found(trace):
    parks = _parks()
    parks[0]["attractions"].pop(1)
    _apply_live_update(_msg({"status": "CLOSED"}), parks)
    assert parks[1]["attractions"][0]["status"] == "CLOSED"
    assert ("op_status", ["p2"], {"fetch_schedules": False}) in trace


def test_pin_a_park_without_attractions_is_skipped(trace):
    parks = [{"id": "p0", "name": "Empty"}] + _parks()
    _apply_live_update(_msg({"status": "OPERATING"}), parks)
    assert parks[1]["attractions"][1]["lastUpdatedTs"] == STAMP


# --- _ws_loop ---

class _Msg:
    def __init__(self, type_, data=""):
        self.type, self.data = type_, data


TEXT, ERROR = aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.ERROR


class _Script:
    """One connection: what ws_connect returns, with the messages the receive loop yields."""

    def __init__(self, log, messages=(), close_code=1006, exc=None, raises_after=None):
        self.log, self.messages = log, list(messages)
        self.close_code, self._exc, self.raises_after = close_code, exc, raises_after
        self.sent = []

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
        self.log.append(("connect", url, kwargs["protocols"], kwargs["headers"], kwargs["heartbeat"]))
        conn = self.connections.pop(0)
        if isinstance(conn, BaseException):
            raise conn
        return conn


class _Task:
    def __init__(self, log):
        self._log = log

    def cancel(self):
        self._log.append("watchdog cancel")


def _run(trace, connections, parks, sleeps=1, monotonic=(100.0, 100.0), **hooks):
    """Run _ws_loop until the sleep number `sleeps` (counting from 1), which cancels it. Sleeps are logged.
    hooks: fetch=, apply= (replacements for the REST fetch and the update handler); returns=True: the
    loop is expected to end by itself."""
    fetch, apply, returns = hooks.get("fetch"), hooks.get("apply"), hooks.get("returns", False)
    log = trace
    count = {"sleeps": 0}
    ticks = list(monotonic)

    async def fake_sleep(delay):
        log.append(("sleep", delay))
        count["sleeps"] += 1
        if count["sleeps"] >= sleeps:
            raise asyncio.CancelledError

    def create_task(coro):
        log.append("watchdog start")
        coro.close()
        return _Task(log)

    def watchdog(ws, stats, parks_data):
        log.append(("watchdog args", ws is not None, type(stats).__name__, parks_data is parks))

        async def noop():
            pass
        return noop()

    async def default_fetch(park):
        log.append(("fetch", park["id"]))
        return [{"id": "live"}]

    def default_merge(attractions, new):
        log.append(("merge", attractions is not None, new))

    def default_apply(data, parks_data):
        log.append(("apply", data, parks_data is parks))

    fake_time = SimpleNamespace(monotonic=lambda: ticks.pop(0) if len(ticks) > 1 else ticks[0])
    with patch.object(ws_legacy.aiohttp, "ClientSession", lambda: _Session(log, connections)), \
         patch.object(ws_legacy.asyncio, "sleep", fake_sleep), \
         patch.object(ws_legacy.asyncio, "create_task", create_task), \
         patch.object(ws_legacy, "_watchdog", watchdog), \
         patch.object(ws_legacy, "time", fake_time), \
         patch.object(ws_legacy, "fetch_park_live_data", fetch or default_fetch), \
         patch.object(ws_legacy, "merge_live_data", default_merge), \
         patch.object(ws_legacy, "_apply_live_update", apply or default_apply):
        if returns:
            assert asyncio.run(_ws_loop(" key ", parks)) is None
        else:
            with pytest.raises(asyncio.CancelledError):
                asyncio.run(_ws_loop(" key ", parks))


def _dest_parks():
    return [{"id": "p1", "name": "MK", "destination_id": "d1", "attractions": [{"id": "a"}]}]


CONNECT = ("connect", ws_legacy.WS_URL, ws_legacy.WS_SUBPROTOCOLS, {"X-API-Key": "key"}, ws_legacy._WS_HEARTBEAT_SECS)


def test_pin_first_connection_subscribes_reads_messages_and_backs_off(trace):
    ws = _Script(trace, [_Msg(TEXT, '{"event": "x"}'), _Msg(TEXT, "not json"), _Msg(aiohttp.WSMsgType.BINARY, b"")],
                 close_code=1001)
    parks = _dest_parks()
    _run(trace, [ws], parks, monotonic=(10.0, 12.0))
    assert trace == [
        "session open", CONNECT, "ws open",
        ("info", "WebSocket connected to ThemeParks.wiki"),
        ("send", {"event": "subscribe", "entityId": "d1", "entityTypeFilter": "ATTRACTION"}),
        ("send", {"event": "subscribe", "entityId": "d1", "entityTypeFilter": "SHOW"}),
        ("info", "Subscribed to destinations: ['d1']"),
        ("watchdog args", True, "_WsStats", True), "watchdog start",
        ("net", True), ("log", 'WS raw: {"event": "x"}'), ("apply", {"event": "x"}, True),
        ("net", True), ("log", "WS raw: not json"),
        ("warning", "Non-JSON WS message: not json"),
        ("net", True),
        "watchdog cancel",
        ("warning", "WebSocket receive loop ended: close_code=1001, exception=None"),
        "ws close", "session close",
        ("info", "WebSocket disconnected; reconnecting in 10s"),
        ("sleep", 10),
    ]


def test_pin_a_websocket_error_message_stops_reading(trace):
    ws = _Script(trace, [_Msg(ERROR), _Msg(TEXT, "{}")], exc=RuntimeError("boom"))
    _run(trace, [ws], _dest_parks())
    assert trace[trace.index(("net", True)):] == [
        ("net", True),
        ("warning", "WebSocket error message: boom"),
        "watchdog cancel",
        ("warning", "WebSocket receive loop ended: close_code=1006, exception=boom"),
        "ws close", "session close",
        ("info", "WebSocket disconnected; reconnecting in 10s"),
        ("sleep", 10),
    ]
    assert len(ws.messages) == 1


def test_pin_two_destinations_subscribe_to_every_type_in_turn(trace):
    parks = _dest_parks() + [{"id": "p2", "destination_id": "d2"}, {"id": "p3", "destination_id": "d1"}, {"id": "p4"}]
    ws = _Script(trace)
    _run(trace, [ws], parks)
    sends = [e[1] for e in trace if isinstance(e, tuple) and e[0] == "send"]
    assert len(sends) == 4
    assert {(s["entityId"], s["entityTypeFilter"]) for s in sends} == {
        (d, t) for d in ("d1", "d2") for t in ("ATTRACTION", "SHOW")}
    # One destination's types are sent together, ATTRACTION first.
    assert [s["entityTypeFilter"] for s in sends][0::2] == ["ATTRACTION", "ATTRACTION"]


def test_pin_no_destination_ids_warns_and_ends_the_loop(trace):
    # The warning says "will retry", but the break leaves the while True: the coroutine returns, with no backoff.
    parks = [{"id": "p1", "name": "MK"}]
    _run(trace, [_Script(trace)], parks, monotonic=(1.0, 2.0), returns=True)
    assert trace == [
        "session open", CONNECT, "ws open",
        ("info", "WebSocket connected to ThemeParks.wiki"),
        ("warning", "No destination IDs in parks_data; will retry"),
        "ws close", "session close",
    ]


def test_pin_backoff_doubles_to_the_cap_and_resets_after_a_stable_connection(trace):
    conns = [OSError("x"), OSError("y"), OSError("z"), OSError("w"), OSError("v"), OSError("u"),
             _Script(trace), OSError("t")]
    _run(trace, conns, _dest_parks(), sleeps=8, monotonic=(0.0, 100.0))
    assert [e[1] for e in trace if isinstance(e, tuple) and e[0] == "sleep"] == [10, 20, 40, 60, 60, 60, 5, 10]


def test_pin_a_short_connection_keeps_doubling(trace):
    conns = [_Script(trace), _Script(trace)]
    _run(trace, conns, _dest_parks(), sleeps=2, monotonic=(0.0, 59.9, 60.0, 61.0))
    assert [e[1] for e in trace if isinstance(e, tuple) and e[0] == "sleep"] == [10, 20]


def test_pin_second_connection_refreshes_every_park_over_rest_first(trace):
    parks = [
        {"id": "p1", "name": "MK", "destination_id": "d1", "attractions": [{"id": "a"}]},
        {"id": "p2", "name": "Empty", "destination_id": "d1", "attractions": []},
        {"id": "p3", "name": "EPCOT", "destination_id": "d2", "attractions": [{"id": "b"}], "live_data_stale": True},
        {"id": "p4", "name": "DHS", "destination_id": "d2", "attractions": [{"id": "c"}]},
    ]

    async def fetch(park):
        trace.append(("fetch", park["id"]))
        return None if park["id"] == "p4" else [{"id": "live-" + park["id"]}]

    _run(trace, [_Script(trace), _Script(trace)], parks, sleeps=2, fetch=fetch)
    second = trace[trace.index(("sleep", 10)) + 1:]
    assert second[:3] == ["session open", CONNECT, "ws open"]
    refresh = second[3:second.index(("info", "REST refresh after reconnect complete.")) + 1]
    assert refresh == [
        ("info", "WebSocket reconnected — refreshing live data via REST."),
        ("fetch", "p1"), "lock+", ("merge", True, [{"id": "live-p1"}]), "lock-",
        ("fetch", "p3"), "lock+", ("merge", True, [{"id": "live-p3"}]), "lock-",
        ("fetch", "p4"),
        ("warning", "Live data refresh failed for DHS after reconnect; keeping existing data."),
        ("op_status", ["p1", "p2", "p3", "p4"], {"fetch_schedules": False}),
        ("info", "REST refresh after reconnect complete."),
    ]
    assert [p.get("live_data_stale") for p in parks] == [False, None, False, True]
    assert ("info", "Subscribed to destinations: ['d1', 'd2']") in second or \
        ("info", "Subscribed to destinations: ['d2', 'd1']") in second
    assert second[-1] == ("sleep", 20)


def test_pin_a_reconnect_with_no_destinations_still_refreshes_then_ends(trace):
    parks = _dest_parks()

    def lose_destinations(data, parks_data):
        parks_data[0].pop("destination_id")

    _run(trace, [_Script(trace, [_Msg(TEXT, "{}")]), _Script(trace)], parks, sleeps=2, apply=lose_destinations,
         returns=True)
    second = trace[trace.index(("sleep", 10)) + 1:]
    assert ("fetch", "p1") in second
    assert second[-3:] == [("warning", "No destination IDs in parks_data; will retry"), "ws close", "session close"]
    assert "watchdog start" not in second


@pytest.mark.parametrize("error, flags", [(OSError("dns"), True), (RuntimeError("rejected"), False)])
def test_pin_a_connect_failure_logs_the_traceback_and_flags_only_socket_errors(trace, error, flags):
    _run(trace, [error], _dest_parks())
    assert trace[:3] == ["session open", CONNECT, "session close"]
    level, text = trace[3]
    assert level == "error" and text.startswith(f"WebSocket error: {error}\nTraceback")
    rest = trace[4:]
    assert rest == ([("net", False)] if flags else []) + [
        ("info", "WebSocket disconnected; reconnecting in 10s"), ("sleep", 10)]


def test_pin_an_error_after_connecting_is_not_a_network_flag_and_cancels_the_watchdog(trace):
    ws = _Script(trace, raises_after=OSError("reset"))
    _run(trace, [ws], _dest_parks(), monotonic=(0.0, 1.0))
    assert ("net", False) not in trace
    assert trace.index("watchdog cancel") < trace.index("ws close")
    assert any(e[0] == "error" and e[1].startswith("WebSocket error: reset") for e in trace if isinstance(e, tuple))
    assert not any(isinstance(e, tuple) and e[:1] == ("warning",) and "receive loop ended" in e[1] for e in trace)
    assert trace[-2:] == [("info", "WebSocket disconnected; reconnecting in 10s"), ("sleep", 10)]


def test_pin_a_failure_while_applying_an_update_ends_the_connection(trace):
    def boom(data, parks_data):
        raise ValueError("bad update")

    _run(trace, [_Script(trace, [_Msg(TEXT, "{}")])], _dest_parks(), apply=boom)
    assert "watchdog cancel" in trace
    assert any(e[0] == "error" and e[1].startswith("WebSocket error: bad update") for e in trace if isinstance(e, tuple))


def test_pin_a_json_decode_error_from_the_handler_is_taken_as_non_json(trace):
    def boom(data, parks_data):
        raise json.JSONDecodeError("x", "y", 0)

    _run(trace, [_Script(trace, [_Msg(TEXT, "{}")])], _dest_parks(), apply=boom)
    assert ("warning", "Non-JSON WS message: {}") in trace
