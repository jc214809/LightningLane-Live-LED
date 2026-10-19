"""
A fireworks show's score: what the castle fireworks do at each second of the soundtrack, read from
display/fireworks/shows/<show>.json (the show's clip_name, like its sound). Each scene there may add
cues to its section's palette and intensity; see the file's cue_note.

A later version of a show (a config.json "shows" entry's "version", like "v2") is an overlay on that timeline:
<show>.<version>.json adds a stage and characters to scenes named by title, so re-timing V1 moves it too.
<show>.<version>.lips.json, made by tools/lip_sync.py, holds the mouth tracks of the characters who sing.
"""
import json
import os
from typing import Dict, FrozenSet, NamedTuple, Optional, Tuple

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
CASTLE_EFFECTS = frozenset({"keyhole_glow", "keyhole_glow_dim", "keyhole_open", "bells", "flame_jets", "gold_burst",
                            "fountains", "te_fiti", "wishing_star", "tink"})
# A scene's "hits": one firework at a set moment, for the real show's single cues. A roof fan fires comets
# outward from both side rooftops; a shell bursts at (x, y), fractions of the board; a comet flies up and
# across from one side.
HIT_KINDS = ("roof_fan", "shell", "comet")
SHELL_STYLES = ("peony", "willow", "curtain")  # a curtain is a big willow hanging down over the castle
SIDES = ("left", "right")


class Hit(NamedTuple):
    at: float  # seconds into the show: when a shell bursts, or a fan or comet launches
    kind: str  # one of HIT_KINDS
    rgb: Tuple[int, int, int]
    x: float = 0.5  # a shell's burst, as fractions of the board's width and height
    y: float = 0.25
    style: str = "peony"  # a shell's, one of SHELL_STYLES
    side: str = "right"  # where a comet launches from, one of SIDES


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
    hits: Tuple[Hit, ...] = ()  # set-moment fireworks, by time
    castle_changes: Tuple[Tuple[float, str], ...] = ()  # (show seconds, CASTLE_LOOKS key) after the start's
    stage_changes: Tuple[Tuple[float, str], ...] = ()  # (show seconds, one of STAGES) after the start's

    def progress(self, t):
        """0..1 through this scene at t seconds into the show."""
        return progress(t, self.start, self.end)

    def castle_at(self, t):
        """The castle's look at t seconds into the show: the scene's, or its latest change by then."""
        return _latest(self.castle, self.castle_changes, t)

    def stage_at(self, t):
        """The stage at t seconds into the show: the scene's, or its latest change by then."""
        return _latest(self.stage, self.stage_changes, t)


def _latest(first, changes, t):
    for at, value in changes:
        if t < at:
            break
        first = value
    return first


class Lips(NamedTuple):
    """A singing character's mouth: one shape per 1/fps second from start (audio seconds)."""
    start: float
    fps: float
    track: str  # 0 closed, 1 half, 2 open

    def shape(self, t):
        """The mouth at t seconds into the show (0, 1 or 2), or None outside the track."""
        if t < self.start:
            return None
        i = int((t - self.start) * self.fps)
        return int(self.track[i]) if i < len(self.track) else None


class Score(NamedTuple):
    name: str
    end: float
    cues: Tuple[Cue, ...]
    lips: Optional[Dict[str, Lips]] = None  # by show_actors.ACTORS name

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


def _hits(scene):
    hits = []
    for entry in scene.get("hits", ()):
        unknown = set(entry) - {"at", "kind", "colour", "x", "y", "style", "side"}
        if unknown:
            raise ValueError(f"{scene['title']}: unknown hit keys {sorted(unknown)}")
        hit = Hit(float(entry["at"]), entry["kind"], _rgb(entry["colour"]), float(entry.get("x", 0.5)),
                  float(entry.get("y", 0.25)), entry.get("style", "peony"), entry.get("side", "right"))
        if hit.kind not in HIT_KINDS or hit.style not in SHELL_STYLES or hit.side not in SIDES:
            raise ValueError(f"{scene['title']}: unknown hit {entry}")
        if not float(scene["start"]) <= hit.at < float(scene["end"]):
            raise ValueError(f"{scene['title']}: a hit at {hit.at} is outside the scene")
        if not (0 <= hit.x <= 1 and 0 <= hit.y <= 1):
            raise ValueError(f"{scene['title']}: a hit's x and y are fractions of the board")
        hits.append(hit)
    return tuple(sorted(hits))


def _changes(title, entries, key, known, start, end, relative=False):
    """(show seconds, value) pairs, by time, from a scene's [{when: seconds, key: value}] list: `when` is
    "at" (show seconds), or "after" (seconds into the scene) if relative."""
    when, offset = ("after", start) if relative else ("at", 0.0)
    changes = []
    for entry in entries:
        if set(entry) != {when, key}:
            raise ValueError(f"{title}: a change is {{{when!r}, {key!r}}}, not {entry}")
        at = offset + float(entry[when])
        if entry[key] not in known:
            raise ValueError(f"{title}: unknown {key} {entry[key]!r}")
        if not start < at < end:
            raise ValueError(f"{title}: a change at {at} is outside the scene")
        changes.append((at, entry[key]))
    return tuple(sorted(changes))


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
    start, end = float(scene["start"]), float(scene["end"])
    castle_changes = _changes(scene["title"], scene.get("castle_changes", ()), "castle", CASTLE_LOOKS, start, end)
    return Cue(section["id"], scene["title"], start, end, palette, max(0.0, rate), castle, shapes, effects,
               hits=_hits(scene), castle_changes=castle_changes)


def _overlay(cue, extra):
    """The cue with a version's additions for its scene: {"stage", "stage_changes", "actors", "rate",
    "effects"}, each optional; stage_changes are [{"after": seconds into the scene, "stage": ...}], so they
    move with it; effects replaces the scene's (an actor drawing the same thing its own way)."""
    unknown = set(extra) - {"stage", "stage_changes", "actors", "rate", "effects", "note"}
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
    effects = extra.get("effects", cue.effects)
    if not all(isinstance(e, str) for e in effects) or isinstance(effects, str):
        raise ValueError(f"{cue.title}: effects should be a list of names, not {effects!r}")
    effects = frozenset(effects)
    if not effects <= EFFECTS:
        raise ValueError(f"{cue.title}: unknown effects {sorted(effects - EFFECTS)}")
    stage_changes = _changes(cue.title, extra.get("stage_changes", ()), "stage", STAGES, cue.start, cue.end,
                             relative=True)
    if "off" in {stage, *(s for _, s in stage_changes)} and effects & CASTLE_EFFECTS:
        raise ValueError(f"{cue.title}: the castle is off, but {sorted(effects & CASTLE_EFFECTS)} draw on it")
    rate = max(0.0, float(extra.get("rate", cue.rate)))
    return cue._replace(stage=stage, stage_changes=stage_changes, actors=tuple(actors), rate=rate, effects=effects)


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


def parse_lips(data):
    """{actor: Lips} from a lips file's JSON; raises like parse_score on a bad one."""
    lips = {}
    for actor, entry in data["lips"].items():
        if actor not in ACTORS:
            raise ValueError(f"unknown actor {actor!r}")
        track, fps = entry["track"], float(entry["fps"])
        if not isinstance(track, str) or not track or set(track) - set("012"):
            raise ValueError(f"{actor}: a track is a string of 0, 1 and 2")
        if fps <= 0:
            raise ValueError(f"{actor}: fps must be positive")
        lips[actor] = Lips(float(entry["start"]), fps, track)
    return lips


def _load_lips(name, version, shows_dir):
    """The version's mouth tracks, or None without a file. A broken one is logged and dropped: the
    characters still play, just without moving their mouths."""
    path = os.path.join(shows_dir, f"{name}.{version}.lips.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return parse_lips(json.load(f))
    except _LOAD_ERRORS as e:
        debug.warning(f"Can't use the mouth tracks in {path}: {e!r}; the characters' mouths won't move.")
        return None


def load_score(name, shows_dir=None, version="v1"):
    """The show's Score, or None with no file (the random fireworks play instead). A broken file is
    logged and also gives None, so a typo never stops the show. A version past v1 adds its overlay file
    (<name>.<version>.json); without one, or with a broken one, it logs and plays V1. Its mouth tracks
    (<name>.<version>.lips.json) are optional."""
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
            score = parse_score(name, data, json.load(f))
    except _LOAD_ERRORS as e:
        debug.warning(f"Can't use {name}'s {version} ({overlay_path}): {e!r}; playing v1.")
        return score
    return score._replace(lips=_load_lips(name, version, shows_dir))
