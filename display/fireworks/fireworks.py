import math
import random
import time

from driver import graphics
from display.animation import frame_canvas, present
from display.display import get_text_width, loaded_fonts
from utils import debug
from display.motion import smooth
from display.fireworks.fireworks_art import (  # noqa: F401  (re-exported: music_show, the countdown, the castle landmark and tests import them here)
    BAT_RGB, CANE_RED, CANE_WHITE, CAP_RGB, FACE_RGB, FLAKE_RGB, FLAKE_TIP_RGB,
    GREEN_ORNAMENT_FILL_RGB, GREEN_ORNAMENT_RGB, MOON_RGB, ORNAMENT_FILL_RGB, ORNAMENT_RGB,
    PUMPKIN_FILL_RGB, PUMPKIN_RGB, SHINE_RGB, SNOW_RGB, STAR_FILL_RGB, STAR_RGB, STEM_RGB,
    TREE_FILL_RGB, TREE_LIGHTS, TREE_RGB, TRUNK_RGB, castle_sprite, _BIG_CASTLE_ROW_PATCH,
    _CANE_HOOK_R, _CANE_X, _CASTLE_ART, _CASTLE_COLORS, _LIT_KINDS, _MAIN_WALL_COLS,
    _MICKEY_CIRCLES, _MICKEY_HALF_WIDTH, _MICKEY_PLACED, _MICKEY_TOP, _NOSE_BRIGHT, _NOSE_DIM,
    _REINDEER, _REINS_ROW, _RUDOLPH, _SANTA_SLEIGH, _SHAPE_POINTS, _SHAPE_RGB, _SHAPE_TILTS,
    _SHAPE_TURNS, _SLEIGH_ART_BIG, _SLEIGH_ART_SMALL, _SLEIGH_COLORS, _STAR_CORNERS,
    _TREE_TIERS, _candy_cane_points, _green_ornament_points, _inside, _line, _mickey_fill,
    _mickey_ornament_points, _mickey_outline, _mickey_pumpkin_points, _outlined, _pumpkin_face,
    _shape_points, _sleigh_team, _snowflake_points, _star_points, _tree_points,
)

# The full name is too wide for one line on a 64-px board, even in 4x6.
TITLE_LINES = ("Lightning Lane", "LED")
TITLE_RGB = (255, 215, 0)
TITLE_DELAY_S = 0.5
TITLE_FADE_S = 1.5
_OUTLINE_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]

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
        # 22% in all (the everyday show's Mickeys are 15%); ornaments take turns red and green.
        "shapes": {"mickey_ornament": 0.06, "candy_cane": 0.05, "snowflake": 0.04, "tree": 0.04, "star": 0.03},
    },
}

GRAVITY = 0.035
DRAG = 0.965

MICKEY_CHANCE = 0.15
MICKEY_LIFE = 55


class _Rocket:
    __slots__ = ("x", "y", "vx", "vy", "burst_y", "color", "mickey", "shape", "tilt")

    def __init__(self, x, y, vx, vy, burst_y, color, mickey=False, shape=None, tilt=0):  # noqa: PLR0913
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.burst_y = burst_y
        self.color = color
        self.mickey = mickey
        self.shape = shape  # a party burst shape (a key of _SHAPE_POINTS), or None
        self.tilt = tilt  # degrees clockwise the shape bursts at (a candy cane's; see _SHAPE_TILTS)


class _Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "gravity", "hold")

    def __init__(self, x, y, vx, vy, life, color, gravity=GRAVITY, hold=1.0):  # noqa: PLR0913
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color
        self.gravity = gravity
        self.hold = hold  # >1 keeps a spark bright longer before it fades (shape bursts)


def _plotter(out, width, height):
    """A put(x, y, rgb) that lights a pixel of `out`, keeping the brighter channels where two meet."""
    def put(x, y, rgb):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < width and 0 <= yi < height:
            prev = out.get((xi, yi))
            if prev:
                rgb = tuple(max(a, b) for a, b in zip(prev, rgb))
            out[(xi, yi)] = rgb

    return put


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
        self.turns = {}  # shape -> whether its turn-taking partner (_SHAPE_TURNS) goes next

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
        if shape in _SHAPE_TURNS:  # red ornament, then green, then red...
            partner_next = self.turns.get(shape, False)
            self.turns[shape] = not partner_next
            shape = _SHAPE_TURNS[shape] if partner_next else shape
        if shape:
            # Keep the whole shape on the board.
            mickey = shape == "mickey"
            radius = self.mickey_radius if mickey else self.shape_radius
            tilt = rng.choice(_SHAPE_TILTS[shape]) if shape in _SHAPE_TILTS else 0
            if shape in _MICKEY_PLACED:
                half_w = _MICKEY_HALF_WIDTH * radius + 1
                up, down = _MICKEY_TOP, 1.0
                x = rng.uniform(half_w, self.width - half_w)
            else:
                points = _shape_points(shape, radius, tilt)
                left, right = -min(p[0] for p in points), max(p[0] for p in points)
                up, down = -min(p[1] for p in points), max(p[1] for p in points)
                x = rng.uniform(left * radius + 1, self.width - right * radius - 1)
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
        self._launch_when_due()
        self._advance_rockets()
        self._advance_sparks()
        self.flash = [f * 0.85 for f in self.flash]
        self.frame += 1
        if self.bats_on:
            self._advance_bats()
        self._advance_snow()
        if self.sleigh_on:
            self._advance_sleighs()

    def _launch_when_due(self):
        if self.frames_to_next_launch <= 0:
            self.launch()
            if self.rng.random() < 0.3:
                self.launch()
            self.frames_to_next_launch = self.rng.randint(*self.launch_gap)
        self.frames_to_next_launch -= 1

    def _advance_rockets(self):
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

    def _advance_sparks(self):
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

    def _advance_bats(self):
        for bat in self.bats:
            bat[0] += bat[2]
        self.bats = [b for b in self.bats if -4 <= b[0] <= self.width + 3]
        if len(self.bats) < 3 and self.rng.random() < 0.012:
            self._add_bat(self.rng.random() < 0.5, self.rng.uniform(2, max(3, self.castle_y * 0.6)))

    def _advance_snow(self):
        for flake in self.snow:
            flake[1] += flake[2]
            if flake[1] >= self.height:  # off the bottom: back to the top somewhere new
                flake[0], flake[1] = self.rng.uniform(0, self.width), 0.0

    def _advance_sleighs(self):
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
        put = _plotter(out, self.width, self.height)
        self._draw_stars(put)
        self._draw_snow(put)
        self._draw_sparks(put)
        self._draw_rockets(put)
        self._draw_bats(out)
        self._draw_sleighs(out)
        self._draw_castle(out)
        return out

    def _draw_stars(self, put):
        for sx, sy in self.stars:
            twinkle = 25 + int(25 * self.rng.random())
            put(sx, sy, (twinkle, twinkle, twinkle + 10))

    def _draw_snow(self, put):
        for fx, fy, _, phase in self.snow:
            put(fx + math.sin(self.frame * 0.05 + phase), fy, SNOW_RGB)

    def _draw_sparks(self, put):
        for s in self.sparks:
            f = min(1.0, s.life / s.max_life * s.hold)
            # Fresh sparks run white-hot, then settle into their color and fade (a held spark only
            # stays bright longer; its white flash is as quick as anyone's).
            hot = max(0.0, (s.life / s.max_life - 0.8) / 0.2)
            rgb = tuple(int((c + (255 - c) * hot) * f) for c in s.color)
            put(s.x, s.y, rgb)
            if f > 0.5:
                put(s.x - s.vx * 1.5, s.y - s.vy * 1.5, tuple(int(c * f * 0.35) for c in s.color))

    def _draw_rockets(self, put):
        for r in self.rockets:
            put(r.x, r.y, (255, 230, 180))
            put(r.x, r.y + 1, (140, 90, 40))
            put(r.x, r.y + 2, (50, 30, 10))

    def _draw_bats(self, out):
        # Bats are silhouettes: drawn over the sky, moon and sparks rather than blended.
        for bat in self.bats:
            for x, y in self._bat_pixels(bat):
                if 0 <= x < self.width and 0 <= y < self.height:
                    out[(x, y)] = BAT_RGB

    def _draw_sleighs(self, out):
        # Santa's sleigh is opaque like the bats: over the sky and sparks, under the castle.
        for sleigh in self.sleighs:
            for x, y, rgb in self._sleigh_pixels(sleigh):
                if 0 <= x < self.width and 0 <= y < self.height:
                    out[(x, y)] = rgb

    def _draw_castle(self, out):
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
