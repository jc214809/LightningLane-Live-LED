"""Carl's house from Up for the synced show (see show_actors.py)."""
import math
import random

from display.fireworks.actors.base import Actor
from display.motion import smooth


class UpHouseFloats(Actor):
    """
    Touch the Sky / Up: Carl's house (ART, 1x on 64x32 and doubled on 64x64) rises from behind the
    castle's right side, lifted by a dense bunch of balloons (1-px dots in the Balloons effect's
    colours) tied by a few strings to its chimney. Anything below the castle's roofline is hidden,
    so the balloons come up over the castle first and the house follows. It hangs there with a gentle
    sway and a slight lift, then drifts up and off the right edge, gone by DRIFT_END_S (the scene is
    22 s).
    """
    NAME = "The Up house"
    RISE_S = 6.0  # from hidden behind the castle up to where it hangs
    DRIFT_FROM_S = 15.0  # then up and off to the right...
    DRIFT_END_S = 21.5  # ...gone by here
    SWAY_S = 3.2  # one sway
    SCALE = 1  # the house on 64x32 (the editor's preview)
    BIG_SCALE = 2  # on 64x64
    # The balloons' colours: V1's Balloons effect (show_effects.py), so the bunch matches them.
    BALLOON_COLOURS = ((240, 50, 50), (250, 200, 40), (60, 120, 255), (60, 200, 80), (240, 110, 200),
                       (255, 140, 40))
    STRING_RGB = (190, 190, 190)

    # Carl's house: a brick chimney through a steep dark-red roof, pale teal clapboard walls framed
    # in white trim, a yellow-lit window, a brown door, and the porch deck along the bottom.
    # '.' empty, C chimney, R roof, T white trim, B wall, Y lit window, D door, P porch.
    ART = [
        "........C..",
        "....RRR.C..",
        "..RRRRRRR..",
        "RRRRRRRRRRR",
        ".TTTTTTTTT.",
        ".TBYYBBBDT.",
        ".TBYYBBBDT.",
        ".TBBBBBBDT.",
        "PPPPPPPPPPP",
    ]
    COLORS = {
        "C": (170, 70, 50),
        "R": (140, 30, 40),
        "T": (235, 235, 235),
        "B": (110, 195, 205),
        "Y": (255, 215, 80),
        "D": (110, 60, 30),
        "P": (150, 95, 50),
    }
    CHIMNEY_COL = 8

    def __init__(self, show):
        super().__init__(show)
        s = self.scale = self.BIG_SCALE if self.big else self.SCALE
        self.w, self.h = len(self.ART[0]) * s, len(self.ART) * s
        # The bunch: an ellipse of dots over the house, strings from its underside to the chimney.
        rx, ry = 6.5 * s, 3.0 * s
        gap = 2 * s  # rows of string between the bunch and the chimney's top
        self.above = gap + int(2 * ry)  # rows of balloons and string over the house's top
        cx, cy = self.w / 2 - 0.5, -gap - ry - 0.5
        art_rng = random.Random(5)  # the same bunch every show
        cells = {}
        for dy in range(-self.above, -gap):
            for dx in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((dx - cx) / rx) ** 2 + ((dy - cy) / ry) ** 2 <= 1 and art_rng.random() < 0.9:
                    cells[(dx, dy)] = art_rng.choice(self.BALLOON_COLOURS)
        chim_x = self.CHIMNEY_COL * s + (s - 1) / 2
        for k in (-3, 0, 3):
            ex, ey = cx + k * s, -gap - 0.5  # where the string leaves the bunch
            n = 2 * int(max(abs(chim_x - ex), gap)) + 1
            for i in range(n + 1):
                f = i / n
                x, y = round(ex + (chim_x - ex) * f), round(ey + f * gap)
                if y < 0:
                    cells.setdefault((x, y), self.STRING_RGB)
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind != ".":
                    for oy in range(s):
                        for ox in range(s):
                            cells[(col * s + ox, row * s + oy)] = self.COLORS[kind]
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
        self.sway = 1 if not self.big else 2
        self.base_x = show.castle_x + show.castle_w - self.w + 2 + s
        cols = range(max(0, self.base_x), min(show.width, self.base_x + self.w + self.sway))
        clear = min(self.clip[x] for x in cols)
        self.hover = max(self.above, clear - self.h - 1)  # its top where it hangs, house clear of the roof
        self.lift = max(0, min(2 * s, self.hover - self.above))  # how much higher it floats while hanging
        lowest = max(self.clip[x] for x in range(int(cx - rx) - 1 + self.base_x,
                                                  int(cx + rx) + 2 + self.base_x + self.sway)
                     if 0 <= x < show.width)
        self.start = lowest + self.above  # its top when everything is still hidden

    def top_left(self, e):
        """The house's top-left e seconds into the scene."""
        rise = smooth(e / self.RISE_S)
        top = self.start + (self.hover - self.start) * rise
        top -= self.lift * smooth((e - self.RISE_S) / (self.DRIFT_FROM_S - self.RISE_S))
        left = self.base_x + self.sway * (0.5 - 0.5 * math.cos(2 * math.pi * e / self.SWAY_S))
        k = max(0.0, min(1.0, (e - self.DRIFT_FROM_S) / (self.DRIFT_END_S - self.DRIFT_FROM_S)))
        left += (self.show.width - self.min_dx + 1 - self.base_x) * k * k
        top -= self.show.height * 0.3 * k
        return left, top

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
