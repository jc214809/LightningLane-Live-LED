"""The Fireworks shows card: the version of each show, and whether it plays or runs once as a test."""
from html import escape

from settings_page.form import show_names
from settings_page.markup import CASTLE_KEY, _attr, _led, _notice, _options, _section, _switch_input, landmarks
from utils.config import SHOW_VERSIONS


def _show_row(i, name, entry):
    """One show's row: its version, whether it plays, and whether it plays once at start-up (a test)."""
    label = _attr(name)
    return (
        f'<div class="show"><div class="show-name">{escape(name)}'
        f'<input type="hidden" name="show_name_{i}" value="{label}"></div><div class="show-ctl">'
        f'<label><span class="mini">Version</span>'
        + _options(f"show_version_{i}", [(v, v.upper() if v != "default" else "Default") for v in SHOW_VERSIONS],
                   entry.get("version", "default"), f' aria-label="{label} version"')
        + '</label><label><span class="mini">Play</span>'
        + _switch_input(f"show_enabled_{i}", entry.get("enabled", True), f' aria-label="Play {label}"')
        + '</label><label><span class="mini">Test</span>'
        + _switch_input(f"show_force_{i}", entry.get("force"), f' aria-label="Play {label} at start-up"')
        + "</label></div></div>")


def shows_card(config):
    shows_by_name = {e["name"]: e for e in config.get("shows") or []
                     if isinstance(e, dict) and isinstance(e.get("name"), str)}
    show_rows = "".join(_show_row(i, name, shows_by_name.get(name, {})) for i, name in enumerate(show_names(config)))
    castle = landmarks().get(CASTLE_KEY)
    show_scene = (f'<div class="previews">{_led(castle, "The castle on the board")}<p class="hint">Each show plays '
                  "over the board's castle when that show starts in the park, by ThemeParks.wiki's showtimes.</p></div>"
                  if castle else "")
    return _section("shows", "Fireworks shows", "What plays when each show starts in the park.", (
        show_scene
        + f'<div class="shows">{show_rows}</div>'
        + _notice("info", "<strong>Default</strong> plays the castle fireworks for five minutes. <strong>V1</strong> "
                          "and <strong>V2</strong> play the whole show in time with its music. <strong>Test</strong> "
                          "plays a show once each time the app starts; turn it off when you're done.")
    ), "sparkle")
