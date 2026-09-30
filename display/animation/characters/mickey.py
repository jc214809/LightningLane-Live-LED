import math
import random

from display.animation.drawing import _blackout, art_pixels, paint
from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS, ease_out


class MickeyReveal(CapturesScreens):
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
        """The incoming screen's pixels are what materializes."""
        super().capture_new(draw_new, new_t)
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
        paint(canvas, art_pixels(self.ART, 0, int(round(y0)), self.COLORS, self.scale), self.width, self.height)
