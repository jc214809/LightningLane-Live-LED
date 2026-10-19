"""
The castle fireworks in time with a show's soundtrack: a copy of fireworks.py's simulation (its own,
so the everyday and party fireworks don't change) driven by a Score (score.py). The clock decides
which scene is on, not the frame count, so a slow board still hits each section with the music.
"""
import colorsys
import math
import random
import time

from display.animation import frame_canvas, present
from display.animation.characters.tink import TinkReveal
from display.fireworks import show_actors, show_effects
from display.fireworks.fireworks import (_CASTLE_COLORS, _MICKEY_CIRCLES, DRAG, GRAVITY, MICKEY_LIFE,
                                         castle_sprite)
from display.motion import ease_out, smooth
from utils import debug, system_stats

# Castle colours by look, over the everyday ones; a scene's "castle" names one. Only the walls (W)
# and roofs (R) change: windows, gold and the door keep theirs.
CASTLE_LOOKS = {
    "blue": {"W": (110, 150, 240), "R": (30, 60, 210)},
    "purple": {"W": (170, 140, 220), "R": (110, 60, 190)},
    "green": {"W": (120, 230, 140), "R": (110, 40, 180)},  # electric green walls, villain-purple roofs
    "fire": {"W": (255, 130, 50), "R": (200, 40, 20)},
    "gold": {"W": (255, 215, 120), "R": (230, 160, 40)},
    "dark": {"W": (60, 40, 45), "R": (40, 20, 35)},
    "jungle": {"W": (90, 170, 80), "R": (40, 110, 40)},
    "pink": {"W": (250, 175, 210), "R": (220, 90, 160)},
    # Gold, its walls tiled in coloured glass (_STAINED_GLASS) as it fades in.
    "stained_glass": {"W": (255, 215, 120), "R": (230, 160, 40)},
    # From watching the real show (docs/shows/happily-ever-after/README.md):
    "grey": {"W": (180, 180, 190), "R": (60, 90, 230)},  # the opening: grey walls, blue spires
    "royal": {"W": (220, 60, 80), "R": (60, 90, 230)},  # the theme song's build: red walls, royal-blue roofs
    "red": {"W": (215, 35, 40), "R": (60, 90, 230)},  # the theme chorus, its design traced in gold, blue roofs
    "pastel": {"W": (210, 170, 245), "R": (90, 210, 215)},  # When You Wish: lavender and turquoise
    "sunset": {"W": (255, 175, 60), "R": (225, 70, 40)},  # Hakuna Matata
    "monsters": {"W": (240, 200, 40), "R": (50, 70, 220)},  # Mike and Sulley: scream-canister yellow, blue roofs
    "friends": {"W": (235, 130, 110), "R": (50, 70, 220)},  # That's What Friends Are For: salmon, blue roofs
    "ice": {"W": (170, 210, 255), "R": (120, 90, 220)},  # Olaf
    "crimson": {"W": (130, 30, 45), "R": (40, 40, 90)},  # the Emperor: crimson on dark navy
    "lavender": {"W": (230, 160, 235), "R": (60, 75, 225)},  # Can You Feel the Love Tonight: pink-lavender, blue roofs
}
_STAINED_GLASS = ((255, 200, 60), (70, 120, 255), (220, 50, 60), (255, 230, 140))
_FLICKERS = {"fire"}
CASTLE_FADE_S = 1.5
# "wipe_down": the scene's castle change runs from the spire down to the base over WIPE_S instead
# (the theme chorus's slow fade to blue): the top row is done halfway through, the bottom row starts then.
WIPE_S = 8.0
# The castle's brightness on each of a scene's stages (score.STAGES): a ghost leaves characters the
# room to stand in front of it; off clears the board for them. It fades between them over CASTLE_FADE_S.
STAGE_LEVELS = {"castle": 1.0, "ghost": 0.25, "off": 0.0}
_LIT_KINDS = {"W", "R"}

# The wishing star lands on the spire this far through its scene; the castle turns after that.
WISH_LANDS_AT = 0.7
WISH_RGB, WISH_GLOW_RGB = (255, 255, 230), (255, 220, 120)
LANTERN_RGB = (255, 150, 40)
EMBER_RGB = (255, 70, 20)
# Gold willows: most bursts in a "willow" scene hang and droop in long-lived gold.
WILLOW_CHANCE = 0.7
WILLOW_RGB = (255, 185, 70)
# "You Can Fly": Tink (her park-title sprite, doubled on 64x64 like there) takes off from the spire
# and arcs up and out to the right in TINK_FLY_S, while the fireworks hold back to TINK_RATE.
TINK_FLY_S = 12.0
TINK_RATE = 0.3
# The frame rate a hit shell's climb is timed at (render_music_show's), so it bursts on its hit.
HIT_FPS = 30


def _unit(points):
    """Scale outline points so the widest reaches 1."""
    reach = max(max(abs(x), abs(y)) for x, y in points)
    return [(x / reach, y / reach) for x, y in points]


def _mickey():
    points = []
    for cx, cy, r in _MICKEY_CIRCLES:
        n = 44 if r == 1.0 else 26
        for i in range(n):
            a = 2 * math.pi * i / n
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            if not any((px - ox) ** 2 + (py - oy) ** 2 < (orr - 0.05) ** 2
                       for ox, oy, orr in _MICKEY_CIRCLES if (ox, oy, orr) != (cx, cy, r)):
                points.append((px, py))
    return _unit(points)


def _heart(n=40):
    points = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        points.append((x, y + 2))  # roughly centred on the burst
    return _unit(points)


def _star(per_edge=5):
    corners = [(math.cos(-math.pi / 2 + i * math.pi / 5) * (1.0 if i % 2 == 0 else 0.45),
                math.sin(-math.pi / 2 + i * math.pi / 5) * (1.0 if i % 2 == 0 else 0.45)) for i in range(10)]
    points = []
    for i in range(10):
        (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 10]
        points += [(x0 + (x1 - x0) * k / per_edge, y0 + (y1 - y0) * k / per_edge) for k in range(per_edge)]
    return points


def _ring(r, n, rgb=None, cx=0.0, cy=0.0, start=0.0, end=2 * math.pi):
    return [(cx + r * math.cos(start + (end - start) * i / n), cy + r * math.sin(start + (end - start) * i / n), rgb)
            for i in range(n)]


def _lion():
    """Hakuna Matata's lion head: a yellow face in a red mane."""
    face = [(x * 0.25, y * 0.25, (255, 200, 60)) for y in range(-2, 3) for x in range(-2, 3) if x * x + y * y <= 5]
    return face + _ring(1.0, 30, (220, 60, 30))


def _smiley():
    yellow = (255, 220, 40)
    return (_ring(1.0, 30, yellow) + [(-0.35, -0.3, yellow), (0.35, -0.3, yellow)]
            + _ring(0.55, 9, yellow, start=math.radians(25), end=math.radians(155)))


def _door():
    """A Monsters, Inc. door: an upright rectangle with a gold knob."""
    edge = [(x / 5 * 0.6, -1.0) for x in range(-5, 6)] + [(x / 5 * 0.6, 1.0) for x in range(-5, 6)]
    edge += [(-0.6, y / 5) for y in range(-4, 5)] + [(0.6, y / 5) for y in range(-4, 5)]
    return [(x, y, None) for x, y in edge] + [(0.35, 0.1, (255, 200, 60))]


def _bullseye():
    return _ring(1.0, 28, (230, 40, 40)) + _ring(0.66, 20, (255, 255, 255)) + _ring(0.33, 10, (230, 40, 40))


def _jellyfish():
    """A dome over four wavy tentacles."""
    dome = _ring(0.8, 14, cy=-0.1, start=math.pi, end=2 * math.pi) + [(x / 4 * 0.8, -0.1, None) for x in range(-4, 5)]
    tentacles = [(x + 0.1 * math.sin(y * 6), y, None) for x in (-0.5, -0.17, 0.17, 0.5) for y in (0.15, 0.4, 0.65, 0.9)]
    return dome + tentacles


# Burst shapes: (x, y, rgb) in units of the shape radius; an rgb of None takes the rocket's colour.
SHAPES = {
    "mickey": [(x, y, None) for x, y in _mickey()],
    "heart": [(x, y, None) for x, y in _heart()],
    "star": [(x, y, None) for x, y in _star()],
    "lion": _lion(),
    "smiley": _smiley(),
    "door": _door(),
    "bullseye": _bullseye(),
    "jellyfish": _jellyfish(),
}
# Effects drawn here; show_effects.py has the rest.
_OWN_EFFECTS = {"wishing_star", "lanterns", "embers", "rainbow", "final_flash", "tink", "willow", "wipe_down"}
EFFECTS = _OWN_EFFECTS | set(show_effects.EFFECTS)


class _Rocket:
    __slots__ = ("x", "y", "vx", "vy", "burst_y", "color", "shape", "style")

    def __init__(self, x, y, vx, vy, burst_y, color, shape=None, style=None):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.burst_y = burst_y
        self.color = color
        self.shape = shape
        self.style = style  # a hit shell's (score.SHELL_STYLES)


class _Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "gravity")

    def __init__(self, x, y, vx, vy, life, color, gravity=GRAVITY):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color
        self.gravity = gravity


class MusicShow:
    """Frame-stepped castle and fireworks that follow the cue set on them; knows nothing about the
    matrix driver or the clock."""

    def __init__(self, width, height, rng=None, lips=None):
        self.width, self.height = width, height
        self.lips = lips or {}  # the score's mouth tracks (score.Lips) by actor, for those who sing
        self.rng = rng or random.Random()
        self.frame = 0
        self.rockets, self.sparks = [], []
        self.lanterns, self.embers = [], []
        self.dust = []  # Tink's pixie dust: [x, y, vx, vy, life, max life, rgb]
        self.flash = [0.0, 0.0, 0.0]
        self._castle_key, self._castle_layer = None, {}  # frame_pixels' finished castle, kept while it holds
        self.white = 0.0
        self.frames_to_next_launch = 0

        self.castle_pixels, cw, ch = castle_sprite(height)
        # A reshaped castle for the frame (an actor's: the castle singing stretches), drawn in its place;
        # None draws castle_pixels. Same origin, so dy can go above 0 when it's taller.
        self.castle_shape = None
        self.castle_x, self.castle_y = (width - cw) // 2, height - ch
        self.castle_w, self.castle_h = cw, ch
        sx, sy, _ = min((p for p in self.castle_pixels if p[2] == "G"), key=lambda p: p[1])
        self.spire = (self.castle_x + sx, self.castle_y + sy - 1)

        big = height >= 64
        self.scale = 2 if big else 1  # the castle's pixel scale
        self.spark_count = 48 if big else 22
        self.spark_speed = 1.1 if big else 0.6
        self.rocket_speed = 1.6 if big else 1.1
        self.launch_gap = (6, 16) if big else (10, 26)
        self.shape_radius = 7 if big else 4
        self.stars = [(self.rng.randrange(width), self.rng.randrange(max(1, self.castle_y + ch // 2)))
                      for _ in range(width // 5)]

        self.cue = None
        self.t = 0.0
        self.palette = [(255, 255, 255)]
        self.rate = 1.0
        self.shapes = ()
        self.effects = frozenset()
        self.castle_from = self.castle_to = dict(_CASTLE_COLORS)
        self.castle_change_t = -CASTLE_FADE_S
        self.castle_look = None
        self.castle_wipe = False  # the change under way runs top to bottom (WIPE_S)
        self.flashed = False
        self.tink_scale = self.scale
        self.tink_w = len(TinkReveal.art[0]) * self.tink_scale
        self.tink_h = len(TinkReveal.art) * self.tink_scale
        self.extras = {name: effect(self) for name, effect in show_effects.EFFECTS.items()}
        self.hit_comets = show_effects.HitComets(self)
        self.hits_done = set()  # (scene start, index) of the score's hits already fired
        self.stage = "castle"
        self.stage_from = self.stage_to = 1.0
        self.stage_change_t = -CASTLE_FADE_S
        self.actors = {name: actor(self) for name, actor in show_actors.ACTORS.items()}

    # ---- cues ----

    def set_cue(self, cue, t):
        """Follow the score's scene at t seconds into the show."""
        self.t = t
        if cue is not self.cue:
            self.cue = cue
            self.palette = list(cue.palette)
            self.shapes = cue.shapes
            self.effects = cue.effects
        # A scene's look and stage are set as it starts, and again at each of its timed changes.
        look = cue.castle_at(t)
        if look != self.castle_look:
            # The castle turns once the wishing star lands; otherwise as the scene starts or changes.
            starting = look == cue.castle
            wish = starting and "wishing_star" in cue.effects
            when = cue.start + WISH_LANDS_AT * (cue.end - cue.start) if wish else t
            self.castle_from = self._castle_now()
            self.castle_to = {**_CASTLE_COLORS, **CASTLE_LOOKS.get(look, {})}
            self.castle_change_t = when
            self.castle_look = look
            self.castle_wipe = starting and "wipe_down" in cue.effects
        stage = cue.stage_at(t)
        if stage != self.stage:
            self.stage_from = self.castle_level()
            self.stage_to = STAGE_LEVELS[stage]
            self.stage_change_t = t
            self.stage = stage
        flying = "tink" in self.effects and t < cue.start + TINK_FLY_S
        self.rate = cue.rate * (TINK_RATE if flying else 1.0)
        # The white flash on the show's last hit: its scene starts on the hit.
        if "final_flash" in self.effects and not self.flashed:
            self.white, self.flashed = 1.0, True

    def _castle_now(self):
        blend = smooth((self.t - self.castle_change_t) / (WIPE_S if self.castle_wipe else CASTLE_FADE_S))
        return {k: tuple(int(a + (b - a) * blend) for a, b in zip(self.castle_from[k], self.castle_to[k]))
                for k in self.castle_to}

    def castle_level(self):
        """How bright the castle is (1 full, 0 gone), fading to the scene's stage."""
        blend = smooth((self.t - self.stage_change_t) / CASTLE_FADE_S)
        return self.stage_from + (self.stage_to - self.stage_from) * blend

    # ---- simulation ----

    def _colour(self):
        if "rainbow" in self.effects:
            r, g, b = colorsys.hsv_to_rgb((self.frame * 0.03 + self.rng.random() * 0.2) % 1.0, 1.0, 1.0)
            return int(r * 255), int(g * 255), int(b * 255)
        return self.rng.choice(self.palette)

    def _pick_shape(self):
        roll = self.rng.random()
        for shape, chance in self.shapes:
            if roll < chance:
                return shape
            roll -= chance
        return None

    def launch(self):
        rng = self.rng
        top = self.height * 0.12
        bottom = self.castle_y + self.castle_h * 0.15
        shape = self._pick_shape()
        if shape in SHAPES:
            # Keep the whole shape on the board.
            reach = self.shape_radius + 1
            x = rng.uniform(reach, self.width - reach)
            top = max(top, reach)
            burst_y = rng.uniform(top, max(top + 1, min(bottom, self.height - reach)))
            self.rockets.append(_Rocket(x, self.height - 1, 0.0, -self.rocket_speed, burst_y, self._colour(), shape))
            return
        if rng.random() < 0.5:
            x = self.castle_x + rng.uniform(2, self.castle_w - 3)
        else:
            margin = max(2, self.castle_x - 1)
            x = rng.uniform(1, margin) if rng.random() < 0.5 else rng.uniform(self.width - margin, self.width - 2)
        burst_y = rng.uniform(top, max(top + 1, bottom))
        self.rockets.append(_Rocket(x, self.height - 1, rng.uniform(-0.12, 0.12), -self.rocket_speed,
                                    burst_y, self._colour()))

    def _explode(self, rocket):
        rng = self.rng
        if rocket.shape:
            # Every spark shares one life, so the shape grows, holds and fades together, reaching
            # full size about 60% of the way through.
            travel = (1 - DRAG ** (MICKEY_LIFE * 0.6)) / (1 - DRAG)
            speed = self.shape_radius / travel
            for px, py, rgb in SHAPES[rocket.shape]:
                self.sparks.append(_Spark(rocket.x, rocket.y, px * speed, py * speed, MICKEY_LIFE,
                                          rgb or rocket.color, gravity=GRAVITY * 0.2))
        elif rocket.style in ("willow", "curtain"):
            # A hit's willow in its own colour; a curtain is bigger and hangs down over the castle.
            curtain = rocket.style == "curtain"
            for _ in range(int(self.spark_count * (1.6 if curtain else 1.0))):
                angle = rng.uniform(0, 2 * math.pi)
                speed = self.spark_speed * rng.uniform(0.4, 1.0 if curtain else 0.9)
                self.sparks.append(_Spark(rocket.x, rocket.y, math.cos(angle) * speed, math.sin(angle) * speed,
                                          rng.randint(90, 130) if curtain else rng.randint(60, 90), rocket.color,
                                          gravity=GRAVITY * (0.9 if curtain else 0.6)))
        elif "willow" in self.effects and rng.random() < WILLOW_CHANCE:
            # Slow sparks that live long and droop, trailing gold.
            for _ in range(self.spark_count):
                angle = rng.uniform(0, 2 * math.pi)
                speed = self.spark_speed * rng.uniform(0.4, 0.9)
                self.sparks.append(_Spark(rocket.x, rocket.y, math.cos(angle) * speed, math.sin(angle) * speed,
                                          rng.randint(60, 90), WILLOW_RGB, gravity=GRAVITY * 0.6))
        else:
            second = self._colour() if rng.random() < 0.35 else None
            ring = rng.random() < 0.3
            for i in range(self.spark_count):
                angle = (2 * math.pi * i / self.spark_count) if ring else rng.uniform(0, 2 * math.pi)
                speed = self.spark_speed * (1.0 if ring else rng.uniform(0.3, 1.0))
                colour = second if (second and i % 2) else rocket.color
                self.sparks.append(_Spark(rocket.x, rocket.y, math.cos(angle) * speed, math.sin(angle) * speed,
                                          rng.randint(28, 44), colour))
        for c in range(3):
            self.flash[c] = min(1.0, self.flash[c] + rocket.color[c] / 255 * 0.6)

    def step(self):
        rng = self.rng
        if self.rate > 0:
            if self.frames_to_next_launch <= 0:
                self.launch()
                if rng.random() < min(0.6, 0.3 * self.rate):
                    self.launch()
                self.frames_to_next_launch = rng.randint(*self.launch_gap) / self.rate
            self.frames_to_next_launch -= 1

        self._fire_hits()
        self.hit_comets.step(False)

        rising = []
        for r in self.rockets:
            r.x += r.vx
            r.y += r.vy
            r.vy += GRAVITY * 0.3
            if r.y <= r.burst_y or r.vy >= 0:
                self._explode(r)
            else:
                rising.append(r)
        self.rockets = rising

        alive = []
        for s in self.sparks:
            s.vx *= DRAG
            s.vy = s.vy * DRAG + s.gravity
            s.x += s.vx
            s.y += s.vy
            s.life -= 1
            if s.life > 0 and -2 <= s.x < self.width + 2 and s.y < self.height:
                alive.append(s)
        self.sparks = alive

        big = self.height >= 64
        if "lanterns" in self.effects and len(self.lanterns) < 40 and rng.random() < (0.2 if big else 0.12):
            # [x, y, rise speed, wobble phase]
            self.lanterns.append([rng.uniform(1, self.width - 2), float(self.height),
                                  rng.uniform(0.08, 0.15) * (1.6 if big else 1.0), rng.uniform(0, 2 * math.pi)])
        for lantern in self.lanterns:
            lantern[1] -= lantern[2]
        self.lanterns = [lantern for lantern in self.lanterns if lantern[1] > -2]

        if "embers" in self.effects and len(self.embers) < 60 and rng.random() < 0.3:
            # [x, y, vx, vy, life, max life]: drifting down from the burning sky
            life = rng.randint(60, 120)
            self.embers.append([rng.uniform(0, self.width), rng.uniform(0, self.height * 0.5),
                                rng.uniform(-0.05, 0.05), rng.uniform(0.04, 0.1), life, life])
        for ember in self.embers:
            ember[0] += ember[2]
            ember[1] += ember[3]
            ember[4] -= 1
        self.embers = [e for e in self.embers if e[4] > 0 and e[1] < self.height]

        tink = self.tink_at()
        if tink:
            x, y = tink
            for _ in range(2 * self.tink_scale):
                life = rng.randint(15, 30)
                self.dust.append([x + rng.uniform(-self.tink_w / 2, 0), y + rng.uniform(0, self.tink_h / 2),
                                  rng.uniform(-0.15, 0.05), rng.uniform(0.05, 0.3), life, life,
                                  rng.choice(TinkReveal.dust_colors)])
        for d in self.dust:
            d[0] += d[2]
            d[1] += d[3]
            d[4] -= 1
        self.dust = [d for d in self.dust if d[4] > 0]

        self.flash = [f * 0.85 for f in self.flash]
        self.white *= 0.93
        for name, effect in self.extras.items():
            effect.step(name in self.effects)
        actors = self.cue.actors if self.cue else ()
        for name, actor in self.actors.items():
            actor.follow(name in actors)
            actor.step(name in actors)
        self.frame += 1

    def _fire_hits(self):
        """Fire each of the scene's hits once, at its time: a shell launches early by its climb so it
        bursts on time. One more than a second late (the show started past it) is skipped."""
        cue = self.cue
        for i, hit in enumerate(cue.hits if cue else ()):
            key = (cue.start, i)
            if key in self.hits_done:
                continue
            burst_y = hit.y * self.height
            climb_s = (self.height - 1 - burst_y) / self.rocket_speed / HIT_FPS if hit.kind == "shell" else 0.0
            if self.t < hit.at - climb_s:
                continue
            self.hits_done.add(key)
            if self.t > hit.at + 1.0:
                continue
            if hit.kind == "shell":
                self.rockets.append(_Rocket(hit.x * self.width, self.height - 1, 0.0, -self.rocket_speed,
                                            burst_y, hit.rgb, style=hit.style))
            elif hit.kind == "roof_fan":
                self.hit_comets.roof_fan(hit.rgb)
            else:
                self.hit_comets.comet(hit.side, hit.rgb)

    # ---- drawing ----

    def _wish_path(self, p):
        """Where the wishing star is p (0..1) of the way through its scene: from the top corner down
        onto the spire, landing at WISH_LANDS_AT and staying there."""
        sx, sy = self.width - 3.0, 1.0
        ex, ey = self.spire
        k = ease_out(min(1.0, p / WISH_LANDS_AT))
        return sx + (ex - sx) * k, sy + (ey - sy) * k

    def tink_at(self):
        """Tink's centre while she flies, else None: up off the spire (rising for the first half of the
        flight), then out past the right edge, speeding up as she goes, with a little bob."""
        if "tink" not in self.effects or self.cue is None:
            return None
        p = (self.t - self.cue.start) / TINK_FLY_S
        if not 0 <= p < 1:
            return None
        sx, sy = self.spire[0], self.spire[1] - self.tink_h / 2
        top = self.height * 0.2
        end_x = self.width + self.tink_w
        x = sx + (end_x - sx) * p ** 1.5
        y = sy + (top - sy) * smooth(p / 0.5) + math.sin(p * math.pi * 4) * self.tink_scale
        return x, y

    def frame_pixels(self):
        """Compose the current frame as {(x, y): (r, g, b)}; unlisted pixels are black."""
        out = {}
        width, height, seen = self.width, self.height, out.get

        # Called for every lit LED of every frame, so it's written out long-hand: a Pi Zero spends
        # most of a frame here.
        def put(x, y, rgb):
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < width and 0 <= yi < height:
                prev = seen((xi, yi))
                if prev:
                    rgb = (max(prev[0], rgb[0]), max(prev[1], rgb[1]), max(prev[2], rgb[2]))
                out[(xi, yi)] = rgb

        for sx, sy in self.stars:
            twinkle = 25 + int(25 * self.rng.random())
            put(sx, sy, (twinkle, twinkle, twinkle + 10))

        for s in self.sparks:
            f = s.life / s.max_life
            hot = max(0.0, (f - 0.8) / 0.2)
            r, g, b = s.color
            put(s.x, s.y, (int((r + (255 - r) * hot) * f), int((g + (255 - g) * hot) * f),
                           int((b + (255 - b) * hot) * f)))
            if f > 0.5:
                put(s.x - s.vx * 1.5, s.y - s.vy * 1.5, (int(r * f * 0.35), int(g * f * 0.35), int(b * f * 0.35)))

        for r in self.rockets:
            put(r.x, r.y, (255, 230, 180))
            put(r.x, r.y + 1, (140, 90, 40))
            put(r.x, r.y + 2, (50, 30, 10))

        # A lantern is a glowing body (2 LEDs tall, 2x2 on a 64-row board) over a dim halo.
        size = 2 if self.height >= 64 else 1
        for x, y, _, phase in self.lanterns:
            glow = 0.8 + 0.2 * math.sin(self.frame * 0.2 + phase)
            lx = int(round(x + 0.6 * math.sin(self.frame * 0.05 + phase)))
            ly = int(round(y))
            halo = tuple(int(c * glow * 0.25) for c in LANTERN_RGB)
            for dx in range(-1, size + 1):
                for dy in range(-1, 3):
                    put(lx + dx, ly + dy, halo)
            body = tuple(int(c * glow) for c in LANTERN_RGB)
            for dx in range(size):
                for dy in range(2):
                    put(lx + dx, ly + dy, body)

        for x, y, _, _, life, max_life in self.embers:
            put(x, y, tuple(int(c * life / max_life) for c in EMBER_RGB))

        if "wishing_star" in self.effects and self.cue is not None:
            p = self.cue.progress(self.t)
            for k in range(6, 0, -1):  # a fading trail behind it
                tx, ty = self._wish_path(max(0.0, p - k * 0.02))
                put(tx, ty, tuple(int(c * (1 - k / 7) * 0.5) for c in WISH_GLOW_RGB))
            x, y = self._wish_path(p)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                put(x + dx, y + dy, WISH_GLOW_RGB)
            put(x, y, WISH_RGB)

        for x, y, _, _, life, max_life, rgb in self.dust:
            put(x, y, tuple(int(c * life / max_life) for c in rgb))

        for name, effect in self.extras.items():
            effect.draw_behind(put, out, name in self.effects)
        self.hit_comets.draw_behind(put, out, True)

        # The castle hides anything launched from behind it; Tink and the effects' fronts don't. Dimmed
        # for a stage, it's a ghost the sky shows through; gone, it hides nothing.
        shown = self.castle_level()
        colours = self._castle_now()
        flicker = self.castle_look in _FLICKERS
        wipe = (self.t - self.castle_change_t) / WIPE_S if self.castle_wipe else 1.0
        wiping = 0 <= wipe < 1
        rows = {}  # a wipe's colours for each row of the castle, worked out once a frame

        def row_colours(dy):
            row = rows.get(dy)
            if row is None:
                f = smooth(wipe * 2 - dy / self.castle_h)
                row = rows[dy] = {k: tuple(int(a + (b - a) * f) for a, b in zip(self.castle_from[k], to))
                                  for k, to in self.castle_to.items()}
            return row
        glass = smooth((self.t - self.castle_change_t) / CASTLE_FADE_S) if self.castle_look == "stained_glass" else 0
        # A lit colour and a dimmed one depend only on the colour going in (and this frame's flash and
        # stage level), so each is worked out once a frame, not once an LED: the castle is most of a
        # frame's LEDs.
        fr, fg, fb = self.flash
        lit, dimmed = {}, {}

        def glowing(base):
            glow = lit.get(base)
            if glow is None:
                glow = lit[base] = (min(255, int(base[0] * 0.75 + 110 * fr)),
                                    min(255, int(base[1] * 0.75 + 110 * fg)),
                                    min(255, int(base[2] * 0.75 + 110 * fb)))
            return glow

        def dim(base):
            low = dimmed.get(base)
            if low is None:
                low = dimmed[base] = (int(base[0] * shown), int(base[1] * shown), int(base[2] * shown))
            return low

        if shown > 0.01 and not flicker and not wiping:
            # Without the fire's flicker every LED of a kind (or of a stained-glass tile) is one colour,
            # and from one frame to the next usually the same one: the finished castle is kept and
            # reused while its colours hold.
            finals = {}
            for kind, base in colours.items():
                finals[kind] = glowing(base) if kind in _LIT_KINDS else base
            if glass:
                for i, tile in enumerate(_STAINED_GLASS):
                    base = tuple(int(a + (b - a) * glass) for a, b in zip(colours["W"], tile))
                    finals[("W", i)] = glowing(base) if "W" in _LIT_KINDS else base
            if shown < 1:
                finals = {k: dim(rgb) for k, rgb in finals.items()}
            key = (tuple(sorted((str(k), rgb) for k, rgb in finals.items())), shown < 1, id(self.castle_shape))
            if key != self._castle_key:
                layer = {}
                for dx, dy, kind in self.castle_shape or self.castle_pixels:
                    x, y = self.castle_x + dx, self.castle_y + dy
                    if 0 <= x < width and 0 <= y < height:
                        if kind == "W" and glass:
                            kind = ("W", (dx // (2 * self.scale) * 3 + dy // (2 * self.scale)) % 4)
                        layer[(x, y)] = finals[kind]
                self._castle_key, self._castle_layer = key, layer
            if shown < 1:
                for xy, rgb in self._castle_layer.items():
                    prev = seen(xy)
                    out[xy] = (max(prev[0], rgb[0]), max(prev[1], rgb[1]), max(prev[2], rgb[2])) if prev else rgb
            else:
                out.update(self._castle_layer)
        else:
            for dx, dy, kind in ((self.castle_shape or self.castle_pixels) if shown > 0.01 else ()):
                x, y = self.castle_x + dx, self.castle_y + dy
                if not (0 <= x < width and 0 <= y < height):
                    continue
                base = row_colours(dy)[kind] if wiping else colours[kind]
                if kind == "W" and glass:
                    tile = _STAINED_GLASS[(dx // (2 * self.scale) * 3 + dy // (2 * self.scale)) % 4]
                    base = tuple(int(a + (b - a) * glass) for a, b in zip(base, tile))
                if kind in _LIT_KINDS and flicker:
                    # Each LED on its own phase (a hash of its spot), so the fire doesn't band.
                    level = 0.75 + 0.25 * math.sin(self.frame * 0.7 + (dx * 7919 + dy * 104729) % 628 / 100)
                    base = glowing((int(base[0] * level), int(base[1] * level), int(base[2] * level)))
                elif kind in _LIT_KINDS:
                    base = glowing(base)
                if shown < 1:
                    put(x, y, dim(base))
                else:
                    out[(x, y)] = base

        for name, effect in self.extras.items():
            effect.draw_front(put, out, name in self.effects)

        tink = self.tink_at()
        if tink:
            left = int(round(tink[0] - self.tink_w / 2))
            top = int(round(tink[1] - self.tink_h / 2))
            for row, line in enumerate(TinkReveal.art):
                for col, key in enumerate(line):
                    if key == ".":
                        continue
                    for oy in range(self.tink_scale):
                        for ox in range(self.tink_scale):
                            x, y = left + col * self.tink_scale + ox, top + row * self.tink_scale + oy
                            if 0 <= x < self.width and 0 <= y < self.height:
                                out[(x, y)] = TinkReveal.colors[key]

        actors = self.cue.actors if self.cue else ()
        for name, actor in self.actors.items():
            actor.draw(put, out, name in actors)

        if self.white > 0.02:
            level = int(255 * min(1.0, self.white))
            # Every pixel at least `level` on each channel. Written as plain loops, not a tuple(max(...)
            # for ...) per pixel: this is the biggest frame of the show, and the Pi's build time was in it.
            for pos, (r, g, b) in out.items():
                out[pos] = (r if r > level else level, g if g > level else level, b if b > level else level)
            blank = (level, level, level)
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) not in out:
                        out[(x, y)] = blank
        return out


def render_music_show(matrix, score, fps=30, rng=None, clock=time.monotonic):
    """Play the score's show on the matrix from its first second to its end, following the clock. Logs
    each scene's frame rate and slowest frame as it ends, to see how a board keeps up: where the slowest
    frame's time went (building the picture or pushing it to the panel), how many frames ran past their
    slot, the busiest frame's pixel count, how much CPU the show thread used against the whole process
    (the difference is the other threads), and the board's own state (system_stats)."""
    # The music started just before this call: count from here, so the time spent building the show
    # (its characters draw their poses up front) doesn't put the picture behind the music.
    t0 = clock()
    show = MusicShow(matrix.width, matrix.height, rng, score.lips)
    canvas = frame_canvas(matrix)
    frame_time = 1.0 / fps
    debug.info(f"Playing the {score.name} show ({score.version}) for {score.end:.0f}s "
               f"(ready in {(clock() - t0) * 1000:.0f} ms).")
    cue = None
    frames, late, most_pixels, scene_start = 0, 0, 0, 0.0
    slowest, slowest_build = 0.0, 0.0
    cpu_thread, cpu_process = time.thread_time(), time.process_time()

    def log_scene(t):
        nonlocal cpu_thread, cpu_process
        thread, process = time.thread_time(), time.process_time()
        if cue is not None and t > scene_start:
            wall = t - scene_start
            board = system_stats.describe()
            debug.info(f"{score.name} {cue.title}: {frames / wall:.1f} fps "
                       f"(aiming for {fps}), slowest frame {slowest * 1000:.0f} ms "
                       f"(build {slowest_build * 1000:.0f} / push {(slowest - slowest_build) * 1000:.0f}), "
                       f"{late} late, {most_pixels} px, "
                       f"CPU show {(thread - cpu_thread) / wall:.0%} / process {(process - cpu_process) / wall:.0%}"
                       + (f", {board}" if board else ""))
        cpu_thread, cpu_process = thread, process

    while True:
        start = clock()
        t = start - t0
        if t >= score.end:
            break
        now = score.cue_at(t)
        if now is not cue:
            log_scene(t)
            cue = now
            frames, late, most_pixels, scene_start = 0, 0, 0, t
            slowest, slowest_build = 0.0, 0.0
            debug.info(f"{score.name} {t:.0f}s: {cue.title}")  # once a scene, to check the sync by ear
        show.set_cue(cue, t)
        show.step()
        pixels = show.frame_pixels()
        built = clock()
        canvas.Clear()
        for (x, y), (r, g, b) in pixels.items():
            canvas.SetPixel(x, y, r, g, b)
        canvas = present(matrix, canvas)
        spent = clock() - start
        frames += 1
        most_pixels = max(most_pixels, len(pixels))
        if spent > frame_time:
            late += 1
        if spent > slowest:
            slowest, slowest_build = spent, built - start
        remaining = frame_time - spent
        if remaining > 0:
            time.sleep(remaining)
    log_scene(clock() - t0)
    matrix.Clear()
