"""
The everyday castle fireworks' art: the castle chart and its colours, the party burst shapes (Mickey
bauble, pumpkin, snowflake, star, tree, candy cane) as spark points, and Santa's sleigh team.
Split out of fireworks.py, which re-exports every name so old imports keep working.
"""

import math

# '.' empty, W wall, R roof, G gold finial, Y lit window, D doorway.
_CASTLE_ART = [
    "...........G...........",
    "...........R...........",
    "..........RRR..........",
    "..........RRR..........",
    ".........RRRRR.........",
    ".........WWYWW.........",
    "......G..WWWWW..G......",
    "......R..WWWWW..R......",
    ".....RRR.WWYWW.RRR.....",
    ".....RRR.WWWWW.RRR.....",
    "..G.RRRRRWWWWWRRRRR.G..",
    "..R..WYW.WWWWW.WYW..R..",
    ".RRR.WWW.WWYWW.WWW.RRR.",
    "RRRRRWWWWWWWWWWWWWRRRRR",
    ".WWW.WWWWWWWWWWWWW.WWW.",
    ".WYW.W.W.W.W.W.W.W.WYW.",
    ".WWWWWWWWWWWWWWWWWWWWW.",
    ".WWWWWWWWWDDDWWWWWWWWW.",
    ".WYWWWWWWDDDDDWWWWWWYW.",
    ".WWWWWWWWDDDDDWWWWWWWW.",
]

# The 2x castle alone gets a door 2 LEDs taller (not 4) with the black windows raised 2 LEDs to match:
# {LED row: art row to copy} across the main-wall columns only, leaving the corner turrets untouched.
_BIG_CASTLE_ROW_PATCH = {28: 15, 29: 15, 30: 16, 31: 16, 32: 17, 33: 17, 34: 19, 35: 19}
_MAIN_WALL_COLS = range(5, 18)

_CASTLE_COLORS = {
    "W": (190, 200, 230),
    "R": (40, 80, 200),
    "G": (255, 200, 50),
    "Y": (255, 190, 70),
    "D": (25, 15, 40),
}

# Only walls/roofs pick up light from bursts; windows, gold and the door keep their color.
_LIT_KINDS = {"W", "R"}

# (center_x, center_y, radius) in head-radius units: head plus two ears.
_MICKEY_CIRCLES = [(0.0, 0.0, 1.0), (-0.95, -0.95, 0.6), (0.95, -0.95, 0.6)]
# Head-radius multiples from the burst center to the shape's outer edge.
_MICKEY_HALF_WIDTH = 1.55
_MICKEY_TOP = 1.55

PUMPKIN_RGB, STEM_RGB, FACE_RGB = (255, 120, 10), (90, 210, 70), (255, 235, 110)
PUMPKIN_FILL_RGB = (225, 95, 5)  # deeper than the outline, so the edge and the face still stand out
MOON_RGB, BAT_RGB = (240, 235, 200), (8, 4, 12)

ORNAMENT_RGB, ORNAMENT_FILL_RGB = (230, 30, 30), (160, 15, 20)  # a red Mickey bauble, filled a deeper red
GREEN_ORNAMENT_RGB, GREEN_ORNAMENT_FILL_RGB = (40, 210, 60), (15, 120, 30)  # every other one is green
CAP_RGB, SHINE_RGB = (255, 200, 50), (255, 255, 255)  # its gold cap and loop, and the white shine on its head
FLAKE_RGB, FLAKE_TIP_RGB = (235, 245, 255), (150, 210, 255)  # a snowflake's white arms, icy-blue tips
STAR_RGB, STAR_FILL_RGB = (255, 200, 50), (150, 105, 15)  # a gold star, filled a deeper gold
TREE_RGB, TREE_FILL_RGB, TRUNK_RGB = (60, 220, 70), (20, 120, 35), (140, 85, 40)
TREE_LIGHTS = ((255, 40, 40), (255, 200, 50), (255, 255, 255), (80, 160, 255))  # its strand, round and round
CANE_RED, CANE_WHITE = (230, 30, 30), (255, 255, 255)
SNOW_RGB = (190, 200, 225)


def _mickey_outline():
    """Unit-radius points on the outer outline of Mickey's head and ears."""
    points = []
    for cx, cy, r in _MICKEY_CIRCLES:
        n = 44 if r == 1.0 else 26
        for i in range(n):
            a = 2 * math.pi * i / n
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            if not any(
                (px - ox) ** 2 + (py - oy) ** 2 < (orr - 0.05) ** 2
                for ox, oy, orr in _MICKEY_CIRCLES
                if (ox, oy, orr) != (cx, cy, r)
            ):
                points.append((px, py))
    return points


def _mickey_fill(radius, clear_of, gap, rgb):
    """One spark per LED across Mickey's head and ears, inside the outline and clear of it, leaving a
    `gap`-LED dark ring round each of the (x, y, rgb) points in `clear_of`."""
    step = 1 / radius
    n = int(1.6 / step) + 1
    points = []
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            x, y = i * step, j * step
            if not any((x - cx) ** 2 + (y - cy) ** 2 <= (r - 1.2 * step) ** 2 for cx, cy, r in _MICKEY_CIRCLES):
                continue
            if any((x - fx) ** 2 + (y - fy) ** 2 < (gap * step) ** 2 for fx, fy, _ in clear_of):
                continue
            points.append((x, y, rgb))
    return points


def _mickey_pumpkin_points(radius):
    """(x, y, rgb) in head-radius units for a Mickey jack-o'-lantern burst: Mickey's head and ears
    outlined in orange and filled a deeper orange, a green stem and a glowing carved face. Fewer
    face sparks on a small board, where they'd land on the same LED anyway."""
    points = [(x, y, PUMPKIN_RGB) for x, y in _mickey_outline()]
    face = _pumpkin_face(radius)
    # Fill: one spark per LED at full size, inside the shape, clear of the outline, with a dark
    # gap round the face like the edge of a carved hole, so the glow stands out from the orange.
    # On a small pumpkin the face's sparks sit an LED or so apart, so a 1.6-LED gap round each
    # would join up and empty the whole head (64x32's pumpkins had just an outline and a face):
    # there, only clear the LEDs the face itself lands on.
    points += _mickey_fill(radius, face, 1.6 if radius >= 6 else 0.6, PUMPKIN_FILL_RGB)
    # A stubby stem, about 3 sparks wide on a 64-row board, leaning a little to the right at the top.
    points += [(x, y, STEM_RGB) for y in (-1.08, -1.19) for x in (-0.11, 0.0, 0.11)]
    points += [(0.05, -1.3, STEM_RGB), (0.16, -1.3, STEM_RGB)]
    return points + face


def _pumpkin_face(radius):
    """The carved face's sparks, (x, y, rgb) in head-radius units."""
    points = []
    for ex in (-0.4, 0.4):  # triangle eyes, filled
        points += [
            (ex - 0.16, -0.1, FACE_RGB),
            (ex, -0.1, FACE_RGB),
            (ex + 0.16, -0.1, FACE_RGB),
            (ex - 0.08, -0.24, FACE_RGB),
            (ex + 0.08, -0.24, FACE_RGB),
            (ex, -0.38, FACE_RGB),
        ]
    steps = 11 if radius >= 6 else 5  # a grin, lowest in the middle
    for i in range(steps):
        u = -0.55 + 1.1 * i / (steps - 1)
        points.append((u, 0.3 + 0.2 * (1 - (u / 0.55) ** 2), FACE_RGB))
    return points


def _mickey_ornament_points(radius, outline=ORNAMENT_RGB, fill=ORNAMENT_FILL_RGB):
    """(x, y, rgb) in head-radius units for a Mickey Christmas-ornament burst: his head and ears
    outlined in red (or another colour) and filled a deeper shade, a gold cap with a loop on top of the
    head between the ears, and a white shine at the upper left (with a dark gap round it, so it reads)."""
    big = radius >= 6
    step = 1 / radius
    points = [(x, y, outline) for x, y in _mickey_outline()]
    shine = (
        [(-0.55, -0.3), (-0.55, -0.41), (-0.44, -0.52), (-0.33, -0.52)]
        if big
        else [(-0.4, -0.2), (-0.4, -0.4), (-0.2, -0.4)]
    )  # on the 5-LED grid
    shine = [(x, y, SHINE_RGB) for x, y in shine]
    points += _mickey_fill(radius, shine, 1.6 if big else 0.6, fill)
    # The cap sits on the head's top (y = -1): 3 sparks wide and 2 tall on a 64-row board, 2 by 1 on
    # a small one; the hook is a little ring (a single bar on a small board) above it.
    w = 3 if big else 2
    xs = [(i - (w - 1) / 2) * step for i in range(w)]
    rows = 2 if big else 1
    points += [(x, -1.0 - step * (1 + j), CAP_RGB) for j in range(rows) for x in xs]
    top = -1.0 - step * (rows + 1)
    if big:
        points += [
            (xs[0], top, CAP_RGB),
            (xs[2], top, CAP_RGB),
            (xs[0], top - step, CAP_RGB),
            (xs[1], top - step, CAP_RGB),
            (xs[2], top - step, CAP_RGB),
        ]
    else:
        points += [(x, top, CAP_RGB) for x in xs]
    return points + shine


def _green_ornament_points(radius):
    """The Mickey ornament in green: the Christmas show alternates red and green ones."""
    return _mickey_ornament_points(radius, GREEN_ORNAMENT_RGB, GREEN_ORNAMENT_FILL_RGB)


def _line(x0, y0, x1, y1, radius):
    """Points from (x0, y0) to (x1, y1), both ends included (head-radius units), one per LED along the
    longer axis so a slanted line has no gaps."""
    n = max(1, int(math.ceil(max(abs(x1 - x0), abs(y1 - y0)) * radius)))
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def _inside(x, y, polygon):
    """Whether (x, y) is inside the polygon [(x, y), ...] (even-odd rule)."""
    inside = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
    return inside


def _outlined(polygon, radius, edge_rgb, fill_rgb):
    """A polygon's outline (one spark per LED it crosses) and a fill of every LED inside it right up
    to the outline, so there's no dark ring between them."""
    step = 1 / radius
    edge = {
        (round(x * radius), round(y * radius))
        for a, b in zip(polygon, polygon[1:] + polygon[:1])
        for x, y in _line(*a, *b, radius)
    }
    n = int(1.6 * radius) + 1
    fill = {
        (i, j)
        for j in range(-n, n + 1)
        for i in range(-n, n + 1)
        if (i, j) not in edge and _inside(i * step, j * step, polygon)
    }
    return [(i * step, j * step, edge_rgb) for i, j in sorted(edge)] + [
        (i * step, j * step, fill_rgb) for i, j in sorted(fill)
    ]


def _snowflake_points(radius):
    """A snowflake burst: six white arms from the centre, each with a V of two branches part way out,
    and icy-blue tips. Branches are shorter on a small board, where they'd blur into the arm."""
    big = radius >= 6
    points = []
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3  # one arm straight up
        ux, uy = math.cos(a), -math.sin(a)
        points += [(x, y, FLAKE_RGB) for x, y in _line(0, 0, ux * 0.95, uy * 0.95, radius)]
        points.append((ux * 1.08, uy * 1.08, FLAKE_TIP_RGB))
        at, length = (0.55, 0.35) if big else (0.6, 0.25)
        for side in (-1, 1):  # branches angled out toward the tip
            b = a + side * math.pi / 4
            bx, by = ux * at + math.cos(b) * length, uy * at - math.sin(b) * length
            points += [
                (x, y, FLAKE_TIP_RGB if (x, y) == (bx, by) else FLAKE_RGB)
                for x, y in _line(ux * at, uy * at, bx, by, radius)[1:]
            ]
    return points


# The star's ten corners, points and inner corners in turn, one point straight up; nudged down a little
# since it's taller above its centre than below.
_STAR_CORNERS = [
    (
        (1.05 if k % 2 == 0 else 0.45) * math.cos(-math.pi / 2 + k * math.pi / 5),
        (1.05 if k % 2 == 0 else 0.45) * math.sin(-math.pi / 2 + k * math.pi / 5) + 0.1,
    )
    for k in range(10)
]
# The tree's tiers, top to bottom: (top, bottom, half-width at the bottom), in head-radius units.
_TREE_TIERS = [(-0.95, -0.25, 0.42), (-0.5, 0.25, 0.62), (-0.05, 0.8, 0.85)]


def _star_points(radius):
    """A five-pointed gold star burst, one point straight up, outlined and filled a deeper gold."""
    return _outlined(_STAR_CORNERS, radius, STAR_RGB, STAR_FILL_RGB)


def _tree_points(radius):
    """A Christmas tree burst: three green tiers, outlined and filled, with a strand of coloured
    lights, a gold star on top and a brown trunk."""
    big = radius >= 6
    step = 1 / radius
    tiers = _TREE_TIERS
    points, lights = [], []
    for t, (top, bottom, half) in enumerate(tiers):
        points += _outlined([(0.0, top), (half, bottom), (-half, bottom)], radius, TREE_RGB, TREE_FILL_RGB)
        # Lights along the tier's bottom edge, one LED in, every other few LEDs.
        y = bottom - step
        spacing = 3 if big else 2
        xs = [i * step for i in range(-int(half * radius) + 1, int(half * radius)) if i % spacing == t % spacing]
        lights += [(x, y) for x in xs]
    lights = [(x, y, TREE_LIGHTS[i % len(TREE_LIGHTS)]) for i, (x, y) in enumerate(lights)]
    # Lights replace whatever was drawn where they land.
    taken = {(round(x * radius), round(y * radius)) for x, y, _ in lights}
    points = [p for p in points if (round(p[0] * radius), round(p[1] * radius)) not in taken]
    star_y = tiers[0][0] - step
    star = [
        (0.0, star_y, STAR_RGB),
        (0.0, star_y - step, STAR_RGB),
        (-step, star_y - step, STAR_RGB),
        (step, star_y - step, STAR_RGB),
        (0.0, star_y - 2 * step, STAR_RGB),
    ]
    trunk_w = 2 if big else 1
    trunk = [
        ((i - (trunk_w - 1) / 2) * step, tiers[-1][1] + step * (1 + j), TRUNK_RGB)
        for j in range(2 if big else 1)
        for i in range(trunk_w)
    ]
    return points + lights + star + trunk


# The candy cane: a vertical stick from y = -1 to 1 (2 head-radii tall) at x = _CANE_X, with a hook
# curling over its top to the right, always the same side so no extra rng is drawn.
_CANE_X, _CANE_HOOK_R = -0.4, 0.5


def _candy_cane_points(radius):
    """(x, y, rgb) in head-radius units for a candy-cane burst: a stick 3 sparks wide on a 64-row board
    (2 on a small one) with a round hook over the top, striped red and white in diagonal bands."""
    big = radius >= 6
    step = 1 / radius
    w = 3 if big else 2
    band = 3 if big else 2  # LEDs per stripe
    offsets = [k - (w - 1) // 2 for k in range(w)]  # whole LEDs, so it is w wide whatever the rounding

    def colour(along, k):  # `along` LEDs from the foot; the column shifts the band for the diagonal
        return CANE_RED if int((along + k) // band) % 2 == 0 else CANE_WHITE

    points = []
    for j in range(2 * radius + 1):  # the stick, foot to the top of the hook's start
        y = 1.0 - j * step
        points += [(_CANE_X + o * step, y, colour(j, k)) for k, o in enumerate(offsets)]
    hx, hy, rr = _CANE_X + _CANE_HOOK_R, -1.0, _CANE_HOOK_R
    for k, o in enumerate(offsets):
        r = rr - o * step  # the stick's left edge is the hook's outer rim
        n = int(math.pi * r * radius * 1.3) + 2
        for i in range(1, n + 1):
            a = math.pi - (math.pi + 0.45) * i / n  # over the top and a little way down the far side
            points.append(
                (hx + r * math.cos(a), hy - r * math.sin(a), colour(2 * radius + r * radius * (math.pi - a), k))
            )
    return points


# Per shape: its points (given the radius), its rocket and flash colour, and (half-width, top, bottom)
# in head-radius units where they differ from Mickey's, to keep it on the board and clear of the castle.
_SHAPE_POINTS = {
    "mickey_pumpkin": _mickey_pumpkin_points,
    "mickey_ornament": _mickey_ornament_points,
    "mickey_ornament_green": _green_ornament_points,
    "candy_cane": _candy_cane_points,
    "snowflake": _snowflake_points,
    "star": _star_points,
    "tree": _tree_points,
}
_SHAPE_RGB = {
    "mickey_pumpkin": PUMPKIN_RGB,
    "mickey_ornament": ORNAMENT_RGB,
    "mickey_ornament_green": GREEN_ORNAMENT_RGB,
    "candy_cane": CANE_RED,
    "snowflake": FLAKE_RGB,
    "star": STAR_RGB,
    "tree": TREE_RGB,
}
# Shapes that take turns: each time this one is picked, the next pick is the other (red, then green).
_SHAPE_TURNS = {"mickey_ornament": "mickey_ornament_green"}
# Shapes that burst at an angle, picked at random per burst (degrees clockwise): a candy cane leans
# either way or lies on its side, never upside down.
_SHAPE_TILTS = {"candy_cane": (-40, -25, 25, 40, 90)}
# Placed by Mickey's head-and-ears extents rather than by their own points, so the Halloween show's
# frames stay as they were; every other party shape is kept on the board by its own (tilted) points.
_MICKEY_PLACED = {"mickey", "mickey_pumpkin"}


def _shape_points(shape, radius, tilt=0):
    """A party shape's (x, y, rgb) points in head-radius units, turned `tilt` degrees clockwise."""
    points = _SHAPE_POINTS[shape](radius)
    if not tilt:
        return points
    c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    return [(x * c - y * s, x * s + y * c, rgb) for x, y, rgb in points]


# Santa's sleigh team, drawn flying right (mirrored for left), the user's pick from mocks (2026-11-08):
# 64x32 boards get Santa and two reindeer at 1x, 64x64 boards Santa and Rudolph doubled.


# '.' empty, N Rudolph's nose (it blinks), n another reindeer's (black), B a reindeer, b its far legs,
# A antlers, L the gold reins, S the sleigh, K its gold runner, R Santa's red, W his white, F his face,
# G his dark green sack.
_REINDEER = [  # leaping, with a muzzle that puts the nose out in front of the head
    "......A.A...",
    ".......AA...",
    "........BBn.",
    "B.......BB..",
    ".BBBBBBBB...",
    "..BBBBBB....",
    ".b.....bB...",
    "b........B..",
]
_RUDOLPH = [row.replace("n", "N") for row in _REINDEER]
_SANTA_SLEIGH = [  # Santa faces the reindeer: his hat's pom trails behind, his face and beard in front
    "....WRR.......",
    ".....RRRR.....",
    ".GG..WWWWW....",
    "GGGG.WFFFF....",
    "SGGSRRRWWWS..K",
    "SSSSSSSSSSS.K.",
    ".SSSSSSSSSKK..",
    "KKKKKKKKKK....",
]
_REINS_ROW = 4  # the rows of the art where the reins run between sleigh and team


def _sleigh_team(reindeer):
    """The sleigh, reins, then `reindeer` reindeer with Rudolph in front, as rows of one width."""
    rows = range(len(_SANTA_SLEIGH))
    parts = [_SANTA_SLEIGH, [".L" if r == _REINS_ROW else ".." for r in rows]]
    for k in range(reindeer):
        if k == reindeer - 1:
            parts.append(_RUDOLPH)
        else:
            parts += [_REINDEER, ["L" if r == _REINS_ROW else "." for r in rows]]
    return ["".join(part[r] for part in parts) for r in rows]


_SLEIGH_ART_SMALL = _sleigh_team(2)
_SLEIGH_ART_BIG = ["".join(c * 2 for c in row) for row in _sleigh_team(1) for _ in range(2)]
_SLEIGH_COLORS = {
    "A": (200, 160, 100),
    "B": (150, 90, 40),
    "b": (95, 55, 25),
    "n": (0, 0, 0),
    "L": (230, 200, 60),
    "S": (205, 20, 25),
    "K": (255, 200, 50),
    "R": (235, 40, 40),
    "W": (255, 255, 255),
    "F": (255, 190, 150),
    "G": (20, 110, 40),
}
_NOSE_BRIGHT, _NOSE_DIM = (255, 40, 40), (120, 20, 20)


def castle_sprite(board_height):
    """Return (pixels, width, height); pixels is a list of (dx, dy, kind), scaled 2x on 64-row boards."""
    scale = 2 if board_height >= 64 else 1
    grid = [[kind for kind in line for _ in range(scale)] for line in _CASTLE_ART for _ in range(scale)]
    if scale == 2:
        for led_row, art_row in _BIG_CASTLE_ROW_PATCH.items():
            for col in _MAIN_WALL_COLS:
                grid[led_row][col * 2] = grid[led_row][col * 2 + 1] = _CASTLE_ART[art_row][col]
    pixels = [(x, y, kind) for y, row in enumerate(grid) for x, kind in enumerate(row) if kind != "."]
    return pixels, len(grid[0]), len(grid)
