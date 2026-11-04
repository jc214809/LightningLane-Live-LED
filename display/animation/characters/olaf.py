import math
import random

from display.animation.drawing import paint
from display.animation.motion import ease_out, progress


class OlafReveal:
    """
    Olaf builds himself over the finished ride screen while snow falls over the board: the
    bottom snowball rolls in from the left and pops up onto its two little feet, the middle
    one rolls in from the right and hops up onto it, and his head drops in from the top.
    His face, twig arms and hair pop on, he waves, then walks off the right edge and the
    snow stops. The snowballs, feet and snow are drawn in code like Baymax, since fixed art
    can't roll or step smoothly; his head is hand-drawn art from the user's references,
    because at this size code put his eyes, carrot and mouth in the wrong places.
    """

    over_screen = True
    BOTTOM = (0.15, 0.85)  # rolls in from the left...
    FEET = (0.85, 1.0)  # ...and pops up onto its feet
    MIDDLE = (0.75, 1.35)  # rolls in from the right...
    MIDDLE_HOP = (1.35, 1.65)  # ...and hops up onto the bottom one
    HEAD = (1.6, 2.0)  # drops in from the top
    FACE_S, ARMS_S, HAIR_S = 2.1, 2.25, 2.4  # then the rest pops on
    WAVE = (2.5, 3.5)
    WALK = (3.6, 5.0)  # walks off the right edge; the snow stops starting new flakes
    STEPS = 5
    duration = WALK[1]

    # His head, the biggest part of him, turned three-quarters like the user's references:
    # tall and leaning, round eyes in light-blue rims up top with dark brows, the carrot
    # pointing down, and the mouth a tall D down the left side, dark along its left edge and
    # bottom with his big buck tooth white under the sloping lip. 64x64 gets the BRIK
    # pixel-art Olaf cell for cell (its black made dark grey, since LEDs draw black as off);
    # 64x32 a redraw of it shrunk to fit. Both are 1x. '.' empty, E rim, W snow, S shade,
    # K eye rim, P pupil, R brow, O carrot, M mouth, B twig hair.
    HEAD_ART = [
        ".......B.B..B...",
        "........B.BB....",
        "........EEEE....",
        ".......EWWWWE...",
        "......EWWWWWWE..",
        ".....EWRRRWRRRE.",
        "....EWWKKWWKKWE.",
        "...EWWKWPKKWPKE.",
        "...EWWKWPKKWPKE.",
        "...EWWWKKOOKKWE.",
        "..EWWWWWWOOOWWE.",
        "..EWMWWWWWOOWWE.",
        ".EWWMMWWWWOWWWE.",
        ".EWWMMMWWWWWWWE.",
        ".EWWMMWMMWWWWE..",
        ".EWWMMWWWMMWWE..",
        ".EWWMMMWWWWMWE..",
        ".EWWMMMMMMMWE...",
        ".EWWMMMMMMWE....",
        "EWWWWMMMMWE.....",
        "EWWWWWWWWE......",
        ".EEEEEEEE.......",
    ]
    BIG_HEAD_ART = [
        "............B...B....",
        ".............B..B....",
        ".............B.B.BB..",
        "..........EEEEB.B..B.",
        ".........EWWWWE......",
        "........EWRRRWWE.....",
        ".......EWRWWWWWWE....",
        "......EWKKKKWWRRWE...",
        "...EEEWKWWWWKKKPWE...",
        "..EWWWWKWPPWWWWKWE...",
        "..EWWWWKWPPWPPWKWE...",
        ".EWWWWWWKKOOOPWKWE...",
        ".EWWWWWWWOOOOOKKWE...",
        ".EWWMWWWWOOOOOWWWWE..",
        ".EWWMMWWWWOOOWWWWWE..",
        "EWWWMMMWWWWWWWWWWWE..",
        "EWWWMMWMWWWWWWWWWWE..",
        "EWWWMMWWMMWWWWWWWWE..",
        ".EWWMMWWWWMMWWWWWE...",
        ".EWWMMMWWWWWMMWWE....",
        ".EWWMMMMWWWMMWWE.....",
        ".EWWMMMMMMMMWWE......",
        ".EWWMMMMMMMWWE.......",
        "EWWWWMMMMMWWE........",
        "EWWWWWWWWWWE.........",
        "EWWWWWWWWWE..........",
        ".EWWWWWWWE...........",
        "..EEEEEEE............",
    ]
    HEAD_SCALE = BIG_HEAD_SCALE = 1

    WHITE = (245, 248, 255)
    SHADE = (175, 190, 215)
    EDGE = (110, 125, 155)
    COAL = (40, 40, 48)
    CARROT = (255, 130, 30)
    TWIG = (130, 85, 45)
    MOUTH = (40, 40, 46)  # the reference's black, lifted so the LEDs show it
    FLAKE = (255, 255, 255)
    EYE_RING = (110, 165, 230)
    BROW = (70, 50, 45)
    colors = {"E": EDGE, "W": WHITE, "S": SHADE, "K": EYE_RING, "P": COAL, "O": CARROT,
              "M": MOUTH, "R": BROW, "B": TWIG}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        s = self.s = 2 if height >= 64 else 1  # the snowballs, feet and steps double on 64x64
        self.head_art = self.BIG_HEAD_ART if height >= 64 else self.HEAD_ART
        self.cx = round(self.rng.uniform(0.3, 0.55) * width)
        # Each snowball's half-width, half-height and standing centre height, bottom up. On
        # 64x32 feet, snowballs and a 22-row head fill all 32 rows.
        self.foot = (1.7 * s, 1.0 * s, height - 1.0 * s)
        self.bottom = (4.4 * s, 3.2 * s, height - 1.6 * s - 3.2 * s)
        self.middle = (2.8 * s, 2.0 * s, self.bottom[2] - 4.2 * s)
        head_rows = len(self.head_art)
        head_bottom = self.middle[2] - self.middle[1] + 1
        self.head = (len(self.head_art[0]) / 2, head_rows / 2, head_bottom - head_rows / 2)
        # His body sits under his jaw, not under the middle of the art (his cranium leans right).
        last = self.head_art[-1]
        self.neck_col = (len(last) - len(last.lstrip(".")) + len(last.rstrip(".")) - 1) / 2
        # Snowflakes: where each starts across the board, how fast it falls, when it starts.
        self.flakes = [(self.rng.uniform(0, width), self.rng.uniform(8, 14) * s,
                        self.rng.uniform(0, 1.0), self.rng.uniform(0, 2 * math.pi))
                       for _ in range(16 * s)]

    def _phase(self, t, span):
        return progress(t, *span)

    def walk(self, t):
        """(dx, bob, stride): how far he's walked, his body's bob, and the step's angle."""
        p = self._phase(t, self.WALK)
        if p <= 0:
            return 0.0, 0.0, None
        stride = p * self.STEPS * math.pi
        return p * (self.width - self.cx + 12 * self.s), -abs(math.sin(stride)) * 0.8 * self.s, stride

    def parts(self, t):
        """[(name, cx, cy)] of the snowballs that are on the board at t, before he walks."""
        out = []
        rx, ry, cy = self.bottom
        if t >= self.BOTTOM[0]:
            x0 = -rx - 1
            rolling_cy = self.height - ry
            y = rolling_cy + (cy - rolling_cy) * self._phase(t, self.FEET)
            out.append(("bottom", x0 + (self.cx - x0) * ease_out(self._phase(t, self.BOTTOM)), y))
        rx, ry, cy = self.middle
        if t >= self.MIDDLE[0]:
            x0 = self.width + rx + 1
            x = x0 + (self.cx - x0) * ease_out(self._phase(t, self.MIDDLE))
            ground = self.height - ry
            h = self._phase(t, self.MIDDLE_HOP)
            # An arc up and over onto the bottom ball, landing at its resting height.
            y = ground + (cy - ground) * h - math.sin(h * math.pi) * 3 * self.s
            out.append(("middle", x, y))
        rx, ry, cy = self.head
        if t >= self.HEAD[0]:
            # It drops in from above the board, speeding up as it falls.
            p = self._phase(t, self.HEAD)
            out.append(("head", self.cx, -ry + (cy + ry) * p * p))
        return out

    def feet(self, t):
        """[(cx, cy)] of his two feet, stepping while he walks; [] before they pop out."""
        if t < self.FEET[0]:
            return []
        rx, ry, cy = self.foot
        pop = self._phase(t, self.FEET)
        _, _, stride = self.walk(t)
        out = []
        for i, side in enumerate((-1, 1)):
            x, y = self.cx + side * 2.2 * self.s, cy + (1 - pop) * ry
            if stride is not None:
                # The feet take turns: each swings forward, lifted, while the other pushes back.
                swing = math.sin(stride + i * math.pi)
                x += swing * 1.4 * self.s
                y -= max(0.0, swing) * 1.2 * self.s
            out.append((x, y))
        return out

    def waving(self, t):
        """-1..1 swing of his raised right arm while he waves; 0 otherwise."""
        a, b = self.WAVE
        return math.sin((t - a) * 4 * math.pi) if a <= t < b else 0.0

    def snow(self, t):
        """[(x, y)] of the snowflakes falling over the whole board at t."""
        out = []
        span = self.height + 2
        for k, (x0, speed, start, sway) in enumerate(self.flakes):
            if t < start:
                continue
            fallen = (t - start) * speed
            # No new flakes once he starts to walk off; the ones already falling finish.
            if start + (fallen // span) * span / speed >= self.WALK[0]:
                continue
            out.append((int(round(x0 + math.sin(t * 2 + sway) * 0.8 * self.s)) % self.width,
                        int(fallen % span) - 1))
        return out

    def _blob(self, px, cx, cy, rx, ry, roll=None):
        """A shaded snowball; `roll` (radians) puts a speck on it that turns as it rolls."""
        for y in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
            for x in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
                def inside(ax, ay):
                    return ((ax + 0.5 - cx) / rx) ** 2 + ((ay + 0.5 - cy) / ry) ** 2 <= 1.0
                if not inside(x, y):
                    continue
                shade = max(1, int(round(0.8 * self.s)))
                if not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[(x, y)] = self.EDGE
                elif not inside(x + shade, y + shade):
                    px[(x, y)] = self.SHADE
                else:
                    px[(x, y)] = self.WHITE
        if roll is not None:
            px[(int(round(cx + 0.55 * rx * math.cos(roll))), int(round(cy + 0.55 * ry * math.sin(roll))))] = self.SHADE

    def _line(self, px, x0, y0, x1, y1, rgb):
        n = max(1, int(round(max(abs(x1 - x0), abs(y1 - y0)))))
        for i in range(n + 1):
            px[(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)))] = rgb

    def _draw_head(self, px, hx, hy, face, hair):
        """
        The head art with its jaw over hx, centred on hy. Before his face pops on it's blank
        snow (the rim kept), and his hair comes on last.
        """
        art = self.head_art
        x0 = int(round(hx - self.neck_col))
        y0 = int(round(hy - len(art) / 2))
        for row, line in enumerate(art):
            for col, kind in enumerate(line):
                if kind == "." or kind == "B" and not hair:
                    continue
                if not face and kind not in "EWSB":
                    # Blank snow inside his rim; the carrot's tip past the rim isn't there yet.
                    if not ("E" in line[:col] and "E" in line[col + 1:]):
                        continue
                    kind = "W"
                px[(x0 + col, y0 + row)] = self.colors[kind]

    def pixels(self, t):
        """Every pixel he and the snow cover at time t, {(x, y): rgb}, clipped to the board."""
        if t >= self.duration:
            return {}
        s = self.s
        dx, bob, _ = self.walk(t)
        out = {(x, y): self.FLAKE for x, y in self.snow(t) if 0 <= y < self.height}

        body = {}
        for fx, fy in self.feet(t):
            self._blob(body, fx + dx, fy, *self.foot[:2])
        parts = self.parts(t)
        where = {name: (x + dx, y + bob) for name, x, y in parts}
        for name, x, y in parts:
            x, y = where[name]
            rx, ry, _ = getattr(self, name)
            if name == "head":
                self._draw_head(body, x, y, face=t >= self.FACE_S, hair=t >= self.HAIR_S)
                continue
            rolling = name == "bottom" and t < self.BOTTOM[1] or name == "middle" and t < self.MIDDLE[1]
            self._blob(body, x, y, rx, ry, roll=(x / rx) if rolling else None)
            if name == "middle" and "head" in where and t >= self.ARMS_S:
                for side in (-1, 1):
                    sx, sy = x + side * 2.6 * s, y - 0.3 * s
                    lift = 3.0 * s + (2.5 * s * self.waving(t) if side == 1 else 0.0)
                    ex, ey = sx + side * 4.5 * s, sy - lift
                    self._line(body, sx, sy, ex, ey, self.TWIG)
                    # a twig finger forking off near the end
                    self._line(body, ex - side * 1.2 * s, ey + 0.3 * s * (lift / (3.0 * s) if lift else 1),
                               ex - side * 0.4 * s, ey - 1.4 * s, self.TWIG)
        if "head" in where and t >= self.FACE_S:
            hx, _ = where["head"]
            # Coal buttons: one on the middle snowball, two on the bottom one.
            for bx, by in ((-0.5, where["middle"][1] + 0.3 * s),
                           (-0.5, where["bottom"][1] - 1.3 * s), (1.5 * s, where["bottom"][1] + 0.9 * s)):
                for ddx in range(s):
                    for ddy in range(s):
                        body[(int(round(hx + bx)) + ddx, int(round(by)) + ddy)] = self.COAL
        for (x, y), rgb in body.items():
            if 0 <= x < self.width and 0 <= y < self.height:
                out[(x, y)] = rgb
        return out

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        paint(canvas, self.pixels(t), self.width, self.height)
        return True
