"""
Time and easing for everything that moves on the board: transitions, landmarks, fireworks and
the countdown share these.
"""


def ease_out(p):
    """Fast start, gentle stop (a cubic), clamped to 0..1."""
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def smooth(p):
    """Gentle start and stop (smoothstep), clamped to 0..1."""
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def progress(t, start, end):
    """How far t is through start..end, 0 before it and 1 after."""
    return max(0.0, min(1.0, (t - start) / (end - start)))


def ramp(t, start, length):
    """How far t is through the `length` seconds from `start`, 0 before and 1 after."""
    return max(0.0, min(1.0, (t - start) / length))
