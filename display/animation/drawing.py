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


# A walk in four poses for side-on pixel art, as (dx, dy) for the foot behind and the foot
# ahead: striding apart, the back foot lifting, feet passing, the front foot lifting.
WALK_CYCLE = (((-1, 0), (1, 0)), ((0, -1), (0, 0)), ((1, 0), (-1, 0)), ((0, 0), (0, -1)))


def walking_pixels(art, x0, y0, colors, feet, pose, facing=1, scale=1):
    """
    ((x, y), rgb) for art (see art_pixels) with its feet stepping through WALK_CYCLE[pose % 4]
    (None stands still). feet is (first foot row, columns of the foot behind, columns of the
    foot ahead); either set may hold more than one paw. facing is 1 for art facing right, -1
    for art facing left (its steps go the other way). scale draws each cell scale x scale,
    feet rows, columns and steps counted in cells. Feet are drawn over the body, so a
    lifted foot covers the leg above it rather than leaving a hole.
    """
    top, behind, ahead = feet
    offsets = WALK_CYCLE[pose % 4] if pose is not None else ((0, 0), (0, 0))
    body, stepping = [], []
    for (x, y), rgb in art_pixels(art, x0, y0, colors, scale):
        row, col = (y - y0) // scale, (x - x0) // scale
        for cols, (dx, dy) in zip((behind, ahead), offsets):
            if row >= top and col in cols:
                stepping.append(((x + dx * facing * scale, y + dy * scale), rgb))
                break
        else:
            body.append(((x, y), rgb))
    return body + stepping
