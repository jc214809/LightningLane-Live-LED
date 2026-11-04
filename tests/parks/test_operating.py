import copy
from datetime import datetime, timedelta, timezone

import pytest

from parks.operating import actual_park_closing_time, operating_and_why, update_parks_operating_status


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
    monkeypatch.setattr("parks.operating.handle_park_schedule_update", lambda p: None)
    update_parks_operating_status([park])
    assert park["actualParkClosingTime"] == "2026-10-05T01:00:00-04:00"


def test_update_parks_operating_status_logs_only_when_a_park_opens_or_closes(monkeypatch):
    park = _park(PARTY_NIGHT)
    park["schedule_date"] = datetime.now().strftime("%Y-%m-%d")
    monkeypatch.setattr("parks.operating.handle_park_schedule_update", lambda p: None)
    monkeypatch.setattr("parks.operating.operating_and_why", lambda p, now=None: (True, "schedule: open until 01:00"))
    logged = []
    monkeypatch.setattr("parks.operating.debug.info", logged.append)
    update_parks_operating_status([park])
    update_parks_operating_status([park])
    assert logged == ["Magic Kingdom: open (schedule: open until 01:00)"]
    assert park["operatingReason"] == "schedule: open until 01:00"


def test_update_parks_operating_status_actual_park_closing_time_empty_without_schedule(monkeypatch):
    park = _park([])
    monkeypatch.setattr("parks.operating.handle_park_schedule_update", lambda p: None)
    update_parks_operating_status([park])
    assert park["actualParkClosingTime"] == ""

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
    monkeypatch.setattr("parks.operating._park_local_now",
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
    from parks.operating import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12"}
    assert _daily_schedule_refresh_due(park, local_now) is True

def test_daily_schedule_refresh_not_due_before_3am(monkeypatch):
    from parks.operating import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 2, 59, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12"}
    assert _daily_schedule_refresh_due(park, local_now) is False

def test_daily_schedule_refresh_not_due_once_schedule_matches_today(monkeypatch):
    from parks.operating import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 5, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-13"}
    assert _daily_schedule_refresh_due(park, local_now) is False

def test_daily_schedule_refresh_stops_after_9am_local(monkeypatch):
    """API still hasn't published today's hours by 9am: stop retrying for the day."""
    from parks.operating import _daily_schedule_refresh_due
    local_now = datetime(2026, 8, 13, 9, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12"}
    assert _daily_schedule_refresh_due(park, local_now) is False

def test_daily_schedule_refresh_retries_every_30_minutes(monkeypatch):
    """A failed attempt (schedule still stale after fetch) doesn't retry again until
    30 minutes have passed."""
    from parks.operating import _daily_schedule_refresh_due
    last_attempt = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)
    park = {"name": "Test Park", "schedule_date": "2026-08-12", "_daily_refresh_last_attempt": last_attempt}

    too_soon = datetime(2026, 8, 13, 3, 20, tzinfo=timezone.utc)
    assert _daily_schedule_refresh_due(park, too_soon) is False

    due = datetime(2026, 8, 13, 3, 30, tzinfo=timezone.utc)
    assert _daily_schedule_refresh_due(park, due) is True

def test_park_local_now_uses_park_timezone(monkeypatch):
    from parks.operating import _park_local_now
    park = {"name": "Test Park", "timezone": "America/New_York"}
    local_now = _park_local_now(park)
    assert str(local_now.tzinfo) == "America/New_York"

def test_park_local_now_falls_back_to_utc_for_unknown_timezone(monkeypatch):
    from parks.operating import _park_local_now
    park = {"name": "Test Park", "timezone": "Not/A_Real_Zone"}
    local_now = _park_local_now(park)
    assert local_now.tzinfo == timezone.utc

def test_park_local_now_falls_back_to_utc_when_timezone_missing(monkeypatch):
    from parks.operating import _park_local_now
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

    monkeypatch.setattr("parks.operating.datetime", FakeDateTime)

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

    monkeypatch.setattr("parks.operating.datetime", FakeDateTime)

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

    monkeypatch.setattr("parks.operating.datetime", FakeDateTime)

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
    monkeypatch.setattr("api.disney_api.refresh_park_attractions", lambda p: None)
    updated = update_parks_operating_status(copy.deepcopy(parks))
    assert updated[0]["operating"] is True
