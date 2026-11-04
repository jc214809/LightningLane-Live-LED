"""
What the live data says right now: a ride's forecast wait for this hour, and whether a show
has just started. Pure reads over the parks_data dicts that api.disney_api builds.
"""
from datetime import datetime, timedelta, timezone


def forecast_wait_now(forecast, now=None):
    """The forecast wait for the hour containing now, or None if the forecast doesn't cover it."""
    now = now or datetime.now(timezone.utc)
    for point in forecast or []:
        try:
            start = datetime.fromisoformat(point["time"].replace("Z", "+00:00"))
        except (ValueError, AttributeError, KeyError, TypeError):
            continue
        if start.tzinfo is None:
            continue
        if start <= now < start + timedelta(hours=1):
            return point["waitTime"]
    return None



def _plain_name(name):
    """A show name compared loosely: the API mixes curly and straight apostrophes."""
    return (name or "").lower().replace("\u2019", "'").strip()


def _is_show(name, wanted):
    """`name` is the show `wanted` (already plain), on its own or with the event it runs at
    appended: party nights list "Disney's Not-So-Spooky Spectacular at Mickey's Not-So-Scary
    Halloween Party". Not a bare prefix, so "Happily Ever After Dessert Party" isn't the show."""
    name = _plain_name(name)
    return name == wanted or name.startswith(wanted + " at ")


def show_start_due(parks, show_name, window_s, now=None):
    """
    The start time of a performance of `show_name` that began within the last
    `window_s` seconds, in any of `parks`, or None. The API gives no end time, so
    "in progress" means "started less than window_s ago".
    """
    now = now or datetime.now(timezone.utc)
    wanted = _plain_name(show_name)
    for park in parks:
        for attr in park.get("attractions", []):
            if not _is_show(attr.get("name"), wanted):
                continue
            for start in attr.get("showtimes") or []:
                if start <= now < start + timedelta(seconds=window_s):
                    return start
    return None

