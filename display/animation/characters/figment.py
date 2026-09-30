import math

from display.animation.mechanics import FlyByReveal
from display.animation.motion import FLYBY_S


class FigmentReveal(FlyByReveal):
    """Figment flutters across, trailing sparkly imagination dust."""

    duration = FLYBY_S * 1.8

    # Side view flying right: curved horns, long snout, slim neck, bat wing, striped tail.
    # '.' empty, P purple body, D darker purple shading, G green wing, N green wing edge,
    # O orange horn/belly/tail stripe, E white eye, B pupil, K outline, M mouth.
    art = [
        "..............KK.....KK..",
        ".............KOOK...KOOK.",
        ".............KOOK..KOOK..",
        "..............KOOKKOOK...",
        "...............KPPPPK....",
        "..............KPPPPPPK...",
        ".....KKKK....KPPEBPPPPK..",
        "...KKGGGGKK..KPPEBPPPPPK.",
        "..KGGNNGGGGK.KPPPPPMMMPPK",
        "..KGNNNNGGGKKPPPPPPMMMPPK",
        "..KGGNNNGGKPPPPPPPPKKKKK.",
        "...KGGGGGKPPPPPPPPPK.....",
        "....KKKKKPPPPPPPPPK......",
        "..KOK....KPPPPPPPK.......",
        ".KOOOK...KPPPPPPK........",
        "KOOKOOK..KPPDDPPK........",
        "KOK.KOK...KPDDPK.........",
        ".K...KK...KPPPPK.........",
        "..........KOOOOK.........",
        "...........KKKK..........",
    ]
    colors = {
        "P": (150, 70, 190), "D": (110, 45, 150), "G": (90, 200, 110), "N": (140, 230, 150),
        "O": (235, 140, 40), "E": (250, 250, 250), "B": (25, 25, 35), "K": (45, 20, 60),
        "M": (230, 120, 160),
    }
    dust_colors = [(210, 140, 255), (255, 255, 255), (140, 220, 255)]

    def position(self, t):
        p = t / self.duration
        # A gentler, wider bob than Tinker Bell's, clamped to the room his sprite leaves.
        room = max(0, self.height - self.sprite_h)
        amp = min(room / 2, self.height * 0.15)
        return self.progress_x(t), room / 2 + math.sin(p * math.pi * 3) * amp

    def spawn(self, x, y):
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w / 2), y + r.uniform(0, self.sprite_w / 2),
                 r.uniform(-0.2, 0.1), r.uniform(0.05, 0.3), r.randint(10, 20), r.choice(self.dust_colors)]
                for _ in range(2 * self.scale)]
