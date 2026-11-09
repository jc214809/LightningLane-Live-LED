import math
import random
import time

from driver import graphics
from display.animation import frame_canvas, present
from display.display import get_text_width, loaded_fonts
from utils import debug
from display.motion import smooth

# The full name is too wide for one line on a 64-px board, even in 4x6.
TITLE_LINES = ("Lightning Lane", "LED")
TITLE_RGB = (255, 215, 0)
TITLE_DELAY_S = 0.5
TITLE_FADE_S = 1.5
_OUTLINE_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]

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

_PALETTE = [
    (255, 60, 60),
    (255, 170, 30),
    (255, 235, 80),
    (70, 255, 110),
    (60, 180, 255),
    (180, 90, 255),
    (255, 90, 200),
    (255, 255, 255),
]

# Show themes: burst colours, a sky gradient (top, bottom) and castle colour overrides by art key.
# No theme is the everyday show on a black sky.
THEMES = {
    "halloween": {
        "palette": [(255, 120, 10), (255, 165, 40), (210, 120, 255), (170, 90, 255),
                    (110, 255, 120), (60, 210, 90), (255, 255, 255)],
        "sky": ((34, 6, 52), (14, 8, 30)),
        # Dusky lavender walls and purple roofs; windows and finials glow orange.
        "castle": {"W": (150, 135, 185), "R": (100, 55, 160), "Y": (255, 130, 20), "G": (255, 150, 30)},
        "flicker_windows": True,  # each window flickers on its own, like a candle
        "moon": True,
        "bats": True,
        # Burst shapes and their chance per launch; the everyday show's is {"mickey": MICKEY_CHANCE}.
        "shapes": {"mickey_pumpkin": 0.15},  # as often as the everyday show's Mickey bursts
    },
    "christmas": {
        # Reds and greens listed twice over the rest, so they lead; a little icy blue for the snow.
        "palette": [(230, 30, 30), (255, 80, 80), (40, 200, 60), (100, 255, 120),
                    (255, 255, 255), (255, 200, 50), (150, 210, 255)],
        "sky": ((8, 12, 48), (2, 4, 20)),  # midnight blue
        # White walls, red roofs, green windows and gold finials; steady, no flicker.
        "castle": {"W": (225, 225, 235), "R": (200, 25, 30), "Y": (110, 220, 90), "G": (255, 200, 50)},
        "snow": True,
        "sleigh": True,
        "shapes": {"mickey_ornament": 0.08, "candy_cane": 0.07},  # together as often as the everyday Mickeys
    },
}

GRAVITY = 0.035
DRAG = 0.965

MICKEY_CHANCE = 0.15
MICKEY_LIFE = 55
# (center_x, center_y, radius) in head-radius units: head plus two ears.
_MICKEY_CIRCLES = [(0.0, 0.0, 1.0), (-0.95, -0.95, 0.6), (0.95, -0.95, 0.6)]
# Head-radius multiples from the burst center to the shape's outer edge.
_MICKEY_HALF_WIDTH = 1.55
_MICKEY_TOP = 1.55

PUMPKIN_RGB, STEM_RGB, FACE_RGB = (255, 120, 10), (90, 210, 70), (255, 235, 110)
PUMPKIN_FILL_RGB = (225, 95, 5)  # deeper than the outline, so the edge and the face still stand out
MOON_RGB, BAT_RGB = (240, 235, 200), (8, 4, 12)

ORNAMENT_RGB, ORNAMENT_FILL_RGB = (230, 30, 30), (160, 15, 20)  # a red Mickey bauble, filled a deeper red
CAP_RGB, SHINE_RGB = (255, 200, 50), (255, 255, 255)  # its gold cap and loop, and the white shine on its head
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
            if not any((px - ox) ** 2 + (py - oy) ** 2 < (orr - 0.05) ** 2
                       for ox, oy, orr in _MICKEY_CIRCLES if (ox, oy, orr) != (cx, cy, r)):
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
        points += [(ex - 0.16, -0.1, FACE_RGB), (ex, -0.1, FACE_RGB), (ex + 0.16, -0.1, FACE_RGB),
                   (ex - 0.08, -0.24, FACE_RGB), (ex + 0.08, -0.24, FACE_RGB), (ex, -0.38, FACE_RGB)]
    steps = 11 if radius >= 6 else 5  # a grin, lowest in the middle
    for i in range(steps):
        u = -0.55 + 1.1 * i / (steps - 1)
        points.append((u, 0.3 + 0.2 * (1 - (u / 0.55) ** 2), FACE_RGB))
    return points


def _mickey_ornament_points(radius):
    """(x, y, rgb) in head-radius units for a Mickey Christmas-ornament burst: his head and ears
    outlined in red and filled a deeper red, a gold cap with a loop on top of the head between the
    ears, and a white shine at the upper left (with a dark gap round it, so it reads)."""
    big = radius >= 6
    step = 1 / radius
    points = [(x, y, ORNAMENT_RGB) for x, y in _mickey_outline()]
    shine = [(-0.55, -0.3), (-0.55, -0.41), (-0.44, -0.52), (-0.33, -0.52)] if big \
        else [(-0.4, -0.2), (-0.4, -0.4), (-0.2, -0.4)]  # on the 5-LED grid
    shine = [(x, y, SHINE_RGB) for x, y in shine]
    points += _mickey_fill(radius, shine, 1.6 if big else 0.6, ORNAMENT_FILL_RGB)
    # The cap sits on the head's top (y = -1): 3 sparks wide and 2 tall on a 64-row board, 2 by 1 on
    # a small one; the hook is a little ring (a single bar on a small board) above it.
    w = 3 if big else 2
    xs = [(i - (w - 1) / 2) * step for i in range(w)]
    rows = 2 if big else 1
    points += [(x, -1.0 - step * (1 + j), CAP_RGB) for j in range(rows) for x in xs]
    top = -1.0 - step * (rows + 1)
    if big:
        points += [(xs[0], top, CAP_RGB), (xs[2], top, CAP_RGB),
                   (xs[0], top - step, CAP_RGB), (xs[1], top - step, CAP_RGB), (xs[2], top - step, CAP_RGB)]
    else:
        points += [(x, top, CAP_RGB) for x in xs]
    return points + shine


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
            points.append((hx + r * math.cos(a), hy - r * math.sin(a),
                           colour(2 * radius + r * radius * (math.pi - a), k)))
    return points


# Per shape: its points (given the radius), its rocket and flash colour, and (half-width, top, bottom)
# in head-radius units where they differ from Mickey's, to keep it on the board and clear of the castle.
_SHAPE_POINTS = {"mickey_pumpkin": _mickey_pumpkin_points, "mickey_ornament": _mickey_ornament_points,
                 "candy_cane": _candy_cane_points}
_SHAPE_RGB = {"mickey_pumpkin": PUMPKIN_RGB, "mickey_ornament": ORNAMENT_RGB, "candy_cane": CANE_RED}
_SHAPE_EXTENTS = {"candy_cane": (0.8, 1.5, 1.0)}
# Shapes that burst at an angle, picked at random per burst (degrees clockwise): a candy cane leans
# either way or lies on its side, never upside down. Where a shape is placed then comes from its
# tilted points, not _SHAPE_EXTENTS.
_SHAPE_TILTS = {"candy_cane": (-40, -25, 25, 40, 90)}


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
_SLEIGH_COLORS = {"A": (200, 160, 100), "B": (150, 90, 40), "b": (95, 55, 25), "n": (0, 0, 0),
                  "L": (230, 200, 60), "S": (205, 20, 25), "K": (255, 200, 50), "R": (235, 40, 40),
                  "W": (255, 255, 255), "F": (255, 190, 150), "G": (20, 110, 40)}
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


class _Rocket:
    __slots__ = ("x", "y", "vx", "vy", "burst_y", "color", "mickey", "shape", "tilt")

    def __init__(self, x, y, vx, vy, burst_y, color, mickey=False, shape=None, tilt=0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.burst_y = burst_y
        self.color = color
        self.mickey = mickey
        self.shape = shape  # a party burst shape (a key of _SHAPE_POINTS), or None
        self.tilt = tilt  # degrees clockwise the shape bursts at (a candy cane's; see _SHAPE_TILTS)


class _Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "gravity", "hold")

    def __init__(self, x, y, vx, vy, life, color, gravity=GRAVITY, hold=1.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color
        self.gravity = gravity
        self.hold = hold  # >1 keeps a spark bright longer before it fades (shape bursts)


class FireworksShow:
    """Frame-stepped castle + fireworks simulation; knows nothing about the matrix driver."""

    def __init__(self, width, height, rng=None, theme=None):
        self.width = width
        self.height = height
        self.rng = rng or random.Random()
        style = THEMES[theme] if theme else {}
        self.palette = style.get("palette", _PALETTE)
        self.castle_colors = {**_CASTLE_COLORS, **style.get("castle", {})}
        self.shapes = style.get("shapes")
        self.flicker_windows = style.get("flicker_windows", False)
        self.frame = 0
        self.sky = {}
        if "sky" in style:
            top, bottom = style["sky"]
            for y in range(height):
                p = y / max(1, height - 1)
                rgb = tuple(int(a + (b - a) * p) for a, b in zip(top, bottom))
                for x in range(width):
                    self.sky[(x, y)] = rgb
        self.rockets = []
        self.sparks = []
        self.flash = [0.0, 0.0, 0.0]
        self.frames_to_next_launch = 0

        self.castle_pixels, cw, ch = castle_sprite(height)
        self.castle_x = (width - cw) // 2
        self.castle_y = height - ch
        self.castle_w = cw
        self.castle_h = ch

        big = height >= 64
        self.spark_count = 48 if big else 22
        self.spark_speed = 1.1 if big else 0.6
        self.rocket_speed = 1.6 if big else 1.1
        self.launch_gap = (6, 16) if big else (10, 26)
        self.mickey_radius = 7 if big else 4
        self.shape_radius = 9 if big else 5  # party shapes are bigger than Mickey bursts, so their faces read
        self.stars = [
            (self.rng.randrange(width), self.rng.randrange(max(1, self.castle_y + ch // 2)))
            for _ in range(width // 5)
        ]
        self.moon = self._moon() if style.get("moon") else {}
        self.bats_on = style.get("bats", False)
        self.bats = []
        if self.bats_on:
            # One bat crosses the moon soon after the show starts; more come at random.
            self._add_bat(from_left=True, y=self.moon_y if self.moon else height * 0.2)
        self.snow = self._snowfall() if style.get("snow") else []
        self.sleigh_art = _SLEIGH_ART_BIG if big else _SLEIGH_ART_SMALL
        self.sleighs = []  # [x, y, vx]: at most one in the sky
        if style.get("sleigh"):
            # Santa crosses soon after the show starts; another now and then once he's gone.
            self._add_sleigh(from_left=True, y=self._sleigh_lowest() / 2)
        self.sleigh_on = style.get("sleigh", False)

    def _moon(self):
        big = self.height >= 64
        r = 6.0 if big else 3.5
        cx, cy = (10.5, 10.5) if big else (7.0, 6.0)
        self.moon_y = cy
        # A crescent: the disc minus a slightly smaller one shifted up and right, so it opens that way.
        bite_x, bite_y, bite_r = cx + 0.5 * r, cy - 0.25 * r, r * 0.9
        moon = {}
        for y in range(int(cy - r), int(cy + r) + 2):
            for x in range(int(cx - r), int(cx + r) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and (x - bite_x) ** 2 + (y - bite_y) ** 2 > bite_r ** 2:
                    moon[(x, y)] = MOON_RGB
        return moon

    def _snowfall(self):
        """Flakes as [x, y, fall speed, drift phase], spread over the whole sky."""
        big = self.height >= 64
        return [[self.rng.uniform(0, self.width), self.rng.uniform(0, self.height),
                 self.rng.uniform(0.15, 0.3) if big else self.rng.uniform(0.1, 0.2), self.rng.uniform(0, 2 * math.pi)]
                for _ in range(self.width // (4 if big else 6))]

    def _sleigh_lowest(self):
        """The lowest top row that keeps the whole sleigh team above the castle's spire."""
        return max(0, self.castle_y - len(self.sleigh_art) - 1)

    def _add_sleigh(self, from_left, y):
        speed = (0.45 if self.height >= 64 else 0.3) * self.rng.uniform(0.9, 1.1)
        width = len(self.sleigh_art[0])
        self.sleighs.append([-float(width) if from_left else self.width + 1.0, y, speed if from_left else -speed])

    def _sleigh_pixels(self, sleigh):
        """[(x, y, rgb)] for the sleigh, mirrored when it flies left; Rudolph's nose blinks slowly."""
        x0, y0, vx = sleigh
        art = self.sleigh_art
        width = len(art[0])
        nose = _NOSE_BRIGHT if (self.frame // 12) % 2 == 0 else _NOSE_DIM
        pixels = []
        for r, row in enumerate(art):
            for c, kind in enumerate(row):
                if kind != ".":
                    dx = c if vx > 0 else width - 1 - c
                    pixels.append((int(round(x0)) + dx, int(round(y0)) + r, nose if kind == "N" else _SLEIGH_COLORS[kind]))
        return pixels

    def _add_bat(self, from_left, y):
        speed = (0.55 if self.height >= 64 else 0.35) * self.rng.uniform(0.8, 1.2)
        x = -3.0 if from_left else self.width + 2.0
        self.bats.append([x, y, speed if from_left else -speed, self.rng.uniform(0, 2 * math.pi)])

    def _bat_pixels(self, bat):
        """A small V of wings that flaps: up and down every few frames, bobbing as it flies."""
        x, y0, vx, phase = bat
        y = y0 + 1.5 * math.sin(self.frame * 0.15 + phase)
        up = (self.frame // 4 + int(phase * 10)) % 2 == 0
        tip = -1 if up else 1
        if self.height >= 64:
            offsets = [(0, 0), (-1, 0), (1, 0), (-2, tip), (2, tip), (-3, tip * 2 if up else tip), (3, tip * 2 if up else tip)]
        else:
            offsets = [(0, 0), (-1, tip), (1, tip)]
        return [(int(round(x)) + dx, int(round(y)) + dy) for dx, dy in offsets]

    def launch(self):
        rng = self.rng
        top = self.height * 0.12
        bottom = self.castle_y + self.castle_h * 0.15
        shape = self._pick_shape()
        if shape:
            # Keep the whole shape (a head-and-ears silhouette at most) on the board.
            mickey = shape == "mickey"
            radius = self.mickey_radius if mickey else self.shape_radius
            tilt = rng.choice(_SHAPE_TILTS[shape]) if shape in _SHAPE_TILTS else 0
            if shape in _SHAPE_TILTS:
                points = _shape_points(shape, radius, tilt)
                left, right = -min(p[0] for p in points), max(p[0] for p in points)
                up, down = -min(p[1] for p in points), max(p[1] for p in points)
                x = rng.uniform(left * radius + 1, self.width - right * radius - 1)
            else:
                reach, up, down = _SHAPE_EXTENTS.get(shape, (_MICKEY_HALF_WIDTH, _MICKEY_TOP, 1.0))
                half_w = reach * radius + 1
                x = rng.uniform(half_w, self.width - half_w)
            top = max(top, up * radius + 1)
            if not mickey:
                # A party shape (a pumpkin's face, say) must clear the castle, or the spire hides it.
                bottom = min(bottom, self.castle_y - down * radius)
            burst_y = rng.uniform(top, max(top + 1, bottom))
            color = _SHAPE_RGB[shape] if not mickey else rng.choice(self.palette)
            self.rockets.append(_Rocket(x, self.height - 1, 0.0, -self.rocket_speed, burst_y, color,
                                        mickey=mickey, shape=None if mickey else shape, tilt=tilt))
            return
        # Half the rockets rise from behind the castle, half from the grounds on either side.
        if rng.random() < 0.5:
            x = self.castle_x + rng.uniform(2, self.castle_w - 3)
        else:
            margin = max(2, self.castle_x - 1)
            x = rng.uniform(1, margin) if rng.random() < 0.5 else rng.uniform(self.width - margin, self.width - 2)
        burst_y = rng.uniform(top, max(top + 1, bottom))
        vx = rng.uniform(-0.12, 0.12)
        self.rockets.append(_Rocket(x, self.height - 1, vx, -self.rocket_speed, burst_y, rng.choice(self.palette)))

    def _pick_shape(self):
        roll = self.rng.random()
        for shape, chance in (self.shapes or {"mickey": MICKEY_CHANCE}).items():
            if roll < chance:
                return shape
            roll -= chance
        return None

    def _explode_shape(self, rocket):
        """Burst into the rocket's party shape (a Mickey jack-o'-lantern, say); like the Mickey burst,
        every spark shares one life so the shape expands, holds and fades together."""
        travel = (1 - DRAG ** (MICKEY_LIFE * 0.6)) / (1 - DRAG)
        speed = self.shape_radius / travel
        for px, py, rgb in _shape_points(rocket.shape, self.shape_radius, rocket.tilt):
            self.sparks.append(_Spark(rocket.x, rocket.y, px * speed, py * speed,
                                      MICKEY_LIFE, rgb, gravity=GRAVITY * 0.2, hold=1.8))

    def _explode_mickey(self, rocket):
        radius = self.mickey_radius
        # Scale launch speed so the shape reaches full size ~60% of the way through its life.
        travel = (1 - DRAG ** (MICKEY_LIFE * 0.6)) / (1 - DRAG)
        speed = radius / travel
        for cx, cy, r in _MICKEY_CIRCLES:
            n = max(8, int(2 * math.pi * r * radius))
            for i in range(n):
                a = 2 * math.pi * i / n
                px, py = cx + r * math.cos(a), cy + r * math.sin(a)
                # Only the outer outline of the union — skip points buried inside another circle.
                if any((px - ox) ** 2 + (py - oy) ** 2 < (orr - 0.05) ** 2
                       for ox, oy, orr in _MICKEY_CIRCLES if (ox, oy, orr) != (cx, cy, r)):
                    continue
                self.sparks.append(_Spark(rocket.x, rocket.y, px * speed, py * speed,
                                          MICKEY_LIFE, rocket.color, gravity=GRAVITY * 0.2))

    def _explode(self, rocket):
        if rocket.mickey:
            self._explode_mickey(rocket)
            self._add_flash(rocket.color)
            return
        if rocket.shape:
            self._explode_shape(rocket)
            self._add_flash(rocket.color)
            return
        rng = self.rng
        second = rng.choice(self.palette) if rng.random() < 0.35 else None
        ring = rng.random() < 0.3
        for i in range(self.spark_count):
            angle = (2 * math.pi * i / self.spark_count) if ring else rng.uniform(0, 2 * math.pi)
            speed = self.spark_speed * (1.0 if ring else rng.uniform(0.3, 1.0))
            color = second if (second and i % 2) else rocket.color
            life = rng.randint(28, 44)
            self.sparks.append(_Spark(rocket.x, rocket.y, math.cos(angle) * speed, math.sin(angle) * speed, life, color))
        self._add_flash(rocket.color)

    def _add_flash(self, color):
        for c in range(3):
            self.flash[c] = min(1.0, self.flash[c] + color[c] / 255 * 0.6)

    def step(self):
        if self.frames_to_next_launch <= 0:
            self.launch()
            if self.rng.random() < 0.3:
                self.launch()
            self.frames_to_next_launch = self.rng.randint(*self.launch_gap)
        self.frames_to_next_launch -= 1

        still_rising = []
        for r in self.rockets:
            r.x += r.vx
            r.y += r.vy
            r.vy += GRAVITY * 0.3
            if r.y <= r.burst_y or r.vy >= 0:
                self._explode(r)
            else:
                still_rising.append(r)
        self.rockets = still_rising

        alive = []
        for s in self.sparks:
            s.vx *= DRAG
            s.vy = s.vy * DRAG + s.gravity
            s.x += s.vx
            s.y += s.vy
            s.life -= 1
            if s.life > 0 and -2 <= s.x < self.width + 2 and s.y < self.height:
                alive.append(s)
        self.sparks = alive

        self.flash = [f * 0.85 for f in self.flash]

        self.frame += 1
        if self.bats_on:
            for bat in self.bats:
                bat[0] += bat[2]
            self.bats = [b for b in self.bats if -4 <= b[0] <= self.width + 3]
            if len(self.bats) < 3 and self.rng.random() < 0.012:
                self._add_bat(self.rng.random() < 0.5, self.rng.uniform(2, max(3, self.castle_y * 0.6)))
        for flake in self.snow:
            flake[1] += flake[2]
            if flake[1] >= self.height:  # off the bottom: back to the top somewhere new
                flake[0], flake[1] = self.rng.uniform(0, self.width), 0.0
        if self.sleigh_on:
            for sleigh in self.sleighs:
                sleigh[0] += sleigh[2]
            width = len(self.sleigh_art[0])
            self.sleighs = [z for z in self.sleighs if -width - 1 <= z[0] <= self.width + 1]
            if not self.sleighs and self.rng.random() < 0.003:
                self._add_sleigh(self.rng.random() < 0.5, self.rng.uniform(0, self._sleigh_lowest()))

    def frame_pixels(self):
        """Compose the current frame as {(x, y): (r, g, b)}; unlisted pixels are black."""
        # Sparks and stars blend over the sky with max(), so a burst still reads on purple.
        out = dict(self.sky)
        out.update(self.moon)

        def put(x, y, rgb):
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < self.width and 0 <= yi < self.height:
                prev = out.get((xi, yi))
                if prev:
                    rgb = tuple(max(a, b) for a, b in zip(prev, rgb))
                out[(xi, yi)] = rgb

        for sx, sy in self.stars:
            twinkle = 25 + int(25 * self.rng.random())
            put(sx, sy, (twinkle, twinkle, twinkle + 10))

        for fx, fy, _, phase in self.snow:
            put(fx + math.sin(self.frame * 0.05 + phase), fy, SNOW_RGB)

        for s in self.sparks:
            f = min(1.0, s.life / s.max_life * s.hold)
            # Fresh sparks run white-hot, then settle into their color and fade (a held spark only
            # stays bright longer; its white flash is as quick as anyone's).
            hot = max(0.0, (s.life / s.max_life - 0.8) / 0.2)
            rgb = tuple(int((c + (255 - c) * hot) * f) for c in s.color)
            put(s.x, s.y, rgb)
            if f > 0.5:
                put(s.x - s.vx * 1.5, s.y - s.vy * 1.5, tuple(int(c * f * 0.35) for c in s.color))

        for r in self.rockets:
            put(r.x, r.y, (255, 230, 180))
            put(r.x, r.y + 1, (140, 90, 40))
            put(r.x, r.y + 2, (50, 30, 10))

        # Bats are silhouettes: drawn over the sky, moon and sparks rather than blended.
        for bat in self.bats:
            for x, y in self._bat_pixels(bat):
                if 0 <= x < self.width and 0 <= y < self.height:
                    out[(x, y)] = BAT_RGB

        # Santa's sleigh is opaque like the bats: over the sky and sparks, under the castle.
        for sleigh in self.sleighs:
            for x, y, rgb in self._sleigh_pixels(sleigh):
                if 0 <= x < self.width and 0 <= y < self.height:
                    out[(x, y)] = rgb

        # Castle is drawn last so it occludes anything launched from behind it.
        for dx, dy, kind in self.castle_pixels:
            x, y = self.castle_x + dx, self.castle_y + dy
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue
            base = self.castle_colors[kind]
            if kind == "Y" and self.flicker_windows:
                level = 0.8 + 0.1 * math.sin(self.frame * 0.9 + dx * 1.7 + dy * 2.3) \
                    + 0.1 * math.sin(self.frame * 0.37 + dx * 0.7)
                base = tuple(int(c * level) for c in base)
            if kind in _LIT_KINDS:
                base = tuple(min(255, int(c * 0.75 + 110 * f)) for c, f in zip(base, self.flash))
            out[(x, y)] = base
        return out


def title_alpha(elapsed_s):
    """Title opacity 0..1: hidden for TITLE_DELAY_S, then a smoothstep fade-in over TITLE_FADE_S."""
    return smooth((elapsed_s - TITLE_DELAY_S) / TITLE_FADE_S)


def title_layout(font, width, board_height):
    """Return [(x, baseline_y, text)] centering each line horizontally at the top of the board."""
    top = 0 if board_height < 64 else 3
    return [
        ((width - get_text_width(font, text)) // 2, top + font.baseline + i * font.height, text)
        for i, text in enumerate(TITLE_LINES)
    ]


def draw_title(canvas, font, layout, alpha):
    if alpha <= 0:
        return
    color = graphics.Color(*(int(c * alpha) for c in TITLE_RGB))
    black = graphics.Color(0, 0, 0)
    for x, y, text in layout:
        # A 1-px black outline keeps the letters readable when sparks pass behind them.
        for ox, oy in _OUTLINE_OFFSETS:
            graphics.DrawText(canvas, font, x + ox, y + oy, black, text)
        graphics.DrawText(canvas, font, x, y, color, text)


def render_castle_fireworks(matrix, duration=12.0, fps=30, rng=None, title=True, theme=None):
    """Animate the castle fireworks scene on the matrix for `duration` seconds, with or without the
    app's title, in a THEMES look (None for the everyday show)."""
    show = FireworksShow(matrix.width, matrix.height, rng, theme)
    canvas = frame_canvas(matrix)
    frame_time = 1.0 / fps
    frames = int(duration * fps)
    font = loaded_fonts.get("title")
    layout = title_layout(font, matrix.width, matrix.height) if font and title else []
    debug.info(f"Rendering castle fireworks for {duration}s ({frames} frames).")
    # Pre-roll so the sky isn't empty on the first frame.
    for _ in range(20):
        show.step()
    for i in range(frames):
        start = time.monotonic()
        show.step()
        canvas.Clear()
        for (x, y), (r, g, b) in show.frame_pixels().items():
            canvas.SetPixel(x, y, r, g, b)
        # Drawn over the sparks so bursts pass behind the name.
        draw_title(canvas, font, layout, title_alpha(i / fps))
        canvas = present(matrix, canvas)
        remaining = frame_time - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)
    matrix.Clear()
