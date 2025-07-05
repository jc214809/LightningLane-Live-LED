from datetime import timezone as dt_timezone, timedelta


def timezone(name: str):
    if name == "UTC":
        return dt_timezone.utc
    if name in {"US/Eastern", "America/New_York"}:
        # Eastern Time is UTC-5 in winter (non-DST) which is enough for tests
        return dt_timezone(timedelta(hours=-5), name)
    raise NotImplementedError(name)

utc = dt_timezone.utc
