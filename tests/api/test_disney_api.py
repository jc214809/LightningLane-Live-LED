# tests/api/test_disney_api_full.py
import asyncio
import copy
import threading
from datetime import datetime, timedelta, timezone

import pytest
import requests

from api import disney_api
from api.disney_api import (
    fetch_park_schedule,
    fetch_list_of_disney_world_parks,
    fetch_parks_and_attractions,
    get_attraction_name,
    clean_park_name,
    determine_llmp_price,
    get_down_time,
    fetch_park_live_data,
    parse_queue_wait,
    build_live_updates,
    parse_forecast,
    forecast_wait_now,
    parse_showtimes,
    show_start_due,
    actual_park_closing_time,
    operating_and_why,
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

def test_resolve_destination_id_passes_timeout(monkeypatch):
    """Regression test: every request to the ThemeParks Wiki API must pass a
    timeout, so a slow/unreachable API fails fast instead of hanging the
    caller -- resolve_parks_from_config runs synchronously on bullpen's
    render/update thread when used as a plugin."""
    calls = []
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: calls.append(kw) or DummyResponse({"destinations": []}, 200),
    )
    resolve_destination_id("Cedar Point")
    assert calls and calls[0].get("timeout") == disney_api.REQUEST_TIMEOUT_SECONDS

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

def test_get_park_entity_info_success(monkeypatch):
    from api.disney_api import get_park_entity_info
    dummy_location = {"latitude": 28.3759, "longitude": -81.5494}
    monkeypatch.setattr(requests, "get", lambda url, **kwargs: DummyResponse(
        {"location": dummy_location, "timezone": "America/New_York"}, 200))
    location, tz = get_park_entity_info("dummy-park-id")
    assert location == dummy_location
    assert tz == "America/New_York"

def test_get_park_entity_info_exception(monkeypatch):
    from api.disney_api import get_park_entity_info
    monkeypatch.setattr(requests, "get",
                        lambda url, **kwargs: (_ for _ in ()).throw(requests.RequestException("error")))
    location, tz = get_park_entity_info("dummy-park-id")
    assert location == []
    assert tz is None

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

def test_fetch_parks_and_attractions_carries_timezone_through(monkeypatch):
    today_str = datetime.now().strftime('%Y-%m-%d')
    fake_parks_list = [{
        "id": "dummy-id",
        "name": "Magic Kingdom",
        "schedule": [{"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"}],
        "weather": [],
        "location": {"latitude": 28.3759, "longitude": -81.5494},
        "timezone": "America/New_York",
    }]
    def fake_get(url, **kwargs):
        if "children" in url:
            return DummyResponse({"children": []}, 200)
        return DummyResponse({}, 200)
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(disney_api, "fetch_weather_data", lambda lat, lon: {})
    result = fetch_parks_and_attractions(fake_parks_list)
    assert result[0]["timezone"] == "America/New_York"

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
# Live Data Tests (per-park endpoint)
###########

def test_parse_queue_wait_standby():
    assert parse_queue_wait({"STANDBY": {"waitTime": 45}}) == 45

def test_parse_queue_wait_standby_takes_priority_over_boarding_group():
    queue = {
        "STANDBY": {"waitTime": 30},
        "BOARDING_GROUP": {"currentGroupStart": 1, "currentGroupEnd": 50},
    }
    assert parse_queue_wait(queue) == 30

def test_parse_queue_wait_boarding_group_range():
    queue = {"BOARDING_GROUP": {"currentGroupStart": 1, "currentGroupEnd": 50}}
    assert parse_queue_wait(queue) == "Groups 1-50"

def test_parse_queue_wait_boarding_group_open_ended():
    queue = {"BOARDING_GROUP": {"currentGroupStart": 10, "currentGroupEnd": None}}
    assert parse_queue_wait(queue) == "Group 10+"

def test_parse_queue_wait_boarding_group_closed():
    queue = {"BOARDING_GROUP": {"currentGroupStart": None, "currentGroupEnd": None}}
    assert parse_queue_wait(queue) is None

def test_parse_queue_wait_empty_or_null_blocks():
    assert parse_queue_wait({}) is None
    assert parse_queue_wait({"STANDBY": None, "BOARDING_GROUP": None}) is None


def test_build_live_updates_operating_attraction():
    entries = [{
        "id": "attr-1",
        "entityType": "ATTRACTION",
        "status": "OPERATING",
        "lastUpdated": "2023-10-01T12:00:00Z",
        "queue": {"STANDBY": {"waitTime": 45}},
    }]
    updates = build_live_updates(entries)
    assert updates == [{
        "id": "attr-1",
        "status": "OPERATING",
        "lastUpdatedTs": "2023-10-01T12:00:00Z",
        "updateSource": "rest",
        "waitTime": 45,
    }]

def test_build_live_updates_filters_non_attraction_entities():
    entries = [
        {"id": "r-1", "entityType": "RESTAURANT", "status": "OPERATING", "lastUpdated": "ts"},
        {"id": "p-1", "entityType": "PARK", "status": "OPERATING", "lastUpdated": "ts"},
        {"id": "s-1", "entityType": "SHOW", "status": "OPERATING", "lastUpdated": "ts", "queue": {}},
    ]
    updates = build_live_updates(entries)
    assert [u["id"] for u in updates] == ["s-1"]

def test_build_live_updates_down_attraction_omits_wait_time():
    # waitTime for DOWN attractions is derived later in merge_live_data from
    # the persisted down_since, not from the raw per-poll lastUpdated here.
    entries = [{
        "id": "attr-1", "entityType": "ATTRACTION", "status": "DOWN",
        "lastUpdated": "2023-10-01T12:00:00Z",
    }]
    updates = build_live_updates(entries)
    assert "waitTime" not in updates[0]
    assert updates[0]["status"] == "DOWN"

def test_build_live_updates_down_show_omits_wait_time():
    entries = [{
        "id": "show-1", "entityType": "SHOW", "status": "DOWN",
        "lastUpdated": "2023-10-01T12:00:00Z",
    }]
    updates = build_live_updates(entries)
    assert "waitTime" not in updates[0]
    assert updates[0]["status"] == "DOWN"

def test_build_live_updates_closed_omits_wait_time():
    """CLOSED/REFURBISHMENT keep the last known wait time via omission."""
    for status in ("CLOSED", "REFURBISHMENT"):
        entries = [{
            "id": "attr-1", "entityType": "ATTRACTION", "status": status,
            "lastUpdated": "ts",
        }]
        updates = build_live_updates(entries)
        assert "waitTime" not in updates[0]
        assert updates[0]["status"] == status

def test_build_live_updates_missing_queue_fields():
    entries = [{
        "id": "attr-1", "entityType": "ATTRACTION", "status": "OPERATING",
        "lastUpdated": "ts",
    }]
    updates = build_live_updates(entries)
    assert updates[0]["waitTime"] is None


class _FakeLiveResponse:
    def __init__(self, json_data=None, status=200, raise_on_json=False):
        self._json = json_data
        self.status = status
        self._raise_on_json = raise_on_json

    async def json(self):
        if self._raise_on_json:
            raise ValueError("bad json")
        return self._json

    async def __aenter__(self): return self
    async def __aexit__(self, *a): pass


class _FakeLiveSession:
    def __init__(self, response=None, raise_on_get=False):
        self._response = response
        self._raise_on_get = raise_on_get
        self.requested_urls = []

    def get(self, url, **kwargs):
        self.requested_urls.append(url)
        if self._raise_on_get:
            raise Exception("network error")
        return self._response

    async def __aenter__(self): return self
    async def __aexit__(self, *a): pass


DUMMY_PARK = {"id": "park-1", "name": "Magic Kingdom"}

@pytest.mark.asyncio
async def test_fetch_park_live_data_success(monkeypatch):
    live = [{
        "id": "attr-1", "entityType": "ATTRACTION", "status": "OPERATING",
        "lastUpdated": "2023-10-01T12:00:00Z",
        "queue": {"STANDBY": {"waitTime": 45}},
    }]
    session = _FakeLiveSession(_FakeLiveResponse({"liveData": live}))
    monkeypatch.setattr("api.disney_api.aiohttp.ClientSession", lambda **kw: session)
    updates = await fetch_park_live_data(DUMMY_PARK)
    assert updates[0]["waitTime"] == 45
    assert session.requested_urls == ["https://api.themeparks.wiki/v1/entity/park-1/live"]

@pytest.mark.asyncio
async def test_fetch_park_live_data_rate_limited_returns_none(monkeypatch):
    session = _FakeLiveSession(_FakeLiveResponse(status=429))
    monkeypatch.setattr("api.disney_api.aiohttp.ClientSession", lambda **kw: session)
    assert await fetch_park_live_data(DUMMY_PARK) is None

@pytest.mark.asyncio
async def test_fetch_park_live_data_network_error_returns_none(monkeypatch):
    session = _FakeLiveSession(raise_on_get=True)
    monkeypatch.setattr("api.disney_api.aiohttp.ClientSession", lambda **kw: session)
    assert await fetch_park_live_data(DUMMY_PARK) is None

@pytest.mark.asyncio
async def test_fetch_park_live_data_bad_json_returns_none(monkeypatch):
    session = _FakeLiveSession(_FakeLiveResponse(raise_on_json=True))
    monkeypatch.setattr("api.disney_api.aiohttp.ClientSession", lambda **kw: session)
    assert await fetch_park_live_data(DUMMY_PARK) is None

@pytest.mark.asyncio
async def test_fetch_park_live_data_missing_livedata_key(monkeypatch):
    session = _FakeLiveSession(_FakeLiveResponse({"id": "park-1"}))
    monkeypatch.setattr("api.disney_api.aiohttp.ClientSession", lambda **kw: session)
    assert await fetch_park_live_data(DUMMY_PARK) == []

###########
# Tests for Park Operating Status & Schedule Update
###########
def _open(park, now=None):
    return operating_and_why(park, now)[0]

def _fresh_ts(minutes_ago=0):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()

def test_operating_without_a_schedule(monkeypatch):
    park = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": "15", "status": "OPERATING", "lastUpdatedTs": _fresh_ts()},
            {"name": "Ride B", "waitTime": "", "status": "CLOSED", "lastUpdatedTs": _fresh_ts()}
        ]
    }
    assert _open(park) is True
    park["attractions"][0]["status"] = "CLOSED"
    assert _open(park) is False

def test_operating_without_a_schedule_stale_not_counted(monkeypatch):
    park = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": "15", "status": "OPERATING", "lastUpdatedTs": _fresh_ts(minutes_ago=30)},
        ]
    }
    assert _open(park) is False

def test_operating_without_a_schedule_freshness_boundary(monkeypatch):
    """Pin the _ATTRACTION_FRESHNESS_MINUTES=20 cutoff: just inside counts as fresh,
    just outside doesn't. Guards against a silent off-by-one if the constant changes."""
    park_fresh = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": "15", "status": "OPERATING", "lastUpdatedTs": _fresh_ts(minutes_ago=19)},
        ]
    }
    assert _open(park_fresh) is True

    park_stale = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": "15", "status": "OPERATING", "lastUpdatedTs": _fresh_ts(minutes_ago=21)},
        ]
    }
    assert _open(park_stale) is False

def test_operating_without_a_schedule_fresh_past_closing_time(monkeypatch):
    """Without a schedule, the stored regular closingTime isn't consulted: a fresh OPERATING
    ride past it (extended hours) still opens the park."""
    past_closing = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    park = {
        "name": "Test Park",
        "closingTime": past_closing,
        "attractions": [
            {"name": "After Hours Ride", "waitTime": "15", "status": "OPERATING", "lastUpdatedTs": _fresh_ts()},
        ]
    }
    assert _open(park) is True

# ---- Actual park closing time: the park day's last close, party included ----

def _entry(date, kind, opens, closes, description=""):
    return {"date": date, "type": kind, "description": description,
            "openingTime": opens, "closingTime": closes}

# Magic Kingdom's real shape (2026-10-04), with the party running until 1am.
PARTY_NIGHT = [
    _entry("2026-10-04", "TICKETED_EVENT", "2026-10-04T07:30:00-04:00", "2026-10-04T08:00:00-04:00", "Early Entry"),
    _entry("2026-10-04", "OPERATING", "2026-10-04T08:00:00-04:00", "2026-10-04T18:00:00-04:00"),
    _entry("2026-10-04", "TICKETED_EVENT", "2026-10-04T19:00:00-04:00", "2026-10-05T01:00:00-04:00",
           "Special Ticketed Event"),
]
NEXT_DAY = [
    _entry("2026-10-05", "TICKETED_EVENT", "2026-10-05T08:30:00-04:00", "2026-10-05T09:00:00-04:00", "Early Entry"),
    _entry("2026-10-05", "OPERATING", "2026-10-05T09:00:00-04:00", "2026-10-05T23:00:00-04:00"),
]


def _at(when):
    return datetime.fromisoformat(when)


def _park(schedule, last_updated="2026-10-04T18:30:00-04:00"):
    """A park with one OPERATING ride whose live data last changed at last_updated."""
    return {"name": "Magic Kingdom", "schedule": schedule,
            "attractions": [{"name": "Space Mountain", "waitTime": "40", "status": "OPERATING",
                             "lastUpdatedTs": last_updated}]}


@pytest.mark.parametrize("now, expected", [
    ("2026-10-04T12:00:00-04:00", "2026-10-05T01:00:00-04:00"),  # the party's close, not 6pm
    ("2026-10-04T18:30:00-04:00", "2026-10-05T01:00:00-04:00"),  # between regular close and party
    ("2026-10-05T00:30:00-04:00", "2026-10-05T01:00:00-04:00"),  # after midnight: still Oct 4's day
    ("2026-10-05T03:00:00-04:00", "2026-10-05T01:00:00-04:00"),  # Oct 5 hasn't opened yet
    ("2026-10-05T10:00:00-04:00", "2026-10-05T23:00:00-04:00"),  # Oct 5 is now the day in progress
])
def test_actual_park_closing_time_is_the_park_days_last_close(now, expected):
    park = {"schedule": PARTY_NIGHT + NEXT_DAY}
    assert actual_park_closing_time(park, _at(now)) == _at(expected)


def test_actual_park_closing_time_normal_night_is_the_regular_close():
    park = {"schedule": NEXT_DAY}
    assert actual_park_closing_time(park, _at("2026-10-05T12:00:00-04:00")) == _at("2026-10-05T23:00:00-04:00")


@pytest.mark.parametrize("schedule", [
    [],
    None,
    [{"type": "OPERATING", "date": "2026-10-04", "openingTime": "09:00", "closingTime": "22:00"}],  # no dates
    [{"type": "OPERATING", "date": "2026-10-04"}],  # no times at all
    [_entry("2026-10-04", "OPERATING", "2026-10-04T09:00:00", "2026-10-04T22:00:00")],  # no timezone
])
def test_actual_park_closing_time_none_without_a_usable_schedule(schedule):
    assert actual_park_closing_time({"schedule": schedule}, _at("2026-10-04T12:00:00-04:00")) is None


def test_park_open_after_midnight_until_the_party_ends():
    park = _park(PARTY_NIGHT, last_updated="2026-10-05T00:25:00-04:00")
    assert _open(park, _at("2026-10-05T00:30:00-04:00")) is True


def test_park_closes_at_the_actual_closing_time():
    park = _park(PARTY_NIGHT, last_updated="2026-10-05T00:58:00-04:00")
    assert _open(park, _at("2026-10-05T00:59:00-04:00")) is True
    assert _open(park, _at("2026-10-05T01:00:00-04:00")) is False


def test_schedule_decides_whatever_the_rides_say():
    """Within its hours a park is open with every ride CLOSED (the 6-7pm gap before a party),
    and outside them closed with rides still OPERATING."""
    park = _park(PARTY_NIGHT)
    park["attractions"][0]["status"] = "CLOSED"
    assert _open(park, _at("2026-10-04T18:30:00-04:00")) is True
    park["attractions"][0].update(status="OPERATING", lastUpdatedTs="2026-10-05T01:30:00-04:00")
    assert _open(park, _at("2026-10-05T01:31:00-04:00")) is False


def test_early_entry_opens_the_park_day():
    park = _park(NEXT_DAY, last_updated="2026-10-05T05:00:00-04:00")
    assert _open(park, _at("2026-10-05T08:29:00-04:00")) is False
    assert _open(park, _at("2026-10-05T08:30:00-04:00")) is True


@pytest.mark.parametrize("schedule, now, expected", [
    (PARTY_NIGHT, "2026-10-04T18:30:00-04:00", (True, "schedule: open until 01:00")),
    (PARTY_NIGHT, "2026-10-05T02:00:00-04:00", (False, "schedule: closed at 01:00")),
    (NEXT_DAY, "2026-10-05T06:00:00-04:00", (False, "schedule: not open yet")),
    ([], "2026-10-04T18:31:00-04:00",
     (True, "no usable schedule; a ride is operating with live data from the last 20 min")),
    ([], "2026-10-04T19:00:00-04:00",
     (False, "no usable schedule; no ride is operating with live data from the last 20 min")),
])
def test_operating_and_why_says_which_rule_decided(schedule, now, expected):
    assert operating_and_why(_park(schedule), _at(now)) == expected


def test_park_closed_after_the_actual_closing_time_even_with_fresh_operating_rides():
    """The stuck-open park: the feed still says OPERATING, updated a minute ago, after the party."""
    park = _park(PARTY_NIGHT, last_updated="2026-10-05T01:44:00-04:00")
    assert _open(park, _at("2026-10-05T01:45:00-04:00")) is False


def test_park_open_between_regular_close_and_party_with_quiet_data():
    """Within the schedule, a quiet stretch (no ride changed in 20 min) doesn't close the park."""
    park = _park(PARTY_NIGHT, last_updated="2026-10-04T17:45:00-04:00")
    assert _open(park, _at("2026-10-04T18:30:00-04:00")) is True


def test_park_closed_overnight_until_the_next_opening():
    park = _park(PARTY_NIGHT + NEXT_DAY, last_updated="2026-10-05T07:59:00-04:00")
    assert _open(park, _at("2026-10-05T08:00:00-04:00")) is False
    park["attractions"][0]["lastUpdatedTs"] = "2026-10-05T08:44:00-04:00"
    assert _open(park, _at("2026-10-05T08:45:00-04:00")) is True


def test_park_closed_before_the_first_opening():
    park = _park(NEXT_DAY, last_updated="2026-10-05T05:59:00-04:00")
    assert _open(park, _at("2026-10-05T06:00:00-04:00")) is False


def test_stale_schedule_falls_back_to_freshness():
    """Only yesterday's schedule (the refresh failed) and the park is open again today: the
    schedule isn't trusted 9 hours after its close, so fresh live data decides."""
    park = _park(PARTY_NIGHT)
    now = _at("2026-10-05T10:00:00-04:00")
    park["attractions"][0]["lastUpdatedTs"] = "2026-10-05T09:58:00-04:00"
    assert _open(park, now) is True
    park["attractions"][0]["lastUpdatedTs"] = "2026-10-05T09:00:00-04:00"
    assert _open(park, now) is False


def test_stale_schedule_trusted_for_a_few_hours_after_close():
    park = _park(PARTY_NIGHT, last_updated="2026-10-05T05:59:00-04:00")
    assert _open(park, _at("2026-10-05T06:00:00-04:00")) is False


@pytest.mark.parametrize("last_updated", ["2026-10-04T18:29:00", "not a time", None, ""])
def test_operating_without_a_schedule_unreadable_timestamp_is_stale(last_updated):
    """Without a schedule, freshness decides; a time it can't read (a naive one included,
    which used to raise comparing with an aware now) counts as stale."""
    park = _park([], last_updated=last_updated)
    assert _open(park, _at("2026-10-04T18:30:00-04:00")) is False


def test_update_parks_operating_status_stores_actual_park_closing_time(monkeypatch):
    park = _park(PARTY_NIGHT)
    park["schedule_date"] = datetime.now().strftime("%Y-%m-%d")  # no daily refresh
    monkeypatch.setattr("api.disney_api.handle_park_schedule_update", lambda p: None)
    update_parks_operating_status([park])
    assert park["actualParkClosingTime"] == "2026-10-05T01:00:00-04:00"


def test_update_parks_operating_status_logs_only_when_a_park_opens_or_closes(monkeypatch):
    park = _park(PARTY_NIGHT)
    park["schedule_date"] = datetime.now().strftime("%Y-%m-%d")
    monkeypatch.setattr("api.disney_api.handle_park_schedule_update", lambda p: None)
    monkeypatch.setattr("api.disney_api.operating_and_why", lambda p, now=None: (True, "schedule: open until 01:00"))
    logged = []
    monkeypatch.setattr("api.disney_api.debug.info", logged.append)
    update_parks_operating_status([park])
    update_parks_operating_status([park])
    assert logged == ["Magic Kingdom: open (schedule: open until 01:00)"]
    assert park["operatingReason"] == "schedule: open until 01:00"


def test_update_parks_operating_status_actual_park_closing_time_empty_without_schedule(monkeypatch):
    park = _park([])
    monkeypatch.setattr("api.disney_api.handle_park_schedule_update", lambda p: None)
    update_parks_operating_status([park])
    assert park["actualParkClosingTime"] == ""


def test_handle_park_schedule_update(monkeypatch):
    park = {"name": "Test Park", "id": "dummy-id", "schedule": []}
    # Patch fetch_park_schedule to return a dummy schedule with an OPERATING event.
    dummy_schedule = [{
        "type": "OPERATING",
        "date": "2026-08-12",
        "openingTime": "09:00",
        "closingTime": "22:00",
        "purchases": [{"name": "Lightning Lane Multi Pass", "price": {"formatted": "$25"}}]
    }]
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: dummy_schedule)
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: None)
    # Capture debug info if desired.
    from api.disney_api import handle_park_schedule_update
    handle_park_schedule_update(park)
    # Verify that schedule is updated and llmpPrice is set.
    assert park["schedule"] == dummy_schedule
    assert park["llmpPrice"] == "$25"
    assert park["openingTime"] == "09:00"
    assert park["closingTime"] == "22:00"
    assert park["schedule_date"] == "2026-08-12"

def test_handle_park_schedule_update_calls_refresh(monkeypatch):
    park = {"name": "Test Park", "id": "dummy-id", "schedule": [], "attractions": []}
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: [])
    refreshed = []
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: refreshed.append(p))
    handle_park_schedule_update(park)
    assert refreshed == [park]

def test_update_parks_operating_status_no_refresh_when_already_operating(monkeypatch):
    park = {
        "name": "Test Park", "id": "dummy-id", "schedule": [], "operating": True,
        "attractions": [{"name": "Ride A", "waitTime": "10", "status": "OPERATING", "lastUpdatedTs": _fresh_ts()}],
    }
    monkeypatch.setattr("api.disney_api.fetch_park_schedule",
                        lambda park_id: (_ for _ in ()).throw(AssertionError("schedule fetched")))
    # Midday, outside the 3am-9am daily refresh window: with no timezone the park falls back
    # to UTC, so run for real between 11pm and 5am Eastern this test saw the legitimate daily
    # refresh fire and failed.
    monkeypatch.setattr("api.disney_api._park_local_now",
                        lambda p: datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc))
    refreshed = []
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: refreshed.append(p))
    updated = update_parks_operating_status([park])
    assert updated[0]["operating"] is True
    assert refreshed == []
    assert not updated[0].get("schedule_refresh_needed")

def test_update_parks_operating_status_defers_schedule_fetch(monkeypatch):
    """fetch_schedules=False (WS thread): transition flags the park but does no HTTP."""
    park = {
        "name": "Test Park", "id": "dummy-id", "schedule": [],
        "attractions": [{"name": "Ride A", "waitTime": "10", "status": "OPERATING", "lastUpdatedTs": _fresh_ts()}],
    }
    monkeypatch.setattr("api.disney_api.fetch_park_schedule",
                        lambda park_id: (_ for _ in ()).throw(AssertionError("schedule fetched")))
    monkeypatch.setattr("api.disney_api.refresh_park_attractions",
                        lambda p: (_ for _ in ()).throw(AssertionError("attractions refreshed")))
    updated = update_parks_operating_status([park], fetch_schedules=False)
    assert updated[0]["operating"] is True
    assert updated[0]["schedule_refresh_needed"] is True

def test_update_parks_operating_status_consumes_deferred_flag(monkeypatch):
    """fetch_schedules=True (REST thread): a pending flag triggers the fetch and is cleared."""
    park = {
        "name": "Test Park", "id": "dummy-id", "schedule": [],
        "operating": True, "schedule_refresh_needed": True,
        "attractions": [{"name": "Ride A", "waitTime": "10", "status": "OPERATING", "lastUpdatedTs": _fresh_ts()}],
    }
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: [{
        "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00"
    }])
    refreshed = []
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: refreshed.append(p))
    updated = update_parks_operating_status([park])
    assert updated[0]["schedule_refresh_needed"] is False
    assert updated[0]["openingTime"] == "09:00"
    assert refreshed == [park]

def test_daily_schedule_refresh_due_at_3am_when_schedule_stale(monkeypatch):
    """schedule_date doesn't match today and it's within the 3am-9am local window:
    the daily refresh is due."""
    from api.disney_api import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12"}
    assert _daily_schedule_refresh_due(park, local_now) is True

def test_daily_schedule_refresh_not_due_before_3am(monkeypatch):
    from api.disney_api import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 2, 59, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12"}
    assert _daily_schedule_refresh_due(park, local_now) is False

def test_daily_schedule_refresh_not_due_once_schedule_matches_today(monkeypatch):
    from api.disney_api import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 5, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-13"}
    assert _daily_schedule_refresh_due(park, local_now) is False

def test_daily_schedule_refresh_stops_after_9am_local(monkeypatch):
    """API still hasn't published today's hours by 9am: stop retrying for the day."""
    from api.disney_api import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 9, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12"}
    assert _daily_schedule_refresh_due(park, local_now) is False

def test_daily_schedule_refresh_retries_every_30_minutes(monkeypatch):
    """A failed attempt (schedule still stale after fetch) doesn't retry again until
    30 minutes have passed."""
    from api.disney_api import _daily_schedule_refresh_due
    last_attempt = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12", "_daily_refresh_last_attempt": last_attempt}

    too_soon = datetime(2026, 8, 13, 3, 20, tzinfo=timezone.utc)
    assert _daily_schedule_refresh_due(park, too_soon) is False

    due = datetime(2026, 8, 13, 3, 30, tzinfo=timezone.utc)
    assert _daily_schedule_refresh_due(park, due) is True

def test_park_local_now_uses_park_timezone(monkeypatch):
    from api.disney_api import _park_local_now
    park = {"name": "Test Park", "timezone": "America/New_York"}
    local_now = _park_local_now(park)
    assert str(local_now.tzinfo) == "America/New_York"

def test_park_local_now_falls_back_to_utc_for_unknown_timezone(monkeypatch):
    from api.disney_api import _park_local_now
    park = {"name": "Test Park", "timezone": "Not/A_Real_Zone"}
    local_now = _park_local_now(park)
    assert local_now.tzinfo == timezone.utc

def test_park_local_now_falls_back_to_utc_when_timezone_missing(monkeypatch):
    from api.disney_api import _park_local_now
    park = {"name": "Test Park"}
    local_now = _park_local_now(park)
    assert local_now.tzinfo == timezone.utc

def test_update_parks_operating_status_triggers_daily_refresh_at_3am(monkeypatch):
    """End-to-end: at 3am local with yesterday's schedule_date, a refresh fires and
    updates schedule_date/closingTime — the proactive daily refresh, independent of
    attraction status entirely (park attractions are empty/closed here)."""
    class FakeDateTime(datetime):
        _now = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls._now if tz is None else cls._now.astimezone(tz)

    monkeypatch.setattr("api.disney_api.datetime", FakeDateTime)

    park = {
        "name": "Test Park", "id": "dummy-id", "schedule": [],
        "operating": False, "timezone": None,
        "schedule_date": "2026-08-12",
        "attractions": [],
    }
    monkeypatch.setattr("api.disney_api.fetch_park_schedule", lambda park_id: [{
        "type": "OPERATING", "date": "2026-08-13",
        "openingTime": "2026-08-13T09:00:00+00:00", "closingTime": "2026-08-13T22:00:00+00:00",
    }])
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: None)

    updated = update_parks_operating_status([park])
    assert updated[0]["schedule_date"] == "2026-08-13"
    assert updated[0]["closingTime"] == "2026-08-13T22:00:00+00:00"
    assert updated[0]["schedule_refresh_needed"] is False

def test_update_parks_operating_status_daily_refresh_retries_on_stale_response(monkeypatch):
    """API keeps returning yesterday's OPERATING event (hasn't published today's hours
    yet): schedule_date stays stale, so the daily refresh keeps retrying every 30
    minutes instead of firing every single 5-minute poll cycle."""
    class FakeDateTime(datetime):
        _now = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls._now if tz is None else cls._now.astimezone(tz)

    monkeypatch.setattr("api.disney_api.datetime", FakeDateTime)

    park = {
        "name": "Test Park", "id": "dummy-id", "schedule": [],
        "operating": False, "timezone": None,
        "schedule_date": "2026-08-12",
        "attractions": [],
    }
    fetch_count = []

    def stale_fetch(park_id):
        fetch_count.append(1)
        # API still hasn't rolled over to today's schedule.
        return [{"type": "OPERATING", "date": "2026-08-12",
                 "openingTime": "2026-08-12T09:00:00+00:00", "closingTime": "2026-08-12T22:00:00+00:00"}]

    monkeypatch.setattr("api.disney_api.fetch_park_schedule", stale_fetch)
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: None)

    update_parks_operating_status([park])
    assert len(fetch_count) == 1

    # 10 minutes later: too soon to retry, no second fetch.
    FakeDateTime._now = datetime(2026, 8, 13, 3, 10, tzinfo=timezone.utc)
    update_parks_operating_status([park])
    assert len(fetch_count) == 1

    # 30 minutes after the first attempt: retries.
    FakeDateTime._now = datetime(2026, 8, 13, 3, 30, tzinfo=timezone.utc)
    update_parks_operating_status([park])
    assert len(fetch_count) == 2

    # Past 9am local: stops retrying for the day even though schedule is still stale.
    FakeDateTime._now = datetime(2026, 8, 13, 9, 30, tzinfo=timezone.utc)
    update_parks_operating_status([park])
    assert len(fetch_count) == 2

def test_park_reopens_after_midnight_without_deadlock(monkeypatch):
    """
    End-to-end regression test for the original deadlock: a closed park with no
    fresh attractions gets its schedule proactively refreshed by the 3am-local daily
    trigger — without needing any attraction to flip OPERATING first — and then
    correctly shows operating again once fresh live data arrives after opening.
    """
    class FakeDateTime(datetime):
        _now = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls._now if tz is None else cls._now.astimezone(tz)

    monkeypatch.setattr("api.disney_api.datetime", FakeDateTime)

    park = {
        "name": "Test Park", "id": "dummy-id", "schedule": [],
        "operating": False, "timezone": None,
        "schedule_date": "2026-08-12",
        "attractions": [
            {"name": "Ride A", "waitTime": "10", "status": "CLOSED",
             "lastUpdatedTs": "2026-08-12T23:50:00+00:00"},
        ],
    }

    schedule_fetches = []

    def fake_fetch_schedule(park_id):
        schedule_fetches.append(1)
        return [{
            "type": "OPERATING", "date": "2026-08-13",
            "openingTime": "2026-08-13T09:00:00+00:00",
            "closingTime": "2026-08-13T22:00:00+00:00",
        }]

    monkeypatch.setattr("api.disney_api.fetch_park_schedule", fake_fetch_schedule)
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: None)

    # 3am, park closed overnight: daily refresh fires proactively.
    updated = update_parks_operating_status([park])
    assert updated[0]["operating"] is False
    assert schedule_fetches == [1]
    assert updated[0]["schedule_refresh_needed"] is False
    assert updated[0]["closingTime"] == "2026-08-13T22:00:00+00:00"
    assert updated[0]["schedule_date"] == "2026-08-13"

    # Later that morning: a fresh OPERATING attraction update arrives (WS/REST).
    FakeDateTime._now = datetime(2026, 8, 13, 9, 30, tzinfo=timezone.utc)
    park["attractions"][0]["status"] = "OPERATING"
    park["attractions"][0]["lastUpdatedTs"] = "2026-08-13T09:29:00+00:00"
    updated = update_parks_operating_status([park])
    assert updated[0]["operating"] is True
    # closed->open transition triggers its own (separate) schedule refresh too.
    assert schedule_fetches == [1, 1]


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
            "status": "OPERATING",
            "lastUpdatedTs": _fresh_ts()
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
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: None)
    updated = update_parks_operating_status(copy.deepcopy(parks))
    assert updated[0]["operating"] is True

# ---- Wait-time forecasts ----

FORECAST = [
    {"time": "2026-09-25T10:00:00-04:00", "waitTime": 20, "percentage": 17},
    {"time": "2026-09-25T11:00:00-04:00", "waitTime": 40, "percentage": 34},
]


def test_parse_forecast_keeps_time_and_wait_only():
    assert parse_forecast(FORECAST) == [
        {"time": "2026-09-25T10:00:00-04:00", "waitTime": 20},
        {"time": "2026-09-25T11:00:00-04:00", "waitTime": 40},
    ]


@pytest.mark.parametrize("raw", [None, [], "nope", [None], [{"time": "2026-09-25T10:00:00-04:00"}],
                                 [{"waitTime": 10}], [{"time": 5, "waitTime": 10}],
                                 [{"time": "2026-09-25T10:00:00-04:00", "waitTime": "10"}],
                                 [{"time": "2026-09-25T10:00:00-04:00", "waitTime": True}]])
def test_parse_forecast_drops_malformed_points(raw):
    assert parse_forecast(raw) == []


@pytest.mark.parametrize("now_utc, expected", [
    ("2026-09-25T14:00:00+00:00", 20),   # 10:00 EDT, start of the hour
    ("2026-09-25T14:59:59+00:00", 20),
    ("2026-09-25T15:30:00+00:00", 40),   # 11:30 EDT
    ("2026-09-25T13:59:00+00:00", None),  # before the forecast starts
    ("2026-09-25T16:00:00+00:00", None),  # after the last hour
])
def test_forecast_wait_now_picks_the_hour_containing_now(now_utc, expected):
    now = datetime.fromisoformat(now_utc)
    assert forecast_wait_now(parse_forecast(FORECAST), now) == expected


@pytest.mark.parametrize("forecast", [None, [], [{"time": "garbage", "waitTime": 5}],
                                      [{"time": "2026-09-25T10:00:00", "waitTime": 5}]])
def test_forecast_wait_now_without_usable_data_is_none(forecast):
    assert forecast_wait_now(forecast, datetime(2026, 9, 25, 14, 30, tzinfo=timezone.utc)) is None


def test_build_live_updates_includes_forecast_only_when_present():
    entries = [
        {"id": "a", "entityType": "ATTRACTION", "status": "OPERATING", "lastUpdated": "t",
         "queue": {"STANDBY": {"waitTime": 30}}, "forecast": FORECAST},
        {"id": "b", "entityType": "ATTRACTION", "status": "OPERATING", "lastUpdated": "t",
         "queue": {"STANDBY": {"waitTime": 10}}},
    ]
    with_fc, without_fc = build_live_updates(entries)
    assert with_fc["forecast"] == parse_forecast(FORECAST)
    assert "forecast" not in without_fc


# --- showtimes ---

HEA_RAW = [{"type": "Performance Time", "startTime": "2026-09-26T21:30:00-04:00", "endTime": "2026-09-26T21:30:00-04:00"}]
HEA_START = datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc)


def test_parse_showtimes_keeps_valid_starts_and_drops_malformed():
    raw = HEA_RAW + [{"startTime": "not a time"}, {"endTime": "2026-09-26T22:00:00-04:00"},
                     {"startTime": "2026-09-26T23:00:00"}, "junk", {"startTime": None}]
    assert parse_showtimes(raw) == [HEA_START], "naive times are dropped: no way to compare to now"
    assert parse_showtimes(None) == [] and parse_showtimes([]) == []


def test_build_live_updates_carries_showtimes_including_an_empty_list():
    entries = [
        {"id": "hea", "entityType": "SHOW", "status": "OPERATING", "lastUpdated": "x", "showtimes": HEA_RAW},
        {"id": "done", "entityType": "SHOW", "status": "OPERATING", "lastUpdated": "x", "showtimes": []},
        {"id": "ride", "entityType": "ATTRACTION", "status": "OPERATING", "lastUpdated": "x"},
    ]
    hea, done, ride = build_live_updates(entries)
    assert hea["showtimes"] == [HEA_START]
    assert done["showtimes"] == [], "an empty list clears yesterday's showtimes"
    assert "showtimes" not in ride


def _parks_with_show(name="Happily Ever After", starts=(HEA_START,)):
    return [{"name": "Magic Kingdom", "attractions": [
        {"id": "ride", "name": "Space Mountain"},
        {"id": "hea", "name": name, "showtimes": list(starts)},
    ]}]


def test_show_start_due_only_inside_the_window_after_a_start():
    parks = _parks_with_show()
    at = lambda **kw: HEA_START + timedelta(**kw)
    assert show_start_due(parks, "Happily Ever After", 300, now=at(seconds=-1)) is None, "not before it starts"
    assert show_start_due(parks, "Happily Ever After", 300, now=at(seconds=0)) == HEA_START
    assert show_start_due(parks, "Happily Ever After", 300, now=at(seconds=299)) == HEA_START
    assert show_start_due(parks, "Happily Ever After", 300, now=at(seconds=300)) is None, "not after the window"


def test_show_start_due_ignores_other_shows_and_parks_without_showtimes():
    now = HEA_START + timedelta(seconds=10)
    assert show_start_due(_parks_with_show(name="Luminous"), "Happily Ever After", 300, now=now) is None
    assert show_start_due([{"name": "EPCOT", "attractions": [{"name": "Happily Ever After"}]}],
                          "Happily Ever After", 300, now=now) is None
    assert show_start_due([], "Happily Ever After", 300, now=now) is None
    later = HEA_START + timedelta(hours=2)
    two = _parks_with_show(starts=(HEA_START, later))
    assert show_start_due(two, "Happily Ever After", 300, now=later + timedelta(seconds=5)) == later


def test_startup_fetches_log_summaries_not_whole_payloads(monkeypatch):
    # The API returns tens of KB per park; the debug log gets a count, not the payload.
    today_str = datetime.now().strftime('%Y-%m-%d')
    children = [{"id": f"attr-{i}", "name": f"Ride {i} " + "x" * 40, "entityType": "ATTRACTION"} for i in range(200)]
    schedule = [{"date": today_str, "type": "OPERATING", "openingTime": "09:00", "closingTime": "22:00",
                 "description": "y" * 200} for _ in range(30)]

    def fake_get(url, **kwargs):
        if "children" in url:
            return DummyResponse({"children": children}, 200)
        if "schedule" in url:
            return DummyResponse({"schedule": schedule}, 200)
        return DummyResponse({"location": {"latitude": 28.3759, "longitude": -81.5494}}, 200)

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(disney_api, "fetch_weather_data", lambda lat, lon: {"temp": "dummy"})
    logged = []
    for level in ("log", "info"):
        monkeypatch.setattr(disney_api.debug, level, lambda msg, *a, **k: logged.append(str(msg)))
    parks = [{"id": "dummy-id", "name": "Magic Kingdom", "schedule": schedule, "weather": [],
              "location": {"latitude": 28.3759, "longitude": -81.5494}}]
    fetch_park_schedule("dummy-id")
    result = fetch_parks_and_attractions(parks)
    assert len(result[0]["attractions"]) == 200
    assert logged and max(len(m) for m in logged) < 300, "summaries, not the whole response"
    assert len(logged) < 20, "not a line per attraction"
