"""The board's brightness by the clock: config.json's "brightness_schedule" (utils/config.py), as in
Peloton-LED. disney.main() sets it once with use(); display/animation/player.py asks current() for
each canvas it hands out, since rgbmatrix applies brightness per canvas, as pixels are drawn.
"""
import time
from datetime import datetime

CHECK_EVERY_S = 30.0  # asked every frame; the schedule works in minutes

_schedule = None
_cache = {"at": None, "level": None}


def scheduled_brightness(schedule, now):
    """The schedule's level at now (a datetime or time): day from day_start up to night_start, night
    the rest, either way round midnight. Equal starts mean night all day, as in Peloton-LED."""
    minute = now.hour * 60 + now.minute
    day = schedule.day_start.hour * 60 + schedule.day_start.minute
    night = schedule.night_start.hour * 60 + schedule.night_start.minute
    daytime = day <= minute < night if day <= night else (minute >= day or minute < night)
    return schedule.day if daytime else schedule.night


def use(schedule):
    """Follow this BrightnessSchedule from now on; None keeps the board's one brightness."""
    global _schedule
    _schedule = schedule
    _cache.update(at=None, level=None)


def current(clock=time.monotonic, now=datetime.now):
    """The level the schedule wants now, or None with no schedule. Worked out at most every CHECK_EVERY_S."""
    if _schedule is None:
        return None
    at = clock()
    if _cache["at"] is None or at - _cache["at"] >= CHECK_EVERY_S:
        _cache.update(at=at, level=scheduled_brightness(_schedule, now()))
    return _cache["level"]
