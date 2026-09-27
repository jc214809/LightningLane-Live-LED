import math
import random
import time

from driver import graphics
from display.animation import frame_canvas, present
from display.display import get_text_width, loaded_fonts
from utils import debug

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


def _mickey_pumpkin_points(radius):
    """(x, y, rgb) in head-radius units for a Mickey jack-o'-lantern burst: Mickey's head and ears
    outlined in orange and filled a deeper orange, a green stem and a glowing carved face. Fewer
    face sparks on a small board, where they'd land on the same LED anyway."""
    points = [(x, y, PUMPKIN_RGB) for x, y in _mickey_outline()]
    face = _pumpkin_face(radius)
    # Fill: one spark per LED at full size, inside the shape, clear of the outline, with a dark
    # gap round the face like the edge of a carved hole, so the glow stands out from the orange.
    step = 1 / radius
    n = int(1.6 / step) + 1
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            x, y = i * step, j * step
            if not any((x - cx) ** 2 + (y - cy) ** 2 <= (r - 1.2 * step) ** 2 for cx, cy, r in _MICKEY_CIRCLES):
                continue
            if any((x - fx) ** 2 + (y - fy) ** 2 < (1.6 * step) ** 2 for fx, fy, _ in face):
                continue
            points.append((x, y, PUMPKIN_FILL_RGB))
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
    __slots__ = ("x", "y", "vx", "vy", "burst_y", "color", "mickey", "shape")

    def __init__(self, x, y, vx, vy, burst_y, color, mickey=False, shape=None):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.burst_y = burst_y
        self.color = color
        self.mickey = mickey
        self.shape = shape  # a Halloween burst shape ("mickey_pumpkin"), or None


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
        self.shape_radius = 9 if big else 5  # pumpkins are bigger than Mickey bursts, so their faces read
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
            half_w = _MICKEY_HALF_WIDTH * radius + 1
            x = rng.uniform(half_w, self.width - half_w)
            top = max(top, _MICKEY_TOP * radius + 1)
            if not mickey:
                # A pumpkin's face must clear the castle, or the spire hides it.
                bottom = min(bottom, self.castle_y - radius)
            burst_y = rng.uniform(top, max(top + 1, bottom))
            color = PUMPKIN_RGB if not mickey else rng.choice(self.palette)
            self.rockets.append(_Rocket(x, self.height - 1, 0.0, -self.rocket_speed, burst_y, color,
                                        mickey=mickey, shape=None if mickey else shape))
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
        """Burst into a Mickey jack-o'-lantern; like the Mickey burst, every spark shares one life
        so the shape expands, holds and fades together."""
        travel = (1 - DRAG ** (MICKEY_LIFE * 0.6)) / (1 - DRAG)
        speed = self.shape_radius / travel
        for px, py, rgb in _mickey_pumpkin_points(self.shape_radius):
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
    t = (elapsed_s - TITLE_DELAY_S) / TITLE_FADE_S
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


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
