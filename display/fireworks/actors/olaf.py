"""Olaf for "Some people are worth melting for" (see show_actors.py)."""
import math
import random

from display.animation.characters.olaf import OlafReveal
from display.fireworks.actors.base import Actor
from display.motion import ease_out


class OlafStands(Actor):
    """
    Some people are worth melting for: Olaf, built as he finishes building himself on his ride screen
    (OlafReveal's own snowballs, head art and twig arms, the same size on each board), pops up from the
    bottom of the board left of the castle's middle in his first ENTER_S, then stands there waving his
    right arm, one swing every WAVE_S, until his scene ends. His poses are drawn once, up front, so a
    frame only copies one. On 64x64 his skull is redrawn to sit over his jaw (BIG_DOME) instead of
    leaning right, and he mouths his line to the score's track (MOUTHS: closed, half, open as drawn).
    """
    NAME = "Olaf"
    ENTER_S = 0.8
    WAVE_S = 1.0  # one full swing of his arm, up and back
    POSES = 12  # wave poses drawn up front
    SPOT = 0.27  # his middle across the board
    # OlafReveal.BIG_HEAD_ART's rows 0-8 (twig hair and dome) redrawn rounder to the left, so his head
    # stands over his jaw; his face below keeps every cell. 64x64 only: on 64x32 his head fills the board.
    BIG_DOME = [
        ".........B...B.......",
        "..........B..B.B.....",
        "..........B.B.BB.....",
        ".......EEEEEEE.......",
        ".....EWWWWWWWWE......",
        "....EWWWWWRRRWWE.....",
        "...EWWWWWRWWWWWWE....",
        "..EWWWWWKKKKWWRRWE...",
        "..EWWWWKWWWWKKKPWE...",
    ]
    # BIG_HEAD_ART's mouth rows (13-23), its tall D under the sloping lip, by shape: 2 open is as
    # drawn; 1 half lifts the D's bottom; 0 closed leaves the lip's line as a grin.
    MOUTH_ROW = 13
    MOUTHS = {
        1: [".EWWMWWWWOOOOOWWWWE..",
            ".EWWMMWWWWOOOWWWWWE..",
            "EWWWMMMWWWWWWWWWWWE..",
            "EWWWMMWMWWWWWWWWWWE..",
            "EWWWMMWWMMWWWWWWWWE..",
            ".EWWMMWWWWMMWWWWWE...",
            ".EWWMMMWWWWWMMWWE....",
            ".EWWWMMMMMMMWWWE.....",
            ".EWWWWWWWWWWWWE......",
            ".EWWWWWWWWWWWE.......",
            "EWWWWWWWWWWWE........"],
        0: [".EWWMWWWWOOOOOWWWWE..",
            ".EWWWMWWWWOOOWWWWWE..",
            "EWWWWWMWWWWWWWWWWWE..",
            "EWWWWWWMWWWWWWWWWWE..",
            "EWWWWWWWMMWWWWWWWWE..",
            ".EWWWWWWWWMMWWWWWE...",
            ".EWWWWWWWWWWMMWWE....",
            ".EWWWWWWWWWWWWWE.....",
            ".EWWWWWWWWWWWWE......",
            ".EWWWWWWWWWWWE.......",
            "EWWWWWWWWWWWE........"],
    }

    def __init__(self, show):
        super().__init__(show)
        olaf = OlafReveal(show.width, show.height, random.Random(0))  # not the show's dice: fixed art
        olaf.cx = round(show.width * self.SPOT)
        olaf.flakes = []  # the show's own snow falls; just him
        a = OlafReveal.WAVE[0]
        period = 0.5  # OlafReveal's wave swings once every half second
        # Poses from his wave, past the point where everything has popped on, for each mouth shape.
        self.poses = {}
        for shape in (0, 1, 2):
            if self.big:
                art = list(OlafReveal.BIG_HEAD_ART)
                art[:len(self.BIG_DOME)] = self.BIG_DOME
                if shape in self.MOUTHS:
                    art[self.MOUTH_ROW:self.MOUTH_ROW + len(self.MOUTHS[shape])] = self.MOUTHS[shape]
                olaf.head_art = art
            self.poses[shape] = [olaf.pixels(a + period * i / self.POSES) for i in range(self.POSES)]
        top = min(y for pose in self.poses[2] for _, y in pose)
        self.rise = show.height - top  # how far below his standing place he starts

    def pose(self, e):
        """Which wave pose he's in e seconds into the scene (still, arms out, while he pops up)."""
        if e < self.ENTER_S:
            return 0
        return int((e - self.ENTER_S) % self.WAVE_S / self.WAVE_S * self.POSES) % self.POSES

    def drop(self, e):
        """Rows below his standing place he is e seconds in: all the way down to 0 as he pops up."""
        return int(math.floor(self.rise * (1 - ease_out(min(1.0, e / self.ENTER_S))) + 0.5))

    def draw(self, put, out, active):
        if not active:
            return
        e = self.elapsed()
        dy = self.drop(e)
        h = self.show.height
        shape = self.mouth("olaf") if self.big else None
        for (x, y), rgb in self.poses[2 if shape is None else shape][self.pose(e)].items():
            if y + dy < h:
                out[(x, y + dy)] = rgb
