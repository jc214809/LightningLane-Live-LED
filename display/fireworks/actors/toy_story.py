"""You've Got a Friend in Me: Buzz flies over the castle while Woody waves from the ground."""
import math

from display.animation.characters.aliens import AliensToysReveal
from display.animation.characters.buzz import BuzzReveal
from display.fireworks.actors.base import Actor, stamp


def _waving(arm_out):
    """Woody (AliensToysReveal.WOODY_ART) with his right arm raised: the hand at his side (column 12)
    goes up past his shoulder, straight up or tipped out a column, the two halves of a wave."""
    art = [list(row) for row in AliensToysReveal.WOODY_ART]
    art[10][12] = art[11][12] = "."
    for row in (7, 8, 9):
        art[row][12] = "Y"
    if arm_out:
        art[7][12], art[7][13], art[6][13] = ".", "Y", "O"
    else:
        art[6][12] = "O"
    return ["".join(row) for row in art]


class BuzzAndWoody(Actor):
    """
    You've Got a Friend in Me: Buzz (his fly-by art from BuzzReveal, wings out: the big one 1x on 64x32,
    the small one doubled on 64x64, as on his ride screen) flies across the sky from left to right over
    the scene's 6 s, bobbing a little, with a short flickering rocket trail behind him. Woody (his claw
    scene art from AliensToysReveal, 1x on both boards) stands on the ground beside the castle, on its
    left, and waves at him the whole time.
    """
    NAME = "Buzz and Woody"
    CROSS_S = 6.0  # Buzz's flight from off the left edge to off the right
    BOB_S = 1.2  # one bob up and down
    WAVE_S = 0.3  # each half of Woody's wave
    TRAIL = 6  # trail pixels behind Buzz, per board pixel scale

    def __init__(self, show):
        super().__init__(show)
        self.buzz = BuzzReveal.SIZES["small" if self.big else "big"]
        self.buzz_scale = 2 if self.big else 1
        self.buzz_w = len(self.buzz[0]) * self.buzz_scale
        self.buzz_h = len(self.buzz) * self.buzz_scale
        self.buzz_top = 3 if self.big else 1
        self.bob = 2 if self.big else 1
        self.woody = (_waving(False), _waving(True))
        self.woody_w, self.woody_h = len(self.woody[0][0]), len(self.woody[0])
        self.woody_at = (max(0, show.castle_x - self.woody_w), show.height - self.woody_h)

    def buzz_top_left(self, e):
        """Buzz's top-left e seconds into the scene: steadily from wholly off the left edge to wholly off
        the right, bobbing."""
        k = min(1.0, max(0.0, e / self.CROSS_S))
        left = -self.buzz_w + (self.show.width + self.buzz_w) * k
        top = self.buzz_top + self.bob * math.sin(2 * math.pi * e / self.BOB_S)
        return left, top

    def woody_pose(self, e):
        return self.woody[int(e / self.WAVE_S) % 2]

    def draw(self, put, out, active):
        if not active:
            return
        show = self.show
        e = self.elapsed()
        stamp(out, self.woody_pose(e), AliensToysReveal.colors, *self.woody_at, 1, show.width, show.height)
        left, top = self.buzz_top_left(e)
        left, top = int(round(left)), int(round(top))
        # The trail streams from his back (his middle rows), hottest nearest him, flickering by the clock.
        s = self.buzz_scale
        mid = top + self.buzz_h // 2
        flames = BuzzReveal.flame_colors
        flicker = int(e * 20) % 2
        for i in range(self.TRAIL * s):
            x = left - 1 - i
            rgb = flames[min(len(flames) - 1, i * len(flames) // (self.TRAIL * s))]
            for y in range(mid - s, mid + s - (1 if (i + flicker) % 3 == 2 else 0)):
                if 0 <= x < show.width and 0 <= y < show.height:
                    out[(x, y)] = rgb
        stamp(out, self.buzz, BuzzReveal.colors, left, top, s, show.width, show.height)
