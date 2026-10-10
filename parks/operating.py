"""
Whether each park is open, and when to refetch its schedule. The schedule decides when it's
usable (party nights and Early Entry included); otherwise fresh live data does. HTTP stays in
api.disney_api: this module only calls handle_park_schedule_update when a refresh is due.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from api.disney_api import handle_park_schedule_update, parse_timestamp
from utils import debug

_ATTRACTION_FRESHNESS_MINUTES = 20  # wider than the 5-min REST cycle and normal WS cadence
# Past the actual closing time with no next opening in the schedule, it's probably yesterday's (a failed
# refresh): trust it this long, then fall back to the freshness check.
_SCHEDULE_TRUST_HOURS = 6
_DAILY_REFRESH_HOUR = 3    # local time the new day's schedule becomes available to fetch
_DAILY_REFRESH_RETRY_UNTIL_HOUR = 9  # give up retrying once the park would normally be open
_DAILY_REFRESH_RETRY_MINUTES = 30


def _park_local_now(park):
    """Current time in the park's own timezone, or UTC if unknown (fails safe: the
    daily-refresh window just won't line up with local 3am for that park)."""
    tz_name = park.get("timezone")
    if tz_name:
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            debug.warning(f"{park.get('name')}: unknown timezone '{tz_name}', falling back to UTC.")
    return datetime.now(timezone.utc)


def _schedule_reflects_today(park, local_now):
    """True once handle_park_schedule_update has stored a schedule_date matching the
    park's current local date — i.e. the daily refresh actually got today's hours,
    not a stale/yesterday's OPERATING event the API hadn't rolled over yet."""
    return park.get("schedule_date") == local_now.strftime("%Y-%m-%d")


def _daily_schedule_refresh_due(park, local_now):
    """True within the once-daily 3am-9am local refresh window, with a 30-min
    retry backoff, until schedule_date matches today. See CLAUDE.md for why."""
    if local_now.hour < _DAILY_REFRESH_HOUR or local_now.hour >= _DAILY_REFRESH_RETRY_UNTIL_HOUR:
        return False
    if _schedule_reflects_today(park, local_now):
        return False

    last_attempt = park.get("_daily_refresh_last_attempt")
    if last_attempt is None:
        return True
    return (local_now - last_attempt) >= timedelta(minutes=_DAILY_REFRESH_RETRY_MINUTES)


def _attraction_is_fresh(attraction, now):
    ts = parse_timestamp(attraction.get("lastUpdatedTs"))
    return ts is not None and (now - ts) <= timedelta(minutes=_ATTRACTION_FRESHNESS_MINUTES)


def _park_days(schedule):
    """{date: (first opening, actual close)} over every timed entry of each park day: the
    regular hours, Early Entry and any party. Entries without full timestamps are skipped."""
    days = {}
    for event in schedule or []:
        date = event.get("date")
        start, end = parse_timestamp(event.get("openingTime")), parse_timestamp(event.get("closingTime"))
        if not (date and start and end):
            continue
        first, last = days.get(date, (start, end))
        days[date] = (min(first, start), max(last, end))
    return days


def _day_in_progress_close(days, now):
    started = [(date, span) for date, span in days.items() if span[0] <= now]
    return max(started)[1][1] if started else None


def actual_park_closing_time(park, now=None):
    """
    When the park day in progress really ends: the latest close of any of its entries, so a
    party's close on a party night, the regular close otherwise. The day in progress is the
    latest one that has opened; a party past midnight is dated the day it started, so at
    12:30am it's still that day. None with no usable schedule, or before the first opening.
    """
    return _day_in_progress_close(_park_days(park.get("schedule")), now or datetime.now(timezone.utc))


_SCHEDULE_OPEN, _SCHEDULE_CLOSED = "open", "closed"


def _schedule_window(park, now):
    """
    (window, actual close). The window is _SCHEDULE_OPEN while the schedule's park day runs
    (from its first opening, Early Entry included, to its actual closing time), _SCHEDULE_CLOSED
    once it's over or before it starts, None when the schedule can't say (no usable entries, or
    past the close long enough that it's probably stale): then the live data decides.
    """
    days = _park_days(park.get("schedule"))
    if not days:
        return None, None
    actual_close = _day_in_progress_close(days, now)
    if actual_close is None:
        return _SCHEDULE_CLOSED, None  # only future entries: the day hasn't started
    if now < actual_close:
        return _SCHEDULE_OPEN, actual_close
    next_opening_known = any(start > now for start, _ in days.values())
    if next_opening_known or now - actual_close <= timedelta(hours=_SCHEDULE_TRUST_HOURS):
        return _SCHEDULE_CLOSED, actual_close
    return None, actual_close


def _has_fresh_operating_ride(park, now):
    """A ride OPERATING with a wait and live data from the last _ATTRACTION_FRESHNESS_MINUTES:
    how a park counts as open when there's no schedule to go by."""
    for attraction in park.get("attractions", []):
        status = attraction.get("status")
        if status and status.upper() == "OPERATING" and attraction.get("waitTime") not in (None, ''):
            if _attraction_is_fresh(attraction, now):
                return True
            debug.log(f"{attraction['name']} ({park['name']}) is OPERATING but stale; not counted.")
    return False


def operating_and_why(park, now=None):
    """
    (operating, reason). With a usable schedule it alone decides: open from the park day's
    first opening to actual_park_closing_time (a party's close on a party night), whatever
    the rides say. Without one, a ride OPERATING with a wait and recent live data opens it.
    """
    now = now or datetime.now(timezone.utc)
    window, close = _schedule_window(park, now)
    if window == _SCHEDULE_OPEN:
        return True, f"schedule: open until {close.strftime('%H:%M')}"
    if window == _SCHEDULE_CLOSED:
        return False, f"schedule: closed at {close.strftime('%H:%M')}" if close else "schedule: not open yet"
    if _has_fresh_operating_ride(park, now):
        return True, f"no usable schedule; a ride is operating with live data from the last {_ATTRACTION_FRESHNESS_MINUTES} min"
    return False, f"no usable schedule; no ride is operating with live data from the last {_ATTRACTION_FRESHNESS_MINUTES} min"


def update_parks_operating_status(parks, fetch_schedules=True):
    """
    Sets each park's 'operating' key (and 'operatingReason') from operating_and_why, and
    flags 'schedule_refresh_needed' on a closed->open transition or the daily
    refresh window (see _daily_schedule_refresh_due). With fetch_schedules=False
    (the WS event loop) that flag is only set, never acted on — the REST thread
    calls again with fetch_schedules=True to actually perform the fetch. See
    CLAUDE.md for the full design and why both triggers exist.
    """

    for park in parks:
        actual_close = actual_park_closing_time(park)
        park["actualParkClosingTime"] = actual_close.isoformat() if actual_close else ""
        is_park_open, reason = operating_and_why(park)
        if park.get("operating") != is_park_open:
            debug.info(f"{park.get('name')}: {'open' if is_park_open else 'closed'} ({reason})")
        park["operatingReason"] = reason
        local_now = _park_local_now(park)

        if not park.get("operating") and is_park_open:
            park["schedule_refresh_needed"] = True
        elif _daily_schedule_refresh_due(park, local_now):
            park["schedule_refresh_needed"] = True
            park["_daily_refresh_last_attempt"] = local_now

        # Update the operating status
        park["operating"] = is_park_open

        if fetch_schedules and park.get("schedule_refresh_needed"):
            handle_park_schedule_update(park)
            park["schedule_refresh_needed"] = False

    return parks

