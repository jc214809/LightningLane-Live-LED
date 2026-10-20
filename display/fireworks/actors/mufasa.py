"""Mufasa's face for the synced show's Embers (see show_actors.py)."""
import math

from display.fireworks.actors.base import Actor


def _halved(art, rank):
    """art at half size: each 2x2 block becomes its highest-ranked cell, so a feature line, eye or nose
    falling anywhere in the block survives the shrink."""
    h, w = len(art) // 2, len(art[0]) // 2
    return ["".join(max((art[2 * y + j][2 * x + i] for j in (0, 1) for i in (0, 1)), key=rank.index)
                    for x in range(w)) for y in range(h)]


class MufasaInTheStars(Actor):
    """
    Embers ("Remember who you are"): Mufasa's face fills the board's top-right corner, three-quarters
    left so he looks in toward the castle and the middle of the board, the way he looks down from the
    clouds in the film. His art is docs/references/Mufasa in the clouds film still.png traced at 44x44 (trimmed to 42x43)
    (its dark lines kept as his features, its colours made Mufasa's: red mane, gold face, cream muzzle)
    and cleaned by hand, his outline all mane; 64x32 gets it halved (_halved). A while into the scene (APPEAR_S) he fades in
    (FADE_IN_S), breathes with a slow swell (BREATH_S), and fades away as he says his last line, as in the
    film: from its start ("Remember who you are... Remember", found in his mouth track; its echo is part of
    it) to FADE_TAIL_S after his last word, slowly at first, so he's still there to mouth the echo.
    Without a track, he fades over the scene's last FADE_OUT_S.
    The bottom of his mane (FADE_ROWS) melts into the sky, as his neck melts into the clouds. He mouths
    his lines to the score's track (MOUTHS: his smile as drawn when closed, then half and open).
    """
    NAME = "Mufasa"
    APPEAR_S = 6.0
    ENTERS_S = APPEAR_S
    FADE_IN_S = 4.0
    FADE_OUT_S = 6.0
    BREATH_S = 5.0
    BREATH = 0.08  # how far the swell dips below full
    PEAK = 0.9  # his brightest, as a share of his colours
    SCENE_S = 40.0  # used only if the show has no cue
    FADE_ROWS = 0.25  # the bottom quarter of him fades to nothing
    # '.' empty, M mane, m its darker outline (his border is all mane), h its sunlit side, F face,
    # C muzzle, L lines (brows, lids, smile), N nose, E his eyes' amber, P their pupils.
    ART = [
        "...........mmmmmmmm.......................",
        ".........mmMMMMMMMMmm.....................",
        "........mMMMMMMMMMMMMm....................",
        ".......mMMMMMMMMMMMMMMmmmm................",
        "......mMMMMMMMMMMMMMMMMMMMm...............",
        ".....mMMMMMMMMMMMMMMMMMMMMMmm.............",
        ".....mMMMMMMMMMMMMMMMMMMMMMMMm............",
        ".....mMMMMMMMMMMMMMMMMMMMMMMMMmm..........",
        "....mMMMMMMMMMMMMMMMMMMMMMMMMMMMmm........",
        "....mMMMMMMMMMMMMFFMMMMMMMMMMMMMMm........",
        "....mMMMMMMMMMMFFFFFFFMMMMMMMMMMMm........",
        "....mMMMMMFFMFFFFFFFFFFMMMMMMMMMMMmmm.....",
        ".....mMMMFFFFFFFFFFFFFFFMMMMMMMMhMMMm.....",
        ".....mMMFFFFFFFFFFFFFFFFMMMMMMMMMhMMMm....",
        ".....mMMFFFFFFFLLLLLLFFFFMMMMMMMhhhMMm....",
        ".....mMFFFFFFFFLLLLLLFFFFFMMMMMMhhhMMm....",
        ".....mLLLLLLFFFFLEPLCCFFFFFMMMMMhhhhMMm...",
        ".....mMLEPELFFFFFLLFFFFFFFFFMMMMMhhhMMm...",
        "....mMMFLLLFFFFFFFFFFFFFFFFFFMMMMMhhMMm...",
        "...mMMFFFFFFFFFFCCFFFFFFFFFFFFMMMMhhhMMm..",
        "..mMMFFFFFNNNNNFCCCFFFFFCFFFFFMMMMMhMMMm..",
        "..mMMFFNNNNNNNNFCCCCFFFFFFFFFFMMMMMMMMMm..",
        "..mMMFNNNNNNNNCCCCCCCLFFFFFFFFMMMMMMMMMMm.",
        "..mMMMNNNNNNNFCCCCCCCFFFFFFFFFMMMMMMMMMMm.",
        ".mMMMMFNNNNNCCCCCCCCCCFFFFCFFFMMMMMMMMMMm.",
        ".mMMMMMFCCFCCCCCLLLLCFCFFFFCFFMMMMMMMMMMMm",
        "..mMMMMLLLLLLLLLLCCCCFFFFFFFFMMMMMMMMMMMMm",
        "..mMMMMFCCCCCCCCCCCCCFFFFMMMMMMMMMMMMMMMMm",
        "..mMMMMFCCCCCCCCCCCCCFFMMMMMMMMMMMMMMMMmm.",
        "...mMMMFCCCCCCCCCCCCFMMMMMMMMMMMMMMMMMm...",
        "...mMMMFCCCCCCCCCCCCFMMMMMMMMMMMMMMMMm....",
        "...mMMFCCCCCCCCCCCCFMMMMMMMMMMMMMMMMMm....",
        "...mMMFCCCCCCCCCCCFFMMMMMMMMMMMMMMMMm.....",
        "...mMMFCCCCCCCCCCFFMMMMMMMMMMMMMMMMMm.....",
        "....mMMFFFFCFFFFFMMMMMMMMMMMMMMMMMMm......",
        "....mMMFMFFFMMMMMMMMMMMMMMMMMMMMMMMm......",
        "....mMMFMMMMMMMMMMMMMMMMMMMMMMMMMmm.......",
        "....mMMFMMMMMFMMMMMMMMMMMMMMMMMMm.........",
        "....mMMMMMMMMMMMMMMMMMmmmmmmmmmmm.........",
        "...mMMMMMMMMMMMmmmmmmm....................",
        "....mMMMMMMMMMm...........................",
        "....mmmmmmmmMm............................",
        "............m.............................",
    ]
    COLORS = {"M": (195, 60, 35), "m": (130, 30, 20), "h": (225, 100, 50), "F": (230, 160, 60),
              "C": (245, 210, 140), "L": (80, 30, 15), "N": (150, 45, 40), "E": (240, 170, 40), "P": (35, 12, 5),
              "O": (110, 25, 30)}
    # His mouth opening under the smile line (row 26), by shape: (x, y, kind) cells over ART. 0 closed is
    # the smile as drawn; O is the inside of his mouth.
    MOUTHS = {
        1: [(x, 27, "O") for x in range(8, 15)] + [(x, 28, "L") for x in range(9, 14)],
        2: [(x, y, "O") for y in (27, 28) for x in range(8, 16)] + [(x, 29, "L") for x in range(9, 15)],
    }
    RANK = ".hMmFCNEPOL"  # what survives halving: features over muzzle over face over mane

    def __init__(self, show):
        super().__init__(show)
        self.cells = {}  # his cells by mouth shape: (x, y, rgb, fade)
        for shape in (0, 1, 2):
            g = [list(row) for row in self.ART]
            for x, y, k in self.MOUTHS.get(shape, ()):
                g[y][x] = k
            art = ["".join(row) for row in g]
            art = art if self.big else _halved(art, self.RANK)
            self.w, self.h = len(art[0]), len(art)
            fade_from = self.h * (1 - self.FADE_ROWS)
            self.cells[shape] = [(x, y, self.COLORS[k], min(1.0, (self.h - y) / (self.h - fade_from)))
                                 for y, row in enumerate(art) for x, k in enumerate(row) if k != "."]
        self.left = show.width - self.w

    def scene_s(self):
        cue = self.show.cue
        return cue.end - self.since if cue is not None and self.since is not None else self.SCENE_S

    LINE_GAP_S = 2.0  # a pause this long in his mouth track separates two lines (his echo's is 1.35 s)
    FADE_TAIL_S = 1.0  # he's gone this long after his last word

    def last_word_s(self):
        """Seconds into his scene that his last word ends, from his mouth track, or None without one."""
        lips = self.show.lips.get("mufasa")
        if lips is None or self.since is None:
            return None
        spoken = [i for i, k in enumerate(lips.track) if k != "0"]
        return lips.start + (spoken[-1] + 1) / lips.fps - self.since if spoken else None

    def last_line_s(self):
        """Seconds into his scene that his last line starts, from his mouth track, or None without one."""
        lips = self.show.lips.get("mufasa")
        if lips is None or self.since is None:
            return None
        spoken = [i for i, k in enumerate(lips.track) if k != "0"]
        if not spoken:
            return None
        start = spoken[-1]
        for i in reversed(spoken[:-1]):
            if start - i > self.LINE_GAP_S * lips.fps:
                break
            start = i
        return lips.start + start / lips.fps - self.since

    def glow(self, e):
        """0..1: dark before APPEAR_S, fading in, breathing, then fading out (see the class docstring)."""
        fade_in = min(1.0, max(0.0, (e - self.APPEAR_S) / self.FADE_IN_S))
        last = self.last_line_s()
        if last is not None:
            # Eased: slow at first, so he's still there for his echoing last word, then gone after it.
            span = self.last_word_s() + self.FADE_TAIL_S - last
            p = min(1.0, max(0.0, (e - last) / span))
            fade_out = 1 - p * p
        else:
            fade_out = min(1.0, max(0.0, (self.scene_s() - e) / self.FADE_OUT_S))
        breath = 1 - self.BREATH * (0.5 - 0.5 * math.cos(2 * math.pi * e / self.BREATH_S))
        return fade_in * fade_out * breath

    def draw(self, put, out, active):
        if not active:
            return
        g = self.glow(self.elapsed()) * self.PEAK
        if g <= 0.01:
            return
        show = self.show
        shape = self.mouth("mufasa")
        for x, y, rgb, fade in self.cells[shape or 0]:
            level = g * fade
            px, py = self.left + x, y
            if 0 <= px < show.width and py < show.height:
                under = out.get((px, py), (0, 0, 0))
                out[(px, py)] = tuple(int(u + (c - u) * level) for u, c in zip(under, rgb))
