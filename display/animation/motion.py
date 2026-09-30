"""
Time for the animations: the frame rate, the standard lengths, and easing.
"""

import math


FPS = 30
COVER_S = 0.55
WIPE_S = 0.65
FLYBY_S = 1.2


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def progress(t, start, end):
    """How far t is through start..end, 0 before it and 1 after."""
    return max(0.0, min(1.0, (t - start) / (end - start)))


def _hops(t, t0, t1, x0, x1, count, height):
    """(x, lift, hops done) for something hopping from x0 to x1 in `count` equal hops over t0..t1."""
    p = progress(t, t0, t1)
    phase = p * count
    return x0 + (x1 - x0) * p, math.sin((phase % 1.0) * math.pi) * height if p < 1 else 0.0, int(phase)
