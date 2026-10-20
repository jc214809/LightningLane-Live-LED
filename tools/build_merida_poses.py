#!/usr/bin/env python3
"""
Bake Merida's Touch the Sky poses (display/fireworks/actors/merida_poses.py) into merida_poses.json, so a
board only looks them up: turning her sprites live is far too slow for a Pi Zero.

Run from anywhere after changing her poses or the archer's art:  python3 tools/build_merida_poses.py
"""
import json
import logging
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


def load_poses():
    # The archer's module imports display.animation, which only touches driver.graphics while drawing.
    # Stubbing it keeps the real driver, which parses argv and probes for hardware, out of a build step.
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    sys.modules.setdefault("driver", types.SimpleNamespace(graphics=None))
    from display.fireworks.actors import merida_poses
    return merida_poses


def render(frames):
    """The file's text: one frame a line, so a change shows as a readable diff."""
    lines = ['{"note": "Baked by tools/build_merida_poses.py from merida_poses.py; do not edit.", "frames": {']
    keys = list(frames)
    for i, key in enumerate(keys):
        lines.append("%s: %s%s" % (json.dumps(key), json.dumps(frames[key], separators=(",", ":")),
                                   "," if i < len(keys) - 1 else ""))
    lines.append("}}")
    return "\n".join(lines) + "\n"


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    poses = load_poses()
    frames = poses.bake()
    with open(poses.BAKED, "w") as f:
        f.write(render(frames))
    logger.info("baked %d frames into %s", len(frames), os.path.relpath(poses.BAKED, ROOT))


if __name__ == "__main__":
    main()
