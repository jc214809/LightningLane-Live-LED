"""
The runDisney Wine & Dine 10K (The Three Caballeros): José, Panchito and Donald on the medal's royal
blue under "Wine & Dine" and a gold 10K, Panchito centre stage. Each hops in turn, then all three
together as confetti bursts from the top and drifts down. It replaces Spaceship Earth on race day
(utils/special_events.py DATED_LANDMARKS).
"""

import math

from display.pixels import art_pixels

from display.landmarks.scene import Landmark
from display.landmarks.wine_and_dine import GOLD, _text_pixels


WHITE = (255, 255, 255)
MID_FONT = ("assets/fonts/patched/7x13B.bdf", 11)  # the 10K: one size down from the 5K's, to clear Panchito
SMALL_FONT = ("assets/fonts/patched/5x8.bdf", 7)
TINY_FONT = ("assets/fonts/patched/4x6.bdf", 5)

# Traced from the DuckTales (2017) renders of Panchito and José and a classic Donald render on the
# Disney wiki (docs/references/Three Caballeros *.png), keeping their line art; Donald's sailor cap
# swapped for a sombrero and his raised arm moved out clear of its brim.
COLORS = {
    "K": (0, 0, 0),
    "L": (245, 220, 150),
    "N": (70, 200, 70),
    "O": (255, 140, 0),
    "R": (225, 30, 30),
    "T": (235, 190, 115),
    "W": (255, 255, 255),
    "Y": (255, 205, 30),
    "b": (120, 165, 245),
    "k": (45, 45, 50),
    "o": (185, 80, 0),
    "r": (140, 10, 25),
    "t": (170, 120, 60),
}

JOSE_64 = [
    "..........KK.............",
    "........KKooK.K..........",
    ".......KooKKKKoK.........",
    "......KooKKKoooK.........",
    ".......KKKoNNNKKK........",
    "......KoooNNNNNOOK.......",
    "......KooNNTTNOOOOK......",
    ".......KKNNTKNOOOOK......",
    ".......KNNNTKKOOOOK......",
    "......KNNNNOKOOOOOK......",
    "......KNNNNOOOOOOOK......",
    "......KNNNNOOOOOOK.......",
    "...KK..KKKKNOOOKK........",
    "..KYYK.....KTTK..........",
    "...KYYK.....KTK..........",
    "..KYYYKK.KKKKKKK.........",
    ".KYYYYTYKYYYKKKKK........",
    "KYYYYTTYYYYYKYKYYK.......",
    ".KYKKKYYYYYYYYYYYYK......",
    "..K..KKKYKYYYYYYYYYKKKK..",
    "....KttKKYYYYYYKYYYYYYYK.",
    "....KKKtYYYYYYYKKYKYYYYYK",
    "...KooooNYYYYYK..K.KYYoYK",
    "..KoooKNNYYYYYK.....KoKK.",
    "...KKKtKNNNYYYK.....KK...",
    "....KtKKNNNNNK......KK...",
    ".....K.KNNNNNK......KK...",
    "........KNNNNNK....KKKK..",
    ".......KKNNNNNKKKKKKKKK..",
    "....KKKOOOOKOOOOOOOKKK...",
    "...KOOOOOOOKOOOOOOOKK....",
    "...KOOOOOOK.KKOOOOK......",
    "....KOOOOK....KKKK.......",
    ".....KKKK................",
]

PANCHITO_64 = [
    ".......KKKKKKK.............",
    ".....KKLLLLLLLKK...........",
    "....KLLLLLLLLLLLKK.........",
    "...KLLLTTTTLLLLLLLK........",
    "..KLTTTTTTTTTTLLLLLK.......",
    ".KLTTTTTTTTTTTTLLLLLK......",
    ".KTTTTTTTTTTTTTTLLLLK......",
    ".KTTTTTTTTTTTTTTTLLLK......",
    ".KTTTTTTTrTTTTTTTLLLK......",
    ".KTTTTTTTTrrTTTTTLLLK......",
    ".KTTTTTrrrrrTTTTTLLLK......",
    ".KTTTTTrrrrrrTTTTLLLK......",
    "..KTTTrrrrrrTTTTTLLKLK.....",
    "..KTTTrrrrrrTTTTTLLKLLK....",
    "..KTTTrLrrLrTTTTLLLKLLK....",
    "..KTTTTLrLLrTTTTLLLKKK.....",
    "...KTrLKLLLrTTTTLLLK.......",
    "...KTOLKLLKrrTTTLLK........",
    "...KOOOOLKrOrTTLLLK........",
    "..KOOOOOOOOOTTTLLLK........",
    "..KOOOOrrrOOTTTLLLK........",
    "...KKKrrrOTTTTTLLK.........",
    "....KOrOKTTTTTTLLK.........",
    ".....KKKrKTTTTLLK..........",
    ".......KrKKKKTKK...........",
    ".....KKrrrrrrrrrK..........",
    "....KrrKrrrKKKrrK..........",
    "...KrrrKrrrK.KrrK....KK....",
    "..KrrKKKrrrrKrrrK..KKrrKK..",
    ".KrrK..KrrrLLLrrK.KrrrrrrK.",
    ".KrrrKKKrrrLLLLrKKrrrrKrrK.",
    ".KrrLLLKrrrrLLLKKrrrKrrKrK.",
    ".KrrLLLLKrrrLLOOrrrrrrrrK..",
    "..KrLLLKKLLrOTKOOOKKrrrrK..",
    "...KKLK.KLOLOKKOOOKKrKrrK..",
    ".....K..KOOLrrOOOOK.KKrK...",
    "........KOOKrrrKrK....K....",
    ".........KKrrKKKrK.........",
    "........K.KrK.KKrK.........",
    "..KKKKKKrKrrOKOrrKK........",
    ".KOOOOOOOrrrOOOrrrOKKKKKKK.",
    "KOOOOOOOOOrKKKrrOOOOOOOOOOK",
    "KOOOOOOOOKK...KKOOOOOOOOOOK",
    ".KOOOOOOK.......KKOOOOOOOK.",
    "..KKOOKK..........KKOOOKK..",
    "....KK..............KKK....",
]

DONALD_64 = [
    ".................KKK............",
    "................KTTTK...........",
    "...............KTTTTTK..........",
    "...............KTTTTLK..........",
    "..............KRRRRRRRK.........",
    "..........KLK.........KLK.......",
    "..K....K..KLLLLLLLLLLLLLLLK.....",
    ".KWKKKKWK..KtttttttttttttK......",
    ".KWWWWWWK.....KWWWWWWWK.........",
    "..KWWWWK.......KWKWWWWK.........",
    "...KWWWK........KKWWWKWK........",
    "....KWWK.....KKKKOWWKKWK........",
    ".....KWbK.....KOOOOWKKK.........",
    ".....KkbWKK....KOOOOOK..........",
    "......KkbbbK....KKOOK...........",
    ".......KWbbbKKKKKWWK............",
    ".........KbbbbKWWWWK............",
    "..........KbbKKKKWWK............",
    "............KbKKKbbK............",
    ".............KKKKbbbK...........",
    "..............KKKbbbbK..........",
    ".............KbbbbbbbbKKK.KK....",
    ".............KbbbbKbbbbWWKWK....",
    "..............KbbbbWbbbWWWWK....",
    "..............KbWbWWWbWWWWWK....",
    "...............KbbbWKKWWWWK.....",
    "................KbbWKWWWWWK.....",
    ".................KWWWWWOOK......",
    ".........KKKKKKKKOKKWWWKOOK.....",
    "........KOOOOOOOOK..KKKKKOKK....",
    "........KOOOOOOOK.....KOOOOOKK..",
    ".........KOOOOOK......KOOOOOOOK.",
    "..........KKKKK........KOOOOOOK.",
    "........................KKOOKK..",
    "..........................KK....",
]

JOSE_32 = [
    ".....KK........",
    "....KooKK......",
    ".....KKNoK.....",
    "....KoNNNOK....",
    "....KNNTOOOK...",
    "....KNNKOOOK...",
    "....KNNOOOK....",
    "..KK.KKOOK.....",
    ".KYYK.KKK......",
    ".KYYTKYKKK.....",
    "KYYTYYYYYYK....",
    ".KKKKKYYYYYKKK.",
    "..KKtYYYYKYYYYK",
    ".KooNNYYYKKKoK.",
    "..KKKNNNK...K..",
    "....KNNNK...K..",
    "...KKNNNNKKKK..",
    "..KOOOOOOOOKK..",
    "..KOOOKKKKK....",
    "...KKK.........",
]

PANCHITO_32 = [
    "....KKKKK........",
    "...KLLLLLKK......",
    "..KLTTTLLLLK.....",
    ".KTTTTTTTLLLK....",
    ".KTTTTTTTTLLLK...",
    ".KTTTTrTTTTLLK...",
    ".KTTTrrrTTTLK....",
    ".KTTrrrrTTTLKK...",
    ".KTTrrrrTTLLLLK..",
    ".KTTLLLrTTLLKK...",
    "..KTKLLrTTLK.....",
    "..KOOLKOTTLK.....",
    ".KOOOrOTTLLK.....",
    "..KKrKTTTLLK.....",
    "....KrKTTLK......",
    "...KrrrrrrK......",
    "..KrrrrKKrK.KKK..",
    ".KrKKrrLrrKKrrrK.",
    "KrrLKrrLLLKrrrrrK",
    ".KrLLrrrLOrrrrrK.",
    "..KLKKOOKOOKrrrK.",
    "...K.KOrrrOKKKK..",
    "......KrKKrK.....",
    ".KKKKKKrKrrKKKK..",
    "KOOOOOrrOrrOOOOK.",
    "KOOOOOKKKKOOOOOOK",
    ".KOOOK....KKOOOK.",
    "..KKK.......KKK..",
]

DONALD_32 = [
    "..........KKK.....",
    ".........KTTTK....",
    ".........KRRRK....",
    "......KLLLLLLLLLK.",
    "..KKK..KtttttttK..",
    ".KWWWK.KWKKK......",
    ".KWWWK..KWWWK.....",
    "..KWWKKKOOWK......",
    "...KWK.KOOOK......",
    "...KbbK.KWK.......",
    "....KbbKWWK.......",
    ".....KbKKWK.......",
    "......KKKbbK......",
    "......KbbbbbKKK...",
    "......KbbbbbWWWK..",
    "......KbbbWWWWWK..",
    ".......KbbWWWWK...",
    "....KKKKKWWWOOK...",
    "...KOOOOOKKKKOKKK.",
    "...KOOOOK..KOOOOOK",
    "....KKKK....KOOOK.",
    ".............KKK..",
]


SKY_TOP, SKY_BOTTOM = (30, 70, 190), (15, 40, 140)  # the medal's royal blue
RAIN = (90, 150, 230)
RAIN_SPEED = 18  # px a second
RAIN_EVERY = 4  # one drop per this many columns

ORDER = ("jose", "panchito", "donald")  # who hops when, left to right across the board
HOP_AT = {"jose": 0.6, "panchito": 1.2, "donald": 1.8}
ALL_HOP = 2.6  # then all three together, as the confetti starts
HOP_S = 0.35
CONFETTI_FROM = (2.6, 3.6)  # pieces set off from above the board across this second
CONFETTI = ((255, 60, 160), (255, 220, 0), (40, 220, 80), (255, 130, 0), (40, 220, 255), (255, 255, 255))
CONFETTI_COUNT = 50  # on 64x32, scaled by board area
FALL_SPEED = 12  # px/s on 64x32, scaled by the board height


class ThreeCaballeros10KLandmark(Landmark):
    """Wine & Dine 10K: the Three Caballeros hop in turn under a gold 10K, then confetti falls."""

    SCREEN_S = 6.0

    def build(self):
        w, h = self.width, self.height
        big = h >= 64
        self.art = {"jose": JOSE_64 if big else JOSE_32, "panchito": PANCHITO_64 if big else PANCHITO_32,
                    "donald": DONALD_64 if big else DONALD_32}
        self.size = {k: (len(a[0]), len(a)) for k, a in self.art.items()}
        jw, pw, dw = (self.size[k][0] for k in ORDER)
        # Standing on the bottom edge: José left, Panchito centre stage, Donald right.
        xs = {"jose": -3 if big else 0, "panchito": w // 2 - pw // 2 - 2 if big else w // 2 - pw // 2 - 1,
              "donald": w - dw + 1 if big else w - dw}
        self.home = {k: (xs[k], h - self.size[k][1]) for k in ORDER}
        self.hop_px = 3 if big else 2
        if big:
            title = [(SMALL_FONT, "WINE & DINE", 32, 0, WHITE), (MID_FONT, "10K", 32, 6, GOLD)]
        else:
            title = [(TINY_FONT, "WINE&", 10, 0, WHITE), (TINY_FONT, "DINE", 9, 6, WHITE),
                     (MID_FONT, "10K", 53, -2, GOLD)]
        self.title_spec = title
        self.text = {}
        for font, text, center_x, top, rgb in title:
            self.text.update(_text_pixels(font, text, center_x, top, rgb))
        self.sky = {}
        for y in range(h):
            f = y / (h - 1)
            rgb = tuple(round(a + (b - a) * f) for a, b in zip(SKY_TOP, SKY_BOTTOM))
            for x in range(w):
                self.sky[(x, y)] = rgb
        self.drops = [(x, self.rng.uniform(0, h)) for x in range(1, w, RAIN_EVERY)]
        k = h / 32
        self.confetti = [(self.rng.uniform(0, w), -self.rng.uniform(1, 8 * k), self.rng.uniform(*CONFETTI_FROM),
                          self.rng.uniform(-3, 3), FALL_SPEED * k * self.rng.uniform(0.8, 1.2),
                          self.rng.choice(CONFETTI), self.rng.uniform(0, 2 * math.pi))
                         for _ in range(int(CONFETTI_COUNT * k * w / 64))]

    def hop(self, name, t):
        """Pixels up off the ground at scene time t: its own hop, then the one all three do."""
        for start in (HOP_AT[name], ALL_HOP):
            if 0 <= t - start < HOP_S:
                return round(self.hop_px * math.sin(math.pi * (t - start) / HOP_S))
        return 0

    def positions(self, t):
        """{name: (x, y)} of each character's top-left at scene time t."""
        return {k: (x, y - self.hop(k, t)) for k, (x, y) in self.home.items()}

    def rain(self, t):
        out = {}
        for x, start in self.drops:
            y = int(start + t * RAIN_SPEED) % self.height
            for dy in (0, 1):
                if y + dy < self.height:
                    out[(x, y + dy)] = RAIN
        return out

    def confetti_pixels(self, t):
        out = {}
        for x0, y0, t0, vx, fall, rgb, phase in self.confetti:
            age = t - t0
            if age < 0:
                continue
            x = round(x0 + vx * age + 1.5 * math.sin(age * 5 + phase))
            y = round(y0 + fall * age)
            if 0 <= x < self.width and 0 <= y < self.height:
                out[(x, y)] = rgb
        return out

    def frame(self, t):
        out = dict(self.sky)
        out.update(self.rain(t))
        pos = self.positions(t)
        for name in ("jose", "donald", "panchito"):  # Panchito, centre stage, in front
            x, y = pos[name]
            for (px, py), rgb in art_pixels(self.art[name], x, y, COLORS):
                if 0 <= px < self.width and 0 <= py < self.height:
                    out[(px, py)] = rgb
        out.update(self.text)
        out.update(self.confetti_pixels(t))
        return out
