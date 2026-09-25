"""Short animated landmark scenes shown before each park's title screen."""

import math
import random

from display.fireworks.fireworks import castle_sprite, _CASTLE_COLORS

LANDMARK_S = 3.0
SKY_RGB = (4, 6, 22)


class Landmark:
    """Precomputes a static scene once; frame(t) returns {(x, y): rgb} for time t."""

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.base = {}
        self.stars = [(self.rng.randrange(width), self.rng.randrange(height), self.rng.uniform(0, 2 * math.pi))
                      for _ in range(width // 4)]
        self.build()

    def build(self):
        raise NotImplementedError

    def put(self, out, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            out[(x, y)] = rgb

    def draw_stars(self, out, t):
        for x, y, phase in self.stars:
            level = 20 + int(25 * (1 + math.sin(t * 3 + phase)))
            out.setdefault((x, y), (level, level, level + 10))

    def frame(self, t):
        out = {}
        self.draw_stars(out, t)
        out.update(self.base)
        self.animate(out, t)
        return out

    def animate(self, out, t):
        pass


class CastleLandmark(Landmark):
    """The castle under a starry sky, with a shooting star crossing overhead."""

    def build(self):
        pixels, w, h = castle_sprite(self.height)
        x0, y0 = (self.width - w) // 2, self.height - h
        for dx, dy, kind in pixels:
            self.put(self.base, x0 + dx, y0 + dy, _CASTLE_COLORS[kind])
        self.sky_bottom = y0

    def animate(self, out, t):
        p = (t % LANDMARK_S) / 1.4
        if p > 1:
            return
        # A shooting star from upper right to lower left above the spires, with a fading tail.
        for i in range(6 * self.scale):
            q = p - i * 0.02
            if q < 0:
                continue
            x = int(self.width * (0.95 - 0.8 * q))
            y = int(self.height * 0.05 + self.sky_bottom * 0.5 * q)
            f = 1 - i / (6 * self.scale)
            self.put(out, x, y, (int(255 * f), int(250 * f), int(200 * f)))


class SpaceshipEarthLandmark(Landmark):
    """EPCOT's geodesic sphere on its legs, with a glint sweeping across the panels."""

    LEG_ROWS = 2.4

    def build(self):
        s = self.scale
        self.r = 10 * s
        leg_h = round(self.LEG_ROWS * s)
        self.cx, self.cy = self.width // 2, self.height - leg_h - self.r - 1
        self.sphere = []
        for y in range(self.cy - self.r, self.cy + self.r + 1):
            for x in range(self.cx - self.r, self.cx + self.r + 1):
                dx, dy = x - self.cx, y - self.cy
                if dx * dx + dy * dy > self.r * self.r:
                    continue
                # Alternating triangular facets, darker toward the lower right like a lit sphere.
                facet = ((x // (2 * s)) + (y // (2 * s)) + ((x + y) // (3 * s))) % 2
                shade = 0.55 + 0.45 * (1 - (dx + dy) / (2 * self.r))
                base = 150 if facet else 110
                rgb = tuple(min(255, int(c * shade)) for c in (base, base + 10, base + 25))
                self.base[(x, y)] = rgb
                self.sphere.append((x, y))
        self._build_legs(leg_h)

    def _build_legs(self, leg_h):
        s, r = self.scale, self.r
        top = self.cy + r - s
        # Support ring the sphere rests on.
        ring = (150, 150, 160)
        for y in range(top, top + s):
            for x in range(self.cx - r // 2, self.cx + r // 2 + 1):
                self.put(self.base, x, y, ring)
        # Three visible legs: the front pair seen head-on in the middle, and the side
        # legs splaying outward to the ground. Each widens toward its base.
        legs = [(-0.35, -0.8, 1.5), (0.0, 0.0, 2.0), (0.35, 0.8, 1.5)]
        for x_top, x_bottom, width in legs:
            for i, y in enumerate(range(top + s, self.height)):
                p = i / max(1, self.height - top - s - 1)
                center = self.cx + r * (x_top + (x_bottom - x_top) * p)
                half = width * s * (0.6 + 0.4 * p)
                for x in range(int(round(center - half)), int(round(center + half)) + 1):
                    lit = x < center
                    self.put(self.base, x, y, (215, 215, 222) if lit else (165, 165, 175))

    def animate(self, out, t):
        # A diagonal band of light sweeps across the sphere every cycle.
        span = 4 * self.r
        band = -2 * self.r + (t % 2.0) / 2.0 * span
        for x, y in self.sphere:
            d = (x - self.cx) + (y - self.cy) - band
            if -2 * self.scale <= d <= 2 * self.scale:
                r, g, b = out[(x, y)]
                boost = 1 - abs(d) / (2 * self.scale + 1)
                out[(x, y)] = (min(255, r + int(120 * boost)), min(255, g + int(120 * boost)), min(255, b + int(90 * boost)))


class TowerOfTerrorLandmark(Landmark):
    """The Hollywood Tower Hotel at night: flickering windows and a lightning strike."""

    STRIKE_AT = 1.3

    # '.' sky, Y gold wall, L light trim, B window, U blue window, V sign haze, T sign lettering,
    # O dome, N door.
    ART = [
        "...................OOO....",
        "..................OOOOO...",
        ".................LYYYYYL..",
        ".....LLLLLLLLLLL.YBYBYBY..",
        ".....YVVVVVVVVVYYYYYYYYY..",
        ".....YVTTTTTTTVYYYBYBYBY..",
        ".....YVVVVVVVVVYYYYYYYYY..",
        ".....YVVTTTTTVVYBYBYBYBY..",
        ".....YVVVVVVVVVYBYYYYYYY..",
        ".....YVVVVVTTVVYBYBYBYBY..",
        ".....YYYYYYYYYYYBYYYYYYY..",
        ".....YUUYYUUYYYYBYUUUUUY..",
        ".....YUUYYUUYYYYBYUUUUUY..",
        ".....YYYYYYYYYYYBYYYYYYY..",
        ".....YYYBYYYYBYYYYYYYYYY..",
        "..LLLLLLLLLLLLLLLLLLLLL...",
        "..YYYYOOOYYYYYYYLLLLLYY...",
        "..YYYYYYYYYYYYYYYYYYYYYY..",
        "..YYYYYYYYYYYYYYYBYBYBYY..",
        "..YBYYBYBYYBYYYYYYYYYYYY..",
        "..YYYYYYYYYYYYYYYBYYBYYY..",
        "..YBYYBYBYYBYYYYYYYYYYYYY.",
        "..YYYYYYYYYYYYYYYBYYBYYYY.",
        "..YBYYBYYYYLLLLYYYYYYYYYYY",
        "LLLLLYYYYYYLYYLYYYBYYYYYLL",
        "YBYBYYBYYYYYNNYYYYYYYYYLYL",
        "YYYYYYYYYYYYNNYYYYYBYYYYYY",
        "YBYBYYBYYYYYNNYYYYYYYYYYBY",
        "YYYYYYYYYYYYNNYYYYYYYYYYYY",
        "YYYYYYYYYYYYNNYYYYYYYYYYYY",
    ]
    COLORS = {
        "Y": (200, 140, 55), "L": (245, 205, 110), "B": (90, 45, 20), "U": (80, 105, 160),
        "V": (120, 95, 140), "T": (245, 245, 245), "O": (190, 130, 45), "N": (120, 70, 30),
    }
    WINDOW = "B"

    def build(self):
        s = self.scale
        self.tw, self.th = len(self.ART[0]) * s, len(self.ART) * s
        self.tx = (self.width - self.tw) // 2
        self.ty = self.height - self.th
        self.windows = []
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                x, y = self.tx + col * s, self.ty + row * s
                if kind == self.WINDOW:
                    self.windows.append((x, y, self.rng.random()))
                for dy in range(s):
                    for dx in range(s):
                        self.put(self.base, x + dx, y + dy, self.COLORS[kind])
        self.bolt = self._bolt()

    def _bolt(self):
        s = self.scale
        x = min(self.tx + self.tw + 3 * s, self.width - 3 * s)
        points = []
        for y in range(0, self.ty + 6 * s):
            if y % (3 * s) == 0:
                x = min(self.width - s, max(self.tx + self.tw, x + self.rng.choice((-1, 1)) * s))
            points.append((x, y))
        return points

    def animate(self, out, t):
        s = self.scale
        for x, y, phase in self.windows:
            # A few rooms are lit, and some of those flicker like the hotel's failing power.
            lit = phase > 0.85 or (phase > 0.7 and math.sin(t * 7 + phase * 40) > 0.2)
            rgb = (255, 235, 160) if lit else self.COLORS[self.WINDOW]
            for dy in range(s):
                for dx in range(s):
                    self.put(out, x + dx, y + dy, rgb)
        since = (t % LANDMARK_S) - self.STRIKE_AT
        if 0 <= since < 0.25:
            # Sky flash, the bolt, and the hotel lit up by it.
            for (x, y), rgb in list(out.items()):
                if rgb[0] < 60 and rgb[1] < 60:
                    out[(x, y)] = (60, 60, 90)
            for (x, y) in list(out):
                if self.tx <= x < self.tx + self.tw and y >= self.ty:
                    r, g, b = out[(x, y)]
                    out[(x, y)] = (min(255, r + 40), min(255, g + 40), min(255, b + 60))
            for x, y in self.bolt:
                for dx in range(s):
                    self.put(out, x + dx, y, (230, 230, 255))


def _noise(x, y):
    """Deterministic 0..1 value per cell, for leafy and carved textures."""
    return (((x * 73856093) ^ (y * 19349663)) & 1023) / 1023


class TreeOfLifeLandmark(Landmark):
    """The Tree of Life: a broad clumped canopy on a flared, carved trunk, with fireflies."""

    CANOPY = [(40, 95, 45), (60, 125, 55), (85, 155, 75), (120, 180, 105)]

    def build(self):
        s = self.scale
        w, h = self.width, self.height
        self.cx = w // 2
        self.trunk_top = int(h * 0.6)
        # Trunk: short and massive, flaring into wide roots at the ground.
        top_half, base_half = w * 0.1, w * 0.27
        for y in range(self.trunk_top, h):
            p = (y - self.trunk_top) / max(1, h - 1 - self.trunk_top)
            half = top_half + (base_half - top_half) * p ** 2.2
            for x in range(int(self.cx - half), int(self.cx + half) + 1):
                twist = int(2 * s * math.sin(y / (3 * s) + x / (5 * s)))
                groove = (x + twist) % (3 * s) == 0
                if p > 0.8 and _noise(x // s, y // s) > 0.55:
                    rgb = (175, 155, 130)  # rocky roots at the base
                elif groove:
                    rgb = (125, 90, 62)
                else:
                    shade = 0.85 + 0.25 * _noise(x // s, y // s)
                    rgb = tuple(min(255, int(c * shade)) for c in (200, 160, 118))
                self.put(self.base, x, y, rgb)
        # Canopy: a wide dome with a bumpy edge; clumps of greens, brighter on top.
        self.canopy_c = (self.cx, int(h * 0.36))
        self.rx, self.ry = w * 0.46, h * 0.3
        cx, cy = self.canopy_c
        for y in range(0, int(cy + self.ry * 1.2) + 1):
            for x in range(w):
                nx, ny = (x - cx) / self.rx, (y - cy) / self.ry
                theta = math.atan2(ny, nx)
                edge = 1 + 0.07 * math.sin(5 * theta) + 0.05 * math.sin(11 * theta + 1)
                if ny > 0.55 - 0.25 * abs(nx):
                    continue  # ragged underside, so the branches show
                if nx * nx + ny * ny > edge * edge:
                    continue
                clump = _noise(x // (2 * s), y // (2 * s))
                level = min(3, max(0, int(clump * 3 + (0.6 - ny) * 1.0)))
                rgb = self.CANOPY[level]
                if _noise(x, y) > 0.93:
                    rgb = (170, 210, 150)
                self.put(self.base, x, y, rgb)
        # Branches from the top of the trunk up into the canopy.
        branch = (105, 75, 50)
        for spread, rise in ((-0.75, 0.22), (-0.4, 0.3), (0.4, 0.3), (0.75, 0.22)):
            x_end, y_end = cx + spread * self.rx, cy + self.ry * rise
            steps = int(abs(x_end - self.cx) + self.trunk_top - y_end) + 1
            for i in range(steps):
                q = i / steps
                x = int(self.cx + (x_end - self.cx) * q)
                y = int(self.trunk_top + (y_end - self.trunk_top) * q)
                for d in range(s):
                    self.put(self.base, x, y + d, branch)
        self.flies = [(self.rng.uniform(0, 2 * math.pi), self.rng.uniform(0.7, 1.25), self.rng.uniform(0, 2 * math.pi))
                      for _ in range(10 * s)]

    def animate(self, out, t):
        cx, cy = self.canopy_c
        for angle, dist, phase in self.flies:
            a = angle + t * 0.4
            x = int(cx + math.cos(a) * self.rx * dist)
            y = int(cy + math.sin(a * 1.3) * self.ry * dist * 1.2)
            level = (1 + math.sin(t * 6 + phase)) / 2
            if level > 0.3:
                self.put(out, x, y, (int(255 * level), int(240 * level), int(90 * level)))


LANDMARKS = {
    "magic kingdom": CastleLandmark,
    "epcot": SpaceshipEarthLandmark,
    "hollywood studios": TowerOfTerrorLandmark,
    "animal kingdom": TreeOfLifeLandmark,
}


def landmark_for(park_name):
    """The landmark scene class for a park, matched loosely on its name, or None."""
    name = (park_name or "").lower()
    for key, cls in LANDMARKS.items():
        if key in name:
            return cls
    return None


def landmark_screen(landmark):
    """Adapt a Landmark to show_screen's draw(canvas, t) contract; it animates for its whole hold."""
    def draw(canvas, t):
        for (x, y), (r, g, b) in landmark.frame(t).items():
            canvas.SetPixel(x, y, r, g, b)
        return True
    return draw
