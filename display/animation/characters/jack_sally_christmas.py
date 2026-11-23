import math
import random

from display.animation.characters.jack_sally import JackSallyReveal
from display.motion import ease_out, progress
from display.pixels import art_pixels, paint


class JackSallyChristmasReveal(JackSallyReveal):
    """
    The Jack and Sally meet on Christmas party nights ("Meet Santa Jack and Sally at Mickey's Very
    Merry Christmas Party"): the Halloween scene with Jack as Sandy Claws. Zero floats across in a
    Santa hat, his nose glowing, the meet appearing behind him. Then Sally (holly in her hair) and
    Jack (Santa hat, beard, red suit) walk in through falling snow, kiss, a heart floats up, and
    they walk back off. On 64x64 they kiss under mistletoe that pops down from the top of the board,
    pulled back up off the top as they walk away, and Jack's hat has a taller crown.
    """

    FLAKES = 21  # on 64x32; twice as many on 64x64
    FLAKE_FALL = (5, 9)  # pixels a second, slowest to fastest
    FLAKE_SWAY_S = 2.5  # one sway side to side
    DROP_S = 0.4  # the mistletoe dropping in from above the board once Zero's gone
    DIP = 2  # rows it drops past its place before springing back
    SETTLE_S = 0.2  # springing back up to hang at the top edge

    # The Halloween art with the meet's Christmas look added (the user's picks, 2026-11-22, from
    # mocks): Zero gets a Santa hat (five rows over his head, the pom trailing back over his ear);
    # Jack's hat sits on his crown with its tip down his right side to the pom-pom, an ivory beard
    # down his chest, his grey suit red (C) with darker red folds (c) and ivory fur (F) at his
    # cuff and hem; Sally gets a sprig of holly (G leaf, N its dark side, B berries). Built by
    # adding to ZERO_ART and PAIR_ART cell for cell; PAIR_ART_64 is the same pair with a rounded
    # crown on his hat, which only 64x64 has rows for.
    ZERO_ART = [
        ".........FF...........................",
        ".........FFFKKKK......................",
        "..........FKCCCCKKK...................",
        "............KCCCCCCKK.................",
        ".............KCCCCCCCK................",
        "....KK.......KCCCCCCCCK...............",
        "....KWKKKKKKKFFFFFFFFFFK..............",
        "....KKWWWWWWKFFFFFFFFFFFK.............",
        "KKK..KKWWWWWWKKKKKKKKKKKK.............",
        "KWWKKKKKKKWWKKKWWWWWWWWWKK............",
        "KWWWWWWWWKKKKWWWWWWWWWWWWKK...........",
        "KKWWWWWWWWWWWWWWWWWWWWWWWWKK..........",
        ".KKWWWWWWWWWWWWWWWWWWWWWWWWK..........",
        "..KKKWWWWWWWKWWWWWWWWWWWWWWKK.........",
        "....KKKWWWWKKWWWWWWWKKKWWWWWK.........",
        "......KKKKKKWWWWWWWKKKKKWWWWK....KKK..",
        ".........KWWWWWWWWWKKKKKWWWWKK..KKOKK.",
        ".........KWWWWWWWWWKKKKKWWWWWK.KKOOOK.",
        "KK.......KWWWWWWWWWKKKKKWWWWWKKKOOOOOK",
        "KWK......KKWWWWWKKWWKKKWWWWWWWWKOOOOOK",
        "KWWKKKK...KKWWWWWKKWWWWWWWWWWWWKKOOOKK",
        "KWWWWWKKKK.KWWWWWWKKWWWWWWWWWWWWKKOKK.",
        "KWWWWWWWWKKKKKWWWWWKKKKWWWWWWKKK.KKK..",
        ".KWWWWWWWWWKKKKKKKWWWWKKKKKKKK........",
        ".KWWWWWWWWWKMMMMMKKKKKKKKK............",
        ".KKWWWWWWWWWKKMMMMMMMMMMMK............",
        "..KKWWWWWWWWWKKKMMMMMMMKKKKK..........",
        "...KWWWWWWWWWWWKKKKKKKKKWWWKK.........",
        "...KKWWWWWWWWWWWWWWWWWWWWWWWKK........",
        "....KWWWWWWWWWWWWWWWWWWWWWWWWKK.......",
        "....KWWWWWWWWWWWWWWWWWWWWWWWWWKK......",
        "....KKWWWWWWWWWWWWWWWWWWWWWWWWWK......",
        ".....KWWWWWWWWWWWWWWWWWWWWWWWWKK......",
        ".....KWWWWWWWWWWWWWWWWWWWWWWKKK.......",
        ".....KKWWWWWWWWWWWWWWWWKKKKKK.........",
        "......KKKKKWWWWWWWWWWWKK..............",
        "..........KKKWWWWWWWWKK...............",
        "............KKKWWWWWKK................",
        "..............KKKKKKK.................",
    ]
    PAIR_ART = [
        "........HHHHHH.HHH...K.KCCCCCCCCCCCCCCCCK..",
        "......HHRRRRRRHRRRHH.KKCCCCCCCCCCCCCCCCCCK.",
        ".....HRRRHHHRRRHRRRRHKKFFFFFFFFFFFFFFFFKCCK",
        "...GGHGGHHRRHHRHRHHRRHKWWKKWWWWKKKWWWWKKCCK",
        "...NGBGNRRRRRRRKRRRHRHKWKKKKWWKKKKKWWWK.FFF",
        "...HHBBRRRRKKKKSKKKRRKWKKKKKWWKKKKKKWWWKFFF",
        "..HRHRHRRRKKSSSSSSSKRKWKKKKKWWKKKKKKWWWKFFF",
        "..HRHRHRRKKSSSSSSSSKKKWKKKKKWWKKKKKKWWWWK..",
        ".HRRHRRHRKSSSVVVVSSSKWWWKKKWKKWKKKKWWWKWK..",
        ".HRRHRRHRKSSKVVVVVSSKWKWWWWWWWWWWWWWWWKWK..",
        ".HRRRHRHRKSSVKKKKKVSKWKWWWWWWWWWWWWWWKWWK..",
        ".HRRRHRHRKSSKSSSSKSSSKKKWWWWWWWWWWWWKKWWK..",
        ".HRRRHRHRKSSSSSSSSSSSKWKWKWKWKWKWKWKKWWK...",
        ".HRRHRRHRKSSSKSSSSSSSKWWKKKKKKKKKKKWWWWK...",
        ".HRRHRRHRKSSSSKKSSKKKHKWWWWKWKWKWWWWWWK....",
        ".HRRHRRHRKSSSSSSKKSSSK.KWWWWWWWWWWWWWK.....",
        ".HRRHRRHRRKSSSSSSSSSK...KKWWWWWWWWKKK......",
        ".HHRRHRRHRKSSSSSSSKK....KFFFFFFFFFFK.......",
        ".HHRRHRRHRKSSSSKKKRH..KKKFFFFFFFFFFKKKK....",
        ".HHHRHRRHHRKKSKKRRRH.KCCCKFFFFFFFFKCCCCK...",
        ".HRHRHRRHKKKSKSKKKRH.KKKKKFFFFFFFFKccKKK...",
        ".HRHRRRRKTTTYSSQKYKRH....KFFFFFFFFKCK......",
        ".HRHHRRKTKTKYYSKUKYKRH..KCKFFFFFFKKCCK.....",
        ".HRHHRRKSTKYKYKQQKYKRH..KCKFFFFFFK.KCCK....",
        ".HRHHRKSSKHKYYYQKYSSKH.KCCKFFFFFFK.KCCK....",
        ".HHRRKSKHKTUTTKEEEKKSSKCCK.KFFFFKK..FKWWKKK",
        ".KKKKSSKHKUKQUQEEEK.KSScK.KKFFFFKCK.FKWWWWK",
        ".KSSSSKHKKSKKKKSKK..WKKKcKCcKFFKCcCKFKWKKK.",
        "..KKKSKHKSSSK.KSSK..KWWWKCCcKFFKCcCCKcK....",
        ".HRRRRRHKSSK.KSSK....KKKFFKcFFcFFcKFFK.....",
        "HHHHHHHKWWK..KWWK.......KK.KCCKCCK.KK......",
        "......KKKK....KKKK........KKKK.KKKK........",
    ]
    PAIR_ART_64 = [
        ".............................KKKKKKK.......",
        "..........................KKKCCCCCCCKKK....",
        "........................KKCCCCCCCCCCCCCKK..",
        ".......................KCCCCCCCCCCCCCCCCCK.",
        "........HHHHHH.HHH...K.KCCCCCCCCCCCCCCCCCCK",
        "......HHRRRRRRHRRRHH.KKCCCCCCCCCCCCCCCCCCCK",
        ".....HRRRHHHRRRHRRRRHKKFFFFFFFFFFFFFFFFKCCK",
        "...GGHGGHHRRHHRHRHHRRHKWWKKWWWWKKKWWWWKKCCK",
        "...NGBGNRRRRRRRKRRRHRHKWKKKKWWKKKKKWWWK.FFF",
        "...HHBBRRRRKKKKSKKKRRKWKKKKKWWKKKKKKWWWKFFF",
        "..HRHRHRRRKKSSSSSSSKRKWKKKKKWWKKKKKKWWWKFFF",
        "..HRHRHRRKKSSSSSSSSKKKWKKKKKWWKKKKKKWWWWK..",
        ".HRRHRRHRKSSSVVVVSSSKWWWKKKWKKWKKKKWWWKWK..",
        ".HRRHRRHRKSSKVVVVVSSKWKWWWWWWWWWWWWWWWKWK..",
        ".HRRRHRHRKSSVKKKKKVSKWKWWWWWWWWWWWWWWKWWK..",
        ".HRRRHRHRKSSKSSSSKSSSKKKWWWWWWWWWWWWKKWWK..",
        ".HRRRHRHRKSSSSSSSSSSSKWKWKWKWKWKWKWKKWWK...",
        ".HRRHRRHRKSSSKSSSSSSSKWWKKKKKKKKKKKWWWWK...",
        ".HRRHRRHRKSSSSKKSSKKKHKWWWWKWKWKWWWWWWK....",
        ".HRRHRRHRKSSSSSSKKSSSK.KWWWWWWWWWWWWWK.....",
        ".HRRHRRHRRKSSSSSSSSSK...KKWWWWWWWWKKK......",
        ".HHRRHRRHRKSSSSSSSKK....KFFFFFFFFFFK.......",
        ".HHRRHRRHRKSSSSKKKRH..KKKFFFFFFFFFFKKKK....",
        ".HHHRHRRHHRKKSKKRRRH.KCCCKFFFFFFFFKCCCCK...",
        ".HRHRHRRHKKKSKSKKKRH.KKKKKFFFFFFFFKccKKK...",
        ".HRHRRRRKTTTYSSQKYKRH....KFFFFFFFFKCK......",
        ".HRHHRRKTKTKYYSKUKYKRH..KCKFFFFFFKKCCK.....",
        ".HRHHRRKSTKYKYKQQKYKRH..KCKFFFFFFK.KCCK....",
        ".HRHHRKSSKHKYYYQKYSSKH.KCCKFFFFFFK.KCCK....",
        ".HHRRKSKHKTUTTKEEEKKSSKCCK.KFFFFKK..FKWWKKK",
        ".KKKKSSKHKUKQUQEEEK.KSScK.KKFFFFKCK.FKWWWWK",
        ".KSSSSKHKKSKKKKSKK..WKKKcKCcKFFKCcCKFKWKKK.",
        "..KKKSKHKSSSK.KSSK..KWWWKCCcKFFKCcCCKcK....",
        ".HRRRRRHKSSK.KSSK....KKKFFKcFFcFFcKFFK.....",
        "HHHHHHHKWWK..KWWK.......KK.KCCKCCK.KK......",
        "......KKKK....KKKK........KKKK.KKKK........",
    ]
    HAT_ROWS_64 = len(PAIR_ART_64) - len(PAIR_ART)  # the crown's extra rows on 64x64
    # Mistletoe on its red bow, hanging from the top of 64x64 over the kiss: C bow, c its knot and
    # folds, n stem, G and N leaves, w berries with a W shine.
    MISTLETOE_ART = [
        "..CCC...CCC..",
        ".CcccC.CcccC.",
        "..CCCCcCCCC..",
        "....C.n.C....",
        "...C..n..C...",
        ".GG...n...GG.",
        "GNGG.nnn.GGNG",
        ".GNGGnwnGGNG.",
        "...GGwWwGG...",
        "..GNwwwwwNG..",
        ".GNG.www.GNG.",
        ".NG...w...GN.",
    ]
    SALLY_COLORS = JackSallyReveal.SALLY_COLORS | set("GNB")
    JACK_COLORS = JackSallyReveal.JACK_COLORS | set("CcF")
    colors = dict(
        JackSallyReveal.colors,
        C=(200, 20, 30),
        c=(150, 15, 28),
        F=(230, 215, 175),  # ivory, so his beard stands out from his white skull
        G=(40, 170, 60),
        N=(15, 100, 35),
        B=(255, 40, 40),
        n=(110, 140, 50),
        w=(225, 232, 215),
    )
    FLAKE_RGB = (200, 210, 235)

    def __init__(self, width, height, rng=None):
        big = height >= 64
        if big:
            self.PAIR_ART = self.PAIR_ART_64
            self.LIPS = (self.LIPS[0], self.LIPS[1] + self.HAT_ROWS_64)
        super().__init__(width, height, rng)
        if self.zero_h > height:
            # On 64x32 his hat makes him seven rows too tall: the pom's top two rows and the tip
            # of his tail go off the board instead of his hat.
            self.zero_y = -2
        rng = rng or random.Random()
        # Each flake: across the board, its start height, how fast it falls, its sway's phase.
        self.flakes = [
            (rng.uniform(0, width), rng.uniform(0, height), rng.uniform(*self.FLAKE_FALL), rng.uniform(0, 2 * math.pi))
            for _ in range(self.FLAKES * (2 if big else 1))
        ]
        # The mistletoe hangs over the kiss on 64x64; 64x32 has no rows above them for it.
        mistletoe_w = len(self.MISTLETOE_ART[0])
        self.mistletoe_at = (self.pair_x + self.LIPS[0] - mistletoe_w // 2, 0) if big else None

    def snow(self, t):
        """{(x, y): rgb} of the snow at t, falling from when they walk in until they've gone."""
        if not self.walk_in_at <= t < self.duration:
            return {}
        s = t - self.walk_in_at
        out = {}
        for x0, y0, fall, phase in self.flakes:
            x = round(x0 + math.sin(2 * math.pi * s / self.FLAKE_SWAY_S + phase)) % self.width
            out[(x, int(y0 + fall * s) % self.height)] = self.FLAKE_RGB
        return out

    def mistletoe_top(self, t):
        """
        The mistletoe's top row at t (64x64 only, else None): it pops down from above the board once
        Zero's gone, dipping DIP rows past the top edge and springing back to hang there; then it's
        pulled back up as they walk away, slowly at first, clear of the board as they go.
        """
        if not self.mistletoe_at or not self.zero_s <= t < self.duration:
            return None
        h = len(self.MISTLETOE_ART)
        if t < self.zero_s + self.DROP_S:
            return -h + round((h + self.DIP) * ease_out(progress(t, self.zero_s, self.zero_s + self.DROP_S)))
        settle_at = self.zero_s + self.DROP_S
        if t < settle_at + self.SETTLE_S:
            return round(self.DIP * (1 - progress(t, settle_at, settle_at + self.SETTLE_S)))
        pulled = progress(t, self.leave_at, self.duration) ** 2
        return self.mistletoe_at[1] - round(pulled * h)

    def overlay(self, canvas, t):
        if self.zero_s <= t < self.duration:
            paint(canvas, self.snow(t), self.width, self.height)
            top = self.mistletoe_top(t)
            if top is not None:
                art = art_pixels(self.MISTLETOE_ART, self.mistletoe_at[0], top, self.colors)
                paint(canvas, art, self.width, self.height)
        return super().overlay(canvas, t)
