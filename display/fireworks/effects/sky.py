"""Looks in the sky behind the castle: stars, the moon, the stingray and lightning."""

import math

from display.fireworks.effects.base import WHITE, Effect, _Level
from display.motion import smooth


class Starfield(_Level):
    """A sky full of twinkling stars (the narrator, When You Wish, Can You Feel the Love)."""

    def __init__(self, show):
        super().__init__(show)
        rng = self.rng
        self.stars = [
            (
                rng.randrange(show.width),
                rng.randrange(max(1, show.castle_y + show.castle_h // 3)),
                rng.uniform(0, 2 * math.pi),
            )
            for _ in range(show.width // 2)
        ]

    def draw_behind(self, put, out, active):
        if self.level <= 0:
            return
        frame = self.show.frame
        for x, y, phase in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(frame * 0.12 + phase)
            v = int(170 * twinkle * self.level)
            put(x, y, (v, v, min(255, v + 25)))


class EveningStar(_Level):
    """Tiana's evening star: one bright star high on the left, glinting."""

    def draw_behind(self, put, out, active):
        if self.level <= 0:
            return
        show = self.show
        x, y = int(show.width * 0.2), int(show.height * 0.18)
        glint = (0.75 + 0.25 * math.sin(show.t * 4)) * self.level
        put(x, y, tuple(int(c * glint) for c in (255, 245, 210)))
        for k in range(1, 1 + 2 * self.s):
            arm = tuple(int(c * glint * (1 - k / (2 + 2 * self.s))) for c in (255, 220, 140))
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                put(x + dx, y + dy, arm)


class Stingray(_Level):
    """Gramma Tala's glowing stingray: a teal spiral turning in the sky."""

    fade_frames = 90

    def draw_behind(self, put, out, active):
        if self.level <= 0:
            return
        show = self.show
        cx, cy = show.width * 0.5, show.height * 0.28
        n = 16
        for i in range(n):
            a = show.frame * 0.08 + i * 0.45
            r = (1 + i * 0.35) * self.s
            level = self.level * (1 - i / n * 0.7)
            put(cx + math.cos(a) * r * 1.6, cy + math.sin(a) * r * 0.6, tuple(int(c * level) for c in (60, 230, 220)))


class MoonRise(_Level):
    """A full moon rising from behind the castle into the sky (Love Is an Open Door), staying up
    while the scenes keep it and fading after."""

    fade_frames = 90

    def __init__(self, show):
        super().__init__(show)
        self.rise = 0.0

    def step(self, active):
        super().step(active)
        if active:
            self.rise = min(1.0, self.rise + 1 / 450)  # up in 15s

    def draw_behind(self, put, out, active):
        if self.level <= 0:
            return
        show = self.show
        r = 6.0 if self.big else 3.5
        cx = show.width * 0.8
        cy = show.height + r - smooth(self.rise) * (show.height * 0.75 + r)
        rgb = tuple(int(c * self.level) for c in (240, 235, 200))
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    put(x, y, rgb)


class Bolts(Effect):
    """Electric green and purple lightning bolts striking down the sky (the villains attack)."""

    def __init__(self, show):
        super().__init__(show)
        self.bolts = []  # [points, life, rgb]

    def step(self, active):
        show, rng = self.show, self.rng
        if active and rng.random() < 0.04:
            x = rng.uniform(4, show.width - 4)
            bottom = rng.uniform(show.height * 0.3, show.castle_y)
            points, y = [], 0.0
            while y < bottom:
                points.append((x, y))
                y += 1
                x += rng.choice((-1, 0, 0, 1))
            rgb = rng.choice(((57, 255, 20), (180, 60, 255)))
            self.bolts.append([points, 6, rgb])
            for c in range(3):
                show.flash[c] = min(1.0, show.flash[c] + rgb[c] / 255 * 0.5)
        for b in self.bolts:
            b[1] -= 1
        self.bolts = [b for b in self.bolts if b[1] > 0]

    def draw_behind(self, put, out, active):
        for points, life, rgb in self.bolts:
            colour = WHITE if life == 6 else tuple(int(c * life / 5) for c in rgb)
            for x, y in points:
                put(x, y, colour)
                if self.big:
                    put(x + 1, y, colour)
