"""Comets: bright heads on fading tails, fired in volleys or at a scene's set-moment hits."""
import math

from display.fireworks.effects.base import Effect, _roof_peaks


class _Comets(Effect):
    """Comets: bright heads on fading tails, falling back under gravity; volley() launches some."""
    every_s = (2.5, 4.0)  # seconds between volleys

    def __init__(self, show):
        super().__init__(show)
        self.comets = []  # [x, y, vx, vy, life, max life, rgb, tail [(x, y), ...]]
        self.next_t = None

    def volley(self):
        raise NotImplementedError

    def _comet(self, x, y, vx, vy, rgb, life=40):
        self.comets.append([x, y, vx, vy, life, life, rgb, []])

    def step(self, active):
        t = self.show.t
        if not active:
            self.next_t = None
        elif self.next_t is None or t >= self.next_t:
            self.volley()
            self.next_t = t + self.rng.uniform(*self.every_s)
        for c in self.comets:
            c[7] = ([(c[0], c[1])] + c[7])[: 3 * self.s]
            c[0] += c[2]
            c[1] += c[3]
            c[3] += 0.012 * self.s
            c[4] -= 1
        w, h = self.show.width, self.show.height
        self.comets = [c for c in self.comets if c[4] > 0 and -4 <= c[0] < w + 4 and c[1] < h + 1]

    def draw_behind(self, put, out, active):
        for x, y, _, _, life, max_life, rgb, tail in self.comets:
            f = min(1.0, life / (max_life * 0.4))
            for k, (tx, ty) in enumerate(tail):
                fade = f * (1 - (k + 1) / (len(tail) + 1)) * 0.6
                put(tx, ty, tuple(int(c * fade) for c in rgb))
            put(x, y, tuple(int((c + (255 - c) * 0.5) * f) for c in rgb))


class CometFan(_Comets):
    """Fans of comets fired up from the ground at the castle's foot, spreading outward: the show's
    fan shells (When You Wish's fanfare, Out There, Trashin' the Camp, the finale's mine fan). Colours
    from the scene's palette."""

    def volley(self):
        show = self.show
        cx, n = show.width / 2, 7
        rgb = show._colour()
        speed = (0.75 if self.big else 0.5)
        for i in range(n):
            a = -math.pi / 2 + (i - (n - 1) / 2) * 0.22
            self._comet(cx + (i - (n - 1) / 2) * self.s, show.height - 1.0,
                        math.cos(a) * speed, math.sin(a) * speed, rgb, life=55)


class CrossingComets(_Comets):
    """Pairs of comets from the bottom corners arcing over the spire and crossing there (the
    reprise, and You Can Fly's gold arcs)."""
    every_s = (0.8, 1.4)

    def volley(self):
        show, rng = self.show, self.rng
        sx, sy = show.spire
        rgb = show._colour()
        for side in (-1, 1):
            x0 = sx + side * (show.width * 0.45)
            frames = 34
            vx = (sx - x0) * 2 / frames  # over the spire about halfway, then on across
            vy = -(show.height - sy + 4 * self.s) / (frames * 0.55)
            self._comet(x0, show.height - 1.0, vx * rng.uniform(0.9, 1.1), vy, rgb, life=70)


class HitComets(_Comets):
    """The comets of a scene's set-moment hits (score.Hit), fired by the show at their time rather than
    in volleys: a fan from both side rooftops, or one comet up and across from a side."""
    FAN = 5  # comets per rooftop

    def __init__(self, show):
        super().__init__(show)
        peaks = _roof_peaks(show) or [show.spire]
        self.roofs = (peaks[0], peaks[-1])

    def roof_fan(self, rgb):
        speed = 0.75 if self.big else 0.5
        for side, (x, y) in zip((-1, 1), self.roofs):
            for k in range(self.FAN):
                a = -math.pi / 2 + side * (0.25 + k * 0.2)  # from nearly straight up to well out
                self._comet(x, y - 1.0, math.cos(a) * speed, math.sin(a) * speed, rgb, life=45)

    def comet(self, side, rgb):
        show, away = self.show, (-1 if side == "right" else 1)  # flies across, away from its side
        x = show.width - 1.0 if side == "right" else 0.0  # from the board's edge, clear of the castle
        self._comet(x, show.height - 1.0, away * 0.35 * self.s, -0.75 * self.s, rgb, life=80)
