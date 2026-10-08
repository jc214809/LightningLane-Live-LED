from datetime import datetime, timezone

import pytest

from utils.special_events import (
    DEFAULT_STAR_RGB, HOLIDAY_STAR, NIGHTLY_FIREWORKS, SPECIAL_EVENTS, active_party, fireworks_show, is_special, seasonal_event,
    special_event_now, star_rgb,
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
    (["Meet Santa at Mickey's Very Merry Christmas Party"], "christmas"),
    (["Holiday Show at Disney Jollywood Nights"], "jollywood"),
    (["Disney Enchantment at Disney After Hours at Magic Kingdom"], "after_hours"),
    # Magic Kingdom's list today: an After Hours show alongside the Halloween party's.
    (["Disney Enchantment at Disney After Hours at Magic Kingdom",
      "Mickey’s Boo-To-You Halloween Parade at Mickey's Not-So-Scary Halloween Party"], "halloween"),
    (["Extended Evening Hours"], None),
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


def test_fireworks_show_comes_from_tonights_schedule():
    now = et("2026-09-27 21:00")
    assert fireworks_show(mk(party("2026-09-27")), now) == ("Disney's Not-So-Spooky Spectacular", "halloween")
    assert fireworks_show(mk(party("2026-09-28")), now) == NIGHTLY_FIREWORKS, "not a party night"
    assert fireworks_show(mk(party("2026-09-27"), seasonal=None), now) == NIGHTLY_FIREWORKS, "unnamed event"
    assert fireworks_show({"name": "EPCOT"}, now) == NIGHTLY_FIREWORKS


def test_every_fireworks_theme_exists():
    from display.fireworks.fireworks import THEMES
    for key, event in SPECIAL_EVENTS.items():
        assert event.get("fireworks_theme") in (None, *THEMES), key
    assert NIGHTLY_FIREWORKS[1] in (None, *THEMES)


def test_every_event_is_fully_described():
    for key, event in SPECIAL_EVENTS.items():
        named_by = [event[k] for k in ("match", "schedule") if k in event]
        assert len(named_by) == 1 and named_by[0] == named_by[0].lower(), key
        star = event["star_rgb"]
        dots = star if isinstance(star[0], tuple) else [star]
        assert len(dots) in (1, 5), key  # one colour, or one per dot of the "*"
        assert all(len(rgb) == 3 and all(0 <= c <= 255 for c in rgb) for rgb in dots), key


def test_single_colour_stars_are_all_different():
    colours = [e["star_rgb"] for e in SPECIAL_EVENTS.values() if not isinstance(e["star_rgb"][0], tuple)]
    colours.append(DEFAULT_STAR_RGB)
    assert len(set(colours)) == len(colours)


def test_holiday_parties_get_the_green_red_and_white_star():
    assert SPECIAL_EVENTS["christmas"]["star_rgb"] == SPECIAL_EVENTS["jollywood"]["star_rgb"] == HOLIDAY_STAR
    assert set(HOLIDAY_STAR) == {(40, 200, 60), (230, 30, 30), (255, 255, 255)}
    assert HOLIDAY_STAR[2] == (255, 255, 255), "white centre"


def test_extended_evening_is_named_by_the_schedule_not_the_party_season():
    now = et("2026-09-27 21:30")
    eeh = party("2026-09-27", opens="21:00", closes="23:00", description="Extended Evening")
    assert active_party(mk(eeh), now) == "extended_evening", "even in a park holding a party season"
    assert star_rgb(mk(eeh, seasonal=None), now) == SPECIAL_EVENTS["extended_evening"]["star_rgb"] == (255, 215, 0), "gold"
    assert fireworks_show(mk(eeh), now) == NIGHTLY_FIREWORKS


def test_a_party_named_after_hours_colours_the_star():
    now = et("2026-09-27 20:00")
    assert star_rgb(mk(party("2026-09-27"), seasonal="after_hours"), now) == SPECIAL_EVENTS["after_hours"]["star_rgb"]
    assert fireworks_show(mk(party("2026-09-27"), seasonal="christmas"), now) == NIGHTLY_FIREWORKS
