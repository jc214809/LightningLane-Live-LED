from datetime import datetime, time

import pytest

import utils.brightness as brightness
from utils.config import BrightnessSchedule

SCHEDULE = BrightnessSchedule(80, 15, time(7, 0), time(22, 0))


@pytest.mark.parametrize("at, level", [("06:59", 15), ("07:00", 80), ("12:00", 80), ("21:59", 80), ("22:00", 15),
                                       ("00:30", 15)])
def test_day_from_day_start_to_night_start(at, level):
    assert brightness.scheduled_brightness(SCHEDULE, time.fromisoformat(at)) == level


@pytest.mark.parametrize("at, level", [("19:59", 15), ("20:00", 80), ("23:00", 80), ("05:59", 80), ("06:00", 15)])
def test_a_day_that_runs_past_midnight(at, level):
    # Peloton-LED's own test: day from 20:00 to 06:00
    schedule = BrightnessSchedule(80, 15, time(20, 0), time(6, 0))
    assert brightness.scheduled_brightness(schedule, time.fromisoformat(at)) == level


def test_no_schedule_means_no_level():
    brightness.use(None)
    assert brightness.current() is None


def test_the_level_is_worked_out_at_most_every_30_seconds():
    clock = [0.0]
    now = [datetime(2026, 11, 1, 21, 59, 50)]
    brightness.use(SCHEDULE)

    def ask():
        return brightness.current(lambda: clock[0], lambda: now[0])
    assert ask() == 80
    now[0] = datetime(2026, 11, 1, 22, 0, 5)
    clock[0] += 15
    assert ask() == 80, "cached"
    clock[0] += 15
    assert ask() == 15
