"""
Drawing a screen into memory instead of onto the board, for the transitions that need a
screen's pixels (Ralph shatters the old screen, WALL-E eats it, Mickey assembles the new one).

On a Pi, rgbmatrix's DrawText and DrawLine are compiled and only accept rgbmatrix's own
canvas, and that canvas can't be read back. So while a screen is captured, text and lines
are drawn here instead, in Python, from the same BDF font files, onto a canvas that just
records its pixels. The emulator's drawing functions would take the recording canvas
directly; this path is used on both so that what's tested is what runs on the board.
"""
import contextlib

from driver import graphics
from utils import debug

# BDF file behind each loaded font, keyed by id(font); filled by display.initialize_fonts.
font_paths = {}
_glyph_cache = {}
_REPLACEMENT = 0xFFFD


class Capture:
    """Stand-in canvas that records what a screen draws: {(x, y): (r, g, b)}, lit pixels only."""

    def __init__(self, width, height):
        self.width, self.height, self.px = width, height, {}

    def SetPixel(self, x, y, r, g, b):
        if 0 <= x < self.width and 0 <= y < self.height and (r or g or b):
            self.px[(int(x), int(y))] = (r, g, b)

    def SetImage(self, image, x=0, y=0, *_):
        """Like the canvas's SetImage: copy an RGB PIL image onto it, black pixels included."""
        pixels = image.convert("RGB").load()
        for iy in range(image.height):
            for ix in range(image.width):
                px, py = int(x) + ix, int(y) + iy
                self.px.pop((px, py), None)
                self.SetPixel(px, py, *pixels[ix, iy])

    def Clear(self):
        self.px = {}


def _glyphs(path):
    """{codepoint: (advance, height, x_offset, y_offset, rows, width)} from a BDF file, rows as bit strings."""
    if path not in _glyph_cache:
        glyphs, current, rows = {}, None, None
        with open(path, encoding="latin-1") as f:
            for line in f:
                key, _, rest = line.strip().partition(" ")
                if key == "ENCODING":
                    current = {"code": int(rest.split()[0])}
                elif current is None:
                    continue
                elif key == "DWIDTH":
                    current["advance"] = int(rest.split()[0])
                elif key == "BBX":
                    w, h, x_off, y_off = map(int, rest.split())
                    current.update(width=w, height=h, x_offset=x_off, y_offset=y_off)
                elif key == "BITMAP":
                    rows = []
                elif key == "ENDCHAR":
                    if current.get("code", -1) >= 0 and rows is not None:
                        glyphs[current["code"]] = (current.get("advance", 0), current.get("height", 0),
                                                   current.get("x_offset", 0), current.get("y_offset", 0),
                                                   rows[:current.get("height", 0)], current.get("width", 0))
                    current, rows = None, None
                elif rows is not None and key:
                    rows.append(bin(int(key, 16))[2:].zfill(len(key) * 4))
        _glyph_cache[path] = glyphs
    return _glyph_cache[path]


def _rgb(color):
    return int(color.red), int(color.green), int(color.blue)


def draw_text(canvas, font, x, y, color, text):
    """graphics.DrawText for a Capture: y is the baseline; returns the width drawn."""
    path = font_paths.get(id(font))
    if path is None:
        raise ValueError("can't capture text in a font that wasn't loaded through initialize_fonts")
    glyphs = _glyphs(path)
    rgb = _rgb(color)
    start = x
    for ch in text:
        glyph = glyphs.get(ord(ch)) or glyphs.get(_REPLACEMENT)
        if glyph is None:
            continue
        advance, height, x_offset, y_offset, rows, width = glyph
        top = y - height - y_offset
        for r, bits in enumerate(rows):
            for c in range(min(width, len(bits))):
                if bits[c] == "1":
                    canvas.SetPixel(x + x_offset + c, top + r, *rgb)
        x += advance
    return x - start


def draw_line(canvas, x0, y0, x1, y1, color):
    """graphics.DrawLine for a Capture: Bresenham, both ends included."""
    rgb = _rgb(color)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        canvas.SetPixel(x0, y0, *rgb)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


@contextlib.contextmanager
def _software_graphics():
    """Swap in the Python DrawText and DrawLine for as long as a screen is being captured."""
    swaps = {"DrawText": draw_text, "DrawLine": draw_line}
    saved = {name: getattr(graphics, name, None) for name in swaps}
    for name, fn in swaps.items():
        setattr(graphics, name, fn)
    try:
        yield
    finally:
        for name, fn in saved.items():
            if fn is None:
                delattr(graphics, name)
            else:
                setattr(graphics, name, fn)


def capture_screen(draw, t, width, height):
    """
    The lit pixels of draw(canvas, t), drawn in memory. A screen that still can't be drawn
    this way is logged and gives whatever it managed (possibly nothing): a transition that
    eats a blank screen is better than one that takes the app down.
    """
    shot = Capture(width, height)
    try:
        with _software_graphics():
            draw(shot, t)
    except Exception:
        debug.exception("Couldn't capture a screen for a transition; using what was drawn so far.")
    return shot.px
