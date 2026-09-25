import math
import random
import time

from driver import graphics

FPS = 30
COVER_S = 0.55
WIPE_S = 0.65
FLYBY_S = 1.2
EDGE_RGB = (255, 215, 0)

_canvases = {}
_last_screen = {}


def frame_canvas(matrix):
    """One reusable offscreen canvas per matrix; rgbmatrix never frees canvases from CreateFrameCanvas."""
    key = id(matrix)
    if key not in _canvases:
        _canvases[key] = matrix.CreateFrameCanvas()
    return _canvases[key]


def present(matrix, canvas):
    """Show canvas and keep the returned back buffer for the next frame."""
    _canvases[id(matrix)] = matrix.SwapOnVSync(canvas)
    return _canvases[id(matrix)]


def forget_screen(matrix):
    """The next screen should reveal from black rather than cover whatever played last."""
    _last_screen.pop(id(matrix), None)


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def run_frames(matrix, draw_frame, duration_s, fps=FPS):
    """Call draw_frame(canvas, t) each frame for duration_s; once it returns False the image is static and we sleep out the rest."""
    frame_time = 1.0 / fps
    frames = int(duration_s * fps)
    canvas = frame_canvas(matrix)
    began = time.monotonic()
    for i in range(frames):
        start = time.monotonic()
        # A slow board drops frames rather than stretching the screen past duration_s.
        if start - began >= duration_s:
            return
        canvas.Clear()
        animating = draw_frame(canvas, i / fps)
        canvas = present(matrix, canvas)
        if not animating:
            time.sleep(max(0.0, duration_s - (time.monotonic() - began)))
            return
        remaining = frame_time - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)


def _blackout(canvas, x0, x1, height):
    black = graphics.Color(0, 0, 0)
    for x in range(max(0, x0), x1):
        graphics.DrawLine(canvas, x, 0, x, height - 1, black)


def _edge(canvas, x, width, height):
    if 0 <= x < width:
        graphics.DrawLine(canvas, x, 0, x, height - 1, graphics.Color(*EDGE_RGB))


class Wipe:
    """Reveals the new screen left to right behind a gold edge."""

    duration = WIPE_S

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = int(ease_out(t / self.duration) * (self.width + 1))
        _blackout(canvas, x + 1, self.width, self.height)
        _edge(canvas, x, self.width, self.height)
        return True


class FlyByReveal:
    """
    A character flies across the board and the new screen appears behind them and
    their particle trail. Subclasses supply the sprite, flight path and trail.
    """

    duration = FLYBY_S
    art = []
    colors = {}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.art[0]) * self.scale
        self.sprite_h = len(self.art) * self.scale
        # Each particle: [x, y, vx, vy, frames_left, rgb]
        self.particles = []
        self.last_frame = -1

    def progress_x(self, t):
        # Starts just off the left edge and ends just off the right.
        return -self.sprite_w + (t / self.duration) * (self.width + 2 * self.sprite_w)

    def position(self, t):
        raise NotImplementedError

    def spawn(self, x, y):
        """New trail particles for a frame where the sprite's top-left corner is at (x, y)."""
        raise NotImplementedError

    def _step_particles(self, t):
        frame = int(t * FPS)
        while self.last_frame < frame:
            self.last_frame += 1
            if self.last_frame / FPS < self.duration:
                self.particles.extend(self.spawn(*self.position(self.last_frame / FPS)))
            for p in self.particles:
                p[0] += p[2]
                p[1] += p[3]
                p[4] -= 1
            self.particles = [p for p in self.particles if p[4] > 0]

    def overlay(self, canvas, t):
        self._step_particles(t)
        if t < self.duration:
            x, _ = self.position(t)
            _blackout(canvas, int(x) + self.sprite_w // 2 + 1, self.width, self.height)
        for px, py, _, _, life, rgb in self.particles:
            f = min(1.0, life / 12)
            px, py = int(round(px)), int(round(py))
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *(int(c * f) for c in rgb))
        if t < self.duration:
            self._draw_sprite(canvas, t)
        return t < self.duration or bool(self.particles)

    def _draw_sprite(self, canvas, t):
        x0, y0 = self.position(t)
        x0, y0 = int(round(x0)), int(round(y0))
        for row, line in enumerate(self.art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = x0 + col * self.scale + sx, y0 + row * self.scale + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.colors[kind])


class TinkReveal(FlyByReveal):
    """Tinker Bell bobs across leaving a drifting trail of pixie dust."""

    # '.' empty, W wing, Y glow, G dress.
    art = [
        "WW.WW",
        "WWYWW",
        "..Y..",
        ".GGG.",
        "..G..",
    ]
    colors = {"W": (170, 220, 255), "Y": (255, 245, 170), "G": (60, 220, 90)}
    dust_colors = [(255, 235, 140), (255, 255, 255), (255, 200, 90)]

    def position(self, t):
        p = t / self.duration
        return self.progress_x(t), self.height * 0.45 + math.sin(p * math.pi * 3) * self.height * 0.18

    def spawn(self, x, y):
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w / 2), y + r.uniform(0, self.sprite_w / 2),
                 r.uniform(-0.15, 0.15), r.uniform(0.05, 0.35), r.randint(12, 24), r.choice(self.dust_colors)]
                for _ in range(2 * self.scale)]


class BuzzReveal(FlyByReveal):
    """Buzz Lightyear climbs across, to infinity, on a short rocket-flame trail."""

    # Side view flying right. '.' empty, W suit/wings, G green chest and wing tips,
    # P purple hood, S face, R wing light.
    art = [
        "..GG....",
        "...WWR..",
        "WWWWGWPS",
        "...WWR..",
        "..GG....",
    ]
    colors = {"W": (235, 235, 245), "G": (60, 210, 60), "P": (140, 70, 210), "S": (255, 205, 170), "R": (255, 40, 40)}
    flame_colors = [(255, 240, 150), (255, 170, 30), (255, 90, 20), (230, 40, 20)]

    def position(self, t):
        # A steady climb from low left to high right.
        p = t / self.duration
        return self.progress_x(t), self.height * (0.62 - 0.4 * p) - self.sprite_h / 2

    def spawn(self, x, y):
        r = self.rng
        tail_y = y + self.sprite_h / 2 - 0.5
        return [[x - 1, tail_y + r.uniform(-0.5, 0.5) * self.scale,
                 r.uniform(-0.7, -0.2) * self.scale, r.uniform(-0.05, 0.1), r.randint(12, 20), r.choice(self.flame_colors)]
                for _ in range(4 * self.scale)]


class FigmentReveal(FlyByReveal):
    """Figment flutters across, trailing sparkly imagination dust."""

    duration = FLYBY_S * 1.8

    # Side view flying right: curved horns, long snout, slim neck, bat wing, striped tail.
    # '.' empty, P purple body, D darker purple shading, G green wing, N green wing edge,
    # O orange horn/belly/tail stripe, E white eye, B pupil, K outline, M mouth.
    art = [
        "..............KK.....KK..",
        ".............KOOK...KOOK.",
        ".............KOOK..KOOK..",
        "..............KOOKKOOK...",
        "...............KPPPPK....",
        "..............KPPPPPPK...",
        ".....KKKK....KPPEBPPPPK..",
        "...KKGGGGKK..KPPEBPPPPPK.",
        "..KGGNNGGGGK.KPPPPPMMMPPK",
        "..KGNNNNGGGKKPPPPPPMMMPPK",
        "..KGGNNNGGKPPPPPPPPKKKKK.",
        "...KGGGGGKPPPPPPPPPK.....",
        "....KKKKKPPPPPPPPPK......",
        "..KOK....KPPPPPPPK.......",
        ".KOOOK...KPPPPPPK........",
        "KOOKOOK..KPPDDPPK........",
        "KOK.KOK...KPDDPK.........",
        ".K...KK...KPPPPK.........",
        "..........KOOOOK.........",
        "...........KKKK..........",
    ]
    colors = {
        "P": (150, 70, 190), "D": (110, 45, 150), "G": (90, 200, 110), "N": (140, 230, 150),
        "O": (235, 140, 40), "E": (250, 250, 250), "B": (25, 25, 35), "K": (45, 20, 60),
        "M": (230, 120, 160),
    }
    dust_colors = [(210, 140, 255), (255, 255, 255), (140, 220, 255)]

    def position(self, t):
        p = t / self.duration
        # A gentler, wider bob than Tinker Bell's, clamped to the room his sprite leaves.
        room = max(0, self.height - self.sprite_h)
        amp = min(room / 2, self.height * 0.15)
        return self.progress_x(t), room / 2 + math.sin(p * math.pi * 3) * amp

    def spawn(self, x, y):
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w / 2), y + r.uniform(0, self.sprite_w / 2),
                 r.uniform(-0.2, 0.1), r.uniform(0.05, 0.3), r.randint(10, 20), r.choice(self.dust_colors)]
                for _ in range(2 * self.scale)]


class DumboReveal(FlyByReveal):
    """
    TODO (art): his back half is missing — he reads as a head, ears and trunk with no
    body or rear behind them. Extend the sprite so he has a hindquarters and legs.

    Dumbo flies across the board the only way he knows how — by flapping those ears.
    Two poses alternate on FLAP_S, and the same flap phase drives a gentle bob, so he
    lifts on the upstroke and settles on the down. He trails little white feather-puffs
    from the circus act rather than dust or flame.
    """

    duration = FLYBY_S * 1.9
    FLAP_S = 0.22  # seconds per half-flap (ears up, then ears down)

    # Three-quarter view flying right: enormous pink-lined ears either side of a small
    # head, trunk curling down and forward, yellow-and-blue circus hat, white collar.
    # '.' empty, P inner ear pink, D shaded outer ear, G body grey, L lit grey (trunk),
    # K outline, E eye white, B pupil, W collar, Y hat yellow, U hat blue.
    EARS_UP = [
        "............KKYYKK..........",
        "............KUUUUK..........",
        "............KYYYYK..........",
        "...KKKK....KKYYYYKK....KKKK.",
        "..KPPPPKK..KKKKKKKKK..KPPPPK",
        ".KPPPPPPPKKKGGGGGGGKKKPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGEEGGEEGGPPPPPPPP",
        "KPPPPPPPPPPGBEGGBEGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        ".KPPPPPPPPKGGGGGGGGGKPPPPPPP",
        ".KDPPPPPPK.KGGGKLLGK.KPPPPPD",
        "..KDDPPPK..KGGGKLLGK..KPPPDK",
        "...KDDPK...KWWWKLLGK...KPDK.",
        "....KKK...KWWWWWKLLGK...KK..",
        "..........KGGGGGKLLLK.......",
        "..........KGGGGGKKLLLK......",
        "..........KGGKGGGKKLLLK.....",
        "..........KGGKKGGGK.KLLLK...",
        "...........KK..KKK...KKKK...",
    ]

    # The downstroke: the same elephant with both ears swept low, tips curling under.
    EARS_DOWN = [
        "............KKYYKK..........",
        "............KUUUUK..........",
        "............KYYYYK..........",
        "...........KKYYYYKK.........",
        "....KKK....KKKKKKKKK....KKK.",
        "...KPPPKKKKKGGGGGGGKKKKPPPK.",
        "..KPPPPPPPPGGGGGGGGGPPPPPPPK",
        "..KPPPPPPPPGEEGGEEGGPPPPPPPK",
        ".KPPPPPPPPPGBEGGBEGGPPPPPPPP",
        ".KPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPK.KGGKLLGK.PPPPPPP",
        "KDPPPPPPPK.KGGGKLLGK.KPPPPPP",
        "KDDPPPPPK..KWWWKLLGK..KPPPPD",
        ".KDDPPPK..KWWWWWKLLGK..KPPDD",
        "..KDDPK...KGGGGGKLLLK..KPDDK",
        "...KDK....KGGGGGKKLLLK..KDK.",
        "....K.....KGGKGGGKKLLLK..KK.",
        "..........KGGKKGGGK.KLLLK...",
        "...........KK..KKK...KKKK...",
    ]

    # `art` stays a single pose — the framework and the shared fly-by tests measure it —
    # while `poses` is what actually gets drawn, alternating on the flap.
    art = EARS_UP
    poses = [EARS_UP, EARS_DOWN]
    colors = {
        "P": (238, 170, 182), "D": (176, 132, 142), "G": (150, 158, 172),
        "L": (196, 204, 218), "K": (30, 32, 42), "E": (252, 252, 252),
        "B": (30, 34, 52), "W": (252, 252, 252), "Y": (250, 206, 60), "U": (55, 110, 215),
    }
    feather_colors = [(255, 255, 255), (238, 240, 250), (255, 235, 170)]

    def flap_phase(self, t):
        """0..1 through one full flap cycle (ears up, ears down, back again)."""
        return (t / (2 * self.FLAP_S)) % 1.0

    def flap_frame(self, t):
        """Index into self.poses: 0 while the ears are up, 1 while they are down."""
        return int(t / self.FLAP_S) % len(self.poses)

    def position(self, t):
        # He bobs with the flap — lifting on the upstroke, settling on the down — inside
        # whatever vertical room the sprite leaves, so he never clips off either board.
        room = max(0.0, self.height - self.sprite_h)
        amp = min(room / 2, self.height * 0.09)
        y = room / 2 - math.cos(self.flap_phase(t) * 2 * math.pi) * amp
        return self.progress_x(t), y

    def spawn(self, x, y):
        # Feather-puffs shed off the trailing (left) ear, drifting back and down.
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w * 0.35),
                 y + self.sprite_h * r.uniform(0.25, 0.75),
                 r.uniform(-0.45, -0.05), r.uniform(-0.05, 0.25),
                 r.randint(10, 22), r.choice(self.feather_colors)]
                for _ in range(2 * self.scale)]

    def _draw_sprite(self, canvas, t):
        """Same as the base draw, but picks the flap pose for this moment."""
        art = self.poses[self.flap_frame(t)]
        x0, y0 = self.position(t)
        x0, y0 = int(round(x0)), int(round(y0))
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = x0 + col * self.scale + sx, y0 + row * self.scale + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.colors[kind])


class PeekReveal:
    """
    A character pops up from the bottom edge over the already-revealed screen, looks
    around, and ducks back down — no blackout, no particle trail, no travel across
    the board. Subclasses supply the art and how far up "peeking" rises.
    """

    duration = 0
    art = []
    colors = {}
    rise_frac = 0.55  # fraction of the sprite's height that stays visible at the peek's peak

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        # self.art is either one pose (a list of row-strings) or several poses
        # (a list of those); measure the first pose's rows either way.
        first_pose = self.art[0] if isinstance(self.art[0], list) else self.art
        self.sprite_w = len(first_pose[0]) * self.scale
        self.sprite_h = len(first_pose) * self.scale
        self.cx = rng.uniform(0.3, 0.7) * width if rng else width / 2

    def rise(self, t):
        """0 (hidden below the edge) to 1 (fully risen) over the whole duration, holding at the top."""
        raise NotImplementedError

    def look_frame(self, t):
        """Index into self.art's alternate poses (e.g. head turned) for this t, or 0 if art has only one."""
        return 0

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        rise = max(0.0, min(1.0, self.rise(t)))
        if rise <= 0:
            return True
        # y0 slides from `height` (sprite entirely below the board, hidden) up to
        # `height - rise_frac * sprite_h` (his top rise_frac risen above the edge).
        # Rows that land at py >= height are still "underground" — the bounds check
        # below simply doesn't draw them, no separate clipping needed.
        y0 = self.height - rise * self.rise_frac * self.sprite_h
        x0 = int(self.cx - self.sprite_w / 2)
        art = self.art[self.look_frame(t)] if isinstance(self.art[0], list) else self.art
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px = x0 + col * self.scale + sx
                        py = int(round(y0 + row * self.scale + sy))
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.colors[kind])
        return True


def _pupils_at(base, side):
    """
    Fill each '##' eye slot in `base`. Stitch's eyes are near-black ovals with a small
    white glint; `side` (0 left, 1 right) puts that glint on one side so he reads as
    glancing that way.
    """
    rows = []
    for line in base:
        while "####" in line:
            line = line.replace("####", "WPPP" if side == 0 else "PPPW", 1)
        rows.append(line)
    return rows


class StitchReveal(PeekReveal):
    """Stitch pops up from the bottom, looks left and right, then ducks back down."""

    duration = 2.6
    UP_S, HOLD_S, LOOK_S = 0.35, 0.5, 0.7
    # His whole head, down through the chin, clears the edge at full rise; his
    # shoulders stay hidden below, as if he's propped up on his arms out of frame.
    rise_frac = 0.88

    # Long ears swept up and out (a notch bitten from his left one), a wide head
    # tapering to a rounded chin, big black nose over a broad smile.
    # '.' empty, U light-blue fur, D dark-blue fur (ear backs, shading), K outline,
    # E eye white, P pupil, W pupil highlight, N pink inner ear, B nose, M mouth, T teeth.
    _BASE = [
        "...KK...............KK...",
        "..KRRK.............KRRK..",
        "..KRRRK...........KRRRK..",
        "..KRRRRK.........KRRRRK..",
        "..KRRRRRK.......KRRRRRK..",
        "...KRRRRRK.....KRRRRRK...",
        "...KRRRRRRK...KRRRRRRK...",
        "....KRRRRRKKKKKRRRRRK....",
        "....KRRRRKUUUUUKRRRRK....",
        ".....KRRKUUUUUUUKRRK.....",
        ".....KRKUUUUUUUUUKRK.....",
        "......KUUUUUUUUUUUKK.....",
        ".....KUUUUUUUUUUUUUUK....",
        "....KUUKKKKUUUKKKKUUUK...",
        "....KUK####KUUUK####KUK..",
        "....KUK####KUUUK####KUK..",
        "....KUKKKKKUBBBUKKKKKUK..",
        ".....KUUUUUKBBBKUUUUUK...",
        ".....KUUUUUUKBKUUUUUUK...",
        "......KUUMMMMMMMMMUUK....",
        "......KMMTTTTTTTTTMMK....",
        "......KMMMMMMMMMMMMMK....",
        ".......KKUUUUUUUUUKK.....",
        ".........KKKKKKKKK.......",
    ]

    art = [_pupils_at(_BASE, 0), _pupils_at(_BASE, 1)]
    colors = {
        "U": (100, 160, 210), "R": (155, 125, 180), "K": (18, 18, 28),
        "P": (58, 62, 84), "W": (255, 255, 255),
        "B": (28, 40, 70), "M": (205, 65, 100), "T": (252, 238, 195),
    }

    def rise(self, t):
        if t < self.UP_S:
            return ease_out(t / self.UP_S)
        if t < self.duration - self.UP_S:
            return 1.0
        down_t = t - (self.duration - self.UP_S)
        return 1.0 - ease_out(down_t / self.UP_S)

    def look_frame(self, t):
        settled = t - self.UP_S
        if settled < 0:
            return 0
        return int(settled / self.LOOK_S) % 2


class _Capture:
    """Stand-in canvas that records what a screen draws, so it can be shattered."""

    def __init__(self, width, height):
        self.width, self.height, self.px = width, height, {}

    def SetPixel(self, x, y, r, g, b):
        if 0 <= x < self.width and 0 <= y < self.height and (r or g or b):
            self.px[(int(x), int(y))] = (r, g, b)

    def Clear(self):
        self.px = {}


class RalphReveal:
    """
    Wreck-It Ralph rises at the bottom, swings a fist, and the old screen shatters
    into falling pixels, leaving the new one behind. Needs the previous screen's
    pixels, so it opts in via wants_prev.
    """

    wants_prev = True
    RISE_S, WIND_S, FALL_S = 0.45, 0.35, 1.25
    duration = RISE_S + WIND_S + FALL_S
    GRAVITY = 0.055

    # Ralph mid-swing: spiky dark-red hair, big pink fists, red shirt, maroon overalls.
    # '.' empty, H hair, F face/skin, E eye, M mouth, S shirt, O overalls, B buckle, K outline.
    ART = [
        "KKKK.....KHHHK.....KKKK",
        "KFFFK...KHHHHHK...KFFFK",
        "KFFFFK.KHHHHHHHK.KFFFFK",
        "KFFFFFKKHFFFFFHKKFFFFFK",
        "KFFFFFK.KFEFEFK.KFFFFFK",
        "KFFFFFK.KFFFFFK.KFFFFFK",
        ".KFFFK..KFMMMFK..KFFFK.",
        "..KFK....KFFFK....KFK..",
        "..KFK...KSSSSSK...KFK..",
        "..KFFKKKKSSSSSKKKKFFK..",
        "...KFFFFSSSSSSSFFFFK...",
        "....KSSSSSSSSSSSSSK....",
        "....KSSSSOBBBOSSSSK....",
        ".....KSSOOBBBOOSSK.....",
        ".....KOOOOOOOOOOOK.....",
        ".....KOOOOOOOOOOOK.....",
        ".....KOOOOKKKOOOOK.....",
        ".....KOOOK...KOOOK.....",
        ".....KFFK.....KFFK.....",
        ".....KKKK.....KKKK.....",
    ]
    COLORS = {
        "H": (140, 25, 30), "F": (240, 180, 160), "E": (20, 20, 25), "M": (90, 30, 35),
        "S": (200, 40, 45), "O": (110, 25, 35), "B": (190, 120, 50), "K": (25, 15, 20),
    }

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.ART[0]) * self.scale
        self.sprite_h = len(self.ART) * self.scale
        self.debris = []
        self.shattered = False
        self._frames_stepped = 0
        self.prev_px = {}

    def capture_prev(self, prev_draw, prev_t):
        """Redraw the old screen onto a capture canvas; those pixels become the debris."""
        shot = _Capture(self.width, self.height)
        prev_draw(shot, prev_t)
        self.prev_px = shot.px

    def _shatter(self):
        """Turn the captured screen into debris, thrown outward from the impact point."""
        self.shattered = True
        # The fists land centre-bottom; everything is flung away from that point.
        impact_x, impact_y = self.width / 2, self.height - self.sprite_h * 0.55
        for (x, y), rgb in self.prev_px.items():
            dx, dy = x - impact_x, y - impact_y
            dist = max(2.0, (dx * dx + dy * dy) ** 0.5)
            power = self.rng.uniform(1.2, 2.4) / dist * 14
            self.debris.append([
                float(x), float(y),
                dx / dist * power + self.rng.uniform(-0.2, 0.2),
                dy / dist * power - self.rng.uniform(0.2, 0.8),
                rgb,
            ])

    def ralph_y(self, t):
        """His top edge: rises into frame, holds through the swing, then drops away."""
        if t < self.RISE_S:
            return self.height - ease_out(t / self.RISE_S) * self.sprite_h
        if t < self.RISE_S + self.WIND_S:
            return self.height - self.sprite_h
        gone = (t - self.RISE_S - self.WIND_S) / self.FALL_S
        return self.height - self.sprite_h + ease_out(gone) * self.sprite_h

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        impact_at = self.RISE_S + self.WIND_S
        if not self.shattered and t >= impact_at:
            self._shatter()
        if t < impact_at:
            # Old screen still whole, with Ralph rising in front of it.
            for (x, y), rgb in self.prev_px.items():
                canvas.SetPixel(x, y, *rgb)
        else:
            self._step_debris(t - impact_at)
            for x, y, _, _, rgb in self.debris:
                px, py = int(round(x)), int(round(y))
                if 0 <= px < self.width and 0 <= py < self.height:
                    canvas.SetPixel(px, py, *rgb)
        self._draw_ralph(canvas, t)
        return True

    def _step_debris(self, since_impact):
        """Advance the falling pixels to the frame matching `since_impact` seconds."""
        target = int(since_impact * FPS)
        while self._frames_stepped < target:
            self._frames_stepped += 1
            for d in self.debris:
                d[0] += d[2]
                d[1] += d[3]
                d[3] += self.GRAVITY

    def _draw_ralph(self, canvas, t):
        y0 = self.ralph_y(t)
        x0 = int(self.width / 2 - self.sprite_w / 2)
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px = x0 + col * self.scale + sx
                        py = int(round(y0 + row * self.scale + sy))
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])


class MickeyReveal:
    """
    TODO (art): the face needs work — the muzzle/eyes read as a flat mask rather than
    Mickey's features. Everything else (hat, ears, robe, wand sweep) is good.

    Sorcerer Mickey sweeps his wand and the NEW screen materializes out of magic dust
    in the wake of the sweep — the inverse of Ralph's shatter. Needs the new screen's
    pixels before they are shown, so it opts in via wants_new.
    """

    wants_new = True
    RISE_S, CAST_S, SETTLE_S = 0.5, 1.15, 0.45
    duration = RISE_S + CAST_S + SETTLE_S
    # How long a pixel spends flying in from its scattered start to its home.
    FLIGHT_S = 0.45

    # Sorcerer Mickey from Fantasia, facing forward with the wand raised to the
    # board's right. Two round black ears, a tall blue star-and-moon hat tipped
    # back over his head, a red robe, and one oversized white glove on the wand.
    # '.' empty, K his fur (a lifted charcoal rather than true black, so the head
    # and ears read as solid shapes against a dark board), T tan face mask,
    # E eye white, P pupil, N nose, M muzzle, U mouth line,
    # H hat blue, S hat star (gold), B hat brim, R robe red, D robe shadow,
    # C collar, G glove white, W wand shaft, Y wand tip glow.
    ART = [
        ".........HHSH........YYY",
        "........HHHHH.......YYYY",
        "..KKK...HHHHHH.....WW...",
        ".KKKKK..HHHSHH....WW....",
        "KKKKKKK.HHHHHH...WW.....",
        "KKKKKKK.HHHHHHH.GGG.KKK.",
        "KKKKKKKHHHHSHHH.GGGKKKKK",
        ".KKKKKHHHHHHHHHHGGGKKKKK",
        "..KKKKBBBBBBBBBBGGKKKKKK",
        "...KKKKKKKKKKKKKK.KKKKKK",
        "...KKTTTTTTTTTTKK..KKKK.",
        "...KTTTTTTTTTTTTK.......",
        "...KTEEETTTTEEETK.......",
        "...KTEPETTTTEPETK.......",
        "...KTEPETTTTEPETK.......",
        "...KTEEETTTTEEETK.......",
        "...KTTTMMMMMMTTTK.......",
        "....KMMMMNNMMMMK........",
        "....KMMMUUUUMMMK........",
        "....KKMUUUUUUMKK........",
        ".....KKKMMMMKKK.........",
        "....CCCCCCCCCCCC........",
        "...RRRRRRRRRRRRRR.......",
        "..RRRRRDDRRDDRRRRR......",
        ".RRRRRRDDRRDDRRRRRR.....",
        "RRRRRRRRRRRRRRRRRRRR....",
    ]
    COLORS = {
        "K": (74, 72, 88), "T": (245, 200, 160),
        "E": (255, 255, 255), "P": (18, 18, 24), "N": (26, 24, 30),
        "M": (255, 248, 238), "U": (155, 45, 58),
        "H": (50, 80, 205), "S": (255, 220, 80), "B": (28, 45, 130),
        "R": (195, 32, 44), "D": (130, 18, 28), "C": (240, 240, 245),
        "G": (252, 252, 252), "W": (215, 195, 150), "Y": (255, 250, 200),
    }
    SPARK_COLORS = [(255, 245, 190), (255, 255, 255), (170, 210, 255), (255, 205, 110)]

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.ART[0]) * self.scale
        self.sprite_h = len(self.ART) * self.scale
        self.new_px = {}
        # Each motes entry: (home_x, home_y, start_x, start_y, born_t, rgb)
        self.motes = []
        self.sparks = []
        self._last_frame = -1

    def capture_new(self, draw_new, new_t):
        """Draw the incoming screen onto a capture canvas; those pixels are what materializes."""
        shot = _Capture(self.width, self.height)
        draw_new(shot, new_t)
        self.new_px = shot.px
        self._build_motes()

    def _build_motes(self):
        r = self.rng
        self.motes = []
        for (x, y), rgb in self.new_px.items():
            # A pixel is summoned once the wand's sweep has passed over its column.
            born = self.RISE_S + self._sweep_t(x) * self.CAST_S
            angle = r.uniform(0, 2 * math.pi)
            dist = r.uniform(6, 22)
            self.motes.append((
                x, y,
                x + math.cos(angle) * dist, y + math.sin(angle) * dist,
                born, rgb,
            ))

    def _sweep_t(self, x):
        """0..1 — how far into the cast this column is reached by the sweep."""
        span = max(1.0, self.width - self.wand_home_x())
        return min(1.0, max(0.0, (x - self.wand_home_x()) / span))

    def wand_home_x(self):
        """The wand tip's resting x: Mickey stands at the left edge."""
        return self.sprite_w * 0.85

    def mickey_y(self, t):
        """His top edge: rises in from below, then holds for the rest of the reveal."""
        top = self.height - self.sprite_h
        if t < self.RISE_S:
            return self.height - ease_out(t / self.RISE_S) * self.sprite_h
        return top

    def wand_tip(self, t):
        """Where the wand's glowing tip is right now, in board pixels."""
        x0 = 0
        y0 = self.mickey_y(t)
        # Tip of the wand in art coordinates (the 'Y' at the top right).
        tip_x = x0 + 22.5 * self.scale
        tip_y = y0 + 0.5 * self.scale
        cast = (t - self.RISE_S) / self.CAST_S
        if cast <= 0:
            # Still rising: the tip is wherever his raised arm has reached.
            return tip_x, self._on_board_y(tip_y)
        cast = min(1.0, cast)
        # Sweeps right and down in an arc across the board.
        x = tip_x + cast * (self.width - tip_x + 2)
        y = tip_y + math.sin(cast * math.pi) * self.height * 0.35
        return x, self._on_board_y(y)

    def _on_board_y(self, y):
        return min(self.height - 1.0, max(0.0, y))

    def _step_sparks(self, t):
        frame = int(t * FPS)
        while self._last_frame < frame:
            self._last_frame += 1
            ft = self._last_frame / FPS
            if self.RISE_S <= ft <= self.RISE_S + self.CAST_S:
                wx, wy = self.wand_tip(ft)
                r = self.rng
                for _ in range(3 * self.scale):
                    self.sparks.append([
                        wx + r.uniform(-1, 1) * self.scale, wy + r.uniform(-1, 1) * self.scale,
                        r.uniform(-0.4, 0.4), r.uniform(-0.2, 0.5),
                        r.randint(8, 18), r.choice(self.SPARK_COLORS),
                    ])
            for s in self.sparks:
                s[0] += s[2]
                s[1] += s[3]
                s[4] -= 1
            self.sparks = [s for s in self.sparks if s[4] > 0]

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        self._step_sparks(t)
        # Everything the screen drew is hidden; only motes that have been summoned show.
        _blackout(canvas, 0, self.width, self.height)
        for hx, hy, sx, sy, born, rgb in self.motes:
            p = (t - born) / self.FLIGHT_S
            if p <= 0:
                continue
            if p >= 1:
                canvas.SetPixel(hx, hy, *rgb)
                continue
            e = ease_out(p)
            px, py = int(round(sx + (hx - sx) * e)), int(round(sy + (hy - sy) * e))
            # Fading up from a white-hot mote into its final colour.
            f = 0.35 + 0.65 * e
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *(int(c + (255 - c) * (1 - e) * 0.7) for c in
                                          (int(rgb[0] * f), int(rgb[1] * f), int(rgb[2] * f))))
        for sx, sy, _, _, life, rgb in self.sparks:
            px, py = int(round(sx)), int(round(sy))
            f = min(1.0, life / 12)
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *(min(255, int(c * f)) for c in rgb))
        self._draw_mickey(canvas, t)
        return True

    def _draw_mickey(self, canvas, t):
        y0 = self.mickey_y(t)
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px = col * self.scale + sx
                        py = int(round(y0 + row * self.scale + sy))
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])


class SlinkyReveal:
    """
    TODO (art): currently reads as a plain dog with a spring stuck between its halves,
    not as Slinky Dog. The head/rear need to be the actual character. Also note the
    2x sprites nearly meet on a 64-row board, leaving almost no visible spring — the
    stretch only really reads on a 32-row board. Trim the art or scale it down there.

    Slinky Dog stretches across the board: his head pushes in from the left while his
    rear stays put, the spring between them pulling out into widely spaced coils, then
    the rear snaps forward and the coil bunches back up. The new screen is revealed in
    the wake of the stretch — the blackout front tracks his nose, not a fixed sweep,
    so the reveal and the elongation are the same motion.
    """

    STRETCH_S, SNAP_S, SETTLE_S = 1.1, 0.5, 0.3
    duration = STRETCH_S + SNAP_S + SETTLE_S

    # Head, facing right: floppy ear, snout with a black nose, red collar at the back
    # where the spring attaches. '.' empty, B brown head, D darker floppy ear, T tan
    # muzzle, K outline, E eye white, P pupil, N nose, R collar, G collar tag.
    HEAD_ART = [
        "....KKKKKK...",
        "..KKBBBBBBKK.",
        ".KDDKBBBBBBBK",
        ".KDDKBEEBBBBK",
        "KRKDDKBEPBTTK",
        "KRKDDKBBBTTTK",
        "KRGDDKBBBTTNK",
        "KRKDDKBBBTTNK",
        "KRKDDDKBBTTTK",
        ".KRKDDKBBKTTK",
        "..KKDDKBBKKK.",
        "...KKKKKKK...",
    ]

    # Rear, facing right (the spring attaches on its right edge): curled tail, haunch,
    # two back legs. '.' empty, B brown, T tan paws, K outline, R collar.
    REAR_ART = [
        "..KK.......",
        ".KBBK......",
        ".KBBK.KKKK.",
        "..KBKKBBBRK",
        "...KBBBBBRK",
        "..KBBBBBBRK",
        ".KBBBBBBBRK",
        ".KBBBBBBBRK",
        ".KBBBKKBBRK",
        ".KTBK..KTBK",
        ".KTTK..KTTK",
        "..KK....KK.",
    ]

    COLORS = {
        "B": (150, 95, 45), "D": (102, 60, 28), "T": (228, 190, 130), "K": (35, 22, 14),
        "E": (250, 250, 250), "P": (25, 20, 20), "N": (28, 24, 24),
        "R": (200, 45, 45), "G": (235, 190, 60),
    }
    COIL_RGB = (205, 210, 220)
    COIL_SHADE_RGB = (115, 124, 138)
    COILS = 7

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.head_w = len(self.HEAD_ART[0]) * self.scale
        self.head_h = len(self.HEAD_ART) * self.scale
        self.rear_w = len(self.REAR_ART[0]) * self.scale
        self.rear_h = len(self.REAR_ART) * self.scale
        # The body's centre line — the height the spring runs along.
        self.body_y = height / 2
        # The rear plants itself just inside the left edge and holds there while the head
        # drives right; the blackout front (his nose) therefore sweeps the whole board.
        # A shade of him is already on the board at t=0 rather than a wasted black frame.
        self.start_x = -self.rear_w * 0.6
        self.anchor_x = 1.0
        self.lead_x = width - self.head_w - self.scale  # nose at the right edge, still on board
        self.end_x = width + self.scale

    def head_x(self, t):
        """Left edge of the head sprite. It leads the whole way, easing out as it arrives."""
        if t < self.STRETCH_S:
            # Half the easing of ease_out: he pushes out steadily rather than leaping to
            # the far edge in the first few frames, so the stretch itself is what you see.
            p = t / self.STRETCH_S
            eased = 0.5 * p + 0.5 * ease_out(p)
            return self.start_x + eased * (self.lead_x - self.start_x)
        # Once stretched to the far edge he only inches on while the rear catches up.
        p = min(1.0, (t - self.STRETCH_S) / (self.SNAP_S + self.SETTLE_S))
        return self.lead_x + p * (self.end_x - self.lead_x)

    def rear_x(self, t):
        """
        Left edge of the rear sprite. It plants itself near the left edge through the
        stretch — that lag is the elongation — then snaps forward to close the gap.
        """
        if t < self.STRETCH_S:
            return self.start_x + ease_out(min(1.0, t / (self.STRETCH_S * 0.4))) * (self.anchor_x - self.start_x)
        snap = min(1.0, (t - self.STRETCH_S) / self.SNAP_S)
        caught_up = self.head_x(t) - self.rear_w + 2 * self.scale
        return self.anchor_x + ease_out(snap) * (caught_up - self.anchor_x)

    def gap(self, t):
        """Spring length in pixels: how far the rear trails the head. Grows, then collapses."""
        return max(0.0, self.head_x(t) - (self.rear_x(t) + self.rear_w))

    def _draw_art(self, canvas, art, x0, y0):
        x0, y0 = int(round(x0)), int(round(y0))
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = x0 + col * self.scale + sx, y0 + row * self.scale + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])

    def _draw_coils(self, canvas, x_from, x_to, cy):
        """
        The spring: a run of vertical ellipse rings between the rear and the head, linked
        top and bottom. Their spacing is the span divided by the ring count, so a long
        span draws them far apart (stretched) and a short one bunches them together
        (compressed). A stretched spring is also drawn narrower, as a real slinky thins
        when it is pulled.
        """
        span = x_to - x_from
        if span <= 1:
            return
        # Bunched when short, thinned out when pulled long — a real slinky narrows as it
        # stretches, and that change in ring height sells the elongation.
        squeeze = max(0.0, min(1.0, 1.0 - span / (self.width * 0.75)))
        ry = max(2.0 * self.scale, self.head_h * (0.22 + 0.16 * squeeze))
        rx = max(1.2 * self.scale, ry * 0.55)
        # Fewer rings when he is bunched up, so a short spring stays legible instead of
        # collapsing into a solid block of wire.
        coils = max(3, min(self.COILS, int(span / (4.0 * self.scale))))
        step = span / coils
        for i in range(coils + 1):
            cx = x_from + i * step
            rgb = self.COIL_RGB if i % 2 == 0 else self.COIL_SHADE_RGB
            # The ring: an ellipse seen almost edge-on, so it reads as a loop of wire.
            for a in range(0, 360, 4):
                rad = math.radians(a)
                for w in range(self.scale):
                    px = int(round(cx + math.cos(rad) * (rx - w * 0.5)))
                    py = int(round(cy + math.sin(rad) * (ry - w * 0.5)))
                    if 0 <= px < self.width and 0 <= py < self.height:
                        canvas.SetPixel(px, py, *rgb)
            # A short link from this ring's top and bottom to the next one, so the coils
            # read as one connected spring rather than a row of loose hoops.
            if i < coils:
                for py, link in ((int(round(cy - ry)), self.COIL_RGB), (int(round(cy + ry)), self.COIL_SHADE_RGB)):
                    for px in range(int(round(cx)), int(round(cx + step)) + 1):
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *link)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        head_x, rear_x = self.head_x(t), self.rear_x(t)
        # Everything ahead of his nose is still black: the new screen is revealed in the
        # wake of the stretch, so the reveal front and the elongation are one motion.
        _blackout(canvas, int(round(head_x + self.head_w)), self.width, self.height)
        self._draw_coils(canvas, rear_x + self.rear_w - self.scale, head_x + self.scale, self.body_y)
        self._draw_art(canvas, self.REAR_ART, rear_x, self.body_y - self.rear_h / 2)
        self._draw_art(canvas, self.HEAD_ART, head_x, self.body_y - self.head_h / 2)
        return True


class BaymaxReveal:
    """
    Baymax inflates up from the bottom edge over the already-revealed screen,
    settles with a wobble, blinks and waves, then deflates away. Unlike the other
    characters he is drawn procedurally rather than from ASCII art: inflating means
    scaling him smoothly from a flat puddle to full size, and fixed art can only be
    scaled in whole-pixel steps, which reads as popping rather than filling with air.
    """

    INFLATE_S, HOLD_S, DEFLATE_S = 0.9, 2.2, 0.7
    duration = INFLATE_S + HOLD_S + DEFLATE_S

    WHITE = (250, 250, 252)
    SHADE = (150, 158, 172)
    EDGE = (86, 92, 108)
    DARK = (12, 12, 16)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        # Full-size half-width/half-height of each part, in pixels, at inflation 1.0.
        # Height drives every radius so his proportions are identical on a 32- and a
        # 64-row board; he just fills less of the width on the short one. Width only
        # clamps him, so a narrow board can't push his arms off the edge.
        unit = min(height * 0.95, width * 0.88)
        self.body_ry = unit * 0.33
        self.body_rx = unit * 0.26
        self.head_rx = self.body_rx * 0.82
        self.head_ry = self.body_ry * 0.50
        self.cx = width / 2.0

    def inflation(self, t):
        """0 (a flat deflated puddle) up to 1 (full size), wobbling as he settles."""
        if t < self.INFLATE_S:
            return 0.06 + 0.94 * ease_out(t / self.INFLATE_S)
        if t < self.INFLATE_S + self.HOLD_S:
            since = t - self.INFLATE_S
            # A decaying overshoot right after he fills, then a slow idle breath.
            wobble = math.exp(-since * 3.2) * 0.10 * math.sin(since * 11.0)
            breathe = 0.012 * math.sin(since * 2.0)
            return 1.0 + wobble + breathe
        deflating = (t - self.INFLATE_S - self.HOLD_S) / self.DEFLATE_S
        return max(0.0, 1.0 - ease_out(deflating))

    def eye_open(self, t):
        """1 wide open, 0 fully shut — a slow blink every couple of seconds."""
        since = t - self.INFLATE_S
        if since < 0:
            return 1.0
        phase = since % 2.0
        return abs(phase - 0.08) / 0.08 if phase < 0.16 else 1.0

    def wave(self, t):
        """-1..1 for his raised right arm, 0 when it is back at his side."""
        since = t - self.INFLATE_S - 0.35
        if since < 0 or since > 1.6:
            return 0.0
        return math.sin(since * 7.0)

    def _blob(self, px, cx, cy, rx, ry, shade=True):
        """One filled ellipse, rimmed and shaded so it reads as soft, not as a slab."""
        if rx < 0.7 or ry < 0.7:
            return
        for y in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
            for x in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d > 1.0:
                    continue
                # A grey rim all round, and a grey crescent inside the lower right,
                # which gives him a light source instead of a flat white silhouette.
                if d > 0.82:
                    px[(x, y)] = self.EDGE
                elif shade and d > 0.52 and dx + dy > 0.55:
                    px[(x, y)] = self.SHADE
                else:
                    px[(x, y)] = self.WHITE

    def _face(self, px, cy, rx, open_frac):
        """Two small dark eyes joined by a single 1px line — the instantly-Baymax bit."""
        fy = int(round(cy))
        er = max(1, int(round(rx * 0.12)))
        # Keep a clear white gap between the eyes, or the face smears into one bar.
        eye_dx = max(er + 3, int(round(rx * 0.44)))
        lx, rx_ = int(round(self.cx)) - eye_dx, int(round(self.cx)) + eye_dx
        for x in range(lx, rx_ + 1):
            px[(x, fy)] = self.DARK
        # A blink squashes the eyes vertically; the line between them stays put.
        eh = max(0, int(round((er + 1) * open_frac)))
        for ex in (lx, rx_):
            for dy in range(-eh, eh + 1):
                for dx in range(-er, er + 1):
                    if (dx / er) ** 2 + (dy / max(1, eh)) ** 2 <= 1.0:
                        px[(ex + dx, fy + dy)] = self.DARK

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        inf = self.inflation(t)
        if inf <= 0.02:
            return True
        # Parts are drawn into a dict first so later blobs paint over earlier ones
        # (arms behind body, face over head) before anything reaches the canvas.
        px = {}
        # His base stays pinned to the bottom edge and he grows upward from it,
        # which is what sells air going in rather than a sprite sliding up.
        body_ry = self.body_ry * inf
        # Deflated he is wide and flat; inflated he is nearly round.
        squash = 1.0 + 0.55 * (1.0 - min(1.0, inf))
        body_rx = self.body_rx * (0.35 + 0.65 * inf) * squash
        body_cy = self.height - body_ry

        head_ry = self.head_ry * inf
        head_rx = self.head_rx * (0.4 + 0.6 * inf) * squash
        # The head overlaps the body just enough to fuse into one soft mass while
        # leaving the whole face clear of the shoulders.
        head_cy = body_cy - body_ry - head_ry * 0.62

        arm_ry, arm_rx = body_ry * 0.46, body_rx * 0.36
        w = self.wave(t)
        for side in (-1, 1):
            ax = self.cx + side * body_rx * 0.92
            ay = body_cy - body_ry * 0.25
            if side == 1 and w:
                ay -= arm_ry * 1.1 * abs(w)
                ax += arm_rx * 0.5 * w
            self._blob(px, ax, ay, arm_rx, arm_ry)

        self._blob(px, self.cx, body_cy, body_rx, body_ry)
        # The head takes no interior shading: the face needs a clean white field
        # behind it or the eyes and line smear into grey at this resolution.
        self._blob(px, self.cx, head_cy, head_rx, head_ry, shade=False)
        if head_rx >= 3.0 and head_ry >= 1.5:
            # Centre the face on the part of the head that clears the body, not on
            # the head ellipse, whose lower half is buried in the shoulders.
            self._face(px, (head_cy - head_ry + body_cy - body_ry) / 2, head_rx, self.eye_open(t))

        for (x, y), rgb in px.items():
            if 0 <= x < self.width and 0 <= y < self.height:
                canvas.SetPixel(x, y, *rgb)
        return True


class GenieReveal:
    """
    TODO (art): the lamp needs work — it doesn't read as a lamp at this size. Genie
    himself is good.

    Genie erupts from his lamp and flies off with the new screen in his wake. Not a
    FlyByReveal: the first half of the run is an emerge, where he has no flight path at
    all -- a plume of smoke pours out of the lamp's spout and he scales up out of it from
    a point at the spout to full size. Only then does he cross the board, so the blackout
    front stays at 0 (whole screen dark, lamp and smoke on black) until he takes off.

    His trail is smoke rather than the point-like dust the fly-bys leave: each puff is a
    soft disc that grows and fades, drawn additively over whatever is already on the
    canvas so the revealed screen shows through it instead of being punched out.
    """

    EMERGE_S, FLY_S = 1.6, 2.0
    duration = EMERGE_S + FLY_S

    # The lamp he comes out of: a squat gold vessel with a spout at the top left.
    # '.' empty, K outline, Y gold body.
    LAMP_ART = [
        "....K....",
        "...KYK...",
        "KKKYYYKK.",
        "KYYYYYYKK",
        "KYYYYYYYK",
        ".KKKKKKK.",
    ]

    # Genie facing forward: swept-back black topknot, wide blue face, gold hoop earrings,
    # a grin over a pointed black goatee, folded arms in gold cuffs, and -- instead of
    # legs -- a wispy tail that tapers away into smoke.
    # '.' empty, H topknot black, J topknot/goatee highlight, K body outline (a deep blue,
    # not black, so the silhouette still reads on an unlit board), B blue skin, N nose
    # shading, E eye white, W eye highlight, P pupil, U teeth, T tongue, M goatee,
    # G earring gold, C cuff gold, S smoke tail, Y lamp gold.
    ART = [
        ".............JHHJ.......",
        "............JHHHHJ......",
        "...........JHHHHHJ......",
        "...........JHHHHJ.......",
        "..........JHHHHJ........",
        "..........JHHHJ.........",
        "......KKKKKHHKKKK.......",
        ".....KBBBBBJJBBBBK......",
        "....KBBBBBBBBBBBBBK.....",
        "...KBBBBBBBBBBBBBBBK....",
        "GGGKBBEEEBBBBBEEEBBK.GGG",
        "GGGKBEWPPEBBBEWPPEBKGGG.",
        "GGGKBEWPPEBNBEWPPEBKGGG.",
        "...KBBEEEBBNNBEEEBBK....",
        "...KBBBBBBBNNNBBBBBK....",
        "...KBBBBUUUUUUUUBBBK....",
        "....KBBBBTTTTTTBBBK.....",
        ".....KBBBJMMMMJBBBK.....",
        "......KKBJMMMMMJBKK.....",
        ".......KKJMMMMMJKK......",
        "..KKKKKKKKJMMMJKKKKKKK..",
        ".KBBBBBBKKKJMJKKKKBBBBBK",
        "KBBBBBBBKBBBJBBBKBBBBBBK",
        "KCCCCCCKBBBBBBBBBKCCCCCK",
        "KCCCCCCKBBBBBBBBBKCCCCCK",
        ".KBBBBKKBBBBBBBBBKKBBBBK",
        "..KKKK..KBBBBBBBK..KKKK.",
        ".........KBSSSBK........",
        "..........KSSSK.........",
        ".........KSSSSK.........",
        "..........KSSK..........",
    ]
    COLORS = {
        "K": (20, 60, 120), "H": (16, 16, 30), "J": (70, 72, 105), "B": (60, 150, 235),
        "N": (42, 115, 200), "E": (250, 250, 255), "W": (250, 250, 255), "P": (18, 18, 32),
        "U": (252, 250, 245), "T": (200, 60, 80), "M": (16, 16, 30),
        "G": (250, 205, 70), "C": (250, 205, 70), "Y": (250, 205, 70), "S": (105, 180, 242),
    }
    SMOKE_COLORS = [(120, 160, 235), (150, 120, 225), (95, 130, 210), (185, 165, 245)]

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.ART[0]) * self.scale
        self.sprite_h = len(self.ART) * self.scale
        self.lamp_w = len(self.LAMP_ART[0]) * self.scale
        self.lamp_h = len(self.LAMP_ART) * self.scale
        self.lamp_x = 2 * self.scale
        self.lamp_y = height - self.lamp_h
        # Each puff: [x, y, vx, vy, frames_left, rgb, radius]
        self.puffs = []
        self.last_frame = -1

    def spout(self):
        """Where the smoke leaves the lamp, and the point Genie scales up out of."""
        return self.lamp_x + 4.5 * self.scale, self.lamp_y + 0.5 * self.scale

    def grow(self, t):
        """0 (not yet formed) to 1 (full size). Smoke pours alone for the first third."""
        if t >= self.EMERGE_S:
            return 1.0
        return ease_out(max(0.0, t - self.EMERGE_S * 0.35) / (self.EMERGE_S * 0.65))

    def position(self, t):
        """The sprite's top-left at full size: parked over the lamp, then crossing right."""
        sx, sy = self.spout()
        # He is nearly as big as the board, so his resting pose is clamped fully onto it
        # rather than centred on the lamp, which would hang half of him off the left edge.
        home_x = max(0.0, min(sx - self.sprite_w / 2, self.width - self.sprite_w))
        home_y = max(0.0, min(sy - self.sprite_h, self.height - self.sprite_h))
        if t < self.EMERGE_S:
            return home_x, home_y
        p = (t - self.EMERGE_S) / self.FLY_S
        # Accelerating away, so he lingers on board before whipping off the right edge.
        x = home_x + (p * p * 0.35 + p * 0.65) * (self.width + self.sprite_w - home_x)
        y = home_y - math.sin(p * math.pi) * self.height * 0.18
        return x, max(0.0, min(y, self.height - self.sprite_h))

    def reveal_x(self, t):
        """
        The blackout front. It tracks his body but is kept a little behind his leading
        edge, and spans the full width over the fly — his sprite is wide enough (48px of
        a 64px board at 2x) that following his centre would finish the sweep well before
        he has left, leaving him flying over an already-revealed screen.
        """
        if t < self.EMERGE_S:
            return 0
        p = min(1.0, (t - self.EMERGE_S) / self.FLY_S)
        x, _ = self.position(t)
        return int(min(x + self.sprite_w * 0.35, p * (self.width + 1)))

    def spawn(self, t):
        """Smoke for this frame: a plume rising from the spout, or a wake behind him."""
        r = self.rng
        if t < self.EMERGE_S:
            sx, sy = self.spout()
            return [[sx + r.uniform(-1, 1) * self.scale, sy,
                     r.uniform(-0.5, 0.5), r.uniform(-1.2, -0.5) * self.scale,
                     r.randint(14, 26), r.choice(self.SMOKE_COLORS), r.uniform(0.4, 1.0)]
                    for _ in range(3 * self.scale)]
        x, y = self.position(t)
        return [[x + r.uniform(0.25, 0.65) * self.sprite_w,
                 y + self.sprite_h * r.uniform(0.6, 1.0),
                 r.uniform(-0.9, -0.2) * self.scale, r.uniform(-0.25, 0.25),
                 r.randint(16, 28), r.choice(self.SMOKE_COLORS), r.uniform(0.7, 1.6)]
                for _ in range(4 * self.scale)]

    def _step_puffs(self, t):
        frame = int(t * FPS)
        while self.last_frame < frame:
            self.last_frame += 1
            ft = self.last_frame / FPS
            if ft < self.duration:
                self.puffs.extend(self.spawn(ft))
            for p in self.puffs:
                p[0] += p[2]
                p[1] += p[3]
                p[3] *= 0.92  # the rise slows as the puff loses its push
                p[4] -= 1
                p[6] += 0.06  # and it swells as it disperses
            self.puffs = [p for p in self.puffs if p[4] > 0]

    def _draw_puffs(self, canvas):
        """
        Soft discs, brightest at the centre, added to what is already on the canvas -- a
        thinning puff lets the screen behind it show through instead of blacking it out.
        """
        under = dict(getattr(canvas, "px", {}))
        for cx, cy, _, _, life, rgb, rad in self.puffs:
            f = min(1.0, life / 18.0)
            rr = rad * self.scale
            for x in range(int(math.floor(cx - rr)), int(math.ceil(cx + rr)) + 1):
                for y in range(int(math.floor(cy - rr)), int(math.ceil(cy + rr)) + 1):
                    if not (0 <= x < self.width and 0 <= y < self.height):
                        continue
                    d = math.hypot(x - cx, y - cy)
                    if d > rr:
                        continue
                    g = f * (1.0 - d / (rr + 0.001)) ** 0.7
                    if g <= 0.05:
                        continue
                    base = under.get((x, y), (0, 0, 0))
                    canvas.SetPixel(x, y, *(min(255, int(b + c * g)) for b, c in zip(base, rgb)))

    def overlay(self, canvas, t):
        self._step_puffs(t)
        if t < self.duration:
            # Nothing is revealed while he is still forming: lamp and smoke on black.
            _blackout(canvas, self.reveal_x(t), self.width, self.height)
        self._draw_puffs(canvas)
        if t < self.duration:
            if t < self.EMERGE_S:
                self._draw_art(canvas, self.LAMP_ART, self.lamp_x, self.lamp_y)
            self._draw_genie(canvas, t)
        return t < self.duration or bool(self.puffs)

    def _draw_art(self, canvas, art, x0, y0):
        x0, y0 = int(round(x0)), int(round(y0))
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = x0 + col * self.scale + sx, y0 + row * self.scale + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])

    def _draw_genie(self, canvas, t):
        """
        Draw him at `grow(t)` of full size. Below full size every cell is pulled toward
        the spout by that factor, so he swells out of the smoke rather than fading in.
        """
        g = self.grow(t)
        if g <= 0.02:
            return
        x0, y0 = self.position(t)
        ax, ay = self.spout()
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                bx, by = x0 + col * self.scale, y0 + row * self.scale
                if g < 1.0:
                    bx = ax + (bx + self.scale / 2 - ax) * g
                    by = ay + (by + self.scale / 2 - ay) * g
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = int(round(bx)) + sx, int(round(by)) + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])


TRANSITIONS = {
    "wipe": Wipe, "tink": TinkReveal, "buzz": BuzzReveal,
    "figment": FigmentReveal, "stitch": StitchReveal, "ralph": RalphReveal,
    "mickey": MickeyReveal, "slinky": SlinkyReveal, "baymax": BaymaxReveal,
    "dumbo": DumboReveal,
    "genie": GenieReveal,
}


def show_screen(matrix, draw_screen, hold_s, transition="wipe", rng=None):
    """
    Play a screen for hold_s seconds: sweep the previous screen away, reveal this one,
    then let it animate. draw_screen(canvas, t) draws the screen t seconds after the
    reveal finished (t is 0 during the reveal) and returns True while it is still moving.
    """
    prev = _last_screen.get(id(matrix))
    reveal = TRANSITIONS[transition](matrix.width, matrix.height, rng)
    cover_s = COVER_S if prev else 0.0
    last_t = [0.0]

    # A reveal that shatters the old screen needs its pixels; hand it the previous
    # draw function and let it keep the sweep from running.
    if getattr(reveal, "wants_prev", False) and prev:
        reveal.capture_prev(*prev)
        cover_s = 0.0

    # A reveal that materializes the new screen needs its pixels up front; it draws
    # them itself (over a blackout) instead of uncovering what draw_screen painted.
    if getattr(reveal, "wants_new", False):
        reveal.capture_new(draw_screen, 0.0)

    def frame(canvas, t):
        if t < cover_s:
            # Redraw the previous screen exactly as it was last shown, then sweep it away.
            prev_draw, prev_t = prev
            prev_draw(canvas, prev_t)
            x = int(ease_out(t / cover_s) * (matrix.width + 1))
            _blackout(canvas, 0, x, matrix.height)
            _edge(canvas, x, matrix.width, matrix.height)
            return True
        t_reveal = t - cover_s
        last_t[0] = max(0.0, t_reveal - reveal.duration)
        moving = draw_screen(canvas, last_t[0])
        revealing = reveal.overlay(canvas, t_reveal)
        return bool(moving or revealing)

    run_frames(matrix, frame, hold_s)
    _last_screen[id(matrix)] = (draw_screen, last_t[0])
