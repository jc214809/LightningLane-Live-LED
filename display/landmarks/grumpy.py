"""
The runDisney Wine & Dine Two Course Challenge (the 10K and the half marathon; its medal is Grumpy):
Grumpy on the medal's royal blue under "Wine & Dine" and his own race in gold, "Challenge 19.3" (miles),
arms folded, scowling and tapping a foot, until he gives one grudging hop. It plays on the half marathon's day, picked at random
against the penguin waiters each showing (utils/special_events.py DATED_LANDMARKS).
"""

import math

from display.pixels import art_pixels

from display.landmarks.scene import Landmark
from display.landmarks.penguin_waiters import title_pixels
from display.landmarks.three_caballeros import SKY_BOTTOM, SKY_TOP, SMALL_FONT, TINY_FONT, WHITE
from display.landmarks.wine_and_dine import GOLD


# Traced from the Disney wiki's outlined render (docs/references/Grumpy arms folded render.png), keeping
# its line art (a cell 18%+ line stays black: its outlines are thin), then his brows and eyes redrawn.
COLORS = {
    "K": (0, 0, 0),
    "C": (220, 25, 45),  # tunic
    "T": (215, 165, 100),  # shoes
    "N": (150, 90, 35),  # hat and trousers
    "S": (255, 190, 150),  # skin
    "W": (255, 255, 255),  # beard and eyes
    "P": (255, 120, 110),  # nose
}

GRUMPY_64 = [
    ".....KKKKKK............",
    "...KKNNNNNKKK..........",
    "...NNNNNKNNNNK.........",
    "..KNNNNNNKKSKKK........",
    "..KNNNNKKSSSSSSKK......",
    "..KNNNKSSSSSSSSSK......",
    "..KNNKKKKSSSKKKKK......",
    ".KKNNKSSKKSKKSSSK......",
    ".KWKNKSWWKSWKKSK.......",
    ".WKSKSSWKKSWKSSK.......",
    "KWKSSSKKKKPPPKKK.......",
    "KWKSSSSKPPPPPPKWK......",
    ".KWKSSSKPPPPPPKWK......",
    ".KWWKKSKPPPPPPKWK......",
    ".NKWWWKKKKPPPKWWK......",
    "KNNKKKKKKKKKWWKCKKK....",
    "KNNNNCCKSKKKKCCCCKKK...",
    "KNNNKCCCKSKSKCCCCCKCK..",
    ".KKK.KCCKKKKKCCCCCKCC..",
    ".....KCCCCCCCCCCCKCCC..",
    "......KCCCCCCCCCKCCCK..",
    "......KKCCCCCCCKKCKK...",
    ".....KCCKTTTCCKKWKC....",
    "....KCCCCKKKKKWWWKC....",
    ".....KCKCCCCKWWWKCK....",
    "....KCCCKCCCCKWWKCK....",
    "....KCCCKKKCCKWKCK.....",
    "...KCCCCCKKKCKKCK......",
    "...CCCCCCCKKKKKKC......",
    "...KCCCCCCCCKKKKCK.....",
    "....CCCCCCCCKNNCCK.....",
    "....KKCCCCCCKNNKC......",
    ".....NNKNKKCKNNK.......",
    ".....KNNNNKKKNKK.......",
    ".....NNNNKKKKKKKKKKKK..",
    "....KNNNNKTTTTTTTTTTTK.",
    "...KKNNKKTTTTTTTTTTTTTK",
    "...KTTTTTTKTTTTTTTTTTTK",
    "...KTTTTTKKKKKKKKKKKKK.",
    "...KTTTTTTTTK..........",
    "....KTTTTTTTTK.........",
    ".....KTTTTTTTTK........",
    "......KTTTTTTTK........",
    ".......KKKKKKKK........",
]

GRUMPY_32 = [
    "...KNNN........",
    "..NNNNKKK......",
    ".NNNNNKSKK.....",
    ".NNNKKKSKK.....",
    ".KKKSSKSKK.....",
    ".WSSSKKKS......",
    ".WSSSPKPSK.....",
    ".WSSKPPPPKW....",
    ".WWKKPPPPWW....",
    "NNKWWKKPWWK....",
    "KNNKKSSKKCCKK..",
    "KNKKCKKKCCCCCC.",
    "....CCCCCCCKCC.",
    "....KCCCCCKCC..",
    "...CCKTKKKWK...",
    "...KCCCCWWWC...",
    "...CCKKCKWKC...",
    "..CCCCKKKKK....",
    "..CCCCCKKKC....",
    "..KCCCCCKNC....",
    "...KNCCCNKK....",
    "...NNNKNKKKKKK.",
    "...NNKKKTTTTTTK",
    "..KTNTTKTTTTTTK",
    "..KTTTKKKKKKKK.",
    "..KTTTTTK......",
    "...KTTTTTK.....",
    "....KKKKKK.....",
]

# The front shoe's toe with its outline, (first row, last row, first column, last column): it lifts a
# row on each tap while the heel stays down.
TOE_64 = (34, 38, 15, 22)
TOE_32 = (21, 24, 11, 14)

# His race, not the half: three lines over him on 64x64 (ending the row above his hat; mid-hop it draws
# over the hat's top, as the 10K's title does); down the left beside him on 64x32, with no room over him.
TITLE_64 = [(TINY_FONT, "WINE & DINE", 32, 0, WHITE), (SMALL_FONT, "CHALLENGE", 32, 5, GOLD),
            (SMALL_FONT, "19.3", 32, 12, GOLD)]
SIDE_TITLE_32 = [(TINY_FONT, "WINE&", 20, 0, WHITE), (TINY_FONT, "DINE", 19, 6, WHITE),
                 (TINY_FONT, "CHALLENGE", 20, 14, GOLD), (SMALL_FONT, "19.3", 20, 21, GOLD)]

TAP_FROM, TAP_TO = 0.4, 2.8  # scene seconds he taps his foot
TAP_BEAT = 0.2  # toe up for one beat, down for the next
HOP_AT = 3.4  # then his one grudging hop
HOP_S = 0.35


def _lifted(art, toe):
    """The art with the toe (its outline too) moved up a row; what was above its top row shows where
    the toe is empty there, and its bottom row is left empty."""
    top, bottom, left, right = toe
    rows = [list(row) for row in art]
    for c in range(left, right + 1):
        rows[top - 1][c] = art[top][c] if art[top][c] != "." else art[top - 1][c]
        for r in range(top + 1, bottom + 1):
            rows[r - 1][c] = art[r][c]
        rows[bottom][c] = "."
    return ["".join(row) for row in rows]


class GrumpyTwoCourseLandmark(Landmark):
    """Wine & Dine Two Course Challenge: Grumpy, arms folded, taps a foot under his race's name, then hops once."""

    SCREEN_S = 6.0

    def build(self):
        w, h = self.width, self.height
        big = h >= 64
        self.art = GRUMPY_64 if big else GRUMPY_32
        self.tapping_art = _lifted(self.art, TOE_64 if big else TOE_32)
        aw, ah = len(self.art[0]), len(self.art)
        if big:  # centre stage under the title
            self.home = (w // 2 - aw // 2, h - ah)
            self.title_spec = TITLE_64
        else:  # the title down the left, Grumpy at full height on the right
            self.home = (w - aw - 4, h - ah)
            self.title_spec = SIDE_TITLE_32
        self.hop_px = 3 if big else 2
        self.text = title_pixels(self.title_spec, w, h)
        self.sky = {}
        for y in range(h):
            f = y / (h - 1)
            rgb = tuple(round(a + (b - a) * f) for a, b in zip(SKY_TOP, SKY_BOTTOM))
            for x in range(w):
                self.sky[(x, y)] = rgb

    def hop(self, t):
        """Pixels up off the ground at scene time t."""
        if 0 <= t - HOP_AT < HOP_S:
            return round(self.hop_px * math.sin(math.pi * (t - HOP_AT) / HOP_S))
        return 0

    def tapping(self, t):
        """Whether his toe is up at scene time t."""
        return TAP_FROM <= t < TAP_TO and int((t - TAP_FROM) / TAP_BEAT) % 2 == 0

    def position(self, t):
        x, y = self.home
        return x, y - self.hop(t)

    def frame(self, t):
        out = dict(self.sky)
        x, y = self.position(t)
        art = self.tapping_art if self.tapping(t) else self.art
        for (px, py), rgb in art_pixels(art, x, y, COLORS):
            if 0 <= px < self.width and 0 <= py < self.height:
                out[(px, py)] = rgb
        out.update(self.text)
        return out
