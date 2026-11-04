import math

from display.animation.drawing import walking_pixels
from display.animation.motion import FPS
from display.motion import progress, smooth
from display.pixels import art_pixels, paint


class KevinReveal:
    """
    Kevin and Dug, from Up, over the finished ride screen. Kevin struts across from left to
    right, her head pumping forward with each step, and Dug chases after her with a bunch of
    balloons tied to him. He starts on the ground, trotting, and the balloons lift him slowly
    higher as he goes, so he floats off the right edge up high while she struts off it on the
    ground. Both are 1x on both boards; on 64x32 Kevin's neck is shortened to fit.
    """

    over_screen = True
    SCALE = 1
    STEP = 1  # pixels a frame, steady: uneven steps judder at 1x (see Figment)
    POSE_F = 3  # frames each pose of her walk (drawing.WALK_CYCLE)
    DUG_BEHIND = 18  # Dug's left edge this far behind Kevin's
    TROT_F = 4  # frames per bob of Dug's trot, while he's still on the ground
    LIFT_EASE = 2  # his height grows as (share of the way across) ** LIFT_EASE: gently at first
    SWAY = 1  # columns the balloons sway each way
    SWAY_S = 2.4
    KNOT_ABOVE = 4  # rows from the knot down to the top of Dug's head

    # Kevin, copied cell for cell from the user's grid pattern (docs/references/Kevin.jpg),
    # facing right, with a spare column for her head to pump into. The pattern's light grey
    # drop shadow and a stray red cell on her leg are left out; her black legs and eye are
    # lifted to charcoal, since LEDs draw black as off. '.' empty, L plume, C cyan, B blue,
    # Y yellow, k eye, R red (beak), r crimson, P lilac, A dark red (tail), O orange, G legs.
    KEVIN_ART = [
        "....LCL............",
        "...LLLLL...........",
        "...CLLLLBB.........",
        "...LLLLBYYB........",
        "...CLLBBYkYYYYRR...",
        "......BBBYYYYYYRR..",
        ".......BBB.......R.",
        "........B..........",
        "........B..........",
        "........B..........",
        "........B..........",
        "........B..........",
        "........BB.........",
        "........BB.........",
        "........BB.........",
        ".......BBBB........",
        "......CBBBB........",
        ".....CCBBBBY.......",
        "....CCBPrRROY......",
        "....BBBPrRROY......",
        "...BBBPPrRROY......",
        "...BBBPrRROYY......",
        "..BBBPPrRROYY......",
        "..BBPPrrRROYY......",
        "..PPArrRROYY.......",
        "..PArrRROYYY.......",
        "...ArrRROYY........",
        "..AArrGYYYG........",
        ".AAArGY..G.........",
        "AA..G....G.........",
        "....G....G.........",
        "....G....G.........",
        "....G....G.........",
        "....G....G.........",
        "....G....G.........",
        "....G....G.........",
        "....G....G.........",
        "...GGGG.GGGG.......",
    ]
    HEAD_ROWS = 7  # what pumps forward
    NECK = (7, 15)  # her neck's rows; 64x32 keeps only the first and last
    FEET_ROWS = 9  # legs and feet, from the bottom
    BEHIND, AHEAD = {3, 4, 5, 6}, {8, 9, 10, 11}  # columns of each leg and foot

    # Dug, redrawn at 14 x 17 from the user's pattern (docs/references/Dug.jpg, 22 x 27),
    # sitting, facing us: grey ears, eyes, his big nose, open mouth and tongue, front paws.
    # Black lifted to charcoal. '.' empty, D gold, S grey, k charcoal, W white, T tongue, s tooth.
    DUG_ART = [
        "..DD......DD..",
        ".DDDDDDDDDDDD.",
        ".DSDDDDDDDDSD.",
        "DSSDkWDDkWDSSD",
        "DSDDDDDDDDDDSD",
        "DSDDkkkkkkDDSD",
        "DDDkkkkkkkkDDD",
        "DDDkkkkkkkkDDD",
        ".DDDkkkkkkDDD.",
        "..SDDDDDDDDS..",
        "..kSSSSSSSSk..",
        "..kkDTTTTDkk..",
        "..DksTTTkkkD..",
        "..DDDDDDDDDD..",
        ".DDSDDDDDDSDD.",
        "DDSDSDDDDSDSDD",
        "..SDDS..SDDS..",
    ]
    colors = {"L": (200, 200, 205), "C": (1, 230, 230), "B": (10, 20, 252), "Y": (252, 240, 1),
              "k": (45, 35, 30), "R": (253, 0, 1), "r": (203, 25, 49), "P": (210, 113, 252),
              "A": (138, 1, 1), "O": (253, 137, 0), "G": (70, 70, 70),
              "D": (252, 180, 40), "S": (110, 100, 90), "W": (255, 255, 255), "T": (230, 80, 120),
              "s": (171, 170, 166)}

    # The balloons, Up's mix, 3 x 3 with the bottom corners off and a pale shine top left.
    # BUNCH is each one's top-left corner from the knot; the lower ones have strings.
    BALLOON_RGB = [(230, 30, 40), (250, 210, 20), (40, 110, 250), (40, 200, 70), (250, 110, 180),
                   (255, 130, 20), (160, 70, 230), (90, 200, 250)]
    BUNCH = [(-6, -9), (-3, -10), (0, -11), (3, -10), (-7, -6), (-4, -7), (-1, -8), (2, -7), (5, -7),
             (-5, -4), (-2, -5), (1, -4), (4, -4)]
    STRUNG_FROM = -5  # balloons this low or lower show their strings
    STRING = (190, 190, 190)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.kevin_w = len(self.KEVIN_ART[0])
        self.dug_w, self.dug_h = len(self.DUG_ART[0]), len(self.DUG_ART)
        self.ground = height - self.dug_h
        # Until Dug, last, is off the right edge.
        self.frames = (width + self.kevin_w + self.DUG_BEHIND) // self.STEP + 1
        self.duration = self.frames / FPS

    def kevin(self, f):
        """(x, pose) of Kevin at frame f: pose is her step (drawing.WALK_CYCLE)."""
        return -self.kevin_w + f * self.STEP, f // self.POSE_F

    def kevin_art(self, pumped):
        """Her rows for the board: the neck cut down on 64x32, the head pumped forward."""
        rows = list(self.KEVIN_ART)
        first, end = self.NECK
        if self.height < 64:
            rows = rows[:first] + [rows[first], rows[end - 1]] + rows[end:]
        if pumped:
            rows = ["." + row[:-1] for row in rows[:self.HEAD_ROWS]] + rows[self.HEAD_ROWS:]
        return rows

    def dug(self, f):
        """(x, y) of Dug's top-left at frame f: chasing Kevin, lifted higher the further he gets,
        from the ground as he comes on to his head at the top row as he goes off the right."""
        x = self.kevin(f)[0] - self.DUG_BEHIND
        across = min(1.0, max(0.0, (x + self.dug_w) / (self.width + self.dug_w)))
        lifted = round(self.ground * across ** self.LIFT_EASE)
        trot = (f // self.TROT_F) % 2 if lifted == 0 else 0
        return x, self.ground - lifted - trot

    def sway(self, t):
        return round(self.SWAY * math.sin(2 * math.pi * t / self.SWAY_S))

    def balloon_pixels(self, x0, y0, sway):
        """{(x, y): rgb} of the strings and balloons tied to Dug's head at (x0, y0)."""
        out = {}
        head = (x0 + self.dug_w // 2, y0)
        knot = (head[0] + sway, y0 - self.KNOT_ABOVE)
        strings = [(knot[0] + dx + 1, knot[1] + dy + 2) for dx, dy in self.BUNCH if dy >= self.STRUNG_FROM]
        for end in [head] + strings:
            for x, y in _line(knot, end):
                out[(x, y)] = self.STRING
        for i, (dx, dy) in enumerate(self.BUNCH):
            rgb = self.BALLOON_RGB[i % len(self.BALLOON_RGB)]
            shine = tuple(min(255, c + 90) for c in rgb)
            for bx in range(3):
                for by in range(3):
                    if by == 2 and bx != 1:
                        continue
                    out[(knot[0] + dx + bx, knot[1] + dy + by)] = shine if (bx, by) == (0, 0) else rgb
        return out

    def pixels(self, t):
        """{(x, y): rgb} of the whole scene at t."""
        f = int(t * FPS)
        out = {}
        dx, dy = self.dug(f)
        out.update(self.balloon_pixels(dx, dy, self.sway(t)))
        out.update(dict(art_pixels(self.DUG_ART, dx, dy, self.colors)))
        kx, pose = self.kevin(f)
        rows = self.kevin_art(pose % 2 == 1)
        feet = (len(rows) - self.FEET_ROWS, self.BEHIND, self.AHEAD)
        out.update(dict(walking_pixels(rows, kx, self.height - len(rows), self.colors, feet, pose)))
        return out

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        paint(canvas, self.pixels(t), self.width, self.height)
        return True


def _line(a, b):
    """The pixels from a to b, ends included."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]
