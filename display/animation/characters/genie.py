import math
import random

from display.animation.drawing import art_pixels, paint
from display.animation.motion import FPS, ease_out


class GenieReveal:
    """
    Genie erupts from his lamp over the finished ride screen and flies off. Not a
    FlyByReveal: the first half of the run is an emerge, where he has no flight path at
    all -- a plume of smoke pours out of the lamp's spout and he scales up out of it from
    a point at the spout's tip to full size. Only then does he cross the board, and the
    lamp sinks away off the bottom edge.

    His trail is smoke rather than the point-like dust the fly-bys leave: each puff is a
    soft disc that grows and fades, drawn additively over whatever is already on the
    canvas so the revealed screen shows through it instead of being punched out.
    """

    EMERGE_S, FLY_S = 1.6, 2.0
    duration = EMERGE_S + FLY_S
    over_screen = True
    # How long the lamp takes to sink off the bottom once he has taken off.
    LAMP_SINK_S = 0.6

    # Genie rising out of his lamp, cell for cell from docs/references/genie.jpg: black
    # topknot with a red band, wide blue face, white eyes and grin, gold wrists, a red sash,
    # and a tail that curls down to his lamp.
    # '.' empty, B blue skin, b deep blue (ears, cuffs), S charcoal (hair, brows, pupils,
    # goatee; the pattern's near-black was brightened, or it vanished on the board),
    # W white, R red, Y wrist gold.
    ART = [
        ".........SSS.........",
        "........SSSS.........",
        "......SSSSS..........",
        "......SSSRR..........",
        "......S..BBB.........",
        "........SBBBS........",
        ".....B.SBSBSBS.B.....",
        ".....bBBWWBWWBBb.....",
        "......bBWSBSWBb......",
        "......BBBBBBBBB......",
        ".....BSWBBBBBWSB.....",
        ".....SBRWWWWWRBS.....",
        ".....SBRRRRRRRBS.....",
        ".....SBBWWWWWBBS.....",
        "....BBSBBBBBBBSBB....",
        "...BBBBSSSSSSSBBBB...",
        "..BBBBBBBBSSBBBBBBB..",
        ".YBBBBBBBSSBBBBBBBBY.",
        "BYYY.BbBBBBBBBbB.YYYB",
        "BBB..BBbbbBbbbBB..BBB",
        "......BBBBBBBBB......",
        ".......BBBBBBB.......",
        ".......RRRRRRR.......",
        ".......RRRRRRR.......",
        ".......BBBBBBB.......",
        ".......BBBBBBBB......",
        "........BBBBBBB......",
        "........BBBBBB.......",
        ".......BBBBB.........",
        "......BBBB...........",
        "......BBB............",
    ]
    # His lamp, from the same pattern and on the same columns: lid on top (where his tail
    # went in, in the pattern), handle on the left, spout tip turned up on the right, foot below. Its own
    # color keys, so it never borrows Genie's.
    # '.' empty, G lamp gold, O lid orange.
    LAMP_ART = [
        ".......OOO.....GG....",
        "......OOOOO.....G....",
        "..GGGGGGGGGGGGGG.....",
        "..GG.OGGGGGGGG.......",
        "..G...OOOGGG.........",
        ".......GGGG..........",
        "......GGGGGG.........",
        ".....GGGGGGGG........",
    ]
    # The spout's upturned tip (columns 15-16, top row), in lamp cells: smoke pours from
    # here and Genie grows out of it.
    LAMP_SPOUT = (16.0, 0.0)
    # The middle of his tail's tip, in Genie cells (columns 6-8): it sits over the spout.
    TAIL_X = 7.5
    # The lamp stays 1x on both boards: doubled, it swamps the 64x64 board under Genie.
    LAMP_SCALE = 1
    # Rows left out so he fits on his lamp: on 64x64 (Genie doubled, 62 + 8 rows) three
    # of the tail's; on 64x32 (39 rows) those, a hair row and a waist row, and two of the
    # lamp's foot.
    TRIM_64 = (25, 27, 29)
    TRIM_32 = (1, 21, 25, 27, 29)
    LAMP_TRIM_32 = (5, 6)
    COLORS = {
        "B": (136, 199, 239), "b": (35, 68, 241), "S": (70, 72, 105), "W": (254, 254, 254),
        "R": (204, 18, 19), "Y": (242, 232, 45),
        "G": (242, 232, 45), "O": (242, 146, 44),
    }
    SMOKE_COLORS = [(120, 160, 235), (150, 120, 225), (95, 130, 210), (185, 165, 245)]

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        big = height >= 64
        self.scale = 2 if big else 1
        trim = self.TRIM_64 if big else self.TRIM_32
        self.art = [row for i, row in enumerate(self.ART) if i not in trim]
        lamp_trim = () if big else self.LAMP_TRIM_32
        self.lamp_art = [row for i, row in enumerate(self.LAMP_ART) if i not in lamp_trim]
        self.sprite_w = len(self.art[0]) * self.scale
        self.sprite_h = len(self.art) * self.scale
        self.lamp_w = len(self.lamp_art[0]) * self.LAMP_SCALE
        self.lamp_h = len(self.lamp_art) * self.LAMP_SCALE
        self.lamp_x = 2
        self.lamp_y = height - self.lamp_h
        # Each puff: [x, y, vx, vy, frames_left, rgb, radius]
        self.puffs = []
        self.last_frame = -1

    def spout(self):
        """Where the smoke leaves the lamp (its spout's tip), and the point Genie scales up out of."""
        return (self.lamp_x + self.LAMP_SPOUT[0] * self.LAMP_SCALE,
                self.lamp_y + self.LAMP_SPOUT[1] * self.LAMP_SCALE)

    def lamp_top(self, t):
        """The lamp's top row: on the bottom edge, then sinking off it once he takes off."""
        sink = max(0.0, min(1.0, (t - self.EMERGE_S) / self.LAMP_SINK_S))
        return self.lamp_y + round(ease_out(sink) * self.lamp_h)

    def grow(self, t):
        """0 (not yet formed) to 1 (full size). Smoke pours alone for the first third."""
        if t >= self.EMERGE_S:
            return 1.0
        return ease_out(max(0.0, t - self.EMERGE_S * 0.35) / (self.EMERGE_S * 0.65))

    def position(self, t):
        """The sprite's top-left at full size: parked over the lamp, then crossing right."""
        # Sitting on the lamp with the tip of his tail on the spout.
        home_x = float(math.floor(self.spout()[0] - self.TAIL_X * self.scale + 0.5))
        home_y = max(0.0, float(self.lamp_y - self.sprite_h))
        if t < self.EMERGE_S:
            return home_x, home_y
        p = (t - self.EMERGE_S) / self.FLY_S
        # Accelerating away, so he lingers on board before whipping off the right edge.
        x = home_x + (p * p * 0.35 + p * 0.65) * (self.width + self.sprite_w - home_x)
        y = home_y - math.sin(p * math.pi) * self.height * 0.18
        return x, max(0.0, min(y, self.height - self.sprite_h))

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
        self._draw_puffs(canvas)
        if t < self.duration:
            self._draw_art(canvas, self.lamp_art, self.lamp_x, self.lamp_top(t))
            self._draw_genie(canvas, t)
        return t < self.duration or bool(self.puffs)

    def _draw_art(self, canvas, art, x0, y0):
        paint(canvas, art_pixels(art, int(round(x0)), int(round(y0)), self.COLORS, self.LAMP_SCALE),
              self.width, self.height)

    def _full_pixels(self):
        """(dx, dy, rgb) for every lit pixel of Genie at full size, worked out once."""
        if getattr(self, "_full", None) is None:
            s = self.scale
            self._full = [(col * s + sx, row * s + sy, self.COLORS[kind])
                          for row, line in enumerate(self.art) for col, kind in enumerate(line) if kind != "."
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
        for row, line in enumerate(self.art):
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
