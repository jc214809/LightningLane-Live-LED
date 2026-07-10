import copy
from unittest.mock import patch

from updater.websocket_updater import _apply_live_update

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
    mock_update.assert_called_once_with([parks[0]])


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


# --- no match ---

def test_unknown_entity_id_is_ignored():
    parks = _parks_with_attr()
    msg = _make_livedata_msg(entity_id="unknown-id")
    _apply_live_update(msg, parks)
    assert parks[0]["attractions"][0]["waitTime"] == 20
    assert parks[0]["attractions"][0]["lastUpdatedTs"] == "old"
