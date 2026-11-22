#!/usr/bin/env python3
"""
Proof that a refactor of the display changed nothing: render everything the boards draw,
deterministically, and write one SHA-256 per thing, over the raw pixel bytes of every frame.

    python3 tools/frame_hashes.py --out /tmp/before.json          # on the base branch
    # ...change the code...
    python3 tools/frame_hashes.py --out /tmp/after.json --compare /tmp/before.json   # exit 1 on any difference
    python3 tools/frame_hashes.py --only landmark/Castle --only transition/mike      # a subset, quickly
    python3 tools/frame_hashes.py --list                                             # every name

What is hashed, each at 64x32 and 64x64 (names end in @WxH):
  landmark/<Class>              every Landmark subclass: frame(t) every 0.2 s across its whole run, and title(t)
  landmark-screen/<Class>       its screen as show_screen draws it (title text included), through capture_screen()
  transition/<name>             every entry of TRANSITIONS, composed over a fixture screen, every frame
  fireworks/<theme>             the everyday castle fireworks (and the other THEMES), pre-roll plus 12 s, every frame
  fireworks-title               the "Lightning Lane LED" title, through capture_screen()
  show/<clip>.<version>         each synced show's V1 and V2 over the whole score, EVERY frame (N = 1)
  screen/park-info|ride|countdown/<fixture>   the title, ride and countdown screens through capture_screen()

Deterministic: every RNG is a random.Random(SEED) handed to the class (module-level random and numpy
are seeded too), the clock the screens read (utils.special_events.datetime) is frozen, the weather icon
is a fixture (no network), and the script re-runs itself with PYTHONHASHSEED=0 so set order can't vary.
Nothing opens the browser emulator. A thing that raises is recorded as "error: ..." (and so differs).
A synced show needs only its score under display/fireworks/shows/ (in git), not its WAV.
"""
import argparse
import contextlib
import hashlib
import json
import logging
import os
import random
import re
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEED = 1
FPS = 30  # the boards' frame rate; the show and transitions are sampled at it
WIDTH = 64
HEIGHTS = (32, 64)
LANDMARK_STEP_S = 0.2  # landmark frames sampled this often across the run
FIREWORKS_PREROLL = 20  # steps before the first frame, as render_castle_fireworks does
FIREWORKS_FRAMES = 12 * FPS
TRANSITION_TAIL_S = 5.0  # a transition that never stops animating is cut this long after its duration
SHOW_EVERY = 1  # hash every Nth frame of a show (every frame is still stepped and drawn, so the RNG draws stay in step)

logger = logging.getLogger("frame_hashes")


# ---------------------------------------------------------------------------------------- frames to bytes


def frame_bytes(pixels, width, height):
    """{(x, y): (r, g, b)} as width*height*3 raw bytes, black where nothing is lit; off-board pixels are dropped."""
    buf = bytearray(width * height * 3)
    for (x, y), rgb in pixels.items():
        if 0 <= x < width and 0 <= y < height:
            o = (int(y) * width + int(x)) * 3
            try:
                buf[o:o + 3] = bytes(rgb)
            except (ValueError, TypeError):  # a float or an out-of-range channel: clamp the way a panel would
                buf[o:o + 3] = bytes(max(0, min(255, int(c))) for c in rgb)
    return bytes(buf)


class FrameCanvas:
    """A canvas that keeps its pixels, black ones included (a blackout must erase), as a board's would."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        x, y = int(x), int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.px[(x, y)] = (r, g, b)

    def SetImage(self, image, x=0, y=0, *_):
        pixels = image.convert("RGB").load()
        for iy in range(image.height):
            for ix in range(image.width):
                self.SetPixel(int(x) + ix, int(y) + iy, *pixels[ix, iy])

    def Clear(self):
        self.px = {}


class Digest:
    """One SHA-256 over everything fed to it: frames (as bytes) and small tagged values."""

    def __init__(self):
        self.sha = hashlib.sha256()

    def frame(self, pixels, width, height):
        self.sha.update(frame_bytes(pixels, width, height))

    def value(self, value):
        self.sha.update(repr(value).encode())

    def hex(self):
        return self.sha.hexdigest()


def seed_everything(seed=SEED):
    """Module-level random (and numpy, if something uses it) start from the same place for each thing."""
    random.seed(seed)
    if "numpy" in sys.modules:
        sys.modules["numpy"].random.seed(seed)


# ---------------------------------------------------------------------------------------- the frozen clock

FROZEN_NOW_ISO = "2026-10-31T23:00:00+00:00"  # 7 PM at Magic Kingdom, Halloween: a party night
FROZEN_DAY = "2026-10-31"


def party_park():
    """Magic Kingdom on a party night, 7 PM to midnight, dated the frozen day: the scenes that print hours use it."""
    return {"name": "Magic Kingdom", "timezone": "America/New_York", "seasonalEvent": "halloween",
            "schedule": [{"type": "TICKETED_EVENT", "date": FROZEN_DAY, "description": "Special Ticketed Event",
                          "openingTime": f"{FROZEN_DAY}T19:00:00-04:00", "closingTime": f"{FROZEN_DAY}T23:59:00-04:00"}]}


@contextlib.contextmanager
def frozen_clock():
    """utils.special_events reads datetime.now(): freeze it for the run (what the screens and landmarks read)."""
    from datetime import datetime
    from unittest import mock

    from utils import special_events

    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            moment = datetime.fromisoformat(FROZEN_NOW_ISO)
            return moment.astimezone(tz) if tz else moment.replace(tzinfo=None)

    with mock.patch.object(special_events, "datetime", Frozen):
        yield


# ---------------------------------------------------------------------------------------- what is hashed
# Each hasher takes (width, height) and returns a hex digest. Imports are inside them, so that importing
# this module (the tests do) loads no display code, and a name is listed without building anything.


def landmark_classes():
    """Every Landmark subclass the app can show, by name, plus the pumpkin's two pinned motions."""
    import display.landmarks as landmarks
    from display.landmarks.scene import Landmark

    found = {}

    def walk(cls):
        for sub in cls.__subclasses__():
            if sub.__module__.startswith("display.landmarks"):
                found[sub.__name__] = sub
            walk(sub)
    walk(Landmark)
    pumpkin = landmarks.FriendlyJackOLanternLandmark
    for motion in pumpkin.MOTIONS:  # MOTION None picks one at random per showing: pin each
        found[f"FriendlyJackOLantern-{motion}"] = type(f"Friendly{motion}", (pumpkin,), {"MOTION": motion})
    return dict(sorted(found.items()))


def _landmark_run_s(scene):
    """How long the scene itself runs: its screen minus the sweep, and minus the wipe unless it plays under it."""
    import display.animation as animation
    wipe = 0 if scene.PLAYS_UNDER_WIPE else animation.TRANSITIONS["wipe"].duration
    return scene.SCREEN_S - animation.COVER_S - wipe


def _times(run_s, step_s):
    return [k * step_s for k in range(int(run_s / step_s) + 1)] + [run_s]


def hash_landmark(cls, width, height):
    seed_everything()
    scene = cls(width, height, random.Random(SEED), park=party_park())
    digest = Digest()
    for t in _times(_landmark_run_s(scene), LANDMARK_STEP_S):
        digest.frame(scene.frame(t), width, height)
        digest.value(scene.title(t))
    return digest.hex()


def hash_landmark_screen(cls, width, height):
    """The landmark as show_screen draws it, text and shadow included, at the start, middle and end of its run."""
    from display.capture import capture_screen
    from display.display import initialize_fonts
    from display.landmarks.screen import landmark_screen

    initialize_fonts(height)
    seed_everything()
    scene = cls(width, height, random.Random(SEED), park=party_park())
    draw = landmark_screen(scene)
    run_s = _landmark_run_s(scene)
    digest = Digest()
    for t in (0.0, run_s / 2, run_s):
        digest.frame(capture_screen(draw, t, width, height), width, height)
    return digest.hex()


def _fixture_screen(salt):
    """A busy, colourful screen (no text, no fonts) for transitions to cover and reveal."""
    def draw(canvas, t):
        for y in range(canvas.height):
            for x in range(canvas.width):
                canvas.SetPixel(x, y, (x * 4 + salt * 40) % 256, (y * 7 + salt * 90) % 256, ((x + y) * 3 + salt * 20) % 256)
        return False
    return draw


def hash_transition(name, width, height):
    """show_screen's composition without its clock: the new screen (held at its first frame until uncovered)
    with the reveal's overlay on top, every frame until the reveal says it's done."""
    from display.animation import TRANSITIONS

    seed_everything()
    prev_draw, new_draw = _fixture_screen(1), _fixture_screen(2)
    reveal = TRANSITIONS[name](width, height, random.Random(SEED))
    if getattr(reveal, "wants_prev", False):
        reveal.capture_prev(prev_draw, 0.0)
    if getattr(reveal, "wants_new", False):
        reveal.capture_new(new_draw, 0.0)
    over = getattr(reveal, "over_screen", False)
    run_s = reveal.duration + (getattr(reveal, "hold_after_s", None) or 0.0)
    digest = Digest()
    for i in range(int((run_s + TRANSITION_TAIL_S) * FPS) + 1):
        t = i / FPS
        canvas = FrameCanvas(width, height)
        new_draw(canvas, t if over else max(0.0, t - reveal.duration))
        moving = reveal.overlay(canvas, t)
        digest.frame(canvas.px, width, height)
        if not moving and t >= run_s:
            break
    digest.value(i)  # how long it ran is part of what it does
    return digest.hex()


def hash_fireworks(theme, width, height):
    from display.fireworks.fireworks import FireworksShow

    seed_everything()
    show = FireworksShow(width, height, random.Random(SEED), theme)
    for _ in range(FIREWORKS_PREROLL):
        show.step()
    digest = Digest()
    for _ in range(FIREWORKS_FRAMES):
        show.step()
        digest.frame(show.frame_pixels(), width, height)  # draws from the RNG, so it runs every frame
    digest.value(show.rng.getstate())
    return digest.hex()


def hash_fireworks_title(width, height):
    from display.capture import capture_screen
    from display.display import initialize_fonts, loaded_fonts
    from display.fireworks.fireworks import draw_title, title_layout

    initialize_fonts(height)
    font = loaded_fonts["title"]
    layout = title_layout(font, width, height)
    digest = Digest()
    for alpha in (0.0, 0.5, 1.0):
        digest.frame(capture_screen(lambda canvas, t, a=alpha: draw_title(canvas, font, layout, a), 0.0, width, height),
                     width, height)
    return digest.hex()


def show_versions():
    """[(clip name, version)] for every synced show with a score in git: v1 from <clip>.json, a later
    version from its <clip>.<version>.json overlay."""
    from display.fireworks.score import SHOWS_DIR

    names = sorted(f[:-5] for f in os.listdir(SHOWS_DIR) if f.endswith(".json"))
    pairs = []
    for name in names:
        if "." in name:
            continue
        pairs.append((name, "v1"))
        pairs += [(name, m.group(1)) for other in names if (m := re.fullmatch(re.escape(name) + r"\.(v\d+)", other))]
    return pairs


def hash_show(name, version, width, height):
    """The whole show as the board steps it (render_show.frames): the scene at each frame's time, one step, the
    picture. Every frame is stepped and drawn, and every SHOW_EVERY-th is hashed; the RNG's final state is too,
    so a changed number of draws on a frame that isn't hashed still shows."""
    from display.fireworks.music_show import MusicShow
    from display.fireworks.score import load_score

    score = load_score(name, version=version)
    if score is None:
        return "skipped: no usable score"
    seed_everything()
    show = MusicShow(width, height, random.Random(SEED), score.lips)
    digest = Digest()
    for i in range(int(score.end * FPS)):
        t = i / FPS
        show.set_cue(score.cue_at(t), t)
        show.step()
        pixels = show.frame_pixels()
        if i % SHOW_EVERY == 0:
            digest.frame(pixels, width, height)
    digest.value(show.rng.getstate())
    return digest.hex()


def _icon():
    """A 15x15 stand-in for the weather icon the board downloads: a fixed gradient."""
    from PIL import Image
    img = Image.new("RGB", (15, 15))
    for y in range(15):
        for x in range(15):
            img.putpixel((x, y), (x * 16, y * 16, 120))
    return img


def _park_fixtures():
    def iso(h, m):
        return f"{FROZEN_DAY}T{h:02d}:{m:02d}:00-04:00"
    weather = {"temperature": "72F", "short_description": "Clear", "icon": "01d"}
    return {
        "everyday": {"name": "Magic Kingdom", "timezone": "America/New_York", "openingTime": iso(9, 0),
                     "closingTime": iso(22, 0), "llmpPrice": "15", "weather": weather},
        "party": {**party_park(), "openingTime": iso(9, 0), "closingTime": iso(23, 59), "llmpPrice": "$20",
                  "weather": weather},
        "no-hours": {"name": "Disney's Hollywood Studios", "timezone": "America/New_York", "llmpPrice": ""},
    }


def hash_park_info(fixture, width, height):
    from display.display import initialize_fonts
    from display.park import park_details

    initialize_fonts(height)
    park_details.icon_cache["01d"] = _icon()  # no download: the icon is a fixture
    park = _park_fixtures()[fixture]
    return screen_digest(lambda canvas, t: park_details.render_park_information_screen(canvas, park), (0.0,), width, height)


RIDE_FIXTURES = {
    "wait": {"name": "Space Mountain", "waitTime": 35},
    "down": {"name": "Big Thunder Mountain Railroad", "waitTime": "Down"},
    "long-name": {"name": "Mickey and Minnie's Runaway Railway at Disney's Hollywood Studios", "waitTime": 120},
    "walk-on": {"name": "it's a small world", "waitTime": 5},
}
RIDE_TIMES = (0.0, 0.5, 1.0, 2.5, 4.0, 6.0)


def hash_ride(fixture, width, height):
    from display.attractions.attraction_info import draw_attraction_frame
    from display.display import initialize_fonts

    initialize_fonts(height)
    ride = RIDE_FIXTURES[fixture]
    return screen_digest(lambda canvas, t: draw_attraction_frame(canvas, ride, t, expected=40), RIDE_TIMES, width, height)


def _trip_fixtures():
    from datetime import date

    from utils.trips import Trip
    today = date.fromisoformat(FROZEN_DAY)
    def day(n):
        return date.fromordinal(today.toordinal() + n)
    return {
        "days-to-go": (Trip(day(42)), today),
        "named-trip": (Trip(day(9), day(16), "Our Big Trip"), today),
        "tomorrow": (Trip(day(1)), today),
        "disney-day": (Trip(day(0)), today),
        "under-way": (Trip(day(-2), day(3)), today),
    }


def hash_countdown(fixture, width, height):
    from display.countdown.countdown import render_countdown_to_disney
    from display.display import initialize_fonts

    initialize_fonts(height)
    trip, today = _trip_fixtures()[fixture]
    return screen_digest(lambda canvas, t: render_countdown_to_disney(canvas, trip, t, today), (0.0, 0.7, 1.5, 3.0, 6.5),
                            width, height)


def screen_digest(draw, times, width, height):
    """The hash of a screen's frames at the given times, drawn through capture_screen() as a board's captures are."""
    from display.capture import capture_screen

    seed_everything()
    digest = Digest()
    for t in times:
        digest.frame(capture_screen(draw, t, width, height), width, height)
    return digest.hex()


def catalog():
    """{name: callable returning a hex digest}: every thing this tool hashes, at both boards."""
    from display.animation import TRANSITIONS
    from display.fireworks.fireworks import THEMES

    things = {}
    for height in HEIGHTS:
        board = f"@{WIDTH}x{height}"
        for name, cls in landmark_classes().items():
            things[f"landmark/{name}{board}"] = lambda c=cls, h=height: hash_landmark(c, WIDTH, h)
            things[f"landmark-screen/{name}{board}"] = lambda c=cls, h=height: hash_landmark_screen(c, WIDTH, h)
        for name in TRANSITIONS:
            things[f"transition/{name}{board}"] = lambda n=name, h=height: hash_transition(n, WIDTH, h)
        for theme in (None, *THEMES):
            things[f"fireworks/{theme or 'everyday'}{board}"] = lambda th=theme, h=height: hash_fireworks(th, WIDTH, h)
        things[f"fireworks-title{board}"] = lambda h=height: hash_fireworks_title(WIDTH, h)
        for name, version in show_versions():
            things[f"show/{name}.{version}{board}"] = lambda n=name, v=version, h=height: hash_show(n, v, WIDTH, h)
        for fixture in _park_fixtures():
            things[f"screen/park-info/{fixture}{board}"] = lambda f=fixture, h=height: hash_park_info(f, WIDTH, h)
        for fixture in RIDE_FIXTURES:
            things[f"screen/ride/{fixture}{board}"] = lambda f=fixture, h=height: hash_ride(f, WIDTH, h)
        for fixture in _trip_fixtures():
            things[f"screen/countdown/{fixture}{board}"] = lambda f=fixture, h=height: hash_countdown(f, WIDTH, h)
    return things


# ---------------------------------------------------------------------------------------- running and comparing


def selected(names, only):
    """The names containing any of the `only` substrings (all of them when there are none)."""
    return [n for n in names if not only or any(o in n for o in only)]


def run(only=None, progress=None):
    """{name: digest} for every thing selected. A thing that raises gets "error: <type>: <message>"."""
    things = catalog()
    results = {}
    with frozen_clock():
        for name in selected(things, only):
            start = time.monotonic()
            try:
                results[name] = things[name]()
            except Exception as e:  # recorded as the result, so a refactor that breaks one shows up in compare
                logger.exception("%s failed", name)
                results[name] = f"error: {type(e).__name__}: {e}"
            if progress:
                progress(name, time.monotonic() - start)
    return results


def compare(old, new, only=None):
    """[(name, why)] for every name whose digest differs, is missing from either side, or is only on one."""
    names = selected(sorted(set(old) | set(new)), only)
    diffs = []
    for name in names:
        if name not in new:
            diffs.append((name, "missing from the new run"))
        elif name not in old:
            diffs.append((name, "not in the old run"))
        elif old[name] != new[name]:
            diffs.append((name, f"differs ({old[name][:12]} -> {new[name][:12]})"))
    return diffs


def _setup():
    """The environment the display code needs when this runs as a script from any directory."""
    os.environ.setdefault("LLL_LOG_DIR", tempfile.mkdtemp(prefix="lll-frame-hashes-"))  # not the real logs/app.log
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.chdir(ROOT)  # fonts and the shows are found relative to the repo root
    import driver
    if hasattr(driver, "set_mode"):  # not the test stub: never the hardware driver, never the browser emulator's server
        driver.set_mode(driver.DriverMode.SOFTWARE_EMULATION)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", help="write {name: sha256} here as JSON (default: print it)")
    parser.add_argument("--compare", metavar="OLD.json", help="compare with an earlier run; list every difference; exit 1 if any")
    parser.add_argument("--only", action="append", metavar="TEXT", help="only names containing TEXT (repeatable)")
    parser.add_argument("--list", action="store_true", help="list the names and stop")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    _setup()

    if args.list:
        print("\n".join(selected(catalog(), args.only)))
        return 0
    started = time.monotonic()
    results = run(args.only, progress=lambda name, s: print(f"{s:6.1f}s  {name}", file=sys.stderr))
    print(f"{len(results)} hashed in {time.monotonic() - started:.0f}s", file=sys.stderr)
    skipped = [n for n, v in results.items() if v.startswith("skipped")]
    for name in skipped:
        print(f"skipped {name}: {results[name]}", file=sys.stderr)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=1, sort_keys=True)
            f.write("\n")
    elif not args.compare:
        print(json.dumps(results, indent=1, sort_keys=True))
    if args.compare:
        with open(args.compare) as f:
            old = json.load(f)
        diffs = compare(old, results, args.only)
        for name, why in diffs:
            print(f"DIFFERENT {name}: {why}")
        print(f"{len(diffs)} differences")
        return 1 if diffs else 0
    return 0


if __name__ == "__main__":
    if os.environ.get("PYTHONHASHSEED") != "0":  # set order (frozenset of effect names...) must not vary between runs
        os.execve(sys.executable, [sys.executable, *sys.argv], {**os.environ, "PYTHONHASHSEED": "0"})
    sys.exit(main())
