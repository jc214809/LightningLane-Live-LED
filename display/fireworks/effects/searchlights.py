"""Searchlight beams sweeping the sky from either side of the castle, in each show's colours."""

import colorsys
import math

from display.fireworks.effects.base import Effect
from display.motion import smooth


class Searchlights(Effect):
    """Two beams sweeping the sky from either side of the castle, crossing behind it: white and ice
    blue, like the show's opening and closing. The variants below change only the colours."""

    COLOURS = ((235, 240, 255), (130, 170, 255))

    def colours(self):
        return self.COLOURS

    def draw_behind(self, put, out, active):
        if not active:
            return
        show = self.show
        origins = ((show.castle_x - 2, show.height - 1), (show.castle_x + show.castle_w + 1, show.height - 1))
        length = show.height * 1.2
        for i, ((ox, oy), rgb) in enumerate(zip(origins, self.colours())):
            a = -math.pi / 2 + 0.55 * math.sin(show.t * 0.8 + i * math.pi)
            for k in range(int(length)):
                level = 0.85 * (1 - k / length)
                beam = tuple(int(c * level) for c in rgb)
                for w in range(self.s):  # 2 LEDs wide on a 64-row board
                    put(ox + math.cos(a) * k + w, oy + math.sin(a) * k, beam)


class FanfareSearchlights(Searchlights):
    """The theme fanfare's banks of beams: two from each side of the castle, white and ice blue. They
    stand up and sway, lean in to cross over the spire (video 0:17), swing out into a wide fan (0:22)
    and fade before the narrator speaks (0:27-0:28). KEYS are (seconds into the scene, inner beam's
    lean, outer beam's lean) in radians, outward positive, so a negative lean crosses the middle."""

    KEYS = (
        (0.0, 0.12, 0.3),
        (5.0, 0.2, 0.38),
        (6.8, -0.55, -0.62),
        (9.5, -0.5, -0.58),
        (11.8, 0.32, 0.48),
        (16.8, 0.3, 0.45),
    )
    FADE = (16.8, 17.8)
    SWAY = 0.06

    def lean(self, e, k):
        """Beam k's (0 inner, 1 outer) lean e seconds into the scene, eased between KEYS."""
        keys = self.KEYS
        if e <= keys[0][0]:
            return keys[0][1 + k]
        for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
            if e < t1:
                f = smooth((e - t0) / (t1 - t0))
                return a[k] + (b[k] - a[k]) * f
        return keys[-1][1 + k]

    def draw_behind(self, put, out, active):
        if not active:
            return
        show = self.show
        e = show.t - (show.cue.start if show.cue else 0.0)
        fade = 1 - smooth((e - self.FADE[0]) / (self.FADE[1] - self.FADE[0]))
        if fade <= 0:
            return
        length = show.height * 1.2
        gap = 3 * self.s
        for side, foot in ((-1, show.castle_x - 2), (1, show.castle_x + show.castle_w + 1)):
            for k, rgb in enumerate(self.COLOURS):
                ox, oy = foot + side * k * gap, show.height - 1
                lean = self.lean(e, k) + self.SWAY * math.sin(e * 1.3 + k * 1.7 + side)
                a = -math.pi / 2 + side * lean
                for j in range(int(length)):
                    level = 0.85 * fade * (1 - j / length)
                    beam = tuple(int(c * level) for c in rgb)
                    for w in range(self.s):  # 2 LEDs wide on a 64-row board
                        put(ox + math.cos(a) * j + w, oy + math.sin(a) * j, beam)


class GreenSearchlights(Searchlights):
    """Green (Trashin' the Camp, and the villains' crossing beams)."""

    COLOURS = ((90, 255, 60), (40, 200, 90))


class TealSearchlights(Searchlights):
    """Turquoise (How Far I'll Go's climax)."""

    COLOURS = ((60, 230, 220), (120, 255, 230))


class PartySearchlights(Searchlights):
    """Nightclub beams cycling through the colours (Genie, the friendship mash-up)."""

    def colours(self):
        hue = self.show.t * 0.25
        return tuple(tuple(int(c * 255) for c in colorsys.hsv_to_rgb((hue + k / 2) % 1.0, 0.8, 1.0)) for k in (0, 1))
