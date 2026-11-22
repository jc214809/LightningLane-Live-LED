"""Looks that light or dress the castle itself: its gate, outline, finials, torches, flames, and the
water and spiral that cover it."""
import math

from display.fireworks.effects.base import GOLD, Effect, _door, _Level
from display.motion import smooth


class KeyholeGlow(Effect):
    """The castle's doorway glows yellow, shimmering gently (from PULSE of full to full), as the real
    gate glows steadily."""
    COLOUR = (255, 225, 60)
    PULSE = 0.8

    def __init__(self, show):
        super().__init__(show)
        self.door, _ = _door(show)

    def draw_front(self, put, out, active):
        if not active:
            return
        swing = (1 - self.PULSE) / 2
        pulse = 1 - swing + swing * math.sin(self.show.t * 3)
        for x, y in self.door:
            put(x, y, tuple(int(c * pulse) for c in self.COLOUR))


class DimKeyholeGlow(KeyholeGlow):
    """The narrator's opening: the yellow gate at half brightness, waiting for the magic."""
    COLOUR = (128, 112, 30)


class KeyholeOpen(Effect):
    """The finale: the doorway blazes and its gold light spreads out over the whole sky in OPEN_S,
    from when it's first turned on, staying open through the scenes after that keep it."""
    OPEN_S = 12.0

    def __init__(self, show):
        super().__init__(show)
        self.door, (cx, cy) = _door(show)
        self.since = None
        # Every LED by its distance from the door, nearest first, worked out once: the glow walks
        # this list until it passes its edge, so a frame costs only the lit LEDs.
        self.by_distance = sorted((math.hypot(x - cx, y - cy), (x, y))
                                  for y in range(show.height) for x in range(show.width))
        self.shades = [tuple(int(c * 0.6 * k / 32) for c in GOLD) for k in range(33)]

    def opened(self):
        """0..1 of the way open."""
        if self.since is None:
            return 0.0
        return min(1.0, max(0.0, (self.show.t - self.since) / self.OPEN_S))

    def step(self, active):
        if not active:
            self.since = None
        elif self.since is None:
            self.since = self.show.t

    def draw_behind(self, put, out, active):
        if not active:
            return
        if self.since is None:  # drawn before its first step
            self.since = self.show.t
        r = smooth(self.opened()) * self.show.width * 0.9
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


class KeyholeMagic(Effect):
    """The end of the narrator's opening: the keyhole blazes yellow and its magic climbs the castle
    walls, sparkling at its edge, tinting them gold (TINT) up to the top (CLIMB_S) while the roofs stay
    their own blue; it holds, then fades back to the castle's own colours as the singing starts. Timed
    from when it's first turned on, carrying on through the scenes after that keep it."""
    CLIMB_S, HOLD_S, FADE_S = 1.5, 0.8, 1.5
    LIT = (255, 215, 110)
    TINT = 0.45
    BLAZE = (255, 235, 90)

    def __init__(self, show):
        super().__init__(show)
        self.door, _ = _door(show)
        self.bottom = max(y for _, y in self.door)
        self.top = show.castle_y
        # The walls, lowest first, so a frame stops at the climbing edge.
        self.cells = sorted(((show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels
                             if kind == "W"), key=lambda p: -p[1])
        self.since = None
        self.sparkles = []  # [x, y, life]

    def amounts(self):
        """(how far up the castle it has climbed 0..1, how strong the gold is 0..1)."""
        if self.since is None:
            return 0.0, 0.0
        e = self.show.t - self.since
        climbed = smooth(min(1.0, e / self.CLIMB_S))
        fade = (e - self.CLIMB_S - self.HOLD_S) / self.FADE_S
        return climbed, max(0.0, min(1.0, 1 - fade))

    def edge(self, climbed):
        """The row the gold has reached."""
        return self.bottom - (self.bottom - self.top + 1) * climbed

    def step(self, active):
        if not active:
            self.since = None
        elif self.since is None:
            self.since = self.show.t
        climbed, strength = self.amounts()
        if active and 0 < climbed < 1:
            edge = self.edge(climbed)
            near = [c for c in self.cells if abs(c[1] - edge) <= self.s]
            for _ in range(2 * self.s):
                if near:
                    x, y = self.rng.choice(near)
                    self.sparkles.append([x, y, 12])
        for sparkle in self.sparkles:
            sparkle[2] -= 1
        self.sparkles = [sparkle for sparkle in self.sparkles if sparkle[2] > 0]

    def draw_front(self, put, out, active):
        climbed, strength = self.amounts()
        if strength > 0 and climbed > 0:
            edge, k = self.edge(climbed), self.TINT * strength
            for xy in self.cells:
                if xy[1] < edge:
                    break
                prev = out.get(xy, (0, 0, 0))
                out[xy] = tuple(int(p + (g - p) * k) for p, g in zip(prev, self.LIT))
            for xy in self.door:  # blazes, then fades back to whatever lights the gate underneath
                prev = out.get(xy, (0, 0, 0))
                out[xy] = tuple(int(p + (g - p) * strength) for p, g in zip(prev, self.BLAZE))
        for x, y, life in self.sparkles:
            put(x, y, tuple(int(c * life / 12) for c in (255, 250, 220)))


def _outline(show):
    """The castle's outline on the board as one loop, traced clockwise from its bottom-left corner
    (Moore-neighbour tracing over the castle's LEDs)."""
    cells = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, _ in show.castle_pixels}
    start = min(cells, key=lambda p: (-p[1], p[0]))
    ring = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))  # clockwise from west
    path, here, came = [start], start, (start[0] - 1, start[1])
    for _ in range(4 * len(cells)):
        k = ring.index((came[0] - here[0], came[1] - here[1]))
        for i in range(1, 9):
            dx, dy = ring[(k + i) % 8]
            nxt = (here[0] + dx, here[1] + dy)
            if nxt in cells:
                pdx, pdy = ring[(k + i - 1) % 8]
                came, here = (here[0] + pdx, here[1] + pdy), nxt
                break
        if here == start:
            break
        path.append(here)
    return path


class GoldTrace(Effect):
    """The theme chorus: gold magic tracing the castle's design. Bright gold points climb its outline
    from the bottom corners, up each side to the top of the spire every TRACE_S (two a side, half a run
    apart), each leaving a fading gold trail."""
    TRACE_S = 2.5
    PHASES = (0.0, 0.5)  # the points on each side, as fractions of a run
    HEAD = (255, 245, 200)

    def __init__(self, show):
        super().__init__(show)
        path = _outline(show)
        top = min(range(len(path)), key=lambda i: (path[i][1], i))
        bottom_right = max(range(top, len(path)), key=lambda i: (path[i][1], path[i][0]))
        self.sides = (path[:top + 1], path[top:bottom_right + 1][::-1])  # each from the bottom up
        self.trail = 10 * self.s
        self.since = None

    def step(self, active):
        if not active:
            self.since = None
        elif self.since is None:
            self.since = self.show.t

    def heads(self):
        """Each point as (its side, its place along it), or () while it's off."""
        if self.since is None:
            return ()
        run = (self.show.t - self.since) / self.TRACE_S
        return tuple((side, int(((run + phase) % 1.0) * (len(side) - 1)))
                     for side in self.sides for phase in self.PHASES)

    def draw_front(self, put, out, active):
        if not active:
            return
        for side, head in self.heads():
            for k in range(self.trail, 0, -1):
                if head - k >= 0:
                    fade = 1 - k / (self.trail + 1)
                    out[side[head - k]] = tuple(int(c * fade) for c in GOLD)
            out[side[head]] = self.HEAD


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


class TeFiti(_Level):
    """The heart of Te Fiti: a green spiral glowing on the castle's middle as How Far I'll Go
    starts, fading once the scene is under way."""
    fade_frames = 60

    def step(self, active):
        super().step(active and self.progress() < 0.25)

    def draw_front(self, put, out, active):
        if self.level <= 0:
            return
        show = self.show
        cx, cy = show.width / 2, show.castle_y + show.castle_h * 0.35
        pulse = (0.75 + 0.25 * math.sin(show.t * 3)) * self.level
        for i in range(14):
            a = i * 0.7 + show.t * 0.5
            r = (0.3 + i * 0.22) * self.s
            put(cx + math.cos(a) * r, cy + math.sin(a) * r, tuple(int(c * pulse) for c in (40, 255, 90)))


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


class FlameJets(Effect):
    """He's a Pirate's real flame jets: columns of fire bursting up from the castle's ledges and
    either side of its foot, as the scene starts and every few seconds after, lighting the castle."""
    JET_FRAMES = 24

    def __init__(self, show):
        super().__init__(show)
        w, h = show.castle_w, show.castle_h
        ledge = show.castle_y + int(h * 0.55)
        self.spots = [(show.castle_x + int(w * 0.18), ledge), (show.castle_x + int(w * 0.82), ledge),
                      (show.castle_x - 2, show.height - 1), (show.castle_x + w + 1, show.height - 1)]
        self.jets = []  # [x, y, frames left]
        self.next_t = None

    def step(self, active):
        t = self.show.t
        if not active:
            self.next_t = None
        elif self.next_t is None or t >= self.next_t:
            for x, y in self.rng.sample(self.spots, self.rng.choice((2, 4))):
                self.jets.append([x, y, self.JET_FRAMES])
            show = self.show
            show.flash = [min(1.0, f + k) for f, k in zip(show.flash, (0.9, 0.45, 0.1))]
            self.next_t = t + self.rng.uniform(3.0, 6.0)
        for j in self.jets:
            j[2] -= 1
        self.jets = [j for j in self.jets if j[2] > 0]

    def draw_front(self, put, out, active):
        rng = self.rng
        for x, y, left in self.jets:
            f = left / self.JET_FRAMES
            height = int((4 + 3 * f) * self.s * rng.uniform(0.8, 1.0))
            for k in range(height):
                hot = 1 - k / height
                rgb = (255, int(90 + 150 * hot), int(40 * hot))
                for dx in range(self.s):
                    put(x + dx + rng.choice((-1, 0, 0, 1)) * (k > height // 2), y - k,
                        tuple(int(c * (0.4 + 0.6 * f)) for c in rgb))


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
