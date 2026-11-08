#!/usr/bin/env python3
"""
Render the board's park landmarks (display/landmarks/screen.py LANDMARKS) to small PNGs in settings_page/static/,
with landmarks.json naming the file for each park key, so the settings page can show what the board plays before
each park without loading the display code: it runs as its own service and must stay up when the app can't.

Run from anywhere after changing a park landmark:  python3 tools/build_settings_art.py
"""
import io
import json
import logging
import os
import random
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "settings_page", "static")
INDEX = "landmarks.json"
WIDTH, HEIGHT, SCALE = 64, 32, 4  # the 64x32 board, each LED 4px so browsers can scale it crisply
STILL_S = 2.0  # the scene time each still is taken at
STILL_AT = {"CastleLandmark": 0.9}  # mid-way through its shooting star

logger = logging.getLogger(__name__)


def load_landmarks():
    """(LANDMARKS, SKY_RGB). display.display (which the landmarks import) only builds colours from driver.graphics;
    stubbing it keeps the real driver, which probes for hardware, out of a build step."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    sys.modules.setdefault("driver", types.SimpleNamespace(graphics=types.SimpleNamespace(Color=lambda *rgb: rgb)))
    from display.landmarks.scene import SKY_RGB
    from display.landmarks.screen import LANDMARKS
    return LANDMARKS, SKY_RGB


def still(cls, sky):
    """One frame of a landmark as an RGB Pillow image, WIDTH x HEIGHT LEDs. A scene with a character flying
    through it (Spaceship Earth's Tinker Bell) is taken without her: the still is the landmark."""
    from PIL import Image
    scene = cls(WIDTH, HEIGHT, rng=random.Random(7))
    for name in ("_draw_tink", "_draw_dust", "_draw_landing_burst"):
        if hasattr(scene, name):
            setattr(scene, name, lambda *args, **kwargs: None)
    t = STILL_AT.get(cls.__name__, STILL_S)
    if hasattr(cls, "SPIRAL_S"):  # every facet lit, which happens as she passes
        t = cls.SPIRAL_S + getattr(cls, "FLIT_S", 0) + 1.0
    image = Image.new("RGB", (WIDTH, HEIGHT), sky)
    for (x, y), rgb in scene.frame(t).items():
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            image.putpixel((x, y), tuple(int(c) for c in rgb))
    return image


def file_name(key):
    return "landmark-" + "-".join(key.split()) + ".png"


def render():
    """{park key: (file name, image)} for every park landmark."""
    landmarks, sky = load_landmarks()
    return {key: (file_name(key), still(cls, sky)) for key, cls in landmarks.items()}


def build(static=STATIC):
    """Write each landmark's PNG (scaled up SCALE times, nearest-neighbour) and landmarks.json; returns the index."""
    from PIL import Image
    index = {}
    for key, (name, image) in render().items():
        big = image.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.NEAREST)
        buf = io.BytesIO()
        big.save(buf, "PNG", optimize=True)
        with open(os.path.join(static, name), "wb") as f:
            f.write(buf.getvalue())
        index[key] = name
    with open(os.path.join(static, INDEX), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
        f.write("\n")
    return index


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    written = build()
    logger.info("Wrote %d landmark stills and %s to %s", len(written), INDEX, STATIC)
