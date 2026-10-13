import math

from display.animation.characters.baymax import BaymaxReveal
from display.fireworks.actors.base import Actor


class _Collect:
    """A canvas stand-in that keeps what BaymaxReveal paints, so he's drawn by his ride reveal's own code."""

    def __init__(self, out):
        self.out = out

    def SetPixel(self, x, y, r, g, b):
        self.out[(x, y)] = (r, g, b)


class _LongerBaymax(BaymaxReveal):
    """His ride reveal held for the show's window, waving on and off the whole time he's up."""
    INFLATE_S, DEFLATE_S = 1.0, 0.7
    HOLD_S = 7.0 - INFLATE_S - DEFLATE_S
    duration = INFLATE_S + HOLD_S + DEFLATE_S
    WAVE_S, WAVE_EVERY_S = 1.6, 2.4

    def wave(self, t):
        since = t - self.INFLATE_S - 0.35
        if since < 0 or t >= self.INFLATE_S + self.HOLD_S:
            return 0.0
        since %= self.WAVE_EVERY_S
        return math.sin(since * 7.0) if since <= self.WAVE_S else 0.0


class BaymaxInflates(Actor):
    """
    Friendship mash-up, elapsed 15-22 s: Baymax, drawn by his ride reveal's code at its size on each
    board, inflates up from the bottom edge (~1 s), settles with a wobble, blinks and waves (a wave every
    couple of seconds), then deflates away in the last 0.7 s. Placed by the clock: his pose is his
    reveal's at (elapsed - 15) s.
    """
    NAME = "Baymax"
    START_S, END_S = 15.0, 22.0
    ENTERS_S = START_S

    def __init__(self, show):
        super().__init__(show)
        self.baymax = _LongerBaymax(show.width, show.height, self.rng)

    def local(self, e):
        """Seconds into his reveal, or None outside his window."""
        return e - self.START_S if self.START_S <= e < self.END_S else None

    def draw(self, put, out, active):
        if not active:
            return
        t = self.local(self.elapsed())
        if t is not None:
            self.baymax.overlay(_Collect(out), t)
