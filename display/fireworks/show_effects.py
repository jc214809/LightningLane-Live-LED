"""
Scene looks for the synced show (music_show.py), one class each, turned on by name in a scene's
"effects" in the show's JSON. An effect steps every frame but only starts new things while its
scene is on, so what it left (bubbles, smoke, blocks, the moon) drifts or fades off rather than
vanishing on the cut. Effects draw behind the castle unless they draw in front (draw_front).
"""
import math

from display.motion import smooth

GOLD, WHITE = (255, 210, 90), (255, 255, 255)


class Effect:
    def __init__(self, show):
        self.show = show
        self.rng = show.rng
        self.big = show.height >= 64
        self.s = 2 if self.big else 1  # pixel scale: doubled on 64-row boards, like the castle

    def progress(self):
        cue = self.show.cue
        return cue.progress(self.show.t) if cue else 0.0

    def step(self, active):
        pass

    def draw_behind(self, put, out, active):
        pass

    def draw_front(self, put, out, active):
        pass


class _Level(Effect):
    """An effect that fades in while its scene is on and out after it."""
    fade_frames = 45

    def __init__(self, show):
        super().__init__(show)
        self.level = 0.0

    def step(self, active):
        delta = 1 / self.fade_frames
        self.level = min(1.0, self.level + delta) if active else max(0.0, self.level - delta)


class _Particles(Effect):
    """Particles [x, y, vx, vy, life, max life, rgb]; spawn() makes one, `chance` per frame."""
    chance = 0.5
    cap = 80
    front = False

    def __init__(self, show):
        super().__init__(show)
        self.parts = []

    def spawn(self):
        raise NotImplementedError

    def step(self, active):
        if active and len(self.parts) < self.cap and self.rng.random() < self.chance:
            self.parts.append(self.spawn())
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
        w, h = self.show.width, self.show.height
        self.parts = [p for p in self.parts if p[4] > 0 and -3 <= p[0] < w + 3 and -4 <= p[1] < h + 1]

    def _draw(self, put):
        for x, y, _, _, life, max_life, rgb in self.parts:
            f = life / max_life
            put(x, y, tuple(int(c * f) for c in rgb))

    def draw_behind(self, put, out, active):
        if not self.front:
            self._draw(put)

    def draw_front(self, put, out, active):
        if self.front:
            self._draw(put)


def _door(show):
    """The castle's doorway pixels on the board, and its centre."""
    door = [(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind == "D"]
    cx = sum(x for x, _ in door) / len(door)
    cy = sum(y for _, y in door) / len(door)
    return door, (cx, cy)


# ---- the opening ----

class Searchlights(Effect):
    """Two beams sweeping the sky from either side of the castle: blue and orange (also the
    nightclub lights of Genie's Friend Like Me)."""
    COLOURS = ((120, 160, 255), (255, 160, 60))

    def draw_behind(self, put, out, active):
        if not active:
            return
        show = self.show
        origins = ((show.castle_x - 2, show.height - 1), (show.castle_x + show.castle_w + 1, show.height - 1))
        length = show.height * 1.2
        for i, ((ox, oy), rgb) in enumerate(zip(origins, self.COLOURS)):
            a = -math.pi / 2 + 0.55 * math.sin(show.t * 0.8 + i * math.pi)
            for k in range(int(length)):
                level = 0.85 * (1 - k / length)
                beam = tuple(int(c * level) for c in rgb)
                for w in range(self.s):  # 2 LEDs wide on a 64-row board
                    put(ox + math.cos(a) * k + w, oy + math.sin(a) * k, beam)


class KeyholeGlow(Effect):
    """The castle's doorway glows gold, pulsing."""

    def __init__(self, show):
        super().__init__(show)
        self.door, _ = _door(show)

    def draw_front(self, put, out, active):
        if not active:
            return
        pulse = 0.55 + 0.45 * math.sin(self.show.t * 3)
        for x, y in self.door:
            put(x, y, tuple(int(c * pulse) for c in GOLD))


class KeyholeOpen(Effect):
    """The finale: the doorway blazes and its gold light spreads out over the whole sky."""

    def __init__(self, show):
        super().__init__(show)
        self.door, (cx, cy) = _door(show)
        # Every LED by its distance from the door, nearest first, worked out once: the glow walks
        # this list until it passes its edge, so a frame costs only the lit LEDs.
        self.by_distance = sorted((math.hypot(x - cx, y - cy), (x, y))
                                  for y in range(show.height) for x in range(show.width))
        self.shades = [tuple(int(c * 0.6 * k / 32) for c in GOLD) for k in range(33)]

    def draw_behind(self, put, out, active):
        if not active:
            return
        r = smooth(self.progress()) * self.show.width * 0.9
        shades, get = self.shades, out.get
        for d, spot in self.by_distance:
            if d >= r:
                break
            glow = shades[int(32 * (1 - d / r))]
            prev = get(spot)
            out[spot] = glow if prev is None else (max(prev[0], glow[0]), max(prev[1], glow[1]), max(prev[2], glow[2]))

    def draw_front(self, put, out, active):
        if active:
            for x, y in self.door:
                out[(x, y)] = (255, 240, 200)


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


class Starfield(_Level):
    """A sky full of twinkling stars (the narrator, When You Wish, Can You Feel the Love)."""

    def __init__(self, show):
        super().__init__(show)
        rng = self.rng
        self.stars = [(rng.randrange(show.width), rng.randrange(max(1, show.castle_y + show.castle_h // 3)),
                       rng.uniform(0, 2 * math.pi)) for _ in range(show.width // 2)]

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


# ---- dreams ----

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


class Doves(Effect):
    """White doves flying up and out from the spire (Out There)."""

    def __init__(self, show):
        super().__init__(show)
        self.doves = []  # [x, y, vx, vy, phase]

    def step(self, active):
        rng = self.rng
        if active and len(self.doves) < 8 and rng.random() < 0.05:
            sx, sy = self.show.spire
            side = rng.choice((-1, 1))
            self.doves.append([sx, sy, side * rng.uniform(0.25, 0.5) * self.s, -rng.uniform(0.1, 0.25) * self.s,
                               rng.uniform(0, 2 * math.pi)])
        for d in self.doves:
            d[0] += d[2]
            d[1] += d[3]
        w = self.show.width
        self.doves = [d for d in self.doves if -4 <= d[0] <= w + 4 and d[1] > -4]

    def draw_front(self, put, out, active):
        frame = self.show.frame
        for x, y, _, _, phase in self.doves:
            up = (frame // 4 + int(phase * 10)) % 2 == 0
            tip = -1 if up else 1
            wings = [(0, 0), (-1, tip), (1, tip)]
            if self.big:
                wings += [(-2, tip * 2 if up else tip), (2, tip * 2 if up else tip)]
            for dx, dy in wings:
                put(x + dx, y + dy, (235, 235, 245))


class Bells(Effect):
    """The castle's gold finials ring: flash bright in time, about once a second (Out There)."""

    def __init__(self, show):
        super().__init__(show)
        self.finials = [(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind == "G"]

    def draw_front(self, put, out, active):
        if not active:
            return
        ring = max(0.0, math.sin(self.show.t * 2 * math.pi * 1.1)) ** 4
        bright = tuple(int(c * ring) for c in (255, 245, 190))
        for x, y in self.finials:
            put(x, y, bright)
            put(x, y - 1, tuple(c // 2 for c in bright))


# ---- the journey ----

class Water(Effect):
    """Ocean water over the bottom of the board, in front of the castle. In Touch the Sky it starts
    rising halfway through; once up it stays through the scenes that keep it, and drains after."""

    def __init__(self, show):
        super().__init__(show)
        self.level = 0.0
        self.full = show.height - show.castle_y - show.castle_h * 0.6  # covers the castle's lower 40%

    def step(self, active):
        rising = active and (self.level > 0 or self.progress() >= 0.5)
        delta = 1 / 300  # 10 seconds at 30fps, up or down
        self.level = min(1.0, self.level + delta) if rising else max(0.0, self.level - delta)

    def draw_front(self, put, out, active):
        if self.level <= 0:
            return
        show = self.show
        depth = smooth(self.level) * self.full
        for x in range(show.width):
            surface = show.height - depth + 0.6 * math.sin(x * 0.4 + show.frame * 0.15)
            for y in range(max(0, int(surface)), show.height):
                water = (120, 200, 255) if y == int(surface) else (20, 70, 170)
                prev = out.get((x, y), (0, 0, 0))
                out[(x, y)] = tuple(int(a * 0.35 + b * 0.65) for a, b in zip(prev, water))


class Torches(Effect):
    """Flickering torches on the ground either side of the castle (How Far I'll Go)."""

    def draw_front(self, put, out, active):
        if not active:
            return
        show, rng = self.show, self.rng
        xs = (2, show.castle_x - 3, show.castle_x + show.castle_w + 2, show.width - 3)
        for x in xs:
            flick = rng.uniform(0.7, 1.0)
            for k in range(2 * self.s):
                rgb = (255, 140, 30) if k < self.s else (255, 220, 90)
                for dx in range(self.s):
                    put(x + dx, show.height - 1 - k, tuple(int(c * flick * (1 - k * 0.15)) for c in rgb))


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


# ---- friendship ----

class Smoke(_Particles):
    """Purple and blue lamp smoke curling up from the spire (Friend Like Me)."""
    front = True
    chance = 0.6

    def spawn(self):
        rng = self.rng
        sx, sy = self.show.spire
        life = rng.randint(60, 90)
        return [sx + rng.uniform(-1, 1), sy - 1.0, rng.uniform(-0.12, 0.12), -rng.uniform(0.15, 0.3) * self.s,
                life, life, rng.choice(((150, 90, 220), (90, 120, 255), (200, 120, 255)))]


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


# ---- love ----

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


class Waterfalls(_Particles):
    """Two waterfalls of blue, pink and white either side of the castle (the princess garden)."""
    chance = 0.9
    cap = 120

    def spawn(self):
        show, rng = self.show, self.rng
        source = rng.choice((show.castle_x - 2, show.castle_x + show.castle_w + 1))
        return [source + rng.uniform(-1, 1) * self.s, 0.0, 0.0, rng.uniform(0.5, 0.8) * self.s, 80, 80,
                rng.choice(((140, 200, 255), (255, 160, 210), WHITE))]


# ---- adversity ----

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


class GreenFire(_Level):
    """Maleficent's dragon fire: green flames licking up along the ground, over the castle's base."""

    def draw_front(self, put, out, active):
        if self.level <= 0:
            return
        show = self.show
        top = show.height * 0.3 * self.level
        for x in range(show.width):
            noise = (math.sin(x * 0.7 + show.frame * 0.3) + math.sin(x * 1.9 - show.frame * 0.17)) / 4 + 0.5
            h = top * (0.4 + 0.6 * noise)
            for k in range(int(h)):
                f = 1 - k / h
                rgb = tuple(int(a * f + b * (1 - f)) for a, b in zip((180, 255, 120), (20, 120, 30)))
                put(x, show.height - 1 - k, tuple(int(c * (0.4 + 0.6 * f)) for c in rgb))


EFFECTS = {
    "searchlights": Searchlights,
    "keyhole_glow": KeyholeGlow,
    "keyhole_open": KeyholeOpen,
    "gold_stream": GoldStream,
    "starfield": Starfield,
    "evening_star": EveningStar,
    "bubbles": Bubbles,
    "doves": Doves,
    "bells": Bells,
    "water": Water,
    "torches": Torches,
    "stingray": Stingray,
    "smoke": Smoke,
    "blocks": Blocks,
    "moon_rise": MoonRise,
    "waterfalls": Waterfalls,
    "bolts": Bolts,
    "green_fire": GreenFire,
}
