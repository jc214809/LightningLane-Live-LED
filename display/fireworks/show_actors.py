"""
Characters for the synced show's later versions (music_show.py), one class each, turned on by name in a
scene's "actors" (a version's overlay file: see score.py). Like an effect, an actor steps every frame
and only starts while its scene is on, but it places itself by the clock (elapsed(): seconds since the
first of the run of back-to-back scenes it's in, so it carries on across a cut), not by frames, so a slow
board keeps it with the music. Actors draw in front of the castle and
the fireworks, under the final flash. One who sings moves its mouth to the score's track for it
(score.Lips, from tools/lip_sync.py), looked up by the clock like everything else.
"""
import math

from display.animation.characters.genie import GenieReveal
from display.fireworks.actors.base import Actor, smoke, stamp  # noqa: F401 (stamp: tests import it here)
from display.motion import ease_out, smooth


class GenieOrbit(Actor):
    """
    Friend Like Me: Genie (his ride-reveal art, 1x on both boards) swells out of a puff of his smoke at
    the castle's spire, as he grows out of the lamp on his ride screen, then circles the spire until he
    stops singing (through the finale scene too): wide side to side, shallower up and down (on 64x32 he nearly fills the board's
    height, so there it's mostly a side-to-side swing), trailing smoke. When his scenes end he vanishes
    in another puff. He mouths his song (MOUTHS) to the score's track; without one he keeps his grin.
    """
    NAME = "Genie"
    ARRIVE_S = 1.6  # the puff, then he swells out of it
    EASE_IN_S = 1.5  # from where he formed onto his orbit
    LAP_S = 6.0
    PUFFS = 2  # smoke per frame while he flies
    VANISH_PUFFS = 14
    # His mouth rows (ART's 11-13) by shape: 2 open is his grin as drawn; 1 half shows teeth over a
    # thinner red; 0 closed is a toothy grin line.
    MOUTH_ROW = 11
    MOUTHS = {
        1: [".....SBRWWWWWRBS.....",
            ".....SBBRRRRRBBS.....",
            ".....SBBBBBBBBBS....."],
        0: [".....SBBBBBBBBBS.....",
            ".....SBSWWWWWSBS.....",
            ".....SBBBBBBBBBS....."],
    }

    def __init__(self, show):
        super().__init__(show)
        trim = GenieReveal.TRIM_64 if self.big else GenieReveal.TRIM_32
        self.cells = {}  # his lit cells by mouth shape
        for shape in (0, 1, 2):
            art = list(GenieReveal.ART)
            if shape in self.MOUTHS:
                art[self.MOUTH_ROW:self.MOUTH_ROW + 3] = self.MOUTHS[shape]
            art = [row for i, row in enumerate(art) if i not in trim]
            self.cells[shape] = [(col, row, GenieReveal.COLORS[kind]) for row, line in enumerate(art)
                                 for col, kind in enumerate(line) if kind != "."]
        self.w, self.h = len(art[0]), len(art)
        self.puffs = []
        self.last = None  # his top-left on the last frame he was on, for the puff he vanishes in
        sx, sy = show.spire
        self.rx = (show.width - self.w) / 2 - 1
        self.ry = 10 if self.big else 4
        self.home = self._on_board(sx - self.w / 2, sy - self.h / 2)

    def _on_board(self, left, top):
        return (max(0.0, min(left, self.show.width - self.w)), max(0.0, min(top, self.show.height - self.h)))

    def grow(self, e):
        """0 (not formed) to 1 (full size); the smoke pours alone for the first third."""
        return ease_out(max(0.0, e - self.ARRIVE_S * 0.35) / (self.ARRIVE_S * 0.65))

    def top_left(self, e):
        """Where his full-size sprite is e seconds into the scene: formed by the spire, then easing onto
        an ellipse round it, starting above it and heading right."""
        sx, sy = self.show.spire
        a = 2 * math.pi * max(0.0, e - self.ARRIVE_S) / self.LAP_S
        orbit = self._on_board(sx + self.rx * math.sin(a) - self.w / 2, sy - self.ry * math.cos(a) - self.h / 2)
        k = smooth((e - self.ARRIVE_S) / self.EASE_IN_S)
        return tuple(h + (o - h) * k for h, o in zip(self.home, orbit))

    def _puff(self, x, y, spread, rise):
        r = self.rng
        return [x + r.uniform(-spread, spread), y + r.uniform(-spread, spread), r.uniform(-0.4, 0.4),
                r.uniform(-rise, 0.1), r.randint(16, 28), r.choice(GenieReveal.SMOKE_COLORS), r.uniform(0.6, 1.4)]

    def step(self, active):
        e = self.elapsed()
        if active:
            sx, sy = self.show.spire
            if e < self.ARRIVE_S:
                self.puffs += [self._puff(sx, sy, 1, 0.8) for _ in range(3)]
            else:
                left, top = self.top_left(e)
                self.puffs += [self._puff(left + self.w / 2, top + self.h * 0.85, 2, 0.3) for _ in range(self.PUFFS)]
                self.last = (left, top)
        elif self.last is not None:
            left, top = self.last
            self.puffs += [self._puff(left + self.w / 2, top + self.h / 2, self.w / 3, 0.6)
                           for _ in range(self.VANISH_PUFFS)]
            self.last = None
        for p in self.puffs:
            p[0] += p[2]
            p[1] += p[3]
            p[3] *= 0.92
            p[4] -= 1
            p[6] += 0.06
        self.puffs = [p for p in self.puffs if p[4] > 0]

    def draw(self, put, out, active):
        show = self.show
        smoke(out, self.puffs, GenieReveal._stamp, show.width, show.height)
        if not active:
            return
        e = self.elapsed()
        g = self.grow(e)
        if g <= 0.02:
            return
        left, top = (math.floor(v + 0.5) for v in self.top_left(e))
        ax, ay = show.spire
        shape = self.mouth("genie")
        for col, row, rgb in self.cells[2 if shape is None else shape]:
            x, y = left + col, top + row
            if g < 1:
                # The cell's centre pulled toward the spire, so he swells out of the smoke there.
                x = math.floor(ax + (x + 0.5 - ax) * g)
                y = math.floor(ay + (y + 0.5 - ay) * g)
            if 0 <= x < show.width and 0 <= y < show.height:
                out[(x, y)] = rgb


# One module each under actors/, building on actors/base.py.
from display.fireworks.actors.baymax import BaymaxInflates  # noqa: E402
from display.fireworks.actors.canoe import CanoeSails  # noqa: E402
from display.fireworks.actors.castle_mouth import CastleSings  # noqa: E402
from display.fireworks.actors.dumbo import DumboFlies  # noqa: E402
from display.fireworks.actors.lantern_boat import LanternBoat  # noqa: E402
from display.fireworks.actors.memory_orbs import MemoryOrbs  # noqa: E402
from display.fireworks.actors.merida import MeridaShoots  # noqa: E402
from display.fireworks.actors.monsters import MikeAndSulley  # noqa: E402
from display.fireworks.actors.mufasa import MufasaInTheStars  # noqa: E402
from display.fireworks.actors.olaf import OlafStands  # noqa: E402
from display.fireworks.actors.princess_garden import PrincessGarden  # noqa: E402
from display.fireworks.actors.ralph import RalphSmashes  # noqa: E402
from display.fireworks.actors.ray import RayGlows  # noqa: E402
from display.fireworks.actors.toy_story import BuzzAndWoody  # noqa: E402
from display.fireworks.actors.up_house import UpHouseFloats  # noqa: E402
from display.fireworks.actors.walle import WallEFloats  # noqa: E402

ACTORS = {
    "genie": GenieOrbit,
    "buzz_woody": BuzzAndWoody,
    "olaf": OlafStands,
    "walle": WallEFloats,
    "dumbo": DumboFlies,
    "ralph": RalphSmashes,
    "baymax": BaymaxInflates,
    "mufasa": MufasaInTheStars,
    "ray": RayGlows,
    "merida": MeridaShoots,
    "up_house": UpHouseFloats,
    "princess_garden": PrincessGarden,
    "canoe": CanoeSails,
    "lantern_boat": LanternBoat,
    "memory_orbs": MemoryOrbs,
    "mike_sulley": MikeAndSulley,
    "castle_sings": CastleSings,
}
