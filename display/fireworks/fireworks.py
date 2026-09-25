import math
import random
import time

from driver import graphics
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

GRAVITY = 0.035
DRAG = 0.965

MICKEY_CHANCE = 0.15
MICKEY_LIFE = 55
# (center_x, center_y, radius) in head-radius units: head plus two ears.
_MICKEY_CIRCLES = [(0.0, 0.0, 1.0), (-0.95, -0.95, 0.6), (0.95, -0.95, 0.6)]
# Head-radius multiples from the burst center to the shape's outer edge.
_MICKEY_HALF_WIDTH = 1.55
_MICKEY_TOP = 1.55


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
    __slots__ = ("x", "y", "vx", "vy", "burst_y", "color", "mickey")

    def __init__(self, x, y, vx, vy, burst_y, color, mickey=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.burst_y = burst_y
        self.color = color
        self.mickey = mickey


class _Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "gravity")

    def __init__(self, x, y, vx, vy, life, color, gravity=GRAVITY):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color
        self.gravity = gravity


class FireworksShow:
    """Frame-stepped castle + fireworks simulation; knows nothing about the matrix driver."""

    def __init__(self, width, height, rng=None):
        self.width = width
        self.height = height
        self.rng = rng or random.Random()
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
        self.stars = [
            (self.rng.randrange(width), self.rng.randrange(max(1, self.castle_y + ch // 2)))
            for _ in range(width // 5)
        ]

    def launch(self):
        rng = self.rng
        top = self.height * 0.12
        bottom = self.castle_y + self.castle_h * 0.15
        if rng.random() < MICKEY_CHANCE:
            # Keep the whole head-and-ears silhouette on the board.
            half_w = _MICKEY_HALF_WIDTH * self.mickey_radius + 1
            x = rng.uniform(half_w, self.width - half_w)
            top = max(top, _MICKEY_TOP * self.mickey_radius + 1)
            burst_y = rng.uniform(top, max(top + 1, bottom))
            self.rockets.append(_Rocket(x, self.height - 1, 0.0, -self.rocket_speed, burst_y, rng.choice(_PALETTE), mickey=True))
            return
        # Half the rockets rise from behind the castle, half from the grounds on either side.
        if rng.random() < 0.5:
            x = self.castle_x + rng.uniform(2, self.castle_w - 3)
        else:
            margin = max(2, self.castle_x - 1)
            x = rng.uniform(1, margin) if rng.random() < 0.5 else rng.uniform(self.width - margin, self.width - 2)
        burst_y = rng.uniform(top, max(top + 1, bottom))
        vx = rng.uniform(-0.12, 0.12)
        self.rockets.append(_Rocket(x, self.height - 1, vx, -self.rocket_speed, burst_y, rng.choice(_PALETTE)))

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
        rng = self.rng
        second = rng.choice(_PALETTE) if rng.random() < 0.35 else None
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

    def frame_pixels(self):
        """Compose the current frame as {(x, y): (r, g, b)}; unlisted pixels are black."""
        out = {}

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
            f = s.life / s.max_life
            # Fresh sparks run white-hot, then settle into their color and fade.
            hot = max(0.0, (f - 0.8) / 0.2)
            rgb = tuple(int((c + (255 - c) * hot) * f) for c in s.color)
            put(s.x, s.y, rgb)
            if f > 0.5:
                put(s.x - s.vx * 1.5, s.y - s.vy * 1.5, tuple(int(c * f * 0.35) for c in s.color))

        for r in self.rockets:
            put(r.x, r.y, (255, 230, 180))
            put(r.x, r.y + 1, (140, 90, 40))
            put(r.x, r.y + 2, (50, 30, 10))

        # Castle is drawn last so it occludes anything launched from behind it.
        for dx, dy, kind in self.castle_pixels:
            x, y = self.castle_x + dx, self.castle_y + dy
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue
            base = _CASTLE_COLORS[kind]
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


def render_castle_fireworks(matrix, duration=12.0, fps=30, rng=None):
    """Animate the castle fireworks scene on the matrix for `duration` seconds."""
    show = FireworksShow(matrix.width, matrix.height, rng)
    canvas = matrix.CreateFrameCanvas()
    frame_time = 1.0 / fps
    frames = int(duration * fps)
    font = loaded_fonts.get("title")
    layout = title_layout(font, matrix.width, matrix.height) if font else []
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
        canvas = matrix.SwapOnVSync(canvas)
        remaining = frame_time - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)
    matrix.Clear()
