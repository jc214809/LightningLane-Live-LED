import math
import random

from display.animation.drawing import paint
from display.animation.motion import ease_out, progress


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
        return progress(t, *self.GRIN)

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
        paint(canvas, self.pixels(t), self.width, self.height)
        return True
