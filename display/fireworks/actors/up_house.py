"""Carl's house from Up for the synced show (see show_actors.py)."""
import math
import random

from display.fireworks.actors.base import Actor
from display.motion import smooth


class UpHouseFloats(Actor):
    """
    Touch the Sky / Up: Carl's house floats in from the board's left edge, lifted by its balloons
    tied by strings to its chimney: on 64x64 the whole chart (BALLOONS_ART over ART, 24x46, 1x), on
    64x32 only the house (24x24, 1x), under a dense bunch of 1-px dots in the Balloons effect's
    colours. It crosses with a gentle bob, climbing faster as it goes, and leaves off the top-right
    corner, gone by CROSS_S (the scene is 22 s). Anything below the castle's roofline is hidden, so it
    passes behind the castle's towers.
    """
    NAME = "The Up house"
    CROSS_S = 21.5  # from off the left edge to off the top-right corner
    BOB_S = 3.2  # one bob
    SCALE = 1  # 1x on both boards: the chart is 46 rows tall
    # The 64x32 bunch's colours: V1's Balloons effect (show_effects.py), so it matches them.
    BALLOON_COLOURS = ((240, 50, 50), (250, 200, 40), (60, 120, 255), (60, 200, 80), (240, 110, 200),
                       (255, 140, 40))
    STRING_RGB = (190, 190, 190)

    # From docs/references/Up house with balloons chart.png, cell for cell (its sky left out).
    # The balloons and their strings (64x64 only), to sit straight on top of ART.
    BALLOONS_ART = [
        ".........iibbyy.........",
        ".......BOORgBGyRR.......",
        "......bbOORgBBibby......",
        "......PPGGByyiibby......",
        ".....iiyGGyyGggBBBP.....",
        ".....iiggbOOGbbBBBP.....",
        ".....POBBbBBRRbbiiG.....",
        ".....yyBByyORRyyiiG.....",
        ".....yyggRROiiyGGOO.....",
        "......RRgRPPiiRRGO......",
        "......RROOPPyyPPRR......",
        ".......ggbbRROOyR.......",
        ".......ggbggROOyy.......",
        "........yyGGPPBB........",
        "........yyGGPPBB........",
        "........s.s..s.s........",
        "........s.s..s.s........",
        "........s..s.ss.........",
        ".........s.ss.s.........",
        "..........s.ss..........",
        "...........ss...........",
        "............s...........",
    ]
    # Carl's house: the chimney, a dark roof with sky-blue gables, the pink half (a lilac window,
    # brown door, pink porch) and the green half (a blue window) under cream trim.
    ART = [
        "...........SSS....B.....",
        "...........RRR....B.....",
        "...........RRR...BBB....",
        ".......B...RRR...BYB....",
        "...SSSBYBSSRRRSSBBYBBSSS",
        "...SSBYYYBSSSSSSBYYYBSSS",
        "..SSBYCCCYBSSSSBBYYYBBSS",
        "..SSSYWWWYSSSSSBYWWWYBSS",
        ".SSSSYCCCYSSSSBBYWWWYBBS",
        ".SSSSYYYYYSSSSBYYWWWYYB.",
        "SSSSSSSSSSSSSBBYYWWWYYBB",
        ".WIIIIIWIIIIIIYYYyyyYYY.",
        ".WIIIIIWIIIIIIYYYYYYYYY.",
        ".WIPPPIWIIIIIIyyyyyyyyy.",
        ".WIWWWIWINNNNIgGGGGGGGg.",
        ".WIPPPIWINNNNIgGGbbbGGg.",
        ".WIPPPIWINNNNIgGGbbbGGg.",
        ".WIIIIIWINNNNIgGGWWWGGg.",
        ".WWWWWWWINNNNIgGGbbbGGg.",
        ".WIWIWIWINNNNIgGGbbbGGg.",
        ".WiWiWiWiiiiiggGGGGGGGg.",
        ".iiiiiiWWWWWWggGGGGGGGg.",
        ".iDDDDiWCCCCCgDGDDDDDGD.",
        ".iiiiiiWWWWWWWgGGGGGGGg.",
    ]
    COLORS = {
        "S": (54, 54, 54),  # roof, chimney cap
        "R": (200, 20, 20),  # chimney bricks, red balloons
        "B": (54, 163, 248),  # gables, blue balloons
        "Y": (252, 237, 143),  # cream trim
        "y": (251, 232, 32),  # yellow
        "C": (185, 185, 184),  # light grey
        "W": (253, 253, 252),  # white
        "I": (249, 187, 216),  # pink wall
        "i": (250, 122, 186),  # deep pink
        "P": (214, 119, 221),  # lilac
        "N": (105, 82, 46),  # the door
        "G": (120, 247, 101),  # green wall
        "g": (11, 113, 21),  # dark green
        "b": (64, 93, 238),  # blue
        "D": (153, 43, 100),  # the planters
        "O": (247, 132, 44),  # orange balloons
        "s": (134, 133, 136),  # strings
    }
    CHIMNEY_COL = 12

    def __init__(self, show):
        super().__init__(show)
        self.w, self.h = len(self.ART[0]), len(self.ART)
        cells = {}
        if self.big:
            self.above = len(self.BALLOONS_ART)  # rows of balloons and string over the house's top
            for row, line in enumerate(self.BALLOONS_ART):
                for col, kind in enumerate(line):
                    if kind != ".":
                        cells[(col, row - self.above)] = self.COLORS[kind]
        else:
            # The bunch: an ellipse of dots over the house, strings from its underside to the chimney.
            rx, ry = 8.0, 3.0
            gap = 2  # rows of string between the bunch and the chimney's top
            self.above = gap + int(2 * ry)
            cx, cy = self.w / 2 - 0.5, -gap - ry - 0.5
            art_rng = random.Random(5)  # the same bunch every show
            for dy in range(-self.above, -gap):
                for dx in range(int(cx - rx) - 1, int(cx + rx) + 2):
                    if ((dx - cx) / rx) ** 2 + ((dy - cy) / ry) ** 2 <= 1 and art_rng.random() < 0.9:
                        cells[(dx, dy)] = art_rng.choice(self.BALLOON_COLOURS)
            for k in (-3, 0, 3):
                ex, ey = cx + k, -gap - 0.5  # where the string leaves the bunch
                n = 2 * int(max(abs(self.CHIMNEY_COL - ex), gap)) + 1
                for i in range(n + 1):
                    f = i / n
                    x, y = round(ex + (self.CHIMNEY_COL - ex) * f), round(ey + f * gap)
                    if y < 0:
                        cells.setdefault((x, y), self.STRING_RGB)
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind != ".":
                    cells[(col, row)] = self.COLORS[kind]
        self.cells = [(dx, dy, rgb) for (dx, dy), rgb in cells.items()]
        self.min_dx = min(dx for dx, _, _ in self.cells)
        # The castle's roofline per column: anything at or below it is behind the castle.
        self.clip = [show.height] * show.width
        for dx, dy, _ in show.castle_pixels:
            x = show.castle_x + dx
            if 0 <= x < show.width:
                self.clip[x] = min(self.clip[x], show.castle_y + dy)
        # Past the castle's sides it hides what its end walls would, so nothing comes up from the
        # board's bottom there.
        left_end, right_end = max(0, show.castle_x), min(show.width, show.castle_x + show.castle_w) - 1
        for x in range(show.width):
            if x < left_end:
                self.clip[x] = self.clip[left_end]
            elif x > right_end:
                self.clip[x] = self.clip[right_end]
        self.hover = self.above  # its top as it comes in: the balloons just under the board's top
        self.max_dx = max(dx for dx, _, _ in self.cells)

    def top_left(self, e):
        """The house's top-left e seconds into the scene."""
        k = smooth(e / self.CROSS_S)
        x0, x1 = -self.max_dx - 1, self.show.width - self.min_dx  # just off the left, just off the right
        y0, y1 = self.hover, -self.h  # its top where it comes in, then its bottom off the top
        bob = math.sin(2 * math.pi * e / self.BOB_S)
        return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k * k + bob

    def draw(self, put, out, active):
        if not active:
            return
        show = self.show
        left, top = self.top_left(self.elapsed())
        left, top = math.floor(left + 0.5), math.floor(top + 0.5)
        clip = self.clip
        for dx, dy, rgb in self.cells:
            x, y = left + dx, top + dy
            if 0 <= x < show.width and 0 <= y < clip[x]:
                out[(x, y)] = rgb
