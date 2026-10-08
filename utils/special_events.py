"""Special ticketed events (after-hours parties): whether a park is holding one now, which party
it is, and how the board marks it.

The schedule only ever says "Special Ticketed Event"; what names the party is the park's
attraction list, which carries entities like "... at Mickey's Not-So-Scary Halloween Party".
Deluxe Extended Evening Hours is the exception: the schedule names it itself.
To add a party, add an entry to SPECIAL_EVENTS.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from utils import debug

# The holiday parties' star: one colour per dot of the "*" (top-left, top-right, centre,
# bottom-left, bottom-right), green and red on alternate corners round a white centre.
_GREEN, _RED, _WHITE = (40, 200, 60), (230, 30, 30), (255, 255, 255)
HOLIDAY_STAR = (_GREEN, _RED, _WHITE, _RED, _GREEN)

SPECIAL_EVENTS = {
    "halloween": {
        "match": "not-so-scary halloween party",  # found in a lower-cased entity name
        "star_rgb": (255, 130, 20),  # the "*" after the park hours: one colour, or one per dot
        "landmark": "FriendlyJackOLanternLandmark",  # replaces the park's landmark (display/landmarks/pumpkins.py)
        "fireworks_show": "Disney's Not-So-Spooky Spectacular",  # plays the castle fireworks when it starts
        "fireworks_theme": "halloween",  # display/fireworks/fireworks.py THEMES
    },
    # The rest have no landmark or fireworks of their own yet; they just colour the star.
    # Their match strings are the events' published names: none is in the live data today.
    "christmas": {"match": "very merry christmas party", "star_rgb": HOLIDAY_STAR},
    "jollywood": {"match": "jollywood nights", "star_rgb": HOLIDAY_STAR},
    # Last: Magic Kingdom lists "... at Disney After Hours" all through party season, so every
    # more specific party above has to win over it.
    "after_hours": {"match": "disney after hours", "star_rgb": _RED},
    # Named by the schedule entry's own description rather than by the park's entities.
    "extended_evening": {"schedule": "extended evening", "star_rgb": (255, 215, 0)},
}

# A special event we can't name gets a white star.
DEFAULT_STAR_RGB = (255, 255, 255)

# The fireworks show a park runs on an ordinary night, and its castle-fireworks theme (None is the
# everyday look). A party night swaps in the party's own show and theme; see fireworks_show().
NIGHTLY_FIREWORKS = ("Happily Ever After", None)


def seasonal_event(children):
    """The SPECIAL_EVENTS key whose entities are in a park's children, or None. When a park
    lists more than one, the earliest in SPECIAL_EVENTS wins."""
    names = [item.get("name", "").lower().replace("’", "'") for item in children]
    for key, event in SPECIAL_EVENTS.items():
        if event.get("match") and any(event["match"] in name for name in names):
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
    """The schedule entry for a special event the park holds today (its local date), or one
    running now; None if there isn't one. The second case is a party that runs past midnight:
    dated yesterday, still going. Once it ends, yesterday's event no longer counts, even though
    the schedule still holds it."""
    now = now or datetime.now(timezone.utc)
    today = _local_today(park, now)
    for event in park.get("schedule") or []:
        if not is_special(event):
            continue
        if event.get("date") == today:
            return event
        start, end = _parse(event.get("openingTime")), _parse(event.get("closingTime"))
        if start and end and start.tzinfo and end.tzinfo and start <= now < end:
            return event
    return None


def _event_key(park, entry):
    """The SPECIAL_EVENTS key for a special schedule entry: named by its own description when it
    can be (extended evening hours), else the park's seasonal party; None if it can't be named."""
    description = entry.get("description", "").lower()
    for key, event in SPECIAL_EVENTS.items():
        if event.get("schedule") and event["schedule"] in description:
            return key
    key = park.get("seasonalEvent")
    return key if key in SPECIAL_EVENTS and SPECIAL_EVENTS[key].get("match") else None


def active_party(park, now=None):
    """The SPECIAL_EVENTS key of the special event the park is holding now, or None."""
    entry = special_event_now(park, now)
    return _event_key(park, entry) if entry else None


def fireworks_show(park, now=None):
    """(show name, fireworks theme) the park runs tonight, looked up from its schedule: the party's
    own show on a party night (Happily Ever After doesn't run then), else NIGHTLY_FIREWORKS."""
    event = SPECIAL_EVENTS.get(active_party(park, now), {})
    if event.get("fireworks_show"):
        return event["fireworks_show"], event.get("fireworks_theme")
    return NIGHTLY_FIREWORKS


def star_rgb(park, now=None):
    """Colour of the "*" after the park hours: the party's own (an RGB tuple, or a tuple of one per
    dot for a multicoloured star), gold for an unnamed special event, or None when there's no
    special event."""
    if not special_event_now(park, now):
        return None
    key = active_party(park, now)
    return SPECIAL_EVENTS[key]["star_rgb"] if key else DEFAULT_STAR_RGB
