import math
import random
import time

from driver import graphics
from utils import debug

from display.capture import Capture, capture_screen
from display.network import draw_if_offline

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
    # Every frame on the board passes through here, so the badge sits on top of all of them.
    draw_if_offline(canvas)
    _canvases[id(matrix)] = matrix.SwapOnVSync(canvas)
    return _canvases[id(matrix)]


def forget_screen(matrix):
    """The next screen should reveal from black rather than cover whatever played last."""
    _last_screen.pop(id(matrix), None)


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def run_frames(matrix, draw_frame, duration_s, fps=FPS):
    """
    Call draw_frame(canvas, t) each frame for duration_s; once it returns False the image
    is static and we sleep out the rest. Returns (frames drawn, seconds spent animating)
    so callers can see how close a board gets to `fps`.
    """
    frame_time = 1.0 / fps
    frames = int(duration_s * fps)
    canvas = frame_canvas(matrix)
    began = time.monotonic()
    drawn = 0

    def animated_s():
        # A board that keeps up spends a whole frame slot on its last frame too.
        return max(time.monotonic() - began, drawn * frame_time)

    for i in range(frames):
        start = time.monotonic()
        # A slow board drops frames rather than stretching the screen past duration_s.
        if start - began >= duration_s:
            return drawn, animated_s()
        canvas.Clear()
        animating = draw_frame(canvas, i / fps)
        canvas = present(matrix, canvas)
        drawn += 1
        if not animating:
            spent = animated_s()
            time.sleep(max(0.0, duration_s - (time.monotonic() - began)))
            return drawn, spent
        remaining = frame_time - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)
    return drawn, animated_s()


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
    """
    Tinker Bell bobs across leaving a drifting trail of pixie dust. Spaceship Earth's
    landmark borrows her too (at 1x on both boards), so there's one Tink.
    """

    # Wings either side, her yellow bun, a face, the green dress and legs; 9x8 on 64x32 and
    # doubled on 64x64 like the other fly-bys. It replaced a 5x5 Tink that read as a
    # glowing glyph rather than a fairy. '.' empty, W wing, Y hair/glow, S skin, G dress.
    art = [
        "....Y....",
        "WW.YYY.WW",
        "WWWYSYWWW",
        "WWW.S.WWW",
        ".WWGGGWW.",
        "...GGG...",
        "..GGGGG..",
        "...S.S...",
    ]
    colors = {"W": (170, 220, 255), "Y": (255, 230, 110), "S": (255, 205, 170), "G": (60, 220, 90)}
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
    """
    Buzz Lightyear launches, to infinity: drawn front-on from a photo of the toy, he rises
    from below the board on a rocket flame under his feet, hovers while his wings snap open
    with a flash at their tips (his wing-release button), then blasts off the top. The new
    screen is uncovered from the bottom up behind him. Front-on he read as a cutout sliding
    sideways when he crossed the board like the other fly-bys; rising, facing us is natural.
    """

    RISE_S, HOVER_S, BLAST_S = 0.5, 0.3, 0.8
    duration = RISE_S + HOVER_S + BLAST_S
    FLASH_S = 0.15
    HOVER_AT = 0.55  # his centre while he hovers, as a fraction of the board's height
    SIZES = {
        "big": [
            "......DDD......",
            ".....DPPPD.....",
            ".....PSSSP.....",
            ".....PSSSP.....",
            "......PSP......",
            "RWRWRWGGGWRWRWR",
            "PPPPPWWBWWPPPPP",
            ".PPPPWGWGWPPPP.",
            "....WWWWWWW....",
            "....W.KKK.W....",
            ".....WW.WW.....",
            ".....WW.WW.....",
            ".....GP.PG.....",
        ],
        "small": [
            "....DDD....",
            "....PSP....",
            "....PSP....",
            "RWRWGGGWRWR",
            "PPPPWBWPPPP",
            ".PP.WGW.PP.",
            "....WWW....",
            "....W.W....",
            "....G.G....",
        ],
    }
    # Big on 64x32; on 64x64 the small one, doubled (22x18): the big one doubled is 30x26
    # and fills too much of the board. Set SIZE to "big" or "small" to pin one everywhere.
    SIZE = None
    art = SIZES["big"]
    colors = {"D": (130, 180, 235), "P": (160, 90, 235), "S": (255, 205, 170), "R": (235, 45, 45),
              "W": (235, 235, 245), "G": (60, 210, 60), "B": (60, 130, 255), "K": (70, 70, 80)}
    flame_colors = [(255, 240, 150), (255, 170, 30), (255, 90, 20), (230, 40, 20)]
    FLASH_RGB = (255, 250, 220)

    def __init__(self, width, height, rng=None):
        self.art = self.SIZES[self.SIZE or ("small" if height >= 64 else "big")]
        super().__init__(width, height, rng)
        # Wings tucked behind him: only what's within a column of his body shows.
        body = [c for row in self.art for c, ch in enumerate(row) if ch in "SDBK"]
        lo, hi = min(body) - 1, max(body) + 1
        self.folded = ["".join(ch if lo <= c <= hi else "." for c, ch in enumerate(row)) for row in self.art]
        self.wing_tips = [(c, r) for r, row in enumerate(self.art) for c, ch in enumerate(row)
                          if ch in "PR" and (c == 0 or c == len(row) - 1 or row[c - 1] == "." or row[c + 1] == ".")
                          and not lo <= c <= hi]

    def wings_open(self, t):
        return t >= self.RISE_S

    def position(self, t):
        """Top-left of his sprite: up from below the board, a hover, then accelerating off the top."""
        x = (self.width - self.sprite_w) / 2
        hover = self.height * self.HOVER_AT - self.sprite_h / 2
        if t < self.RISE_S:
            start = self.height
            return x, start + (hover - start) * ease_out(t / self.RISE_S)
        if t < self.RISE_S + self.HOVER_S:
            return x, hover
        p = min(1.0, (t - self.RISE_S - self.HOVER_S) / self.BLAST_S)
        return x, hover + (-self.sprite_h - hover) * p * p

    def spawn(self, x, y):
        """Rocket flame from under his feet, streaming down; heavier once he blasts off."""
        r = self.rng
        blasting = y < self.height * self.HOVER_AT - self.sprite_h / 2 - 0.5
        feet = y + self.sprite_h
        return [[x + self.sprite_w * r.uniform(0.38, 0.62), feet,
                 r.uniform(-0.25, 0.25) * self.scale, r.uniform(0.4, 1.0) * self.scale,
                 r.randint(10, 18), r.choice(self.flame_colors)]
                for _ in range((6 if blasting else 4) * self.scale)]

    def overlay(self, canvas, t):
        self._step_particles(t)
        if t < self.duration:
            # Uncovered from the bottom up: everything above his feet is still dark.
            _, y = self.position(t)
            black = graphics.Color(0, 0, 0)
            for row in range(0, min(self.height, int(y + self.sprite_h))):
                graphics.DrawLine(canvas, 0, row, self.width - 1, row, black)
        for px, py, _, _, life, rgb in self.particles:
            f = min(1.0, life / 12)
            px, py = int(round(px)), int(round(py))
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *(int(c * f) for c in rgb))
        if t < self.duration:
            self._draw_sprite(canvas, t)
        return t < self.duration or bool(self.particles)

    def _draw_sprite(self, canvas, t):
        art = self.art
        if not self.wings_open(t):
            self.art = self.folded
        super()._draw_sprite(canvas, t)
        self.art = art
        since = t - self.RISE_S
        if 0 <= since < self.FLASH_S:
            # The snap: a burst of light off each wing tip.
            x0, y0 = (int(round(v)) for v in self.position(t))
            reach = 1 + int(3 * since / self.FLASH_S)
            for c, r in self.wing_tips:
                cx, cy = x0 + c * self.scale + self.scale // 2, y0 + r * self.scale + self.scale // 2
                for dx, dy in ((reach, 0), (-reach, 0), (0, reach), (0, -reach)):
                    px, py = cx + dx * self.scale, cy + dy * self.scale
                    if 0 <= px < self.width and 0 <= py < self.height:
                        canvas.SetPixel(px, py, *self.FLASH_RGB)


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


class TronReveal(FlyByReveal):
    """
    Two TRON light cycles race left to right, blue across the top of the board and red
    along the bottom, red starting a length behind and closing to level by the far edge.
    Each lays a solid light trail at wheel height; everything behind the trailing bike, top
    to bottom, is already the new ride. The trails hang on a beat after the bikes are gone,
    then de-rez.
    """

    CROSS_S, HOLD_S, FADE_S = 1.1, 0.2, 0.4
    duration = CROSS_S + HOLD_S + FADE_S
    SCALE = 1  # 1x on both boards: doubled, one bike filled half of a 64x64 board
    RED_LAG = 10  # how far behind red starts, in pixels; it's level by the end

    # Side view, nose right, from the user's mockup (mirrored): ring wheels, a tall fin over
    # the rear wheel with a lit square front edge, a small rounded cowl over the front one,
    # and a low body between whose light stripe climbs into the cowl. Two ring wheels under a
    # plain bar read as a pair of glasses; the fin and cowl are what make it a light cycle.
    # The shell is a lifted charcoal, since LEDs draw black as off. '.' empty, C wheel ring,
    # D wheel's inside, B shell, H highlight, L light stripe.
    art = [
        "........BBHHH.................",
        "......BBBBBBH.................",
        "....BBBBBBBBH......BBBBBB.....",
        "...CCCCBBBBBH.....BLBBBCCCC...",
        "..CCDDCCBBBBH.....LBBBCCDDCC..",
        ".CDDDDDDCBBBBBBBBLBBBCDDDDDDC.",
        ".CDDDDDDCLLLLLLLLBBBBCDDDDDDC.",
        ".CDDDHDDCCBBBBBBBBB.CCDDDHDDC.",
        ".CDDDDDDC............CDDDDDDC.",
        ".CDDDDDDC............CDDDDDDC.",
        "..CCDDCC..............CCDDCC..",
        "...CCCC................CCCC...",
    ]
    TRAIL_ROWS = (5, 10)  # the art rows the trail spans, its edges one pixel darker
    BLUE = {"C": (0, 200, 255), "D": (16, 18, 24), "B": (38, 44, 54), "H": (95, 105, 118),
            "L": (120, 240, 255)}
    RED = {"C": (255, 45, 25), "D": (24, 16, 16), "B": (54, 38, 38), "H": (118, 100, 95),
           "L": (255, 150, 110)}
    TRAILS = {"blue": ((0, 200, 230), (0, 110, 210)), "red": ((235, 35, 20), (150, 15, 10))}
    colors = BLUE  # the sprite editor previews the art in blue

    def __init__(self, width, height, rng=None):
        super().__init__(width, height, rng)
        self.scale = self.SCALE
        self.sprite_w, self.sprite_h = len(self.art[0]) * self.scale, len(self.art) * self.scale

    def bikes(self, t):
        """[(name, x, y)] for the blue bike on top and the red one on the bottom at time t."""
        # Linear, like light cycles holding their lines; both tails clear the right edge at CROSS_S.
        p = min(t, self.CROSS_S) / self.CROSS_S
        x = -self.sprite_w + p * (self.width + self.sprite_w + self.RED_LAG)
        return [("blue", x, 0), ("red", x - self.RED_LAG * (1 - p), self.height - self.sprite_h)]

    def position(self, t):
        _, x, y = self.bikes(t)[0]
        return x, y

    def spawn(self, x, y):
        return []

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        bikes = [(name, int(round(x)), y) for name, x, y in self.bikes(t)]
        if t < self.CROSS_S:
            _blackout(canvas, min(x for _, x, _ in bikes) + self.sprite_w, self.width, self.height)
        # The trails de-rez rather than dimming: dimming would darken the new screen under
        # them (a Pi canvas can't be read back to blend with), so each pixel drops out whole,
        # in a fixed scattered order.
        left = 1.0 if t < self.CROSS_S + self.HOLD_S else 1.0 - (t - self.CROSS_S - self.HOLD_S) / self.FADE_S
        for name, x, y in bikes:
            core, edge = self.TRAILS[name]
            top, bottom = (y + r * self.scale for r in self.TRAIL_ROWS)
            for py in range(top, bottom):
                rgb = edge if py in (top, bottom - 1) else core
                for px in range(0, min(self.width, x + self.scale)):
                    if ((px * 73856093) ^ (py * 19349663)) % 1000 < left * 1000:
                        canvas.SetPixel(px, py, *rgb)
        if t < self.CROSS_S:
            for name, x, y in bikes:
                self._draw_bike(canvas, x, y, self.BLUE if name == "blue" else self.RED)
        return True

    def _draw_bike(self, canvas, x0, y0, colors):
        for row, line in enumerate(self.art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = x0 + col * self.scale + sx, y0 + row * self.scale + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *colors[kind])


class PeekReveal:
    """
    A character pops up from the bottom edge over the already-revealed screen, looks
    around, and ducks back down — no blackout, no particle trail, no travel across
    the board. Subclasses supply the art and how far up "peeking" rises.
    """

    duration = 0
    over_screen = True
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


_Capture = Capture  # the recording canvas; see display/capture.py


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

    # Ralph mid-swing: spiky dark-red hair, big pink fists, red shirt, overalls.
    # '.' empty, H hair, F face/skin, E eye, A teeth, M mouth, S shirt, O overalls,
    # B buckle, K outline.
    ART = [
        ".......KHKHKHKHK.......",
        ".......KHHHHHHHK.......",
        "KKKKKK.KHHHHHHHK.KKKKKK",
        "KFFFFK.KHFFFFFHK.KFFFFK",
        "KFFFFK.KFFEFEFFK.KFFFFK",
        "KFFFFK.KFFFFFFFK.KFFFFK",
        ".KFFFK.KFFAAAFFK.KFFFK.",
        "..KFFK.KKFFFFFKK.KFFK..",
        "..KFFKKKKSSSSSK..KFFK..",
        "..KFFFFFSSSSSSSFFFFFK..",
        "...KFFFFSSSSSSSFFFFK...",
        "....KSSSSSSSSSSSSSK....",
        "....KSSSSOBBBOSSSSK....",
        ".....KSSOOBBBOOSSK.....",
        ".....KOOOOOOOOOOOK.....",
        ".....KOOOOOOOOOOOK.....",
        ".....KOOOOKKKOOOOK.....",
        ".....KFFFK...KFFFK.....",
        ".....KFFK.....KFFK.....",
        ".....KKKK.....KKKK.....",
    ]
    COLORS = {
        "H": (140, 25, 30),
        "F": (240, 180, 160),
        "E": (20, 20, 25),
        "M": (90, 30, 35),
        "S": (200, 40, 45),
        "O": (255, 220, 170),
        "B": (190, 120, 50),
        "K": (25, 15, 20),
        "A": (250, 250, 250),
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
        """Redraw the old screen in memory; those pixels become the debris."""
        self.prev_px = capture_screen(prev_draw, prev_t, self.width, self.height)

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
        """Draw the incoming screen in memory; those pixels are what materializes."""
        self.new_px = capture_screen(draw_new, new_t, self.width, self.height)
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


class BaymaxReveal:
    """
    Baymax inflates up from the bottom edge over the already-revealed screen,
    settles with a wobble, blinks and waves, then deflates away. Unlike the other
    characters he is drawn procedurally rather than from ASCII art: inflating means
    scaling him smoothly from a flat puddle to full size, and fixed art can only be
    scaled in whole-pixel steps, which reads as popping rather than filling with air.
    """

    over_screen = True
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


class MikeReveal:
    """
    Mike Wazowski pops up from the bottom edge over the ride screen, blinks, looks left
    and right, grins wider, then throws his arms up in a scare and ducks away. Drawn in
    code like Baymax: a round body, one big eye with a lid that closes and a pupil that
    moves, and a mouth that opens are a handful of numbers here but a pile of poses as art.
    """

    over_screen = True
    UP_S, DOWN_S = 0.4, 0.35
    BLINK = (0.55, 0.85)  # the lid shuts and reopens
    LOOK = (0.95, 1.85)  # left, then right, then back to the middle
    GRIN = (1.85, 2.15)  # the grin widens
    SCARE = (2.25, 2.95)  # arms up, mouth wide
    duration = SCARE[1] + DOWN_S
    SIZES = {32: 8, 64: 12}  # his body's half-width, by board height
    R = None  # pins the half-width, for previews

    GREEN = (140, 205, 40)
    LIGHT = (180, 230, 80)
    DARK = (95, 150, 30)
    EDGE = (45, 85, 20)
    WHITE = (245, 245, 240)
    IRIS = (30, 165, 150)
    PUPIL = (15, 25, 25)
    HORN = (205, 195, 170)
    MOUTH = (45, 15, 20)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.r = self.R or self.SIZES[64 if height >= 64 else 32]
        self.ry = self.r * 1.08
        self.cx = round(self.rng.uniform(0.3, 0.7) * width)
        # At full rise his body's bottom sits just above the edge, his feet out of frame.
        self.up_cy = height - self.ry - 2
        self.hidden_cy = height + self.ry + 4

    def rise(self, t):
        if t < self.UP_S:
            return ease_out(t / self.UP_S)
        down = t - (self.duration - self.DOWN_S)
        return 1.0 if down < 0 else max(0.0, 1.0 - ease_out(down / self.DOWN_S))

    def lid(self, t):
        """0 open, 1 shut."""
        a, b = self.BLINK
        if not a <= t < b:
            return 0.0
        return min(1.0, 1.6 * (1 - abs(2 * (t - a) / (b - a) - 1)))

    def look(self, t):
        """-1 his pupil hard left, 1 hard right, 0 in the middle."""
        a, b = self.LOOK
        if not a <= t < b:
            return 0.0
        p = (t - a) / (b - a)
        if p < 0.1:
            return -p / 0.1
        if p < 0.45:
            return -1.0
        if p < 0.6:
            return -1.0 + 2 * (p - 0.45) / 0.15
        if p < 0.9:
            return 1.0
        return 1.0 - (p - 0.9) / 0.1

    def grin(self, t):
        """0 his everyday grin, 1 at its widest."""
        a, b = self.GRIN
        return max(0.0, min(1.0, (t - a) / (b - a)))

    def scaring(self, t):
        return self.SCARE[0] <= t < self.SCARE[1]

    def pixels(self, t):
        """Every pixel he covers at time t, {(x, y): rgb}, clipped to the board."""
        rise = self.rise(t)
        if rise <= 0 or t >= self.duration:
            return {}
        cy = self.hidden_cy + (self.up_cy - self.hidden_cy) * rise
        cx = self.cx
        scare = self.scaring(t)
        if scare:
            # He jumps up at the scare and shakes for a moment.
            since = t - self.SCARE[0]
            cy -= self.r * 0.25 * ease_out(min(1.0, since / 0.12))
            if since < 0.3:
                cx += 1 if int(since * 20) % 2 else -1
        body = self._body(scare, self.look(t), self.lid(t), self.grin(t))
        oy = int(round(cy))
        return {(cx + x, oy + y): rgb for (x, y), rgb in body.items()
                if 0 <= cx + x < self.width and 0 <= oy + y < self.height}

    def _body(self, scare, look, lid, grin):
        """Mike centred on (0, 0), later parts painting over earlier ones."""
        r, ry = self.r, self.ry
        px = {}

        def put(x, y, rgb):
            px[(int(round(x)), int(round(y)))] = rgb

        # Legs and arms go down first, so the body covers where they join.
        for side in (-1, 1):
            lx = side * r * 0.38
            for i in range(max(3, round(r * 0.6))):
                put(lx, ry - 1 + i, self.DARK)
        for side in (-1, 1):
            if scare:
                # Elbows out at shoulder height and forearms straight up, fingers spread:
                # a straight diagonal from the shoulder reads as an antenna, not an arm.
                ey = -r * 0.1
                reach = r + max(2, round(r * 0.3))
                for x in range(int(r) - 1, int(reach) + 1):
                    put(side * x, ey, self.DARK)
                top = ey - max(3, round(r * 0.55))
                for y in range(int(round(top)), int(round(ey)) + 1):
                    put(side * reach, y, self.DARK)
                self._hand(put, side * reach, round(top) - 1, side, up=True)
            else:
                # Long thin arms hanging down and a little out, hands at the ends.
                n = math.hypot(0.35, 1.0)
                dx, dy = side * 0.35 / n, 1.0 / n
                sx, sy = side * (r - 0.5), r * 0.1
                length = max(4, round(r * 0.9))
                for i in range(length):
                    put(sx + dx * i, sy + dy * i, self.DARK)
                self._hand(put, round(sx + dx * length), round(sy + dy * length), side, up=False)

        # Two little cone horns, their bases tucked into the top of his head.
        for side in (-1, 1):
            hx = side * round(r * 0.42)
            edge = int(round(-ry * math.sqrt(1 - (hx / r) ** 2)))
            tall = 3 if r >= 12 else 2
            for y in range(edge - tall, edge + 2):
                half = 1 if r >= 12 and y > edge - tall + 1 else 0
                for x in range(hx - half, hx + half + 1):
                    px[(x, y)] = self.HORN

        # The body: an egg, a touch wider below, lit from the upper left with a darker rim.
        for y in range(-math.ceil(ry) - 1, math.ceil(ry) + 2):
            for x in range(-math.ceil(r) - 1, math.ceil(r) + 2):
                ny = y / ry
                wx = x / r / (1.0 + 0.06 * ny)
                d = wx * wx + ny * ny
                if d > 1.0:
                    continue
                if d > 0.80:
                    px[(x, y)] = self.EDGE if d > 0.92 else self.DARK
                else:
                    px[(x, y)] = self.LIGHT if -0.55 * wx - 0.65 * ny > 0.35 else self.GREEN

        # The eye: white, a teal iris round a dark pupil that looks about, a glint,
        # and a green lid that slides down over it to blink.
        er = max(2.5, r * 0.46)
        ecy = -r * 0.28
        lid_y = ecy - er + lid * 2 * er
        ir = er * 0.55
        icx = look * (er - ir - 0.2)
        for y in range(int(ecy - er) - 1, int(ecy + er) + 2):
            for x in range(int(-er) - 1, int(er) + 2):
                if x * x + (y - ecy) ** 2 > er * er:
                    continue
                if y < lid_y:
                    px[(x, y)] = self.GREEN
                    continue
                d = (x - icx) ** 2 + (y - ecy) ** 2
                if d <= (ir * 0.5) ** 2:
                    px[(x, y)] = self.PUPIL
                elif d <= ir * ir:
                    px[(x, y)] = self.IRIS
                else:
                    px[(x, y)] = self.WHITE
        if lid < 0.4:
            gy = int(round(ecy - ir * 0.4))
            if gy >= lid_y:
                px[(int(round(icx - ir * 0.4)), gy)] = self.WHITE
        if lid >= 0.99:
            for x in range(int(-er) + 1, int(er)):
                px[(x, int(round(ecy + er * 0.3)))] = self.EDGE

        my = r * 0.42
        if scare:
            # Mouth wide open: a row of sharp teeth hanging from the top, and a couple
            # of fangs pointing up from the bottom.
            half, h = r * 0.55, r * 0.55
            mcy = my + h / 2 - 0.5
            cols = {}
            for y in range(int(my - 1), int(my + h) + 1):
                for x in range(int(-half), int(half) + 1):
                    if (x / half) ** 2 + ((y - mcy) / (h / 2 + 0.5)) ** 2 <= 1:
                        px[(x, y)] = self.MOUTH
                        cols.setdefault(x, []).append(y)
            big = r >= 12
            for x, ys in cols.items():
                if abs(x) >= half - 1:
                    continue
                top, bottom = min(ys), max(ys)
                # How far each column's tooth reaches: a sawtooth, its points at the
                # centre and every 2nd (small) or 4th (big) column out from it.
                down = (3, 2, 1, 2)[abs(x) % 4] if big else (2, 1)[abs(x) % 2]
                up = {1: 1, 2: 2, 3: 1}.get(abs(x), 0) if big else (1 if abs(x) == 2 else 0)
                room = bottom - top - 1  # always leave a row of open mouth between them
                down = min(down, room - min(up, 1))
                up = min(up, room - down)
                for y in range(top, top + down):
                    px[(x, y)] = self.WHITE
                for y in range(bottom - up + 1, bottom + 1):
                    px[(x, y)] = self.WHITE
        else:
            # A toothy grin that curls up at the corners and widens as he warms up.
            g = 1.0 + 0.6 * grin
            half = r * (0.45 + 0.15 * g)
            for x in range(int(-half), int(half) + 1):
                top = my - (x / half) ** 2 * r * 0.12
                sag = (1 - (x / half) ** 2) * (1.5 + 1.2 * g) * r / 10
                y0, y1 = round(top), round(top + sag + 0.5)
                for y in range(y0, y1 + 1):
                    px[(x, y)] = self.MOUTH
                px[(x, y0)] = self.WHITE
        return px

    def _hand(self, put, x, y, side, up):
        """
        A palm at (x, y), three fingers fanned out from it and a thumb off the side facing
        his body. Fingers point up when his arms are thrown up and down when they hang. The
        gaps between fingers keep them from reading as one green blob.
        """
        v = -1 if up else 1
        long_ = 3 if self.r >= 12 else 2
        put(x, y, self.DARK)
        for fx in (-1, 0, 1):
            put(x + fx, y + v, self.DARK)
        for fx in (-2, 0, 2):
            for i in range(long_):
                put(x + fx, y + v * (2 + i), self.DARK)
        put(x - side, y, self.DARK)
        put(x - side * 2, y, self.DARK)
        put(x - side * 3, y + v, self.DARK)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        for (x, y), rgb in self.pixels(t).items():
            canvas.SetPixel(x, y, *rgb)
        return True


class GenieReveal:
    """
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

    # The lamp he comes out of, drawn big enough to read as Aladdin's lamp: a looped
    # handle on the left, domed lid with a knob, a low wide body on a short foot, and a
    # long spout tapering off to the right with its tip turned up. It has its own color
    # keys so it never borrows Genie's blue outline.
    # '.' empty, A outline bronze, Y gold, L glint, O shaded gold.
    LAMP_ART = [
        "...........AA.............",
        "..........ALYA............",
        "...........AA.............",
        ".........AAYYAA...........",
        "........ALYYYYOA..........",
        "..AAA.AAAAAAAAAAAA........",
        ".AOOOALLYYYYYYYYYOA....AAA",
        "AO..ALYYYYYYYYYYYYOAAAALYA",
        "AO..AYYYYYYYYYYYYYYYYYYYA.",
        ".AO.AYYYYYYYYYYYYYYOOOAA..",
        "..AOAOYYYYYYYYYYYOOAAA....",
        "...AAOOOYYYYYYYOOAA.......",
        "......AAAAOOOOOAAA........",
        ".........AYYYYA...........",
        "........AOOOOOOA..........",
        "........AAAAAAAA..........",
    ]
    # The spout's upturned tip, in lamp cells: smoke pours from here and Genie grows out of it.
    LAMP_SPOUT = (24.5, 6.0)
    # The lamp stays 1x on both boards: doubled, it swamps the 64x64 board under Genie.
    LAMP_SCALE = 1

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
        "G": (250, 205, 70), "C": (250, 205, 70), "S": (105, 180, 242),
        "A": (125, 72, 12), "Y": (250, 200, 60), "L": (255, 246, 190), "O": (205, 135, 25),
    }
    SMOKE_COLORS = [(120, 160, 235), (150, 120, 225), (95, 130, 210), (185, 165, 245)]

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.ART[0]) * self.scale
        self.sprite_h = len(self.ART) * self.scale
        self.lamp_w = len(self.LAMP_ART[0]) * self.LAMP_SCALE
        self.lamp_h = len(self.LAMP_ART) * self.LAMP_SCALE
        self.lamp_x = 2
        self.lamp_y = height - self.lamp_h
        # Each puff: [x, y, vx, vy, frames_left, rgb, radius]
        self.puffs = []
        self.last_frame = -1

    def spout(self):
        """Where the smoke leaves the lamp, and the point Genie scales up out of."""
        return (self.lamp_x + self.LAMP_SPOUT[0] * self.LAMP_SCALE,
                self.lamp_y + self.LAMP_SPOUT[1] * self.LAMP_SCALE)

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
        """
        Smoke for this frame: a plume rising from the spout, or a wake behind him. The
        same count on both boards: puffs are already twice as wide on 64x64, and doubling
        the count as well made the smoke eight times the work there.
        """
        r = self.rng
        if t < self.EMERGE_S:
            sx, sy = self.spout()
            return [[sx + r.uniform(-1, 1) * self.scale, sy,
                     r.uniform(-0.5, 0.5), r.uniform(-1.2, -0.5) * self.scale,
                     r.randint(14, 26), r.choice(self.SMOKE_COLORS), r.uniform(0.4, 1.0)]
                    for _ in range(3)]
        x, y = self.position(t)
        return [[x + r.uniform(0.25, 0.65) * self.sprite_w,
                 y + self.sprite_h * r.uniform(0.6, 1.0),
                 r.uniform(-0.9, -0.2) * self.scale, r.uniform(-0.25, 0.25),
                 r.randint(16, 28), r.choice(self.SMOKE_COLORS), r.uniform(0.7, 1.6)]
                for _ in range(4)]

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

    _stamps = {}

    @classmethod
    def _stamp(cls, radius):
        """(dx, dy, falloff) for a soft disc of `radius`, cached per quarter pixel."""
        key = round(radius * 4) / 4
        stamp = cls._stamps.get(key)
        if stamp is None:
            reach = int(math.ceil(key))
            stamp = []
            for dy in range(-reach, reach + 1):
                for dx in range(-reach, reach + 1):
                    d = math.hypot(dx, dy)
                    if d <= key:
                        falloff = (1.0 - d / (key + 0.001)) ** 0.7
                        if falloff > 0.05:
                            stamp.append((dx, dy, falloff))
            cls._stamps[key] = stamp
        return stamp

    def _draw_puffs(self, canvas):
        """
        Soft discs, brightest at the centre, added to what is already on the canvas -- a
        thinning puff lets the screen behind it show through instead of blacking it out.
        Each lit pixel keeps its brightest puff and is set once: redrawing every puff
        pixel by pixel was thousands of SetPixel calls a frame, too slow for a Pi.
        """
        light = {}
        width, height = self.width, self.height
        for cx, cy, _, _, life, rgb, rad in self.puffs:
            f = min(1.0, life / 18.0)
            ox, oy = int(round(cx)), int(round(cy))
            r0, g0, b0 = rgb
            for dx, dy, falloff in self._stamp(rad * self.scale):
                x, y = ox + dx, oy + dy
                if not (0 <= x < width and 0 <= y < height):
                    continue
                g = f * falloff
                if g <= 0.05:
                    continue
                seen = light.get((x, y))
                if seen is None:
                    light[(x, y)] = [r0 * g, g0 * g, b0 * g]
                else:
                    seen[0], seen[1], seen[2] = max(seen[0], r0 * g), max(seen[1], g0 * g), max(seen[2], b0 * g)
        under = getattr(canvas, "px", {})
        for (x, y), (r, g, b) in light.items():
            base = under.get((x, y), (0, 0, 0))
            canvas.SetPixel(x, y, min(255, int(base[0] + r)), min(255, int(base[1] + g)), min(255, int(base[2] + b)))

    def overlay(self, canvas, t):
        self._step_puffs(t)
        if t < self.duration:
            # Nothing is revealed while he is still forming: lamp and smoke on black.
            _blackout(canvas, self.reveal_x(t), self.width, self.height)
        self._draw_puffs(canvas)
        if t < self.duration:
            # The lamp stays put on the still-dark side until the reveal sweeps past it.
            self._draw_art(canvas, self.LAMP_ART, self.lamp_x, self.lamp_y,
                           clip_x=self.reveal_x(t))
            self._draw_genie(canvas, t)
        return t < self.duration or bool(self.puffs)

    def _draw_art(self, canvas, art, x0, y0, clip_x=0):
        x0, y0 = int(round(x0)), int(round(y0))
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.LAMP_SCALE):
                    for sx in range(self.LAMP_SCALE):
                        px = x0 + col * self.LAMP_SCALE + sx
                        py = y0 + row * self.LAMP_SCALE + sy
                        if clip_x <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])

    def _full_pixels(self):
        """(dx, dy, rgb) for every lit pixel of Genie at full size, worked out once."""
        if getattr(self, "_full", None) is None:
            s = self.scale
            self._full = [(col * s + sx, row * s + sy, self.COLORS[kind])
                          for row, line in enumerate(self.ART) for col, kind in enumerate(line) if kind != "."
                          for sy in range(s) for sx in range(s)]
        return self._full

    def _draw_genie(self, canvas, t):
        """
        Draw him at `grow(t)` of full size. Below full size every cell is pulled toward
        the spout by that factor, so he swells out of the smoke rather than fading in.
        """
        g = self.grow(t)
        if g <= 0.02:
            return
        # Whole pixels first: a half-pixel home splits cells either side of the spout
        # in opposite directions as he scales, opening a gap down his middle.
        x0, y0 = (math.floor(v + 0.5) for v in self.position(t))
        if g >= 1.0:
            # Full size, i.e. his whole flight: just offset the precomputed pixels.
            width, height = self.width, self.height
            for dx, dy, rgb in self._full_pixels():
                px, py = x0 + dx, y0 + dy
                if 0 <= px < width and 0 <= py < height:
                    canvas.SetPixel(px, py, *rgb)
            return
        ax, ay = self.spout()
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                bx, by = x0 + col * self.scale, y0 + row * self.scale
                if g < 1.0:
                    # Scale the cell's centre, not its corner: otherwise near full size every
                    # column lands on x.5 and round-half-to-even drops every other one.
                    half = self.scale / 2
                    bx = ax + (bx + half - ax) * g - half
                    by = ay + (by + half - ay) * g - half
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = math.floor(bx + 0.5) + sx, math.floor(by + 0.5) + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.COLORS[kind])


class SlinkyReveal:
    """
    Slinky Dog stretched from one side of the board to the other: his rear sits on the
    left edge while his front half walks right until his nose reaches the right edge,
    pulling his spring out across the whole board. He holds there, then the rear snaps
    across to catch up and both halves bound off the right edge.

    The new screen is revealed behind his front half as it walks, so the spring and rear
    are drawn over it; ahead of him the board stays dark.
    """
    STRETCH_S, HOLD_S, SNAP_S, EXIT_S = 1.3, 0.5, 0.35, 0.55
    duration = STRETCH_S + HOLD_S + SNAP_S + EXIT_S

    # Front half facing right: long dark ear down the back of his head, big eye,
    # tan muzzle out front ending in a black nose, chest and two front legs.
    FRONT_ART = [
        "....KKKKKK......",
        "...KBBBBBBK.....",
        "..KBBBBBBBBK....",
        ".KDKBEEBEEBBK...",
        "KDDKBEPBEPBBBKK.",
        "KDDKBEPBEPBTTTTK",
        "KDDKBBBBBBTTTTNK",
        "KDDDKBBBBTTTTTNK",
        "KDDDKBBBTTTTMMK.",
        ".KDDKKBBTTTTTK..",
        ".KDDK.KBBBBBK...",
        "..KK..KBBBBBK...",
        "....KKBTTTBBBK..",
        "...KBBTTTTBBBK..",
        "...KBBBTTBBBBK..",
        "...KBBBBBBBBBK..",
        "...KBBKKKKBBBK..",
        "...KBBK..KBBK...",
        "...KTTK..KTTK...",
        "...KKKK..KKKK...",
    ]
    # Rear half: round rump, two back legs, and a coiled spring tail curling up.
    REAR_ART = [
        "SWS.........",
        ".SWS........",
        "..SWS.......",
        "...KKKKKKK..",
        "..KBBBBBBBK.",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBKKKKBBBK",
        ".KBBK..KBBK.",
        ".KTTK..KTTK.",
        ".KKKK..KKKK.",
    ]
    COLORS = {
        "K": (70, 40, 18), "B": (176, 108, 48), "D": (100, 58, 26), "T": (238, 200, 140),
        "N": (18, 14, 14), "E": (248, 246, 240), "P": (30, 22, 20), "M": (160, 50, 45),
        "S": (215, 220, 230), "W": (120, 128, 142),
    }
    COIL_FRONT, COIL_BACK = (215, 220, 230), (110, 118, 132)
    COILS = 11
    # 1x on both boards: doubled, the two halves eat the 64x64 board and the spring can't stretch.
    SCALE = 1

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.scale = self.SCALE
        s = self.scale
        self.front_w, self.front_h = len(self.FRONT_ART[0]) * s, len(self.FRONT_ART) * s
        self.rear_w, self.rear_h = len(self.REAR_ART[0]) * s, len(self.REAR_ART) * s
        self.ground = height  # feet stand on the bottom row
        self.spring_y = self.ground - 7 * s  # the coil runs through both bodies
        self.coil_h = 7 * s
        self.home_rear = 0
        self.min_gap = 3 * s  # a squashed spring between the halves
        self.far_front = width - self.front_w

    def rear_x(self, t):
        snap_at = self.STRETCH_S + self.HOLD_S
        if t < snap_at:
            return self.home_rear
        caught = self.far_front - self.min_gap - self.rear_w
        if t < snap_at + self.SNAP_S:
            p = (t - snap_at) / self.SNAP_S
            return self.home_rear + (caught - self.home_rear) * ease_out(p)
        return caught + self._exit(t)

    def front_x(self, t):
        start = self.home_rear + self.rear_w + self.min_gap
        if t < self.STRETCH_S:
            # Walks out, easing to a stop with his nose at the right edge.
            return start + (self.far_front - start) * ease_out(t / self.STRETCH_S)
        return self.far_front + self._exit(t)

    def _exit(self, t):
        begin = self.STRETCH_S + self.HOLD_S + self.SNAP_S
        p = max(0.0, (t - begin) / self.EXIT_S)
        return p * p * (self.width + self.rear_w + self.min_gap)

    def bob(self, t):
        """A small step-bounce while the front half walks."""
        if t >= self.STRETCH_S:
            return 0
        return -round(abs(math.sin(t * math.pi * 6)) * self.scale)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        fx, rx = self.front_x(t), self.rear_x(t)
        _blackout(canvas, int(fx + self.front_w * 0.5), self.width, self.height)
        self._draw_spring(canvas, rx + self.rear_w - 2 * self.scale, fx + 4 * self.scale)
        self._draw(canvas, self.REAR_ART, rx, self.ground - self.rear_h)
        self._draw(canvas, self.FRONT_ART, fx, self.ground - self.front_h + self.bob(t))
        return True

    def _draw_spring(self, canvas, x0, x1):
        """
        A row of tilted rings: each coil's back arc in shadow, its front arc bright on
        top. Squashed, the rings overlap into a solid banded tube; stretched, they
        separate into loops you can count.
        """
        if x1 <= x0:
            return
        ry = self.coil_h / 2
        step = (x1 - x0) / self.COILS
        rx = max(1.0, min(step * 0.55, 2.5 * self.scale))
        steps = 8 * self.coil_h
        for front, colour in ((False, self.COIL_BACK), (True, self.COIL_FRONT)):
            for i in range(self.COILS + 1):
                cx = x0 + i * step
                for k in range(steps + 1):
                    a = math.pi * k / steps - math.pi / 2  # top to bottom
                    dx = math.cos(a) * rx
                    x = cx + (dx if front else -dx)
                    # The ring leans: its top sits a little behind its bottom.
                    x += (math.sin(a)) * rx * 0.6
                    self._px(canvas, x, self.spring_y + math.sin(a) * ry, colour)

    def _px(self, canvas, x, y, rgb):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)

    def _draw(self, canvas, art, x0, y0):
        x0, y0 = int(round(x0)), int(round(y0))
        s = self.scale
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for dy in range(s):
                    for dx in range(s):
                        self._px(canvas, x0 + col * s + dx, y0 + row * s + dy, self.COLORS[kind])


class SlinkyWrapReveal:
    """
    A surprise over a ride screen: Slinky walks in along the bottom, his rear stops in
    the bottom-right corner, and his front half keeps going off the right edge. After a
    random pause his front peeks back in at the top-left, as if the spring ran around
    behind the board. He looks down at his own rear, which wags its tail; then his front
    walks across the top, and his rear follows the same way round: off the right edge at
    the bottom, back in at the top-left, catching up behind him. Then the whole dog walks
    off the right edge.

    No blackout: the ride screen stays readable, and keeps animating, underneath him.
    """

    over_screen = True
    WALK_IN_S, WALK_OFF_S, PEEK_S, LOOK_S = 0.8, 0.5, 0.4, 0.6
    CROSS_S, FOLLOW_S, EXIT_S = 0.7, 0.9, 0.5
    FOLLOW_OUT = 0.4  # share of the follow spent leaving the bottom-right; the rest re-entering
    PAUSE_S = (1.0, 3.0)
    # The longest visit; each one rolls its own pause. With the 0.55s sweep it fits
    # inside the 8s ride screen.
    duration = WALK_IN_S + WALK_OFF_S + PEEK_S + LOOK_S + CROSS_S + FOLLOW_S + EXIT_S + PAUSE_S[1]

    FRONT_ART = SlinkyReveal.FRONT_ART
    REAR_ART = SlinkyReveal.REAR_ART
    COLORS = SlinkyReveal.COLORS
    COIL_FRONT, COIL_BACK = SlinkyReveal.COIL_FRONT, SlinkyReveal.COIL_BACK
    # His front half with the pupils dropped to the bottom-right of each eye: looking
    # down at his rear in the opposite corner.
    FRONT_LOOK_ART = [
        "....KKKKKK......",
        "...KBBBBBBK.....",
        "..KBBBBBBBBK....",
        ".KDKBEEBEEBBK...",
        "KDDKBEEBEEBBBKK.",
        "KDDKBEPBEPBTTTTK",
        "KDDKBBBBBBTTTTNK",
        "KDDDKBBBBTTTTTNK",
        "KDDDKBBBTTTTMMK.",
        ".KDDKKBBTTTTTK..",
        ".KDDK.KBBBBBK...",
        "..KK..KBBBBBK...",
        "....KKBTTTBBBK..",
        "...KBBTTTTBBBK..",
        "...KBBBTTBBBBK..",
        "...KBBBBBBBBBK..",
        "...KBBKKKKBBBK..",
        "...KBBK..KBBK...",
        "...KTTK..KTTK...",
        "...KKKK..KKKK...",
    ]
    # His rear with the spring tail swung forward over his back: alternated with
    # REAR_ART it wags.
    REAR_WAG_ART = [
        ".....SWS....",
        "....SWS.....",
        "...SWS......",
        "...KKKKKKK..",
        "..KBBBBBBBK.",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBKKKKBBBK",
        ".KBBK..KBBK.",
        ".KTTK..KTTK.",
        ".KKKK..KKKK.",
    ]
    SCALE = 1
    COILS = 11
    STUB_COILS = 2  # coils showing beside each piece while the spring is round the back

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        rng = rng or random.Random()
        s = self.scale = self.SCALE
        self.front_w, self.front_h = len(self.FRONT_ART[0]) * s, len(self.FRONT_ART) * s
        self.rear_w, self.rear_h = len(self.REAR_ART[0]) * s, len(self.REAR_ART) * s
        self.gap = 3 * s
        self.coil_step = 3 * s  # ring spacing on the stubs that run off an edge
        self.coil_h = 7 * s
        self.bottom = height  # ground lines: feet on the bottom row, or under the top-left peek
        self.top = self.front_h
        self.rear_home = width - self.rear_w - self.STUB_COILS * self.coil_step
        # One extra step: the ring nearest the left edge is half cut off by it.
        self.peek_x = (self.STUB_COILS + 1) * self.coil_step - 4 * s
        self.pause = rng.uniform(*self.PAUSE_S)
        self.duration = self.visit_s()
        b = [self.WALK_IN_S, self.WALK_OFF_S, self.pause, self.PEEK_S, self.LOOK_S,
             self.CROSS_S, self.FOLLOW_S, self.EXIT_S]
        self.beats = [sum(b[:i + 1]) for i in range(len(b))]

    def visit_s(self):
        return (self.WALK_IN_S + self.WALK_OFF_S + self.pause + self.PEEK_S + self.LOOK_S
                + self.CROSS_S + self.FOLLOW_S + self.EXIT_S)

    def phase(self, t):
        """(name, 0..1 progress through it) for time t."""
        names = ("walk_in", "walk_off", "pause", "peek", "look", "cross", "follow", "exit")
        start = 0.0
        for name, end in zip(names, self.beats):
            if t < end:
                return name, (t - start) / (end - start)
            start = end
        return "done", 1.0

    def pose(self, t):
        """
        Where both halves are: {"front": (x, ground) or None, "rear": (x, ground)}, where
        ground is the row under his feet. The front is None while it's off the board.
        """
        name, p = self.phase(t)
        W = self.width
        cross_end = W - self.front_w
        landed = cross_end - self.gap - self.rear_w
        if name == "walk_in":
            rear = -self.rear_w - self.gap - self.front_w + (self.rear_home + self.rear_w + self.gap + self.front_w) * ease_out(p)
            return {"rear": (rear, self.bottom), "front": (rear + self.rear_w + self.gap, self.bottom)}
        if name == "walk_off":
            start = self.rear_home + self.rear_w + self.gap
            return {"rear": (self.rear_home, self.bottom), "front": (start + (W - start) * p * p, self.bottom)}
        if name == "pause":
            return {"rear": (self.rear_home, self.bottom), "front": None}
        if name == "peek":
            return {"rear": (self.rear_home, self.bottom),
                    "front": (-self.front_w + (self.peek_x + self.front_w) * ease_out(p), self.top)}
        if name == "look":
            return {"rear": (self.rear_home, self.bottom), "front": (self.peek_x, self.top)}
        if name == "cross":
            return {"rear": (self.rear_home, self.bottom),
                    "front": (self.peek_x + (cross_end - self.peek_x) * ease_out(p), self.top)}
        if name == "follow":
            # The rear goes the way his front went: off the right edge along the bottom...
            if p < self.FOLLOW_OUT:
                q = p / self.FOLLOW_OUT
                return {"rear": (self.rear_home + (W - self.rear_home) * q * q, self.bottom),
                        "front": (cross_end, self.top)}
            # ...then back in from the left along the top, catching up behind him.
            q = (p - self.FOLLOW_OUT) / (1 - self.FOLLOW_OUT)
            x = -self.rear_w + (landed + self.rear_w) * ease_out(q)
            return {"rear": (x, self.top), "front": (cross_end, self.top)}
        if name == "exit":
            dx = p * p * (W + self.rear_w)
            return {"rear": (landed + dx, self.top), "front": (cross_end + dx, self.top)}
        return {"rear": (W, self.top), "front": (W, self.top)}

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        name, _ = self.phase(t)
        pose, s = self.pose(t), self.scale
        rx, rg = pose["rear"]
        rear_art = self.REAR_WAG_ART if name == "look" and int(t * 8) % 2 else self.REAR_ART
        walking = name in ("walk_in", "walk_off", "cross", "follow", "exit")
        bob = -round(abs(math.sin(t * math.pi * 6)) * s) if walking else 0
        rear_attach = (rx + self.rear_w - 2 * s, rg - 7 * s)
        # Split while the rear is still on the bottom: until it re-enters at the top-left.
        split = name in ("pause", "peek", "look", "cross") or (name == "follow" and rg == self.bottom)
        if split:
            # The spring runs off the right edge from his rear, and back in from the left
            # edge to his front: the middle of it is round the back of the board.
            self._spring(canvas, rear_attach, (self.width + self.coil_step, rear_attach[1]), self.coil_step)
            if pose["front"]:
                fx, fg = pose["front"]
                self._spring(canvas, (-self.coil_step, fg - 7 * s), (fx + 4 * s, fg - 7 * s), self.coil_step)
        elif pose["front"]:
            fx, fg = pose["front"]
            span = max(1.0, fx + 4 * s - rear_attach[0])
            self._spring(canvas, rear_attach, (fx + 4 * s, fg - 7 * s),
                         max(1.5 * s, min(span / self.COILS, 3.5 * s)))
        self._draw(canvas, rear_art, rx, rg - self.rear_h)
        if pose["front"]:
            fx, fg = pose["front"]
            art = self.FRONT_LOOK_ART if name == "look" else self.FRONT_ART
            self._draw(canvas, art, fx, fg - self.front_h + bob)
        return True

    def _spring(self, canvas, a, b, step):
        """Tilted rings every `step` pixels from a to b: shaded backs, then bright fronts."""
        (x0, y0), (x1, y1) = a, b
        length = math.hypot(x1 - x0, y1 - y0)
        if length <= 0:
            return
        count = max(1, int(length / step))
        ry = self.coil_h / 2
        rx = max(1.0, min(step * 0.55, 2.5 * self.scale))
        steps = 8 * self.coil_h
        for front, colour in ((False, self.COIL_BACK), (True, self.COIL_FRONT)):
            for i in range(count + 1):
                f = i / count
                cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                for k in range(steps + 1):
                    ang = math.pi * k / steps - math.pi / 2
                    dx = math.cos(ang) * rx
                    x = cx + (dx if front else -dx) + math.sin(ang) * rx * 0.6
                    self._px(canvas, x, cy + math.sin(ang) * ry, colour)

    def _px(self, canvas, x, y, rgb):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)

    def _draw(self, canvas, art, x0, y0):
        x0, y0, s = int(round(x0)), int(round(y0)), self.scale
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for dy in range(s):
                    for dx in range(s):
                        self._px(canvas, x0 + col * s + dx, y0 + row * s + dy, self.COLORS[kind])


class WallEReveal:
    """
    WALL-E rolls in along the bottom over the old screen, stops in a puff of dust, tilts
    his head and blinks at us, then opens his compactor hatch and vacuums the old screen
    up: its pixels fly into the hatch nearest-first, leaving the board black. The hatch
    closes, a trash cube with a sprout on top drops into the gap between his treads, and
    he trundles off the right edge carrying it, uncovering the new screen in his wake.

    Needs the previous screen's pixels, so it opts in via wants_prev, like Ralph.
    He stays 1x on both boards: doubled he'd cover most of the screen he's compacting.
    """

    wants_prev = True
    SCALE = 1
    ENTER_S, LOOK_S, SWEEP_S, FLY_S, DROP_S, LEAVE_S = 0.8, 0.9, 0.9, 0.3, 0.3, 1.0
    COMPACT_S = SWEEP_S + FLY_S
    # The visit, in order; "compact" is when the old screen is eaten and "leave" is last.
    PHASES = (("enter", ENTER_S), ("look", LOOK_S), ("compact", COMPACT_S), ("drop", DROP_S),
              ("leave", LEAVE_S))
    duration = sum(s for _, s in PHASES)
    STOP_X = 3
    BLINK_AT, BLINK_S = 0.55, 0.14  # into the look
    TILT_S = 0.4  # the look's first part: head tilted, then level for the blink

    # WALL-E in three-quarter view: binocular eyes on a short neck, a boxy yellow body
    # (front face lit, right side shaded) with a dark charge panel and the compactor
    # hatch's seam, grey arms on both sides, and a tread on each side with a gap between.
    # '.' empty, K outline, E eye housing, L lens, G glint, N neck, Y body front,
    # D body side (shade), S charge panel, A arm, T tread, W tread highlight.
    ART = [
        "..KKKKKK...KKKKKK...",
        ".KEEEEEEK.KEEEEEEK..",
        ".KELLLLEK.KELLLLEK..",
        ".KELGLLEK.KELGLLEK..",
        ".KEELLEEK.KEELLEEK..",
        "..KKKKKK...KKKKKK...",
        ".......KNNK.........",
        ".......KNNK.........",
        "..KKKKKKKKKKKKKKKK..",
        "..KYYYYYYYYYYYDDDK..",
        "KKKYSSYYYYYYYYDDDKKK",
        "KAKYYYYYYYYYYYDDDKAK",
        "KAKYKKKKKKKKKYDDDKAK",
        "KAKYYYYYYYYYYYDDDKAK",
        "KKKYYYYYYYYYYYDDDKKK",
        "..KKKKKKKKKKKKKKKK..",
        "KKKKKKK......KKKKKKK",
        "KTWTWTK......KTWTWTK",
        "KWTWTWK......KWTWTWK",
        "KKKKKKK......KKKKKKK",
    ]
    COLORS = {
        "K": (30, 26, 20),
        "E": (175, 175, 185),
        "L": (60, 80, 120),
        "G": (255, 255, 255),
        "N": (140, 140, 150),
        "Y": (240, 190, 40),
        "D": (180, 125, 20),
        "S": (70, 70, 75),
        "A": (150, 150, 160),
        "T": (80, 80, 85),
        "W": (160, 160, 165),
    }
    EYE_ROWS = range(0, 6)
    HATCH_ROWS, HATCH_COLS = (12, 13), range(5, 12)  # the seam drops open into a slot while compacting
    INTAKE = (8, 12)  # sprite cell the old screen is vacuumed into
    CUBE_COLS, CUBE_ROWS = range(7, 13), range(14, 20)  # sits in the gap between the treads
    # The sprout on top of the cube, as (col, row) sprite cells: a Y of two leaves on a stem.
    PLANT = [(9, 11, "leaf"), (11, 11, "leaf"), (10, 12, "stem"), (10, 13, "stem")]
    PLANT_RGB = {"leaf": (120, 255, 120), "stem": (40, 170, 60)}
    CUBE_EDGE_RGB = (110, 110, 115)  # lighter than his outline, so the cube stands clear of him
    DUST_RGB = (150, 135, 110)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.sprite_w, self.sprite_h = len(self.ART[0]), len(self.ART)
        self.y0 = height - self.sprite_h
        self.prev_px = {}
        self.flights = []
        self.cube = [self.CUBE_EDGE_RGB] * 4  # an empty screen makes a plain grey cube
        self.dust = []
        self._dusted = set()

    def capture_prev(self, prev_draw, prev_t):
        """Redraw the old screen in memory: those pixels get vacuumed up."""
        self.prev_px = capture_screen(prev_draw, prev_t, self.width, self.height)
        ix, iy = self.intake()
        # Nearest first: each pixel lifts off when the sweep front reaches it.
        self.flights = sorted(
            (math.hypot(x - ix, y - iy), x, y, rgb) for (x, y), rgb in self.prev_px.items())
        # The cube is made of what he ate: its most common colours, dimmed by the squash.
        counts = {}
        for rgb in self.prev_px.values():
            counts[rgb] = counts.get(rgb, 0) + 1
        common = sorted(counts, key=counts.get, reverse=True)[:4]
        if common:
            self.cube = [tuple(int(c * 0.8) for c in common[i % len(common)]) for i in range(4)]

    # --- timeline ---

    def _phase(self, t):
        """(phase name, seconds into it) at t."""
        for name, length in self.PHASES[:-1]:
            if t < length:
                return name, t
            t -= length
        return self.PHASES[-1][0], t

    def phase_start(self, name):
        """When a phase begins, in seconds from the start of the visit."""
        start = 0.0
        for phase, length in self.PHASES:
            if phase == name:
                return start
            start += length
        raise KeyError(name)

    def walle_x(self, t):
        """His left edge: rolls in from off the left, stops, then drives off the right."""
        phase, p = self._phase(t)
        if phase == "enter":
            return -self.sprite_w + ease_out(p / self.ENTER_S) * (self.STOP_X + self.sprite_w)
        if phase == "leave":
            q = min(1.0, p / self.LEAVE_S)
            return self.STOP_X + q * q * (self.width - self.STOP_X + 1)  # pulls away slowly, then goes
        return float(self.STOP_X)

    def intake(self):
        """Where the sweep starts from, on the board."""
        return self.STOP_X + self.INTAKE[0], self.y0 + self.INTAKE[1]

    def flight_target(self, t):
        """Where the old screen's pixels fly to this frame."""
        return self.intake()

    def sweep_radius(self, t):
        """How far from the hatch the old screen has been taken; -1 before compacting."""
        phase, p = self._phase(t)
        if t < self.phase_start("compact"):
            return -1.0
        if phase == "compact" and p < self.SWEEP_S:
            far = self.flights[-1][0] if self.flights else 0.0
            return p / self.SWEEP_S * (far + 1)
        return float("inf")

    # --- drawing ---

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        self._draw_old_screen(canvas, t)
        self._draw_flights(canvas, t)
        self._step_dust(t)
        x = self.walle_x(t)
        self._draw_walle(canvas, t, x)
        self._draw_dust(canvas)
        return True

    def _draw_old_screen(self, canvas, t):
        """
        Until he leaves, the board is his: black, with whatever of the old screen he hasn't
        eaten yet. As he rolls out, the new screen is uncovered in his wake.
        """
        if self._phase(t)[0] == "leave":
            _blackout(canvas, int(self.walle_x(t)), self.width, self.height)
            return
        _blackout(canvas, 0, self.width, self.height)
        radius = self.sweep_radius(t)
        for dist, x, y, rgb in reversed(self.flights):
            if dist <= radius:
                break
            canvas.SetPixel(x, y, *rgb)

    def _draw_flights(self, canvas, t):
        """Pixels the front has passed, accelerating into the hatch."""
        phase, p = self._phase(t)
        if phase != "compact" or not self.flights:
            return
        far = self.flights[-1][0] + 1
        ix, iy = self.flight_target(t)
        for dist, x, y, rgb in self.flights:
            lift = self.SWEEP_S * dist / far  # when the front passed it
            q = (p - lift) / self.FLY_S
            if q < 0:
                break
            if q >= 1:
                continue
            q = q * q
            canvas.SetPixel(int(round(x + (ix - x) * q)), int(round(y + (iy - y) * q)), *rgb)

    def _step_dust(self, t):
        """A puff from the treads as he stops, and again as he pulls away."""
        for at in (self.ENTER_S - 0.1, self.phase_start("leave")):
            if t >= at and at not in self._dusted:
                self._dusted.add(at)
                x = self.walle_x(at)
                for side_x, push in ((x, -1), (x + self.sprite_w - 1, 1)):
                    for _ in range(4):
                        self.dust.append([side_x, self.height - 1.5, at,
                                          push * self.rng.uniform(4, 10), -self.rng.uniform(2, 6)])
        self.dust = [d for d in self.dust if t - d[2] < 0.5]
        self._t = t

    def _draw_dust(self, canvas):
        under = getattr(canvas, "px", {})
        for x0, y0, born, vx, vy in self.dust:
            age = self._t - born
            px, py = int(round(x0 + vx * age)), int(round(y0 + vy * age))
            if not (0 <= px < self.width and 0 <= py < self.height):
                continue
            f = 1 - age / 0.5
            base = under.get((px, py), (0, 0, 0))
            canvas.SetPixel(px, py, *(min(255, int(b + c * f)) for b, c in zip(base, self.DUST_RGB)))

    def _cell(self, t, row, col, kind):
        """The colour key at one sprite cell this frame: treads roll, eyes blink, hatch opens."""
        phase, p = self._phase(t)
        if kind in "TW" and phase in ("enter", "leave"):
            if int(self.walle_x(t)) % 2:
                kind = "W" if kind == "T" else "T"
        if row in self.EYE_ROWS and phase == "look" and self.BLINK_AT <= p < self.BLINK_AT + self.BLINK_S:
            if kind in "LG":
                kind = "K" if row == 3 else "E"
        if phase == "compact" and row in self.HATCH_ROWS and col in self.HATCH_COLS:
            kind = "K"
        return kind

    def _draw_walle(self, canvas, t, x):
        x0 = int(round(x))
        phase, p = self._phase(t)
        tilt = phase == "look" and p < self.TILT_S
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                kind = self._cell(t, row, col, kind)
                # The curious tilt: his left eye lifts a row while the right stays put.
                dy = -1 if tilt and row in self.EYE_ROWS and col < 10 else 0
                self._px(canvas, x0 + col, self.y0 + row + dy, self.COLORS[kind])
        if phase in ("drop", "leave"):
            self._draw_cube(canvas, x0, min(1.0, p / self.DROP_S) if phase == "drop" else 1.0)

    def _draw_cube(self, canvas, x0, drop):
        """The trash cube, sliding down out of the hatch into the gap between his treads."""
        lift = int(round((1 - drop) * 3))
        top = self.y0 + self.CUBE_ROWS[0] - lift
        left = x0 + self.CUBE_COLS[0]
        n = len(self.CUBE_COLS)
        for r in range(n):
            for c in range(n):
                edge = r in (0, n - 1) or c in (0, n - 1)
                rgb = self.CUBE_EDGE_RGB if edge else self.cube[(r // 2 + c // 2) % len(self.cube)]
                self._px(canvas, left + c, top + r, rgb)
        if drop >= 1:
            for col, row, part in self.PLANT:
                self._px(canvas, x0 + col, self.y0 + row, self.PLANT_RGB[part])

    def _px(self, canvas, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)


class WallESideReveal(WallEReveal):
    """
    WALL-E in profile, drawn from a side-on photo of him, working like the trash baler he
    is. He rolls in facing his travel, swivels his head round to look at us (a bob and a
    blink), then turns back and gets to work:

    1. Collect: his chest door drops open and the whole old screen flies in through it,
       nearest pixels first, leaving the board black.
    2. Compress: the door shuts and he jolts as the press inside crushes it all.
    3. Eject: the door opens and the finished cube slides out and drops to the ground.
    4. Pick up: his arm reaches down, grabs the cube and lifts it.

    Then he drives off the right edge carrying it, uncovering the new screen in his wake.
    """

    ENTER_S, LOOK_S, SWEEP_S, FLY_S, LEAVE_S = 0.8, 0.8, 0.9, 0.3, 1.0
    OPEN_S, CLOSE_S, PRESS_S, EJECT_S, PICKUP_S = 0.15, 0.15, 0.5, 0.45, 0.45
    COMPACT_S = SWEEP_S + FLY_S
    PHASES = (("enter", ENTER_S), ("look", LOOK_S), ("open", OPEN_S), ("compact", COMPACT_S),
              ("close", CLOSE_S), ("press", PRESS_S), ("eject", EJECT_S), ("pickup", PICKUP_S),
              ("leave", LEAVE_S))
    duration = sum(s for _, s in PHASES)
    BLINK_AT = 0.45

    # Facing left as in the photo, and mirrored when drawn so he faces right, the way he
    # travels: a boxy head on a bent neck, the body's grey top rim, his arm tucked against
    # his front (yellow cuff, small grey claw), the big triangular tread over the body's
    # lower front, and the round disc on his back. The photo's long striped forearm is left
    # out: drawn at this size it read as a row of dots.
    # '.' empty, K outline, H head, L lens, G glint, N neck, R rim, Y body, D body shade,
    # M back disc, C claw and forearm, U cuff, T tread, V tread wheel.
    ART = [
        "..KKKKKKKKKKKK.....",
        "..KGLHHHHHHHHK.....",
        "..KLLHHHHHHHHK.....",
        "..KKKKKKKKKKKK.....",
        "..........KNK......",
        "...........KNK.....",
        ".....KRRRRRRRRRRRK.",
        "...KKKKYYYYYYYYYDK.",
        "..KCUUKYYYYYYYYYDKM",
        "..KCKKKYYYYYYYYYDKM",
        "..KK.KYYYYYYYYYYDKM",
        ".....KYYYYYKVKYYDKM",
        ".....KYYYYKVTVKYDKM",
        ".....KYYYYKVVTVKDKM",
        ".....KYYYKVTTTVKDK.",
        ".....KYYKVTTTTTVKK.",
        ".....KYKVVTTTTVTVK.",
        ".....KKVTTTTTTTTVK.",
        ".....KVVVVVVVVVVVVK",
        "....KKKKKKKKKKKKKKK",
    ]
    COLORS = {
        "K": (30, 26, 20),
        "H": (175, 175, 185),
        "E": (175, 175, 185),
        "L": (60, 80, 120),
        "G": (255, 255, 255),
        "N": (140, 140, 150),
        "R": (150, 150, 155),
        "Y": (240, 190, 40),
        "D": (180, 125, 20),
        "M": (200, 145, 30),
        "C": (150, 150, 160),
        "U": (255, 220, 60),
        "T": (55, 55, 60),
        "V": (160, 160, 165),
    }
    # His head turned to face us: both binocular lenses, in the same box.
    HEAD_FRONT = [
        "KKKKKKKKKKKK",
        "KELLEKKELLEK",
        "KELGEKKEGLEK",
        "KKKKKKKKKKKK",
    ]
    HEAD_ROWS, HEAD_COL = range(0, 4), 2
    TURN_S = 0.12  # into the look: the head swivels round, and back at the end
    BOB_S = 0.3  # one bob of the head on its neck
    # All in drawn (mirrored) sprite cells, where his front is on the right.
    FRONT_COL = 13  # the front face of his body
    DOOR_ROWS, DOOR_COLS = range(11, 15), (12, 13)  # the chest opening, dark while the door's open
    # The door: a panel hinged at the bottom of the opening that swings down and out until it
    # lies flat. Shut, it's edge-on (his outline); open, we see its yellow inside face.
    DOOR_HINGE, DOOR_LEN, DOOR_SWING_S = (13, 15), 3, 0.12
    INTAKE = (13, 12)  # the old screen flies in here
    ARM_ROWS, ARM_COLS = range(7, 11), range(13, 17)  # the tucked arm: cuff and claw
    ARM_DROP = 5  # how far the claw reaches down to the cube on the ground
    CUBE_SIZE = 4  # fits the door
    CUBE_GROUND = (16, 16)  # the cube's top-left once it's out, on the ground just past the flap
    CUBE_OUT_ROW = 11  # the row it slides out at, level with the door
    PRESS_JOLT_S = 0.1
    # The sprout on the cube's top, clear of the claw's grip: (col, row) from its top-left.
    PLANT = [(2, -2, "leaf"), (4, -2, "leaf"), (3, -1, "stem")]

    def __init__(self, width, height, rng=None):
        super().__init__(width, height, rng)
        self.art = [row[::-1] for row in self.ART]

    def intake(self):
        return self.STOP_X + self.INTAKE[0], self.y0 + self.INTAKE[1]

    # --- the look ---

    def facing_us(self, t):
        phase, p = self._phase(t)
        return phase == "look" and self.TURN_S <= p < self.LOOK_S - self.TURN_S

    def head_bob(self, t):
        """The curious bob: his head dips a row on its neck and comes back up, once."""
        phase, p = self._phase(t)
        return 1 if phase == "look" and self.TURN_S <= p < self.TURN_S + self.BOB_S else 0

    # --- the baler ---

    def door_angle(self, t):
        """0 shut to 1 lying flat open: it swings open to collect and to eject, and shut after each."""
        phase, p = self._phase(t)
        swing = lambda q: ease_out(min(1.0, q / self.DOOR_SWING_S))
        if phase == "open":
            return swing(p)
        if phase == "compact":
            return 1.0
        if phase == "close":
            return 1 - swing(p)
        if phase == "eject":
            return swing(p)
        if phase == "pickup":
            return 1 - swing(p)
        return 0.0

    def door_open(self, t):
        return self.door_angle(t) > 0

    def door_cells(self, angle):
        """The door panel's cells (col, row), swung `angle` (0-1) from shut toward flat."""
        hx, hy = self.DOOR_HINGE
        a = angle * math.pi / 2
        return [(hx + round(i * math.sin(a)), hy - round(i * math.cos(a))) for i in range(1, self.DOOR_LEN + 1)]

    def jolt(self, t):
        """The press working: his whole body jolts back and forth a column."""
        phase, p = self._phase(t)
        return 1 if phase == "press" and int(p / self.PRESS_JOLT_S) % 2 == 0 else 0

    def arm_drop(self, t):
        """How far the claw has reached down: down to the cube and back up with it."""
        phase, p = self._phase(t)
        if phase != "pickup":
            return 0
        q = p / self.PICKUP_S
        down = ease_out(q * 2) if q < 0.5 else 1 - ease_out((q - 0.5) * 2)
        return round(self.ARM_DROP * down)

    def cube_at(self, t):
        """The cube's top-left in sprite cells, or None while it's still inside him."""
        phase, p = self._phase(t)
        ground_x, ground_y = self.CUBE_GROUND
        if phase == "eject":
            q = p / self.EJECT_S
            if q < 0.6:  # slides out of the door...
                return self.FRONT_COL - self.CUBE_SIZE + ease_out(q / 0.6) * (ground_x - self.FRONT_COL + self.CUBE_SIZE), \
                    self.CUBE_OUT_ROW
            fall = ((q - 0.6) / 0.4) ** 2  # ...and drops to the ground
            return ground_x, self.CUBE_OUT_ROW + fall * (ground_y - self.CUBE_OUT_ROW)
        if phase == "pickup" and p < self.PICKUP_S / 2:
            return ground_x, ground_y
        if phase in ("pickup", "leave"):
            claw_tip = self.ARM_ROWS[-1] + self.arm_drop(t)
            return ground_x, claw_tip + 1  # hanging from the claw
        return None

    # --- drawing ---

    def _draw_walle(self, canvas, t, x):
        x0 = int(round(x)) + self.jolt(t)
        phase, p = self._phase(t)
        rolling = phase in ("enter", "leave") and int(x) % 2
        blinking = phase == "look" and self.BLINK_AT <= p < self.BLINK_AT + self.BLINK_S
        front, bob, drop = self.facing_us(t), self.head_bob(t), self.arm_drop(t)
        door = self.door_open(t)
        for row, line in enumerate(self.art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                dy = 0
                if row in self.HEAD_ROWS:
                    dy = bob
                    if front:
                        continue  # drawn below, turned toward us
                    if blinking and kind in "LG":
                        kind = "H"
                if self._is_arm(row, col, kind):
                    continue  # the arm is drawn on top of everything, below
                if door and row in self.DOOR_ROWS and col in self.DOOR_COLS:
                    kind = "K"  # the dark inside of his chest
                if door and (col, row) == self.DOOR_HINGE:
                    kind = "Y"  # the hinge: yellow, joining the open door to his body
                if rolling and kind in "TV":
                    kind = "V" if kind == "T" else "T"
                self._px(canvas, x0 + col, self.y0 + row + dy, self.COLORS[kind])
        if front:
            left = x0 + self.sprite_w - self.HEAD_COL - len(self.HEAD_FRONT[0])
            for row, line in enumerate(self.HEAD_FRONT):
                for col, kind in enumerate(line):
                    if blinking and kind in "LG":
                        kind = "K" if row == 2 else "E"
                    self._px(canvas, left + col, self.y0 + row + bob, self.COLORS[kind])
        if door:
            for col, row in self.door_cells(self.door_angle(t)):
                self._px(canvas, x0 + col, self.y0 + row, self.COLORS["Y"])
        cube = self.cube_at(t)
        if cube:
            self._draw_cube(canvas, x0, cube, clip=phase == "eject")
        self._draw_arm(canvas, x0, drop)

    def _draw_arm(self, canvas, x0, drop):
        """The cuff and claw, lowered by `drop`, on a grey forearm down from his shoulder."""
        for i in range(drop):
            self._px(canvas, x0 + self.ARM_COLS[1], self.y0 + self.ARM_ROWS[1] + i, self.COLORS["C"])
        for row in self.ARM_ROWS:
            for col in self.ARM_COLS:
                kind = self.art[row][col]
                if self._is_arm(row, col, kind):
                    self._px(canvas, x0 + col, self.y0 + row + drop, self.COLORS[kind])

    def _is_arm(self, row, col, kind):
        """A cell of the tucked arm. Its first column is also his front: there only the cuff moves."""
        if kind == "." or row not in self.ARM_ROWS or col not in self.ARM_COLS:
            return False
        return col != self.FRONT_COL or kind in "CU"

    def _draw_cube(self, canvas, x0, at, clip=False):
        """The trash cube; while it's coming out, only the part past his front shows."""
        left, top = x0 + int(round(at[0])), self.y0 + int(round(at[1]))
        n = self.CUBE_SIZE
        for r in range(n):
            for c in range(n):
                if clip and left + c <= x0 + self.FRONT_COL:
                    continue
                edge = r in (0, n - 1) or c in (0, n - 1)
                rgb = self.CUBE_EDGE_RGB if edge else self.cube[(r + c) % len(self.cube)]
                self._px(canvas, left + c, top + r, rgb)
        if not clip or left > x0 + self.FRONT_COL:
            for col, row, part in self.PLANT:
                self._px(canvas, left + col, top + row, self.PLANT_RGB[part])


class ArmyMenReveal:
    """
    Three green army men parachute in, the way Andy's toys drop in on a mission. Each
    hangs under a camo canopy on rigging lines that swing like a pendulum as he falls, and
    the new screen is uncovered top-down in step with the lead soldier's feet, like a
    curtain coming down with him. They touch down one after another, each with a puff of
    dust off his base; each chute deflates and slumps to the ground downwind behind him.
    Then all three hop off the right edge in step on their bases, as they move in the
    films (the toys can't walk, their feet are molded to the base).

    Needs both the old screen (visible below the curtain) and the new one (uncovered above
    it), so it opts into both wants_prev and wants_new, the first transition to need both.
    Nothing else on the board reveals top-down.

    Stays 1x on both boards: three at 2x collide and clip the edges of 64x64.
    """

    wants_prev = True
    wants_new = True
    SCALE = 1
    FALL_S = 0.8  # each soldier's time in the air, from above the board to touchdown
    # 64x64 is twice the drop: at 0.8s they plummeted. Longer, but still a touch quicker
    # per row than on 64x32, which reads right there.
    FALL_S_TALL = 1.3
    COLLAPSE_S = 0.6  # a landed chute deflating and slumping to the ground
    DUST_S = 0.35  # a landing puff, from kick-up to gone
    LAND_S = 0.45  # everyone holds, after the last lands, before the hop-off
    HOPS, HOP_S = 4, 0.32  # the hop-off: hops across and the time for each
    MARCH_S = HOPS * HOP_S
    SWAY_HZ = 1.1  # pendulum swings per second while falling

    # Each soldier: (x as a fraction of the board width, delay before he starts falling).
    # Staggered delays land them one after another, left to right.
    UNITS = [(0.18, 0.0), (0.5, 0.17), (0.82, 0.34)]
    DROP_S = max(delay for _, delay in UNITS) + FALL_S  # the last touchdown
    duration = DROP_S + LAND_S + MARCH_S

    # The camo canopy from the reference: an olive dome with gold patches and a dark
    # roundel carrying a white star. Its own keys so it never shares the soldier's greens.
    # '.' empty, C rim, N canopy olive, O gold patch, M roundel, * star.
    CANOPY_ART = [
        ".....CCCCC.....",
        "...CCNNNNNCC...",
        "..COOMM*MMNNC..",
        ".COOMM***MMNOC.",
        ".CNM*******MOC.",
        "CNNMM*****MMNNC",
        "CNOOM**M**MOONC",
        "COOOM*MMM*MOOOC",
        "CCCCCCCCCCCCCCC",
    ]
    # Where the rigging lines leave the hem (columns of the canopy's last row).
    RIG_COLS = (1, 4, 10, 13)

    # A green army man, front-on, in bright toy-plastic green: helmet with a dark brim
    # shading his face, rifle held across his chest and poking out past his shoulder and
    # hip (the only way it reads at this size), legs apart, feet on the molded base.
    # '.' empty, K outline, L highlight, G plastic, D shade, R rifle over his body,
    # S rifle against the sky, B base.
    SOLDIER_ART = [
        "....KKK.....",
        "...KLLGK....",
        "..KLGGGDK...",
        ".KDDDDDDDK.S",
        "..KGDGDDK.S.",
        "...KGGDKSS..",
        "..KLGGGRK...",
        ".KLGGGRGDK..",
        ".KLGGRGGDK..",
        ".KLGRGGGDK..",
        ".KRRGGGGDK..",
        ".SKGGKGGDK..",
        "SKGGK.KGDK..",
        ".KLGK.KGDK..",
        "KBBBBBBBBBK.",
        ".KKKKKKKKK..",
    ]
    HELMET_COL = 5  # his centre line: the rigging meets above it
    BASE_COLS = (0, 10)  # the base's two ends, where landing dust kicks out

    COLORS = {
        "C": (22, 34, 16), "N": (72, 110, 45), "O": (170, 145, 60), "M": (40, 62, 28),
        "*": (250, 250, 240),
        "K": (12, 50, 16), "L": (140, 215, 100), "G": (70, 165, 60), "D": (35, 105, 38),
        "R": (20, 68, 24), "S": (60, 140, 55), "B": (45, 120, 45),
    }
    RIG_RGB = (170, 170, 160)
    DUST_RGB = (190, 170, 120)
    RIG_GAP = 5  # rows between the canopy's hem and the top of his helmet

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = s = self.SCALE
        self.canopy_w, self.canopy_h = len(self.CANOPY_ART[0]) * s, len(self.CANOPY_ART) * s
        self.soldier_w, self.soldier_h = len(self.SOLDIER_ART[0]) * s, len(self.SOLDIER_ART) * s
        if height >= 64:
            self.FALL_S = self.FALL_S_TALL
            self.DROP_S = max(delay for _, delay in self.UNITS) + self.FALL_S
            self.duration = self.DROP_S + self.LAND_S + self.MARCH_S
        self.unit_h = self.canopy_h + self.RIG_GAP * s + self.soldier_h
        self.ground_top = height - self.soldier_h  # his top row once he's standing
        # The hop-off carries the leftmost soldier's whole sprite past the right edge.
        left = min(int(f * width) for f, _ in self.UNITS)
        self.march_dist = width - left + self.soldier_w
        self.prev_px = {}
        self.new_px = {}
        # Each soldier swings on his own phase so the three never sway in lockstep.
        self.sway_phase = [self.rng.uniform(0, 2 * math.pi) for _ in self.UNITS]

    def capture_prev(self, prev_draw, prev_t):
        """The old screen, still showing below the curtain."""
        self.prev_px = capture_screen(prev_draw, prev_t, self.width, self.height)

    def capture_new(self, draw_new, new_t):
        """The incoming screen, uncovered top-down above the curtain."""
        self.new_px = capture_screen(draw_new, new_t, self.width, self.height)

    # --- timing -------------------------------------------------------------------

    def _unit_land_time(self, delay):
        """When this soldier's base touches the ground."""
        return delay + self.FALL_S

    def _fall(self, delay, t):
        """0 before he starts falling, 1 at touchdown."""
        return max(0.0, min(1.0, (t - delay) / self.FALL_S))

    def _soldier_top(self, delay, t):
        """
        Top of his helmet: from just above the board down to standing on the bottom row.
        A parachute falls at a near-steady rate, so this only eases a little at the end
        rather than racing down and crawling in.
        """
        p = self._fall(delay, t)
        start = -self.soldier_h
        return start + (1 - (1 - p) ** 2) * (self.ground_top - start)

    def _sway(self, i, delay, t):
        """
        (canopy offset, soldier offset) for the pendulum: the canopy leads and the
        soldier trails it by a fraction of a swing, so the rigging tilts. The swing dies
        away over the last quarter of the fall so he lands upright.
        """
        p = self._fall(delay, t)
        amp = 2.0 * self.scale * min(1.0, (1 - p) / 0.25)
        a = self.sway_phase[i] + t * self.SWAY_HZ * 2 * math.pi
        return amp * math.sin(a), amp * 0.4 * math.sin(a - 0.9)

    def _curtain_y(self, t):
        """
        How far down the new screen is uncovered, 0 to height: the lead soldier's feet,
        so the board uncovers only what he's fallen past.
        """
        lead = min(delay for _, delay in self.UNITS)
        feet = self._soldier_top(lead, t) + self.soldier_h
        return max(0, min(self.height, int(feet)))

    def _march_start(self):
        return self.DROP_S + self.LAND_S

    def _hop(self, t):
        """
        (x offset, lift) for the hop-off, the same for all three so they move in step:
        HOPS hops, each easing across and arcing up HOP_H, landing flat between them.
        """
        since = t - self._march_start()
        if since <= 0:
            return 0, 0
        k, p = divmod(since / self.HOP_S, 1.0)
        if k >= self.HOPS:
            return self.march_dist, 0
        step = self.march_dist / self.HOPS
        eased = p * p * (3 - 2 * p)
        lift = 4 * p * (1 - p) * 4 * self.scale
        return int((k + eased) * step), int(round(lift))

    def _march_x(self, t):
        return self._hop(t)[0]

    def _last_hop_landing(self, t):
        """Seconds since his base last came down in the hop-off, or None mid-air/before."""
        since = t - self._march_start()
        if since <= 0:
            return None
        k, p = divmod(since / self.HOP_S, 1.0)
        if k < 1 or k > self.HOPS:
            return None
        return p * self.HOP_S

    # --- drawing -----------------------------------------------------------------

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        self._cy = self._curtain_y(t)
        for (x, y), rgb in self.new_px.items():
            if y < self._cy:
                canvas.SetPixel(x, y, *rgb)
        # Below the curtain, every pixel is the old screen's, black included: show_screen
        # has already drawn the new screen underneath, and it mustn't show through.
        for y in range(self._cy, self.height):
            for x in range(self.width):
                canvas.SetPixel(x, y, *self.prev_px.get((x, y), (0, 0, 0)))

        march, lift = self._hop(t)
        hop_age = self._last_hop_landing(t)
        # Slumped chutes lie on the ground behind the soldiers, so draw them all first.
        for i, (frac, delay) in enumerate(self.UNITS):
            since = t - self._unit_land_time(delay)
            if 0 <= since < self.COLLAPSE_S:
                self._draw_collapsing_chute(canvas, int(frac * self.width), since / self.COLLAPSE_S)
        for i, (frac, delay) in enumerate(self.UNITS):
            home = int(frac * self.width)
            since = t - self._unit_land_time(delay)
            if since < 0:
                canopy_dx, soldier_dx = self._sway(i, delay, t)
                top = int(round(self._soldier_top(delay, t)))
                self._draw_hanging(canvas, home + canopy_dx, home + soldier_dx, top)
            else:
                x = home + march
                self._draw_soldier(canvas, x, self.ground_top - lift)
                if since < self.DUST_S:
                    self._draw_dust(canvas, x, since / self.DUST_S, 1.0)
                elif hop_age is not None and hop_age < self.DUST_S * 0.7:
                    self._draw_dust(canvas, x, hop_age / (self.DUST_S * 0.7), 0.6)
        return True

    def _draw_hanging(self, canvas, canopy_cx, soldier_cx, soldier_top):
        """A falling soldier: canopy, rigging converging above his helmet, and him."""
        s = self.scale
        cx0 = int(round(canopy_cx)) - self.canopy_w // 2
        hem_y = soldier_top - self.RIG_GAP * s
        canopy_top = hem_y - self.canopy_h
        scx = int(round(soldier_cx))
        # The lines meet in a riser just above his helmet, as in the reference photo.
        meet = (scx, soldier_top - 2 * s)
        for col in self.RIG_COLS:
            self._line(canvas, cx0 + col * s, hem_y, meet[0], meet[1], self.RIG_RGB)
        self._line(canvas, meet[0], meet[1], scx, soldier_top - 1, self.RIG_RGB)
        self._blit(canvas, self.CANOPY_ART, cx0, canopy_top)
        self._draw_soldier(canvas, scx, soldier_top)

    def _draw_soldier(self, canvas, cx, top):
        self._blit(canvas, self.SOLDIER_ART, cx - self.HELMET_COL * self.scale, top)

    def _draw_collapsing_chute(self, canvas, home, p):
        """
        The landed chute losing its air: it blows downwind (the way they'll hop off),
        sinks behind him, flattens and spreads into a heap on the ground, then fades.
        """
        s = self.scale
        eased = ease_out(p)
        w = int(self.canopy_w * (1 + 0.2 * eased))
        h = max(2 * s, int(self.canopy_h * (1 - 0.75 * eased)))
        cx = home + int(7 * s * eased)
        landed_top = self.ground_top - self.RIG_GAP * s - self.canopy_h
        ground_heap = self.height - h
        top = int(round(landed_top + (ground_heap - landed_top) * eased))
        fade = 1.0 if p < 0.5 else 1 - (p - 0.5) / 0.5
        # Crumpled, the star is folded away: squashed, it would sample into a white bar.
        slumped = [row.replace("*", "M") for row in self.CANOPY_ART]
        self._blit_scaled(canvas, slumped, cx - w // 2, top, w, h, fade)

    def _draw_dust(self, canvas, cx, p, size):
        """A puff kicked out sideways from both ends of his base, spreading and fading."""
        x0 = cx - self.HELMET_COL * self.scale
        ends = (x0 + self.BASE_COLS[0] * self.scale, x0 + self.BASE_COLS[1] * self.scale)
        spread = (0.6 + 1.4 * p) * size * self.scale
        rise = int(round(p * 1.5 * self.scale))
        alpha = 0.75 * (1 - p)
        ground = self.height - 1
        for side, end in zip((-1, 1), ends):
            for dx, dy in ((1, 0), (2, 0), (2, -1), (3, 0), (3, -1), (4, -1), (5, -2)):
                x = end + side * int(round(dx * spread))
                y = ground + dy * self.scale - rise
                self._px_blend(canvas, x, y, self.DUST_RGB, alpha)

    # --- pixels ------------------------------------------------------------------

    def _under(self, x, y):
        """What's on the board beneath (x, y): the new screen above the curtain, the old below."""
        return (self.new_px if y < self._cy else self.prev_px).get((x, y), (0, 0, 0))

    def _px_blend(self, canvas, x, y, rgb, alpha):
        """Draw rgb at alpha over the screen beneath: soft things mustn't punch black holes."""
        if 0 <= x < self.width and 0 <= y < self.height:
            under = self._under(x, y)
            canvas.SetPixel(x, y, *(int(u + (c - u) * alpha) for c, u in zip(rgb, under)))

    def _line(self, canvas, x0, y0, x1, y1, rgb):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self._px(canvas, x0, y0, rgb)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def _blit(self, canvas, art, x0, y0):
        s = self.scale
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(s):
                    for sx in range(s):
                        self._px(canvas, x0 + col * s + sx, y0 + row * s + sy, self.COLORS[kind])

    def _blit_scaled(self, canvas, art, x0, y0, target_w, target_h, alpha=1.0):
        """Nearest-neighbour scale of art into a target_w x target_h box, faded to alpha."""
        src_w, src_h = len(art[0]), len(art)
        for py in range(target_h):
            row = art[min(src_h - 1, py * src_h // target_h)]
            for px in range(target_w):
                kind = row[min(src_w - 1, px * src_w // target_w)]
                if kind != ".":
                    self._px_blend(canvas, x0 + px, y0 + py, self.COLORS[kind], alpha)

    def _px(self, canvas, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)


class FalconReveal:
    """
    The Millennium Falcon, top-down with her nose to the right, drawn from a reference photo.
    She drops out of hyperspace over the old ride screen (the stars' streaks snap back into
    points as she brakes in from the left), cruises a beat, then her engine band flares and
    she jumps to lightspeed: she and the whole old screen stretch into streaks running off
    the right edge, a blue-white flash fills the board, and it fades to the new ride.

    Only on the Galaxy's Edge rides (disney.RIDE_VISITORS), never in the random rotation.
    Needs the old screen to stretch and the new one to fade up through the flash, so it
    opts into both wants_prev and wants_new.
    """

    wants_prev = True
    wants_new = True
    ARRIVE_S, CRUISE_S, CHARGE_S, JUMP_S, FLASH_S = 0.8, 0.9, 0.35, 0.55, 0.4
    PHASES = (("arrive", ARRIVE_S), ("cruise", CRUISE_S), ("charge", CHARGE_S),
              ("jump", JUMP_S), ("flash", FLASH_S))
    duration = sum(sec for _, sec in PHASES)

    # Traced from the photo turned nose-right, then only the bold features kept (the
    # panelling came out as grey noise): the gap between the mandibles, the turret ring,
    # the docking arms above and below it, rear spokes, a few red patches, the cockpit tube
    # hanging off the bottom edge (her starboard side, seen from above), and the engine
    # band along the back. '.' empty, K outline, H hull, L light hull, M panel seam,
    # D dark, R red, W cockpit window, E engine.
    ART = [
        ".......KKKKKKK..............",
        ".....KKHHHMDMHKK............",
        "....KHHHHHMDMHHHKK..........",
        "..KKMMHHHHMDMHHHHHK.........",
        "..EHHMMHHHMDMHHHHHHKK.......",
        ".EHHHHMMHHMDMHHHHHHHHKK.....",
        ".EMHHHHMMHMDMHHHHHHHRRHKK...",
        "EHMMMMHHMMHHHHHHHHHHHHHHHKK.",
        "EHHHHMMMHMDDDDHHHHHHHHHHHHHK",
        "EHHHRHHHMHDLLDHMMMMKKKKKKKK.",
        "EHHHHHHHHDDLLDDLLLK.........",
        "EHHHHHHHMHDLLDHMMMMKKKKKKKK.",
        "EHHHHMMMHMDDDDHHHHHHHHHHHHHK",
        "EHMMMMHHMMHHHHHHHHHHHHHHHKK.",
        ".EMHHHHRMHMDMHHHHHHHHHHKK...",
        ".EHHHHMMHHMDMHHHRHHHHKK.....",
        "..EHHMMHHHMDMHHHHHHKK.......",
        "...KMMHHHHMDMHHHHHK.........",
        "....KKHHHHMDMHHHHHHKKK......",
        "......KKKKKKKKHHHHHHWWK.....",
        "..............KKKKKKKKK.....",
    ]
    COLORS = {
        "K": (85, 85, 92), "H": (170, 170, 165), "L": (215, 215, 210), "M": (120, 120, 118),
        "D": (62, 62, 68), "R": (200, 55, 45), "W": (120, 170, 230), "E": (70, 150, 255),
    }
    ENGINE_HOT = (210, 240, 255)  # the engine band at full burn, as she jumps
    STREAK_RGB = (200, 220, 255)  # stars and her arrival trail
    FLASH_RGB = (225, 238, 255)
    STARS = 14

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        # Doubled on 64x64, where she fills the board without swamping it.
        self.scale = s = 2 if height >= 64 else 1
        self.ship_w, self.ship_h = len(self.ART[0]) * s, len(self.ART) * s
        self.y0 = (height - self.ship_h) // 2
        self.cruise_dx = 4 * s
        # Where she comes to a stop: her nose must still be on the board at the end of
        # the cruise, or the mandibles (half her silhouette) get clipped.
        self.hold_x = max(0, min(int(width * 0.1), width - 1 - self.ship_w - self.cruise_dx))
        self.prev_px, self.new_px = {}, {}
        self._base = {}
        # The rows her engine band sits on, for her arrival trail and the glow outside it.
        self.engine_rows = [r for r, row in enumerate(self.ART) if "E" in row]
        self.stars = [(self.rng.randrange(width), self.rng.randrange(height)) for _ in range(self.STARS)]

    def capture_prev(self, prev_draw, prev_t):
        self.prev_px = capture_screen(prev_draw, prev_t, self.width, self.height)

    def capture_new(self, draw_new, new_t):
        self.new_px = capture_screen(draw_new, new_t, self.width, self.height)

    def phase(self, t):
        """(name, 0..1 through it) for the part of the visit at t."""
        for name, sec in self.PHASES:
            if t < sec:
                return name, t / sec
            t -= sec
        return self.PHASES[-1][0], 1.0

    def phase_start(self, name):
        start = 0.0
        for n, sec in self.PHASES:
            if n == name:
                return start
            start += sec
        raise KeyError(name)

    def ship_span(self, t):
        """(rear x, nose x) of her drawn span: braking in, cruising, backing off, then stretching away."""
        name, p = self.phase(t)
        stop = self.hold_x + self.cruise_dx
        if name == "arrive":
            # The jump in reverse: her nose shoots in from the left edge and brakes hard,
            # while the long streak behind it snaps down to her own length.
            nose = self.ship_w + (self.hold_x) * (1 - (1 - p) ** 4)
            nose = int(nose * min(1.0, p / 0.12)) if p < 0.12 else int(nose)
            stretch = 1 + 9 * (1 - min(1.0, p / 0.6)) ** 3
            return int(nose - self.ship_w * stretch), nose
        elif name == "cruise":
            x = self.hold_x + self.cruise_dx * p
        elif name == "charge":
            x = stop - 2 * self.scale * ease_out(p)  # a little settle back before the jump
        else:
            base = stop - 2 * self.scale
            if name == "flash":
                return self.width, self.width
            # The nose leaves far faster than the tail: she stretches into a streak.
            rear = base + (self.width + 1 - base) * p ** 3
            nose = base + self.ship_w + (self.width + 8 * self.ship_w) * p ** 2
            return int(rear), int(nose)
        return int(x), int(x) + self.ship_w

    def engine_rgb(self, t):
        name, p = self.phase(t)
        heat = {"charge": p, "jump": 1.0, "flash": 1.0}.get(name, 0.0)
        cool = self.COLORS["E"]
        return tuple(int(c + (h - c) * heat) for c, h in zip(cool, self.ENGINE_HOT))

    def old_stretch(self, t):
        """(shift, stretch) of the old screen: nothing until she jumps, then it streaks off to the right."""
        name, p = self.phase(t)
        if name == "jump":
            return self.width * 1.3 * p ** 3, 1 + 7 * p ** 2
        if name == "flash":
            return float(self.width * 2), 8.0
        return 0.0, 1.0

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        name, p = self.phase(t)
        if name == "flash":
            self._draw_flash(canvas, p)
            return True
        self._draw_old_screen(canvas, t)
        if name == "arrive":
            self._draw_stars(canvas, p)
        self._draw_ship(canvas, t)
        return True

    def _draw_old_screen(self, canvas, t):
        """
        Every pixel, black included, so the new screen show_screen drew underneath can't
        show through. Once she jumps, each row is stretched and shifted right, so every
        pixel becomes a streak running off the edge.
        """
        shift, stretch = self.old_stretch(t)
        get = self.prev_px.get
        self._base = base = {}  # what's on the board now, for blending soft light over it
        for y in range(self.height):
            for x in range(self.width):
                sx = int((x - shift) / stretch)
                rgb = get((sx, y), (0, 0, 0)) if sx >= 0 else (0, 0, 0)
                base[(x, y)] = rgb
                canvas.SetPixel(x, y, *rgb)

    def _draw_stars(self, canvas, p):
        """Coming out of hyperspace: streaks snapping back into points, then fading."""
        snap = min(1.0, p / 0.55)
        length = int(round(22 * self.scale * (1 - snap) ** 2))
        alpha = 0.85 if p < 0.55 else 0.85 * max(0.0, 1 - (p - 0.55) / 0.45)
        for x, y in self.stars:
            for i in range(length + 1):
                self._blend(canvas, x - i, y, self.STREAK_RGB, alpha * (1 - i / (length + 1)))

    def _draw_ship(self, canvas, t):
        rear, nose = self.ship_span(t)
        w = nose - rear
        if w <= 0:
            return
        src_w = len(self.ART[0])
        engine = self.engine_rgb(t)
        # Stretched out at lightspeed she's a streak of light, not a long grey hull.
        streak = min(0.85, max(0.0, (w / self.ship_w - 1) / 4))
        for py in range(self.ship_h):
            row = self.ART[py // self.scale]
            y = self.y0 + py
            for px in range(w):
                kind = row[min(src_w - 1, px * src_w // w)]
                if kind != ".":
                    rgb = engine if kind == "E" else self.COLORS[kind]
                    if streak:
                        rgb = tuple(int(c + (h - c) * streak) for c, h in zip(rgb, self.STREAK_RGB))
                    self._px(canvas, rear + px, y, rgb)
        name, p = self.phase(t)
        if name in ("charge", "jump"):
            # The burn spills out behind the engine band.
            glow = p if name == "charge" else 1.0
            for r in self.engine_rows:
                for sy in range(self.scale):
                    y = self.y0 + r * self.scale + sy
                    edge = rear + self.ART[r].index("E") * w // src_w
                    for i in range(1, 3 * self.scale + 1):
                        self._blend(canvas, edge - i, y, engine, 0.7 * glow * (1 - i / (3 * self.scale + 1)))

    def _draw_flash(self, canvas, p):
        """The jump's flash, fading to the new screen beneath it."""
        alpha = (1 - p) ** 2
        get = self.new_px.get
        for y in range(self.height):
            for x in range(self.width):
                under = get((x, y), (0, 0, 0))
                canvas.SetPixel(x, y, *(int(u + (f - u) * alpha) for f, u in zip(self.FLASH_RGB, under)))

    def _blend(self, canvas, x, y, rgb, alpha):
        """Soft light over the (possibly stretched) old screen, never a black hole in it."""
        if 0 <= x < self.width and 0 <= y < self.height and alpha > 0:
            under = self._base.get((x, y), (0, 0, 0))
            canvas.SetPixel(x, y, *(int(u + (c - u) * alpha) for c, u in zip(rgb, under)))

    def _px(self, canvas, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)


TRANSITIONS = {
    "wipe": Wipe, "tink": TinkReveal, "buzz": BuzzReveal,
    "figment": FigmentReveal, "stitch": StitchReveal, "ralph": RalphReveal,
    "mickey": MickeyReveal, "slinky": SlinkyReveal, "baymax": BaymaxReveal,
    "dumbo": DumboReveal,
    "genie": GenieReveal,
    "slinky_wrap": SlinkyWrapReveal,
    "walle": WallEReveal,
    "walle_side": WallESideReveal,
    "army_men": ArmyMenReveal,
    "falcon": FalconReveal,
    "mike": MikeReveal,
    "tron": TronReveal,
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
        # A surprise that plays over a finished screen lets it keep animating underneath, and
        # so does a screen that asks to (plays_under_reveal: the Halloween pumpkin lights up as
        # it's uncovered); otherwise a reveal holds the screen at its first frame until it's
        # been uncovered.
        over = getattr(reveal, "over_screen", False) or getattr(draw_screen, "plays_under_reveal", False)
        last_t[0] = t_reveal if over else max(0.0, t_reveal - reveal.duration)
        moving = draw_screen(canvas, last_t[0])
        revealing = reveal.overlay(canvas, t_reveal)
        return bool(moving or revealing)

    drawn, spent = run_frames(matrix, frame, hold_s)
    _last_screen[id(matrix)] = (draw_screen, last_t[0])
    if transition != "wipe" and spent > 0:
        # A readout for checking characters on real boards: journalctl shows how close each gets.
        debug.info(f"{transition}: {drawn / spent:.0f} fps over {spent:.1f}s of animation (target {FPS})")
