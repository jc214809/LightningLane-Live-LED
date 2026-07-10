# tests/api/test_disney_api_full.py
import asyncio
import copy
import threading
from datetime import datetime, timedelta, timezone

import pytest
import requests

from api import disney_api
from api.disney_api import (
    get_park_location,
    fetch_park_schedule,
    fetch_list_of_disney_world_parks,
    fetch_parks_and_attractions,
    get_attraction_name,
    clean_park_name,
    is_special_event,
    determine_llmp_price,
    get_down_time,
    fetch_live_data_for_attraction,
    fetch_live_data,
    park_has_operating_attraction,
    update_parks_operating_status,
    handle_park_schedule_update,
    refresh_park_attractions,
    resolve_destination_id,
    resolve_parks_from_config,
    DISNEY_WORLD_DESTINATION_ID,
)

###########
# Helpers
###########
class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
    def json(self):
        return self._json
    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.RequestException(f"HTTP {self.status_code}")

# A dummy park list for tests.
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

###########
# Tests for resolve_destination_id
###########

def test_resolve_destination_id_passthrough_uuid(monkeypatch):
    # A valid UUID should be returned as-is without any HTTP call.
    called = []
    monkeypatch.setattr(requests, "get", lambda url, **kw: called.append(url) or None)
    result = resolve_destination_id(DISNEY_WORLD_DESTINATION_ID)
    assert result == DISNEY_WORLD_DESTINATION_ID
    assert called == []

def test_resolve_destination_id_by_name(monkeypatch):
    fake_destinations = {"destinations": [
        {"id": "abc-123", "name": "Cedar Point"},
        {"id": DISNEY_WORLD_DESTINATION_ID, "name": "Walt Disney World Resort"},
    ]}
    monkeypatch.setattr(requests, "get", lambda url, **kw: DummyResponse(fake_destinations, 200))
    assert resolve_destination_id("Cedar Point") == "abc-123"
    assert resolve_destination_id("walt disney world resort") == DISNEY_WORLD_DESTINATION_ID

def test_resolve_destination_id_not_found(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: DummyResponse({"destinations": []}, 200))
    assert resolve_destination_id("Nonexistent Park") is None

def test_resolve_destination_id_request_error(monkeypatch):
    monkeypatch.setattr(requests, "get",
                        lambda url, **kw: (_ for _ in ()).throw(requests.RequestException("err")))
    assert resolve_destination_id("Cedar Point") is None

###########
# Tests for resolve_parks_from_config
###########

FAKE_DESTINATIONS = {
    "destinations": [
        {
            "id": DISNEY_WORLD_DESTINATION_ID,
            "name": "Walt Disney World® Resort",
            "parks": [
                {"id": "mk-id", "name": "Magic Kingdom Park"},
                {"id": "ep-id", "name": "EPCOT"},
            ],
        },
        {
            "id": "cedar-dest-id",
            "name": "Cedar Point",
            "parks": [
                {"id": "cp-id", "name": "Cedar Point"},
                {"id": "cps-id", "name": "Cedar Point Shores"},
            ],
        },
    ]
}

FAKE_WDW_SCHEDULE = {
    "parks": [
        {"id": "mk-id", "name": "Magic Kingdom Park", "schedule": []},
        {"id": "ep-id", "name": "EPCOT", "schedule": []},
    ]
}

FAKE_CEDAR_SCHEDULE = {
    "parks": [
        {"id": "cp-id", "name": "Cedar Point", "schedule": []},
        {"id": "cps-id", "name": "Cedar Point Shores", "schedule": []},
    ]
}

def _make_fake_get(monkeypatch):
    def fake_get(url, **kwargs):
        if url.endswith("/destinations"):
            return DummyResponse(FAKE_DESTINATIONS, 200)
        elif DISNEY_WORLD_DESTINATION_ID in url and "schedule" in url:
            return DummyResponse(FAKE_WDW_SCHEDULE, 200)
        elif "cedar-dest-id" in url and "schedule" in url:
            return DummyResponse(FAKE_CEDAR_SCHEDULE, 200)
        else:
            return DummyResponse({"location": None}, 200)
    return fake_get

def test_resolve_parks_from_config_by_raw_name(monkeypatch):
    monkeypatch.setattr(requests, "get", _make_fake_get(monkeypatch))
    result = resolve_parks_from_config(["Cedar Point"])
    assert len(result) == 1
    assert result[0]["id"] == "cp-id"

def test_resolve_parks_from_config_by_cleaned_disney_name(monkeypatch):
    monkeypatch.setattr(requests, "get", _make_fake_get(monkeypatch))
    result = resolve_parks_from_config(["Magic Kingdom"])
    assert len(result) == 1
    assert result[0]["id"] == "mk-id"

def test_resolve_parks_from_config_cross_destination(monkeypatch):
    monkeypatch.setattr(requests, "get", _make_fake_get(monkeypatch))
    result = resolve_parks_from_config(["EPCOT", "Cedar Point"])
    ids = {p["id"] for p in result}
    assert ids == {"ep-id", "cp-id"}

def test_resolve_parks_from_config_empty_defaults_to_wdw(monkeypatch):
    monkeypatch.setattr(requests, "get", _make_fake_get(monkeypatch))
    result = resolve_parks_from_config([])
    ids = {p["id"] for p in result}
    assert "mk-id" in ids and "ep-id" in ids

def test_resolve_parks_from_config_no_match(monkeypatch):
    monkeypatch.setattr(requests, "get", _make_fake_get(monkeypatch))
    result = resolve_parks_from_config(["Nonexistent Park"])
    assert result == []

def test_resolve_parks_from_config_request_error(monkeypatch):
    monkeypatch.setattr(requests, "get",
                        lambda url, **kw: (_ for _ in ()).throw(requests.RequestException("err")))
    result = resolve_parks_from_config(["Cedar Point"])
    assert result == []

def test_resolve_parks_from_config_preserves_config_order(monkeypatch):
    monkeypatch.setattr(requests, "get", _make_fake_get(monkeypatch))
    result = resolve_parks_from_config(["Cedar Point", "EPCOT"])
    assert [p["id"] for p in result] == ["cp-id", "ep-id"]

    result2 = resolve_parks_from_config(["EPCOT", "Cedar Point"])
    assert [p["id"] for p in result2] == ["ep-id", "cp-id"]

###########
# Tests for HTTP Functions
###########

def test_get_park_location_success(monkeypatch):
    dummy_location = {"latitude": 28.3759, "longitude": -81.5494}
    monkeypatch.setattr(requests, "get", lambda url, **kwargs: DummyResponse({"location": dummy_location}, 200))
    result = get_park_location("dummy-park-id")
    assert result == dummy_location

def test_get_park_location_exception(monkeypatch):
    monkeypatch.setattr(requests, "get",
                        lambda url, **kwargs: (_ for _ in ()).throw(requests.RequestException("error")))
    result = get_park_location("dummy-park-id")
    assert result == []

def test_fetch_park_schedule_success(monkeypatch):
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    fake_schedule = [
        {"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"},
        {"date": yesterday_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"},
        {"date": "2000-01-01", "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}
    ]
    monkeypatch.setattr(requests, "get", lambda url, **kwargs: DummyResponse({"schedule": fake_schedule}, 200))
    result = fetch_park_schedule("dummy-park-id")
    for event in result:
        assert event["date"] in (today_str, yesterday_str)

def test_fetch_park_schedule_exception(monkeypatch):
    monkeypatch.setattr(requests, "get",
                        lambda url, **kwargs: (_ for _ in ()).throw(requests.RequestException("error")))
    result = fetch_park_schedule("dummy-park-id")
    assert result == []

def test_fetch_list_of_disney_world_parks_success(monkeypatch):
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    fake_world_schedule = {
        "parks": [
            {
                "id": "dummy-id",
                "name": "Magic Kingdom",
                "schedule": [{"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}]
            },
            {
                "id": "dummy-id-2",
                "name": "Water Park Fun",
                "schedule": [{"date": today_str, "type": "OPERATING", "openingTime": "10:00", "closingTime": "20:00"}]
            }
        ]
    }
    # For Disney World schedule URL, return parks data; otherwise, return location.
    def fake_get(url, **kwargs):
        if "e957da41-3552-4cf6-b636-5babc5cbc4e5" in url:
            return DummyResponse(fake_world_schedule, 200)
        else:
            return DummyResponse({"location": {"latitude": 28.3759, "longitude": -81.5494}}, 200)
    monkeypatch.setattr(requests, "get", fake_get)
    result = fetch_list_of_disney_world_parks()
    # Water parks should be filtered out. Only "Magic Kingdom" remains.
    assert len(result) == 1
    park = result[0]
    assert park["name"] == "Magic Kingdom"
    assert park["location"] == {"latitude": 28.3759, "longitude": -81.5494}

def test_fetch_list_of_disney_world_parks_exception(monkeypatch):
    monkeypatch.setattr(requests, "get",
                        lambda url, **kwargs: (_ for _ in ()).throw(requests.RequestException("error")))
    result = fetch_list_of_disney_world_parks()
    assert result == []

def test_fetch_parks_and_attractions_success(monkeypatch):
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    fake_parks_list = [{
        "id": "dummy-id",
        "name": "Magic Kingdom",
        "schedule": [{"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}],
        "weather": [],
        "location": {"latitude": 28.3759, "longitude": -81.5494}
    }]
    def fake_get(url, **kwargs):
        if "children" in url:
            return DummyResponse({"children": [{"id": "attr-1", "name": "Space Mountain", "entityType": "ATTRACTION"}]}, 200)
        elif "schedule" in url:
            return DummyResponse({"schedule": []}, 200)
        else:
            return DummyResponse({"location": {"latitude": 28.3759, "longitude": -81.5494}}, 200)
    monkeypatch.setattr(requests, "get", fake_get)
    # To avoid real weather calls, patch fetch_weather_data.
    monkeypatch.setattr(disney_api, "fetch_weather_data", lambda lat, lon: {"temp": "dummy"})
    result = fetch_parks_and_attractions(fake_parks_list)
    assert len(result) == 1
    park = result[0]
    assert "attractions" in park
    assert len(park["attractions"]) == 1
    attraction = park["attractions"][0]
    assert get_attraction_name({"name": "Space Mountain\u2122"}) == "Space Mountain"

def test_fetch_parks_and_attractions_includes_shows(monkeypatch):
    today_str = datetime.now().strftime('%Y-%m-%d')
    fake_parks_list = [{
        "id": "dummy-id",
        "name": "Animal Kingdom",
        "schedule": [{"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}],
        "weather": [],
        "location": {"latitude": 28.3600, "longitude": -81.5900}
    }]
    def fake_get(url, **kwargs):
        if "children" in url:
            return DummyResponse({"children": [
                {"id": "show-1", "name": "Bluey's Wild World at Conservation Station", "entityType": "SHOW"},
                {"id": "other-1", "name": "Flame Tree BBQ", "entityType": "RESTAURANT"},
            ]}, 200)
        return DummyResponse({}, 200)
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(disney_api, "fetch_weather_data", lambda lat, lon: {})
    result = fetch_parks_and_attractions(fake_parks_list)
    attractions = result[0]["attractions"]
    ids = [a["id"] for a in attractions]
    assert "show-1" in ids
    assert "other-1" not in ids

def test_fetch_parks_and_attractions_includes_destination_id(monkeypatch):
    today_str = datetime.now().strftime('%Y-%m-%d')
    fake_parks_list = [{
        "id": "dummy-id",
        "name": "Magic Kingdom",
        "destination_id": "dest-abc",
        "schedule": [{"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}],
        "weather": [],
        "location": {"latitude": 28.3759, "longitude": -81.5494},
    }]

    def fake_get(url, **kwargs):
        if "children" in url:
            return DummyResponse({"children": [
                {"id": "attr-1", "name": "Space Mountain", "entityType": "ATTRACTION"}
            ]}, 200)
        return DummyResponse({}, 200)

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(disney_api, "fetch_weather_data", lambda lat, lon: {})
    result = fetch_parks_and_attractions(fake_parks_list)
    assert len(result) == 1
    assert result[0]["destination_id"] == "dest-abc"


def test_fetch_parks_and_attractions_exception(monkeypatch):
    fake_parks_list = [{
        "id": "dummy-id",
        "name": "Magic Kingdom",
        "schedule": [{"date": "2025-01-01", "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}],
        "weather": [],
        "location": {"latitude": 28.3759, "longitude": -81.5494}
    }]
    def fake_get(url, **kwargs):
        raise requests.RequestException("error")
    monkeypatch.setattr(requests, "get", fake_get)
    result = fetch_parks_and_attractions(fake_parks_list)
    # In case of error, the park is skipped, so expect an empty list.
    assert result == []

###########
# Tests for utility functions in disney_api
###########
def test_get_attraction_name():
    # Test that unwanted characters/substrings are removed.
    item = {"name": "Ride™ – An Original at Mickey's Not-So-Scary Halloween Party"}
    clean_name = get_attraction_name(item)
    # Expect trademark symbol removed, "–" replaced with "-", and the trailing text removed.
    assert "™" not in clean_name
    assert "–" not in clean_name
    assert "Halloween" not in clean_name

def test_clean_park_name():
    assert clean_park_name("Disney's Animal Kingdom Theme Park") == "Animal Kingdom"
    assert clean_park_name("Magic Kingdom Park") == "Magic Kingdom"
    assert clean_park_name("Disney's Hollywood Studios") == "Hollywood Studios"
    assert clean_park_name("EPCOT") == "EPCOT"

def test_is_special_event():
    schedule = [{
        "type": "TICKETED_EVENT",
        "description": "Special ticketed event extended evening"
    }]
    assert is_special_event(schedule) is True
    schedule = [{
        "type": "TICKETED_EVENT",
        "description": "Regular event"
    }]
    assert is_special_event(schedule) is False

def test_determine_llmp_price():
    operating_event = {
        "purchases": [
            {"name": "Lightning Lane Multi Pass", "price": {"formatted": "$20"}},
            {"name": "Other", "price": {"formatted": "$10"}}
        ]
    }
    assert determine_llmp_price(operating_event) == "$20"
    operating_event = {"purchases": []}
    assert determine_llmp_price(operating_event) == ""

def test_get_down_time_valid():
    # Test get_down_time by computing a known difference.
    # Create a timestamp 30 minutes ago.
    past = datetime.now(timezone.utc) - timedelta(minutes=30)
    past_iso = past.strftime('%Y-%m-%dT%H:%M:%SZ')
    minutes = get_down_time(past_iso)
    # Allow a range since actual computation might vary slightly.
    assert 29 <= minutes <= 31

def test_get_down_time_with_milliseconds():
    past = datetime.now(timezone.utc) - timedelta(minutes=45)
    past_iso = past.strftime('%Y-%m-%dT%H:%M:%S.') + f"{past.microsecond // 1000:03d}Z"
    minutes = get_down_time(past_iso)
    assert 44 <= minutes <= 46

def test_get_down_time_invalid():
    result = get_down_time("invalid-date")
    assert result is None

def test_get_down_time_none_input():
    result = get_down_time(None)
    assert result is None

def test_get_down_time_empty_string():
    result = get_down_time("")
    assert result is None

###########
# Asynchronous Live Data Tests
###########
@pytest.mark.asyncio
async def test_fetch_live_data_for_attraction_success(monkeypatch):
    # Dummy live entry with status "OPERATING" that should update waitTime.
    dummy_live_entry = {
        "lastUpdated": "2023-10-01T12:00:00Z",
        "status": "OPERATING",
        "queue": {"STANDBY": {"waitTime": 45}},
        "entityType": "ATTRACTION"
    }

    # Define a fake response that implements async context manager.
    class FakeResponse:
        def __init__(self, json_data, status=200):
            self._json = json_data
            self.status = status

        async def json(self):
            return self._json

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    # Define a FakeSession with a normal get() method returning FakeResponse.
    class FakeSession:
        def get(self, url, **kwargs):
            return FakeResponse({"liveData": [dummy_live_entry]}, 200)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    # Create a dummy attraction with blank waitTime values.
    dummy_attraction = {
        "id": "attr-1",
        "name": "Space Mountain",
        "waitTime": '',
        "status": '',
        "lastUpdatedTs": ''
    }

    from api.disney_api import fetch_live_data_for_attraction
    result = await fetch_live_data_for_attraction(FakeSession(), dummy_attraction)

    # Assert that waitTime was updated to 45 (as an int),
    # and that status and lastUpdatedTs are updated properly.
    assert result["waitTime"] == 45, f"Expected waitTime 45, got {result['waitTime']}"
    assert result["status"] == "OPERATING"
    assert result["lastUpdatedTs"] == "2023-10-01T12:00:00Z"

@pytest.mark.asyncio
async def test_fetch_live_data_for_attraction_standby_takes_priority_over_boarding_group():
    dummy_live_entry = {
        "lastUpdated": "2023-10-01T12:00:00Z",
        "status": "OPERATING",
        "queue": {
            "STANDBY": {"waitTime": 30},
            "BOARDING_GROUP": {
                "currentGroupStart": 1,
                "currentGroupEnd": 50,
                "allocationStatus": "OPEN",
                "estimatedWait": None,
                "nextAllocationTime": None
            }
        },
        "entityType": "ATTRACTION"
    }

    class FakeResponse:
        status = 200
        async def json(self): return {"liveData": [dummy_live_entry]}
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    class FakeSession:
        def get(self, url, **kwargs): return FakeResponse()
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    dummy_attraction = {"id": "attr-3", "name": "Test Ride", "waitTime": "", "status": "", "lastUpdatedTs": ""}
    from api.disney_api import fetch_live_data_for_attraction
    result = await fetch_live_data_for_attraction(FakeSession(), dummy_attraction)
    assert result["waitTime"] == 30

@pytest.mark.asyncio
async def test_fetch_live_data_for_attraction_boarding_group_range():
    dummy_live_entry = {
        "lastUpdated": "2023-10-01T12:00:00Z",
        "status": "OPERATING",
        "queue": {
            "BOARDING_GROUP": {
                "currentGroupStart": 1,
                "currentGroupEnd": 50,
                "allocationStatus": "OPEN",
                "estimatedWait": None,
                "nextAllocationTime": None
            }
        },
        "entityType": "ATTRACTION"
    }

    class FakeResponse:
        status = 200
        async def json(self): return {"liveData": [dummy_live_entry]}
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    class FakeSession:
        def get(self, url, **kwargs): return FakeResponse()
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    dummy_attraction = {"id": "attr-2", "name": "Tron", "waitTime": "", "status": "", "lastUpdatedTs": ""}
    from api.disney_api import fetch_live_data_for_attraction
    result = await fetch_live_data_for_attraction(FakeSession(), dummy_attraction)
    assert result["waitTime"] == "Groups 1-50"
    assert result["status"] == "OPERATING"

@pytest.mark.asyncio
async def test_fetch_live_data_for_attraction_boarding_group_closed():
    dummy_live_entry = {
        "lastUpdated": "2023-10-01T12:00:00Z",
        "status": "OPERATING",
        "queue": {
            "BOARDING_GROUP": {
                "currentGroupStart": None,
                "currentGroupEnd": None,
                "allocationStatus": "CLOSED",
                "estimatedWait": None,
                "nextAllocationTime": None
            }
        },
        "entityType": "ATTRACTION"
    }

    class FakeResponse:
        status = 200
        async def json(self): return {"liveData": [dummy_live_entry]}
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    class FakeSession:
        def get(self, url, **kwargs): return FakeResponse()
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    dummy_attraction = {"id": "attr-2", "name": "Tron", "waitTime": "", "status": "", "lastUpdatedTs": ""}
    from api.disney_api import fetch_live_data_for_attraction
    result = await fetch_live_data_for_attraction(FakeSession(), dummy_attraction)
    assert result["waitTime"] is None

@pytest.mark.asyncio
async def test_fetch_live_data_exception(monkeypatch):
    class FakeSession:
        async def get(self, url, **kwargs):
            raise Exception("Live data error")
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
    monkeypatch.setattr("api.disney_api.aiohttp.ClientSession", lambda **kw: FakeSession())
    dummy_attractions = [{
        "id": "attr-1",
        "name": "Space Mountain",
        "waitTime": '',
        "status": '',
        "lastUpdatedTs": ''
    }]
    result = await fetch_live_data(dummy_attractions)
    assert result[0]["waitTime"] == ''
    assert result[0]["status"] == ''
    assert result[0]["lastUpdatedTs"] == ''

###########
# Tests for Park Operating Status & Schedule Update
###########
def test_park_has_operating_attraction(monkeypatch):
    park = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": "15", "status": "OPERATING"},
            {"name": "Ride B", "waitTime": "", "status": "CLOSED"}
        ]
    }
    assert park_has_operating_attraction(park) is True
    park["attractions"][0]["status"] = "CLOSED"
    assert park_has_operating_attraction(park) is False

def test_handle_park_schedule_update(monkeypatch):
    park = {"name": "Test Park", "id": "dummy-id", "schedule": []}
    # Patch fetch_park_schedule to return a dummy schedule with an OPERATING event.
    dummy_schedule = [{
        "type": "OPERATING", 
        "openingTime": "09:00", 
        "closingTime": "22:00",
        "purchases": [{"name": "Lightning Lane Multi Pass", "price": {"formatted": "$25"}}]
    }]
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: dummy_schedule)
    # Patch is_special_event to return True.
    monkeypatch.setattr("api.disney_api.is_special_event", lambda sch: True)
    # Capture debug info if desired.
    from api.disney_api import handle_park_schedule_update
    handle_park_schedule_update(True, park)
    # Verify that schedule is updated, and llmpPrice and specialTicketedEvent are set.
    assert park["schedule"] == dummy_schedule
    assert park["llmpPrice"] == "$25"
    assert park["specialTicketedEvent"] is True
    assert park["openingTime"] == "09:00"
    assert park["closingTime"] == "22:00"

def test_handle_park_schedule_update_calls_refresh(monkeypatch):
    park = {"name": "Test Park", "id": "dummy-id", "schedule": [], "attractions": []}
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: [])
    refreshed = []
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: refreshed.append(p))
    handle_park_schedule_update(True, park)
    assert refreshed == [park]

def test_handle_park_schedule_update_no_refresh_when_already_operating(monkeypatch):
    park = {"name": "Test Park", "id": "dummy-id", "schedule": [], "operating": True, "attractions": []}
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: [])
    refreshed = []
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: refreshed.append(p))
    handle_park_schedule_update(True, park)
    assert refreshed == []

###########
# Tests for refresh_park_attractions
###########

def _make_children_response(children):
    return DummyResponse({"children": children}, 200)

def test_refresh_park_attractions_updates_name(monkeypatch):
    park = {
        "id": "park-1", "name": "Test Park",
        "attractions": [{"id": "a1", "name": "Old Name", "waitTime": 10, "status": "OPERATING", "lastUpdatedTs": "ts"}]
    }
    monkeypatch.setattr(requests, "get", lambda url, **kw: _make_children_response([
        {"id": "a1", "name": "New Name", "entityType": "ATTRACTION"}
    ]))
    refresh_park_attractions(park)
    assert park["attractions"][0]["name"] == "New Name"
    assert park["attractions"][0]["waitTime"] == 10  # live data preserved

def test_refresh_park_attractions_adds_new(monkeypatch):
    park = {
        "id": "park-1", "name": "Test Park",
        "attractions": [{"id": "a1", "name": "Ride A", "waitTime": 5, "status": "OPERATING", "lastUpdatedTs": ""}]
    }
    monkeypatch.setattr(requests, "get", lambda url, **kw: _make_children_response([
        {"id": "a1", "name": "Ride A", "entityType": "ATTRACTION"},
        {"id": "a2", "name": "Ride B", "entityType": "ATTRACTION"},
    ]))
    refresh_park_attractions(park)
    ids = [a["id"] for a in park["attractions"]]
    assert "a1" in ids and "a2" in ids
    new = next(a for a in park["attractions"] if a["id"] == "a2")
    assert new["waitTime"] == ""

def test_refresh_park_attractions_removes_dropped(monkeypatch):
    park = {
        "id": "park-1", "name": "Test Park",
        "attractions": [
            {"id": "a1", "name": "Ride A", "waitTime": 5, "status": "OPERATING", "lastUpdatedTs": ""},
            {"id": "a2", "name": "Ride B", "waitTime": 0, "status": "CLOSED", "lastUpdatedTs": ""},
        ]
    }
    monkeypatch.setattr(requests, "get", lambda url, **kw: _make_children_response([
        {"id": "a1", "name": "Ride A", "entityType": "ATTRACTION"},
    ]))
    refresh_park_attractions(park)
    assert len(park["attractions"]) == 1
    assert park["attractions"][0]["id"] == "a1"

def test_refresh_park_attractions_request_error(monkeypatch):
    park = {
        "id": "park-1", "name": "Test Park",
        "attractions": [{"id": "a1", "name": "Ride A", "waitTime": 5, "status": "OPERATING", "lastUpdatedTs": ""}]
    }
    monkeypatch.setattr(requests, "get",
                        lambda url, **kw: (_ for _ in ()).throw(requests.RequestException("err")))
    refresh_park_attractions(park)
    assert len(park["attractions"]) == 1  # unchanged on error

def test_update_parks_operating_status(monkeypatch):
    park = {
        "name": "Test Park",
        "attractions": [{
            "name": "Ride A",
            "waitTime": "10",
            "status": "OPERATING"
        }],
        "id": "dummy-id",
        "schedule": []
    }
    parks = [park]
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: [{
        "type": "OPERATING",
        "openingTime": "09:00",
        "closingTime": "22:00"
    }])
    monkeypatch.setattr("api.disney_api.fetch_weather_data", lambda lat, lon: {"temp": "dummy"})
    updated = update_parks_operating_status(copy.deepcopy(parks))
    assert updated[0]["operating"] is True