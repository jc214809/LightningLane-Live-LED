import math
import random

from display.animation.drawing import art_pixels, paint
from display.animation.mechanics import CapturesScreens


class StitchSurfReveal(CapturesScreens):
    """
    Stitch surfs the new ride in. A teal wave with a foaming crest rolls left to right and
    washes the old ride away, leaving the new one behind it, with a wall of spray carrying the
    edge up the board above the crest. Stitch rides its face on a red surfboard, bobbing with
    the water: standing, arms out, on 64x64; sitting on 64x32.
    """

    wants_prev = True
    duration = 2.6

    # From the user's bead patterns, copied cell for cell. STAND_ART (docs/references/stich.jpg),
    # for 64x64: standing, facing us, ears up with pink insides, arms out. SIT_ART
    # (docs/references/sitting_stitch.jpg), for 64x32, where the standing one is taller than the
    # board: sitting on the board, facing right, his ear swept back. Its black outline is lifted
    # to charcoal and its eye filled indigo inside the black, which read as holes on the board.
    # '.' empty; standing: K outline, B blue fur, M darker blue, L light fur, E eye, G glint,
    # p pale pink, N pink; sitting: k outline, d blue fur, l light blue, e eye, n pink, G glint.
    STAND_ART = [
        ".........................KKKKK.....",
        "........................KBKpppK....",
        "........................KKpppppK...",
        "...KKKK.................KKNppppK...",
        "..KppKBK................KKNNNpppK..",
        ".KppppKBK......KK.......KBKNppppK..",
        "KppNNpKBK.....KMMKK.....KBKNNpppK..",
        "KpppppKBK.....KMMMMKK....KBKNppppK.",
        "KppppNKBK....KBBBBBBBKKK.KBKNNpppK.",
        "KKppNNKBK..KKBBBBBBBBBBBKKBBKNNppK.",
        "KKpNNpKBK.KBBBBBBBBBBBBBBKBBKNNppK.",
        ".KppNNKBKKBBBBBBBBBBBBBLLBMBBKNppK.",
        "KppNNKBBKKBBBBBBBBBBBBLLLLBMBKNKKK.",
        "KppNNKBBKBLLLBBBBBBBBBLEELLMBKNK...",
        "KpNNNKBBMLLLLLBBBBBBBBLGEELBMKNNK..",
        "KKNNNKBBMLLEELBBBKKKKBLEEEELMKNBK..",
        ".KpNNKBMBLEEEELBKMMMMKLEEEELMKNBK..",
        ".KBNNNKMBLEEEELKMMMMMKLEEEELMBBK...",
        "..KBNNKMBLEEEELKMMMMMKBLLLLBMBK....",
        "...KBpKMBLEEEELBKMMMKBBBBBBBMK.....",
        "....KBNBMBLLLLBBBKKKBBBBBBLLMKK....",
        ".....KBBMBBBBBBBBBLLLLLLLLLMKKBKKK.",
        "......KKMBBBBBBBLLLLLLLLLLMKKKBBBK.",
        "......KKKMLLLLLLLLLLLLLLMMKBBBBBBBK",
        "....KKBBKKMMLLLLLLLLLLMMBBBBBBKKBBK",
        "...KBBBBBBKKMMMMMMMMMMBMBBBBBBKKBK.",
        "...KBBKKBBBBBBBMLLLLLLLMBBBBBBBBBBK",
        "..KBBBKKBBBBBBMBLLLLLLLBMBBBBBBKKK.",
        "...KBBBBBBBBBBMLLLLLLLLBKKKKKKK....",
        "....KKBBBBBBBMBLLLLLLLLLBK.........",
        "......KKKKKKKBBLLLLLLLLLBK.........",
        "............KBBLLLLLLLLLBK.........",
        "............KBBLLLLLLLLLBK.........",
        "...........KBMBBLLLLLLLBMK.........",
        "...........KBBMBBLLLLLBMBBK........",
        "..........KBBBBMBBBBBBMBBBK........",
        "..........KBBBBBMBBBBMBBBBK........",
        "..........KBBBBBBKKKMBBBBBK........",
        ".........KBBBBBBK..KBBBBBBBK.......",
        ".........KBKBKBBK...KBBKBKBK.......",
        "..........KKKKKK.....KKKKKKK.......",
    ]
    SIT_ART = [
        ".......kk.................",
        ".......kdk................",
        ".......kddk..kkkkkkk......",
        ".......kdddkkdddddddkk....",
        ".kk....kdddkddddddddddk...",
        "kddk....kdkdddddkkkddddk..",
        "kdddk...kkdddddkkllldddkk.",
        ".kkddk...kdddddkllllldddkk",
        "knnkddkk.kdddddklleeGlddkk",
        "knnnkdddkdddddddlleeeeldkk",
        "knnnnkkdddddddddlleeeelddk",
        ".knnnnnkdddddddddleeeeldk.",
        "..knnnnnkkddddddddlllldk..",
        "...kknnnnnkdkddddddddkk...",
        ".....kkkkkkkdkkkkkkkk.....",
        "..........kkddddklllk.....",
        ".........kdddddddklk......",
        "........kddddkdddklk......",
        "........kdddllkdddkdkkk...",
        ".......kdddkklkkddkdkkdk..",
        ".......kddkdkkddkdkdkddk..",
        "......kdddddkdddkdkkkddk..",
        "......kdddddddddkddkdkdk..",
        ".......kkdddkddkddddkdk...",
        ".........kkkkkkkkkkkkkk...",
    ]
    STAND_SCALE = SIT_SCALE = 1
    colors = {
        "K": (4, 52, 108), "B": (118, 184, 230), "M": (43, 140, 210), "L": (190, 232, 248),
        "E": (45, 45, 45), "G": (255, 255, 255), "p": (250, 226, 232), "N": (240, 160, 185),
        "k": (40, 40, 48), "d": (45, 80, 150), "l": (40, 140, 210), "e": (48, 40, 96), "n": (240, 120, 180),
    }
    WATER_DEEP, WATER, FACE = (0, 80, 120), (0, 135, 165), (40, 185, 200)
    FOAM = (235, 250, 255)
    BOARD, BOARD_SHADE, STRIPE = (225, 30, 40), (150, 18, 26), (255, 255, 255)
    CREST_FRAC = 0.34   # the crest's height, of the board's
    BACK_FRAC = 0.5     # how far the back of the wave runs before it's flat, of the width
    FACE_FRAC = 0.9     # how far its face runs down in front of the crest, of his board
    RIDE_AT = 0.55      # where along the face his board rides, from the crest

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.art = self.STAND_ART if height >= 64 else self.SIT_ART
        self.art_w, self.art_h = len(self.art[0]), len(self.art)
        self.crest = round(height * self.CREST_FRAC)
        self.board_w = self.art_w + 6
        self.back = width * self.BACK_FRAC
        self.face = self.board_w * self.FACE_FRAC
        self.seed = self.rng.random()
        # The crest runs from where all of him is still off the left side to where the
        # back of the wave has gone off the right.
        self.start = -(self.face * self.RIDE_AT + self.board_w / 2) - 2
        self.end = width + self.back + 1

    def crest_x(self, t):
        return self.start + (self.end - self.start) * min(1.0, t / self.duration)

    def surface(self, u):
        """Height of the water u columns ahead of the crest (negative: behind it)."""
        if -self.back <= u <= 0:
            return self.crest * (1 + u / self.back) ** 0.7
        if 0 < u <= self.face:
            return self.crest * (1 - (u / self.face) ** 0.6)  # steep under the lip, easing out
        return 0

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        w, h = self.width, self.height
        xc = int(self.crest_x(t))
        frame = {}
        # Ahead of the crest: the old ride, every pixel of it (the new one is already underneath).
        for x in range(max(0, xc + 1), w):
            for y in range(h):
                frame[(x, y)] = self.prev_px.get((x, y), (0, 0, 0))
        # The water: the back slope, then the face, shaded deeper toward the bottom.
        for x in range(max(0, xc - int(self.back) - 1), min(w, xc + int(self.face) + 1)):
            u = x - xc
            top = h - int(round(self.surface(u)))
            for y in range(top, h):
                frame[(x, y)] = self.FACE if 0 <= u and y < top + 2 else self.WATER if y < top + 3 else self.WATER_DEEP
            if top < h and -self.back * 0.4 < u <= 1:
                frame[(x, top)] = self.FOAM
        # The lip curls forward over the face.
        for i, reach in enumerate((4, 3, 2, 1)):
            y = h - self.crest + i
            for x in range(xc + 1, xc + 1 + reach):
                if 0 <= x < w and 0 <= y < h:
                    frame[(x, y)] = self.FOAM if i == 0 or x == xc + reach else self.FACE
        # Spray up the edge above the crest, thinning with height.
        spray = random.Random(f"{self.seed}:{int(t * 30)}")
        for y in range(0, h - self.crest):
            chance = 0.55 * (y / max(1, h - self.crest)) + 0.15
            for x in (xc, xc + 1, xc - 1):
                if 0 <= x < w and spray.random() < chance:
                    frame[(x, y)] = self.FOAM
        # Stitch on his board, down the face ahead of the curl.
        mid = int(round(xc + self.face * self.RIDE_AT))
        left, right = mid - self.board_w // 2, mid + (self.board_w - 1) // 2
        bob = round(math.sin(t * 9))
        board_y = h - int(round(self.surface(mid - xc))) - 2 + bob
        for x in range(left, right + 1):
            end = x in (left, right)
            if not end:
                frame[(x, board_y)] = self.STRIPE if abs(x - mid) < self.board_w // 2 - 2 else self.BOARD
            frame[(x, board_y + 1)] = self.BOARD if end else self.BOARD_SHADE
        frame.update(dict(art_pixels(self.art, mid - self.art_w // 2, board_y - self.art_h, self.colors)))
        paint(canvas, frame, w, h)
        return True
