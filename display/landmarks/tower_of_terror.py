import math
import random

from display.landmarks.scene import Landmark, _noise


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
    # strike, doors and drop get room to breathe in the 3.3s of scene that leaves, with a hold
    # after the car lands. 64x32 is longer again: its camera tilts up to the dome first.
    SCREEN_S = 4.5
    SHORT_SCREEN_S = 5.5
    TOWER_L, TOWER_R = 17, 46
    STRIP_L, STRIP_R = 28, 35
    PAN_S = 1.2
    # Scene times of (strike, doors open, car drops, car lands), without and with the tilt.
    BEATS = {False: (0.6, 1.2, 1.9, 2.5), True: (1.6, 2.2, 2.9, 3.5)}
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

    def __init__(self, width, height, rng=None, park=None):
        self.view_h = height
        self.pans = height < 64
        if self.pans:
            self.SCREEN_S = self.SHORT_SCREEN_S
        self.STRIKE_AT, self.DOORS_AT, self.DROP_AT, self.LAND_AT = self.BEATS[self.pans]
        # The scene is always built 64 tall; frame() shows a window of it on a short board.
        super().__init__(width, 64, rng, park)

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
