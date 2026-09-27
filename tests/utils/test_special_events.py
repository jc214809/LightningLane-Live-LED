from datetime import datetime, timezone

import pytest

from utils.special_events import (
    DEFAULT_STAR_RGB, SPECIAL_EVENTS, active_party, is_special, seasonal_event, special_event_now, star_rgb,
)

ET = "America/New_York"


def party(date, opens="19:00", closes_date=None, closes="00:00", description="Special Ticketed Event"):
    """A schedule entry like the live API's: 7pm to midnight, closing on the next day's date."""
    closes_date = closes_date or date
    return {"type": "TICKETED_EVENT", "date": date, "description": description,
            "openingTime": f"{date}T{opens}:00-04:00", "closingTime": f"{closes_date}T{closes}:00-04:00"}


def et(day_time):
    """An aware 'now' from an Orlando wall-clock time, e.g. '2026-09-27 20:00'."""
    return datetime.fromisoformat(day_time + ":00-04:00").astimezone(timezone.utc)


def mk(*events, seasonal="halloween"):
    return {"name": "Magic Kingdom", "timezone": ET, "seasonalEvent": seasonal, "schedule": list(events)}


def test_is_special_matches_ticketed_parties_and_extended_evenings():
    assert is_special(party("2026-09-27"))
    assert is_special(party("2026-09-27", description="Extended Evening Hours"))
    assert not is_special(party("2026-09-27", description="Early Entry"))
    assert not is_special({"type": "OPERATING", "description": "Special Ticketed Event"})
    assert not is_special({})


@pytest.mark.parametrize("names, expected", [
    (["Mickey’s Boo-To-You Halloween Parade at Mickey's Not-So-Scary Halloween Party"], "halloween"),
    (["Stitch’s Masquerade Mashup at Mickey’s Not-So-Scary Halloween Party"], "halloween"),
    (["Space Mountain", "Haunted Mansion"], None),
    ([{}], None),
    ([], None),
])
def test_seasonal_event_names_the_party_from_the_parks_entities(names, expected):
    children = [n if isinstance(n, dict) else {"name": n} for n in names]
    assert seasonal_event(children) == expected


def test_party_day_counts_all_day_in_the_parks_own_timezone():
    park = mk(party("2026-09-27"))
    assert special_event_now(park, et("2026-09-27 08:00")), "morning of a party night"
    # 9pm in Orlando is already the 28th in UTC; the park's date is still the 27th.
    assert special_event_now(park, et("2026-09-27 21:00"))


def test_party_running_past_midnight_counts_until_it_ends():
    park = mk(party("2026-09-27", closes_date="2026-09-28", closes="01:00"))
    assert special_event_now(park, et("2026-09-28 00:30")), "still going after midnight"
    assert not special_event_now(park, et("2026-09-28 01:00")), "over at closing time"
    assert not special_event_now(park, et("2026-09-28 09:00")), "yesterday's party doesn't mark the next day"


def test_no_special_event_without_one_in_the_schedule():
    park = mk(party("2026-09-27", description="Early Entry"))
    assert not special_event_now(park, et("2026-09-27 20:00"))
    assert not special_event_now({"name": "Nowhere"}, et("2026-09-27 20:00"))


def test_malformed_times_and_unknown_timezone_fail_safe():
    park = mk({"type": "TICKETED_EVENT", "date": "2026-09-26", "description": "Special Ticketed Event",
               "openingTime": "not a time", "closingTime": None})
    assert not special_event_now(park, et("2026-09-27 20:00"))
    park = mk(party("2026-09-27"))
    park["timezone"] = "Mars/Olympus_Mons"
    assert special_event_now(park, datetime(2026, 9, 27, 12, tzinfo=timezone.utc)), "falls back to UTC"


def test_active_party_needs_both_a_party_tonight_and_a_known_name():
    now = et("2026-09-27 20:00")
    assert active_party(mk(party("2026-09-27")), now) == "halloween"
    assert active_party(mk(party("2026-09-27"), seasonal=None), now) is None, "unnamed special event"
    assert active_party(mk(party("2026-09-28")), now) is None, "party-season night with no party"
    assert active_party(mk(party("2026-09-27"), seasonal="bogus"), now) is None


def test_star_is_the_partys_colour_gold_when_unnamed_and_absent_without_an_event():
    now = et("2026-09-27 20:00")
    assert star_rgb(mk(party("2026-09-27")), now) == SPECIAL_EVENTS["halloween"]["star_rgb"]
    assert star_rgb(mk(party("2026-09-27"), seasonal=None), now) == DEFAULT_STAR_RGB
    assert star_rgb(mk(party("2026-09-28")), now) is None


def test_every_event_is_fully_described():
    for key, event in SPECIAL_EVENTS.items():
        assert event["match"] == event["match"].lower(), key
        assert len(event["star_rgb"]) == 3 and all(0 <= c <= 255 for c in event["star_rgb"]), key
