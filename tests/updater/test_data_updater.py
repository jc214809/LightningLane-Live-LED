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
    using live data. For testing, we patch updater.data_updater.fetch_live_data to return dummy live data.
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
    monkeypatch.setattr("updater.data_updater.fetch_live_data", dummy_fetch_live_data)

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
    after one iteration. We patch updater.data_updater.fetch_live_data to return updated live data,
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
    monkeypatch.setattr("updater.data_updater.fetch_live_data", dummy_fetch_live_data)

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


def test_merge_live_data_appends_new():
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
    assert len(result) == 2
    ids = {a["id"] for a in result}
    assert ids == {"1", "2"}
    attr2 = next(a for a in result if a["id"] == "2")
    assert attr2["waitTime"] == 5
    assert attr2["status"] == "OPERATING"
    assert attr2["lastUpdatedTs"] == "new2"


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

    monkeypatch.setattr("updater.data_updater.fetch_live_data", dummy_fetch_live_data)

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

    monkeypatch.setattr("updater.data_updater.fetch_live_data", dummy_fetch_live_data)

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