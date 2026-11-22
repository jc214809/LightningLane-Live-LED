"""The Display card: the panel's brightness, all day or by the time of day."""

from settings_page.form import BRIGHTNESS
from settings_page.markup import CASTLE_KEY, _attr, _field, _input, _section, _switch, landmarks, sub_dict

LEVEL = ' min="1" max="100" inputmode="numeric"'  # a brightness box's attributes


def _brightness_previews():
    """The castle at each brightness the Display card sets; the script dims them as the numbers change."""
    castle = landmarks().get(CASTLE_KEY)
    if not castle:
        return ""
    return (
        '<div class="previews" aria-hidden="true">'
        + "".join(
            f'<div id="pv-{k}-box"><span class="led"><img id="pv-{k}" src="{castle}" alt=""></span>'
            f'<div class="preview-label" id="pv-{k}-l">{label}</div></div>'
            for k, label in (("all", "All day"), ("day", "Day"), ("night", "Night"))
        )
        + "</div>"
    )


def _scheduled(key, label, value, start_key, start_label, start):
    """A brightness box and the time it starts, side by side."""
    return (
        f'<div><label class="mini" for="{key}">{label}</label>{_input(key, value, "number", LEVEL)}</div>'
        f'<div><label class="mini" for="{start_key}">{start_label}</label>{_input(start_key, start, "time")}</div>'
    )


def _schedule_fields(schedule):
    """The day and night brightness rows; schedule is None when none is saved (suggested values show)."""
    sched = schedule or {}
    return (
        '<div class="schedule-wrap" id="schedule">'
        + (
            ""
            if schedule
            else '<p class="hint schedule-note">Not set up yet: these are suggested starting values, '
            "saved only if you turn this on.</p>"
        )
        + '<div class="schedule">'
        + _scheduled(
            "bright_day",
            "Day brightness",
            sched.get("day", 80),
            "day_start",
            "Day starts",
            sched.get("day_start", "07:00"),
        )
        + _scheduled(
            "bright_night",
            "Night brightness",
            sched.get("night", 15),
            "night_start",
            "Night starts",
            sched.get("night_start", "22:00"),
        )
        + "</div></div>"
    )


def display_card(config, blanks):
    """blanks: what each blank Panel field says for the chosen Pi model (cards.panel.panel_blanks)."""
    brightness = sub_dict(config, "matrix").get(BRIGHTNESS)
    schedule = config.get("brightness_schedule") if isinstance(config.get("brightness_schedule"), dict) else None
    return _section(
        "display",
        "Display",
        "How bright the LED panel is, all day or by the time of day.",
        (
            _brightness_previews()
            + _field(
                f"matrix_{BRIGHTNESS}",
                "Brightness",
                _input(
                    f"matrix_{BRIGHTNESS}",
                    "" if brightness is None else brightness,
                    "number",
                    f'{LEVEL} placeholder="{_attr(blanks.get(BRIGHTNESS, "Default"))}" data-key="{BRIGHTNESS}"',
                ),
                "1 to 100. Blank uses the Pi model's (see Panel). A schedule, when on, takes over from it.",
            )
            + _switch(
                "brightness_schedule",
                "Day and night brightness",
                schedule is not None,
                "Dim the board at night, by the board's clock.",
            )
            + _schedule_fields(schedule)
        ),
        "sun",
    )
