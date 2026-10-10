from datetime import datetime, timedelta, timezone

import pytest

from api.disney_api import parse_forecast
from parks.live import forecast_wait_now, show_start_due

FORECAST = [
    {"time": "2026-09-25T10:00:00-04:00", "waitTime": 20, "percentage": 17},
    {"time": "2026-09-25T11:00:00-04:00", "waitTime": 40, "percentage": 34},
]
HEA_START = datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc)


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


def test_show_start_due_matches_a_show_named_with_the_event_it_runs_at():
    now = HEA_START + timedelta(seconds=10)
    spooky = "Disney\u2019s Not-So-Spooky Spectacular at Mickey\u2019s Not-So-Scary Halloween Party"
    assert show_start_due(_parks_with_show(name=spooky), "Disney's Not-So-Spooky Spectacular",
                          300, now=now) == HEA_START, "live data appends the party's name"
    assert show_start_due(_parks_with_show(name="Happily Ever After Dessert Party"),
                          "Happily Ever After", 300, now=now) is None, "a longer name isn't the show"
