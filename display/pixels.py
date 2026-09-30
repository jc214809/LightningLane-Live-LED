"""
Putting pixels on the board, shared by the transitions, the landmarks and the fireworks: sprites
from pixel art, bounds-checked setting and painting, blending over what's beneath, turning art
exactly, and a repeatable per-cell noise for textures.
"""


def put(pixels, x, y, rgb, width, height):
    """Add (x, y) to a {(x, y): rgb} scene if it's on the board."""
    if 0 <= x < width and 0 <= y < height:
        pixels[(x, y)] = rgb


def set_pixel(canvas, x, y, rgb, width, height):
    """SetPixel if (x, y) is on the board."""
    if 0 <= x < width and 0 <= y < height:
        canvas.SetPixel(x, y, *rgb)


def paint(canvas, pixels, width, height):
    """Set each ((x, y), rgb) that lands on the board; pixels is a {(x, y): rgb} dict or pairs."""
    if isinstance(pixels, dict):
        pixels = pixels.items()
    for (x, y), rgb in pixels:
        if 0 <= x < width and 0 <= y < height:
            canvas.SetPixel(x, y, *rgb)


def blend(rgb, under, alpha):
    """rgb laid over `under` at alpha (0 shows only under, 1 only rgb): soft light, never a hole."""
    return tuple(int(u + (c - u) * alpha) for c, u in zip(rgb, under))


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


def rotate_art(art, quarters):
    """Pixel art turned counter-clockwise by 90 degrees `quarters` times: exact, no smearing."""
    for _ in range(quarters % 4):
        art = ["".join(row[len(row) - 1 - c] for row in art) for c in range(len(art[0]))]
    return art


def noise(x, y):
    """A repeatable 0..1 value per cell, for leafy and carved textures."""
    return (((x * 73856093) ^ (y * 19349663)) & 1023) / 1023
