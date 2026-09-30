from display.animation.mechanics import PeekReveal
from display.animation.motion import ease_out


def _pupils_at(base, side):
    """
    Fill each '##' eye slot in `base`. Stitch's eyes are near-black ovals with a small
    white glint; `side` (0 left, 1 right) puts that glint on one side so he reads as
    glancing that way.
    """
    rows = []
    for line in base:
        while "####" in line:
            line = line.replace("####", "WPPP" if side == 0 else "PPPW", 1)
        rows.append(line)
    return rows


class StitchReveal(PeekReveal):
    """Stitch pops up from the bottom, looks left and right, then ducks back down."""

    duration = 2.6
    UP_S, HOLD_S, LOOK_S = 0.35, 0.5, 0.7
    # His whole head, down through the chin, clears the edge at full rise; his
    # shoulders stay hidden below, as if he's propped up on his arms out of frame.
    rise_frac = 0.88

    # Long ears swept up and out (a notch bitten from his left one), a wide head
    # tapering to a rounded chin, big black nose over a broad smile.
    # '.' empty, U light-blue fur, D dark-blue fur (ear backs, shading), K outline,
    # E eye white, P pupil, W pupil highlight, N pink inner ear, B nose, M mouth, T teeth.
    _BASE = [
        "...KK...............KK...",
        "..KRRK.............KRRK..",
        "..KRRRK...........KRRRK..",
        "..KRRRRK.........KRRRRK..",
        "..KRRRRRK.......KRRRRRK..",
        "...KRRRRRK.....KRRRRRK...",
        "...KRRRRRRK...KRRRRRRK...",
        "....KRRRRRKKKKKRRRRRK....",
        "....KRRRRKUUUUUKRRRRK....",
        ".....KRRKUUUUUUUKRRK.....",
        ".....KRKUUUUUUUUUKRK.....",
        "......KUUUUUUUUUUUKK.....",
        ".....KUUUUUUUUUUUUUUK....",
        "....KUUKKKKUUUKKKKUUUK...",
        "....KUK####KUUUK####KUK..",
        "....KUK####KUUUK####KUK..",
        "....KUKKKKKUBBBUKKKKKUK..",
        ".....KUUUUUKBBBKUUUUUK...",
        ".....KUUUUUUKBKUUUUUUK...",
        "......KUUMMMMMMMMMUUK....",
        "......KMMTTTTTTTTTMMK....",
        "......KMMMMMMMMMMMMMK....",
        ".......KKUUUUUUUUUKK.....",
        ".........KKKKKKKKK.......",
    ]

    art = [_pupils_at(_BASE, 0), _pupils_at(_BASE, 1)]
    colors = {
        "U": (100, 160, 210), "R": (155, 125, 180), "K": (18, 18, 28),
        "P": (58, 62, 84), "W": (255, 255, 255),
        "B": (28, 40, 70), "M": (205, 65, 100), "T": (252, 238, 195),
    }

    def rise(self, t):
        if t < self.UP_S:
            return ease_out(t / self.UP_S)
        if t < self.duration - self.UP_S:
            return 1.0
        down_t = t - (self.duration - self.UP_S)
        return 1.0 - ease_out(down_t / self.UP_S)

    def look_frame(self, t):
        settled = t - self.UP_S
        if settled < 0:
            return 0
        return int(settled / self.LOOK_S) % 2
