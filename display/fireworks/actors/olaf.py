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
    leaning right, and he mouths his line to the score's track (MOUTHS: closed, half, open as drawn),
    grinning wide (open, as drawn) before his first word and after his last. He melts as he says his
    line ("some people are worth melting for"): from his first word his body squashes down into a pale
    blue puddle spreading at his feet, his head riding down on top of it as drawn so he can finish
    talking; from his last word his head melts too. By PUDDLE_S before his scene ends only the puddle
    is left, his carrot and coal buttons lying in it, and it fades out by his scene's end. Without a
    track he melts over his scene's last MELT_S + PUDDLE_S.
    """
    NAME = "Olaf"
    ENTER_S = 0.8
    WAVE_S = 1.0  # one full swing of his arm, up and back
    POSES = 12  # wave poses drawn up front
    SPOT = 0.27  # his middle across the board
    MELT_S = 2.0  # from standing to a puddle, without a track
    PUDDLE_S = 0.6  # the puddle fades out over his scene's last this long
    WATER = (140, 180, 235)
    WATER_EDGE = (95, 130, 190)
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
        feet = [x for x, y in self.poses[2][0] if y == show.height - 1]
        self.cx = (min(feet) + max(feet)) / 2  # his middle, over the puddle
        self.feet_half = (max(feet) - min(feet) + 1) / 2
        self.puddle_rows = 3 if self.big else 2
        rows = len(olaf.head_art)
        self.neck = int(round(olaf.head[2] - rows / 2)) + rows - 1  # his head's bottom row, standing

    def words(self):
        """(first word's start, last word's end) in seconds into his scene, from his mouth track's moves
        within the scene, or None without a track or a word."""
        lips = self.show.lips.get("olaf")
        cue = self.show.cue
        if lips is None or cue is None or self.since is None:
            return None
        spoken = [lips.start + i / lips.fps for i, k in enumerate(lips.track) if k != "0"]
        spoken = [t for t in spoken if self.since <= t < cue.end]
        if not spoken:
            return None
        return spoken[0] - self.since, spoken[-1] + 1 / lips.fps - self.since

    def scene_s(self):
        cue = self.show.cue
        return cue.end - self.since if cue is not None and self.since is not None else 0.0

    def melt_s(self):
        """(body, head, gone): seconds into his scene that his body starts to melt, his head starts to
        melt, and he's only a puddle."""
        gone = self.scene_s() - self.PUDDLE_S
        words = self.words()
        if words is None:
            return gone - self.MELT_S, gone - self.MELT_S, gone
        first, last = words
        return min(first, gone), min(last, gone), gone

    @staticmethod
    def _eased(e, start, end):
        """0..1 from start to end, slow to begin (as the snow gives)."""
        p = 1.0 if end <= start else min(1.0, max(0.0, (e - start) / (end - start)))
        return p * p

    def melted(self, e):
        """(body, head): 0..1, how far each has melted e seconds in."""
        body, head, gone = self.melt_s()
        return self._eased(e, body, gone), self._eased(e, head, gone)

    def puddle_glow(self, e):
        """0..1: the puddle's brightness once he's melted, fading out over his scene's last PUDDLE_S."""
        return min(1.0, max(0.0, 1 - (e - self.melt_s()[2]) / self.PUDDLE_S))

    def shape(self, e):
        """His mouth shape e seconds in on 64x64: the track's while he talks, his open grin either side."""
        words = self.words()
        if words is None or not words[0] <= e < words[1]:
            return 2
        shape = self.mouth("olaf")
        return 2 if shape is None else shape

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
        w = self.show.width
        shape = self.shape(e) if self.big else 2
        p, q = self.melted(e)
        if p >= 1 and q >= 1:
            self.draw_puddle(out, 1.0, self.puddle_glow(e))
            return
        # Melting: his body's rows squash toward the bottom row and his head rides down on top of
        # them as drawn, until it melts the same way after his last word.
        b = h - 1
        ride = (b - (b - (self.neck + 1)) * (1 - p)) - (self.neck + 1)
        for (x, y), rgb in sorted(self.poses[shape][self.pose(e)].items(), key=lambda c: -c[0][1]):
            y += dy
            if y <= self.neck + dy:
                y = b - (b - (y + ride)) * (1 - q)
            else:
                y = b - (b - y) * (1 - p)
            y = int(math.floor(y + 0.5))
            if 0 <= y < h and 0 <= x < w:
                out[(x, y)] = rgb
        if p > 0:
            self.draw_puddle(out, p, 1.0)

    def draw_puddle(self, out, p, glow):
        """The puddle he leaves: wider and deeper as he melts (p), with his carrot and buttons in it
        once he's gone, all at glow brightness."""
        if glow <= 0.05:  # too dim for the LEDs
            return
        h, w = self.show.height, self.show.width
        dim = lambda rgb: tuple(int(c * glow) for c in rgb)
        half = self.feet_half * (0.8 + 1.2 * p)
        rows = max(1, round(self.puddle_rows * p))
        for k in range(rows):
            span = half * (1 - (k / rows) ** 2) ** 0.5
            for x in range(math.floor(self.cx - span + 0.5), math.floor(self.cx + span + 0.5) + 1):
                if 0 <= x < w:
                    edge = k == rows - 1 or abs(x - self.cx) > span - 1
                    out[(x, h - 1 - k)] = dim(self.WATER_EDGE if edge else self.WATER)
        if p >= 1:
            y = h - 1 - (rows // 2)
            cx = round(self.cx)
            for x in range(cx - 4, cx - 1):  # his carrot, lying on its side
                if 0 <= x < w:
                    out[(x, y)] = dim(OlafReveal.CARROT)
            for x in (cx + 1, cx + 3, cx + 5):  # his coal buttons
                if 0 <= x < w:
                    out[(x, y)] = dim(OlafReveal.COAL)
