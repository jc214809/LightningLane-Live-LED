import math

from display.fireworks.actors.base import Actor, stamp


class DumboFlies(Actor):
    """
    You'll Be in My Heart: Dumbo flies left to right across the sky over the ghost castle, flapping his
    ears (both swing up and down from their roots, the near one more, over his hat, which stays still)
    and paddling his legs, one flap every FLAP_S, gliding with a gentle bob (one every BOB_S). His art is docs/references/Flying Dumbo.jpg
    cell for cell (his whole body and tail, which his ride-reveal sprite lacks; the paper cleaned away),
    1x on both boards. He enters off the left edge as his scene starts and is gone off the right by its
    end, swooping in a gentle arc that dips mid-scene in front of the ghost castle's towers.
    """
    NAME = "Dumbo"
    SCENE_S = 14.0  # the crossing's length when there's no cue to read it from
    BOB_S = 1.6  # one glide up and down
    # From Flying Dumbo.jpg by tools/analyze_reference.py: S light and s darker grey skin, K and k
    # outline, A shade, I and i pink ear insides, D his trunk tip's pink, Y and O his hat, R and Y his
    # collar, C the white of his eye and c its blue, B his trunk's dark curl.
    ART = [
        "................OOOO...........................",
        "..............OOYYYYOOOO.......................",
        ".............OYYYYYYYYYYOO.........kkkkBB......",
        "..............OOYYYYYYOOYYO......kkSSSSSSBB....",
        ".......kKkKKK...OYYYOOYYYYYO..kkkSSSSSSBBDD.BB.",
        "....KKksssssskk..OYOYYYYYkkkkkSSSSSSSSk..BB...B",
        "..KkssssKKKKKssKKYOYYYYYSsSSSSkSSSSSSk....BBBB.",
        ".KsssssKiiiiiKkssKkYYYssSssSSSSkSSSSk..........",
        "KssssKKiIIIIDiikkssKKsssSkssSSSSkSkB...........",
        "sssKKiiIIIIIIIIiiKKssssskssssSSkkk...k.........",
        "KKK..KIIIIIIIIIIIiiKKssssskkssSCk...kSk........",
        "......KKIIIIIIIIIIIiisssssKCCSScSk.kSDDk.......",
        "........KKIIIIIIIIIIIisssssCcskkSk..ksDk.......",
        "..........KKKKIIIIIkkssssssssssSk..kssDk.......",
        "..............KKKKKRssssssssssssSkkssKk........",
        "...............KKRYRRsssAsssksssssssK..........",
        ".............KKssRYRRsKsssssiKksssKK...........",
        "............KssssRRYYRskKssssiskkk.............",
        "...........KssssssRRYRRssKKKKKK................",
        "...........KAssssssRRYYRRskRYR.................",
        "..........KAssssssssRRRYYRRYRR.................",
        "..........KAAsssssssssRRRYYRR..................",
        "...........KAsssssssssssRRRK...................",
        "..........KKAssssssKsssKsssK...................",
        ".........KAKKAsssKsKsssKKAK....................",
        ".......KKAK..KsAsKKKAssKAAK....................",
        "........KK..KAAssK.KAAK.KK.....................",
        "...........KKAAAK...KK.........................",
    ]
    COLORS = {
        "S": (177, 174, 172), "s": (138, 144, 149), "A": (111, 117, 121),
        "K": (25, 19, 20), "k": (49, 40, 43), "B": (80, 67, 70),
        "I": (190, 117, 132), "i": (208, 87, 141), "D": (205, 149, 160),
        "Y": (194, 172, 11), "O": (205, 122, 32), "R": (180, 54, 48),
        "C": (200, 198, 198), "c": (12, 145, 175),
    }
    SCALE = 1
    FLAP_S = 0.8  # one flap: up, back through level, down and back
    # Each ear, row by row: (first col, last col) in ART. The near ear spreads back to the left from its
    # root by his cheek (NEAR_ROOT); the far ear sweeps up to the right from behind his hat (FAR_ROOT).
    NEAR = {3: (7, 12), 4: (4, 14), 5: (2, 16), 6: (1, 18), 7: (0, 20), 8: (0, 18), 9: (0, 20), 10: (6, 20),
            11: (8, 21), 12: (10, 20), 13: (14, 18)}
    FAR = {2: (33, 40), 3: (33, 42), 4: (30, 46), 5: (30, 46), 6: (30, 45), 7: (31, 36)}
    NEAR_ROOT, FAR_ROOT = 21, 29
    FAR_SWING = 0.7  # the far ear swings this much of the near one's
    HAT = "YO"  # cells in the ears' rows that are his hat, which doesn't flap
    LEGS_SPLIT = 17  # front legs right of this column, back legs left of it; rows LEGS_FROM down
    LEGS_FROM = 22
    # The flap: (lift as a share of the most, legs step) per frame.
    CYCLE = ((0, 0), (0.6, 1), (1, 1), (0.6, 0), (0, -1), (-0.6, -1), (-0.8, 0), (-0.4, 0))

    def __init__(self, show):
        super().__init__(show)
        self.w, self.h = len(self.ART[0]), len(self.ART)
        self.bob = 2 if self.big else 1
        # How far the near ear's tip rises at the top of a flap; 64x32 has only 4 rows to spare.
        self.lift = 5 if self.big else 3
        self.frames = [self._frame(round(k * self.lift), step) for k, step in self.CYCLE]
        self.high = self.lift  # his top at either edge, leaving room above for a raised ear
        # Mid-scene he dips a fifth of the board lower, in front of the ghost castle (the spire is too
        # high on both boards for him to clear it), always leaving room for the bob.
        self.low = max(self.high, min(round(show.height * 0.2), show.height - self.h - self.bob))

    def _frame(self, lift, step):
        """His art with the ears raised `lift` at the tip (negative lowers them) and the legs stepped.
        lift extra rows sit on top, so a raised ear is never cut off."""
        art = self.ART
        pad = self.lift
        rows = len(art) + pad
        g = [["."] * self.w for _ in range(pad)] + [list(r) for r in art]
        near = {(x, y) for y, (a, b) in self.NEAR.items() for x in range(a, b + 1) if art[y][x] not in "." + self.HAT}
        far = {(x, y) for y, (a, b) in self.FAR.items() for x in range(a, b + 1) if art[y][x] not in "." + self.HAT}
        legs = {(x, y) for y in range(self.LEGS_FROM, len(art)) for x in range(self.w) if art[y][x] != "."}
        for x, y in near | far | legs:
            g[y + pad][x] = "."
        for x, y in legs:  # front legs reach forward as the back ones push back, and the other way
            nx = x + step if x >= self.LEGS_SPLIT else x - step
            g[y + pad][min(self.w - 1, max(0, nx))] = art[y][x]
        # The ears last, so they lie over his hat; each cell rises with its distance from the root.
        for x, y in sorted(near, key=lambda c: -c[0]):
            ny = y + pad - round(lift * (self.NEAR_ROOT - x) / self.NEAR_ROOT)
            if 0 <= ny < rows:
                g[ny][x] = art[y][x]
        span = max(b for _, b in self.FAR.values()) - self.FAR_ROOT
        for x, y in sorted(far, key=lambda c: c[0]):
            ny = y + pad - round(lift * self.FAR_SWING * (x - self.FAR_ROOT) / span)
            if 0 <= ny < rows:
                g[ny][x] = art[y][x]
        return ["".join(r) for r in g]

    def frame(self, e):
        """Which flap frame he's in e seconds in."""
        return int(e / self.FLAP_S * len(self.CYCLE)) % len(self.CYCLE)

    def crossing_s(self):
        cue = self.show.cue
        return cue.end - self.since if cue is not None and self.since is not None else self.SCENE_S

    def top_left(self, e):
        """Where his sprite is e seconds into the scene: off the left edge at 0, off the right at the end."""
        p = min(1.0, max(0.0, e / self.crossing_s()))
        left = -self.w + (self.show.width + self.w) * p
        glide = (e / self.BOB_S) % 1.0
        top = self.high + (self.low - self.high) * math.sin(math.pi * p) - math.cos(glide * 2 * math.pi) * self.bob
        return left, max(0.0, top)

    def draw(self, put, out, active):
        if not active:
            return
        e = self.elapsed()
        left, top = self.top_left(e)
        show = self.show
        # Frames carry `lift` spare rows on top: drawn that much higher, his body stays where top says.
        stamp(out, self.frames[self.frame(e)], self.COLORS, left, top - self.lift, self.SCALE, show.width, show.height)
