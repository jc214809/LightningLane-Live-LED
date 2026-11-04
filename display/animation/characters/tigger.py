import math

from display.animation.drawing import _blackout, walking_pixels
from display.animation.motion import FPS
from display.pixels import art_pixels, paint


class TiggerReveal:
    """
    Tigger, two ways, by board. On 64x64 he bounces across on his tail, left to right: his
    tail squashes as he lands and stretches as he springs off again. On 64x32, where he only
    fits lying down, he walks in low on all fours, stalking, wiggles his tail, and pounces off the right.
    Either way the new ride is uncovered behind him.
    """

    STEP = 2  # pixels a frame, steady: uneven steps judder at 1x (see Figment)
    BOUNCES = 4
    SQUASH = 0.12  # the share of each bounce he spends squashed on the ground
    REST_X = 4  # where he stops stalking, lying down
    WIGGLE_S = 0.8
    WIGGLES = 3  # tail sways in WIGGLE_S
    TAIL_ROWS, TAIL_COLS = 10, 17  # LYING_ART's tail: what wiggles
    STALK_POSE_S = 3 / FPS  # each pose of his walk in (drawing.WALK_CYCLE)
    # LYING_ART's paws: (first paw row, back paw and far front paw, near front paw).
    LYING_FEET = (30, set(range(0, 28)) | set(range(39, 58)), set(range(28, 39)))
    POUNCE_STEP = 4  # pixels a frame, steady, when he pounces
    POUNCE_H = 4

    # Both copied cell for cell from pixel-art grids. BOUNCE_ART is the cute sitting Tigger
    # (pink nose, cream face, tail hanging below), 1x on 64x64; its hearts are left out.
    # SQUASHED_ART has two rows of his tail pressed out for a landing. LYING_ART is him on
    # his belly, ready to pounce, 1x on 64x32: exactly the board's height (the tip of his
    # tail lost a row of outline). '.' empty, K outline and stripes, O orange (sitting),
    # G orange (lying), Y face (sitting), C cream (lying), N nose.
    BOUNCE_ART = [
        "..................KKKKK...................",
        "..KKK........KKKKKOOOOOKKKKK.........KKK..",
        ".KOOOKK....KKOOOOOOOOOOOOOOOKK.....KKOOOK.",
        "KOOOOOOK..KOOOOOOOOOOOOOOOOOOOKK..KOOOOOOK",
        "KOOOOOOOKKOOOOOOKKKOOOKKKOOOOOOOK.KOOOOOOK",
        "KOOYYOOOOOOOOOOKKKKYYYKKKKOOOOOOOKOOOYYOOK",
        "KOYYYYYOOOOOOOKKKYYYYYYYKKKOOOOOOOOOYYYOOK",
        "KOYYYYYOOOOOOOKKYYYYYYYYYYKKOOOOOOOYYYYOOK",
        "KOOYYYOOOOOOOKKYYYYYYYYYYYYKKOOOOOOYYYYOOK",
        ".KOYYYOOOOOOKKYYYYYYYYYYYYYYKKOOOOOOYYYOOK",
        "..KOOOOOOOOOKYYYYYYYYYYYYYYYYKOOOOOOYOOOK.",
        "...KKOOOOOOOYYYYYYYYYYYYYYYYYYOOOOOOOKKK..",
        ".....KOOOOOOYYYKKYYYYYYYYKKYYYOOOOOOK.....",
        ".....KOOOOOOYYKKKKYYYYYYKKKKYYOOOOOOK.....",
        "......KKKOOOOYKKKKYYYYYYKKKKYOOOOKKKK.....",
        "......KKKOOOOYYKKYYYYYYYYKKYYOOOOKKK......",
        "......KKOOOOOOOOOONNNNNOOOOOOOOOOOKK......",
        "......KOOOOOOOOONNNNNNNNNOOOOOOOOOK.......",
        "......KOOOOYYYYYNNNNNNNNNYYYYYOOOOK.......",
        ".......KOOYYYYYYNNNNNNNNNYYYYYYOOOK.......",
        ".......KOYYYYYYYYNNNNNNNYYYYYYYYOK........",
        "........KYYYKYYYYYNNNNNYYYYYYYYYOK........",
        ".....KKKKKKKYYYYYYYNNNYYYYYYYKKKKKKK......",
        ".........KYYYKYYYYYYYYYYYYYYYYYKK.........",
        "..........KYKYYYYKYYYYYYKYYYKYKK..........",
        "........KKKKYYYYYYKYYYYKYYYYYKKK..........",
        ".....KKKOOOOKKYYYYYKKKKYYYYYKOOOKKK.......",
        ".......KOOOOOOKYYYYYYYYYYYYKOOOOK.........",
        ".......KOOOOOOOKYYYYYYYYYKKOOOOOK.........",
        "........KOOOOOOOKKYYYYYKKOOOOOOK..........",
        "........KOOOOOOOOOKKKKKOOOOOOOOK..........",
        ".........KKKOOOOOOOOOOOOOOOOOKK...........",
        "............KKKKOOYYYYYYOOOKK.............",
        ".......KKKKKKKKKKKYYYYYYKKKKKKKKKKK.......",
        "......KOOOOOKKKOOYYYYYYYYOOKOOOOOOOK......",
        "......KOOOOOOOKKKKYYYYYYKKKOOOOOOOOK......",
        ".....KOOOOOOOOOOOYYYYYYYYOOOOOOOOOOK......",
        ".....KOOOOOOOOOOOYYYYYYYYOOOOOOOOOOK......",
        "......KOOOOOOOOOOOOYYYYYOOOOOOOOOOK.......",
        "......KOOOOOOOOOOOOOOOOOOOOOOOOOOOK.......",
        ".......KOOOOOOOOOOOOKKKOOOOOOOOOOK........",
        "........KKKKKKKKKKKKOOOKKKKKKKKKK.........",
        "...................KOOOOK.................",
        "...................KOOOOK.................",
        "...................KOOOKK.................",
        "....................KOOOK.................",
        "....................KKOOK.................",
        "....................KOOOK.................",
        "....................KOOOK.................",
        ".....................KKK..................",
    ]
    SQUASHED_ART = BOUNCE_ART[:42] + BOUNCE_ART[44:]
    LYING_ART = [
        ".KKK....KKKKKK............................................",
        "KKKGK..KKKGKKKK...........................................",
        "KKGGGKKGKKGKGGGK..........................................",
        ".KGKGGKGKKKKGGGK..........................................",
        "..KKKGGGK..KGKKK..........................................",
        "...KKKKK...KKKKK..........................................",
        "...........KGGGK.........................KK...............",
        "..........KGGGK..........................KGK..............",
        "..........KKKGK..........................KGKKK............",
        "..........KKGGK....................KKK..KKGGGK............",
        "...........KGGGK.KKKKK............KGGGKKGGGGGGK...........",
        "...........KGGKKKGGGGKKK..........KGGKGGGGGGGKKK..........",
        "............KKKKGGGGKKKKK.....KKK.KGKKGGGGGGKKKKK.........",
        ".............KKKGGGGKKKKKK...KGGGKCKKKGGGGGGKKKCCK........",
        ".............KKKGGGGKKKKGGK..KGGGGKKKKGGGGGKKKKCCK........",
        "............KKKKGGGGKKKGGGK.KKKKGGGKKKGGGGGKKKCCCCK.......",
        "............KGKKKGGGKKGGGKKKKCCCKGGGKKGGGGGKKKCCCKK.......",
        "............KGKKKGGGKGGGGKKKKCCCCKGGGKGGGGGKKCCCCKCK......",
        "............KGGKKGGGKGGGGKKKKCCCCCKGGGGGGGGGKCCCCCCK......",
        "............KGGGKGGGGKGGKKKKGKCCCCCKGGGGGGGGGCCCCKKKKKKKK.",
        "............KGGGGGGKKKGGKKKGGGKCCCCCKGGGGGKGGGCCCKKGGGKNNK",
        ".............KGGGGKGGGKGKKGGGKKKCCKKGGGGKGKGGGGGGGGGGKNNNK",
        ".............KGGGGGGKKKGGGGGKKKKKKKKKKGGKGKKGGGGGGGKKKNNNK",
        "..............KGGGGKKKKGGGGGKKGGGKKKGGKGKKKKKKKKKKKCCKNNNK",
        "..............KGGGKKKKKGGGGGKGKGGKKGGKKKKKCCCCCCCKCCCCKKK.",
        "...............KGGGGGKCCGGGGGKGGGKGGKKKKKCCCCCCCCCKCCCCK..",
        "...............KGGGKKKCCCCGGGGGGGGGGGGKKKKKKKCCCCCCKCCK...",
        "................KGGGKKKCCCCCCCCKGGGGGKGGGGGGGKCCCCCCKK....",
        "...............KGGGKGGGKCCCCCCCKGGGGGGGGGGGGGGKCCCCCK.....",
        "...............KGGKGGGGKKKKKKKKKGGGGGKKGGGGGGKKCCCCCK.....",
        "...............KGGGGGGGK.......KGGGGGGKKGGGGGGKKKKKK......",
        "................KKKKKKK.........KKKKKKKKKKKKKK............",
    ]
    colors = {"K": (60, 34, 20), "O": (253, 103, 38), "G": (255, 162, 0), "Y": (254, 254, 129),
              "C": (232, 228, 151), "N": (245, 166, 202)}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.lying = height < len(self.BOUNCE_ART) + 2
        self.art = self.LYING_ART if self.lying else self.BOUNCE_ART
        self.w = len(self.art[0])
        if self.lying:
            self.creep_s = (self.REST_X + self.w) / (self.STEP * FPS)
            self.pounce_at = self.creep_s + self.WIGGLE_S
            self.duration = self.pounce_at + (width - self.REST_X) / (self.POUNCE_STEP * FPS)
        else:
            self.duration = (width + 2 * self.w) / (self.STEP * FPS)
            # As high as the board allows above his stretched tail.
            self.bounce_h = max(2, min(16, height - len(self.art) - 1))

    def x_at(self, t):
        if not self.lying:
            return -self.w + self.STEP * FPS * t
        if t < self.creep_s:
            return -self.w + self.STEP * FPS * t
        if t < self.pounce_at:
            return self.REST_X
        return self.REST_X + self.POUNCE_STEP * FPS * (t - self.pounce_at)

    def bounce(self, t):
        """(rows above the ground, squashed?) at t: a hop per bounce, squashing between them."""
        phase = (t / self.duration * self.BOUNCES) % 1.0
        if phase < self.SQUASH / 2 or phase > 1 - self.SQUASH / 2:
            return 0, True
        p = (phase - self.SQUASH / 2) / (1 - self.SQUASH)
        return round(math.sin(p * math.pi) * self.bounce_h), False

    def pounce_lift(self, t):
        """Rows he's off the ground lying down: an arc over the pounce, none before it."""
        if t < self.pounce_at:
            return 0
        p = min(1.0, (self.x_at(t) - self.REST_X) / (self.width - self.REST_X))
        return round(math.sin(p * math.pi) * self.POUNCE_H)

    def tail_sway(self, t):
        """How far the tip of his tail sways (-2..2 columns) while he waits to pounce."""
        if not self.creep_s <= t < self.pounce_at:
            return 0
        return round(2 * math.sin((t - self.creep_s) / self.WIGGLE_S * self.WIGGLES * 2 * math.pi))

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = int(round(self.x_at(t)))
        _blackout(canvas, x + self.w, self.width, self.height)  # ahead of him, still dark
        if self.lying:
            y = self.height - len(self.art) - self.pounce_lift(t)
            sway = self.tail_sway(t)
            walking = int(t / self.STALK_POSE_S) if t < self.creep_s else None
            pixels = []
            for (px, py), rgb in walking_pixels(self.art, x, y, self.colors, self.LYING_FEET, walking):
                row, col = py - y, px - x
                if row < self.TAIL_ROWS and col < self.TAIL_COLS:
                    px += round(sway * (self.TAIL_ROWS - row) / self.TAIL_ROWS)  # the base stays put
                pixels.append(((px, py), rgb))
        else:
            lift, squashed = self.bounce(t)
            art = self.SQUASHED_ART if squashed else self.art
            pixels = art_pixels(art, x, self.height - len(art) - lift, self.colors)
        paint(canvas, pixels, self.width, self.height)
        return True
