"""
The base every landmark builds on: a static scene precomputed once, with frame(t)
returning its pixels at time t; plus the shared sky colours and texture noise.
"""

import math
import random


LANDMARK_S = 3.0


SKY_RGB = (4, 6, 22)


TITLE_SHADOW_RGB = (10, 2, 18)


class Landmark:
    """Precomputes a static scene once; frame(t) returns {(x, y): rgb} for time t."""

    SCREEN_S = LANDMARK_S  # how long the landmark's screen is held, sweep and wipe included
    STAR_SPACING = 4  # one twinkling star per this many columns
    # False: the scene waits at its first frame until the wipe has uncovered it, then starts.
    # True: it's already playing as the wipe uncovers it, so its clock starts with the wipe.
    PLAYS_UNDER_WIPE = False

    def __init__(self, width, height, rng=None, park=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.park = park or {}  # the park it's shown for, for scenes that use its data
        self.scale = 2 if height >= 64 else 1
        self.base = {}
        self.stars = [(self.rng.randrange(width), self.rng.randrange(height), self.rng.uniform(0, 2 * math.pi))
                      for _ in range(width // self.STAR_SPACING)]
        self.build()

    def build(self):
        raise NotImplementedError

    def put(self, out, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            out[(x, y)] = rgb

    def draw_stars(self, out, t):
        for x, y, phase in self.stars:
            level = 20 + int(25 * (1 + math.sin(t * 3 + phase)))
            out.setdefault((x, y), (level, level, level + 10))

    def frame(self, t):
        out = {}
        self.draw_stars(out, t)
        out.update(self.base)
        self.animate(out, t)
        return out

    def animate(self, out, t):
        pass

    def title(self, t):
        """Text drawn over the scene in the board's title font: [(text, center_x, top_y, rgb)]."""
        return []


def _noise(x, y):
    """Deterministic 0..1 value per cell, for leafy and carved textures."""
    return (((x * 73856093) ^ (y * 19349663)) & 1023) / 1023
