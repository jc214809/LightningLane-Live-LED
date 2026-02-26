from datetime import datetime, timedelta

import pytest

import disney


def _dt(days_offset: int) -> datetime:
    return datetime.now() + timedelta(days=days_offset)


def test_active_trip_prefers_recent_past_within_week_over_future():
    # Past trip 3 days ago and a future trip 10 days out
    trip_dates = [
        _dt(-3),  # recent past
        _dt(10),  # future
    ]
    active = disney.get_active_trip_date(trip_dates)
    assert active is not None
    assert active.date() == _dt(-3).date()


def test_active_trip_picks_closest_upcoming_when_no_recent_past():
    # Past is 10 days ago (beyond 7), futures at +2 and +5 -> pick +2
    trip_dates = [
        _dt(-10),
        _dt(5),
        _dt(2),
    ]
    active = disney.get_active_trip_date(trip_dates)
    assert active is not None
    assert active.date() == _dt(2).date()


def test_active_trip_none_when_all_past_and_beyond_week():
    trip_dates = [
        _dt(-8),
        _dt(-20),
    ]
    active = disney.get_active_trip_date(trip_dates)
    assert active is None


def test_parse_trip_dates_array_and_legacy(monkeypatch):
    # Array mode with one invalid date should skip the invalid one
    config_array = {
        "trip_countdown": {
            "enabled": True,
            "trip_dates": [
                datetime.now().date().isoformat(),
                "invalid-date"
            ]
        }
    }
    dates_array = disney.parse_trip_dates(config_array)
    assert len(dates_array) == 1

    # Legacy mode single trip_date
    today_iso = datetime.now().date().isoformat()
    config_legacy = {
        "trip_countdown": {
            "enabled": True,
            "trip_date": today_iso
        }
    }
    dates_legacy = disney.parse_trip_dates(config_legacy)
    assert len(dates_legacy) == 1
    assert dates_legacy[0].date().isoformat() == today_iso
