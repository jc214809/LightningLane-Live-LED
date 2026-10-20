"""Ray the firefly for the synced show (see show_actors.py)."""
import math

from display.fireworks.actors.base import Actor
from display.motion import smooth


class RayGlows(Actor):
    """
    Down in New Orleans into When You Wish Upon a Star: Ray, the firefly from The Princess and the Frog,
    drawn in code (no sprite): a warm yellow-green core (1px, 2x2 on 64x64) in a dim halo, his glow
    pulsing slowly (PULSE_S), with a faint short trail of where he just was. Through the prologue
    (FIRST_S) he flies a lazy figure-eight just right of and below Evangeline, the evening star; when
    the fanfare starts he drifts over to the castle's spire (DRIFT_S) and circles it until his scenes
    end. Everything, the trail included, is placed by the clock, so he leaves nothing behind when off.
    """
    NAME = "Ray"
    FIRST_S = 24.0  # the prologue's length; the fanfare follows
    EIGHT_S = 8.0  # one figure-eight
    DRIFT_S = 4.0  # from the eight over to the spire
    LAP_S = 6.0  # one circle of the spire
    PULSE_S = 2.4  # one slow swell of his glow
    TRAIL = 4  # trail dots...
    TRAIL_GAP_S = 0.09  # ...this far apart in time
    CORE_RGB = (225, 255, 90)
    HALO_RGB = (90, 130, 25)

    def __init__(self, show):
        super().__init__(show)
        self.size = 2 if self.big else 1
        # Where EveningStar (show_effects.py) puts Evangeline.
        self.star = (int(show.width * 0.2), int(show.height * 0.18))
        sx, sy = self.star
        if self.big:
            self.eight_mid, self.eight_r = (sx + 10, sy + 7), (9.0, 5.0)
            self.orbit_r = (11.0, 5.0)
        else:
            self.eight_mid, self.eight_r = (sx + 7, sy + 4), (6.0, 3.0)
            self.orbit_r = (7.0, 3.0)

    def _on_board(self, x, y):
        return (max(1.0, min(x, self.show.width - 1 - self.size)),
                max(1.0, min(y, self.show.height - 1 - self.size)))

    def _eight(self, e):
        a = 2 * math.pi * e / self.EIGHT_S
        (cx, cy), (rx, ry) = self.eight_mid, self.eight_r
        return cx + rx * math.sin(a), cy + ry * math.sin(2 * a)

    def _orbit(self, e):
        a = 2 * math.pi * (e - self.FIRST_S) / self.LAP_S
        (sx, sy), (rx, ry) = self.show.spire, self.orbit_r
        return sx - rx * math.cos(a), sy - ry * math.sin(a)

    def at(self, e):
        """His core's top-left e seconds into his scenes."""
        if e < self.FIRST_S:
            x, y = self._eight(e)
        else:
            k = smooth((e - self.FIRST_S) / self.DRIFT_S)
            ex, ey = self._eight(e)
            ox, oy = self._orbit(e)
            x, y = ex + (ox - ex) * k, ey + (oy - ey) * k
        return self._on_board(x, y)

    def glow(self, e):
        """0.55 (dimmest) to 1 (brightest), swelling slowly."""
        return 0.775 + 0.225 * math.sin(2 * math.pi * e / self.PULSE_S)

    def draw(self, put, out, active):
        if not active:
            return
        show = self.show
        e = self.elapsed()
        g = self.glow(e)

        def add(x, y, rgb):
            if 0 <= x < show.width and 0 <= y < show.height:
                under = out.get((x, y), (0, 0, 0))
                out[(x, y)] = tuple(max(u, c) for u, c in zip(under, rgb))

        for i in range(self.TRAIL, 0, -1):
            tx, ty = (int(round(v)) for v in self.at(max(0.0, e - i * self.TRAIL_GAP_S)))
            f = 0.35 * g * (1 - i / (self.TRAIL + 1))
            add(tx, ty, tuple(int(c * f) for c in self.HALO_RGB))
        x, y = (int(round(v)) for v in self.at(e))
        halo = tuple(int(c * g) for c in self.HALO_RGB)
        n = self.size
        for dx in range(-1, n + 1):
            for dy in range(-1, n + 1):
                if 0 <= dx < n and 0 <= dy < n:
                    continue
                corner = dx in (-1, n) and dy in (-1, n)
                add(x + dx, y + dy, tuple(c // 2 for c in halo) if corner else halo)
        core = tuple(int(c * (0.7 + 0.3 * g)) for c in self.CORE_RGB)
        for dx in range(n):
            for dy in range(n):
                if 0 <= x + dx < show.width and 0 <= y + dy < show.height:
                    out[(x + dx, y + dy)] = core
