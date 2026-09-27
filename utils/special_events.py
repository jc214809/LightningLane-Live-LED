"""Special ticketed events (after-hours parties): whether a park is holding one now, which party
it is, and how the board marks it.

The schedule only ever says "Special Ticketed Event"; what names the party is the park's
attraction list, which carries entities like "... at Mickey's Not-So-Scary Halloween Party".
To add a party, add an entry to SPECIAL_EVENTS.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from utils import debug

SPECIAL_EVENTS = {
    "halloween": {
        "match": "not-so-scary halloween party",  # found in a lower-cased entity name
        "star_rgb": (255, 130, 20),  # the "*" after the park hours
        "landmark": "FriendlyJackOLanternLandmark",  # replaces the park's landmark (display/landmarks.py)
        "fireworks_show": "Disney's Not-So-Spooky Spectacular",  # plays the castle fireworks when it starts
        "fireworks_theme": "halloween",  # display/fireworks/fireworks.py THEMES
    },
}

# A special event we can't name (e.g. extended evening hours) keeps the original gold star.
DEFAULT_STAR_RGB = (255, 215, 0)

# The fireworks show a park runs on an ordinary night, and its castle-fireworks theme (None is the
# everyday look). A party night swaps in the party's own show and theme; see fireworks_show().
NIGHTLY_FIREWORKS = ("Happily Ever After", None)


def seasonal_event(children):
    """The SPECIAL_EVENTS key whose entities are in a park's children, or None."""
    for item in children:
        name = item.get("name", "").lower().replace("’", "'")
        for key, event in SPECIAL_EVENTS.items():
            if event["match"] in name:
                return key
    return None


def is_special(event):
    """A schedule entry for a special ticketed event or extended evening hours."""
    description = event.get("description", "").lower()
    return event.get("type") == "TICKETED_EVENT" and (
        "special ticketed event" in description or "extended evening" in description)


def _parse(when):
    try:
        return datetime.fromisoformat(when.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None


def _local_today(park, now):
    try:
        tz = ZoneInfo(park["timezone"]) if park.get("timezone") else timezone.utc
    except Exception:
        debug.warning(f"{park.get('name')}: unknown timezone {park.get('timezone')!r}; using UTC for special events.")
        tz = timezone.utc
    return now.astimezone(tz).strftime("%Y-%m-%d")


def special_event_now(park, now=None):
    """True if the park holds a special event today (its local date), or one is running now.
    The second case is a party that runs past midnight: dated yesterday, still going. Once it
    ends, yesterday's event no longer counts, even though the schedule still holds it."""
    now = now or datetime.now(timezone.utc)
    today = _local_today(park, now)
    for event in park.get("schedule") or []:
        if not is_special(event):
            continue
        if event.get("date") == today:
            return True
        start, end = _parse(event.get("openingTime")), _parse(event.get("closingTime"))
        if start and end and start.tzinfo and end.tzinfo and start <= now < end:
            return True
    return False


def active_party(park, now=None):
    """The SPECIAL_EVENTS key of the party the park is holding now, or None."""
    key = park.get("seasonalEvent")
    if key in SPECIAL_EVENTS and special_event_now(park, now):
        return key
    return None


def fireworks_show(park, now=None):
    """(show name, fireworks theme) the park runs tonight, looked up from its schedule: the party's
    own show on a party night (Happily Ever After doesn't run then), else NIGHTLY_FIREWORKS."""
    event = SPECIAL_EVENTS.get(active_party(park, now), {})
    if event.get("fireworks_show"):
        return event["fireworks_show"], event.get("fireworks_theme")
    return NIGHTLY_FIREWORKS


def star_rgb(park, now=None):
    """Colour of the "*" after the park hours: the party's own, gold for an unnamed special
    event, or None when there's no special event."""
    if not special_event_now(park, now):
        return None
    key = park.get("seasonalEvent")
    return SPECIAL_EVENTS[key]["star_rgb"] if key in SPECIAL_EVENTS else DEFAULT_STAR_RGB
