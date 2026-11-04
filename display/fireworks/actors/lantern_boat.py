"""Rapunzel and Flynn's rowing boat from Tangled's lantern scene, for the synced show (see show_actors.py)."""
import math

from display.fireworks.actors.base import Actor, stamp

# music_show's LANTERN_RGB, copied: importing music_show here would be a cycle once show_actors registers this.
LANTERN_RGB = (255, 150, 40)


class LanternBoat(Actor):
    """
    I See the Light (and its lanterns scene after it): Rapunzel and Flynn's little rowboat (ART, 1x on
    64x32, 2x on 64x64) drifts in off the left edge along the bottom of the board, easing to rest in
    front of the castle's base by SETTLE_S, mid-song, while V1's lanterns rise all round. It rocks
    gently on a slow swell (by the clock) over a strip of dark ripples with lantern-orange glints. Near
    the end Rapunzel lights a lantern of her own in her hands (HOLD_S) and lets it go (RELEASE_S): it
    rises from the boat and drifts up the sky. The boat stays to the end of both scenes. Everything is
    placed by elapsed(), so nothing is kept between frames.
    """
    NAME = "Rapunzel and Flynn's boat"
    SETTLE_S = 14.0  # drifting in from the left edge to its rest by the castle
    ROCK_S = 3.4  # one rock
    HOLD_S = 40.0  # her lantern lights in her hands...
    RELEASE_S = 44.0  # ...and she lets it go; both scenes run 56 s
    RISE_PX_S = 2.2  # her lantern's climb on 64x32 (doubled on 64x64)
    WATER_RGB = (10, 25, 70)
    RIPPLE_RGB = (30, 60, 130)

    # Rapunzel (left, facing right: golden hair trailing over the stern into the water, lilac dress) and
    # Flynn (right, facing her: brown hair, white shirt, blue-green vest, his oar in the water) in the
    # rowboat. '.' empty, Y her hair, S skin, P her dress, h his hair, W his shirt, V his vest,
    # O oar, B gunwale, D hull, k hull shadow.
    ART = [
        "...YYY....hhh...",
        "...YYS....SSh...",
        "..YYPP....VWV...",
        ".YY.PPP...VWVO..",
        "Y.kBBBBBBBBBBkO.",
        "Y..kDDDDDDDDk..O",
        "YY..kDDDDDDk...O",
        ".YY..kkkkkk.....",
    ]
    COLORS = {
        "Y": (255, 200, 60),
        "S": (240, 175, 135),
        "P": (165, 105, 215),
        "h": (110, 60, 25),
        "W": (230, 230, 225),
        "V": (25, 125, 110),
        "O": (150, 95, 45),
        "B": (175, 110, 50),
        "D": (110, 62, 28),
        "k": (65, 35, 14),
    }
    SCALE = 1  # 2 on a 64-row board
    HANDS = (5, 2)  # her hands, in ART cells: where her lantern starts

    def __init__(self, show):
        super().__init__(show)
        self.scale = 2 if self.big else 1
        self.w, self.h = len(self.ART[0]) * self.scale, len(self.ART) * self.scale
        self.rock = self.scale  # px up and down
        self.water = self.scale  # rows of water along the bottom
        self.rest_left = show.castle_x + (show.castle_w - self.w) / 2
        self.rest_top = show.height - self.h - self.rock  # with the swell it never leaves the board

    def top_left(self, e):
        """The boat's top-left e seconds in: off the left edge at 0, easing to rest by SETTLE_S."""
        k = min(1.0, max(0.0, e / self.SETTLE_S))
        k = 1 - (1 - k) ** 2
        left = -self.w + (self.rest_left + self.w) * k
        top = self.rest_top + self.rock * math.sin(2 * math.pi * e / self.ROCK_S)
        return left, max(0.0, min(top, self.show.height - self.h))

    def lantern_at(self, e):
        """Her lantern's (x, y, glow) e seconds in, or None before she lights it."""
        if e < self.HOLD_S:
            return None
        left, top = self.top_left(e)
        hx, hy = left + self.HANDS[0] * self.scale, top + self.HANDS[1] * self.scale - self.scale
        if e < self.RELEASE_S:
            return hx, hy, min(1.0, 0.3 + (e - self.HOLD_S) / 2.0)
        up = e - self.RELEASE_S
        return hx + 1.5 * self.scale * math.sin(up * 0.9), hy - self.RISE_PX_S * self.scale * up, 1.0

    def _water(self, out, left):
        show, t = self.show, self.show.t
        x0, x1 = max(0, int(left) - 6 * self.scale), min(show.width, int(left) + self.w + 6 * self.scale)
        glints = {int(round(x)) for x, *_ in show.lanterns}
        for y in range(show.height - self.water, show.height):
            for x in range(x0, x1):
                if x in glints and math.sin(t * 3 + x) > 0:
                    out[(x, y)] = tuple(int(c * 0.45) for c in LANTERN_RGB)
                elif math.sin(x * 0.9 - t * 1.7 + y) > 0.35:
                    out[(x, y)] = self.RIPPLE_RGB
                else:
                    out[(x, y)] = self.WATER_RGB

    def _lantern(self, put, out, e):
        lit = self.lantern_at(e)
        if lit is None:
            return
        x, y, glow = lit
        lx, ly, size = int(round(x)), int(round(y)), self.scale
        halo = tuple(int(c * glow * 0.3) for c in LANTERN_RGB)
        for dx in range(-1, size + 1):
            for dy in range(-1, 3):
                put(lx + dx, ly + dy, halo)
        body = tuple(int(c * glow) for c in LANTERN_RGB)
        for dx in range(size):
            for dy in range(2):
                if 0 <= lx + dx < self.show.width and 0 <= ly + dy < self.show.height:
                    out[(lx + dx, ly + dy)] = body

    def draw(self, put, out, active):
        if not active:
            return
        show, e = self.show, self.elapsed()
        left, top = self.top_left(e)
        self._water(out, left)
        stamp(out, self.ART, self.COLORS, math.floor(left + 0.5), math.floor(top + 0.5), self.scale,
              show.width, show.height)
        self._lantern(put, out, e)
