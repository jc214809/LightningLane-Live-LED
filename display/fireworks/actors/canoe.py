"""Moana's outrigger canoe for the synced show (see show_actors.py)."""
import math

from display.fireworks.actors.base import Actor, stamp


class CanoeSails(Actor):
    """
    How Far I'll Go (climax): Moana's outrigger canoe (ART on 64x32; BIG_ART, after the toy, on 64x64) sails along the water
    line that the Water effect keeps up, bobbing on the waves, with a tan sail carrying a darker swirl
    for the heart of Te Fiti and Moana at the stern. It sails in off the left edge as the castle goes
    dark and crosses once, off the right edge just before the scene ends at 398 s. (Not in the song
    before it: the water isn't up yet there.) A short white wake flickers behind the stern. On 64x64
    Moana herself (MOANA_ART, from the princes sheet) stands at the stern in front of the sail; 64x32's
    small canoe has a three-pixel Moana of its own.
    """
    NAME = "Moana's canoe"
    ART = (
        ".......M.......",
        ".......MS......",
        ".......MSS.....",
        ".......MSDS....",
        ".......MSDDS...",
        ".......MSSDSS..",
        ".H.....MSSSSSS.",
        ".K.FFFFMFFFFF..",
        "BR.o...M...o..B",
        "BBBBBBBBBBBBBBB",
        ".bbbbbbbbbbbbb.",
    )
    COLORS = {
        "M": (95, 60, 25),  # mast
        "S": (215, 175, 115),  # Moana's tan sail...
        "D": (140, 100, 55),  # ...and its darker heart-of-Te-Fiti swirl
        "H": (45, 28, 18),  # her dark hair
        "K": (175, 115, 70),  # her face
        "R": (235, 85, 30),  # her red-orange top
        "F": (115, 72, 35),  # the outrigger float, behind the hull
        "o": (125, 82, 40),  # its struts
        "B": (150, 90, 40),  # the wooden hull
        "b": (90, 50, 20),  # its shaded underside
    }
    # 64x64's canoe, after the toy (docs/references has no chart of it): a peach crab-claw sail with the
    # heart of Te Fiti's red spiral on a jointed bamboo mast and booms, a plain wooden hull, and the yellow
    # outrigger float on its struts. 1x; the 64x32 canoe above is too small for any of it.
    BIG_ART = (
        "...........................mM.......",
        ".........................MSMM.......",
        ".........................MSM........",
        "........................MSSm........",
        ".......................MSSsM........",
        "......................MSSsSM........",
        ".....................MSSsSSm........",
        "....................MSSsSSSM........",
        "...................MSSsSSSSM........",
        "..................MSXXXXSSsm........",
        ".................MSXXSSXXsSM........",
        "................MXSXSXXSXSSM........",
        "...............MSXsSXXXsXSSm........",
        "..............MSSXXSSSsXXSSM........",
        ".............MSSsSXXXXXXSSsM........",
        "............MSSsSSSSXXSSSsSm........",
        "...........MSSsSSSSsSSSSsSSM........",
        "...........MMMMMMMMMMMMMMMMM......H.",
        "..H..DDDDDDDDDDDDDDDDDDDDDDDDDDDDH..",
        "...HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH..",
        "....HHHHHHHHHHHHHHHHHHHHHHHHHHHHH...",
        "......hhhhhhhhhhhhhhhhhhhhhhhhh.....",
        ".........y....y....y................",
        ".........y....y....y................",
        "......YYYYYYYYYYYYYYYYY.............",
        "........YYYYYYYYYYYYY...............",
    )
    BIG_COLORS = {
        "D": (220, 180, 115),  # the deck
        "H": (140, 95, 45),  # the hull
        "M": (150, 105, 50),  # mast and booms
        "S": (240, 175, 145),  # the sail
        "X": (210, 50, 40),  # the red spiral of the heart of Te Fiti
        "Y": (245, 195, 70),  # its yellow float
        "h": (95, 60, 25),  # its shaded underside
        "m": (95, 65, 30),  # the bamboo's joints
        "s": (220, 150, 120),  # its weave
        "y": (200, 150, 60),  # the outrigger's struts
    }
    BIG_DECK = 18  # the deck row Moana stands on
    BIG_HULL = 21  # the hull's underside, on the water
    # Moana from docs/references/princesses_and_Princes.jpg (box 40,972,176,1116), 1x: '.' empty, K and
    # k her hair (the chart's near-black lifted to dark brown, or the LEDs show it as off), r its shine,
    # O skin, R its shade, W her eyes' glints, N brows and lashes, A her red top, b its blue trim,
    # o and B her skirt.
    MOANA_ART = (
        "........KKKKKK.....",
        "......KKrrrrrrKK...",
        ".....KrrKKKKKKrrK..",
        ".....KKOOOOOOOOKK..",
        "....KrOOOOOOOOOOrK.",
        "....kKOOOOOOOOOOKk.",
        "....kKOOOOOOOOOOKk.",
        "....kKOkkOOOOkkOKk.",
        "....kKOWkOOOOkWOKk.",
        "...KKkROKOOOOKORkk.",
        "...KKKkROOOOOORkKk.",
        "...KKKkkkRRRRkkkK..",
        "...KKkOONkkkkNOOk..",
        "...KkOOOONOONOOOOk.",
        "..KkOORkAAbbAAkROOk",
        "..KkORkOAAAAAAOkROk",
        ".KrKkkoOOOOOOOOokk.",
        "KrKKKKKBOORROOBk...",
        "KKkkkkkkBooooBk....",
        "......kOORkkROOk...",
    )
    MOANA_COLORS = {
        "K": (70, 45, 35), "k": (50, 32, 25), "r": (84, 70, 66),
        "O": (202, 131, 107), "R": (163, 100, 81), "W": (246, 252, 246), "N": (97, 54, 21),
        "A": (180, 56, 58), "b": (67, 134, 190), "o": (211, 192, 155), "B": (237, 208, 181),
    }
    MOANA_LEFT = -2  # her left edge against the canoe's: she stands at the stern, in front of the sail
    # (start, end) seconds into its scene of each edge-to-edge crossing: once, across the 28 s climax.
    PASSES = ((0.0, 27.5),)
    BOB_S = 1.8  # one bob on the waves
    WAKE_RGB = (230, 240, 255)

    def __init__(self, show):
        super().__init__(show)
        # 64x64 sails the toy's canoe with Moana aboard; 64x32 the small one with its tiny figure.
        self.moana = self.big
        self.art, self.colors = (self.BIG_ART, self.BIG_COLORS) if self.big else (self.ART, self.COLORS)
        self.scale = 1
        self.w, self.h = len(self.art[0]), len(self.art)
        self.hull = self.BIG_HULL if self.big else len(self.ART) - 1  # its row that rides on the water
        # Water's full surface (show_effects.Water): it covers the castle's lower 40%.
        self.water = show.castle_y + show.castle_h * 0.6
        self.bob = 2.0 if self.big else 1.0

    def top_left(self, e):
        """The canoe's top-left e seconds in, or None between and after its crossings."""
        for start, end in self.PASSES:
            if start <= e < end:
                k = (e - start) / (end - start)
                left = -self.w + (self.show.width + self.w) * k
                # The hull's underside rides on the surface, the bob lifting and dipping it.
                top = self.water - self.hull + self.bob * math.sin(2 * math.pi * e / self.BOB_S)
                return left, top
        return None

    def draw(self, put, out, active):
        if not active:
            return
        show = self.show
        e = self.elapsed()
        at = self.top_left(e)
        if at is None:
            return
        left, top = math.floor(at[0] + 0.5), math.floor(at[1] + 0.5)
        # Wake: a few white specks trailing the stern at the waterline, flickering by the clock.
        wy = top + self.hull
        for i in range(3):
            f = (0.55 + 0.45 * math.sin(e * 6 + i * 2.1)) * (1 - i * 0.25)
            x = left - 1 - i * 2 * self.scale
            for dx in range(self.scale):
                if 0 <= x + dx < show.width and 0 <= wy < show.height:
                    out[(x + dx, wy)] = tuple(int(c * f) for c in self.WAKE_RGB)
        stamp(out, self.art, self.colors, left, top, 1, show.width, show.height)
        if self.moana:
            feet = top + self.BIG_DECK
            stamp(out, self.MOANA_ART, self.MOANA_COLORS, left + self.MOANA_LEFT, feet - len(self.MOANA_ART) + 1, 1,
                  show.width, show.height)
