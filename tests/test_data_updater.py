import copy

from updater.data_updater import merge_live_data


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
