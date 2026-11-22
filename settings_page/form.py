"""config.json to the settings page's form and back. No HTTP or HTML here (server.py and
page.py): apply_form takes the posted fields and returns the config to save, or what's wrong.

Only the keys the page shows change; anything else in config.json (old keys, keys a newer
version adds) is kept as it is. Every check is the app's own, so a saved config starts the app.
"""
import copy
import re
from datetime import time
from typing import NamedTuple

import cli
from settings_page.surprise_form import surprise_names
# Re-exported: callers (server.py, the pages, tests) import all of these from settings_page.form.
from settings_page.surprise_form import (CHARACTER_NAMES, MAX_RIDE_NAME, MAX_RIDES_PER_CHARACTER, SurpriseRow,  # noqa: F401
                                         apply_surprises, character_label, default_rides, import_surprises,
                                         percent_text, snapshot_surprises, surprise_characters, surprise_rows)
from utils.config import (DEFAULT_VOLUME, SHOW_VERSIONS, WS_PROTOCOLS, has_api_key, parse_brightness_schedule,
                          pushover_keys)
from utils.special_events import NIGHTLY_FIREWORKS, SPECIAL_EVENTS
from utils.trips import parse_date

WDW_PARKS = ("Magic Kingdom", "EPCOT", "Hollywood Studios", "Animal Kingdom")
# Up front on the page; the rest of "matrix" is under Advanced.
BRIGHTNESS = "led_brightness"
# Saved keys are never sent back to the browser: the page shows their last few letters, and a
# blank field keeps the saved one.
SHOWN_KEY_LETTERS = 4
_TRIP_FIELD = re.compile(r"trip_start_(\d+)$")
_SHOW_FIELD = re.compile(r"show_name_(\d+)$")


def masked(key):
    """A saved API key as the page shows it: its last letters only, or "" when there's none."""
    if not has_api_key(key):
        return ""
    return "•" * 4 + key.strip()[-SHOWN_KEY_LETTERS:]


class PanelChoices(NamedTuple):
    models: list  # (value, text) for the Pi model dropdown, Automatic first
    sizes: list  # (value, text) for the Panel size dropdown
    auto_model: str  # what Automatic is on this board: a model key, or "" for none
    blanks: dict  # model key ("" for none) -> {matrix key: what that field says when left blank}


PANEL_SIZES = ("64x64", "64x32")


def panel_choices(config, detected, detected_text):
    """The Pi model and Panel size dropdowns, and what each blank panel field says for each model
    ("Pi 4 default: 4", or the driver's "Default: 130"). Automatic says what it is on this board
    (cli.pick_model). detected, detected_text: cli.pi_model()."""
    matrix = config.get("matrix") if isinstance(config.get("matrix"), dict) else {}
    auto_model, why = cli.pick_model(None, detected, detected_text)
    auto = cli.MODEL_NAMES[auto_model] if auto_model else f"none: {why}"
    sizes = list(PANEL_SIZES)
    if panel_size(matrix) not in sizes:  # a size set by hand, like 128x32: offered as it is
        sizes.append(panel_size(matrix))
    driver = cli.matrix_defaults()

    def texts(name, defaults):
        """What each blank field says: the model's default, named for it, else the driver's."""
        found = {}
        for key, value in driver.items():
            if key in defaults:
                found[key] = f"{f'{name} default' if name else 'Default'}: {_shown(defaults[key])}"
            else:
                found[key] = f"Default: {_shown(value)}" if value not in (None, "") else "Default"
        return found
    blanks = {model: texts(cli.MODEL_NAMES[model], defaults) for model, defaults in cli.MODEL_DEFAULTS.items()}
    blanks[""] = texts(None, cli.BONNET if detected_text else {})  # a Pi we don't know gets the bonnet's
    return PanelChoices([(cli.AUTO, f"Automatic ({auto})")] + [(m, n) for m, n in cli.MODEL_NAMES.items()],
                        [(z, z) for z in sizes], auto_model or "", blanks)


def _shown(value):
    return "On" if value is True else "Off" if value is False else value


def panel_size(matrix):
    """config.json's matrix size as "64x32"; 64 columns and 32 rows (the driver's) where unset."""
    return f"{matrix.get('led_cols') or 64}x{matrix.get('led_rows') or 32}"


def show_names(config):
    """Every show the board plays (the nightly one, then each party's), then any others config.json lists."""
    names = [NIGHTLY_FIREWORKS[0]] + [e["fireworks_show"] for e in SPECIAL_EVENTS.values() if e.get("fireworks_show")]
    shows = config.get("shows")
    for entry in shows if isinstance(shows, list) else []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"] not in names:
            names.append(entry["name"])
    return list(dict.fromkeys(names))


def trip_rows(config):
    """config.json's trips as (start, end, name) strings for the form's date fields, soonest start first (one whose
    start isn't a date goes last, as it was)."""
    entries = (config.get("trip_countdown") or {}).get("trip_dates")
    rows = []
    for entry in entries if isinstance(entries, list) else []:
        entry = entry if isinstance(entry, dict) else {"start": entry}
        rows.append(tuple(_date_text(entry.get(k)) if k != "name" else str(entry.get(k) or "")
                          for k in ("start", "end", "name")))
    return sorted(rows, key=lambda row: _by_start(row[0]))


def _by_start(text):
    """A sort key: a trip's start date, or after every date when it isn't one."""
    try:
        return 0, parse_date(text)
    except (TypeError, ValueError):
        return 1, None


def _date_text(value):
    try:
        return parse_date(value).isoformat() if value else ""
    except (TypeError, ValueError):
        return str(value)


def chosen_device(form):
    """The speaker the form picks: one from the list, one typed under Other device, or None."""
    def one(name):
        return (form.get(name) or [""])[0].strip()
    return (one("sound_device_custom") if one("sound_device") == "custom" else one("sound_device")) or None


def volume_from_form(form):
    """(volume, problem) from the form's Volume: blank is DEFAULT_VOLUME."""
    text = (form.get("sound_volume") or [""])[0].strip()
    if not text:
        return DEFAULT_VOLUME, None
    if re.fullmatch(r"\d+", text) and int(text) <= 100:
        return int(text), None
    return None, f"Volume should be 0 to 100, not {text!r}."


def _one(form, name, default=""):
    """A form field's first value, stripped; default when the form doesn't have it (or has it empty)."""
    return (form.get(name) or [default])[0].strip()


def _checked(form, name):
    return _one(form, name) == "on"


def _section(new, key):
    """new[key] as a dict, made (replacing anything else) if it isn't one."""
    if not isinstance(new.get(key), dict):
        new[key] = {}
    return new[key]


def _field_indexes(pattern, form):
    """The numbers in the form's field names that match pattern (trip_start_3: 3), in order."""
    return sorted(int(m.group(1)) for m in map(pattern.match, form) if m)


def apply_form(config, form, park_names=()):
    """(the config to save, [problems]) from the posted form: {field: [values]}, as
    urllib.parse.parse_qs(..., keep_blank_values=True) gives it. With any problem, nothing
    should be saved. park_names: park_names.ParkNames.names(), the names a park may have."""
    new = copy.deepcopy(config)
    problems = []
    _apply_live_updates(new, form, problems)
    _apply_pushover(new, form, problems)
    _apply_parks(new, form, problems, park_names)
    _apply_trips(new, form, problems)
    _apply_sound(new, form, problems)
    _apply_shows(new, form, problems)
    _apply_panel(new, form, problems)
    _apply_brightness_schedule(new, form, problems)
    new["debug"] = _checked(form, "debug")
    _apply_force_surprise(new, form, problems)
    return new, problems


def _apply_live_updates(new, form, problems):
    """API keys and live updates."""
    ws = _section(new, "websocket")
    ws["enabled"] = _checked(form, "ws_enabled")
    protocol = _one(form, "ws_protocol", "legacy")
    if protocol in WS_PROTOCOLS:
        ws["protocol"] = protocol
    else:
        problems.append(f"Live update protocol should be one of {', '.join(WS_PROTOCOLS)}, not {protocol!r}.")
    if _one(form, "themeparks_key"):
        ws["api_key"] = _one(form, "themeparks_key")
    if ws["enabled"] and not has_api_key(ws.get("api_key")):
        problems.append("Live updates need a ThemeParks.wiki API key (or turn them off).")
    if _one(form, "weather_key"):
        _section(new, "weather")["apikey"] = _one(form, "weather_key")


def _apply_pushover(new, form, problems):
    """Pushover, for sending the sign-in PIN to a phone: kept out of config.json until a key is typed."""
    if "pushover_user" not in form:  # the page always posts it; a form without it leaves Pushover alone
        return
    typed = {key: _one(form, field) for key, field in (("user_key", "pushover_user"), ("app_token", "pushover_token"))
             if _one(form, field)}
    if not (typed or isinstance(new.get("pushover"), dict)):
        return
    pushover = _section(new, "pushover")
    pushover.update(typed)
    pushover["enabled"] = _checked(form, "pushover_enabled")
    if pushover["enabled"] and not pushover_keys(new):
        problems.append("Sending the PIN needs both a Pushover user key and an app token (or turn it off).")


def _typed_parks(form):
    """The park names the form names, in order: the chips less any ticked to remove, then the added one(s)."""
    removed = {p.strip().lower() for p in form.get("park_remove", [])}
    return [p for p in form.get("park", []) if p.strip().lower() not in removed] + _one(form, "park_add").split(",")


def _apply_parks(new, form, problems, park_names):
    """Parks: the chips in order, less any ticked to remove, then the added one(s), named as the
    list has them. With no list (never fetched), names can't be checked, so they're taken as typed."""
    known = {name.lower(): name for name, _ in park_names}
    parks = []
    for typed in _typed_parks(form):
        typed = " ".join(typed.split())
        if not typed or typed.lower() in (p.lower() for p in parks):
            continue
        if known and typed.lower() not in known:
            problems.append(f"{typed!r} isn't a ThemeParks.wiki park: pick one from the list.")
        parks.append(known.get(typed.lower(), typed))
    if not parks:
        problems.append("Pick at least one park.")
    new["parks"] = parks


def _apply_trips(new, form, problems):
    """Trip countdown."""
    countdown = _section(new, "trip_countdown")
    countdown["enabled"] = _checked(form, "trips_enabled")
    trips = []
    for index in _field_indexes(_TRIP_FIELD, form):
        trip = _trip_from_form(form, index, problems)
        if trip is not None:
            trips.append(trip)
    # Soonest first, so config.json reads in order as the page does (every start here is a date).
    countdown["trip_dates"] = sorted(trips, key=lambda t: parse_date(t["start"] if isinstance(t, dict) else t))
    countdown.pop("trip_date", None)  # the old single date; trip_dates replaces it


def _trip_from_form(form, index, problems):
    """One trip row as config.json holds it (a bare start date, or {start, end, name}), or None for a row
    that's removed, blank or refused (its problem is added)."""
    start, end, name = (_one(form, f"trip_{k}_{index}") for k in ("start", "end", "name"))
    if _checked(form, f"trip_remove_{index}") or not (start or end or name):
        return None
    try:
        first = parse_date(start)
        if end and parse_date(end) < first:
            problems.append(f"Trip {name or start}: it ends before it starts.")
            return None
    except ValueError:
        problems.append(f"Trip {name or start or '(no name)'}: the start date should be a date, not {start!r}.")
        return None
    return ({"start": start, **({"end": end} if end else {}), **({"name": name} if name else {})}
            if end or name else start)


def _apply_sound(new, form, problems):
    sound = _section(new, "sound")
    sound["enabled"] = _checked(form, "sound_enabled")
    sound["device"] = chosen_device(form)
    _apply_volume(sound, form, problems)
    _apply_quiet_hours(sound, form, problems)


def _apply_volume(sound, form, problems):
    if "sound_volume" not in form:  # the page always posts it; a form without it leaves the volume alone
        return
    volume, problem = volume_from_form(form)
    if problem:
        problems.append(problem)
    elif _one(form, "sound_volume"):
        sound["volume"] = volume
    else:
        sound.pop("volume", None)


def _apply_quiet_hours(sound, form, problems):
    quiet = _one(form, "quiet_start"), _one(form, "quiet_end")
    if not any(quiet):
        sound.pop("quiet_hours", None)
        return
    try:
        time.fromisoformat(quiet[0]), time.fromisoformat(quiet[1])
        sound["quiet_hours"] = {"start": quiet[0], "end": quiet[1]}
    except ValueError:
        problems.append("Quiet hours need both a start and an end time (or neither).")


def _apply_shows(new, form, problems):
    shows = new.get("shows") if isinstance(new.get("shows"), list) else []
    by_name = {e["name"]: e for e in shows if isinstance(e, dict) and isinstance(e.get("name"), str)}
    for index in _field_indexes(_SHOW_FIELD, form):
        _apply_show(shows, by_name, form, index, problems)
    if [e for e in shows if isinstance(e, dict) and e.get("force")][1:]:
        problems.append("Only one show can be forced to play at start-up.")
    new["shows"] = shows


def _apply_show(shows, by_name, form, index, problems):
    """One show row onto the shows list: its entry updated, or added at the end if the list lacks it."""
    name = _one(form, f"show_name_{index}")
    version = _one(form, f"show_version_{index}", "default")
    if version not in SHOW_VERSIONS:
        problems.append(f"{name}: the version should be one of {', '.join(SHOW_VERSIONS)}, not {version!r}.")
        return
    entry = by_name.get(name)
    if entry is None:
        entry = by_name[name] = {"name": name}
        shows.append(entry)
    entry.update(enabled=_checked(form, f"show_enabled_{index}"), version=version)
    if _checked(form, f"show_force_{index}"):
        entry["force"] = True
    else:
        entry.pop("force", None)


def _apply_panel(new, form, problems):
    """The panel: the Pi model, size and the settings the model sets in the Panel card, the rest
    under Advanced. A blank setting is the Pi model's default (or the driver's)."""
    _apply_pi_model(new, form, problems)
    matrix = _section(new, "matrix")
    _apply_panel_size(matrix, form, problems)
    _apply_matrix_fields(matrix, form)
    problem = cli.matrix_problem(matrix)
    if problem:
        problems.append(f"Panel: {problem}.")
    brightness = matrix.get(BRIGHTNESS)
    if brightness is not None and not (isinstance(brightness, int) and 1 <= brightness <= 100):
        problems.append(f"Brightness should be 1 to 100, not {brightness!r}.")


def _apply_pi_model(new, form, problems):
    if "pi_model" not in form:
        return
    model = _one(form, "pi_model", cli.AUTO)
    if model == cli.AUTO:
        new.pop("pi_model", None)
    elif model in cli.MODEL_DEFAULTS:
        new["pi_model"] = model
    else:
        problems.append(f"Pi model: {model!r} isn't one of {', '.join(cli.MODEL_NAMES.values())}.")


def _apply_panel_size(matrix, form, problems):
    if "panel_size" not in form:
        return
    found = re.fullmatch(r"(\d+)x(\d+)", _one(form, "panel_size"))
    if found:
        matrix["led_cols"], matrix["led_rows"] = int(found.group(1)), int(found.group(2))
    else:
        problems.append(f"Panel size should be like 64x32, not {_one(form, 'panel_size')!r}.")


def _matrix_value(text, switch, number):
    """A matrix field's text as config.json holds it: None when blank, true/false for a switch, an int for
    a number; a bad number stays text, for cli.matrix_problem to name."""
    if text == "":
        return None
    if switch:
        return text == "true"
    return int(text) if number and re.fullmatch(r"-?\d+", text) else text


def _apply_matrix_fields(matrix, form):
    for key, _, _, switch, number in cli.matrix_settings():
        field = f"matrix_{key}"
        if field in form:
            matrix[key] = _matrix_value(_one(form, field), switch, number)


def _apply_brightness_schedule(new, form, problems):
    if "bright_day" not in form:  # the page always posts it; a form without it leaves the schedule alone
        return
    if not _checked(form, "brightness_schedule"):
        new["brightness_schedule"] = None
        return
    levels = {}
    for key, field in (("day", "bright_day"), ("night", "bright_night")):
        text = _one(form, field)
        levels[key] = int(text) if re.fullmatch(r"\d+", text) else text
    schedule = {**levels, "day_start": _one(form, "day_start"), "night_start": _one(form, "night_start")}
    _, problem = parse_brightness_schedule(schedule)
    if problem:
        problems.append(f"Day and night brightness: {problem}.")
    new["brightness_schedule"] = schedule


def _apply_force_surprise(new, form, problems):
    surprise = _one(form, "force_surprise")
    if surprise and surprise not in surprise_names():
        problems.append(f"Surprise on every ride screen: {surprise!r} isn't a character.")
    else:
        new["force_surprise"] = surprise

