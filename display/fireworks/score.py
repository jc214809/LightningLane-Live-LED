"""
A fireworks show's score: what the castle fireworks do at each second of the soundtrack, read from
display/fireworks/shows/<show>.json (the show's clip_name, like its sound). Each scene there may add
cues to its section's palette and intensity; see the file's cue_note.
"""
import json
import os
from typing import FrozenSet, NamedTuple, Optional, Tuple

from display.fireworks.music_show import CASTLE_LOOKS, SHAPES
from display.motion import progress
from utils import debug

SHOWS_DIR = os.path.join(os.path.dirname(__file__), "shows")

EFFECTS = {"wishing_star", "lanterns", "embers", "rainbow", "final_flash"}
# A section's intensity at which it launches like the everyday show.
_EVERYDAY_INTENSITY = 0.6
# Burst colours dimmer than this read as nothing on the LEDs.
_MIN_BURST_LEVEL = 80


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


def parse_score(name, data):
    """A Score from a show file's JSON; raises ValueError/KeyError/TypeError on a bad file."""
    cues = tuple(sorted((_cue(section, scene)
                         for section in data["sections"] for scene in section["scenes"]),
                        key=lambda c: c.start))
    if not cues:
        raise ValueError("no scenes")
    end = float(data["show_end"])
    return Score(name, end, cues)


def load_score(name, shows_dir=None):
    """The show's Score, or None with no file (the random fireworks play instead). A broken file is
    logged and also gives None, so a typo never stops the show."""
    path = os.path.join(shows_dir or SHOWS_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return parse_score(name, json.load(f))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        debug.warning(f"Can't use the show score {path}: {e!r}; playing the everyday fireworks.")
        return None
