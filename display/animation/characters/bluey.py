import math

from display.animation.drawing import _blackout, walking_pixels
from display.animation.motion import FPS
from display.motion import smooth
from display.pixels import art_pixels, paint


class GranniesReveal:
    """
    Bluey and Bingo as the Grannies, Janet and Rita, shuffle slowly in from the left side by
    side in their dressing gowns and curlers, uncovering the new ride behind them. Bingo goes a
    step at a time with her walking frame: she lifts it and plants it a step ahead, her arm
    reaching after it, then shuffles up to it, feet stepping and a bob as each lifts. Bluey
    shuffles along steadily beside her. They take about 10s to cross, so the ride screen stays
    up a while after they've gone.
    """

    SCALE = 1  # each board has its own art, both 1x
    hold_after_s = 3.0  # the ride screen, after they leave
    # Bingo's step with the frame: (pixels a step, frames the frame is up and moving a pixel a
    # frame, frames a step). She shuffles up to it in the rest of the step, so the pair goes
    # about 10 pixels a second (Chip 'n' Dale run 60).
    SHUFFLE, BIG_SHUFFLE = (4, 4, 12), (6, 6, 16)
    BLUEY_POSE_F = 3  # frames each pose of Bluey's shuffle (drawing.WALK_CYCLE)
    # Columns between the frame and Bluey at rest; the frame gets a step ahead of her when lifted.
    GAP, BIG_GAP = 4, 5
    # Bingo's sleeve, (column, rows) in her art: when the frame is ahead of her, her hand goes
    # with it and this column repeats to fill the gap, so her arm reaches after it.
    SLEEVE, BIG_SLEEVE = (13, range(9, 13)), (18, range(14, 20))

    # From the user's grid pattern of the pair. 64x64 gets it cell for cell; 64x32 a redraw
    # about 24 rows tall, since the pattern's 40 rows don't fit. Bluey is mirrored to face the
    # way they walk; her nose's black is lifted to charcoal, as LEDs draw black as off. Bingo's
    # walking frame is its own art so it can lift (its top is her hand on the handle). Bingo:
    # '.' empty, K outline, D gown, W white, O orange fur, T tan, L tan shading, N brown patch,
    # P pupils, S shorts, Q shorts' edge; the frame: R handle, G pole, T base, K feet. Bluey:
    # A light blue, B red, C gown, U purple hair, F dark blue, W white, P pupils, E blue fur,
    # T tan snout, L its shading, J nose, G shorts, H their edge.
    BINGO_ART = [
        "...KKKKKKKK......",
        "..KDDWWDDWWK.....",
        ".KDDWWWDDWWWK....",
        "KDDKKKKKKKKKDK...",
        "KDKOOOWWWOOOKK...",
        "KDKOOWWWWWOOKK...",
        "KDKOWPWWWPWOKK...",
        "KDKOWPWWWPNOKK...",
        "KDKOWWWWWNNOKK...",
        "KDKOWLWWWWLOKKKK.",
        "KDKTWWLLLLTTKDDDK",
        "KDKTTWWWWWTTKDDK.",
        "KDKTTTTTTTTKKKKK.",
        "KDDKKKKKKKKDDDK..",
        "KDDDDDDKDDDDDK...",
        "KDDDDDDKDDDDDK...",
        "QSSSSSSQSSSSSQ...",
        "QSSSSSSQSSSSSQ...",
        ".QQQQQQQQQQQQ....",
        "...WW....WW......",
        "...WWW...WWW.....",
    ]
    WALKER_ART = [
        "..WW.",
        ".RWWR",
        ".R..R",
        ".RRRR",
        "..G..",
        "..G..",
        "..G..",
        "..G..",
        ".TTT.",
        "KTTTK",
        "KK.KK",
    ]
    BIG_BINGO_ART = [
        "....KKKKKKKKKKK......",
        "...KDDDDDDDDDDDK.....",
        "..KDDDDWWDDDDWWDK....",
        ".KDDDDWWWWDDWWWWDK...",
        "KDDDDWWWDDDDDDWWDK...",
        "KDDDKKKKKKKKKKKKDK...",
        "KDDKKOOOOWWWOOOOKK...",
        "KDDKOOOWWWWWWWOOKK...",
        "KDDKOOWWPWWWPWWOKK...",
        "KDDKOOWWPWWWPWWOKK...",
        "KDDKOOWWWWWWWNNOKK...",
        "KDDKOOOWWWWWWNNOKK...",
        "KDDKOOOWWLWWWWLOKK...",
        "KDDKOOWWLWWWWWLOKK...",
        "KDDKOWWLWLWWWWLOKKKDK",
        "KDDKTWWWWWLLLLTTKKDDD",
        "KDDKTTWWWWWWWTTTKKDDD",
        "KDDKTTTTTTTTTTTTKKDDD",
        "KDDKTTTTTTTTTTTKDKDDK",
        "KDDDKTTTWWWWWTTKDKDK.",
        "KDDDDKKKKKKKKKKDDKK..",
        "KDDDDDDDDDKKDDDDDK...",
        "KDDDDDDDDDKKDDDDDK...",
        "KDDDDDDDDKDKDDDDDK...",
        "QSSSSSSSSSSQSSSSSQ...",
        "QSSSSSSSSSSQSSSSSQ...",
        "QSSSSSSSSSSQSSSSSQ...",
        "QSSSSSSSSSSQSSSSSQ...",
        "..QQQQQQQQQWQQQQQ....",
        ".....WWW...WW........",
        ".....WWWW..WWWW......",
        ".....WWWW..WWWW......",
        ".....WWWW..WWWW......",
    ]
    BIG_WALKER_ART = [
        ".KWWW...",
        "KKWWW...",
        "..RWRRR.",
        "..RKKKR.",
        "..R...R.",
        "..RRRRR.",
        "...RRR..",
        "...GGG..",
        "...GGG..",
        "...GGG..",
        "...GGG..",
        "...GGG..",
        "...GGG..",
        "...GGG..",
        "...GGG..",
        "..TTTTT.",
        "..TTTTT.",
        ".KKTTTKK",
        ".KK...KK",
        ".KKK.KKK",
        ".KKK.KKK",
    ]
    BLUEY_ART = [
        "...BBAAABBAAA...",
        "...BCCCAACCCAA..",
        "..BCCCCCCCCCCCB.",
        ".BCCBBBBBBBBBBB.",
        "BCCBUUUUUUUUUUUU",
        "BCCBUFFWWUUWWFFU",
        "BCCBUFWWPUUPWWFU",
        "BCCBUFWWPEUPWWFU",
        "BCCBFUUUUEEATJJJ",
        "BCCBEEEEEEATTTTJ",
        "BCCBEEEEATTTTTTL",
        "BCCBEEEATTTTTTTL",
        "BCCBEEEATLLLLLLB",
        "BCCCBEEAAAAEEBCB",
        "BCCCCBAAEEEEBCCB",
        "BCCCCCBBBBBBCCCB",
        "BCCCCCCBBCCCCCCB",
        "BCCCCCBCCBCCCCCB",
        "BCCCCCBCCCCCCCCB",
        "HGGGGGHGGGGGGGGH",
        "HGGGGGHGGGGGGGGH",
        ".HHHHHAHHHHHHHH.",
        "...AAA....AAA...",
        "...AAAA...AAAA..",
    ]
    BIG_BLUEY_ART = [
        ".....BBBAAAABBBAAAA...",
        "....BCCAAAAACCCAAAAA..",
        "...BCCCCAAACCCCCAAAB..",
        "..BCCCCCCCCCCCCCCCCCB.",
        ".BCCCBBBBBBBBBBBBBBBB.",
        "BCCCBUUUUUUUEEEUUUUUUU",
        "BCCCBUUUFFWUUEUUWFFUUU",
        "BCCCBFUFFWWWUUUWWWFBUU",
        "BCCBUUUFWWPWUUUPWWFBUU",
        "BCCBUUUFWWPWUEUPWWFBUU",
        "BCCBFFUWWWPWUEEATTTJJJ",
        "BCCBFUUUWWWUEEEATTTJJJ",
        "BCCBFUUUUUUEEAAATTTTJL",
        "BCCBFFFFEEEAATTTTTTTTL",
        "BCCBEEEEEAATLTTTTTTTTL",
        "BCCBEEEEEATLTTTTTTTTTL",
        "BCCBEEEEEALTLTTTTTTTLB",
        "BCCBEEEEEATTTLLLLLLLCB",
        "BCCCBEEEEATTTTTTAEEBCB",
        "BCCCCBEEEAAAAAAAAEEBCB",
        "BCCCCBEEEEEEEEEEEEEBCB",
        "BCCCCCBBAAAAEEEEEEEBCB",
        "BCCCCCCCBBAAAAEEEEBCCB",
        "BCCCCCCCCCBBAAAEEBCCCB",
        "BCCCCCCCCCBBBBBBBCCCCB",
        "BCCCCCCCCCBBBCCCCCCCCB",
        "BCCCCCCCCBCBBCCCCCCCCB",
        "BCCCCCCCBCCBCBCCCCCCCB",
        "BCCCCCCBCCCBCCBCCCCCCB",
        "BCCCCCCCCCCBCCCCCCCCCB",
        "BCCCCCCCCCCBCCCCCCCCCB",
        "HGGGGGGGGGGHGGGGGGGGGH",
        "HGGGGGGGGGGHGGGGGGGGGH",
        "HGGGGGGGGGGHGGGGGGGGGH",
        "HGGGGGGGGGGHGGGGGGGGGH",
        ".HHHHHHHHHHAHHHHHHHHH.",
        "...AAAA....AAAA.......",
        "...AAAAA...AAAAA......",
        "...AAAAAA..AAAAAA.....",
        "...AAAAAA..AAAAAA.....",
    ]
    BINGO_COLORS = {"K": (101, 21, 179), "D": (180, 107, 255), "W": (251, 255, 251),
                    "O": (251, 148, 39), "T": (241, 193, 76), "L": (190, 151, 44), "N": (91, 45, 10),
                    "P": (36, 37, 37), "S": (253, 160, 252), "Q": (248, 43, 228), "R": (230, 42, 40),
                    "G": (184, 181, 182)}
    BLUEY_COLORS = {"A": (198, 226, 244), "B": (230, 42, 40), "C": (241, 113, 116),
                    "U": (180, 107, 255), "F": (50, 67, 213), "W": (251, 255, 251), "P": (36, 37, 37),
                    "E": (127, 195, 245), "T": (241, 193, 76), "L": (190, 151, 44), "J": (80, 80, 90),
                    "G": (156, 211, 42), "H": (82, 115, 26)}
    # (first foot row, columns of the back foot, columns of the front foot) in each one's art,
    # and the column where the walking frame's art starts in Bingo's.
    BINGO_FEET, BIG_BINGO_FEET = (19, range(0, 7), range(7, 13)), (29, range(0, 10), range(10, 18))
    BLUEY_FEET, BIG_BLUEY_FEET = (22, range(0, 8), range(8, 16)), (36, range(0, 10), range(10, 22))
    WALKER_X, BIG_WALKER_X = 15, 19

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        big = height >= 64
        self.bingo = self.BIG_BINGO_ART if big else self.BINGO_ART
        self.walker = self.BIG_WALKER_ART if big else self.WALKER_ART
        self.bluey = self.BIG_BLUEY_ART if big else self.BLUEY_ART
        self.bingo_feet = self.BIG_BINGO_FEET if big else self.BINGO_FEET
        self.bluey_feet = self.BIG_BLUEY_FEET if big else self.BLUEY_FEET
        self.walker_x = self.BIG_WALKER_X if big else self.WALKER_X
        self.sleeve = self.BIG_SLEEVE if big else self.SLEEVE
        self.step, self.lift_f, self.step_f = self.BIG_SHUFFLE if big else self.SHUFFLE
        self.bluey_dx = self.walker_x + len(self.walker[0]) + (self.BIG_GAP if big else self.GAP)
        self.bluey_w = len(self.bluey[0])
        self.pair_w = self.bluey_dx + self.bluey_w
        steps = -(-(width + self.pair_w) // self.step)  # until Bingo is off the right edge
        self.duration = steps * self.step_f / FPS

    def _frame(self, t):
        """(steps taken, frame within this step) at t."""
        return divmod(int(t * FPS + 1e-6), self.step_f)

    def bingo_x(self, t):
        """Bingo's left edge: still while the frame moves, then a pixel at a time up to it."""
        k, f = self._frame(t)
        walk_f = self.step_f - self.lift_f
        return -self.pair_w + self.step * k + max(0, f - self.lift_f) * self.step // walk_f

    def walker_ahead(self, t):
        """(pixels the frame is ahead of its place by Bingo, rows it's lifted)."""
        k, f = self._frame(t)
        moved = min(f, self.lift_f) * self.step // self.lift_f
        bingo = max(0, f - self.lift_f) * self.step // (self.step_f - self.lift_f)
        return moved - bingo, 1 if f < self.lift_f else 0

    def bluey_x(self, t):
        """Bluey's left edge: steady, a pixel every few frames, at the pair's pace."""
        n = int(t * FPS + 1e-6)
        return -self.pair_w + self.bluey_dx + n * self.step // self.step_f

    def bingo_pose(self, t):
        """Her pose while she shuffles up to the frame (drawing.WALK_CYCLE); None standing."""
        k, f = self._frame(t)
        if f < self.lift_f:
            return None
        return 4 * k + (f - self.lift_f) * 4 // (self.step_f - self.lift_f)

    def bluey_pose(self, t):
        return int(t * FPS + 1e-6) // self.BLUEY_POSE_F + 1  # out of step with Bingo

    def front(self, t):
        """The reveal's edge: the middle of Bluey, who leads. Dark ahead of it."""
        return self.bluey_x(t) + self.bluey_w // 2

    def _bingo_pixels(self, x, y, pose, ahead):
        """Bingo, her hand moved `ahead` with the frame and her sleeve stretched after it."""
        col, rows = self.sleeve
        pixels = []
        for (px, py), rgb in walking_pixels(self.bingo, x, y, self.BINGO_COLORS, self.bingo_feet, pose):
            c, r = px - x, py - y
            if r in rows and c >= col:
                if c == col:
                    pixels += [((px + i, py), rgb) for i in range(1, ahead + 1)]
                else:
                    px += ahead
            pixels.append(((px, py), rgb))
        return pixels

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        _blackout(canvas, self.front(t), self.width, self.height)
        x, pose = self.bingo_x(t), self.bingo_pose(t)
        ahead, lifted = self.walker_ahead(t)
        bob = 0 if pose is None else pose % 2
        pixels = self._bingo_pixels(x, self.height - len(self.bingo) - bob, pose, ahead)
        pixels += art_pixels(self.walker, x + self.walker_x + ahead, self.height - len(self.walker) - lifted,
                             self.BINGO_COLORS)
        pose = self.bluey_pose(t)
        pixels += walking_pixels(self.bluey, self.bluey_x(t), self.height - len(self.bluey) - pose % 2,
                                 self.BLUEY_COLORS, self.bluey_feet, pose)
        paint(canvas, pixels, self.width, self.height)
        return True


class KeepyUppyReveal:
    """
    Bluey and Bingo playing Keepy Uppy. A red balloon floats in from the left with the pair
    running after it, uncovering the new ride behind them. They stop, Bluey turns to face
    Bingo, and they take turns hopping up to bat the balloon back and forth over their heads,
    never letting it touch the ground. Bingo's last hit sends it sailing off to the right;
    Bluey turns and they both run off after it.
    """

    SCALE = 1  # each board has its own art, both 1x
    STEP = 2  # pixels a frame running, steady (see Chip 'n' Dale)
    POSE_S = 2 / FPS  # each pose of the run (drawing.WALK_CYCLE)
    TURN_S = 0.2  # Bluey turns round, then the first hit
    HITS = ("bluey", "bingo", "bluey", "bingo")  # who bats it, in turn; the last sends it away
    HIT_S = 0.9  # from one hit to the next: up fast, drifting down slowly
    HOP_S = 0.2  # the hitter's hop
    CHASE_S = 0.25  # after the last hit, they turn and run
    FLY_S = 1.4  # the last hit, sailing off the right edge

    # Bingo from the user's grid pattern of her waving, Bluey from their photo of beads (arms
    # out); 64x64 gets Bluey bead for bead and Bingo shrunk to fit beside her, and 64x32 both
    # redrawn about 20 rows tall to leave the balloon room. Both drawn facing right, the way
    # they run (Bingo mirrored from her pattern); Bluey turns to face Bingo for the game.
    # Bingo: '.' empty, B outline, O orange, T tan, C cream, E cream edge, W white, P pupils
    # and eye rims, N nose, K feet band. Bluey: N navy, O orange, L light blue, M blue, W white,
    # P pupils, nose and mouth, R tongue. The balloon: R red, H shine, D shade, K knot, S string.
    BINGO_ART = [
        ".......B....B...",
        ".....BOB..BOB...",
        "....BOCB.BOCB...",
        "...BOOOBBOOOB...",
        "...BOWWWCCWWB...",
        "...BOWPWCCPWB...",
        "...BOWPWCCPWB.E.",
        "E.EBOWWWCCCNBECE",
        "CECBOOCCCCCNTTCE",
        "ECCTOOCCWWCBTTE.",
        ".EETTTTCCCTTB...",
        "...BTTTTTTTTB...",
        "...BOTTTTTTTB...",
        "...BOTCCCCCCB...",
        "...BTTCCCCCCB...",
        "...BTTCCCCCCB...",
        "ECTTBKKBKKBE....",
        "ECCTTBTTBTTB....",
        ".ECB.ECCECCE....",
        "..E..EEEEEEEE...",
    ]
    BIG_BINGO_ART = [
        "..........B.....B.....",
        ".........BB....BB.....",
        "........BOB...BOB.....",
        ".......BOCB..BOCB.....",
        "......BOCCB..BCCB.....",
        ".....BOOOOBBBOOOB.....",
        "....BOOPPPPCPPPOB.....",
        "....BOPWWWPCPWWWP.....",
        "....BOPWWWPCPWPWP.....",
        "....BOPWPWPCPWPWP..EE.",
        "....BOPWPWPCPWPWP.ECCE",
        "....BOPWWWPCCPPPBECCCE",
        ".E.EBOPWWWPCCCNNBTCCE.",
        "ECECBOOPPPCCCCNNBTTE..",
        "ECCCTOOOCCCCCCCBTTE...",
        ".ECCTTOOCCWWWCBTTB....",
        "..EETTTTTCCCCCTTB.....",
        "....BTTTTTTTTTTTB.....",
        "....BOTTTTTTTTTTB.....",
        "....BOTTCCCCCCCCB.....",
        "....BOTTCCCCCCCCB.....",
        "....BTTTCCCCCCCCB.....",
        "....BTTTCCCCCCCCB.....",
        "EEBOTBTTCCCCCCCE......",
        "ECCTTTBKKKBKKKB.......",
        "ECCCTTBTTTBTTTB.......",
        ".ECCB.ECCCECCCE.......",
        "..EE..ECCCECCCCE......",
        "......EEEE.EEEEE......",
    ]
    BLUEY_ART = [
        ".........N...N......",
        "........NN..NN......",
        ".......NON.NON......",
        ".......NLNNNLN......",
        ".......NWWLWWWN.....",
        ".......NWPLWPWNPP...",
        ".......NWPLOOOPPP...",
        ".......NMLOOOOOO....",
        "...L..NMMOWWWOO..L..",
        "..LLL.LMMORPPO..LLL.",
        "..LLMMMMMMOOOMMMLLL.",
        "...LLLMMMMMMMMMLL...",
        "......MMLLLLLLM.....",
        "......NMLLLLLLM.....",
        "......NMLLLLLLM.....",
        ".NNMMMNMLLLLLLM.....",
        "NNNNMMMMLLLLLM......",
        ".NNN...MMM.MMM......",
        ".......MM...MM......",
        "......MMM...MMM.....",
        ".....LLMM...MMLL....",
        ".....LLL.....LLL....",
    ]
    BIG_BLUEY_ART = [
        "..............N.....N.......",
        ".............NN....NN.......",
        "............NNN...NNN.......",
        "...........NNON..NNON.......",
        "..........NNOON.NNOON.......",
        "..........NNLLN.NLLLN.......",
        "..........NNNLLLLLLNN.......",
        "..........NNLWWWLWWWN.......",
        "..........NNWWWWLWWWN.......",
        "..........NNWWPPLWPWNPP.....",
        "..........NNWWPPLOOOPPP.....",
        "..........NNLLLLOOOOOOO.....",
        "..........NNMMLOOOOOOOO.....",
        "......L...NMMMMOWWWWOO...L..",
        "....LLLL.LMMMMMORRPPO..LLLL.",
        "....LLLMMMMMMMMOOOOOMMMLLLL.",
        ".....LLLMMMMMMMMMMMMMMMLLL..",
        "........LMMMMMLLLLLLMM......",
        ".........MMMLLLLLLLLM.......",
        ".........NMMLLLLLLLLM.......",
        ".........NMMLLLLLLLLM.......",
        "...MM....NMMLLLLLLLLM.......",
        ".NNNMMMMMNMMLLLLLLLLM.......",
        "NNNNMMMMMMMMLLLLLLLM........",
        "NNNNNMMM..MMLLLLLLLM........",
        ".NNNNMM...MMMM..MMMM........",
        "..........MMM....MMM........",
        ".........MMMM....MMMM.......",
        ".........MMM......MMM.......",
        ".......LLMMM......MMMLL.....",
        ".......LLLLL......LLLLL.....",
        "........LLL........LLL......",
    ]
    BALLOON_ART = [
        "..RRRR..",
        ".RHRRRR.",
        "RHHRRRRD",
        "RHRRRRRD",
        "RRRRRRRD",
        "RRRRRRDD",
        ".RRRRRD.",
        "..RRDD..",
        "...KK...",
        "....S...",
        "...S....",
    ]
    BIG_BALLOON_ART = [
        ".....RRRR.....",
        "...RRRRRRRR...",
        "..RRHHRRRRRR..",
        ".RRHHRRRRRRRR.",
        ".RHHRRRRRRRRD.",
        "RRHRRRRRRRRRRD",
        "RRRRRRRRRRRRRD",
        "RRRRRRRRRRRRRD",
        "RRRRRRRRRRRRDD",
        ".RRRRRRRRRRRD.",
        ".RRRRRRRRRRDD.",
        "..RRRRRRRRDD..",
        "...RRRRRRDD...",
        ".....RRDD.....",
        "......KK......",
        ".......S......",
        "......S.......",
        ".......S......",
    ]
    BINGO_COLORS = {"B": (150, 75, 40), "O": (246, 130, 36), "T": (252, 175, 110),
                    "C": (255, 245, 200), "E": (215, 205, 150), "W": (250, 250, 250), "P": (55, 50, 50),
                    "N": (110, 60, 45), "K": (196, 136, 79)}
    BLUEY_COLORS = {"N": (27, 59, 120), "O": (240, 160, 40), "L": (150, 215, 245), "M": (60, 165, 215),
                    "W": (250, 250, 250), "P": (60, 60, 70), "R": (220, 40, 60)}
    BALLOON_COLORS = {"R": (230, 30, 40), "H": (255, 150, 150), "D": (150, 15, 25), "K": (150, 15, 25),
                      "S": (180, 180, 180)}
    # (first foot row, columns of the back foot, columns of the front foot), facing right.
    BINGO_FEET, BIG_BINGO_FEET = (16, range(4, 8), range(8, 13)), (24, range(6, 10), range(10, 16))
    BLUEY_FEET, BIG_BLUEY_FEET = (17, range(4, 11), range(11, 20)), (26, range(0, 15), range(15, 28))
    # The hand each bats with, (column, row) of its top as they face each other: Bingo's right
    # hand in her art, and the near hand of Bluey's turned round (her right, mirrored).
    BINGO_HAND, BIG_BINGO_HAND = (14, 6), (19, 9)
    BLUEY_HAND, BIG_BLUEY_HAND = (2, 8), (2, 13)
    MARGIN, BIG_MARGIN = 6, 0  # columns from each edge to them while they play

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        big = height >= 64
        self.bingo = self.BIG_BINGO_ART if big else self.BINGO_ART
        self.bluey = self.BIG_BLUEY_ART if big else self.BLUEY_ART
        self.balloon = self.BIG_BALLOON_ART if big else self.BALLOON_ART
        self.bingo_feet = self.BIG_BINGO_FEET if big else self.BINGO_FEET
        self.bluey_feet = self.BIG_BLUEY_FEET if big else self.BLUEY_FEET
        self.bingo_w, self.bluey_w = len(self.bingo[0]), len(self.bluey[0])
        self.balloon_w = len(self.balloon[0])
        self.balloon_body = sum(1 for row in self.balloon if "R" in row)  # rows above the knot
        margin = self.BIG_MARGIN if big else self.MARGIN
        self.bingo_stop, self.bluey_stop = margin, width - margin - self.bluey_w
        # Both run the same even distance in, Bluey starting just off the left edge.
        far = self.bluey_stop + self.bluey_w
        self.distance = far + far % 2
        self.run_s = self.distance / (self.STEP * FPS)
        self.contacts = [self.run_s + self.TURN_S + i * self.HIT_S for i in range(len(self.HITS))]
        self.leave_at = self.contacts[-1] + self.CHASE_S
        off = width - self.bingo_stop  # Bingo, last, off the right edge
        self.duration = max(self.leave_at + (off + off % 2) / (self.STEP * FPS),
                            self.contacts[-1] + self.FLY_S)
        bingo_hand = self.BIG_BINGO_HAND if big else self.BINGO_HAND
        bluey_hand = self.BIG_BLUEY_HAND if big else self.BLUEY_HAND
        # Where the balloon's left edge and top sit as each one bats it, the balloon's body
        # resting on the hand, a little inside it.
        self.spot = {
            "bingo": (self.bingo_stop + bingo_hand[0] - self.balloon_w // 2,
                      height - len(self.bingo) + bingo_hand[1] - self.balloon_body),
            "bluey": (self.bluey_stop + bluey_hand[0] - self.balloon_w // 2,
                      height - len(self.bluey) + bluey_hand[1] - self.balloon_body),
        }
        self.top = 0 if not big else 4  # the balloon's highest, between hits
        self.arts = {
            "bingo": {1: self.bingo, -1: [row[::-1] for row in self.bingo]},
            "bluey": {1: self.bluey, -1: [row[::-1] for row in self.bluey]},
        }

    def _run(self, stop, t):
        step = self.STEP * FPS
        if t < self.run_s:
            return stop - self.distance + step * t
        if t < self.leave_at:
            return stop
        return stop + step * (t - self.leave_at)

    def bingo_x(self, t):
        return int(round(self._run(self.bingo_stop, t)))

    def bluey_x(self, t):
        return int(round(self._run(self.bluey_stop, t)))

    def bluey_facing(self, t):
        """1 facing right, the way they run; -1 facing Bingo while they play."""
        return -1 if self.run_s + self.TURN_S / 2 <= t < self.leave_at else 1

    def running(self, t):
        return t < self.run_s or t >= self.leave_at

    def pose(self, t, offset=0):
        return int(t / self.POSE_S) + offset if self.running(t) else None

    def lift(self, t, who):
        """Rows each is off the ground: a bob while running, a hop as they bat the balloon."""
        pose = self.pose(t, 1 if who == "bluey" else 0)
        if pose is not None:
            return pose % 2
        for at, hitter in zip(self.contacts, self.HITS):
            if hitter == who and at - self.HOP_S / 2 <= t < at + self.HOP_S / 2:
                return 2 if abs(t - at) < self.HOP_S / 4 else 1
        return 0

    def balloon_at(self, t):
        """(left, top) of the balloon at t."""
        first = self.contacts[0]
        if t < first:
            # Floating in over the pair, just behind Bluey, and drifting down onto her hand.
            x, y = self.spot["bluey"]
            s = min(1.0, t / first)
            return x - (self.bluey_stop - self.bluey_x(t)), round(self.top + (y - self.top) * s * s)
        for i, (at, hitter) in enumerate(zip(self.contacts, self.HITS)):
            nxt = self.contacts[i + 1] if i + 1 < len(self.contacts) else None
            if nxt is not None and at <= t < nxt:
                (x0, y0), (x1, y1) = self.spot[hitter], self.spot[self.HITS[i + 1]]
                s = (t - at) / self.HIT_S
                x = x0 + (x1 - x0) * smooth(s)
                y = y0 + (y1 - y0) * s - (min(y0, y1) - self.top) * math.sin(math.pi * s ** 0.6)
                return int(round(x)), int(round(y))
        # The last hit: up and away off the right edge.
        x0, y0 = self.spot[self.HITS[-1]]
        s = min(1.0, (t - self.contacts[-1]) / self.FLY_S)
        x = x0 + (self.width - x0) * s * s + self.balloon_w * s
        y = y0 + (self.top - y0) * math.sin(math.pi / 2 * min(1.0, s * 2))
        return int(round(x)), int(round(y))

    def front(self, t):
        """The reveal's edge: the middle of Bluey running in, then on to the right edge."""
        mid = self.bluey_x(min(t, self.run_s)) + self.bluey_w // 2
        return mid + max(0, int((t - self.run_s) * self.STEP * FPS))

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        _blackout(canvas, self.front(t), self.width, self.height)
        pixels = []
        for who, x, facing, offset in (("bingo", self.bingo_x(t), 1, 0),
                                       ("bluey", self.bluey_x(t), self.bluey_facing(t), 1)):
            art = self.arts[who][facing]
            top, behind, ahead = self.bingo_feet if who == "bingo" else self.bluey_feet
            if facing < 0:
                w = len(art[0])
                behind, ahead = {w - 1 - c for c in behind}, {w - 1 - c for c in ahead}
            colors = self.BINGO_COLORS if who == "bingo" else self.BLUEY_COLORS
            y = self.height - len(art) - self.lift(t, who)
            pixels += walking_pixels(art, x, y, colors, (top, behind, ahead), self.pose(t, offset), facing)
        bx, by = self.balloon_at(t)
        pixels += art_pixels(self.balloon, bx, by, self.BALLOON_COLORS)
        paint(canvas, pixels, self.width, self.height)
        return True
