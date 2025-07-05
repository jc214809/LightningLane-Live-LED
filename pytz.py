from datetime import timezone as dt_timezone, timedelta, datetime, tzinfo


class _USEastern(tzinfo):
    """Very small tzinfo implementation for the US/Eastern time zone."""

    def __init__(self, name: str = "US/Eastern"):
        self.name = name

    def __repr__(self):
        return f"<Timezone {self.name}>"

    def _is_dst(self, dt: datetime) -> bool:
        """Determine if ``dt`` is in daylight saving time."""
        if dt is None:
            return False

        # Work with naive datetime for calculations
        dt = dt.replace(tzinfo=None)
        year = dt.year

        # DST starts at 2am on the second Sunday in March
        start = datetime(year, 3, 8)
        start += timedelta(days=(6 - start.weekday()))  # move to Sunday
        start = start.replace(hour=2)

        # DST ends at 2am on the first Sunday in November
        end = datetime(year, 11, 1)
        end += timedelta(days=(6 - end.weekday()))
        end = end.replace(hour=2)

        return start <= dt < end

    def utcoffset(self, dt: datetime) -> timedelta:
        return timedelta(hours=-5) + self.dst(dt)

    def dst(self, dt: datetime) -> timedelta:
        if self._is_dst(dt):
            return timedelta(hours=1)
        return timedelta(0)

    def tzname(self, dt: datetime) -> str:  # pragma: no cover - simple accessor
        return self.name


def timezone(name: str):
    if name == "UTC":
        return dt_timezone.utc
    if name in {"US/Eastern", "America/New_York"}:
        # Return a timezone with simple DST logic.
        return _USEastern(name)
    raise NotImplementedError(name)

utc = dt_timezone.utc
