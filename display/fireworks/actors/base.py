"""
What every synced-show character builds on (show_actors.py has the rest): the Actor base, and
stamp/smoke for drawing. Its own module so the characters under actors/ and show_actors.py, which
registers them, can both import it without a cycle.
"""


class Actor:
    NAME = None  # what tools/show_sync_checker.html lists it as
    ENTERS_S = 0.0  # seconds into its run of scenes it first shows, for the checker to jump to

    def __init__(self, show):
        self.show = show
        self.rng = show.rng
        self.big = show.height >= 64
        self.since = None  # where the run of scenes it's in started, while it's on

    def follow(self, active):
        """Called by the show before step(): note where its run of scenes started, by the score's clock
        (the scene's start, not the frame it was first stepped), and forget it once it's off."""
        if not active:
            self.since = None
        elif self.since is None:
            self.since = self.show.cue.start

    def mouth(self, name):
        """The mouth shape now from the score's track for `name` (0 closed, 1 half, 2 open), or None
        without one."""
        lips = self.show.lips.get(name)
        return lips.shape(self.show.t) if lips else None

    def elapsed(self):
        """Seconds since the first of the back-to-back scenes it's been on in started (0 while off)."""
        return self.show.t - self.since if self.since is not None else 0.0

    def step(self, active):
        pass

    def draw(self, put, out, active):
        pass


def stamp(out, art, colors, left, top, scale, width, height):
    """Draw pixel art ('.' empty) over whatever is at out, its top-left at (left, top), each cell
    scale x scale; cells off the board are skipped. Sprites are solid: they cover what's behind."""
    left, top = int(round(left)), int(round(top))
    for row, line in enumerate(art):
        for col, kind in enumerate(line):
            if kind == ".":
                continue
            rgb = colors[kind]
            for oy in range(scale):
                y = top + row * scale + oy
                if not 0 <= y < height:
                    continue
                for ox in range(scale):
                    x = left + col * scale + ox
                    if 0 <= x < width:
                        out[(x, y)] = rgb


def smoke(out, puffs, stamp_for, width, height):
    """Soft puffs [x, y, vx, vy, frames left, rgb, radius] added onto out, so what's behind shows through
    a thinning puff; each pixel takes its brightest puff, as GenieReveal draws his."""
    light = {}
    for cx, cy, _, _, life, rgb, rad in puffs:
        f = min(1.0, life / 18.0)
        ox, oy = int(round(cx)), int(round(cy))
        for dx, dy, falloff in stamp_for(rad):
            x, y = ox + dx, oy + dy
            g = f * falloff
            if g <= 0.05 or not (0 <= x < width and 0 <= y < height):
                continue
            seen = light.get((x, y), (0.0, 0.0, 0.0))
            light[(x, y)] = tuple(max(s, c * g) for s, c in zip(seen, rgb))
    for xy, add in light.items():
        under = out.get(xy, (0, 0, 0))
        out[xy] = tuple(min(255, int(u + a)) for u, a in zip(under, add))
