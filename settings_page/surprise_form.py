"""The Surprise characters page's form logic: the characters it lists, Save (apply_surprises), Export
(snapshot_surprises) and Import (import_surprises). No HTTP or HTML here. Split out of form.py, which re-exports
every public name, so callers still import them from settings_page.form."""

import ast
import copy
import json
import os
import re
from typing import NamedTuple

from utils.config import SURPRISE_LOOKS, SURPRISES_UNUSED
from utils.surprises import DEFAULT_RIDE_CHANCE, PARK_REVEALS, RIDE_VISITORS, SURPRISES

# Where TRANSITIONS lives. Read, not imported: importing it loads every character's art.
_CHARACTERS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "display", "animation", "characters", "__init__.py"
)

# Proper names for the surprise characters, where title case gets them wrong; the rest are title-cased.
CHARACTER_NAMES = {
    "tink": "Tinker Bell",
    "buzz": "Buzz Lightyear",
    "ralph": "Wreck-It Ralph",
    "slinky": "Slinky Dog",
    "slinky_wrap": "Slinky Dog (wrap)",
    "walle": "WALL-E",
    "walle_side": "WALL-E (side)",
    "army_men": "Green Army Men",
    "falcon": "Millennium Falcon",
    "mike": "Mike Wazowski",
    "mcqueen": "Lightning McQueen",
    "chip_dale": "Chip 'n' Dale",
    "chip_dale_swing": "Chip 'n' Dale (swing)",
    "pooh": "Winnie the Pooh",
    "donald": "Donald Duck",
    "jack_sally": "Jack & Sally",
    "grannies": "Bluey: Grannies",
    "keepy_uppy": "Bluey: Keepy Uppy",
    "saber_duel": "Saber Duel (random)",
    "saber_duel_obiwan": "Saber Duel Obi-Wan",
    "archer": "Merida (archer)",
}


def character_label(name):
    return CHARACTER_NAMES.get(name, name.replace("_", " ").title())


def _one(form, name):
    """A form field's first value, stripped; "" when the form doesn't have it."""
    return (form.get(name) or [""])[0].strip()


def surprise_names(path=_CHARACTERS):
    """The characters force_surprise can name: TRANSITIONS' keys but "wipe", as disney.py's
    set_forced_surprise takes them. [] if the file can't be read."""
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError):
        return []
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Dict)
            and any(isinstance(t, ast.Name) and t.id == "TRANSITIONS" for t in node.targets)
        ):
            return [k.value for k in node.value.keys if isinstance(k, ast.Constant) and k.value != "wipe"]
    return []


def surprise_characters(path=_CHARACTERS):
    """The characters the Surprise characters page lists, one each: surprise_names() less the extra looks
    (utils.config.SURPRISE_LOOKS), the ones no roll picks and the park titles' (Tink, Buzz), which aren't
    ride-screen surprises."""
    looks = {look for group in SURPRISE_LOOKS.values() for look in group}
    return [
        name
        for name in surprise_names(path)
        if name not in looks and name not in SURPRISES_UNUSED and name not in PARK_REVEALS
    ]


def percent_text(fraction):
    """A chance (0 to 1) as the page shows it: 0.012 is "1.2"."""
    return f"{round(fraction * 100, 3):g}"


class SurpriseRow(NamedTuple):
    name: str
    anywhere: str  # the default % of all ride screens, as the page shows it
    own: str  # the default % on its own rides
    rides: list  # the rides it visits by default, as pieces of their names, titled; [] for none


MAX_RIDES_PER_CHARACTER = 300
MAX_RIDE_NAME = 120


def surprise_rows():
    """A SurpriseRow for each character on the Surprise characters page, from the odds tables in
    utils/surprises.py. Every character can take a chance on any ride screen and rides of its own."""
    rows = []
    for name in surprise_characters():
        spec = RIDE_VISITORS.get(name)
        rows.append(
            SurpriseRow(
                name,
                percent_text(SURPRISES.get(name, 0)),
                percent_text(spec["chance"] if spec else DEFAULT_RIDE_CHANCE),
                [ride.title() for ride in spec["rides"]] if spec else [],
            )
        )
    return rows


def default_rides(name, rides):
    """The rides in rides ({park: [names]}) that a character visits by default: those whose name has one of
    utils/surprises.py's pieces in it, as the app matches them. Sorted; [] for a character with none."""
    pieces = RIDE_VISITORS.get(name, {}).get("rides", ())
    return sorted(
        {ride for names in (rides or {}).values() for ride in names if any(piece in ride.lower() for piece in pieces)},
        key=str.lower,
    )


CHANCE_KEYS = ("chance", "ride_chance")


def apply_surprises(data, form, rides=None):
    """(the surprises.json to save, [problems]) from the Surprise characters page's form. A ticked box lets
    that character visit; a chance left blank is the default (utils/surprises.py), so a character at its
    defaults has no entry at all, and no rides chosen means its usual rides. Characters and settings the
    page doesn't know (a newer version's) stay."""
    new = copy.deepcopy(data) if isinstance(data, dict) else {}
    problems = []
    characters = new.get("characters") if isinstance(new.get("characters"), dict) else {}
    for row in surprise_rows():
        old = characters.get(row.name) if isinstance(characters.get(row.name), dict) else {}
        entry = _character_entry(row.name, old, form, rides, problems)
        if entry:
            characters[row.name] = entry
        else:
            characters.pop(row.name, None)
    problem = _chances_total_problem(characters)
    if problem:
        problems.append(problem)
    new["enabled"] = _one(form, "surprises_enabled") == "on"
    new["characters"] = characters
    return new, problems


def _character_entry(name, old, form, rides, problems):
    """One character's entry from its fields on the form, on top of what was saved for it: {} for all defaults."""
    entry = {k: v for k, v in old.items() if k not in ("on", *CHANCE_KEYS)}
    if f"rides_set_{name}" in form:
        entry.pop("rides", None)
    if _one(form, f"surprise_{name}") != "on":
        entry["on"] = False
    for key in CHANCE_KEYS:
        text = _one(form, f"{key}_{name}")
        if not text:
            continue
        if not re.fullmatch(r"\d+(\.\d+)?", text) or float(text) > 100:
            problems.append(f"{character_label(name)}: the chance should be a percent from 0 to 100, not {text!r}.")
        else:
            entry[key] = _number(text)
    if f"rides_set_{name}" in form:
        _apply_posted_rides(entry, name, form, rides, problems)
    return entry


def _apply_posted_rides(entry, name, form, rides, problems):
    """The rides the page posted for a character onto its entry: nothing for its default rides."""
    posted = list(dict.fromkeys(r.strip() for r in form.get(f"rides_{name}", []) if r.strip()))
    # "saved": these were saved as the rides, so none at all stays none even when the ride list has none of
    # the character's default rides in it (which makes none look like the defaults).
    explicit_none = form[f"rides_set_{name}"][0] == "saved" and not posted and name in RIDE_VISITORS
    if len(posted) > MAX_RIDES_PER_CHARACTER or any(len(r) > MAX_RIDE_NAME for r in posted):
        problems.append(f"{character_label(name)}: that's too many rides, or a ride name that's too long.")
    elif explicit_none or sorted(posted, key=str.lower) != default_rides(name, rides):
        entry["rides"] = sorted(posted, key=str.lower)


def _chances_total_problem(characters):
    """What's wrong if the characters' chances on any ride screen (saved, else default) pass 100%, else None."""
    total = sum(
        characters.get(name, {}).get("chance", SURPRISES.get(name, 0) * 100)
        for name in set(SURPRISES) | set(characters)
    )
    if total > 100:
        return (
            f"Together the characters' chances on any ride screen come to {round(total, 1):g}%: they can't pass 100%."
        )
    return None


def snapshot_surprises(data, rides=None):
    """The whole of the Surprise characters settings as the page shows them, for Export: for every character on the
    page its "on", "chance" and "ride_chance" (what's saved, else the default) and the "rides" it visits, so a copy
    is complete on its own. data: what Save would write (apply_surprises); rides: {park: [names]}, ride_names.
    A character's default rides are given by name when the ride list has them, else by the pieces of their names."""
    saved = data.get("characters") if isinstance(data.get("characters"), dict) else {}
    characters = {}
    for row in sorted(surprise_rows(), key=lambda r: character_label(r.name).lower()):
        entry = saved.get(row.name) if isinstance(saved.get(row.name), dict) else {}
        if isinstance(entry.get("rides"), list):
            visits = entry["rides"]
        else:
            # By name when the list has them, else by the pieces of their names: an empty list always means none.
            visits = default_rides(row.name, rides) or [ride.lower() for ride in row.rides]
        characters[row.name] = {
            "on": entry.get("on", True),
            "chance": _number(entry.get("chance", row.anywhere)),
            "ride_chance": _number(entry.get("ride_chance", row.own)),
            "rides": list(visits),
        }
    return {"enabled": data.get("enabled", True), "characters": characters}


def _number(value):
    """A percent as JSON should show it: 25, not 25.0; 1.5 stays."""
    value = round(float(value), 3)
    return int(value) if value == int(value) else value


def _percent(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and 0 <= value <= 100


def import_surprises(text, rides=None):
    """(the surprises.json the pasted text makes, [problems], [names skipped]), for moving one board's Surprise
    characters settings to another: the text is what the Export button copied (or a surprises.json). Only what the
    page itself would save is kept, and what is only a default (an "on" of true, a chance, or rides that are the
    character's default ones, from rides, {park: [names]}) is dropped, so a copy doesn't freeze numbers a later
    version may change. A character this version doesn't have is skipped, not an error, so a newer board's export
    still goes onto an older one. With any problem, nothing should be used."""
    data, refusal = _parse_export(text)
    if refusal:
        return None, [refusal], []
    problems, skipped = [], []
    enabled = _import_enabled(data, problems)
    characters = _import_characters(_import_given(data, problems), rides, problems, skipped)
    problem = _chances_total_problem(characters)
    if problem:
        problems.append(problem)
    return {"enabled": enabled, "characters": characters}, problems, skipped


def _parse_export(text):
    """(the pasted object, None), or (None, why the text isn't one)."""
    try:
        data = json.loads(text)
    except ValueError as e:
        return None, f"That isn't settings the Export button copied: it isn't valid JSON ({e})."
    if not isinstance(data, dict):
        return None, "That isn't settings the Export button copied: it should be an object in {braces}."
    return data, None


def _import_enabled(data, problems):
    enabled = data.get("enabled", True)
    if isinstance(enabled, bool):
        return enabled
    problems.append('"enabled" should be true or false.')
    return True


def _import_given(data, problems):
    given = data.get("characters", {})
    if isinstance(given, dict):
        return given
    problems.append('"characters" should be an object of characters.')
    return {}


def _import_characters(given, rides, problems, skipped):
    """The characters worth keeping from the pasted ones: each checked (problems added), a character this
    version lacks named in skipped, and each one's defaults dropped."""
    rows = {row.name: row for row in surprise_rows()}
    characters = {}
    for name, entry in given.items():
        label = character_label(name)
        if name not in rows:
            skipped.append(name)
            continue
        if not isinstance(entry, dict):
            problems.append(f"{label}: its settings should be an object.")
            continue
        kept = _import_entry(entry, label, problems)
        _drop_defaults(kept, rows[name], rides)
        if kept:
            characters[name] = kept
    return characters


def _import_entry(entry, label, problems):
    """What the page would save from one pasted character: a false "on", chances and rides that are valid."""
    kept = {}
    if "on" in entry:
        if not isinstance(entry["on"], bool):
            problems.append(f'{label}: "on" should be true or false.')
        elif not entry["on"]:
            kept["on"] = False
    for key in CHANCE_KEYS:
        if key not in entry:
            continue
        if _percent(entry[key]):
            kept[key] = _number(entry[key])
        else:
            problems.append(f'{label}: "{key}" should be a percent from 0 to 100, not {entry[key]!r}.')
    if "rides" in entry:
        _import_rides(kept, entry["rides"], label, problems)
    return kept


def _import_rides(kept, visits, label, problems):
    if not isinstance(visits, list) or not all(isinstance(r, str) for r in visits):
        problems.append(f'{label}: "rides" should be a list of ride names.')
    elif len(visits) > MAX_RIDES_PER_CHARACTER or any(len(r) > MAX_RIDE_NAME for r in visits):
        problems.append(f"{label}: that's too many rides, or a ride name that's too long.")
    else:
        kept["rides"] = sorted(dict.fromkeys(r.strip() for r in visits if r.strip()), key=str.lower)


def _drop_defaults(kept, row, rides):
    """Take out of kept what's only the character's default (row: its SurpriseRow)."""
    for key, default in zip(CHANCE_KEYS, (row.anywhere, row.own)):
        if kept.get(key) == _number(default):
            del kept[key]
    if "rides" in kept and _rides_are_default(row.name, kept["rides"], rides):
        del kept["rides"]


def _rides_are_default(name, mine, rides):
    """Whether the rides are just the character's default ones (by name, or by the pieces of their names), or
    none for a character with no default rides; none for one that has them is kept: it switches them off."""
    if not mine:
        return name not in RIDE_VISITORS
    pieces = sorted(piece.lower() for piece in RIDE_VISITORS.get(name, {}).get("rides", ()))
    return mine == default_rides(name, rides) or sorted(r.lower() for r in mine) == pieces
