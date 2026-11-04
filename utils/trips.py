from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from utils import debug

# A trip with no end date shows "Have a Magical Trip!" this long after it starts.
OPEN_ENDED_TRIP_DAYS = 7
# A trip with an end date says "Welcome Home" this long after it ends.
WELCOME_HOME_DAYS = 2


@dataclass(frozen=True)
class Trip:
    start: date
    end: Optional[date] = None
    name: Optional[str] = None

    def shown_until(self):
        """Last day this trip still owns the countdown screen."""
        if self.end:
            return self.end + timedelta(days=WELCOME_HOME_DAYS)
        return self.start + timedelta(days=OPEN_ENDED_TRIP_DAYS)


def parse_date(value):
    """A date from YYYY-MM-DD or a full ISO datetime string."""
    text = str(value)
    if len(text) == 10:
        return date.fromisoformat(text)
    return datetime.fromisoformat(text).date()


def _parse_trip(entry):
    if not isinstance(entry, dict):
        return Trip(parse_date(entry))
    start = parse_date(entry["start"])
    end = parse_date(entry["end"]) if entry.get("end") else None
    if end and end < start:
        raise ValueError(f"end {end} is before start {start}")
    name = str(entry["name"]).strip() if entry.get("name") else None
    return Trip(start, end, name or None)


def parse_trips(config):
    """
    Trips from config trip_countdown.trip_dates: each entry is a date string or
    {"start": ..., "end": ..., "name": ...} (end and name optional). Falls back to the
    legacy single trip_date. Invalid entries are logged and skipped.
    """
    tc = config.get("trip_countdown", {})
    entries = tc.get("trip_dates")
    if not isinstance(entries, list):
        entries = [tc["trip_date"]] if tc.get("trip_date") else []
    trips = []
    for entry in entries:
        try:
            trips.append(_parse_trip(entry))
        except (KeyError, TypeError, ValueError) as e:
            debug.warning(f"Ignoring invalid trip {entry!r}: {e}")
    return trips


def active_trip(trips: Iterable[Trip], today: Optional[date] = None) -> Optional[Trip]:
    """
    The one trip the countdown shows: a trip under way (or just finished) wins,
    the latest-starting one if several are; otherwise the nearest upcoming trip.
    """
    today = today or date.today()
    current = [t for t in trips if t.start <= today <= t.shown_until()]
    if current:
        return max(current, key=lambda t: t.start)
    upcoming = [t for t in trips if t.start > today]
    return min(upcoming, key=lambda t: t.start) if upcoming else None
