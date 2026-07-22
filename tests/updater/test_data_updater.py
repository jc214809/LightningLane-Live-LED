import copy
import threading

from updater.data_updater import (
    merge_live_data,
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


def test_update_parks_live_data_websocket_skips_http_fetch(monkeypatch):
    """When use_websocket=True, fetch_live_data must not be called."""
    called = []

    async def should_not_be_called(attractions):
        called.append(True)
        return []

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", should_not_be_called)

    parks_copy = copy.deepcopy(DUMMY_PARKS)
    update_parks_live_data(parks_copy, use_websocket=True)

    assert called == [], "fetch_live_data should not be called when use_websocket=True"


def test_update_parks_live_data_no_websocket_calls_http_fetch(monkeypatch):
    """When use_websocket=False (default), fetch_live_data must be called."""
    called = []

    async def dummy_fetch_live_data(park):
        called.append(True)
        return []

    monkeypatch.setattr("updater.data_updater.fetch_park_live_data", dummy_fetch_live_data)

    parks_copy = copy.deepcopy(DUMMY_PARKS)
    update_parks_live_data(parks_copy, use_websocket=False)

    assert called == [True], "fetch_live_data should be called when use_websocket=False"


def test_live_data_updater_websocket_does_initial_fetch_then_skips_polling(monkeypatch):
    """
    live_data_updater with use_websocket=True must call fetch_live_data once for the
    initial population, then skip it in the polling loop.
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

    # fetch_live_data called exactly once (initial fetch), not again in the loop
    assert len(fetch_call_count) == 1, "fetch_live_data should be called once for the initial fetch"
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