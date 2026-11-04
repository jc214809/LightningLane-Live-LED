import math

from display.animation.drawing import _blackout, walking_pixels
from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS
from display.pixels import paint


def _open_jaw(art, jaw, opening):
    """
    (art with its mouth opened `opening`, 0 shut to 1 wide, as a grid of cells; the cells of his
    head). jaw is (first row of the lower jaw, its last row, hinge column, rows it drops): columns
    ahead of the hinge swing open, more toward the front of his face, like a jaw on a hinge, and
    the gap fills with his mouth, teeth along its top and bottom. Everything above the jaw is head.
    """
    split, bottom, hinge, drop = jaw
    grid = [["."] * len(art[0]) for _ in range(len(art))]
    head, moving = set(), []
    for r, row in enumerate(art):
        for c, k in enumerate(row):
            if k == ".":
                continue
            if r < split:
                head.add((r, c))
            if c < hinge and split <= r <= bottom:
                moving.append((r + round(drop * (hinge - c) / hinge * opening), c, k))
            else:
                grid[r][c] = k
    for r, c, k in moving:  # the swinging jaw goes over anything it swings across (his arm)
        grid[r][c] = k
        head.add((r, c))
    for c in range(hinge):
        if art[split - 1][c] != "." and art[split][c] != ".":
            gap = round(drop * (hinge - c) / hinge * opening)
            for r in range(split, split + gap):
                grid[r][c] = "M"
                head.add((r, c))
            if gap and art[split][c] == "W":
                grid[split - 1][c] = "W"  # a tooth above each of the lower jaw's, on the upper jaw
    return grid, head


NECK_COLS = 6  # how far ahead of and above the neck its cells stay put as his head tips back


def _roar_pose(art, jaw, tilt, opening, room):
    """
    art (facing left, as drawn) roaring `opening` of the way: jaw open and head tipped back about
    his neck, padded on top with the rows the head rises above the art (at most `room`, the rows
    above him on the board; past that the head sinks into his neck to fit). tilt is (the neck's
    column, its row, degrees the head tips back at full roar).
    """
    grid, head = _open_jaw(art, jaw, opening)
    px, py, degrees = tilt
    a = math.radians(degrees * opening)
    cos, sin = math.cos(a), math.sin(a)
    tipped = {}
    rows = [r for r, _ in head]
    cols = [c for _, c in head]
    reach = max(abs(r - py) for r in rows) + max(abs(c - px) for c in cols)
    for r in range(py - reach, py + reach + 1):
        for c in range(px - reach, px + reach + 1):
            # The head cell that lands here: turn back the other way (snout up, crown back).
            dx, dy = c - px, r - py
            sc, sr = round(px + dx * cos + dy * sin), round(py - dx * sin + dy * cos)
            if (sr, sc) in head and 0 <= c < len(grid[0]):
                tipped[(r, c)] = grid[sr][sc]
    top = min(r for r, _ in tipped)
    sink = max(0, -top - room)
    pad = max(0, -top) - sink
    out = [["."] * len(grid[0]) for _ in range(len(grid) + pad)]
    for r, row in enumerate(grid):
        for c, k in enumerate(row):
            # Body, and the head's back near the neck under the tipped head, so no gap opens there.
            if (r, c) not in head or (c >= px - NECK_COLS and r >= py - NECK_COLS):
                out[r + pad][c] = k
    for (r, c), k in tipped.items():
        if 0 <= r + pad + sink < len(out):
            out[r + pad + sink][c] = k
    return ["".join(row) for row in out]


def _mirror(art):
    return [row[::-1] for row in art]


class RexReveal(CapturesScreens):
    """
    Rex stomps in from the left edge, facing right, uncovering the new ride behind him.
    Halfway across he stops, throws his head back and his jaw open and roars, and the whole board shakes; then
    he shuts his mouth and stomps off the right edge, feet stepping all the way.
    """

    SCALE = 1  # each board has its own art, both 1x
    wants_new = True  # the roar shakes the new ride, so it needs its pixels
    hold_after_s = 3.0  # the ride screen, after he leaves
    STEP = 1  # pixels a frame, steady
    POSE_F = 4  # frames each pose of his walk (drawing.WALK_CYCLE)
    OPEN_S, ROAR_S, SHUT_S = 0.2, 1.0, 0.25
    SHAKE = 1  # pixels the board jumps each frame of the roar

    # From the user's art, cell for cell, one per board: 38x32 for 64x32, 61x51 for 64x64.
    # Drawn facing left; he's mirrored on the board to face the way he walks.
    # '.' empty, g outline, G green, A shading, B highlight, Y belly, W white (eyes, teeth),
    # K black, M inside his mouth (only when it's open: nearly off, a gap between his teeth).
    ART = [
        ".........gg...........................",
        "........gGGg..........................",
        ".......gWgWgg.........................",
        "......gWKgKWg.........................",
        ".....gGGGGGGGg........................",
        "....gGGGGGGGGGg.......................",
        "..GGGGGGGGGGGgB.......................",
        ".gggGggGGGGGgGGg......................",
        "gGAgGggGGGGGgGGg......................",
        "gGAAGAGGGGGGggGg......................",
        "gGGGGGGGGGGGggG.......................",
        "gGGGGGGGGGWWGGg.......................",
        "gKWWKWWKWWggGgg.......................",
        ".gggggggggGGgGG.......................",
        "..GGGGGGGGggGGGg..gBBBgg..............",
        "..ggGGGGGgYYGGGGggBBBBBBgg............",
        ".......gYYYYggGGGGGGGGBBBBB...........",
        ".g.g...gYYYYGGgGGGGGgGGGGGGg..........",
        ".ggG...gYYYYGGggGGGGgGGGGGGGg.......gg",
        ".gAAg..YYYggYGggGGGGGGGGGGGAgg....gBg.",
        ".gggAggYYYgBggGgGGGgGGGGGGGAgBg..gBg..",
        ".....ggYYYgGggAGGGGgGGGGGGGgGGGGGGg...",
        ".......gYYggYYGGGGGgGGGGGGAGGGGGgg....",
        "........gYYYYYGGGGGGGGGGGGAGGgGG......",
        ".........gYYYYYYYGGGAAGGGgYYYgg.......",
        ".........GgYYYYYYYYGgAAGAgYYY.........",
        ".........GGAggYYYYYYYgAAGGY...........",
        ".........gGGAAg.YYYYYYAGGGG...........",
        ".........gGGGAg.......AGGGG...........",
        ".......gggGGGGA......gAGgGGg..........",
        ".......gggGgGGA.....gGGggGGgg.........",
        "......gggggggGg....gggggggGgg.........",
    ]
    BIG_ART = [
        ".............gggg............................................",
        "............gGGGGg...........................................",
        "...........gggggggg..........................................",
        "..........ggWWgWWggg.........................................",
        ".........ggWKKgKKWgg.........................................",
        ".........ggWKKgKKWggg........................................",
        ".......ggGGGGGGGGGGGg........................................",
        ".....ggGGGGGGGGGGGGGGgg......................................",
        "...ggGGGGGGGGGGGGGGGgGBg.....................................",
        "..gGGGGGGGGGGGGGGGGGgGBg.....................................",
        ".gGGGGGGGGGGGGGGGGGgGGGBg....................................",
        ".gGggGGGggGGGGGGGGGgGGGBg....................................",
        "gGGAgGGggggGGGGGGGGgGGGBg....................................",
        "gGGAgGGgAAAGGGGGGGGgGGGBg....................................",
        "gGGAAGGAAGGGGGGGGGGggGGBg....................................",
        "gGGGGGGGGGGGGGGGGGGKgGGg.....................................",
        "gGGGGGGGGGGGGGGGGGKgGGGg.....................................",
        "gGGGGGGGGGGGGGGGKKgGGGg......................................",
        "gGGGGGGGGGGGGKKKWggGGGg......................................",
        "gKKKKKKKKKKKKWWgggGGgGg......................................",
        ".gGgWWgWWgWWgWggGGGgGGGg.....................................",
        ".gGGggggggggggGGGGgGGGGg......ggggg..........................",
        "..gGGGGGGGGGGGGGggGGGGGGg...ggBBBBBggg.......................",
        "...ggGGGGGGGGgggYYGGGGGgGgggBBBBBBBBBgggg....................",
        ".....ggggggggYYYYYGGGggGGGBBBBGGGGGggBBBBg...................",
        "...........gYYYYYYgggGGGGGGGGGGGGGgBBBBBBBg..................",
        "...........gggggggGGGGGGGGGGGGGGGgGGGGGGGBBg.................",
        ".gg.gg.....gYYYYYYGGGGgGGGGGGGGGgGGGGGGGGGBg.................",
        ".gGgGg.....gYYYYYYYGGGgGgGGGGGGGgGGGGGGGGGGGg............gggg",
        "..gAAg....gYYYYYYYYGGGgGgGGGGGGgGGGGGGGGGGGGg..........ggBBg.",
        ".gGAAAgg..gYYYYYggYYGGgGgGGGGGGgGGGGGGGGGGGAggg.......gBBgg..",
        ".gggggAAgggYYYYYgBggggGGgGGGGGgGGGGGGGGGGGGAgBBgg...ggBBg....",
        "......ggAAgYYYYgBGGGGGggAGGGGGgGGGGGGGGGGGGAgGGgBgggBBBg.....",
        "........gggYYYYggGGgggAAGGGGGGgGGGGGGGGGGGAgGGGgGGGGGGg......",
        "...........gYYYYgBgAAAGGGGGGGGgGGGGGGGGGGAAgGGGgGGGGGg.......",
        "...........gYYYYggAYYGGGGGGGGGgGGGGGGGGGGAgGGGGgGGGgg........",
        "............gYYYYYYYYYGGGGGGGGGgGGGGGGGGGAgGGGgGGGg..........",
        ".............gYYYYYYYYYYGGGGGGGgAGGGGGGGAgYYYYgYYg...........",
        ".............ggYYYYYYYYYYYGGGGGgAAGGGGGAgYYYYgggg............",
        ".............gGggYYYYYYYYYYYYGGGgAAAGGAAgggggg...............",
        ".............gGGGggYYYYYYYYYYYYYgAAAAAAGGg...................",
        ".............gGGGAAggYYYYYYYYYYYYgAAAGGGGg...................",
        ".............gGGGGAAAggggYYYYYYYYgAAGGGGGg...................",
        "..............gGGGGAAAg..ggggggggggAGGGGGGg..................",
        "..............gGGGGGAAg...........gAGGGGGGg..................",
        ".............gGGGGGGAAg...........gAGGGGGGg..................",
        "...........ggGgGGGGGGAAg.........ggAGggGGGGg.................",
        "..........gggggGGgGGGGAg........gGGGggggGGGgg................",
        ".........ggggggGgggGGGAg.......ggGGggggggGgggg...............",
        ".........gggggggggggGGg.......ggggGggggggGgggg...............",
        ".........ggggggggggggg........gggggggggggggggg...............",
    ]
    colors = {"G": (97, 184, 17), "g": (34, 92, 8), "Y": (199, 214, 115), "A": (78, 149, 11),
              "B": (155, 230, 17), "K": (5, 7, 5), "W": (248, 250, 247), "M": (10, 16, 6)}
    # The jaw for _open_jaw: (first row of the lower jaw, its last row, hinge column, rows it
    # drops). The tilt for _roar_pose: (his neck's column and row, degrees his head tips back).
    JAW, TILT = (12, 15, 12, 5), (14, 14, 25)
    BIG_JAW, BIG_TILT = (20, 24, 18, 6), (22, 22, 25)
    # (first foot row, columns of the foot behind him, columns of the foot ahead).
    FEET = (28, set(range(18, 38)), set(range(0, 18)))
    BIG_FEET = (44, set(range(31, 61)), set(range(0, 31)))

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        big = height >= 64
        self.drawn = self.BIG_ART if big else self.ART  # facing left, as drawn
        self.art = _mirror(self.drawn)
        self.jaw = self.BIG_JAW if big else self.JAW
        self.tilt = self.BIG_TILT if big else self.TILT
        self.w = len(self.drawn[0])
        top, behind, ahead = self.BIG_FEET if big else self.FEET
        self.feet = (top, {self.w - 1 - c for c in behind}, {self.w - 1 - c for c in ahead})
        self.y0 = height - len(self.art)
        self.stop_x = (width - self.w) // 2
        speed = self.STEP * FPS
        self.stop_at = (self.stop_x + self.w) / speed
        self.roar_at = self.stop_at + self.OPEN_S
        self.shut_at = self.roar_at + self.ROAR_S
        self.leave_at = self.shut_at + self.SHUT_S
        self.duration = self.leave_at + (width - self.stop_x) / speed
        self.new_px = {}
        self._mouths = {}

    def mouth(self, opening):
        """His art roaring `opening` of the way (jaw open, head back), worked out once per step."""
        step = round(opening * 10)
        if not step:
            return self.art
        if step not in self._mouths:
            self._mouths[step] = _mirror(_roar_pose(self.drawn, self.jaw, self.tilt, step / 10, self.y0))
        return self._mouths[step]

    def x_at(self, t):
        """His left edge (the tip of his tail) at t."""
        speed = self.STEP * FPS
        if t < self.stop_at:
            return -self.w + round(speed * t)
        if t < self.leave_at:
            return self.stop_x
        return self.stop_x + round(speed * (t - self.leave_at))

    def opening(self, t):
        """How far his jaw is open, 0 to 1."""
        if t < self.stop_at or t >= self.leave_at:
            return 0.0
        if t < self.roar_at:
            return (t - self.stop_at) / self.OPEN_S
        if t < self.shut_at:
            return 1.0
        return 1 - (t - self.shut_at) / self.SHUT_S

    def shake(self, t):
        """(dx, dy) the whole board is knocked by the roar at t."""
        if not self.roar_at <= t < self.shut_at:
            return 0, 0
        frame = int(t * FPS)
        return ((-1, 0), (1, -1), (0, 1), (1, 0), (-1, 1), (0, -1))[frame % 6]

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = self.x_at(t)
        dx, dy = (d * self.SHAKE for d in self.shake(t))
        edge = min(self.width, max(0, x + self.w + dx))  # the tip of his snout
        if dx or dy:
            # Repaint the ride knocked sideways, black included, so the steady one underneath doesn't show.
            for py in range(self.height):
                for px in range(edge):
                    canvas.SetPixel(px, py, *self.new_px.get((px - dx, py - dy), (0, 0, 0)))
        _blackout(canvas, edge, self.width, self.height)  # ahead of him, still dark
        art = self.mouth(self.opening(t))
        lift = len(art) - len(self.art)
        walking = int(t * FPS) // self.POSE_F if not self.stop_at <= t < self.leave_at else None
        pixels = walking_pixels(art, x + dx, self.y0 - lift + dy, self.colors,
                                (self.feet[0] + lift, *self.feet[1:]), walking)
        paint(canvas, pixels, self.width, self.height)
        return True
