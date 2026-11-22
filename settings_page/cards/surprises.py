"""The Surprise characters card (a link to its own page) and the Testing card, which forces one character."""

from html import escape

from settings_page.form import character_label, surprise_characters, surprise_names
from settings_page.markup import _field, _options, _section, _switch, icon


def surprises_card():
    cast = sorted(character_label(n) for n in surprise_characters())
    cast_list = (
        f'<ul class="cast" aria-label="The characters">{"".join(f"<li>{escape(n)}</li>" for n in cast)}</ul>'
        if cast
        else ""
    )
    return _section(
        "surprises",
        "Surprise characters",
        "Who now and then drops in between ride screens and park titles, and how often.",
        (
            cast_list + f'<a class="btn secondary" href="/surprises">{icon("sparkle")}<span>Choose '
            f"{f'from all {len(cast)} characters and their' if cast else 'characters and'} chances</span></a>"
        ),
        "sparkle",
    )


def testing_card(config):
    return _section(
        "testing",
        "Testing",
        "For checking the board; turn them off when you're done.",
        (
            _switch("debug", "Debug logging", config.get("debug", False), "More detail in the board's log.")
            + _field(
                "force_surprise",
                "Surprise on every ride screen",
                _options(
                    "force_surprise",
                    [("", "None")] + sorted(((n, character_label(n)) for n in surprise_names()), key=lambda o: o[1]),
                    config.get("force_surprise") or "",
                ),
                "Plays that character on every ride screen, for checking it on the board. "
                "Set it back to None when you're done.",
            )
        ),
        "flask",
    )
