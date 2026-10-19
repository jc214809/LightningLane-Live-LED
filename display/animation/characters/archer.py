import math

from display.animation.drawing import _blackout
from display.motion import ease_out, ramp
from display.pixels import art_pixels, noise, paint


class ArcherReveal:
    """
    An archer rises from the bottom of the board at full draw over a black screen, holds her aim, and
    looses: the string snaps straight and rings, she rocks back a pixel, and the arrow flies out across
    the board, the new screen appearing behind it with a fading white trail. Then she sinks away and
    leaves the ride screen uncovered. 64x64 only (disney.py keeps her off shorter boards): at 31x57 she
    fills the board's height. The string and the arrow are drawn in code, from the cells the art had
    them in, so they can move; every other cell is the user's art as drawn (docs/references/Archer.png).
    Everything is a function of t, so a slow board stays on the clock.
    """

    SCALE = 1
    # docs/references/Archer.png, less its arrow and string (both drawn in code; where the string ran
    # through her hair and face the neighbouring cell fills in, and her arrow's row is outline). '.'
    # empty, K outline, N D T her dress (shadow, base, light), O R P her hair and the bow, F h her skin,
    # w e E her eyes (a glint, light and dark blue), p her cheeks, n her nose, m her mouth (her face is
    # three rows taller than the art's, which had none, so her hair and bow sit higher; a row of skin
    # keeps the nose off the mouth), Y y the gold of her sleeves, b q her quiver, z her boots.
    ART = [
        "..................K............",
        ".................KOK...........",
        ".................KOK...........",
        ".................KOOK..........",
        "..................KOOKK........",
        "..................KKOOOK.......",
        "....................KKOPK......",
        "......................KPPK.....",
        ".......................KPK.....",
        "........KKKKKKKK.......KOOK....",
        ".......KKRRRRRORKK...K..KOK....",
        "......KYYRYORRORRKKKKRK.KOOK...",
        ".....KRRRROOORRRROORRRKK.KPK...",
        ".K..KKRRROOOOOROOOOORKKRKKPPK..",
        "KYKKRRYYORRRRRROOORRRRORK.KPK..",
        "KRRYRYYOROOROROOORRRORRKK.KPK..",
        ".KYRRYORRORRhhhhROORRORORKKPPK.",
        "..KKYRORORRhhhhhORROORRORRRKPK.",
        "...KRRRRORRRFRRFROORORRORORKK..",
        "...KRRRRORweFweFROORORRORORKK..",
        "...KRRRROREEFEEFROORORRORORKK..",
        "..KROORRRhpFnFpFKRROORORRRRKFK.",
        "..KROORRRhFFFFFFKRROORORRRRKFK.",
        ".KKKKKKKKKFKmmFKORROORRKKKKFKFK",
        "KYTTTTTTTyKFFKKKKKKKKKKKKKKFKFK",
        "KYyTTDDDDYKFFFKDDDDYDDDDDyKKKFK",
        ".KKTDDDDDyKFFFKDDDDyDDDDDKKKRK.",
        "...KKKKKKKNKKKKDDDDDyKKKKRRKK..",
        ".......KNNNyyNNDDDDKKRRORRRKRK.",
        ".......KNNNNNNNNKKKRRORORRKRRK.",
        "........KNNNNNNNK..KKORRRKKPK..",
        "........KNNNNNNN.....KKKK.KPK..",
        ".........KNNNNNKK........KPPK..",
        ".........KDDDDPPP........KOK...",
        "........KKPPPPDKK.......KOOK...",
        "....KK.KPPDDDDDKK.......KOK....",
        "...KbbKPKKDDDDDDKK.....KOOK....",
        "..KbbqKPDDDDDDDDKK.....KOK.....",
        "..KbqKPKDDDDDDDDKK....KOOK.....",
        "...KqqKNDDDDDDDDDKK.KKPPK......",
        "....KqKNDDDDDDDDDDDKOOPK.......",
        ".....KNNDDDDDDDDDDKPOKK........",
        ".....KNDDDDDDDDDDKPPK..........",
        "....KNNDDDDKNDDDDKPKNK.........",
        "...KNNNDDDDKNDDDDKPKNK.........",
        "...KNNNDDDDKNNDDDNKNNK.........",
        "..KNNNNDDDDDKNDDDDNNDDK........",
        "..KNNKNNDDDDKNDDDDDDDDK........",
        ".KNNNKNNDDDDKNNDDDKNDDK........",
        ".KNNNNKNNDDDKNNNDDKNNDDK.......",
        "KNNNNNKNNNDDNKNNDDDKNDDK.......",
        "KNNNNNKNNNDDDKNNNDDKNNDDK......",
        "KNNNNNNKNNNDDKNNNDDDKNNNK......",
        ".KKKNNNKNNNNDDKNNNNDDKKK.......",
        "....KKKKKKNNNNKKKKKKKzK........",
        ".....KzzzzKKKK...KzzzzzK.......",
        ".....KKKKK.......KKKKKK........",
    ]
    COLORS = {
        "K": (25, 22, 42), "N": (20, 100, 100), "D": (0, 150, 138), "T": (70, 200, 178),
        "O": (255, 127, 62), "R": (226, 91, 69), "P": (239, 121, 90),
        "F": (242, 228, 214), "h": (226, 190, 160), "Y": (255, 215, 90), "y": (255, 239, 141),
        "b": (186, 116, 93), "q": (158, 85, 86), "z": (81, 48, 70),
        "w": (255, 255, 255), "e": (38, 137, 202), "E": (1, 101, 179), "p": (250, 175, 170), "m": (200, 90, 95),
        "n": (205, 140, 115),
    }

    LEFT = 1  # her art's first column on the board: room for the rock back
    # Where the string ran, per art row: the column it was drawn in at full draw (the rows behind her
    # hand, 24 to 26, keep the nock's). It runs from the bow's tips (rest, TIP_COL) to the nock, a V.
    STRING_COLS = {
        5: 18, 6: 18, 7: 17, 8: 17, 9: 17, 10: 17, 11: 16, 12: 16,
        13: 16, 14: 16, 15: 15, 16: 15, 17: 15, 18: 15, 19: 15, 20: 15,
        21: 14, 22: 14, 23: 14, 24: 14, 25: 14, 26: 14, 27: 14, 28: 14,
        29: 15, 30: 15, 31: 15, 32: 16, 33: 16, 34: 16, 35: 16, 36: 17,
        37: 17, 38: 17, 39: 18, 40: 18,
    }
    TIP_COL = 18
    NOCK = (14, 24)       # art (col, row) of the arrow's tail at full draw
    HAND_COLS = (27, 29)  # the bow hand: the arrow passes behind it
    ARROW_LEN = 20
    STRING_RGB = (255, 255, 255)
    SHAFT_RGB = (235, 205, 150)
    FLETCH_RGB = (240, 60, 50)
    TIP_RGB = (255, 255, 255)

    RISE_S, AIM_S = 0.55, 0.8
    RECOIL_S = 0.13       # she rocks back a pixel
    FLY_PX_S = 170        # the arrow's speed once it's away, in px/s, after a short pick-up
    PICKUP_S = 0.15
    RING_HZ, RING_DECAY_S = 6.0, 0.14  # the string's swing past straight, and how fast it dies
    TRAIL = 16
    HOLD_S = 0.55         # from the release to the start of her sinking
    SINK_S = 0.5

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.art_h = len(self.ART)
        self.top = height - self.art_h  # her top row standing, her feet on the bottom row
        self.release_at = self.RISE_S + self.AIM_S
        self.sink_at = self.release_at + self.HOLD_S
        self.duration = self.sink_at + self.SINK_S
        self.tail0 = self.LEFT + self.NOCK[0]
        self.row = self.top + self.NOCK[1]

    def drop(self, t):
        """Rows below her standing place: rising in her first RISE_S, sinking at the end."""
        if t < self.release_at:
            return int(round(self.art_h * (1 - ease_out(ramp(t, 0.0, self.RISE_S)))))
        sunk = ramp(t, self.sink_at, self.SINK_S)
        return int(round(self.art_h * sunk * sunk))

    def recoil(self, t):
        """Columns she's rocked back by the shot (0 or -1)."""
        return -1 if self.release_at <= t < self.release_at + self.RECOIL_S else 0

    def tension(self, t):
        """The string's pull: 1 at full draw, 0 straight; after the release it swings past and dies away."""
        if t < self.release_at:
            return 1.0
        s = t - self.release_at
        return math.cos(2 * math.pi * self.RING_HZ * s) * math.exp(-s / self.RING_DECAY_S)

    def flown(self, t):
        """How far the arrow has travelled since the release, in px."""
        s = t - self.release_at
        if s <= 0:
            return 0.0
        if s < self.PICKUP_S:
            return self.FLY_PX_S * s * s / (2 * self.PICKUP_S)
        return self.FLY_PX_S * (s - self.PICKUP_S / 2)

    def arrow_tail(self, t):
        return self.tail0 + self.flown(t)

    def front(self, t):
        """The first column still black: the new screen is uncovered behind the arrow's tail."""
        if t < self.release_at:
            return 0
        reach = self.width - self.tail0
        return int((self.arrow_tail(t) - self.tail0) * self.width / reach) + 1

    def string_pixels(self, t, dx, dy):
        """The string at its pull: a V at full draw, each row's column moving between it and straight."""
        pull = self.tension(t)
        out = {}
        for row, col in self.STRING_COLS.items():
            x = self.TIP_COL - int(round(pull * (self.TIP_COL - col)))
            if x == self.NOCK[0] and 24 <= row <= 26:
                continue  # behind her hand
            out[(self.LEFT + x + dx, self.top + row + dy)] = self.STRING_RGB
        return out

    def arrow_pixels(self, t, dy):
        """The arrow, tail to tip: red fletching, a pale shaft, a white head; hidden behind her bow hand."""
        flying = t >= self.release_at
        tail = int(round(self.arrow_tail(t)))
        y = self.row + (0 if flying else dy)
        out = {}
        for i in range(self.ARROW_LEN):
            x = tail + i
            if self.LEFT + self.HAND_COLS[0] <= x <= self.LEFT + self.HAND_COLS[1]:
                continue
            if i == self.ARROW_LEN - 1:
                out[(x, y)] = self.TIP_RGB
            elif i < 3:
                out[(x, y)] = self.FLETCH_RGB
                if i:
                    out[(x, y - 1)] = out[(x, y + 1)] = self.FLETCH_RGB
            else:
                out[(x, y)] = self.SHAFT_RGB
        if not flying and int(t * 6) % 2:  # a glint on the head while she aims
            out[(tail + self.ARROW_LEN, y - 1)] = self.TIP_RGB
        return out

    def trail_pixels(self, t):
        """A fading white wake behind the arrow's tail, with sparkles, only past her bow: it's a function of position."""
        if t < self.release_at:
            return {}
        tail = int(round(self.arrow_tail(t)))
        out = {}
        for k in range(1, self.TRAIL + 1):
            x = tail - k
            if x < self.LEFT + len(self.ART[0]) or x >= self.width:
                continue
            fade = 1 - k / self.TRAIL
            out[(x, self.row)] = tuple(int(230 * fade) for _ in range(3))
            if noise(x, k) < 0.35:
                dy = 1 if noise(k, x) < 0.5 else -1
                out[(x, self.row + dy * (1 + int(noise(x, 7) * 2)))] = tuple(int(c * fade) for c in (255, 235, 170))
        return out

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        cut = self.front(t)
        if cut < self.width:
            _blackout(canvas, cut, self.width, self.height)
        dy, dx = self.drop(t), self.recoil(t)
        paint(canvas, self.trail_pixels(t), self.width, self.height)
        if dy < self.art_h:
            paint(canvas, art_pixels(self.ART, self.LEFT + dx, self.top + dy, self.COLORS), self.width, self.height)
            paint(canvas, self.string_pixels(t, dx, dy), self.width, self.height)
        paint(canvas, self.arrow_pixels(t, dy), self.width, self.height)
        return True
