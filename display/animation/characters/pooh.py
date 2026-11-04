import math
import random

from display.animation.drawing import EDGE_RGB, art_pixels, paint
from display.animation.mechanics import CapturesScreens
from display.motion import progress, smooth


class PoohReveal(CapturesScreens):
    """
    Pooh floats up from the bottom of the board on his red balloon, hangs there a moment, and
    drifts up and off the top. The old ride stays above him and the new one is uncovered a few
    rows below his feet as he rises, behind a gold edge. The balloon sways side to side and Pooh swings a
    beat behind it, the string bending between them. On 64x32 he's taller than the board, so the
    balloon passes first and he hovers with his feet on the bottom edge.
    """

    wants_prev = True
    SCALE = 1
    RISE_SPEED = 30.0  # rows a second, on average, coming up and going off (time by distance)
    # Both ease in and out (smooth), so a balloon never goes faster than 1.5x that.
    HOVER_S = 1.0
    SWAY = 2  # columns the balloon sways each way
    SWAY_S = 2.4  # one sway, there and back
    LAG_S = 0.35  # how far Pooh's swing trails the balloon's
    GAP = 4  # rows between his feet and the edge, so the line isn't right on him

    # From the user's grid pattern (docs/references/Pooh and Balloon.jpg), copied cell for cell,
    # 1x on both boards. Split by row: the balloon (BALLOON_ROWS), the string between them,
    # drawn as a line so it bends with the swing, and Pooh, holding it, from POOH_ROW down.
    # '.' empty, K outline, R red (balloon and shirt), Y yellow (Pooh and the balloon's shine),
    # S string grey (also the strands of his hair).
    ART = [
        ".........KKKK.......",
        ".......KKRRRRKK.....",
        "......KRRRRRRRRK....",
        ".....KRRRYYRRRRRK...",
        ".....KRRYYYYRRRRRK..",
        "....KRRYYYYYYRRRRK..",
        "....KRRYYYYYYRRRRRK.",
        "....KRRYYYYYYRRRRRK.",
        "....KRRRYYYYRRRRRRK.",
        "....KRRRYYYRRRRRRRK.",
        ".....KRRYYYRRRRRRK..",
        ".....KRRRRRRRRRRRK..",
        "......KRRRRRRRRRK...",
        ".......KRRRRRRRK....",
        "........KRRRRRK.....",
        ".........KRRRK......",
        "..........KKK.......",
        ".........KRRK.......",
        "..........KK........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "...........S........",
        "..........KKK.......",
        "........KKYYYK......",
        ".......KYYKYK.......",
        ".......KYYYKYK.S....",
        ".......KYKKYYKS.S...",
        ".......KYYYYYK......",
        ".......KYYKYYK......",
        ".......KYYKYYYK.KK..",
        "......KYYYKKYKKKYYK.",
        "......KYYKYYKYYYKYK.",
        ".....KRKYKYYKYYYYK..",
        ".....KRKYKYYYYYYYK..",
        "....KRRRKYKKYYYYYYK.",
        "....KRRRRKKYYYKKYYK.",
        "...KRRRRRRKYYYYYYK..",
        "..KRRRRKRKYYYYYKYYK.",
        "..KRRRRKRKYYYYYYYYKK",
        "..KRRRRRKRKYYYYYYYKK",
        ".KYKRRRRRRKYYYKYYK..",
        ".KYYKRRRRKRKKKKKK...",
        "KYYYYKRRKRRRRK......",
        "KYYYYYKRRRRRRK......",
        "KYYYYYYKKKKKKK......",
        "KYYYYYYYYYYYK.......",
        "KYKKKKYYYYYYKK.KK...",
        "KYYYYYKYYYYYKYKYYK..",
        ".KYYKYYKYYYKYYYYYK..",
        ".KYYYKKKYKKYYYYYK...",
        "..KYYYYKK..KYYYK....",
        "..KYYYYK....KKK.....",
        "...KYYYYKK..........",
        "....KYYYYYK.........",
        ".....KYYYK..........",
        "......KKK...........",
    ]
    BALLOON_ROWS = 19
    POOH_ROW = 30
    STRING_COL = 11
    colors = {"K": (40, 24, 14), "R": (210, 24, 32), "Y": (255, 184, 28), "S": (170, 170, 170)}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.art_w, self.art_h = len(self.ART[0]), len(self.ART)
        self.x0 = self.rng.randint(self.SWAY, width - self.art_w - self.SWAY)
        self.phase = self.rng.random() * self.SWAY_S
        # His top row: from just below the board, up to where his feet rest on the bottom edge
        # (all of him on 64x64), then up until the edge GAP rows under his feet is off the top.
        self.start_y, self.hover_y, self.end_y = height, height - self.art_h, -self.art_h - self.GAP
        self.rise_s = (self.start_y - self.hover_y) / self.RISE_SPEED
        self.leave_s = (self.hover_y - self.end_y) / self.RISE_SPEED
        self.leave_at = self.rise_s + self.HOVER_S
        self.duration = self.leave_at + self.leave_s

    def top_y(self, t):
        """His top row at t: easing up into the hover, still, then easing off it and away."""
        if t < self.leave_at:
            return self.start_y - (self.start_y - self.hover_y) * smooth(progress(t, 0, self.rise_s))
        return self.hover_y - (self.hover_y - self.end_y) * smooth(progress(t, self.leave_at, self.duration))

    def sway(self, t):
        """(balloon, Pooh) columns off centre: the same swing, Pooh's a beat behind."""
        def at(s):
            return round(self.SWAY * math.sin(2 * math.pi * (s + self.phase) / self.SWAY_S))
        return at(t), at(t - self.LAG_S)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        w, h = self.width, self.height
        top = int(round(self.top_y(t)))
        seam = top + self.art_h + self.GAP  # the edge: the old ride above it, the new below
        frame = {}
        for y in range(max(0, min(h, seam))):
            for x in range(w):
                frame[(x, y)] = self.prev_px.get((x, y), (0, 0, 0))
        if 0 <= seam < h:
            for x in range(w):
                frame[(x, seam)] = EDGE_RGB
        balloon, pooh = self.sway(t)
        frame.update(dict(art_pixels(self.ART[:self.BALLOON_ROWS], self.x0 + balloon, top, self.colors)))
        string = self.POOH_ROW - self.BALLOON_ROWS
        for i in range(string):
            shift = balloon + (pooh - balloon) * (i + 1) / (string + 1)
            frame[(self.x0 + self.STRING_COL + round(shift), top + self.BALLOON_ROWS + i)] = self.colors["S"]
        frame.update(dict(art_pixels(self.ART[self.POOH_ROW:], self.x0 + pooh, top + self.POOH_ROW, self.colors)))
        paint(canvas, frame, w, h)
        return True
