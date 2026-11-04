"""config.json to the settings page's form and back. No HTTP or HTML here (server.py and
page.py): apply_form takes the posted fields and returns the config to save, or what's wrong.

Only the keys the page shows change; anything else in config.json (old keys, keys a newer
version adds) is kept as it is. Every check is the app's own, so a saved config starts the app.
"""
import ast
import copy
import os
import re
from datetime import time
from typing import NamedTuple

import cli
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
# Where TRANSITIONS lives. Read, not imported: importing it loads every character's art.
_CHARACTERS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "display", "animation", "characters", "__init__.py")


def masked(key):
    """A saved API key as the page shows it: its last letters only, or "" when there's none."""
    if not has_api_key(key):
        return ""
    return "•" * 4 + key.strip()[-SHOWN_KEY_LETTERS:]


def surprise_names(path=_CHARACTERS):
    """The characters force_surprise can name: TRANSITIONS' keys but "wipe", as disney.py's
    set_forced_surprise takes them. [] if the file can't be read."""
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError):
        return []
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                and any(isinstance(t, ast.Name) and t.id == "TRANSITIONS" for t in node.targets)):
            return [k.value for k in node.value.keys if isinstance(k, ast.Constant) and k.value != "wipe"]
    return []


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
    """config.json's trips as (start, end, name) strings for the form's date fields."""
    entries = (config.get("trip_countdown") or {}).get("trip_dates")
    rows = []
    for entry in entries if isinstance(entries, list) else []:
        entry = entry if isinstance(entry, dict) else {"start": entry}
        rows.append(tuple(_date_text(entry.get(k)) if k != "name" else str(entry.get(k) or "")
                          for k in ("start", "end", "name")))
    return rows


def _date_text(value):
    try:
        return parse_date(value).isoformat() if value else ""
    except (TypeError, ValueError):
        return str(value)


def chosen_device(form):
    """The speaker the form picks: one from the list, one typed under Other device, or None."""
    one = lambda name: (form.get(name) or [""])[0].strip()
    return (one("sound_device_custom") if one("sound_device") == "custom" else one("sound_device")) or None


def volume_from_form(form):
    """(volume, problem) from the form's Volume: blank is DEFAULT_VOLUME."""
    text = (form.get("sound_volume") or [""])[0].strip()
    if not text:
        return DEFAULT_VOLUME, None
    if re.fullmatch(r"\d+", text) and int(text) <= 100:
        return int(text), None
    return None, f"Volume should be 0 to 100, not {text!r}."


def apply_form(config, form, park_names=()):
    """(the config to save, [problems]) from the posted form: {field: [values]}, as
    urllib.parse.parse_qs(..., keep_blank_values=True) gives it. With any problem, nothing
    should be saved. park_names: park_names.ParkNames.names(), the names a park may have."""
    new = copy.deepcopy(config)
    problems = []

    def one(name, default=""):
        return (form.get(name) or [default])[0].strip()

    def checked(name):
        return one(name) == "on"

    def section(key):
        if not isinstance(new.get(key), dict):
            new[key] = {}
        return new[key]

    # API keys and live updates
    ws = section("websocket")
    ws["enabled"] = checked("ws_enabled")
    protocol = one("ws_protocol", "legacy")
    if protocol in WS_PROTOCOLS:
        ws["protocol"] = protocol
    else:
        problems.append(f"Live update protocol should be one of {', '.join(WS_PROTOCOLS)}, not {protocol!r}.")
    if one("themeparks_key"):
        ws["api_key"] = one("themeparks_key")
    if ws["enabled"] and not has_api_key(ws.get("api_key")):
        problems.append("Live updates need a ThemeParks.wiki API key (or turn them off).")
    if one("weather_key"):
        section("weather")["apikey"] = one("weather_key")

    # Pushover, for sending the sign-in PIN to a phone: kept out of config.json until a key is typed
    if "pushover_user" in form:  # the page always posts it; a form without it leaves Pushover alone
        typed = {key: one(field) for key, field in (("user_key", "pushover_user"), ("app_token", "pushover_token"))
                 if one(field)}
        if typed or isinstance(new.get("pushover"), dict):
            pushover = section("pushover")
            pushover.update(typed)
            pushover["enabled"] = checked("pushover_enabled")
            if pushover["enabled"] and not pushover_keys(new):
                problems.append("Sending the PIN needs both a Pushover user key and an app token (or turn it off).")

    # Parks: the chips in order, less any ticked to remove, then the added one(s), named as the
    # list has them. With no list (never fetched), names can't be checked, so they're taken as typed.
    known = {name.lower(): name for name, _ in park_names}
    removed = {p.strip().lower() for p in form.get("park_remove", [])}
    parks = []
    for typed in [p for p in form.get("park", []) if p.strip().lower() not in removed] + one("park_add").split(","):
        typed = " ".join(typed.split())
        if not typed or typed.lower() in (p.lower() for p in parks):
            continue
        if known and typed.lower() not in known:
            problems.append(f"{typed!r} isn't a ThemeParks.wiki park: pick one from the list.")
        parks.append(known.get(typed.lower(), typed))
    if not parks:
        problems.append("Pick at least one park.")
    new["parks"] = parks

    # Trip countdown
    countdown = section("trip_countdown")
    countdown["enabled"] = checked("trips_enabled")
    trips = []
    for index in sorted((int(m.group(1)) for m in map(_TRIP_FIELD.match, form) if m)):
        start, end, name = (one(f"trip_{k}_{index}") for k in ("start", "end", "name"))
        if checked(f"trip_remove_{index}") or not (start or end or name):
            continue
        try:
            first = parse_date(start)
            if end and parse_date(end) < first:
                problems.append(f"Trip {name or start}: it ends before it starts.")
                continue
        except ValueError:
            problems.append(f"Trip {name or start or '(no name)'}: the start date should be a date, not {start!r}.")
            continue
        trips.append({"start": start, **({"end": end} if end else {}), **({"name": name} if name else {})}
                     if end or name else start)
    countdown["trip_dates"] = trips
    countdown.pop("trip_date", None)  # the old single date; trip_dates replaces it

    # Sound
    sound = section("sound")
    sound["enabled"] = checked("sound_enabled")
    sound["device"] = chosen_device(form)
    if "sound_volume" in form:  # the page always posts it; a form without it leaves the volume alone
        volume, problem = volume_from_form(form)
        if problem:
            problems.append(problem)
        elif one("sound_volume"):
            sound["volume"] = volume
        else:
            sound.pop("volume", None)
    quiet = one("quiet_start"), one("quiet_end")
    if any(quiet):
        try:
            time.fromisoformat(quiet[0]), time.fromisoformat(quiet[1])
            sound["quiet_hours"] = {"start": quiet[0], "end": quiet[1]}
        except ValueError:
            problems.append("Quiet hours need both a start and an end time (or neither).")
    else:
        sound.pop("quiet_hours", None)

    # Shows
    shows = new.get("shows") if isinstance(new.get("shows"), list) else []
    by_name = {e["name"]: e for e in shows if isinstance(e, dict) and isinstance(e.get("name"), str)}
    for index in sorted((int(m.group(1)) for m in map(_SHOW_FIELD.match, form) if m)):
        name = one(f"show_name_{index}")
        version = one(f"show_version_{index}", "default")
        if version not in SHOW_VERSIONS:
            problems.append(f"{name}: the version should be one of {', '.join(SHOW_VERSIONS)}, not {version!r}.")
            continue
        entry = by_name.get(name)
        if entry is None:
            entry = by_name[name] = {"name": name}
            shows.append(entry)
        entry.update(enabled=checked(f"show_enabled_{index}"), version=version)
        if checked(f"show_force_{index}"):
            entry["force"] = True
        else:
            entry.pop("force", None)
    if [e for e in shows if isinstance(e, dict) and e.get("force")][1:]:
        problems.append("Only one show can be forced to play at start-up.")
    new["shows"] = shows

    # The panel: the Pi model, size and the settings the model sets in the Panel card, the rest
    # under Advanced. A blank setting is the Pi model's default (or the driver's).
    if "pi_model" in form:
        model = one("pi_model", cli.AUTO)
        if model == cli.AUTO:
            new.pop("pi_model", None)
        elif model in cli.MODEL_DEFAULTS:
            new["pi_model"] = model
        else:
            problems.append(f"Pi model: {model!r} isn't one of {', '.join(cli.MODEL_NAMES.values())}.")
    matrix = section("matrix")
    if "panel_size" in form:
        found = re.fullmatch(r"(\d+)x(\d+)", one("panel_size"))
        if found:
            matrix["led_cols"], matrix["led_rows"] = int(found.group(1)), int(found.group(2))
        else:
            problems.append(f"Panel size should be like 64x32, not {one('panel_size')!r}.")
    for key, _, _, switch, number in cli.matrix_settings():
        field = f"matrix_{key}"
        if field not in form:
            continue
        text = one(field)
        if text == "":
            matrix[key] = None
        elif switch:
            matrix[key] = text == "true"
        else:  # a bad number stays text, for matrix_problem to name
            matrix[key] = int(text) if number and re.fullmatch(r"-?\d+", text) else text
    problem = cli.matrix_problem(matrix)
    if problem:
        problems.append(f"Panel: {problem}.")
    brightness = matrix.get(BRIGHTNESS)
    if brightness is not None and not (isinstance(brightness, int) and 1 <= brightness <= 100):
        problems.append(f"Brightness should be 1 to 100, not {brightness!r}.")
    if "bright_day" in form:  # the page always posts it; a form without it leaves the schedule alone
        if checked("brightness_schedule"):
            levels = {}
            for key, field in (("day", "bright_day"), ("night", "bright_night")):
                text = one(field)
                levels[key] = int(text) if re.fullmatch(r"\d+", text) else text
            schedule = {**levels, "day_start": one("day_start"), "night_start": one("night_start")}
            _, problem = parse_brightness_schedule(schedule)
            if problem:
                problems.append(f"Day and night brightness: {problem}.")
            new["brightness_schedule"] = schedule
        else:
            new["brightness_schedule"] = None

    new["debug"] = checked("debug")
    surprise = one("force_surprise")
    if surprise and surprise not in surprise_names():
        problems.append(f"Surprise on every ride screen: {surprise!r} isn't a character.")
    else:
        new["force_surprise"] = surprise
    return new, problems
