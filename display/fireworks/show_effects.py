"""
Scene looks for the synced show (music_show.py), one class each, turned on by name in a scene's
"effects" in the show's JSON. An effect steps every frame but only starts new things while its
scene is on, so what it left (bubbles, smoke, blocks, the moon) drifts or fades off rather than
vanishing on the cut. Effects draw behind the castle unless they draw in front (draw_front).
"""
import colorsys
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


def _roof_peaks(show):
    """The top of each roof on the board, left to right: the highest roof LED in each run of columns."""
    tops = {}
    for dx, dy, kind in show.castle_pixels:
        if kind == "R" and (dx not in tops or dy < tops[dx]):
            tops[dx] = dy
    peaks = [dx for dx in sorted(tops) if tops.get(dx - 1, 99) >= tops[dx] <= tops.get(dx + 1, 99)]
    return [(show.castle_x + dx, show.castle_y + tops[dx]) for dx in peaks]


# ---- the opening ----

class Searchlights(Effect):
    """Two beams sweeping the sky from either side of the castle, crossing behind it: white and ice
    blue, like the show's opening and closing. The variants below change only the colours."""
    COLOURS = ((235, 240, 255), (130, 170, 255))

    def colours(self):
        return self.COLOURS

    def draw_behind(self, put, out, active):
        if not active:
            return
        show = self.show
        origins = ((show.castle_x - 2, show.height - 1), (show.castle_x + show.castle_w + 1, show.height - 1))
        length = show.height * 1.2
        for i, ((ox, oy), rgb) in enumerate(zip(origins, self.colours())):
            a = -math.pi / 2 + 0.55 * math.sin(show.t * 0.8 + i * math.pi)
            for k in range(int(length)):
                level = 0.85 * (1 - k / length)
                beam = tuple(int(c * level) for c in rgb)
                for w in range(self.s):  # 2 LEDs wide on a 64-row board
                    put(ox + math.cos(a) * k + w, oy + math.sin(a) * k, beam)


class FanfareSearchlights(Searchlights):
    """The theme fanfare's banks of beams: two from each side of the castle, white and ice blue. They
    stand up and sway, lean in to cross over the spire (video 0:17), swing out into a wide fan (0:22)
    and fade before the narrator speaks (0:27-0:28). KEYS are (seconds into the scene, inner beam's
    lean, outer beam's lean) in radians, outward positive, so a negative lean crosses the middle."""
    KEYS = ((0.0, 0.12, 0.3), (5.0, 0.2, 0.38), (6.8, -0.55, -0.62), (9.5, -0.5, -0.58), (11.8, 0.32, 0.48),
            (16.8, 0.3, 0.45))
    FADE = (16.8, 17.8)
    SWAY = 0.06

    def lean(self, e, k):
        """Beam k's (0 inner, 1 outer) lean e seconds into the scene, eased between KEYS."""
        keys = self.KEYS
        if e <= keys[0][0]:
            return keys[0][1 + k]
        for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
            if e < t1:
                f = smooth((e - t0) / (t1 - t0))
                return a[k] + (b[k] - a[k]) * f
        return keys[-1][1 + k]

    def draw_behind(self, put, out, active):
        if not active:
            return
        show = self.show
        e = show.t - (show.cue.start if show.cue else 0.0)
        fade = 1 - smooth((e - self.FADE[0]) / (self.FADE[1] - self.FADE[0]))
        if fade <= 0:
            return
        length = show.height * 1.2
        gap = 3 * self.s
        for side, foot in ((-1, show.castle_x - 2), (1, show.castle_x + show.castle_w + 1)):
            for k, rgb in enumerate(self.COLOURS):
                ox, oy = foot + side * k * gap, show.height - 1
                lean = self.lean(e, k) + self.SWAY * math.sin(e * 1.3 + k * 1.7 + side)
                a = -math.pi / 2 + side * lean
                for j in range(int(length)):
                    level = 0.85 * fade * (1 - j / length)
                    beam = tuple(int(c * level) for c in rgb)
                    for w in range(self.s):  # 2 LEDs wide on a 64-row board
                        put(ox + math.cos(a) * j + w, oy + math.sin(a) * j, beam)


class GoldSearchlights(Searchlights):
    """Yellow and cyan (the theme song's build; gold and white for the reprise)."""
    COLOURS = ((255, 210, 70), (90, 220, 255))


class GreenSearchlights(Searchlights):
    """Green (Trashin' the Camp, and the villains' crossing beams)."""
    COLOURS = ((90, 255, 60), (40, 200, 90))


class TealSearchlights(Searchlights):
    """Turquoise (How Far I'll Go's climax)."""
    COLOURS = ((60, 230, 220), (120, 255, 230))


class PartySearchlights(Searchlights):
    """Nightclub beams cycling through the colours (Genie, the friendship mash-up)."""

    def colours(self):
        hue = self.show.t * 0.25
        return tuple(tuple(int(c * 255) for c in colorsys.hsv_to_rgb((hue + k / 2) % 1.0, 0.8, 1.0)) for k in (0, 1))


class KeyholeGlow(Effect):
    """The castle's doorway glows gold, pulsing (from PULSE of full to full)."""
    COLOUR = GOLD
    PULSE = 0.1

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


class CyanKeyholeGlow(KeyholeGlow):
    """The theme fanfare's doorway: a steadier cyan glow, as the real gate is lit turquoise."""
    COLOUR = (60, 220, 230)
    PULSE = 0.75


class DimKeyholeGlow(CyanKeyholeGlow):
    """The narrator's opening: the same cyan gate at half brightness, waiting for the magic."""
    COLOUR = (30, 110, 115)


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
    """The end of the narrator's opening: the keyhole blazes gold-orange and its magic climbs the castle
    walls, sparkling at its edge, tinting them gold (TINT) up to the top (CLIMB_S) while the roofs stay
    their own blue; it holds, then fades back to the castle's own colours as the singing starts. Timed
    from when it's first turned on, carrying on through the scenes after that keep it."""
    CLIMB_S, HOLD_S, FADE_S = 1.5, 0.8, 1.5
    LIT = (255, 215, 110)
    TINT = 0.45
    BLAZE = (255, 175, 60)

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
            for xy in self.door:
                out[xy] = tuple(int(c * strength) for c in self.BLAZE)
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
                life, life, rng.choice(((150, 90, 220), (90, 120, 255), (200, 120, 255), (230, 170, 60)))]


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


class Savanna(_Level):
    """Can You Feel the Love Tonight's Pride Lands, from FROM of the way through the scene (video 10:25):
    the castle's walls and roofs warm to amber and two black acacia trees stand on its lower walls. Drawn
    only as far as the castle is shown, so it's gone with the castle off."""
    FROM = 0.45
    AMBER = (255, 150, 50)
    ACACIA = ["#######", ".#####.", "...#...", "...#..."]

    def __init__(self, show):
        super().__init__(show)
        self.cells = [(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels
                      if kind in ("W", "R")]
        th = len(self.ACACIA) * self.s
        self.trees = []
        for at in (0.12, 0.70):
            left, top = show.castle_x + int(show.castle_w * at), show.height - th
            self.trees += [(left + col * self.s + ox, top + row * self.s + oy)
                           for row, line in enumerate(self.ACACIA) for col, c in enumerate(line) if c == "#"
                           for oy in range(self.s) for ox in range(self.s)]

    def step(self, active):
        super().step(active and self.progress() >= self.FROM)

    def draw_front(self, put, out, active):
        k = self.level * self.show.castle_level()
        if k <= 0.01:
            return
        warm = 0.8 * k
        for xy in self.cells:
            prev = out.get(xy, (0, 0, 0))
            out[xy] = tuple(int(p + (a - p) * warm) for p, a in zip(prev, self.AMBER))
        for xy in self.trees:
            if xy in out:
                out[xy] = tuple(int(c * (1 - k)) for c in out[xy])


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


EFFECTS = {
    "searchlights": Searchlights,
    "searchlights_fanfare": FanfareSearchlights,
    "searchlights_gold": GoldSearchlights,
    "searchlights_green": GreenSearchlights,
    "searchlights_teal": TealSearchlights,
    "searchlights_party": PartySearchlights,
    "comet_fan": CometFan,
    "crossing_comets": CrossingComets,
    "balloons": Balloons,
    "te_fiti": TeFiti,
    "fountains": Fountains,
    "snow": Snow,
    "flame_jets": FlameJets,
    "keyhole_glow": KeyholeGlow,
    "keyhole_glow_cyan": CyanKeyholeGlow,
    "keyhole_glow_dim": DimKeyholeGlow,
    "keyhole_open": KeyholeOpen,
    "keyhole_magic": KeyholeMagic,
    "gold_trace": GoldTrace,
    "gold_stream": GoldStream,
    "starfield": Starfield,
    "evening_star": EveningStar,
    "bubbles": Bubbles,
    "bells": Bells,
    "water": Water,
    "torches": Torches,
    "stingray": Stingray,
    "smoke": Smoke,
    "blocks": Blocks,
    "moon_rise": MoonRise,
    "waterfalls": Waterfalls,
    "savanna": Savanna,
    "bolts": Bolts,
    "green_fire": GreenFire,
}
