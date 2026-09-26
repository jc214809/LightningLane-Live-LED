#!/usr/bin/env python3
"""
Embed every character sprite and its palette from display/animation.py into
tools/sprite_editor.html, so the editor always opens on the art the board draws.

Run from anywhere after changing character art:  python3 tools/build_sprite_editor.py
"""
import json
import logging
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITOR = os.path.join(ROOT, "tools", "sprite_editor.html")
BEGIN, END = "/*SPRITES:BEGIN*/", "/*SPRITES:END*/"
# Keys the art uses but the palette doesn't define (Stitch's '#' eye slots, filled at
# draw time) still need a color in the editor; grey marks them as placeholders.
UNMAPPED_RGB = [128, 128, 128]

logger = logging.getLogger(__name__)


def load_animation():
    # animation.py only touches driver.graphics while drawing. Stubbing it keeps the real
    # driver, which parses argv and probes for hardware, out of a build step.
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    sys.modules.setdefault("driver", types.SimpleNamespace(graphics=None))
    from display import animation
    return animation


def _is_art(value):
    return (isinstance(value, list) and len(value) > 1
            and all(isinstance(row, str) for row in value)
            and len({len(row) for row in value}) == 1 and len(value[0]) > 1)


def _palette(cls):
    for name in ("COLORS", "colors"):
        palette = getattr(cls, name, None)
        if isinstance(palette, dict) and palette:
            return name, palette
    return "COLORS", {}


def collect_sprites(animation):
    """
    {"slinky/FRONT_ART": {character, attr, label, palette_attr, rows, colors, unmapped}}.
    A sprite is any class attribute that is a list of equal-width strings, or a list of
    those (animation frames). Aliases of the same art (Dumbo's `art = EARS_UP`) appear once.
    """
    sprites, seen = {}, set()
    for character, cls in animation.TRANSITIONS.items():
        palette_attr, palette = _palette(cls)
        for attr in sorted(dir(cls)):
            value = getattr(cls, attr)
            if _is_art(value):
                frames = [value]
            elif isinstance(value, list) and value and all(_is_art(f) for f in value):
                frames = value
            else:
                continue
            for i, rows in enumerate(frames):
                if (character, tuple(rows)) in seen:
                    continue
                seen.add((character, tuple(rows)))
                label = attr if len(frames) == 1 else f"{attr}[{i}]"
                used = sorted({ch for row in rows for ch in row} - {"."})
                colors = {k: list(rgb) for k, rgb in palette.items() if len(k) == 1}
                unmapped = [k for k in used if k not in colors]
                colors.update({k: list(UNMAPPED_RGB) for k in unmapped})
                # A sprite drawn at a fixed size on every board declares it: per sprite
                # (Genie's LAMP_ART has LAMP_SCALE) or for the whole class (SCALE).
                # The rest double on 64-row boards.
                fixed = getattr(cls, attr[:-len("ART")] + "SCALE", None) if attr.endswith("ART") else None
                fixed = fixed if fixed is not None else getattr(cls, "SCALE", None)
                sprites[f"{character}/{label}"] = {
                    "character": character, "attr": attr, "label": label,
                    "scale": fixed if isinstance(fixed, int) else None,
                    "palette_attr": palette_attr, "rows": list(rows),
                    "colors": colors, "unmapped": unmapped,
                }
    return sprites


def embedded_sprites(html):
    start, end = html.index(BEGIN) + len(BEGIN), html.index(END)
    return json.loads(html[start:end])


def build(path=EDITOR, animation=None):
    """Rewrite the sprite block in the editor. Returns how many sprites it holds."""
    sprites = collect_sprites(animation or load_animation())
    with open(path, encoding="utf-8") as f:
        html = f.read()
    start, end = html.index(BEGIN) + len(BEGIN), html.index(END)
    updated = html[:start] + json.dumps(sprites, separators=(",", ":")) + html[end:]
    if updated != html:
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
    return len(sprites)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Embedded %d sprites into %s", build(), os.path.relpath(EDITOR))
