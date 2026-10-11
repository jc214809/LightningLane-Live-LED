"""
A fireworks show's score: what the castle fireworks do at each second of the soundtrack, read from
display/fireworks/shows/<show>.json (the show's clip_name, like its sound). Each scene there may add
cues to its section's palette and intensity; see the file's cue_note.

A later version of a show (config.json's "show_version", like "v2") is an overlay on that timeline:
<show>.<version>.json adds a stage and characters to scenes named by title, so re-timing V1 moves it too.
"""
import json
import os
from typing import FrozenSet, NamedTuple, Optional, Tuple

from display.fireworks.music_show import CASTLE_LOOKS, EFFECTS, SHAPES
from display.fireworks.show_actors import ACTORS
from display.motion import progress
from utils import debug

SHOWS_DIR = os.path.join(os.path.dirname(__file__), "shows")

# A section's intensity at which it launches like the everyday show.
_EVERYDAY_INTENSITY = 0.6
# Burst colours dimmer than this read as nothing on the LEDs.
_MIN_BURST_LEVEL = 80

# How much of the castle a scene shows: all of it, a dim ghost for characters to stand in front of,
# or none (music_show.STAGE_LEVELS has the brightness of each).
STAGES = ("castle", "ghost", "off")
# Effects that draw on or from the castle, so a scene with it off can't use them.
CASTLE_EFFECTS = frozenset({"keyhole_glow", "keyhole_open", "bells", "flame_jets", "fountains", "te_fiti",
                            "wishing_star", "tink"})


class Cue(NamedTuple):
    section: str
    title: str
    start: float
    end: float
    palette: Tuple[Tuple[int, int, int], ...]
    rate: float  # launches against the everyday show; 0 is dark
    castle: Optional[str]  # a music_show.CASTLE_LOOKS key, or None for the everyday castle
    shapes: Tuple[Tuple[str, float], ...]  # (music_show.SHAPES key, chance per launch)
    effects: FrozenSet[str]
    stage: str = "castle"  # one of STAGES
    actors: Tuple[str, ...] = ()  # show_actors.ACTORS keys, drawn in front of everything

    def progress(self, t):
        """0..1 through this scene at t seconds into the show."""
        return progress(t, self.start, self.end)


class Score(NamedTuple):
    name: str
    end: float
    cues: Tuple[Cue, ...]

    def cue_at(self, t):
        """The scene playing at t seconds; the last one past the end, the first one before 0."""
        for cue in self.cues:
            if t < cue.end:
                return cue
        return self.cues[-1]


def _rgb(text):
    text = text.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"not a #RRGGBB colour: {text!r}")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def _palette(colours):
    rgbs = tuple(_rgb(c) for c in colours)
    bright = tuple(c for c in rgbs if max(c) >= _MIN_BURST_LEVEL)
    if not bright:
        raise ValueError(f"no colour bright enough for a burst in {colours}")
    return bright


def _cue(section, scene):
    palette = _palette(scene.get("palette", section["palette"]))
    rate = float(scene.get("rate", section["intensity"] / _EVERYDAY_INTENSITY))
    castle = scene.get("castle")
    if castle is not None and castle not in CASTLE_LOOKS:
        raise ValueError(f"unknown castle look {castle!r}")
    shapes = tuple((str(k), float(v)) for k, v in scene.get("shapes", {}).items())
    unknown = [k for k, _ in shapes if k not in SHAPES]
    if unknown:
        raise ValueError(f"unknown shapes {unknown}")
    effects = frozenset(scene.get("effects", ()))
    if not effects <= EFFECTS:
        raise ValueError(f"unknown effects {sorted(effects - EFFECTS)}")
    return Cue(section["id"], scene["title"], float(scene["start"]), float(scene["end"]),
               palette, max(0.0, rate), castle, shapes, effects)


def _overlay(cue, extra):
    """The cue with a version's additions for its scene: {"stage", "actors", "rate"}, each optional."""
    unknown = set(extra) - {"stage", "actors", "rate", "note"}
    if unknown:
        raise ValueError(f"{cue.title}: unknown overlay keys {sorted(unknown)}")
    stage = extra.get("stage", cue.stage)
    if stage not in STAGES:
        raise ValueError(f"{cue.title}: unknown stage {stage!r}")
    actors = extra.get("actors", list(cue.actors))
    if not isinstance(actors, list) or not all(isinstance(a, str) for a in actors):
        raise ValueError(f"{cue.title}: actors should be a list of names, not {actors!r}")
    missing = [a for a in actors if a not in ACTORS]
    if missing:
        raise ValueError(f"{cue.title}: unknown actors {missing}")
    if stage == "off" and cue.effects & CASTLE_EFFECTS:
        raise ValueError(f"{cue.title}: the castle is off, but {sorted(cue.effects & CASTLE_EFFECTS)} draw on it")
    rate = max(0.0, float(extra.get("rate", cue.rate)))
    return cue._replace(stage=stage, actors=tuple(actors), rate=rate)


def parse_score(name, data, overlay=None):
    """A Score from a show file's JSON, with a version's overlay file's JSON on it if given; raises
    ValueError/KeyError/TypeError on a bad file. An overlay title that matches no scene is an error, so
    renaming a scene can't silently drop what a version adds to it."""
    cues = tuple(sorted((_cue(section, scene)
                         for section in data["sections"] for scene in section["scenes"]),
                        key=lambda c: c.start))
    if not cues:
        raise ValueError("no scenes")
    if overlay is not None:
        extras = overlay["overlays"]
        unmatched = set(extras) - {c.title for c in cues}
        if unmatched:
            raise ValueError(f"overlay scenes not in the show: {sorted(unmatched)}")
        cues = tuple(_overlay(c, extras[c.title]) if c.title in extras else c for c in cues)
    end = float(data["show_end"])
    return Score(name, end, cues)


_LOAD_ERRORS = (OSError, ValueError, KeyError, TypeError, AttributeError)


def load_score(name, shows_dir=None, version="v1"):
    """The show's Score, or None with no file (the random fireworks play instead). A broken file is
    logged and also gives None, so a typo never stops the show. A version past v1 adds its overlay file
    (<name>.<version>.json); without one, or with a broken one, it logs and plays V1."""
    shows_dir = shows_dir or SHOWS_DIR
    path = os.path.join(shows_dir, f"{name}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        score = parse_score(name, data)
    except _LOAD_ERRORS as e:
        debug.warning(f"Can't use the show score {path}: {e!r}; playing the everyday fireworks.")
        return None
    if version == "v1":
        return score
    overlay_path = os.path.join(shows_dir, f"{name}.{version}.json")
    try:
        with open(overlay_path) as f:
            return parse_score(name, data, json.load(f))
    except _LOAD_ERRORS as e:
        debug.warning(f"Can't use {name}'s {version} ({overlay_path}): {e!r}; playing v1.")
        return score
