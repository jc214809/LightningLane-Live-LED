"""The Parks card: the parks the board cycles through, as chips in order, with the landmark each plays before."""
from html import escape

from settings_page.form import WDW_PARKS
from settings_page.markup import _attr, _field, _input, _json_for_script, _section, icon, landmark_src, landmarks


def _park_chip(name, unknown=False):
    """One chosen park: posted as "park" in page order. The X is a checkbox, so removing works
    without the script; the arrow (script only) moves it one place earlier."""
    label = _attr(name)
    title = ' title="Not a ThemeParks.wiki park name"' if unknown else ""
    # The landmark the board plays before this park; the script fills it in for a park added on the page.
    src = landmark_src(name) if name else None
    scene = (f'<span class="led"><img class="park-landmark" src="{src or ""}" alt="" width="64" height="32"'
             f'{"" if src else " hidden"}><span class="noland"{" hidden" if src else ""}>Title only</span></span>')
    return (f'<li class="park-chip{" unknown" if unknown else ""}"{title}><input type="hidden" name="park" value="{label}">'
            f'{scene}<span class="park-name">{escape(name)}</span>'
            f'<button type="button" class="chip-btn js-only" hidden aria-label="Move earlier: {label}">{icon("left")}</button>'
            f'<label class="chip-x" title="Remove"><input type="checkbox" name="park_remove" value="{label}" '
            f'aria-label="Remove {label}">{icon("x")}</label></li>')


def parks_card(config, park_names):
    """park_names: [(name, destination)] for the picker's suggestions, [] when the list hasn't loaded."""
    parks = config.get("parks") if isinstance(config.get("parks"), list) else list(WDW_PARKS)
    known = {name.lower() for name, _ in park_names}
    chips = "".join(_park_chip(p, bool(known) and p.lower() not in known) for p in parks if isinstance(p, str))
    suggestions = "".join(f'<option value="{_attr(n)}">{escape(d)}</option>' for n, d in park_names)
    add_input = _input("park_add", extra=' list="park-names" autocomplete="off" placeholder="Start typing a park" '
                                         'aria-describedby="park-error"')
    add = (f'<div class="add-row">{add_input}'
           f'<button type="button" class="secondary js-only" id="park-add-btn" hidden>{icon("plus")}Add</button></div>'
           f'<datalist id="park-names">{suggestions}</datalist>'
           '<p class="field-error" id="park-error" role="alert" hidden></p>')
    return _section("parks", "Parks", "Which parks the board cycles through, in this order, with the landmark "
                                      "it plays before each one.", (
        f'<ol class="park-chips" id="park-chips" aria-label="Parks, in order">{chips}</ol>'
        + f'<template id="park-chip">{_park_chip("")}</template>'
        + f'<script type="application/json" id="park-scenes">{_json_for_script(landmarks())}</script>'
        + _field("park_add", "Add a park", add,
                 "Any park on ThemeParks.wiki: start typing and pick it from the list. It goes on the end; "
                 "the arrow moves a park earlier." if park_names else
                 "The list of parks hasn't loaded yet (the board needs the internet for it): type the name "
                 "exactly as ThemeParks.wiki has it.")
    ), "pin")
