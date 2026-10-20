"""You've Got a Friend in Me: Woody slides in and waves while alphabet blocks fill the castle, then slides
off, and Buzz flies through and knocks them down."""
import math
import random

from display.animation.characters.buzz import BuzzReveal
from display.fireworks.actors.base import Actor, stamp
from display.motion import smooth


# Woody as a chibi, from docs/references/Woody - New.jpg cell for cell (19 x 26), with two empty columns
# on the right for his raised hand. Drawn for this scene only: the claw scene's 14 x 18 Woody was too
# small to read beside the castle.
WOODY_ART = [
    ".....KKKKKKKKK.......",
    "....KNNNNNNNNNK......",
    "....KNNNNNNNNNK......",
    ".KKKnnnnnnnnnnnKKK...",
    "KNNNNNNNNNNNNNNNNNK..",
    "KNNNNNNNNNNNNNNNNNK..",
    ".KKKKKKKKKKKKKKKKK...",
    "..KnOOOnnnnnOOOnK....",
    "..KnOOOOOOOOOOOnK....",
    "..KOOOWKOOOWKOOOK....",
    "...KOOKKOOOKKOOK.....",
    "...KOOOOOOOOOOOK.....",
    "....KOOOOOOOOOK......",
    ".....KKOOOOOKK.......",
    "....KKWKKKKKWKK......",
    "...KoWKWRRRWKWoK.....",
    "..KooKWKoRoKWKooK....",
    ".KOOoKKWoRoWKKoOOK...",
    ".KOOKKWKoooKWKKOOK...",
    "..KK.KNNNNNNNKwKK....",
    ".....KBBBBBBBKN......",
    ".....KBBBKBBBKNN.....",
    ".....KBBK.KBBKNN.....",
    ".....KNNK.KNNK.......",
    "....KNNNK.KNNNK......",
    "....KKKKK.KKKKK......",
]
WOODY_COLORS = {"K": (0, 0, 0), "N": (146, 75, 47), "n": (95, 50, 11), "O": (234, 200, 175),
                "o": (233, 184, 80), "W": (255, 255, 254), "R": (230, 38, 5), "B": (50, 86, 136),
                "w": (216, 217, 216)}
# His right arm (on our right, by the holster) raised: the hand beside his hat brim and the yellow
# sleeve down to his shoulder; the same arm tipped out a column is the other half of the wave.
_ARM_UP = {6: (18, "K"), 7: (17, "OOK"), 8: (17, "OOK"), 9: (17, "ooK"), 10: (16, "KooK"), 11: (16, "KooK"),
           12: (15, "KKooK"), 13: (14, "KKooK"), 14: (15, "ooK"), 15: (14, "ooK")}
_ARM_OUT = {6: (18, "KK"), 7: (18, "OOK"), 8: (18, "OOK"), 9: (17, "KooK"), 10: (17, "ooK"),
            11: (16, "KooK"), 12: (15, "KKooK"), 13: (14, "KKooK"), 14: (15, "ooK"), 15: (14, "ooK")}


def _waving(arm_out):
    """WOODY_ART with his right arm raised from his side (rows 16-18) to beside his hat, straight up or
    tipped out a column: the two halves of a wave."""
    art = [list(row) for row in WOODY_ART]
    for row in (16, 17, 18):
        art[row][14:18] = "K..."
    for row, (col, cells) in (_ARM_OUT if arm_out else _ARM_UP).items():
        art[row][col:col + len(cells)] = cells
    return ["".join(row) for row in art]


# Buzz flying, from docs/references/Buzz flying 64x64 grid.png cell for cell (40 x 26, its own palette):
# fist out to the right, wings back, legs trailing down to the left. Mirrored to fly right to left.
BUZZ_ART = [
    "............IJJ.........................",
    "...........IIIKK........................",
    ".........AIIIGGJJ.......................",
    "........AIIIGGGGKK......................",
    "........IIIGGGGGGJJA....A...............",
    ".........DIGGGGGGGKKGAAHIA..............",
    "..........AIGGGGGGGIIGGIIAA.............",
    "...........AIGGGGGGGKKHIIHGGGA..........",
    "............AIGGGGGGGHHIIHGGMA..........",
    ".............AIIIIIGHHHHHGGLMMA......AGA",
    ".............AIKKKKKHKHHGGGLALM.....AKHH",
    ".............EKKKKKHAKKAIGGLLMA.AAAGKKHH",
    ".............AKKKKKHAKAAIIGLLMAEIAKKKHDA",
    "..............AKDIIDHHAIIIGLLDAKIIKH....",
    "................DIKKDHKKIIGDDDDKHEA.....",
    "..............DKIDKKKKDIIIGHHKKBD.......",
    ".............AKKICDDHKDIIIIIDA..........",
    ".............AKKKFCCADIIBIII............",
    ".....A......AKKKKCFCHGGIBBHH............",
    "..GHEHHHHGAAKKKKKHCDDGGIKHBA............",
    ".AKKKKKKKHHKKKKKHHDC.GKHEA..............",
    ".GKIKKKKKKKKKKKHD.......................",
    "AKKIKKKKKKKKKKG.........................",
    "DKKKIKKKKKKKDD..........................",
    "DKKDAIKHDAAA............................",
    "AEE.....................................",
]
BUZZ_COLORS = {"A": (0x1D, 0x16, 0x2B), "B": (0x20, 0x9F, 0xB9), "C": (0x45, 0x40, 0x53), "D": (0x55, 0x28, 0x7D),
               "E": (0x5D, 0xAC, 0x1C), "F": (0x70, 0x74, 0x84), "G": (0x87, 0x4D, 0xB0), "H": (0x9B, 0xAB, 0xBC),
               "I": (0xA3, 0xE7, 0x39), "J": (0xF0, 0x2B, 0x35), "K": (0xF8, 0xFA, 0xFF), "L": (0xFF, 0xBE, 0x9E),
               "M": (0xFF, 0xD8, 0xB9)}
BUZZ_BOOTS_ROW = 23  # his boots' middle row (bottom left in the art), where his rocket trail streams from

# Toy blocks in primary colours (red, blue, yellow, green), and on 64x64 a letter on each: A, B, C in turn.
BLOCK_COLOURS = ((230, 40, 40), (40, 90, 230), (250, 210, 40), (40, 190, 70))
LETTERS = (
    (".X.", "XXX", "X.X"),
    ("XX.", "XXX", "XXX"),
    ("XXX", "X..", "XXX"),
)


class BuzzAndWoody(Actor):
    """
    You've Got a Friend in Me, as the real show's alphabet blocks fill the castle, one toy at a time.
    Woody (a chibi, WOODY_ART, 1x on both boards: big enough to read, not to the castle's scale) slides
    in from the left edge, bobbing, over SLIDE_S, waves on the ground there (beside the castle on 64x32,
    in front of its left side on 64x64) while toy blocks drop in and stack up over the castle from its
    base to its spire over FILL_S, then slides back off by WOODY_OFF. Each standing block shows only on
    the castle's pixels, like a projection (its outline and doorway kept): 5x5 ABC blocks on 64x64, 3x3
    shaded ones on 64x32. Then Buzz (BUZZ_ART, flying, 1x on both boards) flies through from SWOOP_AT,
    right to left, fist first, low through the castle's middle (wholly on the board), a short flickering
    rocket trail streaming back from his boots: each block comes loose as he reaches its column, the ones he hits flying off ahead of him and
    the rest toppling, all tumbling to the ground and fading out. Everything is placed by the clock, as
    a function of the seconds into the scene.
    """
    NAME = "Buzz and Woody"
    WAVE_S = 0.3  # each half of Woody's wave
    SLIDE_S = 0.8  # Woody's slide on, and off
    WOODY_OFF = 6.0  # Woody wholly off the left edge
    TRAIL = 6  # trail pixels behind Buzz, per board pixel scale
    FILL_START, FILL_S = 0.3, 5.0  # the blocks stack up from 0.3 s to 5.3 s in
    DROP_S = 0.3  # each block's fall into its slot...
    DROP_ROWS = 4  # ...from this many block sizes above it
    SWOOP_AT, SWOOP_S = 7.0, 1.6  # Buzz through, off the right edge to off the left
    GRAVITY = 90.0  # px/s^2 per board pixel scale, for the loosened blocks
    FADE_S = 0.8  # a block fades this long after it lands
    GONE_BY = 13.8  # every block gone, half a second before the mash-up (the scene is 14 s)

    def __init__(self, show):
        super().__init__(show)
        self.px = 2 if self.big else 1  # board pixel scale, for speeds and the trail
        self.buzz = [row[::-1] for row in BUZZ_ART]  # flying right to left, fist first
        self.buzz_w, self.buzz_h = len(BUZZ_ART[0]), len(BUZZ_ART)
        self.woody = (_waving(False), _waving(True))
        self.woody_w, self.woody_h = len(self.woody[0][0]), len(self.woody[0])
        # His middle row through the castle's middle, unless that puts his boots off the bottom (64x32).
        self.swoop_top = min(show.castle_y + show.castle_h // 2 - self.buzz_h // 2, show.height - self.buzz_h)
        self.block = 5 if self.big else 3
        # The castle's lit pixels, which the blocks are projected onto while they stand.
        self.facade = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind != "D"}
        self.blocks = self._stack(show)

    def _stack(self, show):
        """[(left, top, rgb, letter, landing s, loose s, vx, vy)]: a grid of blocks over the castle, each at
        least half on its pixels (not the doorway's), bottom row first, each row in a random order;
        colours by place so no two neighbours match. Each comes loose when Buzz's front reaches its
        right edge on his way back, flying off ahead of him (left and up) if it's in his path,
        otherwise toppling with a little sideways drift."""
        n, s = self.block, self.px
        # Its own generator: every actor is built with the show, and drawing from the show's would
        # change the fireworks of every version, V1 included.
        rng = random.Random(show.height)
        slots = []
        for r, top in enumerate(range(show.castle_y + show.castle_h - n, show.castle_y - n, -n)):
            row = [(c, left) for c, left in enumerate(range(show.castle_x, show.castle_x + show.castle_w, n))
                   if 2 * sum((left + i, top + j) in self.facade for i in range(n) for j in range(n)) >= n * n]
            rng.shuffle(row)
            slots += [(r, c, left, top) for c, left in row]
        step = self.FILL_S / max(1, len(slots))
        speed = (self.show.width + self.buzz_w) / self.SWOOP_S
        blocks = []
        for k, (r, c, left, top) in enumerate(slots):
            loose = self.SWOOP_AT + (self.show.width - (left + n)) / speed
            hit = top < self.swoop_top + self.buzz_h and top + n > self.swoop_top
            if hit:
                vx, vy = -speed * (0.4 + 0.3 * rng.random()), -(12 + 10 * rng.random()) * s
            else:
                vx, vy = (rng.random() - 0.5) * 16 * s, -4 * rng.random() * s
            blocks.append((left, top, BLOCK_COLOURS[(c + 2 * r) % 4], LETTERS[(c + r) % len(LETTERS)],
                           self.FILL_START + (k + 1) * step, loose, vx, vy))
        return blocks

    def block_at(self, block, e):
        """Where a block's top-left is e seconds into the scene, and how bright (0 when not there)."""
        left, top, _, _, lands, loose, vx, vy = block
        n, ground = self.block, self.show.height - self.block
        if e < lands - self.DROP_S:
            return None
        if e < lands:  # dropping into its slot under gravity
            k = (lands - e) / self.DROP_S
            return left, top - self.DROP_ROWS * n * k * k, 1.0
        if e < loose:
            return left, top, 1.0
        t = e - loose
        g = self.GRAVITY * self.px
        y = top + vy * t + 0.5 * g * t * t
        if y < ground:
            return left + vx * t, y, 1.0
        # Landed: when it reached the ground, then it slides no further and fades.
        t_land = (-vy + math.sqrt(vy * vy + 2 * g * (ground - top))) / g
        fade = 1.0 - (t - t_land) / self.FADE_S
        if fade <= 0 or e >= self.GONE_BY:
            return None
        return left + vx * t_land, ground, min(fade, (self.GONE_BY - e) / 0.3, 1.0)

    def buzz_top_left(self, e):
        """Buzz's top-left e seconds into the scene: off the right edge until SWOOP_AT, then steadily across,
        wholly off the left by SWOOP_AT + SWOOP_S, and on (so his trail follows him off)."""
        k = max(0.0, (e - self.SWOOP_AT) / self.SWOOP_S)
        return self.show.width - (self.show.width + self.buzz_w) * k, self.swoop_top

    def woody_top_left(self, e):
        """Woody's top-left e seconds into the scene, or None once he's gone: sliding in from wholly off the
        left edge to standing at it, then back off it by WOODY_OFF, hopping a pixel as he slides."""
        k = min(1.0, e / self.SLIDE_S, (self.WOODY_OFF - e) / self.SLIDE_S)
        if k <= 0:
            return None
        bob = round(abs(math.sin(math.pi * e / 0.2))) if k < 1 else 0
        return -self.woody_w * (1 - smooth(k)), self.show.height - self.woody_h - bob

    def woody_pose(self, e):
        return self.woody[int(e / self.WAVE_S) % 2]

    def _draw_block(self, out, block, x, y, f, clip):
        """The block at (x, y), f bright; with clip, only where it's on the castle's facade."""
        n, w, h = self.block, self.show.width, self.show.height
        rgb, letter = block[2], block[3]
        x, y = int(round(x)), int(round(y))
        for i in range(n):
            for j in range(n):
                if not (0 <= x + i < w and 0 <= y + j < h) or (clip and (x + i, y + j) not in self.facade):
                    continue
                if n == 5 and 0 < i < 4 and 0 < j < 4:
                    # The face: a pale letter on the block's colour.
                    c = (245, 240, 225) if letter[j - 1][i - 1] == "X" else rgb
                elif i == n - 1 or j == n - 1:
                    c = tuple(int(v * 0.6) for v in rgb)  # its shaded bottom and right edges
                elif i == 0 or j == 0:
                    c = tuple(min(255, int(v * 1.1 + 40)) for v in rgb)  # lit top and left edges
                else:
                    c = rgb
                out[(x + i, y + j)] = tuple(int(v * f) for v in c)

    def draw(self, put, out, active):
        if not active:
            return
        show = self.show
        e = self.elapsed()
        g = show.castle_level()
        for block in self.blocks:
            at = self.block_at(block, e)
            if at:
                # Standing in its slot it's part of the projection; dropping in or knocked loose, it's whole.
                standing = block[4] <= e < block[5]
                self._draw_block(out, block, at[0], at[1], at[2] * g, standing)
        woody = self.woody_top_left(e)
        if woody:
            stamp(out, self.woody_pose(e), WOODY_COLORS, *woody, 1, show.width, show.height)
        left, top = self.buzz_top_left(e)
        left, top = int(round(left)), int(round(top))
        s = self.px
        if left >= show.width or left + self.buzz_w + self.TRAIL * s <= 0:
            return
        # The trail streams back from his boots, hottest nearest him, flickering by the clock.
        mid = top + BUZZ_BOOTS_ROW
        flames = BuzzReveal.flame_colors
        flicker = int(e * 20) % 2
        for i in range(self.TRAIL * s):
            x = left + self.buzz_w + i
            rgb = flames[min(len(flames) - 1, i * len(flames) // (self.TRAIL * s))]
            for y in range(mid - s, mid + s - (1 if (i + flicker) % 3 == 2 else 0)):
                if 0 <= x < show.width and 0 <= y < show.height:
                    out[(x, y)] = rgb
        stamp(out, self.buzz, BUZZ_COLORS, left, top, 1, show.width, show.height)
