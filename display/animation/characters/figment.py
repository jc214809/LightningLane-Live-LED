import math

from display.animation.mechanics import FlyByReveal
from display.animation.motion import FLYBY_S, FPS


class FigmentReveal(FlyByReveal):
    """Figment flutters across, trailing sparkly imagination dust."""

    duration = FLYBY_S * 1.8  # the class default; each board's is set from its width (see __init__)
    SCALE = 1  # all of him at 1x on both boards
    STEP = 2  # pixels he moves every frame: a steady whole number, or 1- and 2-pixel steps judder
    BOB = 1.2  # rows up and down as he flutters: any more reads as hopping at 1x

    # Flying right. His head is from the user's pixel-art Dreamfinder and Figment (mirrored):
    # orange horns, big yellow eyes, his open grin. The body is drawn to fly along it, after
    # the painted EPCOT Center Figment: a pink striped belly, a small orange wing on his back,
    # and his tail curling up to an orange tuft. That picture's Figment stands 43 rows tall, so
    # lying him down is what fits all of him on 64x32. Earlier drawings: a purple blob with a
    # green wing, then just his head on 64x32. '.' empty, V violet, v deep violet edge,
    # P pink belly, M magenta stripes, Y yellow eyes, O orange, o dark orange, T his mouth,
    # K outline and pupils.
    art = [
        "......................O..........",
        ".....................ooO.........",
        ".....................ooOo........",
        ".................Ooo...oO........",
        "................OoOOo..OVv.......",
        ".Oo........o...oO.OoOvvVvVv......",
        "OOO.......oOo..o...OVVVVVYY......",
        "OO.......oOOOo......vVYYVVYY.....",
        "o.......oOOOOo......vYYYYvKYvv...",
        "vvv......ooOOo.....vVYKYYvVVVVv..",
        "vvvv....vVVooovv.vvvVYKYVVVVVVv..",
        "...v..vvVVVVVVVVvVVvVVYVVVVVvv...",
        "...vvvVVVVVVVVVVVVVVvVVVVVKKK....",
        "....vVVVVVVVVVVVVVVVvvvVTTTKK....",
        "....vvMPPMPPMPPMPPVVVVvVVTTTKK...",
        "....v.MvPMPPMPPMvvvvvvvvVVTTTKv..",
        "........vMPvMvPM......vMvvvvTvv..",
        ".........vv...vv.................",
        ".........O.....O.................",
    ]
    colors = {
        "V": (213, 103, 254), "v": (150, 20, 210), "P": (255, 145, 247), "M": (255, 74, 241),
        "Y": (255, 242, 0), "O": (255, 120, 20), "o": (191, 48, 0), "T": (99, 7, 12), "K": (20, 20, 20),
    }
    dust_colors = [(210, 140, 255), (255, 255, 255), (140, 220, 255)]

    def __init__(self, width, height, rng=None):
        super().__init__(width, height, rng)
        self.scale = self.SCALE
        self.sprite_w, self.sprite_h = len(self.art[0]), len(self.art)
        # Off the left edge to off the right at exactly STEP pixels a frame.
        self.duration = (width + 2 * self.sprite_w) / (self.STEP * FPS)

    def position(self, t):
        p = t / self.duration
        room = max(0, self.height - self.sprite_h)
        return self.progress_x(t), room / 2 + round(math.sin(p * math.pi * 4) * self.BOB)

    def spawn(self, x, y):
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w / 3), y + r.uniform(self.sprite_h / 3, self.sprite_h),
                 r.uniform(-0.2, 0.1), r.uniform(0.05, 0.3), r.randint(10, 20), r.choice(self.dust_colors)]
                for _ in range(2)]
