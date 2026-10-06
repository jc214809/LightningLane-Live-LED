import math
import random

from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS
from display.motion import ease_out, progress, smooth
from display.pixels import put


# Solid blades, no white core: at this size a core reads as a third, thinner line. Each
# hums between two shades, a frame at a time.
BLADES = {"red": ((255, 25, 15), (215, 15, 10)), "blue": ((20, 110, 255), (10, 80, 225)),
          "green": ((40, 255, 30), (20, 210, 15)), "yellow": ((255, 235, 20), (225, 195, 10))}
SPARKS = ((255, 255, 255), (255, 230, 90), (255, 190, 40))  # white-hot, yellow, cooling


def throw_sparks(rng, waves, count, scale):
    """[(t0, x, y, vx, vy, life)]: `count` flecks per (t0, x, y) wave, flying from (x, y) at t0 (px/s, s)."""
    flecks = []
    for t0, x, y in waves:
        for _ in range(count):
            angle = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(14, 38) * scale
            flecks.append((t0, x, y, math.cos(angle) * speed, math.sin(angle) * speed - 8 * scale,
                           rng.uniform(0.25, 0.45)))
    return flecks


def spark_pixels(pixels, flecks, t, scale, width, height):
    """Add the flecks in flight at t to pixels, white-hot cooling to orange as they fall."""
    gravity = 60 * scale
    for t0, x0, y0, vx, vy, life in flecks:
        age = t - t0
        if not 0 <= age < life:
            continue
        x = int(round(x0 + vx * age))
        y = int(round(y0 + vy * age + gravity * age * age / 2))
        put(pixels, x, y, SPARKS[min(2, int(3 * age / life))], width, height)


def burst_pixels(pixels, x, y, frame, r, width, height):
    """Add the flickering star where two blades meet: arms r or r + 1 long, alternate frames."""
    r += frame % 2
    x, y = int(round(x)), int(round(y))
    core = SPARKS[frame % 2]
    for k in range(-r, r + 1):
        put(pixels, x + k, y, core, width, height)
        put(pixels, x, y + k, core, width, height)
    if frame % 3 == 0:
        for k in (-r + 1, r - 1):
            put(pixels, x + k, y + k, SPARKS[0], width, height)
            put(pixels, x + k, y - k, SPARKS[0], width, height)


class SaberClashReveal(CapturesScreens):
    """
    Two lightsaber blades, no hilts or wielders: red swings in from the bottom-left corner
    and blue from the bottom-right, each pivoting about a point just off the board, and they
    lock in an X at the centre of the old ride screen. They grind there, shivering, while
    sparks burst from the crossing. Then they unlock, swing upright together, and sweep
    apart to the edges, red left and blue right, the new ride opening between them, the way
    the TRON cycles' trails are their wipe.

    Only on the Star Wars rides (disney.RIDE_VISITORS), never in the random rotation. The old
    screen stays up until the blades sweep it away, so it opts into wants_prev.
    """

    wants_prev = True
    SWING_S, CLASH_S, UNLOCK_S, SPREAD_S = 0.45, 0.75, 0.25, 0.5
    duration = SWING_S + CLASH_S + UNLOCK_S + SPREAD_S
    PIVOT_OUT = 4  # how far off the board, past each bottom corner, the blades pivot

    BLADES, SPARKS = BLADES, SPARKS
    JITTER = 0.025  # radians either way the locked blades shiver
    WAVES = (0.0, 0.3)  # seconds into the clash that each burst of sparks flies

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.prev_px = {}
        self.tall = height >= 64
        self.blade_w = 3 if self.tall else 2
        self.cx, self.cy = (width - 1) / 2, (height - 1) / 2
        out = self.PIVOT_OUT
        self.pivots = {"red": (-out, height - 1 + out), "blue": (width - 1 + out, height - 1 + out)}
        # Each pivot aims at the opposite top corner (as far off the board), so the two
        # mirror-image blades cross at the centre.
        reach = (width - 1 + 2 * out, -(height - 1 + 2 * out))
        self.locked = {"red": math.atan2(reach[1], reach[0]), "blue": math.atan2(reach[1], -reach[0])}
        self.sparks = throw_sparks(self.rng, [(t0, self.cx, self.cy) for t0 in self.WAVES],
                                   16 if self.tall else 10, height / 32)

    def blades(self, t):
        """{name: (x, y, angle)}: each blade as a line through (x, y) at `angle` (y down)."""
        up = -math.pi / 2
        if t < self.SWING_S:
            # Accelerating in, so they hit hard.
            p = progress(t, 0, self.SWING_S) ** 2
            return {name: (*self.pivots[name], up + p * (self.locked[name] - up)) for name in self.pivots}
        t -= self.SWING_S
        if t < self.CLASH_S:
            shiver = self.JITTER if int(t * FPS) // 2 % 2 else -self.JITTER
            return {"red": (self.cx, self.cy, self.locked["red"] + shiver),
                    "blue": (self.cx, self.cy, self.locked["blue"] - shiver)}
        t -= self.CLASH_S
        # Upright, they stand side by side rather than one over the other.
        side = self.blade_w / 2
        if t < self.UNLOCK_S:
            p = smooth(progress(t, 0, self.UNLOCK_S))
            return {name: (self.cx + sign * p * side, self.cy, self.locked[name] + p * (up - self.locked[name]))
                    for name, sign in (("red", -1), ("blue", 1))}
        p = ease_out(progress(t - self.UNLOCK_S, 0, self.SPREAD_S))
        off = self.cx + self.blade_w + 1
        return {"red": (self.cx - side - p * off, self.cy, up), "blue": (self.cx + side + p * off, self.cy, up)}

    def gap(self, t):
        """(left, right): the columns strictly between the blades show the new ride; none before they spread."""
        if t < self.SWING_S + self.CLASH_S + self.UNLOCK_S:
            return None
        b = self.blades(t)
        return b["red"][0], b["blue"][0]

    def _blade_pixels(self, x0, y0, angle, rgb):
        """A solid line blade_w thick through (x0, y0), drawn along whichever axis it runs more of."""
        dx, dy = math.cos(angle), math.sin(angle)
        pixels = {}
        lo = -(self.blade_w // 2)
        if abs(dy) >= abs(dx):
            for y in range(self.height):
                x = int(round(x0 + (y - y0) * dx / dy))
                for k in range(lo, lo + self.blade_w):
                    put(pixels, x + k, y, rgb, self.width, self.height)
        else:
            for x in range(self.width):
                y = int(round(y0 + (x - x0) * dy / dx))
                for k in range(lo, lo + self.blade_w):
                    put(pixels, x, y + k, rgb, self.width, self.height)
        return pixels

    def _spark_pixels(self, since):
        """The burst at the crossing and its flying flecks, `since` seconds into the clash."""
        pixels = {}
        if since < self.CLASH_S:
            burst_pixels(pixels, self.cx, self.cy, int(since * FPS), 2 if self.tall else 1, self.width, self.height)
        spark_pixels(pixels, self.sparks, since, self.height / 32, self.width, self.height)
        return pixels

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        gap = self.gap(t)
        # The old screen, every pixel of it, black included, except between the spread blades:
        # show_screen has already drawn the new screen underneath.
        frame = {}
        for x in range(self.width):
            if gap and gap[0] < x < gap[1]:
                continue
            for y in range(self.height):
                frame[(x, y)] = self.prev_px.get((x, y), (0, 0, 0))
        shade = int(t * FPS) % 2
        for name, (x, y, angle) in self.blades(t).items():
            frame.update(self._blade_pixels(x, y, angle, self.BLADES[name][shade]))
        since = t - self.SWING_S
        if since >= 0:
            frame.update(self._spark_pixels(since))
        for (x, y), rgb in frame.items():
            canvas.SetPixel(x, y, *rgb)
        return True
