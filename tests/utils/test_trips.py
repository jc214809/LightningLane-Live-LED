# tests/utils/test_trips.py
from datetime import date, timedelta

import pytest

from utils.trips import Trip, active_trip, parse_date, parse_trips

TODAY = date(2026, 9, 26)


def day(offset):
    return TODAY + timedelta(days=offset)


# --- parsing ---

def test_parse_date_accepts_dates_and_datetimes():
    assert parse_date("2020-02-29") == date(2020, 2, 29)
    assert parse_date("2026-11-10T08:30:00") == date(2026, 11, 10)
    with pytest.raises(ValueError):
        parse_date("not-a-date")


def test_parses_plain_dates_and_full_trips():
    config = {"trip_countdown": {"trip_dates": [
        "2026-11-10",
        {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"},
        {"start": "2027-06-01"},
    ]}}
    assert parse_trips(config) == [
        Trip(date(2026, 11, 10)),
        Trip(date(2027, 3, 14), date(2027, 3, 19), "Spring Break"),
        Trip(date(2027, 6, 1)),
    ]


@pytest.mark.parametrize("bad", [
    "invalid-date",
    {"end": "2027-03-19"},
    {"start": "2027-03-19", "end": "2027-03-14"},
    {"start": "2027-03-14", "end": "soon"},
    None,
])
def test_invalid_trips_are_skipped(bad):
    config = {"trip_countdown": {"trip_dates": [bad, "2026-11-10"]}}
    assert parse_trips(config) == [Trip(date(2026, 11, 10))]


def test_blank_name_is_no_name():
    config = {"trip_countdown": {"trip_dates": [{"start": "2026-11-10", "name": "  "}]}}
    assert parse_trips(config)[0].name is None


def test_legacy_single_trip_date():
    assert parse_trips({"trip_countdown": {"trip_date": "2026-11-10"}}) == [Trip(date(2026, 11, 10))]
    assert parse_trips({"trip_countdown": {}}) == []
    assert parse_trips({}) == []


# --- which trip shows ---

def test_nearest_upcoming_trip_shows():
    trips = [Trip(day(30)), Trip(day(5)), Trip(day(-40))]
    assert active_trip(trips, TODAY) == Trip(day(5))


def test_trip_under_way_beats_the_next_one():
    under_way = Trip(day(-2), day(3))
    assert active_trip([Trip(day(10)), under_way], TODAY) == under_way


def test_finished_trip_holds_the_screen_for_welcome_home_then_moves_on():
    finished = Trip(day(-6), day(-2))
    nxt = Trip(day(60))
    assert active_trip([finished, nxt], TODAY) == finished, "2 days after it ends"
    assert active_trip([Trip(day(-7), day(-3)), nxt], TODAY) == nxt, "3 days after"


def test_open_ended_trip_holds_the_screen_for_a_week():
    nxt = Trip(day(10))
    assert active_trip([Trip(day(-7)), nxt], TODAY) == Trip(day(-7))
    assert active_trip([Trip(day(-8)), nxt], TODAY) == nxt


def test_latest_start_wins_when_trips_overlap():
    assert active_trip([Trip(day(-5), day(1)), Trip(day(-1), day(2))], TODAY) == Trip(day(-1), day(2))


def test_no_trip_when_all_are_long_past():
    assert active_trip([Trip(day(-20)), Trip(day(-30), day(-25))], TODAY) is None
    assert active_trip([], TODAY) is None


def test_defaults_to_today():
    assert active_trip([Trip(date.today() + timedelta(days=3))]) is not None
