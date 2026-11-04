import math
import random

from display.animation.characters.aliens import _text_cells
from display.animation.drawing import art_pixels, paint
from display.animation.mechanics import CapturesScreens
from display.motion import ease_out, ramp
from display.pixels import rotate_art


class ForkyReveal(CapturesScreens):
    """
    Forky waddles in from the left over the old ride, stops, and spots it: TRASH! He hops,
    flips over and dives head first through the bottom of the board, and the old screen is
    pulled down into the hole after him, nearest first, uncovering the new ride, while his
    feet kick out of the top of it. Then they slip in too. Needs the previous screen's
    pixels, so it opts in via wants_prev.
    """

    wants_prev = True
    WALK_S, SPOT_S, HOP_S, DIVE_S, SUCK_S, SINK_S = 1.3, 0.9, 0.45, 0.35, 0.9, 0.3
    duration = WALK_S + SPOT_S + HOP_S + DIVE_S + SUCK_S + SINK_S
    STEPS_PER_S = 6
    HOP_ROWS = 5       # how far he springs up (1x rows)
    FEET_OUT = 7       # rows of him left sticking out of the hole (1x rows): his base and feet, not his arms

    # From the user's pattern (docs/references/Forky.jpg), copied cell for cell: a white
    # spork, the red unibrow, two mismatched eye holes (left big, right small), the blue
    # mouth, red pipe-cleaner arms and tan popsicle-stick feet. The eye holes are filled in
    # code as googly eyes: a grey ring with a black pupil that rolls as he moves (a white
    # eye would vanish into his white head). 1x on 64x32, 2x on 64x64.
    # '.' empty, W white, R red, B blue, F feet, E an eye (filled per frame).
    ART = [
        "........W.W.W.W........",
        ".......WW.W.W.WW.......",
        "......WWWWWWWWWWW......",
        "......WWWRRRRRRWW......",
        ".....WWRRRWWWWRRWW.....",
        ".....WWRWWWWWWWRWW.....",
        ".....WWWEEWWWWWWWW.....",
        ".....WWEEEEWWEEWWW.....",
        ".....WWEEEEWWEEWWW.....",
        ".....WWWEEWWWWWWWW.....",
        "......WWWWWWWBBWW......",
        "......WWWBBBBWBWW......",
        ".......WWWBWWBWW.......",
        "........WWWBBWW........",
        "....R....WWWWW....R....",
        ".R..R.....WWW.....R..R.",
        ".RR.R.....WWW.....R.RR.",
        "..RRRR...RRRRR...RRRR..",
        "RRRRRRR.RRRRRRR.RRRRRRR",
        ".....RRR.WWW.RRR.......",
        ".......R..WWW..R.......",
        "..........WWW..........",
        "..........WWW..........",
        "..........WWW..........",
        ".........WWWWW.........",
        "........WWWWWWW........",
        "........WWWWWWW........",
        ".......FFFF.FFFF.......",
    ]
    SCALE = 1  # the editor previews the 64x32 size; 64x64 draws it at 2x
    COLORS = {
        "W": (235, 235, 235), "R": (220, 30, 30), "B": (20, 90, 250), "F": (240, 200, 150),
        "G": (130, 130, 140), "P": (0, 0, 0),
    }
    EDGE_RGB = (0, 0, 0)   # a ring round him, so he stands off the old screen's text
    ARM_ROW = 14           # arms start here (the brow above is red too)
    EYES = ((7, 6, 4), (13, 7, 2))  # (col, row, size) of each eye's box; the big one has its corners cut
    TEXT = "TRASH!"
    TEXT_RGB = (255, 230, 60)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.tall = height >= 64
        self.scale = 2 if self.tall else 1
        self.art_w, self.art_h = len(self.ART[0]), len(self.ART)
        self.w, self.h = self.art_w * self.scale, self.art_h * self.scale
        self.ground = height - self.h          # his top row, feet on the bottom row
        # 64x64: centred, TRASH! over his head. 64x32: no room overhead, so he stops left
        # of centre and it goes beside him.
        self.stop_x = (width - self.w) // 2 if self.tall else 6
        cells, (tw, th) = _text_cells(self.TEXT, "5x8.bdf")
        if self.tall:
            tx, ty = (width - tw) // 2, max(0, self.ground - th - 1)
        else:
            tx, ty = self.stop_x + self.w + 3, self.ground + 4
        self.text = [(tx + x, ty + y) for x, y in cells]
        self.hole_x = self.stop_x + self.w / 2
        self.prev_order = self.prev_dark = None

    @property
    def spot_at(self):
        return self.WALK_S

    @property
    def hop_at(self):
        return self.WALK_S + self.SPOT_S

    @property
    def dive_at(self):
        return self.hop_at + self.HOP_S

    @property
    def suck_at(self):
        return self.dive_at + self.DIVE_S

    @property
    def sink_at(self):
        return self.suck_at + self.SUCK_S

    def forky_x(self, t):
        """His left edge: waddles in from off the left and stops."""
        if t >= self.WALK_S:
            return self.stop_x
        return int(round(-self.w + ease_out(t / self.WALK_S) * (self.stop_x + self.w)))

    def forky_y(self, t):
        """His top row, upright until the hop's peak, then the top of the flipped art."""
        s = self.scale
        if t < self.hop_at:
            return self.ground
        if t < self.dive_at:
            p = ramp(t, self.hop_at, self.HOP_S)
            return self.ground - int(round(math.sin(p * math.pi / 2) * self.HOP_ROWS * s))
        out = self.height - self.FEET_OUT * s
        if t < self.suck_at:
            p = ramp(t, self.dive_at, self.DIVE_S)
            top = self.ground - self.HOP_ROWS * s
            return int(round(top + p * p * (out - top)))
        if t < self.sink_at:
            return out
        return int(round(out + ramp(t, self.sink_at, self.SINK_S) * self.FEET_OUT * s))

    def flipped(self, t):
        return t >= self.dive_at

    def look(self, t):
        """Where his pupils sit in their eyes, each -1..1: rolling side to side as he waddles,
        settling once he stops, then down at the old ride, and wild on the way down."""
        if t < self.WALK_S:
            return math.sin(t * self.STEPS_PER_S * math.pi), 0.0
        if t < self.hop_at:
            since = t - self.WALK_S
            settle = math.exp(-since * 5) * math.cos(since * 25)
            return settle, min(1.0, since * 3)
        return math.sin(t * 30), math.cos(t * 23)

    def _art(self, t):
        """ART at t: googly eyes filled in, arms flapping as he shouts, flipped for the dive."""
        rows = [list(r) for r in self.ART]
        lx, ly = self.look(t)
        for col, row, size in self.EYES:
            box = [(col + dx, row + dy) for dy in range(size) for dx in range(size)
                   if rows[row + dy][col + dx] == "E"]
            pupil = max(1, size // 2)
            px = col + int(round((lx + 1) / 2 * (size - pupil)))
            py = row + int(round((ly + 1) / 2 * (size - pupil)))
            for x, y in box:
                rows[y][x] = "P" if px <= x < px + pupil and py <= y < py + pupil else "G"
        if self.spot_at <= t < self.hop_at and int((t - self.spot_at) * 8) % 2 == 0:
            for r in range(self.ARM_ROW, self.art_h):
                for c, k in enumerate(rows[r]):
                    if k == "R":
                        rows[r - 1][c], rows[r][c] = "R", ("W" if self.ART[r][c] == "W" else ".")
        art = ["".join(r) for r in rows]
        return rotate_art(art, 2) if self.flipped(t) else art

    def _forky_px(self, t):
        art = self._art(t)
        x0, y0 = self.forky_x(t), self.forky_y(t)
        if not self.flipped(t) and t < self.WALK_S:
            # Waddle: a bob each step and his top half leaning into it.
            step = int(t * self.STEPS_PER_S)
            lean = 1 if step % 2 else -1
            px = {}
            for (x, y), rgb in art_pixels(art, x0, y0 - (step % 2) * self.scale, self.COLORS, self.scale):
                px[(x + (lean * self.scale if y - y0 < self.h // 2 else 0), y)] = rgb
            return px
        if self.suck_at <= t < self.sink_at:
            x0 += self.scale if int(t * 12) % 2 else -self.scale  # feet kicking
        return dict(art_pixels(art, x0, y0, self.COLORS, self.scale))

    def _order_prev(self):
        """The old screen's lit pixels with when each one's pulled in: nearest the hole first."""
        far = math.hypot(max(self.hole_x, self.width - self.hole_x), self.height)
        reach = lambda x, y: math.hypot(x - self.hole_x, y - self.height) / far * 0.65
        self.prev_order = [(x, y, rgb, reach(x, y) + self.rng.uniform(0, 0.1))
                           for (x, y), rgb in self.prev_px.items()]
        # Its dark pixels stay black until the hole reaches them, then simply go.
        self.prev_dark = [((x, y), reach(x, y) + 0.05) for x in range(self.width) for y in range(self.height)
                          if (x, y) not in self.prev_px]

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        if t < self.suck_at:
            # The old screen whole, every pixel of it, black included: show_screen has
            # already drawn the new screen underneath.
            frame = {(x, y): (0, 0, 0) for x in range(self.width) for y in range(self.height)}
            frame.update(self.prev_px)
            paint(canvas, frame, self.width, self.height)
        else:
            self._draw_suck(canvas, ramp(t, self.suck_at, self.SUCK_S + self.SINK_S * 0.5))
        forky = self._forky_px(t)
        edge = {(x + dx, y + dy) for x, y in forky for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        paint(canvas, [(p, self.EDGE_RGB) for p in edge - forky.keys()], self.width, self.height)
        paint(canvas, forky, self.width, self.height)
        if self.spot_at <= t < self.hop_at + self.HOP_S / 2:
            lift = 1 if t - self.spot_at < 0.08 else 0  # pops up into place
            lit = [(x, y - lift) for x, y in self.text]
            ring = {(x + dx, y + dy) for x, y in lit for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
            paint(canvas, [(p, self.EDGE_RGB) for p in ring - set(lit)] + [(p, self.TEXT_RGB) for p in lit],
                  self.width, self.height)
        return True

    def _draw_suck(self, canvas, p):
        """The old screen pulled into the hole, `p` 0..1 through it: until its turn each lit
        pixel stays put, then it falls into the hole and is gone."""
        if self.prev_order is None:
            self._order_prev()
        hx, hy = self.hole_x, self.height
        paint(canvas, [(xy, (0, 0, 0)) for xy, gone in self.prev_dark if p < gone], self.width, self.height)
        px = []
        for x, y, rgb, start in self.prev_order:
            if p < start:
                px.append(((x, y), rgb))
                continue
            k = min(1.0, (p - start) / 0.3)
            k *= k
            fx, fy = int(round(x + (hx - x) * k)), int(round(y + (hy - y) * k))
            if fy < self.height:
                px.append(((fx, fy), rgb))
        paint(canvas, px, self.width, self.height)
