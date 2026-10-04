import asyncio
import copy
import threading
from datetime import datetime, timedelta, timezone

import pytest

from updater import shared
from updater.data_updater import (
    LIVE_FEED_STARTUP_WAIT_SECS,
    REST_INTERVAL_WITH_LIVE_FEED_SECS,
    merge_live_data,
    rest_poll_due,
    update_parks_live_data,
    live_data_updater
)

# Dummy parks list used for testing.
DUMMY_PARKS = [{
    "id": "park1",
    "name": "Fantasy Land",
    "attractions": [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old"
    }]
}]

# --- Existing Tests ---

def test_update_parks_live_data(monkeypatch):
    """
    Assume update_parks_live_data takes a parks list and updates each park's attractions
    using live data. For testing, we patch updater.data_updater.fetch_park_live_data to return dummy live data.
    """
    # Dummy live data that should update the attraction.
    dummy_live_data = [{
        "id": "1",
        "waitTime": 25,
        "status": "OPERATING",
        "lastUpdatedTs": "new"
    }]

    async def dummy_fetch_live_data(attractions):
        return dummy_live_data

    # Patch fetch_live_data inside updater.data_updater.
    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    # Call update_parks_live_data with a copy of the dummy parks.
    parks_copy = copy.deepcopy(DUMMY_PARKS)
    updated_parks = update_parks_live_data(parks_copy)

    # Verify that the attraction has been updated.
    updated_attr = updated_parks[0]["attractions"][0]
    assert updated_attr["waitTime"] == 25
    assert updated_attr["lastUpdatedTs"] == "new"
    # For an attraction not down, down_since should remain unchanged.
    assert updated_attr["down_since"] == ""


def test_live_data_updater(monkeypatch):
    """
    Test live_data_updater by running it in a separate thread and forcing it to break out
    after one iteration. We patch updater.data_updater.fetch_park_live_data to return updated live data,
    and patch time.sleep along with fetch_parks_and_attractions to bypass real HTTP calls.
    """
    parks_data = []

    # Dummy live data to update the attraction.
    dummy_live_data = [{
        "id": "1",
        "waitTime": 30,
        "status": "OPERATING",
        "lastUpdatedTs": "new_live"
    }]

    async def dummy_fetch_live_data(attractions):
        return dummy_live_data

    # Patch fetch_live_data inside updater.data_updater.
    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    # Patch fetch_parks_and_attractions to return the parks unchanged.
    monkeypatch.setattr("updater.data_updater.fetch_parks_and_attractions", lambda parks: parks)

    # Fake sleep function that raises KeyboardInterrupt to break the loop.
    def fake_sleep(duration):
        raise KeyboardInterrupt()

    # Patch time.sleep used by live_data_updater via updater.data_updater.
    monkeypatch.setattr("updater.data_updater.time", type("t", (), {"sleep": fake_sleep}))

    # Run live_data_updater in a thread. It takes parameters: (parks_list, update_interval, parks_data)
    updater_thread = threading.Thread(
        target=live_data_updater,
        args=(copy.deepcopy(DUMMY_PARKS), 0, parks_data),
        daemon=True
    )
    try:
        updater_thread.start()
        updater_thread.join(timeout=2)
    except KeyboardInterrupt:
        pass

    # Check that parks_data has been updated. Expect at least one park.
    assert len(parks_data) > 0
    updated_attr = parks_data[0]["attractions"][0]
    assert updated_attr["waitTime"] == 30
    assert updated_attr["lastUpdatedTs"] == "new_live"


def test_live_data_updater_logs_consecutive_failure_count(monkeypatch):
    """Repeated loop failures log an incrementing consecutive-failure count, and a
    subsequent success resets it back to 0 — surfaces a persistent bug in the logs
    with escalating visibility instead of an identical line forever."""
    parks_data = []
    monkeypatch.setattr("updater.data_updater.fetch_parks_and_attractions", lambda parks: parks)

    call_count = []

    def failing_operating_status(parks, **kwargs):
        call_count.append(1)
        if len(call_count) <= 2:
            raise RuntimeError("boom")
        return parks

    monkeypatch.setattr("updater.data_updater.update_parks_operating_status", failing_operating_status)

    async def dummy_fetch_live_data(park):
        return None

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    logged_errors = []
    monkeypatch.setattr("updater.data_updater.debug.error", lambda msg, *a: logged_errors.append(msg))

    iterations = []

    def fake_sleep(duration):
        iterations.append(1)
        if len(iterations) >= 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr("updater.data_updater.time", type("t", (), {"sleep": fake_sleep}))

    updater_thread = threading.Thread(
        target=live_data_updater,
        args=(copy.deepcopy(DUMMY_PARKS), 0, parks_data),
        daemon=True,
    )
    try:
        updater_thread.start()
        updater_thread.join(timeout=2)
    except KeyboardInterrupt:
        pass

    failure_logs = [m for m in logged_errors if "consecutive failure" in m]
    assert "consecutive failure #1" in failure_logs[0]
    assert "consecutive failure #2" in failure_logs[1]


def test_merge_live_data_updates_existing():
    existing = [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old",
    }]
    new_live = [{
        "id": "1",
        "waitTime": 20,
        "status": "OPERATING",
        "lastUpdatedTs": "new",
    }]
    result = merge_live_data(copy.deepcopy(existing), new_live)
    assert len(result) == 1
    updated = result[0]
    assert updated["waitTime"] == 20
    assert updated["status"] == "OPERATING"
    assert updated["lastUpdatedTs"] == "new"
    assert updated["down_since"] == ""


def test_merge_live_data_down_since_handling():
    existing = [{
        "id": "1",
        "waitTime": 5,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old",
    }]

    new_down = [{
        "id": "1",
        "waitTime": 0,
        "status": "DOWN",
        "lastUpdatedTs": "tsdown",
    }]
    result = merge_live_data(copy.deepcopy(existing), new_down)
    assert result[0]["status"] == "DOWN"
    assert result[0]["down_since"] == "tsdown"

    new_up = [{
        "id": "1",
        "waitTime": 15,
        "status": "OPERATING",
        "lastUpdatedTs": "tsup",
    }]
    result2 = merge_live_data(result, new_up)
    assert result2[0]["status"] == "OPERATING"
    assert result2[0]["down_since"] == ""


def test_merge_live_data_down_wait_time_uses_down_since_not_last_updated():
    """Regression test: waitTime for a DOWN attraction must reflect elapsed
    time since down_since (when the ride actually went down), not the raw
    per-poll lastUpdatedTs, which stays recent on every REST poll."""
    down_since_ts = (datetime.now(timezone.utc) - timedelta(minutes=42)).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing = [{
        "id": "1",
        "waitTime": 5,
        "status": "DOWN",
        "down_since": down_since_ts,
        "lastUpdatedTs": down_since_ts,
    }]

    # A fresh REST poll re-reports DOWN with a lastUpdatedTs from "just now".
    new_still_down = [{
        "id": "1",
        "status": "DOWN",
        "lastUpdatedTs": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }]
    result = merge_live_data(copy.deepcopy(existing), new_still_down)

    assert result[0]["down_since"] == down_since_ts
    assert result[0]["waitTime"] == "Down 42"


def test_merge_live_data_ignores_unknown_ids():
    """Live updates carry no name/entityType, so unknown ids must be skipped —
    roster additions are handled by refresh_park_attractions."""
    existing = [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old",
    }]
    new_live = [
        {
            "id": "1",
            "waitTime": 15,
            "status": "OPERATING",
            "lastUpdatedTs": "new",
        },
        {
            "id": "2",
            "waitTime": 5,
            "status": "OPERATING",
            "lastUpdatedTs": "new2",
        },
    ]
    result = merge_live_data(copy.deepcopy(existing), new_live)
    assert len(result) == 1
    assert result[0]["id"] == "1"
    assert result[0]["waitTime"] == 15


def test_merge_live_data_mutates_in_place():
    """merge must return the same list and same dict objects it was given —
    rebuilding either would drop concurrent WS-thread updates."""
    existing = [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old",
    }]
    original_attr = existing[0]
    result = merge_live_data(existing, [
        {"id": "1", "waitTime": 15, "status": "OPERATING", "lastUpdatedTs": "new"},
    ])
    assert result is existing
    assert result[0] is original_attr
    assert original_attr["waitTime"] == 15


class SpyLock:
    def __init__(self):
        self.acquisitions = 0

    def __enter__(self):
        self.acquisitions += 1
        return self

    def __exit__(self, *args):
        return False


def test_update_parks_live_data_merges_under_lock(monkeypatch):
    async def ok_fetch(park):
        return [{"id": "1", "waitTime": 12, "status": "OPERATING", "lastUpdatedTs": "new"}]

    spy = SpyLock()
    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", ok_fetch)
    monkeypatch.setattr("updater.data_updater.parks_data_lock", spy)
    update_parks_live_data(copy.deepcopy(DUMMY_PARKS))
    assert spy.acquisitions == 1


def test_rest_merge_and_ws_write_interleave_safely_under_lock(monkeypatch):
    """
    With REST polling always-on (Change 3), merge_live_data (REST thread) and a
    simulated WS-thread write can run concurrently against the same attraction
    dict. Both must serialize on the real parks_data_lock so neither write is lost —
    extends test_update_parks_live_data_merges_under_lock to the continuous-polling
    scenario described in the plan.
    """
    from updater.shared import parks_data_lock

    parks_copy = copy.deepcopy(DUMMY_PARKS)
    attr = parks_copy[0]["attractions"][0]

    results = {}

    async def slow_fetch(park):
        return [{"id": "1", "waitTime": 12, "status": "OPERATING", "lastUpdatedTs": "rest-update"}]

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", slow_fetch)

    def ws_write():
        with parks_data_lock:
            attr["status"] = "DOWN"
            attr["lastUpdatedTs"] = "ws-update"
        results["ws_done"] = True

    def rest_update():
        update_parks_live_data(parks_copy)
        results["rest_done"] = True

    t1 = threading.Thread(target=ws_write)
    t2 = threading.Thread(target=rest_update)
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)

    assert results.get("ws_done") is True
    assert results.get("rest_done") is True
    # Whichever wrote last wins cleanly — status and lastUpdatedTs must be consistent
    # with each other (no torn write mixing fields from both threads).
    if attr["lastUpdatedTs"] == "ws-update":
        assert attr["status"] == "DOWN"
    else:
        assert attr["lastUpdatedTs"] == "rest-update"
        assert attr["status"] == "OPERATING"


def test_merge_live_data_preserves_wait_time_when_omitted():
    """A CLOSED update omits waitTime; the last known value must survive."""
    existing = [{
        "id": "1",
        "waitTime": 25,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old",
    }]
    new_live = [{"id": "1", "status": "CLOSED", "lastUpdatedTs": "new"}]
    result = merge_live_data(copy.deepcopy(existing), new_live)
    assert result[0]["status"] == "CLOSED"
    assert result[0]["waitTime"] == 25
    assert result[0]["lastUpdatedTs"] == "new"


def test_update_parks_live_data_fetch_failure_keeps_data_and_flags_stale(monkeypatch):
    """A failed park fetch (429/timeout) must keep existing data and set live_data_stale."""
    async def failing_fetch(park):
        return None

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", failing_fetch)
    parks_copy = copy.deepcopy(DUMMY_PARKS)
    updated = update_parks_live_data(parks_copy)
    attr = updated[0]["attractions"][0]
    assert attr["waitTime"] == 10
    assert attr["lastUpdatedTs"] == "old"
    assert updated[0]["live_data_stale"] is True


def test_update_parks_live_data_success_clears_stale_flag(monkeypatch):
    async def ok_fetch(park):
        return [{"id": "1", "waitTime": 12, "status": "OPERATING", "lastUpdatedTs": "new"}]

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", ok_fetch)
    parks_copy = copy.deepcopy(DUMMY_PARKS)
    parks_copy[0]["live_data_stale"] = True
    updated = update_parks_live_data(parks_copy)
    assert updated[0]["live_data_stale"] is False
    assert updated[0]["attractions"][0]["waitTime"] == 12


# --- Additional Tests to Increase Coverage ---

def test_update_parks_live_data_no_change(monkeypatch):
    """
    Test update_parks_live_data when dummy live data is identical to the existing attractions,
    so no changes should occur.
    """
    # Dummy live data equal to existing.
    dummy_live_data = [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "lastUpdatedTs": "old"
    }]

    async def dummy_fetch_live_data(attractions):
        return dummy_live_data

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    parks_copy = copy.deepcopy(DUMMY_PARKS)
    updated_parks = update_parks_live_data(parks_copy)
    # Verify that the attraction remains unchanged.
    updated_attr = updated_parks[0]["attractions"][0]
    assert updated_attr["waitTime"] == 10
    assert updated_attr["lastUpdatedTs"] == "old"
    assert updated_attr["down_since"] == ""


def test_update_parks_live_data_multiple_attractions(monkeypatch):
    """
    Test update_parks_live_data with a park containing multiple attractions.
    We patch fetch_live_data to return updated data for each attraction.
    """
    parks = [{
        "id": "park1",
        "name": "Fantasy Land",
        "attractions": [
            {
                "id": "1",
                "waitTime": 10,
                "status": "OPERATING",
                "down_since": "",
                "lastUpdatedTs": "old1"
            },
            {
                "id": "2",
                "waitTime": 20,
                "status": "OPERATING",
                "down_since": "",
                "lastUpdatedTs": "old2"
            }
        ]
    }]

    dummy_live_data = [
        {
            "id": "1",
            "waitTime": 12,
            "status": "OPERATING",
            "lastUpdatedTs": "new1"
        },
        {
            "id": "2",
            "waitTime": 18,
            "status": "OPERATING",
            "lastUpdatedTs": "new2"
        }
    ]

    async def dummy_fetch_live_data(attractions):
        return dummy_live_data

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    parks_copy = copy.deepcopy(parks)
    updated_parks = update_parks_live_data(parks_copy)
    attr1 = updated_parks[0]["attractions"][0]
    attr2 = updated_parks[0]["attractions"][1]
    assert attr1["waitTime"] == 12
    assert attr1["lastUpdatedTs"] == "new1"
    assert attr2["waitTime"] == 18
    assert attr2["lastUpdatedTs"] == "new2"


def test_update_parks_live_data_fetches_multiple_parks_concurrently(monkeypatch):
    """
    fetch_park_live_data is called once per park, on one shared event loop, via
    asyncio.gather rather than one asyncio.run per park — all in-flight
    simultaneously rather than strictly sequential.
    """
    parks = [
        {"id": "park1", "name": "Fantasy Land",
         "attractions": [{"id": "1", "waitTime": 10, "status": "OPERATING", "down_since": "", "lastUpdatedTs": "old"}]},
        {"id": "park2", "name": "Adventure Land",
         "attractions": [{"id": "2", "waitTime": 5, "status": "OPERATING", "down_since": "", "lastUpdatedTs": "old"}]},
    ]

    in_flight = []
    max_concurrent = []

    async def tracking_fetch(park):
        in_flight.append(park["id"])
        max_concurrent.append(len(in_flight))
        await asyncio.sleep(0)  # yield control, allowing the other fetch to start
        in_flight.remove(park["id"])
        return [{"id": park["attractions"][0]["id"], "waitTime": 99, "status": "OPERATING", "lastUpdatedTs": "new"}]

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", tracking_fetch)
    updated = update_parks_live_data(copy.deepcopy(parks))

    assert max(max_concurrent) == 2, "both parks' fetches should overlap, not run strictly sequentially"
    assert updated[0]["attractions"][0]["waitTime"] == 99
    assert updated[1]["attractions"][0]["waitTime"] == 99


def test_update_parks_live_data_one_park_failure_does_not_block_another(monkeypatch):
    """One park's fetch failing (returns None) must not prevent another park's
    successful fetch from being merged."""
    parks = [
        {"id": "park1", "name": "Fantasy Land",
         "attractions": [{"id": "1", "waitTime": 10, "status": "OPERATING", "down_since": "", "lastUpdatedTs": "old"}]},
        {"id": "park2", "name": "Adventure Land",
         "attractions": [{"id": "2", "waitTime": 5, "status": "OPERATING", "down_since": "", "lastUpdatedTs": "old"}]},
    ]

    async def flaky_fetch(park):
        if park["id"] == "park1":
            return None
        return [{"id": "2", "waitTime": 42, "status": "OPERATING", "lastUpdatedTs": "new"}]

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", flaky_fetch)
    updated = update_parks_live_data(copy.deepcopy(parks))

    assert updated[0]["live_data_stale"] is True
    assert updated[0]["attractions"][0]["waitTime"] == 10  # unchanged
    assert updated[1]["live_data_stale"] is False
    assert updated[1]["attractions"][0]["waitTime"] == 42


def test_merge_live_data_no_change():
    """
    Test merge_live_data when new_live data is identical to the existing data.
    """
    existing = [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "down_since": "",
        "lastUpdatedTs": "old",
    }]
    new_live = [{
        "id": "1",
        "waitTime": 10,
        "status": "OPERATING",
        "lastUpdatedTs": "old",
    }]
    result = merge_live_data(copy.deepcopy(existing), new_live)
    # Expect the output to be identical to the original existing data.
    assert result == existing


def test_update_parks_live_data_always_calls_http_fetch(monkeypatch):
    """REST polling is an always-on backstop (PR #73 made the per-park fetch cheap):
    fetch_live_data must be called regardless of whether WS is also active —
    update_parks_live_data no longer takes a use_websocket flag at all."""
    called = []

    async def dummy_fetch_live_data(park):
        called.append(True)
        return []

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    parks_copy = copy.deepcopy(DUMMY_PARKS)
    update_parks_live_data(parks_copy)

    assert called == [True], "fetch_live_data should always be called"


def test_live_data_updater_websocket_polls_every_loop_iteration(monkeypatch):
    """
    live_data_updater with use_websocket=True calls fetch_live_data for the initial
    population AND again on every polling-loop iteration — REST stays on as a
    continuous backstop rather than handing off exclusively to WS after startup.
    """
    parks_data = []
    fetch_call_count = []

    async def counting_fetch(park):
        fetch_call_count.append(1)
        return []

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", counting_fetch)
    monkeypatch.setattr("updater.data_updater.fetch_parks_and_attractions", lambda parks: copy.deepcopy(DUMMY_PARKS))
    monkeypatch.setattr("updater.data_updater.update_parks_operating_status", lambda parks: parks)

    loop_iterations = []

    def fake_sleep(duration):
        loop_iterations.append(1)
        raise KeyboardInterrupt()

    monkeypatch.setattr("updater.data_updater.time", type("t", (), {"sleep": fake_sleep}))

    updater_thread = threading.Thread(
        target=live_data_updater,
        args=(copy.deepcopy(DUMMY_PARKS), 0, parks_data),
        kwargs={"use_websocket": True},
        daemon=True,
    )
    try:
        updater_thread.start()
        updater_thread.join(timeout=2)
    except KeyboardInterrupt:
        pass

    # fetch_live_data called for the initial fetch AND once in the polling loop
    assert len(fetch_call_count) == 2, "fetch_live_data should be called for the initial fetch and each loop iteration"
    assert loop_iterations == [1], "polling loop should have run once then stopped"


def test_live_data_updater_websocket_loop_updates_operating_status(monkeypatch):
    """
    In websocket mode the polling loop must still call update_parks_operating_status
    (with schedule fetching enabled) so schedule refreshes deferred by the WS thread
    via 'schedule_refresh_needed' get serviced.
    """
    parks_data = []
    status_calls = []

    async def dummy_fetch(park):
        return []

    def recording_update(parks, fetch_schedules=True):
        status_calls.append(fetch_schedules)
        return parks

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch)
    monkeypatch.setattr("updater.data_updater.fetch_parks_and_attractions", lambda parks: copy.deepcopy(DUMMY_PARKS))
    monkeypatch.setattr("updater.data_updater.update_parks_operating_status", recording_update)

    def fake_sleep(duration):
        raise KeyboardInterrupt()

    monkeypatch.setattr("updater.data_updater.time", type("t", (), {"sleep": fake_sleep}))

    updater_thread = threading.Thread(
        target=live_data_updater,
        args=(copy.deepcopy(DUMMY_PARKS), 0, parks_data),
        kwargs={"use_websocket": True},
        daemon=True,
    )
    updater_thread.start()
    updater_thread.join(timeout=2)

    # One call from the initial fetch, one from the loop iteration — both with
    # schedule fetching enabled (the REST thread is where blocking HTTP belongs).
    assert status_calls == [True, True]

def test_merge_live_data_copies_forecast_and_keeps_it_when_an_update_has_none():
    forecast = [{"time": "2026-09-25T10:00:00-04:00", "waitTime": 20}]
    existing = [{"id": "1", "waitTime": 10, "status": "OPERATING", "down_since": "", "lastUpdatedTs": "old"}]
    merge_live_data(existing, [{"id": "1", "waitTime": 20, "status": "OPERATING", "lastUpdatedTs": "a", "forecast": forecast}])
    assert existing[0]["forecast"] == forecast
    merge_live_data(existing, [{"id": "1", "waitTime": 25, "status": "OPERATING", "lastUpdatedTs": "b"}])
    assert existing[0]["forecast"] == forecast



def test_merge_live_data_copies_showtimes_and_an_empty_list_clears_them():
    start = datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc)
    existing = [{"id": "hea", "status": "OPERATING", "down_since": "", "lastUpdatedTs": "old"}]
    merge_live_data(existing, [{"id": "hea", "status": "OPERATING", "lastUpdatedTs": "a", "showtimes": [start]}])
    assert existing[0]["showtimes"] == [start]
    merge_live_data(existing, [{"id": "hea", "status": "OPERATING", "lastUpdatedTs": "b"}])
    assert existing[0]["showtimes"] == [start], "an update without showtimes keeps them"
    merge_live_data(existing, [{"id": "hea", "status": "OPERATING", "lastUpdatedTs": "c", "showtimes": []}])
    assert existing[0]["showtimes"] == []

# --- network badge flag ---

TWO_PARKS = [
    {"id": "park1", "name": "MK", "attractions": [{"id": "1", "down_since": ""}]},
    {"id": "park2", "name": "EP", "attractions": [{"id": "2", "down_since": ""}]},
]


def _fetch_results(monkeypatch, by_park):
    async def fetch(park):
        return by_park[park["id"]]
    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", fetch)


def test_every_park_failing_flags_a_network_issue(monkeypatch):
    from updater.shared import network_issues
    _fetch_results(monkeypatch, {"park1": None, "park2": None})
    update_parks_live_data(copy.deepcopy(TWO_PARKS))
    assert network_issues() is True


def test_one_park_getting_through_clears_the_network_issue(monkeypatch):
    from updater.shared import network_issues, note_network_result
    note_network_result(False)
    _fetch_results(monkeypatch, {"park1": None, "park2": []})
    update_parks_live_data(copy.deepcopy(TWO_PARKS))
    assert network_issues() is False


def test_no_fetchable_parks_leaves_the_network_flag_alone(monkeypatch):
    from updater.shared import network_issues, note_network_result
    note_network_result(False)
    _fetch_results(monkeypatch, {})
    update_parks_live_data([{"id": "park1", "name": "MK", "attractions": []}])
    assert network_issues() is True, "nothing was fetched, so nothing was learned"


def test_merge_live_data_marks_a_ride_last_written_by_rest():
    from api.disney_api import build_live_updates
    existing = [{"id": "1", "waitTime": 10, "status": "OPERATING", "down_since": "",
                 "lastUpdatedTs": "ws-time", "updateSource": "websocket"}]
    merge_live_data(existing, build_live_updates([{
        "id": "1", "entityType": "ATTRACTION", "status": "OPERATING",
        "lastUpdated": "rest-time", "queue": {"STANDBY": {"waitTime": 25}}}]))
    assert existing[0]["updateSource"] == "rest"
    assert existing[0]["lastUpdatedTs"] == "rest-time"


# ---- Newer data wins (preview WebSocket replays, late REST polls) ----

def _ride(ts, wait=20):
    return {"id": "a1", "name": "Ride", "status": "OPERATING", "waitTime": wait, "lastUpdatedTs": ts, "down_since": ""}


def test_merge_live_data_skips_an_update_older_than_what_the_ride_has():
    rides = [_ride("2026-10-04T16:30:00Z", wait=60)]
    merge_live_data(rides, [{"id": "a1", "status": "OPERATING", "waitTime": 45, "lastUpdatedTs": "2026-10-04T16:10:00Z"}])
    assert rides[0]["waitTime"] == 60


@pytest.mark.parametrize("existing_ts, new_ts", [
    ("2026-10-04T16:30:00Z", "2026-10-04T16:30:00Z"),       # the same time: applied
    ("2026-10-04T16:30:00Z", "2026-10-04T16:31:00+00:00"),  # newer
    ("", "2026-10-04T16:10:00Z"),                           # nothing yet
    ("old", "2026-10-04T16:10:00Z"),                        # unparseable existing
    ("2026-10-04T16:30:00Z", None),                         # update without a time
    ("2026-10-04T16:30:00", "2026-10-04T16:10:00Z"),        # naive vs aware: can't compare, applied
])
def test_merge_live_data_applies_updates_it_cant_prove_are_older(existing_ts, new_ts):
    rides = [_ride(existing_ts, wait=60)]
    merge_live_data(rides, [{"id": "a1", "status": "OPERATING", "waitTime": 45, "lastUpdatedTs": new_ts}])
    assert rides[0]["waitTime"] == 45


# ---- REST polling alongside the preview WebSocket ----


@pytest.mark.parametrize("healthy, last_fetch, now, expected", [
    (False, 100.0, 101.0, True),                                  # feed down: poll every cycle
    (True, None, 101.0, True),                                    # never polled
    (True, 100.0, 100.0 + REST_INTERVAL_WITH_LIVE_FEED_SECS - 1, False),
    (True, 100.0, 100.0 + REST_INTERVAL_WITH_LIVE_FEED_SECS, True),  # the 30-minute backstop
])
def test_rest_poll_due(monkeypatch, healthy, last_fetch, now, expected):
    monkeypatch.setattr("updater.data_updater.live_feed_healthy", lambda: healthy)
    assert rest_poll_due(last_fetch, now) is expected


def test_update_parks_live_data_without_fetch_live_makes_no_request(monkeypatch):
    calls = []

    async def fetch(park):
        calls.append(park)
        return []

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", fetch)
    parks = copy.deepcopy(DUMMY_PARKS)
    assert update_parks_live_data(parks, fetch_live=False) is parks
    assert calls == []


def _run_preview_updater(monkeypatch, snapshot_arrives, healthy):
    """One preview-mode cycle of live_data_updater; returns (REST fetches, status checks, startup wait)."""
    fetches, checks, waits = [], [], []

    async def fetch(park):
        fetches.append(park["id"])
        return []

    def wait(timeout_s):
        waits.append(timeout_s)
        return snapshot_arrives

    def fake_sleep(duration):
        raise KeyboardInterrupt()

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", fetch)
    monkeypatch.setattr("updater.data_updater.fetch_parks_and_attractions", lambda parks: copy.deepcopy(DUMMY_PARKS))
    monkeypatch.setattr("updater.data_updater.update_parks_operating_status",
                        lambda parks, fetch_schedules=True: checks.append(fetch_schedules) or parks)
    monkeypatch.setattr("updater.data_updater.wait_for_live_feed", wait)
    monkeypatch.setattr("updater.data_updater.live_feed_healthy", lambda: healthy)
    monkeypatch.setattr("updater.data_updater.time.sleep", fake_sleep)
    thread = threading.Thread(target=live_data_updater, args=([], 0, []),
                              kwargs={"use_websocket": True, "ws_protocol": "preview"}, daemon=True)
    thread.start()
    thread.join(timeout=2)
    return fetches, checks, waits


def test_preview_snapshot_replaces_the_startup_rest_fetch(monkeypatch):
    fetches, checks, waits = _run_preview_updater(monkeypatch, snapshot_arrives=True, healthy=True)
    assert waits == [LIVE_FEED_STARTUP_WAIT_SECS]
    assert fetches == []        # no startup fetch, and the first cycle skips too
    assert checks == [True]     # operating status and schedules still run every cycle


def test_preview_without_a_snapshot_falls_back_to_rest(monkeypatch):
    fetches, checks, _ = _run_preview_updater(monkeypatch, snapshot_arrives=False, healthy=False)
    assert fetches == [p["id"] for p in DUMMY_PARKS if p.get("attractions")]
    assert checks == [True]


def test_preview_polls_rest_when_the_feed_turns_unhealthy(monkeypatch):
    fetches, _, _ = _run_preview_updater(monkeypatch, snapshot_arrives=True, healthy=False)
    assert fetches == [p["id"] for p in DUMMY_PARKS if p.get("attractions")]


# ---- Live feed health (updater/shared.py) ----

def test_live_feed_healthy_needs_a_sync_and_a_recent_frame(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("updater.shared.time.monotonic", lambda: clock[0])
    assert shared.live_feed_healthy() is False
    shared.note_live_feed_frame()
    assert shared.live_feed_healthy() is False  # connected, not yet synced
    shared.note_live_feed_synced()
    assert shared.live_feed_healthy() is True
    clock[0] += shared.LIVE_FEED_SILENCE_SECS + 1
    assert shared.live_feed_healthy() is False  # silent too long
    shared.note_live_feed_frame()
    assert shared.live_feed_healthy() is True
    shared.note_live_feed_down()
    assert shared.live_feed_healthy() is False


def test_wait_for_live_feed_returns_once_synced():
    assert shared.wait_for_live_feed(0) is False
    shared.note_live_feed_synced()
    assert shared.wait_for_live_feed(0) is True
