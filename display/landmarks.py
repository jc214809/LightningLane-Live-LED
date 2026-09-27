"""Short animated landmark scenes shown before each park's title screen."""

import math
import random

from driver import graphics
from display.display import get_text_width, loaded_fonts
from display.fireworks.fireworks import castle_sprite, _CASTLE_COLORS
from utils.special_events import SPECIAL_EVENTS

LANDMARK_S = 3.0
SKY_RGB = (4, 6, 22)
TITLE_SHADOW_RGB = (10, 2, 18)


class Landmark:
    """Precomputes a static scene once; frame(t) returns {(x, y): rgb} for time t."""

    SCREEN_S = LANDMARK_S  # how long the landmark's screen is held, sweep and wipe included

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

    def title(self, t):
        """Text drawn over the scene in the board's title font: [(text, center_x, top_y, rgb)]."""
        return []


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
    """
    The Hollywood Tower Hotel on a stormy night: salmon stucco, red roofs, slim spired
    corners around a domed cupola, a weathered strip down the middle that is the elevator
    shaft, and trees along the bottom. Lightning forks out of a cloud, the doors at the top
    of the shaft open on a lit car, and it drops.

    Drawn once at 64x64. On a 64x32 board the camera first tilts up from the trees to the
    dome, then the story plays at the top: shrinking the tower lost its windows and spires.
    """

    # Longer than the other landmarks: the sweep and wipe take 1.2s of the screen, and the
    # tilt, strike, doors and drop need the 2.3s of scene that leaves.
    SCREEN_S = 3.5
    TOWER_L, TOWER_R = 17, 46
    STRIP_L, STRIP_R = 28, 35
    PAN_S = 0.8
    # Scene times of (strike, doors open, car drops, car lands), without and with the tilt.
    BEATS = {False: (0.5, 0.9, 1.3, 1.8), True: (1.0, 1.35, 1.6, 2.0)}
    FLASH_S, DOORS_OPEN_S = 0.15, 0.25
    BOLT_RGB, BOLT_EDGE_RGB, CAR_RGB = (235, 235, 255), (170, 170, 230), (255, 235, 180)
    COLORS = {
        "wall": (200, 124, 96), "shade": (150, 88, 70), "lit_wall": (225, 150, 115),
        "strip": (96, 68, 60), "strip_dark": (70, 48, 44),
        "roof": (170, 52, 40), "roof_dark": (120, 34, 28), "spire": (95, 115, 160),
        "win": (45, 26, 26), "win_lit": (255, 200, 110), "arch": (240, 170, 60),
        "tree": (22, 48, 28), "tree_lit": (34, 70, 38),
        "cloud_top": (96, 88, 118), "cloud": (68, 62, 88), "cloud_under": (52, 47, 68),
    }
    # Storm clouds as (centre x, centre y, puffs of (dx, dy, radius)). The first is the one
    # the lightning comes out of.
    CLOUDS = ((9, 5, ((-6, 1, 4), (0, -1, 5), (6, 1, 4), (11, 2, 3))),
              (55, 4, ((-5, 1, 3), (0, 0, 4), (5, 1, 3))),
              (5, 25, ((-3, 0, 3), (2, -1, 3), (6, 0, 2))),
              (58, 21, ((-4, 0, 2), (0, -1, 3), (4, 0, 2))))

    def __init__(self, width, height, rng=None):
        self.view_h = height
        self.pans = height < 64
        self.STRIKE_AT, self.DOORS_AT, self.DROP_AT, self.LAND_AT = self.BEATS[self.pans]
        # The scene is always built 64 tall; frame() shows a window of it on a short board.
        super().__init__(width, 64, rng)

    def build(self):
        c, rect = self.COLORS, self._rect
        # Stormy sky: a purple-gray gradient with soft cloud banks.
        for y in range(self.height):
            for x in range(self.width):
                k = 0.55 + 0.45 * (_noise(x // 5, y // 3) * 0.5 + _noise(x // 9 + 7, y // 5 + 3) * 0.5)
                self.put(self.base, x, y, (int((18 + y * 0.35) * k), int((14 + y * 0.2) * k), int((34 + y * 0.3) * k)))
        self._clouds()
        L, R, SL, SR = self.TOWER_L, self.TOWER_R, self.STRIP_L, self.STRIP_R
        # Lower wings with red roofs.
        rect(L - 9, 46, L - 1, 57, c["shade"])
        rect(R + 1, 42, R + 9, 57, c["shade"])
        for i in range(4):
            rect(L - 9 + i, 45 - i, L - 1, 45 - i, c["roof"])
            rect(R + 1, 41 - i, R + 9 - i, 41 - i, c["roof"])
        rect(L, 12, R, 57, c["wall"])
        rect(SL, 13, SR, 57, c["strip"])
        for y in range(13, 58):
            for x in range(SL, SR + 1):
                if _noise(x, y) > 0.72:
                    self.put(self.base, x, y, c["strip_dark"])
        # Slim corner pillars up past the roof, each with a red cap and a blue spire.
        for x0 in (L, R - 2):
            rect(x0, 6, x0 + 2, 12, c["lit_wall"])
            rect(x0, 5, x0 + 2, 5, c["roof"])
            self.put(self.base, x0 + 1, 4, c["roof"])
            rect(x0 + 1, 1, x0 + 1, 3, c["spire"])
        # Red hipped roofs between the pillars and the cupola.
        for x0, x1 in ((L + 3, SL - 2), (SR + 2, R - 3)):
            rect(x0, 11, x1, 12, c["roof"])
            rect(x0 + 1, 10, x1 - 1, 10, c["roof"])
            rect(x0 + 2, 9, x1 - 2, 9, c["roof_dark"])
        # The domed cupola, with a spire.
        rect(SL, 5, SR, 12, c["wall"])
        for dy, inset in ((4, -1), (3, 0), (2, 1), (1, 2)):
            rect(SL + inset, dy, SR - inset, dy, c["roof"])
        rect(31, 0, 32, 0, c["spire"])
        # The arched window at the top of the shaft: the elevator doors.
        self.doors = (SL + 2, 14, SR - 2, 19)
        rect(SL + 2, 15, SR - 2, 19, c["win"])
        rect(SL + 3, 14, SR - 3, 14, c["win"])
        # Gold-lit arches at the foot of the shaft.
        for x0 in (SL, SL + 3, SL + 6):
            rect(x0, 53, x0 + 1, 57, c["arch"])
            self.put(self.base, x0, 52, c["arch"])
        # Trees along the bottom.
        for x in range(self.width):
            top = 57 + int(3 * _noise(x // 3, 1)) - (2 if (x // 7) % 2 else 0)
            for y in range(top, self.height):
                self.put(self.base, x, y, c["tree_lit"] if _noise(x, y) > 0.6 else c["tree"])
        # Windows: a grid down both sides of the shaft, a few on the wings, two in the cupola.
        self.windows = [(x, y, self.rng.random()) for y in range(15, 54, 3)
                        for x in list(range(L + 3, SL - 1, 2)) + list(range(SR + 2, R - 2, 2))]
        self.windows += [(x, y, self.rng.random()) for y in range(48, 55, 3)
                         for x in list(range(L - 8, L - 1, 2)) + list(range(R + 2, R + 8, 2))]
        self.windows += [(30, 7, 0.95), (33, 7, 0.95)]
        self.bolt = self._bolt()

    def _rect(self, x0, y0, x1, y1, rgb):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(self.base, x, y, rgb)

    def _clouds(self):
        """Each cloud is a cluster of puffs: dark underneath, lighter along its top."""
        self.clouds = []
        for cx, cy, puffs in self.CLOUDS:
            cells = set()
            for dx, dy, r in puffs:
                for y in range(cy + dy - r, cy + dy + r + 1):
                    for x in range(cx + dx - r - 1, cx + dx + r + 2):
                        if ((x - cx - dx) / (r + 1)) ** 2 + ((y - cy - dy) / r) ** 2 <= 1 and y <= cy + 2:
                            cells.add((x, y))
            self.clouds.append(cells)
            for x, y in cells:
                kind = "cloud_top" if (x, y - 1) not in cells else "cloud_under" if (x, y + 1) not in cells else "cloud"
                self.put(self.base, x, y, self.COLORS[kind])

    def _bolt(self):
        """A jagged bolt out of the underside of the first cloud toward the tower's left wall, with a fork."""
        source = self.clouds[0]
        bottom = max(y for _, y in source)
        under = sorted(x for x, y in source if y == bottom)
        x, target_x = under[len(under) // 2], self.TOWER_L - 2
        rng = random.Random(4)
        points, fork = [], None
        for y in range(bottom + 1, 35):
            points.append((x, y))
            if y % 2 == 0:
                x += rng.choice((-1, 0, 1, 1)) if x < target_x else rng.choice((-1, 0))
                points.append((x, y))
            if y == bottom + 8:
                fork = (x, y)
        points += [(fork[0] - (i + 1) // 2, fork[1] + i) for i in range(1, 6)]
        return points

    def draw_stars(self, out, t):
        pass  # storm clouds, no stars

    def frame(self, t):
        out = super().frame(t)
        if not self.pans:
            return out
        # Tilt up: start on the trees, ease to a stop on the dome.
        top = round((self.height - self.view_h) * (1 - min(1.0, t / self.PAN_S)) ** 3)
        return {(x, y - top): rgb for (x, y), rgb in out.items() if top <= y < top + self.view_h}

    def animate(self, out, t):
        c = self.COLORS
        for x, y, phase in self.windows:
            lit = phase > 0.8 or (phase > 0.6 and math.sin(t * 9 + phase * 40) > 0.3)
            for dy in (0, 1):
                self.put(out, x, y + dy, c["win_lit"] if lit else c["win"])
        x0, y0, x1, y1 = self.doors
        if self.DOORS_AT <= t < self.DROP_AT:
            # The doors slide apart from the middle onto the lit car.
            half = (x1 - x0) / 2 * min(1.0, (t - self.DOORS_AT) / self.DOORS_OPEN_S)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if abs(x - (x0 + x1) / 2) <= half + 0.01 and not (y == y0 and x in (x0, x1)):
                        self.put(out, x, y, c["win_lit"])
        elif self.DROP_AT <= t < self.LAND_AT:
            # The car falls, accelerating, down the shaft to the arches, trailing its light.
            p = (t - self.DROP_AT) / (self.LAND_AT - self.DROP_AT)
            car_y = y0 + 1 + int((52 - y0 - 1) * p * p)
            left = (self.STRIP_L + self.STRIP_R + 1) // 2 - 2
            for tail in range(1, 6):
                f = 1 - tail / 6
                if car_y - tail * 2 >= y0:
                    for x in range(left, left + 5):
                        self.put(out, x, car_y - tail * 2, tuple(int(v * f) for v in c["win_lit"]))
            for y in range(car_y, car_y + 4):
                for x in range(left, left + 5):
                    self.put(out, x, y, self.CAR_RGB)
        if 0 <= t - self.STRIKE_AT < self.FLASH_S:
            for p, (r, g, b) in list(out.items()):
                if r < 70 and g < 70:
                    out[p] = (min(255, r + 35), min(255, g + 30), min(255, b + 60))
            # The cloud it comes out of lights up from inside.
            for p in self.clouds[0] & out.keys():  # the cloud runs off the board's edge
                r, g, b = out[p]
                out[p] = (min(255, r + 60), min(255, g + 60), min(255, b + 80))
            for x, y in self.bolt:
                self.put(out, x, y, self.BOLT_RGB)
                self.put(out, x + 1, y, self.BOLT_EDGE_RGB)


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


class ScaryJackOLanternLandmark(Landmark):
    """A scary Mickey-shaped jack-o'-lantern (triangle eyes, toothy grin) under a purple Halloween sky: it sits dark, then its
    candle catches and the carved face flickers, over a drifting green ground mist."""

    IGNITE_AT, IGNITE_S = 0.5, 0.6
    OUTLINE = (70, 24, 4)
    STEM = (60, 120, 40)
    GLOW_HOT, GLOW_EDGE = (255, 245, 170), (255, 205, 60)
    CUT_RIM = (55, 16, 2)
    CARVED_DARK = (22, 8, 2)

    def build(self):
        w, h = self.width, self.height
        self.R, self.cx, self.cy = self._layout()
        ear_r = self.R * 0.56
        ears = [(self.cx + dx * self.R, self.cy - self.R * 1.22, ear_r) for dx in (-0.95, 0.95)]
        self.sky = {}
        for y in range(h):
            p = y / (h - 1)
            rgb = (int(34 - 20 * p), int(6 + 2 * p), int(52 - 22 * p))
            for x in range(w):
                self.sky[(x, y)] = rgb
        self.shell = {}  # (x, y) -> full-brightness pumpkin colour
        for ex, ey, er in ears:
            self._paint_pumpkin(ex, ey, er)
        self._paint_pumpkin(self.cx, self.cy, self.R)
        self._paint_stem()
        self.carved = [(x, y) for x in range(w) for y in range(h) if self._is_carved(x, y)]
        carved = set(self.carved)
        for p in carved:
            self.shell.pop(p, None)
        # A dark cut wall around each carving keeps the glow from bleeding into the orange shell.
        for x, y in self.carved:
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in self.shell and n not in carved:
                    self.shell[n] = self.CUT_RIM
        self.flicker = [(self.rng.uniform(5, 9), self.rng.uniform(11, 17), self.rng.uniform(0, 6.3)) for _ in range(2)]
        self.mist = [(self.rng.uniform(0, w), self.rng.uniform(0.6, 1.4), self.rng.uniform(3, 7))
                     for _ in range(4)]

    def _layout(self):
        """Head radius and centre. Proportions follow the height so the pumpkin fills the board."""
        w, h = self.width, self.height
        r = h * 0.28
        return r, w / 2 - 0.5, h - 0.5 - r - h * 0.06

    def _paint_pumpkin(self, cx, cy, r):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, y - cy)
                if d > r:
                    continue
                if d > r - 1.2:
                    self.shell[(x, y)] = self.OUTLINE
                    continue
                u, v = (x - cx) / r, (y - cy) / r
                # Ribs: vertical grooves that bunch toward the sides like a real pumpkin's.
                angle = math.asin(max(-1.0, min(1.0, u / math.sqrt(max(1e-6, 1 - v * v)))))
                rib = 0.5 + 0.5 * math.cos(angle * 7)
                light = 0.62 + 0.38 * (1 - d / r) + 0.12 * (-u - v) / 2
                k = light * (0.72 + 0.28 * rib)
                self.shell[(x, y)] = (min(255, int(250 * k)), min(255, int(115 * k)), int(10 * k))

    def _paint_stem(self):
        s = self.R / 18
        top = self.cy - self.R
        for i in range(max(3, round(5 * s))):
            y = int(top) - i
            x = int(self.cx + i * 0.35)
            for dx in range(max(2, round(3 * s))):
                self.shell[(x + dx - 1, y)] = self.STEM if dx else (40, 85, 28)

    def _is_carved(self, x, y):
        """Triangle eyes, a triangle nose and a toothy grin, in head-relative coordinates."""
        u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
        for ex in (-0.4, 0.4):
            # Eyes: upward-pointing triangles, apex tilted toward the nose for a sly look.
            if -0.5 <= v <= -0.05:
                q = (v + 0.5) / 0.45
                apex = ex - 0.08 * (1 if ex > 0 else -1) * -1
                if abs(u - (apex + (ex - apex) * q)) <= 0.23 * q:
                    return True
        if 0.02 <= v <= 0.24 and abs(u) <= 0.12 * (v - 0.02) / 0.22:
            return True
        if abs(u) <= 0.66:
            m = 1 - (u / 0.66) ** 2
            top, bottom = 0.3 + 0.16 * m, 0.42 + 0.3 * m
            if top <= v <= bottom:
                if -0.3 <= u <= -0.14 and v <= top + 0.12:
                    return False  # a tooth hanging from the top lip
                if 0.14 <= u <= 0.3 and v >= bottom - 0.12:
                    return False  # a tooth standing on the bottom lip
                return True
        return False

    def frame(self, t):
        out = dict(self.sky)
        self.draw_stars(out, t)
        self.animate(out, t)
        return out

    def draw_stars(self, out, t):
        for x, y, phase in self.stars:
            level = 30 + int(40 * (1 + math.sin(t * 3 + phase)))
            out[(x, y)] = (level + 20, level + 15, level + 40)

    def _lit(self, t):
        """0 while the pumpkin sits dark, easing to 1 as the candle catches."""
        p = (t % LANDMARK_S - self.IGNITE_AT) / self.IGNITE_S
        return 0.0 if p <= 0 else 1.0 if p >= 1 else p * p * (3 - 2 * p)

    def animate(self, out, t):
        self._draw_pumpkin(out, t)
        self._draw_mist(out, t)

    def _draw_pumpkin(self, out, t):
        lit = self._lit(t)
        # Flicker in -1..1. It mostly swells and shrinks the candle's hot spot; brightness only
        # dips a little, so the glow never sinks to the shell's orange.
        flicker = sum(0.5 * math.sin(t * a + ph) * math.sin(t * b) for a, b, ph in self.flicker)
        # The shell warms with the candle but stays well under the glow, so the carved face pops.
        shell_k = 0.3 + 0.52 * lit
        for (x, y), (r, g, b) in self.shell.items():
            out[(x, y)] = (int(r * shell_k), int(g * shell_k), int(b * shell_k))
        glow = lit * (0.94 + 0.06 * flicker)
        reach = self.R * (0.9 + 0.3 * flicker)
        hot_x, hot_y = self.cx, self.cy + self.R * 0.25
        for x, y in self.carved:
            near = max(0.0, 1 - math.hypot(x - hot_x, y - hot_y) / reach)
            base = tuple(e + (hc - e) * near for hc, e in zip(self.GLOW_HOT, self.GLOW_EDGE))
            out[(x, y)] = tuple(min(255, int(d + (c - d) * glow)) for c, d in zip(base, self.CARVED_DARK))

    # Two layers of ground mist: (height as a share of the board, wave number, speed, brightness).
    # The back layer is taller and dimmer and rolls left; the front one is lower and brighter and
    # rolls right, so the tops weave through each other.
    MIST_LAYERS = ((0.2, 0.17, -1.3, 0.4), (0.13, 0.26, 1.7, 0.6))
    MIST_RGB = (60, 150, 80)

    def _draw_mist(self, out, t):
        h, w = self.height, self.width
        for i, (depth, k, speed, strength) in enumerate(self.MIST_LAYERS):
            top_max = depth * h
            phase = self.mist[i][0]
            for x in range(w):
                # Two sine waves at different scales give a rolling, uneven top edge.
                wave = 0.55 + 0.35 * math.sin(k * x + speed * t + phase) \
                    + 0.15 * math.sin(2.3 * k * x - 1.7 * speed * t + 2 * phase)
                top = top_max * wave
                # Brighter and fainter wisps drift along the band, so it swirls rather than sits.
                swirl = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(0.6 * k * x + 1.4 * speed * t + phase + 1))
                for y in range(h - 1, max(-1, h - 2 - int(top)), -1):
                    rise = (h - 1 - y) / max(top, 1e-6)
                    if rise > 1:
                        break
                    a = strength * swirl * (1 - rise) ** 0.7
                    r, g, b = out.get((x, y), (0, 0, 0))
                    mr, mg, mb = self.MIST_RGB
                    out[(x, y)] = (min(255, int(r + mr * a)), min(255, int(g + mg * a)), min(255, int(b + mb * a)))

class FriendlyJackOLanternLandmark(ScaryJackOLanternLandmark):
    """The friendly Mickey pumpkin: ribbed ears and head, pie-cut eyes, an oval nose and an open
    smile with a pink tongue. Once the candle catches it either winks or hops, picked at random
    each showing unless MOTION pins one."""

    MOTIONS = ("wink", "bounce")
    MOTION = None
    GOLD, GHOST, ORANGE = (255, 200, 60), (175, 255, 170), (255, 130, 20)
    # The party's name: two lines over the pumpkin and one under it on 64x64, and a narrow
    # column beside it on 64x32.
    TITLE_TALL = (("MICKEY'S", GOLD), ("NOT-SO-SCARY", GHOST), ("HALLOWEEN PARTY", ORANGE))
    TITLE_SHORT = (("MICKEY'S", GOLD), ("NOT-SO-", GHOST), ("SCARY", GHOST), ("HALLOWEEN", ORANGE), ("PARTY", ORANGE))
    TITLE_ROW_H = 6
    TITLE_COLUMN_X = 18  # centre of the 64x32 text column: HALLOWEEN, the widest line, starts at x=0
    GROOVE = (150, 52, 4)
    TONGUE = (230, 55, 110)
    TONGUE_DARK = (30, 6, 10)
    EYES = (-0.25, 0.25)
    EYE_V, EYE_HW, EYE_HH = -0.38, 0.15, 0.31
    WINK_AT, WINK_S = 1.75, 0.5
    HOP_AT, HOP_S = 1.2, 0.45

    def build(self):
        self.motion = self.MOTION or self.rng.choice(self.MOTIONS)
        super().build()
        tongue = set(p for p in self.carved if self._is_tongue(*p))
        self.tongue = sorted(tongue)
        self.carved = [p for p in self.carved if p not in tongue]
        self.eye_of = {}
        for x, y in self.carved:
            u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
            if v < -0.02:
                self.eye_of[(x, y)] = 0 if u < 0 else 1
        # Uncarved pumpkin under the winking eye and its cut rim, shown as the lid covers them.
        wink = [p for p, e in self.eye_of.items() if e == 1]
        rim = {(x + dx, y + dy) for x, y in wink for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        self.wink_rim = sorted(p for p in rim if p in self.shell and self.shell[p] == self.CUT_RIM)
        self.eye_skin = {p: self._shade(self.cx, self.cy, self.R, *p) for p in wink + self.wink_rim}

    def _shade(self, cx, cy, r, x, y, axis=(0.0, 1.0), grooves=(-1.0, -0.45, 0.45, 1.0)):
        """Pumpkin colour at (x, y): lit toward the upper left, with 1px grooves between the ribs.
        `axis` is the pumpkin's up-down direction, so tilted ears get grooves that follow them."""
        ax, ay = axis
        du, dv = x - cx, y - cy
        along, across = du * ax + dv * ay, du * ay - dv * ax
        d = math.hypot(du, dv)
        half = r * math.sqrt(max(0.0, 1 - (along / r) ** 2))
        light = 0.62 + 0.38 * (1 - d / r) + 0.12 * (-du - dv) / (2 * r)
        if any(abs(across - half * math.sin(g)) < 0.55 for g in grooves):
            base = self.GROOVE
        else:
            base = (250, 115, 10)
        return tuple(min(255, int(c * light)) for c in base)

    def _layout(self):
        """Shrunk to leave room for the title: between its lines on 64x64, to its right on 64x32."""
        if self.height >= 64:
            r = 15.0
            return r, self.width / 2 - 0.5, self.height - 7.5 - r
        r = 9.5
        return r, self.width - 15.5, self.height - 1.5 - r

    def title(self, t):
        lit = self._lit(t)
        if not lit:
            return []
        fade = lambda rgb: tuple(int(c * lit) for c in rgb)
        if self.height >= 64:
            (a, ca), (b, cb), (c, cc) = self.TITLE_TALL
            mid = self.width / 2
            return [(a, mid, 1, fade(ca)), (b, mid, 1 + self.TITLE_ROW_H + 1, fade(cb)),
                    (c, mid, self.height - self.TITLE_ROW_H - 1, fade(cc))]
        return [(text, self.TITLE_COLUMN_X, 1 + i * self.TITLE_ROW_H, fade(rgb)) for i, (text, rgb) in enumerate(self.TITLE_SHORT)]

    def _paint_pumpkin(self, cx, cy, r):
        if r < self.R:
            # An ear: it leans out from the head, with its ribs running along the lean.
            ax, ay = self.cx - cx, self.cy - cy
            n = math.hypot(ax, ay)
            axis, grooves = (ax / n, ay / n), (-0.7, 0.0, 0.7)
        else:
            axis, grooves = (0.0, 1.0), (-1.0, -0.45, 0.45, 1.0)
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, y - cy)
                if d > r:
                    continue
                if d > r - 1.2:
                    self.shell[(x, y)] = self.OUTLINE
                else:
                    self.shell[(x, y)] = self._shade(cx, cy, r, x, y, axis, grooves)

    def _paint_stem(self):
        s = self.R / 18
        top = self.cy - self.R
        for i in range(max(4, round(6 * s))):
            y = int(top) - i
            x = int(self.cx - 1 + i * 0.3)
            for dx in range(max(3, round(4 * s))):
                self.shell[(x + dx - 1, y)] = self.STEM if 0 < dx < 3 else (40, 85, 28)

    def _mouth(self, u, v):
        if abs(u) > 0.6:
            return False
        m = 1 - (u / 0.6) ** 2
        return 0.36 * m <= v <= 0.82 * math.sqrt(m)

    def _is_tongue(self, x, y):
        u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
        return self._mouth(u, v) and abs(u) < 0.36 and v >= 0.56 + 0.12 * (u / 0.3) ** 2

    def _is_carved(self, x, y):
        """Mickey's pie-cut eyes, oval nose and open smile (tongue included), head-relative."""
        u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
        for ex in self.EYES:
            if ((u - ex) / self.EYE_HW) ** 2 + ((v - self.EYE_V) / self.EYE_HH) ** 2 <= 1:
                # The pie cut: a rounded bump of pumpkin rising into the inner bottom of the eye.
                nx = ex - 0.06 * (1 if ex > 0 else -1)
                if ((u - nx) / 0.08) ** 2 + ((v - (self.EYE_V + 0.2)) / 0.15) ** 2 <= 1:
                    return False
                return True
        if (u / 0.26) ** 2 + ((v - 0.1) / 0.12) ** 2 <= 1:
            return True
        return self._mouth(u, v)

    def _winking(self, t):
        """How closed the winking eye is, 0 open to 1 shut."""
        if self.motion != "wink":
            return 0.0
        p = (t % LANDMARK_S - self.WINK_AT) / self.WINK_S
        return math.sin(math.pi * p) ** 0.5 if 0 < p < 1 else 0.0

    def _wink(self, pumpkin, shut, lit):
        """Lower a lid over the right-hand eye; shut tight, it's a happy upturned arc."""
        ecx, ecy = self.cx + self.EYES[1] * self.R, self.cy + self.EYE_V * self.R
        hh, hw = self.EYE_HH * self.R, self.EYE_HW * self.R
        glow = max((pumpkin[p] for p, e in self.eye_of.items() if e == 1), key=sum)
        lid = ecy - hh + 2 * hh * shut
        open_px = {(x, y) for (x, y), e in self.eye_of.items() if e == 1 and y > lid and shut < 0.8}
        skin_k = 0.3 + 0.52 * lit
        for p, rgb in self.eye_skin.items():
            if p in open_px:
                continue
            near_open = any((p[0] + dx, p[1] + dy) in open_px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            pumpkin[p] = self.CUT_RIM if near_open else tuple(int(c * skin_k) for c in rgb)
        if shut >= 0.8:
            for i in range(-round(hw), round(hw) + 1):
                x = round(ecx + i)
                y = round(ecy + hh * 0.45 - 2 * (1 - (i / hw) ** 2))
                pumpkin[(x, y)] = glow
                pumpkin[(x, y + 1)] = self.CUT_RIM

    def _hop(self, t):
        """Rows the pumpkin is lifted: one hop as the candle catches and a smaller rebound."""
        if self.motion != "bounce":
            return 0
        p = (t % LANDMARK_S - self.HOP_AT) / self.HOP_S
        if 0 < p < 1:
            return round(self.R * 0.24 * math.sin(math.pi * p))
        if 1 <= p < 1.6:
            return round(self.R * 0.08 * math.sin(math.pi * (p - 1) / 0.6))
        return 0

    def _draw_pumpkin(self, out, t):
        pumpkin = {}
        super()._draw_pumpkin(pumpkin, t)
        lit = self._lit(t)
        for x, y in self.tongue:
            pumpkin[(x, y)] = tuple(int(d + (c - d) * lit) for c, d in zip(self.TONGUE, self.TONGUE_DARK))
        shut = self._winking(t)
        if shut:
            self._wink(pumpkin, shut, lit)
        lift = self._hop(t)
        for (x, y), rgb in pumpkin.items():
            self.put(out, x, y - lift, rgb)


LANDMARKS = {
    "magic kingdom": CastleLandmark,
    "epcot": SpaceshipEarthLandmark,
    "hollywood studios": TowerOfTerrorLandmark,
    "animal kingdom": TreeOfLifeLandmark,
}


def landmark_for(park_name, party=None):
    """The landmark scene class for a park, matched loosely on its name, or None. A party
    (a SPECIAL_EVENTS key the park is holding today) swaps in that party's own landmark, if it has one."""
    if SPECIAL_EVENTS.get(party, {}).get("landmark"):
        return globals()[SPECIAL_EVENTS[party]["landmark"]]
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
        lines = landmark.title(t)
        if lines:
            font = loaded_fonts["title"]
            shadow = graphics.Color(*TITLE_SHADOW_RGB)
            for text, center_x, top, rgb in lines:
                x = round(center_x - get_text_width(font, text) / 2)
                y = top + font.baseline
                # A one-pixel drop shadow keeps the letters off the sky, the mist and the pumpkin.
                graphics.DrawText(canvas, font, x + 1, y + 1, shadow, text)
                graphics.DrawText(canvas, font, x, y, graphics.Color(*rgb), text)
        return True
    return draw
