"""
The runDisney Wine & Dine Half Marathon: the Mary Poppins penguin waiters on the medal's royal blue
under "Wine & Dine" and a gold "Half Marathon". Each flaps a flipper and hops in turn, then all three together.
It replaces Spaceship Earth on race day, picked at random against Grumpy's Two Course Challenge screen
(display/landmarks/grumpy.py) each showing (utils/special_events.py DATED_LANDMARKS).
"""

import math

from display.pixels import art_pixels

from display.landmarks.scene import Landmark
from display.landmarks.three_caballeros import SKY_BOTTOM, SKY_TOP, SMALL_FONT, TINY_FONT, WHITE
from display.landmarks.wine_and_dine import GOLD, _text_pixels


# Hand-drawn in the half marathon poster's pose (docs/references/Wine and Dine 2026 posters.png): no
# render of them traces cleanly.
COLORS = {
    "K": (0, 0, 0),
    "W": (255, 255, 255),
    "w": (150, 175, 210),  # the penguins' belly shading
    "O": (255, 150, 0),  # beaks and feet
    "o": (200, 80, 0),
    "R": (230, 20, 40),  # bow ties (the poster's are red; the film's black ones would vanish)
}

PENGUIN_64 = [
    "......KKKK.....",
    "....KKKKKKKK...",
    "...KKKKKKKKKK..",
    "...KKKKKKKKKK..",
    "..KKKWWWWKKKK..",
    "..KKWWKKWWKKK..",
    "..KKWWKKWWKKK..",
    "OOOOOOWWWWKKK..",
    ".ooOOOOOWWKKK..",
    "...oooWWWWKKK..",
    "....KWWWWKKKK..",
    "....KWWWWWKKK..",
    "...KWRRWRRWKK..",
    "...KWWRRRWWKK..",
    "...KWRRWRRWKKK.",
    "...KWWWWWWWKKK.",
    "..KWWWWWWWWKKK.",
    "..KWWWWWWWWKKK.",
    "..KWWWWWWWWWKKK",
    "..KWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    ".KWWWWWWWWWWKKK",
    "..KWWWWWWWWWKKK",
    "..KWWWWWWWWWKKK",
    "..KwWWWWWWWwKKK",
    "..KwWWWWWWWwKKK",
    "...KwwWWWwwKKKK",
    "...KKwwwwwKKKKK",
    "....KKKKKKK.KKK",
    "...OOOO.OOOO..K",
    "..OOOOO.OOOOO.K",
]

PENGUIN_32 = [
    "....KKK...",
    "...KKKKKK.",
    "..KKKKKKK.",
    "..KKWWKKK.",
    "..KWKWWKK.",
    "OOOOWWWKK.",
    ".ooWWWKKK.",
    "..KWWWWKK.",
    "..KRRWRRK.",
    "..KWRRRWKK",
    ".KWWWWWWKK",
    ".KWWWWWWKK",
    ".KWWWWWWWK",
    ".KWWWWWWWK",
    ".KWWWWWWWK",
    ".KWWWWWWWK",
    "..KwWWWwKK",
    "..KwwwwwKK",
    "...KKKKK.K",
    "..OOO.OOO.",
]

# The far flipper raised in a wave: black cells over and past the penguin's right edge, (col, row).
WAVE_64 = [(13, 17), (14, 16), (15, 16), (15, 15), (16, 15), (16, 14), (17, 14), (17, 13), (18, 13), (18, 12)]
WAVE_32 = [(10, 10), (10, 9), (11, 9), (11, 8), (12, 8), (12, 7)]

# "Wine & Dine" over a gold "Half Marathon" (Grumpy's screen shares it): one line each on 64x64, where
# 5x8 "HALF MARATHON" is the board's full width; in the top corners on 64x32, above the penguins.
TITLES = {
    True: [(SMALL_FONT, "WINE & DINE", 32, 0, WHITE), (SMALL_FONT, "HALF MARATHON", 32, 9, GOLD)],
    False: [(TINY_FONT, "WINE&", 10, 0, WHITE), (TINY_FONT, "DINE", 9, 6, WHITE),
            (TINY_FONT, "HALF", 47, 0, GOLD), (TINY_FONT, "MARATHON", 47, 6, GOLD)],
}


def title_pixels(spec, w, h):
    """{(x, y): rgb} for a title spec, kept on the board (a full-width line's shadow falls off its edge)."""
    out = {}
    for font, text, center_x, top, rgb in spec:
        out.update(_text_pixels(font, text, center_x, top, rgb))
    return {(x, y): rgb for (x, y), rgb in out.items() if 0 <= x < w and 0 <= y < h}


ORDER = ("left", "middle", "right")
TURN_AT = {"left": 0.6, "middle": 1.2, "right": 1.8}  # each penguin's flap and hop, left to right
ALL_AT = 2.6  # then all three together
HOP_S = 0.35
FLAP_S = 0.6  # the flipper goes up and down over this long from a penguin's turn
FLAP_BEAT = 0.15  # up for one beat, down for the next


class PenguinWaitersHalfLandmark(Landmark):
    """Wine & Dine Half Marathon: three penguin waiters flap and hop in turn under a gold "Half Marathon"."""

    SCREEN_S = 6.0

    def build(self):
        w, h = self.width, self.height
        big = h >= 64
        self.cast = ORDER
        penguin = PENGUIN_64 if big else PENGUIN_32
        self.art = {name: penguin for name in ORDER}
        self.size = {k: (len(a[0]), len(a)) for k, a in self.art.items()}
        self.wave = WAVE_64 if big else WAVE_32
        xs = {"left": 3, "middle": 24, "right": 45} if big else {"left": 3, "middle": 22, "right": 41}
        self.home = {k: (xs[k], h - self.size[k][1]) for k in ORDER}  # standing on the bottom edge
        self.hop_px = 3 if big else 2
        self.title_spec = TITLES[h >= 64]
        self.text = title_pixels(self.title_spec, w, h)
        self.sky = {}
        for y in range(h):
            f = y / (h - 1)
            rgb = tuple(round(a + (b - a) * f) for a, b in zip(SKY_TOP, SKY_BOTTOM))
            for x in range(w):
                self.sky[(x, y)] = rgb

    def hop(self, name, t):
        """Pixels up off the ground at scene time t: a penguin's own hop, then the one they all do."""
        for start in (TURN_AT[name], ALL_AT):
            if 0 <= t - start < HOP_S:
                return round(self.hop_px * math.sin(math.pi * (t - start) / HOP_S))
        return 0

    def waving(self, name, t):
        """Whether a penguin's flipper is up at scene time t: it flaps through its turn and the all-hop."""
        return any(0 <= t - start < FLAP_S and int((t - start) / FLAP_BEAT) % 2 == 0
                   for start in (TURN_AT[name], ALL_AT))

    def positions(self, t):
        """{name: (x, y)} of each character's top-left at scene time t."""
        return {k: (x, y - self.hop(k, t)) for k, (x, y) in self.home.items()}

    def frame(self, t):
        out = dict(self.sky)
        for name, (x, y) in self.positions(t).items():
            for (px, py), rgb in art_pixels(self.art[name], x, y, COLORS):
                if 0 <= px < self.width and 0 <= py < self.height:
                    out[(px, py)] = rgb
            if self.waving(name, t):
                for c, r in self.wave:
                    if 0 <= x + c < self.width and 0 <= y + r < self.height:
                        out[(x + c, y + r)] = COLORS["K"]
        out.update(self.text)
        return out
