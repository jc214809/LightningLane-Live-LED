"""Mike and Sulley for the synced show's friendship mash-up (see show_actors.py)."""
from display.fireworks.actors.base import Actor, stamp
from display.motion import ease_out


class MikeAndSulley(Actor):
    """
    Friendship mash-up, elapsed START_S-END_S (audio 505.5-511, the real show's video 8:36-8:41): Sulley
    and Mike stand side by side over the castle's gate, as they do in the window over it in the real
    show. They pop up out of the gate together (POP_S), blink now and then, Mike waves his raised hand,
    and they sink back down at the end. 64x64: Sulley from docs/references/Sulley.jpg (1x) and Mike from
    Mike_waving.png, shrunk to 27x25 by dropping repeated rows and columns so he stands a head shorter;
    64x32: a small pair redrawn in the same styles. Placed by the clock: everything is a function of
    (elapsed - START_S) s.
    """
    NAME = "Mike and Sulley"
    START_S, END_S = 32.2, 37.7
    ENTERS_S = START_S
    POP_S = 0.35  # up out of the gate, and back down
    GAP = {32: 1, 64: 2}  # LEDs between them
    BLINK_S = 0.15
    SULLEY_BLINKS = (1.4, 3.9)  # seconds into their visit
    MIKE_BLINKS = (2.3, 4.5)
    WAVE = (0.6, 4.6)  # Mike's hand rocks one LED left and right...
    WAVE_S = 0.3  # ...this often

    # Sulley.jpg's chart: C fur, c his belly, P his spots, S his horns and claws, B his fur's darker lines,
    # W white (his eyes, claws), b navy (pupils, nose, mouth), K his eyes' black.
    SULLEY_ART = (
        "......SS...........SS......",
        ".....SS.............SS.....",
        ".....SSS.CCCCCCCCC.SSS.....",
        "......SSCCCCCCCCCCCSS......",
        ".......SCSSSCCCSSSCS.......",
        "........SWbKWCWbKWS........",
        "........CWbbWCWbbWC........",
        ".......CCCWWbbbWWCCC.......",
        ".......CCCCCCbCCCCCC.......",
        ".......CCCCCCCCCCbCC.......",
        "....CPPCCCbWCCCWbCCCPPCP...",
        "...CPPBCCCCbbbbbCCCCBPCC...",
        "..CCPPBCCCCCCCCCCCCCBCCCP..",
        ".CCCCCCBCCCCCCCCCCCBCCCCP..",
        "PPCCCCCCBCCCCCCCCCBCCCCCCC.",
        "PPPCCCCCCBBBBBBBBBCCCCCCCC.",
        "PPCCWWCCCCCCCCCCCCCCWWCCCC.",
        "CCCCCWCCCCCCCCCCCCCPWCCPPP.",
        ".CCCCCCPCCCcccccCCCPCPCCP..",
        "..CCCCPPCCccccccCCCCPPCC...",
        "...PPCPPCcccccccccCCCCC....",
        ".....CCCCcccccccccCCC......",
        "....CCCCCcccccccccCCPCC....",
        "...SCCCCCcccccccccCPPCCS...",
        "......CPCcccccccccCCC......",
        "......CPCcccccccccCCC......",
        "......CBCCcccccccCCBCC.....",
        "......CCBCCcccccCCBCPPP....",
        "......CCCBBBBBBBBBCCPCPS...",
        "......PCCCCPC.CCCCCPPCCCCS.",
        "......PPCCCP...CCCCPCWCCCCC",
        ".....PPCCCCC...PCCCCCC.....",
        "....CCCCCCCC...PCCCCCCC....",
        "...SSCSCCCCC...CCCCCSCSS...",
    )
    SULLEY_COLORS = {
        "C": (18, 183, 243), "c": (169, 250, 250), "P": (179, 80, 242), "S": (126, 132, 134),
        "B": (78, 102, 243), "W": (242, 250, 247), "b": (9, 9, 133), "K": (31, 27, 31),
    }
    SULLEY_SMALL_ART = (
        ".S........S.",
        ".SS.CCCC.SS.",
        "..SCCCCCCS..",
        "..CSSCCSSC..",
        "..CWbCCWbC..",
        "..CCCbbCCC..",
        "..CCbbbbCC..",
        ".PCCCCCCCCP.",
        "PCCCccccCCCP",
        "CPCccccccCPC",
        "WCCccccccCCW",
        ".CPCccccCPC.",
        "..CCBBBBCC..",
        "..CCC..CCC..",
        ".SCSC..CSCS.",
    )
    # Mike_waving.png's chart, shrunk: G green, B its highlight, A its shade, g and Y his outline, W white
    # (his eye, teeth and toes), K black, s his pupil's glint, S his teeth's line, n, N and O his horns,
    # C grey.
    MIKE_ART = (
        ".....nN..gYYYggg.n.....gg..",
        ".....nOggGGBGGGGgO.....Gg..",
        ".....gGGGAAAAGGGGg...YGGg..",
        ".....gGGAWWWWAGGGA...gGGY..",
        "....gGGAWWWWWWAGGA...gGGg..",
        "....gGGAWWKKKWAGGGY...gGg..",
        "....GGAWWKCsKKAGGGg....GGg.",
        "....GGAWWKsKKKAGGGAg...gGg.",
        "...gGGGAWKKKKKAGGGGGGGggGGY",
        "..ggGGGAWWKKKAGGGGGggGGGgGg",
        ".gAgGGGGAAAAAGGGGGGAAggGGGg",
        "gAAgGGBGGBGGGGGGGGGGAg.YgY.",
        "GAgYGGKKKKKKKKKKKGGGGg.....",
        "GgWYGGKWWWWWWWWWKGGGGg.....",
        "GgWYGGKSSSSSSSSSKGGGGY.....",
        "GGYgAGGKKWWWWWWKGGGGg......",
        "gGGGAGGGGKKKKKKGGGGAg......",
        ".YGGYAAGGGGGGBGGGGAY.......",
        "..gggYAAAGGGGGGGGAY........",
        "..gg..gAYYYYYYYYYAg........",
        "......gAAY.......Ag........",
        ".....gGgg........gGY.......",
        "....gggGg........YggY......",
        "....WgWgGg.......GWgWY.....",
        "....YgYgYg.......gYggg.....",
    )
    MIKE_SMALL_ART = (
        "..n.....n...g",
        ".ggGGGGGgg.gG",
        "gGAWWWWAGGggG",
        "gGAWsKWAGGGGg",
        "gGAWKKWAGGGg.",
        "gGGAAAAGGGGg.",
        "gGKKKKKKKGAg.",
        "gGKWWWWWKGAg.",
        "gGKSSSSSKGAg.",
        ".gAKKKKKAAg..",
        "..gAg..gAg...",
        ".gWWg..gWWg..",
    )
    MIKE_COLORS = {
        "G": (180, 205, 101), "g": (80, 96, 25), "A": (125, 150, 43), "Y": (53, 62, 7), "K": (6, 7, 6),
        "W": (248, 249, 244), "S": (199, 203, 214), "O": (178, 149, 109), "B": (206, 227, 138),
        "s": (108, 108, 108), "N": (112, 71, 44), "n": (86, 45, 18), "C": (86, 87, 87),
    }
    # Where each one's eyes close: {row: (from col, to col, the kinds a lid covers)}, and the lid's colour.
    SULLEY_LIDS = {
        32: {4: (3, 9, "Wb")},
        64: {5: (8, 19, "WbK"), 6: (8, 19, "WbK"), 7: (8, 19, "W")},
    }
    MIKE_LIDS = {
        32: {r: (3, 7, "WsK") for r in (2, 3, 4)},
        64: {r: (7, 15, "WKsC") for r in range(3, 10)},
    }
    # Mike's raised hand: the cells at or right of this column, at or above this row.
    MIKE_HAND = {32: (10, 2), 64: (20, 7)}

    def __init__(self, show):
        super().__init__(show)
        h = 64 if self.big else 32
        self.sulley = self.SULLEY_ART if self.big else self.SULLEY_SMALL_ART
        self.mike = self.MIKE_ART if self.big else self.MIKE_SMALL_ART
        self.sulley_lids, self.mike_lids = self.SULLEY_LIDS[h], self.MIKE_LIDS[h]
        self.hand = self.MIKE_HAND[h]
        gap = self.GAP[h]
        self.bottom = show.height - 2  # their feet, just above the board's last row
        self.sulley_x = (show.width - len(self.sulley[0]) - gap - len(self.mike[0])) // 2
        self.mike_x = self.sulley_x + len(self.sulley[0]) + gap

    def local(self, e):
        """Seconds into their visit, or None outside it."""
        return e - self.START_S if self.START_S <= e < self.END_S else None

    def rise(self, t):
        """How far up out of the gate they are: 0 hidden, 1 all the way up."""
        down = t - (self.END_S - self.START_S - self.POP_S)
        return ease_out(min(1.0, t / self.POP_S)) * (1.0 - ease_out(max(0.0, down) / self.POP_S))

    @staticmethod
    def _blinking(t, blinks, length):
        return any(at <= t < at + length for at in blinks)

    @staticmethod
    def _shut(art, lids, lid):
        """The art with its eyes closed: each lid's cells of its kinds turned to the lid's colour."""
        rows = [list(r) for r in art]
        for r, (c0, c1, kinds) in lids.items():
            for c in range(c0, c1):
                if rows[r][c] in kinds:
                    rows[r][c] = lid
        return ["".join(r) for r in rows]

    def mike_now(self, t):
        """Mike's art at t s in: eye shut in a blink, his raised hand rocked over by a column in a wave."""
        art = self._shut(self.mike, self.mike_lids, "G") if self._blinking(t, self.MIKE_BLINKS, self.BLINK_S)             else list(self.mike)
        if self.WAVE[0] <= t < self.WAVE[1] and int((t - self.WAVE[0]) / self.WAVE_S) % 2:
            col, last_row = self.hand
            art = [r[:col] + "." + r[col:] if i <= last_row else r for i, r in enumerate(art)]
        return art

    def sulley_now(self, t):
        if self._blinking(t, self.SULLEY_BLINKS, self.BLINK_S):
            return self._shut(self.sulley, self.sulley_lids, "C")
        return list(self.sulley)

    def draw(self, put, out, active):
        t = self.local(self.elapsed()) if active else None
        if t is None:
            return
        rise = self.rise(t)
        if rise <= 0:
            return
        show = self.show
        for art, colors, left in ((self.sulley_now(t), self.SULLEY_COLORS, self.sulley_x),
                                  (self.mike_now(t), self.MIKE_COLORS, self.mike_x)):
            top = round(self.bottom + 1 - len(art) * rise)
            # Clipped at their feet's line, so they come up out of the gate rather than the board's edge.
            shown = art[:self.bottom + 1 - top]
            stamp(out, shown, colors, left, top, 1, show.width, show.height)
