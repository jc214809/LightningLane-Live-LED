import math

from display.animation.mechanics import FlyByReveal


class TinkReveal(FlyByReveal):
    """
    Tinker Bell bobs across leaving a drifting trail of pixie dust. Spaceship Earth's
    landmark borrows her too (at 1x on both boards), so there's one Tink.
    """

    # Wings either side, her yellow bun, a face, the green dress and legs; 9x8 on 64x32 and
    # doubled on 64x64 like the other fly-bys. It replaced a 5x5 Tink that read as a
    # glowing glyph rather than a fairy. '.' empty, W wing, Y hair/glow, S skin, G dress.
    art = [
        "....Y....",
        "WW.YYY.WW",
        "WWWYSYWWW",
        "WWW.S.WWW",
        ".WWGGGWW.",
        "...GGG...",
        "..GGGGG..",
        "...S.S...",
    ]
    colors = {"W": (170, 220, 255), "Y": (255, 230, 110), "S": (255, 205, 170), "G": (60, 220, 90)}
    dust_colors = [(255, 235, 140), (255, 255, 255), (255, 200, 90)]

    def position(self, t):
        p = t / self.duration
        return self.progress_x(t), self.height * 0.45 + math.sin(p * math.pi * 3) * self.height * 0.18

    def spawn(self, x, y):
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w / 2), y + r.uniform(0, self.sprite_w / 2),
                 r.uniform(-0.15, 0.15), r.uniform(0.05, 0.35), r.randint(12, 24), r.choice(self.dust_colors)]
                for _ in range(2 * self.scale)]
