"""The Panel card (Pi model, size, rotation, the settings a Pi model sets) and the Advanced card (the rest)."""

import cli
from settings_page.form import BRIGHTNESS, panel_size
from settings_page.markup import (
    CASTLE_KEY,
    _attr,
    _field,
    _input,
    _json_for_script,
    _notice,
    _options,
    _section,
    icon,
    landmarks,
    sub_dict,
)

# The Panel card's settings, the ones a Pi model sets (and rotation), with their labels; the rest
# are under Advanced. Rows and columns are the Panel size dropdown's.
PANEL_SETTINGS = {
    "led_pixel_mapper": "Rotation",
    "led_gpio_mapping": "GPIO mapping",
    "led_slowdown_gpio": "GPIO slowdown",
    "led_pwm_lsb_nanoseconds": "PWM timing (ns)",
}
SIZE_SETTINGS = ("led_rows", "led_cols")
# Rotation's choices: --led-pixel-mapper values. A saved one not here is offered as it is.
ROTATIONS = (
    ("Rotate:180", "Upside down (Rotate:180)"),
    ("Rotate:90", "A quarter turn (Rotate:90)"),
    ("Rotate:270", "Three quarters (Rotate:270)"),
    ("Mirror:H", "Mirrored left to right (Mirror:H)"),
    ("Mirror:V", "Mirrored top to bottom (Mirror:V)"),
)


def panel_blanks(config, panel):
    """(the Pi model chosen, what each blank panel field says for it). panel: form.PanelChoices, or None."""
    chosen_model = config.get("pi_model") if config.get("pi_model") in cli.MODEL_DEFAULTS else cli.AUTO
    blanks = panel.blanks.get(panel.auto_model if chosen_model == cli.AUTO else chosen_model, {}) if panel else {}
    return chosen_model, blanks


def _matrix_field(key, label, help_text, options, switch, value, blank="Default"):
    """A config.json "matrix" setting's row; blank, it says what the board gets (blank)."""
    name = f"matrix_{key}"
    data = f' data-key="{key}"'
    if key == "led_pixel_mapper":
        choices = list(ROTATIONS) + ([(value, value)] if value and value not in dict(ROTATIONS) else [])
        control = _options(name, [("", blank)] + choices, value or "", data)
        help_text = "Which way up the panel is mounted, for a board that shows upside down or sideways."
    elif switch:
        chosen = "" if value is None else ("true" if value else "false")
        control = _options(name, [("", blank), ("true", "On"), ("false", "Off")], chosen, data)
    elif options:
        chosen = "" if value is None else str(value)
        control = _options(name, [("", blank)] + [(str(o), str(o) or "None") for o in options], chosen, data)
    else:
        control = _input(
            name, "" if value is None else value, extra=f' class="mono" placeholder="{_attr(blank)}"{data}'
        )
    return _field(name, label, control, help_text or "")


def _rotation_preview():
    castle = landmarks().get(CASTLE_KEY)
    if not castle:
        return ""
    return (
        f'<div class="previews"><div><span class="led"><img id="pv-rot" src="{castle}" alt=""></span>'
        '<div class="preview-label" id="pv-rot-l">Drawn as is</div></div><p class="hint">Rotation turns the whole '
        "picture. Pick the one that puts the castle the right way up on your panel.</p></div>"
    )


def _matrix_settings():
    """{matrix key: (help text, options, is a switch)} for every setting the driver takes."""
    return {key: (help_text, options, switch) for key, help_text, options, switch, _ in cli.matrix_settings()}


def _model_and_size(matrix, panel, chosen_model):
    """The Pi model and Panel size dropdowns (and the script's data for the blanks); "" with no panel choices."""
    if not panel:
        return ""
    for_script = {"auto": panel.auto_model, "blanks": panel.blanks}
    return (
        _field(
            "pi_model",
            "Pi model",
            _options("pi_model", panel.models, chosen_model),
            "Which Raspberry Pi drives the panel: it sets the defaults below. Automatic is the one this board reports.",
        )
        + _field(
            "panel_size",
            "Panel size",
            _options("panel_size", panel.sizes, panel_size(matrix)),
            "Columns x rows, as on the panel's label.",
        )
        + f'<script type="application/json" id="panel-blanks">{_json_for_script(for_script)}</script>'
    )


def panel_card(config, panel, chosen_model, blanks):
    """panel: form.PanelChoices (None leaves the Pi model and size dropdowns off); chosen_model and blanks
    from panel_blanks."""
    matrix = sub_dict(config, "matrix")
    settings = _matrix_settings()
    panel_fields = "".join(
        _matrix_field(key, label, *settings[key], matrix.get(key), blanks.get(key, "Default"))
        for key, label in PANEL_SETTINGS.items()
    )
    return _section(
        "panel",
        "Panel",
        "Which Pi and panel this is, and which way up it's mounted.",
        (
            _rotation_preview()
            + _model_and_size(matrix, panel, chosen_model)
            + _notice(
                "info",
                "Each setting left blank is the Pi model's default, shown greyed out. Set one to "
                "customise this board, like Rotation for a panel mounted upside down; clear it to go back.",
            )
            + panel_fields
        ),
        "board",
    )


def advanced_card(config, blanks):
    matrix = sub_dict(config, "matrix")
    advanced_fields = "".join(
        _matrix_field(
            key,
            key.removeprefix("led_").replace("_", " ").capitalize(),
            help_text,
            options,
            switch,
            matrix.get(key),
            blanks.get(key, "Default"),
        )
        for key, (help_text, options, switch) in _matrix_settings().items()
        if key != BRIGHTNESS and key not in PANEL_SETTINGS and key not in SIZE_SETTINGS
    )
    return (
        '<details class="card" id="advanced"><summary class="card-head">'
        f'<span class="card-icon">{icon("sliders")}</span><div><h2>Advanced</h2>'
        "<p>Panel hardware. Most boards never need these.</p></div>"
        f'<span class="chev">{icon("chevron")}</span></summary><div class="card-body">'
        + _notice(
            "warn",
            "The wrong panel settings can leave the board dark or flickering. Blank leaves each one to "
            "the Pi model's default. Size, rotation and timing are in Panel.",
        )
        + advanced_fields
        + "</div></details>"
    )
