"""
Time for the transitions: the frame rate and standard lengths (easing is display.motion's).
"""

import math

from display.motion import ease_out, progress  # noqa: F401  (re-exported: animation.ease_out, .progress)

FPS = 30
COVER_S = 0.55
WIPE_S = 0.65
FLYBY_S = 1.2


def _hops(t, t0, t1, x0, x1, count, height):
    """(x, lift, hops done) for something hopping from x0 to x1 in `count` equal hops over t0..t1."""
    p = progress(t, t0, t1)
    phase = p * count
    return x0 + (x1 - x0) * p, math.sin((phase % 1.0) * math.pi) * height if p < 1 else 0.0, int(phase)
