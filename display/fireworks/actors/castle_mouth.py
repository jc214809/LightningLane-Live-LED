"""The castle singing That's What Friends Are For in the synced show (see show_actors.py)."""
from display.fireworks.actors.base import Actor


class CastleSings(Actor):
    """
    That's What Friends Are For: the castle sings it, as in the real show (video 8:44-8:58). Its doorway
    is the mouth, opening and shutting to the score's mouth track (tools/lip_sync.py, "castle_sings"),
    and the whole castle stretches with it like a cartoon singing: taller and thinner as the mouth opens,
    back to itself as it shuts. It draws nothing of its own: each frame it hands the show the castle's
    shape for the mouth's shape (show.castle_shape), worked out once per shape, anchored at the bottom
    centre. With no track the mouth stays shut and the castle still.
    """
    NAME = "The castle sings"
    # By mouth shape (0 shut, 1 half, 2 open): how much of the doorway is open (the rest is wall), and
    # how far the castle stretches up and squeezes in.
    DOOR = {0: 0.35, 1: 0.7, 2: 1.0}
    TALLER = {0: 1.0, 1: 1.06, 2: 1.12}
    THINNER = {0: 1.0, 1: 0.97, 2: 0.94}

    def __init__(self, show):
        super().__init__(show)
        self.shapes = {m: self._shape(m) for m in self.DOOR}

    def _shape(self, m):
        """The castle's [(dx, dy, kind)] for mouth shape m."""
        show = self.show
        grid = {(dx, dy): kind for dx, dy, kind in show.castle_pixels}
        door = [(dx, dy) for (dx, dy), kind in grid.items() if kind == "D"]
        top, bottom = min(dy for _, dy in door), max(dy for _, dy in door)
        opens_from = bottom + 1 - round((bottom - top + 1) * self.DOOR[m])
        for dx, dy in door:
            if dy < opens_from:
                grid[(dx, dy)] = "W"  # the shut part of the doorway is wall
        sy, sx = self.TALLER[m], self.THINNER[m]
        cx, base = (show.castle_w - 1) / 2, show.castle_h - 1
        tall = round(show.castle_h * sy)
        shape = []
        for ty in range(base - tall + 1, base + 1):
            src_y = round(base - (base - ty) / sy)
            for tx in range(show.castle_w):
                kind = grid.get((round(cx + (tx - cx) / sx), src_y))
                if kind is not None:
                    shape.append((tx, ty, kind))
        return shape

    def shape(self):
        """The mouth now: the track's shape, or shut without one."""
        shape = self.mouth("castle_sings")
        return 0 if shape is None else shape

    def step(self, active):
        if active:
            self.show.castle_shape = self.shapes[self.shape()]
        elif any(self.show.castle_shape is s for s in self.shapes.values()):
            self.show.castle_shape = None
