"""
Putting pixels on the board: sprites from pixel art, painting, blacking out, turning art.
"""

from driver import graphics


EDGE_RGB = (255, 215, 0)


def art_pixels(art, x0, y0, colors, scale=1):
    """
    ((x, y), rgb) for every lit cell of pixel art ('.' is empty) with its top-left at
    (x0, y0), each cell drawn scale x scale. Pair with paint(), or px.update() to add a
    sprite to a scene's pixels.
    """
    for row, line in enumerate(art):
        for col, kind in enumerate(line):
            if kind == ".":
                continue
            rgb = colors[kind]
            for sy in range(scale):
                for sx in range(scale):
                    yield (x0 + col * scale + sx, y0 + row * scale + sy), rgb


def paint(canvas, pixels, width, height):
    """Set each ((x, y), rgb) that lands on the board; pixels is a {(x, y): rgb} dict or pairs."""
    if isinstance(pixels, dict):
        pixels = pixels.items()
    for (x, y), rgb in pixels:
        if 0 <= x < width and 0 <= y < height:
            canvas.SetPixel(x, y, *rgb)


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


def _rotate_art(art, quarters):
    """Pixel art turned counter-clockwise by 90 degrees `quarters` times: exact, no smearing."""
    for _ in range(quarters % 4):
        art = ["".join(row[len(row) - 1 - c] for row in art) for c in range(len(art[0]))]
    return art


def _letters(text, font):
    """A banner's text as art rows: the font's 3x5 letters a column apart, a cell of cloth round it."""
    rows = ["." * 0] * 5
    for ch in text:
        glyph = font[ch]
        rows = [row + ("." if row else "") + g for row, g in zip(rows, glyph)]
    width = len(rows[0]) + 2
    body = ["Q" + row.replace(".", "Q").replace("#", "X") + "Q" for row in rows]
    return ["Q" * width] + body + ["Q" * width]
