"""
Blacking out and edging for the transitions, and the banner lettering (the general pixel helpers are display.pixels').
"""

from driver import graphics

from display.pixels import art_pixels, paint, rotate_art as _rotate_art  # noqa: F401  (re-exported)


EDGE_RGB = (255, 215, 0)


def _blackout(canvas, x0, x1, height):
    black = graphics.Color(0, 0, 0)
    for x in range(max(0, x0), x1):
        graphics.DrawLine(canvas, x, 0, x, height - 1, black)


def _blackout_rows(canvas, y0, y1, width):
    black = graphics.Color(0, 0, 0)
    for y in range(max(0, y0), y1):
        graphics.DrawLine(canvas, 0, y, width - 1, y, black)


def _edge(canvas, x, width, height):
    if 0 <= x < width:
        graphics.DrawLine(canvas, x, 0, x, height - 1, graphics.Color(*EDGE_RGB))


def _letters(text, font):
    """A banner's text as art rows: the font's 3x5 letters a column apart, a cell of cloth round it."""
    rows = ["." * 0] * 5
    for ch in text:
        glyph = font[ch]
        rows = [row + ("." if row else "") + g for row, g in zip(rows, glyph)]
    width = len(rows[0]) + 2
    body = ["Q" + row.replace(".", "Q").replace("#", "X") + "Q" for row in rows]
    return ["Q" * width] + body + ["Q" * width]
