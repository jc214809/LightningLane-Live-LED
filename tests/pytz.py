from datetime import timezone as _timezone, timedelta

utc = _timezone.utc


def timezone(name: str):
    if name == 'US/Eastern':
        return _timezone(timedelta(hours=-5))
    raise NotImplementedError(f"timezone {name} not implemented in stub")
