"""Looks made of drifting, rising or falling bits: sparkles, bubbles, balloons, smoke, fountains,
snow, blocks and waterfalls."""
import math

from display.fireworks.effects.base import GOLD, WHITE, Effect, _door, _Particles, _roof_peaks


class GoldStream(_Particles):
    """A stream of falling gold sparkles sweeping across the sky; red joins the gold halfway."""
    cap = 120

    @property
    def chance(self):
        return 0.9 if self.big else 0.6

    def spawn(self):
        show, rng = self.show, self.rng
        band = (show.t * 8) % (show.width + 20) - 10
        colours = [GOLD, WHITE] + ([(220, 40, 40)] if self.progress() > 0.5 else [])
        return [band + rng.uniform(-6, 6), -1.0, 0.15, rng.uniform(0.3, 0.6) * self.s, 50, 50, rng.choice(colours)]


class GoldBurst(Effect):
    """A burst of gold magic out of the gate over the lower castle as its scene starts (video 1:13, on
    "...unfold"), fading over LIFE frames. Once per run of scenes that keep it."""
    LIFE = 45
    COUNT = 30

    def __init__(self, show):
        super().__init__(show)
        self.door, self.centre = _door(show)
        self.fired = False
        self.sparks = []  # [x, y, vx, vy, life]

    def step(self, active):
        if not active:
            self.fired = False
        elif not self.fired:
            self.fired = True
            cx, cy = self.centre
            for _ in range(self.COUNT * self.s):
                a = self.rng.uniform(math.pi, 2 * math.pi)  # outward and up, over the walls
                v = self.rng.uniform(0.2, 0.7) * self.s
                self.sparks.append([cx, cy, math.cos(a) * v, math.sin(a) * v * 0.6, self.LIFE])
        for p in self.sparks:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.94
            p[3] *= 0.94
            p[4] -= 1
        self.sparks = [p for p in self.sparks if p[4] > 0]

    def draw_front(self, put, out, active):
        for x, y, _, _, life in self.sparks:
            f = life / self.LIFE
            for dx in range(self.s):
                for dy in range(self.s):
                    put(x + dx, y + dy, tuple(int(c * f) for c in (255, 245, 190)))
        if self.sparks:
            f = max(p[4] for p in self.sparks) / self.LIFE
            for xy in self.door:
                put(*xy, tuple(int(c * f) for c in (255, 235, 150)))


class Bubbles(_Particles):
    """Bubbles rising from the bottom (Part of Your World): rings on a 64-row board, dots on 32."""
    cap = 40

    @property
    def chance(self):
        return 0.25 if self.big else 0.15

    def spawn(self):
        rng = self.rng
        return [rng.uniform(1, self.show.width - 2), float(self.show.height), 0.0,
                -rng.uniform(0.15, 0.3) * self.s, 400, 400, (120, 200, 255)]

    def _draw(self, put):
        frame = self.show.frame
        for x, y, _, _, _, _, rgb in self.parts:
            x += 0.5 * math.sin(frame * 0.1 + y)
            if self.big:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(x + dx, y + dy, rgb)
                put(x + 0.6, y - 0.6, WHITE)
            else:
                put(x, y, rgb)


class Balloons(_Particles):
    """Up's balloons in every colour, rising from behind the castle and drifting off the top."""
    front = True
    cap = 40
    COLOURS = ((240, 50, 50), (250, 200, 40), (60, 120, 255), (60, 200, 80), (240, 110, 200), (255, 140, 40))

    @property
    def chance(self):
        return 0.5 if self.big else 0.3

    def spawn(self):
        show, rng = self.show, self.rng
        x = show.width / 2 + rng.uniform(-0.3, 0.3) * show.castle_w
        return [x, show.castle_y + show.castle_h * 0.4, rng.uniform(-0.1, 0.1), -rng.uniform(0.15, 0.3) * self.s,
                400, 400, rng.choice(self.COLOURS)]

    def _draw(self, put):
        frame = self.show.frame
        for x, y, _, _, _, _, rgb in self.parts:
            x += 0.4 * math.sin(frame * 0.07 + y * 0.3)
            for dx in range(self.s):
                for dy in range(self.s):
                    put(x + dx, y + dy, rgb)
            put(x, y + self.s, (90, 90, 90))  # the string


class Smoke(_Particles):
    """Purple and blue lamp smoke curling up from the spire (Friend Like Me)."""
    front = True
    chance = 0.6

    def spawn(self):
        rng = self.rng
        sx, sy = self.show.spire
        life = rng.randint(60, 90)
        return [sx + rng.uniform(-1, 1), sy - 1.0, rng.uniform(-0.12, 0.12), -rng.uniform(0.15, 0.3) * self.s,
                life, life, rng.choice(((150, 90, 220), (90, 120, 255), (200, 120, 255), (230, 170, 60)))]


class GroundFountains(_Particles):
    """A wall of fountains spraying up from the ground all along the board's foot, in the scene's
    colours (the When You Wish interlude's pink fountains across the whole castle)."""
    cap = 260
    chance = 1.0
    COUNT = 7  # fountains across the board

    def step(self, active):
        if active and len(self.parts) < self.cap:
            for _ in range(self.s):  # twice as many on a 64-row board
                self.parts.append(self.spawn())
        super().step(active)
        for p in self.parts:
            p[3] += 0.02 * self.s  # arcs over and falls back

    def spawn(self):
        show, rng = self.show, self.rng
        k = rng.randrange(self.COUNT)
        x = (k + 0.5) * show.width / self.COUNT + rng.uniform(-1, 1)
        life = rng.randint(30, 45)
        return [x, show.height - 1.0, rng.uniform(-0.15, 0.15) * self.s, -rng.uniform(0.7, 1.0) * self.s, life, life,
                show._colour()]

    def _draw(self, put):
        # Bright streaks, 2x2 on a 64-row board like the castle, fading only near the end.
        for x, y, _, _, life, max_life, rgb in self.parts:
            f = min(1.0, 2.0 * life / max_life)
            for dx in range(self.s):
                for dy in range(self.s):
                    put(x + dx, y + dy, tuple(int(c * f) for c in rgb))


class Fountains(_Particles):
    """Gold and white fountains spraying up from the castle's rooftops and showering down over it
    (Friend Like Me's roof fountains)."""
    front = True
    cap = 150
    chance = 1.0

    def __init__(self, show):
        super().__init__(show)
        self.sources = _roof_peaks(show) or [show.spire]

    def step(self, active):
        if active and self.big and len(self.parts) < self.cap:  # twice as many on a 64-row board
            self.parts.append(self.spawn())
        super().step(active)
        for p in self.parts:
            p[3] += 0.03 * self.s  # falls back over the castle

    def spawn(self):
        rng = self.rng
        x, y = rng.choice(self.sources)
        life = rng.randint(25, 40)
        return [x, y - 1.0, rng.uniform(-0.35, 0.35) * self.s, -rng.uniform(0.4, 0.7) * self.s, life, life,
                rng.choice((GOLD, GOLD, WHITE))]


class Snow(_Particles):
    """Olaf's snowflakes floating up past the spires."""
    front = True
    cap = 30
    chance = 0.25

    def spawn(self):
        show, rng = self.show, self.rng
        return [show.castle_x + rng.uniform(0, show.castle_w), float(show.height), rng.uniform(-0.05, 0.05),
                -rng.uniform(0.1, 0.2) * self.s, 300, 300, (220, 235, 255)]


class Blocks(Effect):
    """Toy building blocks in primary colours dropping onto the ground beside the castle
    (You've Got a Friend in Me)."""
    COLOURS = ((230, 40, 40), (40, 90, 230), (250, 210, 40), (40, 190, 70))

    def __init__(self, show):
        super().__init__(show)
        self.blocks = []  # [x, y, vy, life, rgb]
        self.size = 3 if self.big else 2

    def step(self, active):
        show, rng = self.show, self.rng
        if active and len(self.blocks) < 14 and rng.random() < 0.06:
            left = rng.random() < 0.5
            lo, hi = (0, show.castle_x - self.size) if left else (show.castle_x + show.castle_w, show.width - self.size)
            self.blocks.append([float(rng.randint(lo, max(lo, hi))), -float(self.size), 0.5 * self.s, 120,
                                rng.choice(self.COLOURS)])
        ground = show.height - self.size
        for b in self.blocks:
            b[1] = min(ground, b[1] + b[2])
            if b[1] >= ground:
                b[3] -= 1
        self.blocks = [b for b in self.blocks if b[3] > 0]

    def draw_front(self, put, out, active):
        for x, y, _, life, rgb in self.blocks:
            f = min(1.0, life / 30)
            for dy in range(self.size):
                for dx in range(self.size):
                    edge = dx in (0, self.size - 1) and dy in (0, self.size - 1)
                    put(x + dx, y + dy, tuple(int(c * f * (0.7 if edge else 1.0)) for c in rgb))


class Waterfalls(_Particles):
    """Two waterfalls of blue, pink and white either side of the castle (the princess garden)."""
    chance = 0.9
    cap = 120

    def spawn(self):
        show, rng = self.show, self.rng
        source = rng.choice((show.castle_x - 2, show.castle_x + show.castle_w + 1))
        return [source + rng.uniform(-1, 1) * self.s, 0.0, 0.0, rng.uniform(0.5, 0.8) * self.s, 80, 80,
                rng.choice(((140, 200, 255), (255, 160, 210), WHITE))]
