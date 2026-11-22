"""The bases every scene look builds on (Effect, its fading and particle kinds) and the castle
measurements they share: the doorway, the roof peaks."""

GOLD, WHITE = (255, 210, 90), (255, 255, 255)


class Effect:
    def __init__(self, show):
        self.show = show
        self.rng = show.rng
        self.big = show.height >= 64
        self.s = 2 if self.big else 1  # pixel scale: doubled on 64-row boards, like the castle

    def progress(self):
        cue = self.show.cue
        return cue.progress(self.show.t) if cue else 0.0

    def step(self, active):
        pass

    def draw_behind(self, put, out, active):
        pass

    def draw_front(self, put, out, active):
        pass


class _Level(Effect):
    """An effect that fades in while its scene is on and out after it."""

    fade_frames = 45

    def __init__(self, show):
        super().__init__(show)
        self.level = 0.0

    def step(self, active):
        delta = 1 / self.fade_frames
        self.level = min(1.0, self.level + delta) if active else max(0.0, self.level - delta)


class _Particles(Effect):
    """Particles [x, y, vx, vy, life, max life, rgb]; spawn() makes one, `chance` per frame."""

    chance = 0.5
    cap = 80
    front = False

    def __init__(self, show):
        super().__init__(show)
        self.parts = []

    def spawn(self):
        raise NotImplementedError

    def step(self, active):
        if active and len(self.parts) < self.cap and self.rng.random() < self.chance:
            self.parts.append(self.spawn())
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
        w, h = self.show.width, self.show.height
        self.parts = [p for p in self.parts if p[4] > 0 and -3 <= p[0] < w + 3 and -4 <= p[1] < h + 1]

    def _draw(self, put):
        for x, y, _, _, life, max_life, rgb in self.parts:
            f = life / max_life
            put(x, y, tuple(int(c * f) for c in rgb))

    def draw_behind(self, put, out, active):
        if not self.front:
            self._draw(put)

    def draw_front(self, put, out, active):
        if self.front:
            self._draw(put)


def _door(show):
    """The castle's doorway pixels on the board, and its centre."""
    door = [(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind == "D"]
    cx = sum(x for x, _ in door) / len(door)
    cy = sum(y for _, y in door) / len(door)
    return door, (cx, cy)


def _roof_peaks(show):
    """The top of each roof on the board, left to right: the highest roof LED in each run of columns."""
    tops = {}
    for dx, dy, kind in show.castle_pixels:
        if kind == "R" and (dx not in tops or dy < tops[dx]):
            tops[dx] = dy
    peaks = [dx for dx in sorted(tops) if tops.get(dx - 1, 99) >= tops[dx] <= tops.get(dx + 1, 99)]
    return [(show.castle_x + dx, show.castle_y + tops[dx]) for dx in peaks]
