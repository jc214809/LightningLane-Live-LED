import math

from display.animation.drawing import _blackout
from display.motion import progress
from display.pixels import art_pixels, paint


class MaterReveal:
    """
    Mater drives across backwards, the way he likes to: facing right with his big grin, he
    rolls in from the right edge tow hook first and out the left, bobbing on his springs. The
    new ride is uncovered behind him, on the side he's already passed.
    """

    duration = 2.4
    BOB_S = 0.18  # one bounce of his suspension

    # From the user's pixel-art Mater: his tow boom and hook, the windshield eyes, the rusty
    # grille and buck teeth, and his teal body. 1x on both boards. '.' empty, O outline,
    # b brown, R rust, r dark rust, W white, C cream, G his green eyes, T teal body, K tyres,
    # k hubs.
    ART = [
        "................bbbbbbbbb.......",
        "..............bbrRRRRRrrrb......",
        "............OOrRRRRRRRRrrrb.....",
        "...........OOrRRRRRCWWWWCrbbbbO.",
        ".O........OTORRCWWWWWWWWWCb.bRO.",
        "bkObb...OOOOOrWWWWWWWWWWWWb.brO.",
        ".bbO.bb.OROTOCWWWWWWWWWWWWb.brO.",
        ".k.bO..bOROTOCWWWWWWWWWWWWCOOrO.",
        ".k..bO..OROTOCWCGGCWCGGCWWCOOOO.",
        "..O..bO.OrOTOCWGKWGWGKWGWW.O....",
        "...O..bOOOOOOCWGKKGWGKKGWW.O....",
        "....O..bOOTTOCWCGGCWCGGCWWCO....",
        ".k..O...OTTbOObr.........CRrbbr.",
        "..kk.OOOTbbbObC.rRrrbbbbbrrrbKKr",
        "....OTOOOOObObCCbOOOOOOOOOOObTKb",
        "..OOOTOTTTOOTObbrrrrrrrrrrrrrbb.",
        ".OTTTTOTTTOTTTbrRRRRRRRRRRRRRRO.",
        "OTTTTTOTGTOTTTbrRrRRRRRRRRRRRrO.",
        "OTTTTTTOTTOTTTbrbRrbbbbbrRRbRrO.",
        "OTOOOTTOGGOOOTbrRbbKWWKCbbbrRrO.",
        "OOKKKOTOTTOKKObrRRbKCWKWCKbRRrO.",
        "OKkTkKOOTTKkTKbrRRrKKKKKKKrRrrO.",
        "KKTkTKKKKKkTkTKOrRRbKKKKKrRRrrO.",
        ".kTkTKkK.kTkkkKrbbRRRRRRRRRrOOOK",
        ".kTkTKkK.kTkKkKKrRbbbbbbbOOOrrKK",
        ".kkTkKkK.kTkkkTKKKrRRRRRrrrrKKkK",
        "..kKKkK..kkTkTkKkKKKKKKKKKKKkkkK",
        "...KKK....kkTkKkK.........KkkkK.",
        "...........KKKKK...........KKK..",
    ]
    colors = {"O": (60, 47, 39), "b": (90, 61, 46), "R": (214, 116, 80), "r": (153, 89, 64),
              "W": (250, 250, 245), "C": (235, 226, 185), "G": (105, 115, 64), "T": (64, 78, 77),
              "K": (28, 28, 32), "k": (60, 60, 66)}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.w, self.h = len(self.ART[0]), len(self.ART)
        self.y0 = height - self.h - 1

    def x_at(self, t):
        """His left edge at t: in from past the right edge, out past the left, steady and backwards."""
        p = progress(t, 0.0, self.duration)
        return self.width + 1 + (-self.w - 1 - (self.width + 1)) * p

    def bob(self, t):
        return -1 if math.sin(t / self.BOB_S * math.pi) > 0.6 else 0

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = int(round(self.x_at(t)))
        _blackout(canvas, 0, min(self.width, max(0, x)), self.height)  # ahead of him (to his left) still dark
        paint(canvas, art_pixels(self.ART, x, self.y0 + self.bob(t), self.colors), self.width, self.height)
        return True
