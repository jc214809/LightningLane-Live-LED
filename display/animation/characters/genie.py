import math
import random

from display.animation.drawing import _blackout, art_pixels, paint
from display.animation.motion import FPS, ease_out


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
        cells = art_pixels(art, int(round(x0)), int(round(y0)), self.COLORS, self.LAMP_SCALE)
        paint(canvas, ((p, rgb) for p, rgb in cells if p[0] >= clip_x), self.width, self.height)

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
