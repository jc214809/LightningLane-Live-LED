"""The Trip countdown card: what the board shows between parks, and the trips it counts down to."""

from html import escape

from settings_page.form import trip_rows
from settings_page.markup import _attr, _input, _section, _switch, icon, sub_dict
from utils.trips import active_trip, countdown_message, parse_trips


def _trip(index, start="", end="", name="", on_board=False):
    """on_board: the trip the countdown shows now, tagged so."""
    i = index
    name_input = _input(f"trip_name_{i}", name, extra=' placeholder="Spring Break"')
    remove = (
        f'<label class="trip-x" for="trip_remove_{i}" title="Remove this trip"><input type="checkbox" '
        f'id="trip_remove_{i}" name="trip_remove_{i}" aria-label="Remove this trip">{icon("x")}</label>'
    )
    tag = '<span class="tag">On the board now</span>' if on_board else ""
    return (
        f'<div class="trip{" next" if on_board else ""}">{tag}<div class="wide"><label class="mini" for="trip_name_{i}">Name</label>'
        f"{name_input}</div>"
        f'<div><label class="mini" for="trip_start_{i}">Start</label>{_input(f"trip_start_{i}", start, "date")}</div>'
        f'<div><label class="mini" for="trip_end_{i}">End <span class="hint">(optional)</span></label>'
        f"{_input(f'trip_end_{i}', end, 'date')}</div>{remove}</div>"
    )


def _countdown_preview(config, enabled, today=None):
    """(the LED-style preview of what the countdown shows today, the Trip it's counting to or None),
    in utils.trips' own words."""
    trip = active_trip(parse_trips(config), today)
    if not enabled:
        return '<p class="hint countdown">Off: the board goes straight from park to park.</p>', None
    if trip is None:
        return '<p class="hint countdown">No trip coming up: the board skips the countdown until you add one.</p>', None
    number, lines = countdown_message(trip, today)
    big = f'<span class="big">{escape(number)}</span>' if number else ""
    words = "".join(f'<span class="line">{escape(line)}</span>' for line in lines)
    when = f"{trip.start:%B} {trip.start.day}, {trip.start.year}"
    return (
        f'<div class="countdown"><div class="led" role="img" aria-label="{_attr(" ".join(filter(None, (number,) + lines)))}">'
        f'{big}{words}</div><p class="hint">What the board shows between parks today, counting to '
        f"<strong>{escape(trip.name or 'your trip')}</strong> on {when}.</p></div>"
    ), trip


def _same_trip(row, trip):
    """Whether a trip_rows row (start, end, name as the form shows them) is this Trip."""
    if trip is None:
        return False
    start, end, name = row
    return (
        start == trip.start.isoformat()
        and (end or None) == (trip.end.isoformat() if trip.end else None)
        and (name.strip() or None) == trip.name
    )


def trips_card(config, today=None):
    """today: the date the countdown preview counts from."""
    countdown = sub_dict(config, "trip_countdown")
    rows = trip_rows(config)
    preview, counting_to = _countdown_preview(config, countdown.get("enabled", False), today)
    return _section(
        "trips",
        "Trip countdown",
        "Days to go until your next trip, between the parks.",
        (
            preview
            + _switch("trips_enabled", "Show the countdown", countdown.get("enabled", False))
            + '<div class="trips" id="trip-list">'
            + "".join(_trip(i, *row, on_board=_same_trip(row, counting_to)) for i, row in enumerate(rows))
            + ("" if rows else _trip(0))
            + "</div>"  # a blank row to start from only when there are no trips
            + f'<template id="trip-row">{_trip("N")}</template>'
            + f'<p style="margin-top:12px"><button type="button" class="ghost" id="add-trip">{icon("plus")}Add a trip'
            f"</button></p>"
        ),
        "calendar",
    )
