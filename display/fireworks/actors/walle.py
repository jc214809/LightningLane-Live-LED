"""WALL-E's space dance for the synced show (see show_actors.py)."""
import math

from display.animation.characters.walle import WallEReveal
from display.fireworks.actors.base import Actor, stamp


class WallEFloats(Actor):
    """
    Can You Feel the Love Tonight: WALL-E (his ride-reveal art, 1x on both boards) floats across the
    starry sky as in the film's space dance, alone since EVE has no art yet. He drifts in off the left
    edge, rises on a slow arc to the middle of the board and sinks again with a gentle bob, and is off
    the right edge by the scene's end (CROSS_S). Every couple of seconds he gives his fire extinguisher
    a squirt: a short burst of white specks puffs out behind him and fades.
    """
    NAME = "WALL-E"
    CROSS_S = 19.0  # edge to edge; the scene is 20 s
    BOB_S = 2.6  # one bob
    SQUIRT_S = 2.2  # one squirt every this many seconds...
    SQUIRT_ON_S = 0.5  # ...lasting this long
    SPECK_RGB = (235, 240, 255)

    def __init__(self, show):
        super().__init__(show)
        self.art, self.colors, self.scale = WallEReveal.ART, WallEReveal.COLORS, WallEReveal.SCALE
        self.w, self.h = len(self.art[0]) * self.scale, len(self.art) * self.scale
        room = show.height - self.h  # rows his top can use with all of him on the board
        self.mid = room * 0.62  # where his top starts and ends, a little below the middle
        self.arc = room * 0.35  # how far he rises at the middle of the crossing
        self.bob = 1.5 if not self.big else 3.0
        self.specks = []  # [x, y, vx, vy, frames left]

    def top_left(self, e):
        """His top-left e seconds into the scene: off the left edge at 0, off the right by CROSS_S."""
        k = e / self.CROSS_S
        left = -self.w + (self.show.width + self.w) * k
        top = self.mid - self.arc * math.sin(math.pi * min(1.0, max(0.0, k))) \
            + self.bob * math.sin(2 * math.pi * e / self.BOB_S)
        return left, max(0.0, min(top, self.show.height - self.h))

    def squirting(self, e):
        return (e % self.SQUIRT_S) < self.SQUIRT_ON_S

    def step(self, active):
        e = self.elapsed()
        if active and self.squirting(e):
            left, top = self.top_left(e)
            r = self.rng
            # Out of his left side (behind him) at arm height, pushing him on to the right.
            for _ in range(2):
                self.specks.append([left - 1, top + 11 * self.scale + r.uniform(-1, 1),
                                    -r.uniform(0.3, 0.8), r.uniform(-0.15, 0.15), r.randint(10, 20)])
        for s in self.specks:
            s[0] += s[2]
            s[1] += s[3]
            s[4] -= 1
        self.specks = [s for s in self.specks if s[4] > 0]

    def draw(self, put, out, active):
        show = self.show
        for x, y, _, _, life in self.specks:
            px, py = int(round(x)), int(round(y))
            if 0 <= px < show.width and 0 <= py < show.height:
                f = min(1.0, life / 10.0)
                out[(px, py)] = tuple(int(c * f) for c in self.SPECK_RGB)
        if not active:
            return
        left, top = self.top_left(self.elapsed())
        stamp(out, self.art, self.colors, math.floor(left + 0.5), math.floor(top + 0.5), self.scale,
              show.width, show.height)
