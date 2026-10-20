"""Four princesses meet their princes in the synced show's Princess garden (see show_actors.py)."""
import math

from display.animation.characters.jack_sally import JackSallyReveal
from display.fireworks.actors.base import Actor, stamp
from display.motion import ease_out

# The couples, from docs/references/princesses_and_Princes.jpg's chart (each box is its Pattern-mode
# crop), 1x on both boards: K is each one's outline. Charming's and Eric's near-black hair (k, with S
# its shine) is lifted, as Moana's is, or the LEDs show it as off.
# cinderella: princesses_and_Princes.jpg box 860,944,976,1116
CINDERELLA = (
    ".....yyyyyy.....",
    "....yAAAAAAy....",
    "....AYBBBBYA....",
    "....yybbyyyy....",
    "...yAAyyAAAAy...",
    "..yAYYAAYYYYAy..",
    ".CAYYYYYYYYYYAC.",
    ".KYYyyyyYYYyYYK.",
    ".KYCooooyyyoCYK.",
    ".KYCOOOOoooOCYK.",
    ".BCoOOOOOOOOoCB.",
    ".bCOKKOOOOKKOCb.",
    "..bOWEOOOOEWOb..",
    "..DoOEOOOOEOoD..",
    "...KoOOOOOOoK...",
    "...BKKooooKKB...",
    "..bDBOKKKKOBDb..",
    ".KOOBBOooOBBOOK.",
    "KDBbKBBOODBKbBDK",
    "KBbKbBBBBBBbKbBK",
    ".KKbBBbBBbBBbKK.",
    ".KbBBbBBBBbDBbK.",
    "..KKbBbbbbBbKK..",
    "....KKKKKKKK....",
)
CINDERELLA_COLORS = {
    "K": (3, 3, 5), "O": (234, 180, 160), "B": (130, 174, 251), "Y": (245, 218, 78), "b": (77, 138, 250),
    "y": (135, 118, 38), "A": (252, 241, 177), "o": (194, 140, 121), "C": (77, 70, 21), "D": (174, 202, 248),
    "E": (74, 126, 181), "W": (252, 252, 253),
}

# charming: princesses_and_Princes.jpg box 1008,960,1124,1116
CHARMING = (
    ".....kkkkkk.....",
    "...kkSSSSSSkk...",
    "..kSSkkkkkkSSk..",
    "..KkkkkkkkkkkK..",
    ".kSkkkkSSSkkkSk.",
    ".KkkKkkkkkkKkkK.",
    ".KkKoKKKKKKoKkK.",
    ".KkoOooooooOokK.",
    ".KkOOOOOOOOOOkK.",
    ".KkOKKOOOOKKOkK.",
    ".KKOwkOOOOkwOKK.",
    "..KoWkOOOOkOoK..",
    "...KoOOOOOOoK...",
    ".BYYKKooooKKYYB.",
    "BYAAOOKKKKOOAAYB",
    "YAAOWWOOOOWWOAAY",
    "KWOWKAWWWWAKWOWK",
    "KWOKWOAYYAOWKWWK",
    ".KKKRWOOOOWRKKK.",
    "...KRRRRRRRRK...",
    "..KSSkkKKkkSSK..",
    "...KKKK..KKKK...",
)
CHARMING_COLORS = {
    "K": (4, 3, 2), "k": (62, 48, 40), "O": (221, 183, 161), "W": (221, 216, 198), "S": (105, 90, 80),
    "o": (193, 140, 119), "A": (235, 179, 26), "Y": (251, 204, 54), "R": (177, 61, 62), "B": (250, 219, 132),
    "w": (253, 252, 247),
}

# tiana: princesses_and_Princes.jpg box 472,944,588,1116
TIANA = (
    ".....nnnnnn.....",
    "....nkknnkkn....",
    "....kknkknkk....",
    "...nykKAAkKyn...",
    "...kkAKBBkAkk...",
    "...kAYAYYAYAK...",
    "..nYYGGGGGGYBn..",
    "..YGGkkkkkkGGY..",
    "..GkkOOOOOOkkG..",
    "..kOONNNNNNOOk..",
    "..kNNNNNNNNNNk..",
    "..kNKKNNNNKKNk..",
    "..kNWCNNNNCWNk..",
    "..KNOCNNNNCONK..",
    "...KNNNNNNNNK...",
    "....KKNNNNKK....",
    "..KONNKKKKNNOK..",
    ".KBNCBONNOBNNYK.",
    "KYGyKyBOOByKyGYK",
    "KGyKGyGYYGyGKyGK",
    ".KKGYYyyyyGYyKK.",
    ".KYYyyGYyGYyYYK.",
    "..KKYGYyGYyYKK..",
    "....KKKKKKKK....",
)
TIANA_COLORS = {
    "N": (145, 102, 84), "K": (5, 4, 3), "k": (37, 24, 22), "Y": (179, 190, 118), "G": (137, 150, 82),
    "y": (111, 120, 63), "O": (183, 131, 112), "n": (74, 59, 51), "A": (232, 241, 157), "B": (205, 210, 138),
    "C": (127, 70, 43), "W": (254, 250, 247),
}

# naveen: princesses_and_Princes.jpg box 628,1024,720,1116
NAVEEN = (
    "....YY.YY....",
    "...YAAYAAY...",
    "..YAYYAYYAY..",
    ".YCYKKyKKYCY.",
    ".KyYWRyRWYyK.",
    ".KyyARBRAyyK.",
    "..KyyyyyyyK..",
    "...KAyyyAK...",
    "...YBAAABY...",
    ".YYByAAAyBYY.",
    "YBByBAyAByBBY",
    "KyyYByKyBYyyK",
    ".YYYYK.KYYYY.",
)
NAVEEN_COLORS = {
    "Y": (60, 64, 16), "y": (164, 175, 57), "A": (200, 209, 122), "K": (11, 10, 7), "B": (122, 120, 44),
    "R": (135, 67, 45), "W": (251, 252, 244), "C": (183, 196, 80),
}

# ariel: princesses_and_Princes.jpg box 408,656,608,828
ARIEL = (
    "............rrrrrrrr........",
    "...........rAAAAAAAAr.......",
    "..........rARRRRRRRAAr......",
    ".........rARRRRRRRRrrrr.....",
    ".........rARRRRRRRAAAAAr....",
    ".........KRRRRRRRRRRRRRAr...",
    ".........KRRRRrrrRRRRRRRAr..",
    ".........KRRROooorrRRRRRAK..",
    "........rARKOOOOOoorRRRRK...",
    "........KRKoKKOOOOKKrrKK....",
    ".......rARKoWCOOOOCWoK......",
    ".......KARKoICOOOOCIoK......",
    ".......KRRRKoOOOOOOoKAr.....",
    "........KRRKKKooooKKKRArrr..",
    "........KRKIOoKKKKoOIKRAAAr.",
    ".gggg...gKIOPPooooPPOOKRRRAr",
    "g.gBBg.gKIOoPPPOOPPPoOIKRRRK",
    "...gBBgBKOoKPppDDppPKoOKRKK.",
    "....ggBggKKgggoOOogggKKRK...",
    "......gGGkWkGggooggGkRRK....",
    ".......EGGkGGGGggGGGkKK.....",
    "........kGGGGGGGGGGGk.......",
    ".........kkGGGGGGGGk........",
    "..........kkkkkkkkk.........",
)
ARIEL_COLORS = {
    "R": (192, 58, 58), "K": (5, 3, 3), "O": (226, 184, 169), "r": (84, 25, 24), "G": (48, 138, 102),
    "A": (228, 108, 108), "o": (188, 145, 130), "g": (117, 191, 160), "k": (23, 46, 35), "P": (166, 87, 198),
    "B": (61, 169, 126), "C": (47, 153, 172), "p": (130, 63, 162), "W": (250, 252, 249), "D": (75, 51, 79),
    "I": (243, 207, 198), "E": (42, 89, 72),
}

# eric: princesses_and_Princes.jpg box 628,668,744,828
ERIC = (
    "......kkkkkk....",
    "...kkkSSSSSSk...",
    "..kSSSkkkkkkSK..",
    "..KkkkkkkkkkkSk.",
    ".kSkkSkkkkkkkkK.",
    ".KkkSKSSSkkSSSK.",
    ".KkkKoKKKKkkkkSK",
    ".KkKoOooooKKkkkK",
    ".KkoOOOOOOOoKKKK",
    ".KkOKKOOOOKKokK.",
    ".KkOwKOOOOKwOkK.",
    "..KOAbOOOObAOK..",
    "...KoOOOOOOoK...",
    "...KKKooooKKK...",
    "..KwWWKKKKWWwK..",
    ".KwWsWooooWsWwK.",
    "KAOsKsWOOWsKsOAK",
    "KOoKRRsWWsRRKoOK",
    ".KKkBBRRRRBBkKK.",
    "...kSBBBBBBSk...",
    "..kSkkkKKkkkSk..",
    "...KKKK..KKKK...",
)
ERIC_COLORS = {
    "K": (6, 5, 7), "k": (48, 48, 66), "O": (221, 169, 149), "S": (95, 95, 120), "o": (188, 146, 131),
    "W": (202, 209, 221), "B": (51, 90, 113), "s": (157, 169, 186), "R": (179, 59, 61), "w": (236, 238, 243),
    "A": (247, 197, 176), "b": (117, 145, 179),
}

# belle: princesses_and_Princes.jpg box 444,360,572,532
BELLE = (
    ".......NNNNNN.....",
    "......NCCCCCCN....",
    ".....NCooooooCN...",
    "......KooooooK....",
    ".....NNNBBBBNNN...",
    "....NCCCNNNNCCCN..",
    "...NCooCooCoCooCN.",
    "...KooKKoCoCKKoCK.",
    "...KoKDDKKKKDDKoK.",
    "..NCoKOODDDDOOKoCN",
    "..KoKDOOOOOOOODKoK",
    "..KoKOKKOOOOKKOKoK",
    "...KKOWNOOOONWOKK.",
    "....BDONOOOONODA..",
    "....NKDOOOOOODK...",
    "...NooKKDDDDKKE...",
    "..NCKODDKKKKDDOK..",
    ".NCKYBBODDDDOBBYK.",
    "NCKYAAKBBOOBBKAAYK",
    "KoKABKAAYBBYAAKBAK",
    ".KoKKABAAAYAABAKK.",
    "..KKABABABBABABAK.",
    "....KKAABAABAAKK..",
    "......KKKKKKKK....",
)
BELLE_COLORS = {
    "K": (6, 3, 3), "O": (233, 179, 159), "o": (166, 75, 33), "N": (96, 39, 12), "A": (250, 206, 82),
    "B": (244, 183, 6), "C": (203, 95, 46), "D": (197, 143, 121), "W": (255, 252, 250), "Y": (252, 226, 137),
    "E": (176, 120, 101),
}

# beast: princesses_and_Princes.jpg box 592,336,756,532
BEAST = (
    "........AAnnnnAA.......",
    ".......ANnNNAAAAA......",
    ".....NAOOnNNNNnOOAN....",
    "....NONAONnNNnNOANON...",
    ".....KANnNnNNnNNNAK....",
    "...AANKADNnNNnNDAKNAA..",
    "..AOONDDODNNNNDODDNOOA.",
    "...KNDnOOOnnnnOOOnDNK..",
    "....KANnwBnOOnBwnNAK...",
    "....KONNOBnOOnBONNOK...",
    "....KnnNnnAAAAnnNnnK...",
    ".....KnNwnNKKNnwNnK....",
    "....KbKnNwnnnnwNnKbK...",
    "...KbkWKOONNNNOOKWkbK..",
    "...KyBkWAAODDOAAWkByK..",
    "..KbBoBkSsNOONsSkBoBbK.",
    "..KbBBokoosNNsookoBBbK.",
    ".KyBBkBokoSWWSokoBkBByK",
    ".KbokBBCkoSWWSoECBBkEbK",
    ".KWBkBBCkooSSookCBBkBWK",
    "..KSskBCkooooooECBksSK.",
    "..KOnKoCkYoYYoYkCoKnOK.",
    "NNwKKnKoBbYbbYbBoK.KK..",
    "AOAnnNKnCBBbbBBCnK.....",
    ".AnNNKAnNCCKKCCNnAK....",
    "..AAKOnnNNK..KNNnnnK...",
    "....KKKKKK....KKKKKK...",
)
BEAST_COLORS = {
    "N": (102, 58, 39), "K": (5, 3, 3), "n": (134, 81, 56), "A": (60, 32, 19), "O": (167, 113, 89),
    "B": (42, 80, 136), "o": (206, 154, 6), "k": (11, 24, 49), "b": (58, 104, 174), "C": (29, 58, 102),
    "D": (202, 148, 122), "S": (179, 186, 202), "W": (205, 212, 223), "w": (251, 249, 248),
    "Y": (133, 101, 4), "s": (156, 161, 178), "y": (244, 188, 5), "E": (223, 179, 60),
}

ROCK_ART = (
    "....GGGGGGGG....",
    "..GGgGGGGGGgGG..",
    ".GgGGGGGgGGGGgG.",
    "GGGGgGGGGGGGGGGG",
    "gggggggggggggggg",
)
ROCK_COLORS = {"G": (120, 120, 130), "g": (80, 80, 92)}


class PrincessGarden(Actor):
    """
    Princess garden: four couples, one every quarter of the scene (SLOT_S each): Cinderella and Prince
    Charming, Tiana and Naveen (a frog), Ariel and Eric, Belle and the Beast. Each princess glides in
    from the left and her prince from the right, bobbing a row with each step (STRIDE_S), to meet in the
    middle on the bottom row; they lean together a column, Jack and Sally's heart floats up between
    them, and they walk back off their own sides. Naveen hops in, in little arcs (HOP_S each), as the
    frog he is. Ariel, all tail on the sheet, is already sitting on a rock in the middle when her slot
    starts (fading in), and fades out once Eric has walked off. Times are seconds into the couple's slot.
    """
    NAME = "Princess garden couples"
    COUPLES = (
        ("Cinderella", CINDERELLA, CINDERELLA_COLORS, "Prince Charming", CHARMING, CHARMING_COLORS),
        ("Tiana", TIANA, TIANA_COLORS, "Naveen", NAVEEN, NAVEEN_COLORS),
        ("Ariel", ARIEL, ARIEL_COLORS, "Eric", ERIC, ERIC_COLORS),
        ("Belle", BELLE, BELLE_COLORS, "Beast", BEAST, BEAST_COLORS),
    )
    SCENE_S = 31.0  # used only if the show has no cue
    WALK_S = 2.0  # walking in, and off again
    LEAN_S = 0.3
    HEART_S = 2.8  # the heart floating up while they lean together (a couple takes 7.1 s of its 7.25 s slot)
    STRIDE_S = 0.18  # each bob of their walk
    HOP_S = 0.4  # each of the frog's hops
    HOP_UP = 4  # rows each hop lifts him
    FADE_S = 0.4  # Ariel fading in and out
    HEART_RISE = 12
    HEART = JackSallyReveal.HEART_ART
    HEART_RGB = JackSallyReveal.colors["R"]

    def __init__(self, show):
        super().__init__(show)
        self.mid = show.width // 2

    def slot_s(self):
        cue = self.show.cue
        scene = cue.end - self.since if cue is not None and self.since is not None else self.SCENE_S
        return scene / len(self.COUPLES)

    def now(self):
        """(couple index, seconds into its slot), or None past the last."""
        e = self.elapsed()
        slot = self.slot_s()
        i = int(e // slot)
        return (i, e - i * slot) if i < len(self.COUPLES) else None

    def times(self):
        """(met, leaving, gone) seconds into a slot: done walking in, starting off, off the board."""
        met = self.WALK_S + self.LEAN_S
        leaving = met + self.HEART_S
        return met, leaving, leaving + self.WALK_S

    def places(self, i, s):
        """{who: (left, top)} for couple i, s seconds into its slot ('her', 'him', and 'rock' for Ariel)."""
        _, her, _, _, him, _ = self.COUPLES[i]
        w, h = self.show.width, self.show.height
        met, leaving, gone = self.times()
        # Where they stand when they've met: either side of the middle, a column apart, then touching.
        lean = 1 if self.WALK_S <= s < leaving else 0
        out = {}
        if her is ARIEL:
            # Her face is left of her flowing hair: the sprite ends just right of the middle, and her
            # tail (columns 8-20) sits on the rock.
            left = self.mid + 2 - len(her[0])
            out["rock"] = (left + 6, h - len(ROCK_ART))
            out["her"] = (left, h - len(ROCK_ART) - len(her) + 2)
            his_stop = self.mid + 3 - lean
        else:
            her_stop = self.mid - len(her[0]) - 1 + lean
            out["her"] = (self._walk(s, -len(her[0]), her_stop), h - len(her) + self._bob(s, 0))
            his_stop = self.mid + 1 - lean
        his_x = self._walk(s, w, his_stop)
        if him is NAVEEN:
            out["him"] = (his_x, h - len(him) - self._hop(s))
        else:
            out["him"] = (his_x, h - len(him) + self._bob(s, 1))
        return out

    def _walk(self, s, edge, stop):
        """A column: from edge to stop walking in, stop while they meet, back to edge walking off."""
        met, leaving, gone = self.times()
        if s < self.WALK_S:
            return round(edge + (stop - edge) * ease_out(s / self.WALK_S))
        if s < leaving:
            return stop
        k = min(1.0, (s - leaving) / self.WALK_S)
        return round(stop + (edge - stop) * k * k)

    def walking(self, s):
        met, leaving, gone = self.times()
        return s < self.WALK_S or leaving <= s < gone

    def _bob(self, s, phase):
        """Rows dropped mid-stride (0 or 1), out of step with each other; down, so heads stay on."""
        return (int(s / self.STRIDE_S) + phase) % 2 if self.walking(s) else 0

    def _hop(self, s):
        """Rows the frog is off the ground: an arc per hop while he moves."""
        if not self.walking(s):
            return 0
        p = (s / self.HOP_S) % 1.0
        return int(round(self.HOP_UP * math.sin(math.pi * p)))

    def heart(self, i, s):
        """The heart's top-left at s, floating up from between them while they lean together; or None."""
        met, leaving, _ = self.times()
        if not met <= s < leaving:
            return None
        _, her, _, _, him, _ = self.COUPLES[i]
        places = self.places(i, s)
        start = min(places["her"][1], places["him"][1]) + 4
        rise = round(min(self.HEART_RISE, start) * ease_out((s - met) / self.HEART_S))
        return self.mid - len(self.HEART[0]) // 2, start - rise

    def ariel_glow(self, s):
        """0..1: Ariel and her rock fading in as her slot starts, and out after Eric's gone, by its end."""
        _, _, gone = self.times()
        end = min(gone + self.FADE_S, self.slot_s())
        return max(0.0, min(1.0, s / self.FADE_S, (end - s) / self.FADE_S))

    def draw(self, put, out, active):
        if not active:
            return
        now = self.now()
        if now is None:
            return
        i, s = now
        _, her, her_colors, _, him, him_colors = self.COUPLES[i]
        _, _, gone = self.times()
        if her is not ARIEL and s >= gone:
            return
        w, h = self.show.width, self.show.height
        places = self.places(i, s)
        if "rock" in places:
            g = self.ariel_glow(s)
            if g <= 0.05:  # too dim for the LEDs
                return
            dim = {k: tuple(int(c * g) for c in rgb) for k, rgb in ROCK_COLORS.items()}
            stamp(out, ROCK_ART, dim, *places["rock"], 1, w, h)
            dim = {k: tuple(int(c * g) for c in rgb) for k, rgb in her_colors.items()}
            stamp(out, her, dim, *places["her"], 1, w, h)
        else:
            stamp(out, her, her_colors, *places["her"], 1, w, h)
        if s < gone:
            stamp(out, him, him_colors, *places["him"], 1, w, h)
        at = self.heart(i, s)
        if at is not None:
            stamp(out, self.HEART, {"X": self.HEART_RGB}, *at, 1, w, h)
