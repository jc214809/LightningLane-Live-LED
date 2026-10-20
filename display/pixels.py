"""
Putting pixels on the board, shared by the transitions, the landmarks and the fireworks: sprites
from pixel art, bounds-checked setting and painting, blending over what's beneath, turning art
exactly (or by any angle, RotSprite's way), and a repeatable per-cell noise for textures.
"""
import math


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


def turn(point, pivot, degrees):
    """(x, y) turned `degrees` about pivot on the board (y down): positive turns counter-clockwise, so a
    point above the pivot goes left."""
    a = math.radians(degrees)
    dx, dy = point[0] - pivot[0], point[1] - pivot[1]
    return (pivot[0] + dx * math.cos(a) + dy * math.sin(a), pivot[1] - dx * math.sin(a) + dy * math.cos(a))


def _scale2x(grid):
    """Scale2x (EPX) on rows of cells (None empty): doubles the grid, keeping 1px lines and corners sharp."""
    h, w = len(grid), len(grid[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            p = grid[y][x]
            a = grid[y - 1][x] if y else p
            b = grid[y][x + 1] if x < w - 1 else p
            c = grid[y][x - 1] if x else p
            d = grid[y + 1][x] if y < h - 1 else p
            out[2 * y][2 * x] = a if c == a and c != d and a != b else p
            out[2 * y][2 * x + 1] = b if a == b and a != c and b != d else p
            out[2 * y + 1][2 * x] = c if d == c and d != b and c != a else p
            out[2 * y + 1][2 * x + 1] = d if b == d and b != a and d != c else p
    return out


def rotate_cells(cells, pivot, degrees, offset=(0.0, 0.0)):
    """
    Pixel art as {(x, y): kind} turned `degrees` about pivot (turn()'s direction), then moved by offset
    (which may be fractional): RotSprite's way, three Scale2x passes to 8x, then each cell takes the 8x
    sample under its centre turned back, so outlines stay one pixel and unbroken at any angle. Slow in
    pure Python (milliseconds per sprite): bake the poses, don't turn sprites every frame on a board.
    """
    if not cells:
        return {}
    if degrees % 360 == 0 and offset == (0.0, 0.0):
        return dict(cells)
    xs, ys = [p[0] for p in cells], [p[1] for p in cells]
    x0, y0 = min(xs) - 1, min(ys) - 1
    w, h = max(xs) - x0 + 2, max(ys) - y0 + 2
    grid = [[cells.get((x0 + c, y0 + r)) for c in range(w)] for r in range(h)]
    for _ in range(3):
        grid = _scale2x(grid)
    corners = [turn((x, y), pivot, degrees) for x in (x0, x0 + w) for y in (y0, y0 + h)]
    a = math.radians(degrees)
    co, si = math.cos(a), math.sin(a)
    px, py = pivot
    ox, oy = offset
    out = {}
    for y in range(int(math.floor(min(c[1] for c in corners) + oy)) - 1,
                   int(math.ceil(max(c[1] for c in corners) + oy)) + 1):
        for x in range(int(math.floor(min(c[0] for c in corners) + ox)) - 1,
                       int(math.ceil(max(c[0] for c in corners) + ox)) + 1):
            dx, dy = x + 0.5 - ox - px, y + 0.5 - oy - py
            gx = int(math.floor((px + dx * co - dy * si - x0) * 8))
            gy = int(math.floor((py + dx * si + dy * co - y0) * 8))
            if 0 <= gy < len(grid) and 0 <= gx < len(grid[0]) and grid[gy][gx] is not None:
                out[(x, y)] = grid[gy][gx]
    return out


def noise(x, y):
    """A repeatable 0..1 value per cell, for leafy and carved textures."""
    return (((x * 73856093) ^ (y * 19349663)) & 1023) / 1023
