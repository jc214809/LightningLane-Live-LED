from display.fireworks.actors.base import Actor

# The five emotions' colours: Joy, Sadness, Anger, Fear, Disgust.
EMOTIONS = ((255, 210, 40), (40, 110, 255), (235, 40, 35), (165, 80, 230), (60, 210, 70))


class MemoryOrbs(Actor):
    """
    Friendship mash-up, elapsed START_S-END_S (the real show's Inside Out, video 8:30-8:35): the castle
    fills up with memory orbs, as the real one's windows and towers do. Small round orbs in the five
    emotions' colours (2x2 LEDs on 64x32, 3x3 on 64x64) drop in and pile up row by row from the
    castle's base to its spire over FILL_S, each slot inside the castle's own pixels (the doorway left
    clear), then they fade out by END_S, just as Mike and Sulley pop up. Drawn over the castle, only as
    far as it shows. Placed by the clock: each orb's fall is a function of (elapsed - START_S) s.
    """
    NAME = "Inside Out's memory orbs"
    START_S, END_S = 25.0, 32.2  # audio 498.3-505.5
    ENTERS_S = START_S
    FILL_S = 5.7  # all landed by 504.0
    DROP_S = 0.35  # each one's fall into its slot...
    DROP_ROWS = 6  # ...from this many orb sizes above it
    FADE_S = 1.2  # gone by END_S

    def __init__(self, show):
        super().__init__(show)
        self.size = 3 if self.big else 2
        n = self.size
        inside = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind != "D"}
        base = show.castle_y + show.castle_h  # the row under the castle
        slots = []
        for top in range(base - n, show.castle_y - 1, -n):
            row = [left for left in range(show.castle_x, show.castle_x + show.castle_w - n + 1, n)
                   if all((left + i, top + j) in inside for i in range(n) for j in range(n))]
            self.rng.shuffle(row)  # each row fills in a random order
            slots += [(left, top) for left in row]
        step = self.FILL_S / max(1, len(slots))
        # (left, top, rgb, landing s): bottom rows first, so the castle fills from its base up.
        self.orbs = [(left, top, self.rng.choice(EMOTIONS), (i + 1) * step) for i, (left, top) in enumerate(slots)]
        # The orb's look: lit from the top left, a highlight there and a shade at the bottom right, so it
        # reads as a glowing ball (dimmed corners made a 3x3 one a "+").
        if n == 3:
            self.shade = {(0, 0): 1.45, (1, 0): 1.15, (0, 1): 1.15, (2, 1): 0.8, (1, 2): 0.8, (2, 2): 0.6}
        else:
            self.shade = {(0, 0): 1.35, (1, 1): 0.7}

    def local(self, e):
        return e - self.START_S if self.START_S <= e < self.END_S else None

    def fade(self, t):
        return max(0.0, min(1.0, (self.END_S - self.START_S - t) / self.FADE_S))

    def draw(self, put, out, active):
        if not active:
            return
        t = self.local(self.elapsed())
        if t is None:
            return
        g = self.fade(t) * self.show.castle_level()
        if g <= 0.01:
            return
        n, w, h = self.size, self.show.width, self.show.height
        for left, top, rgb, lands in self.orbs:
            falling = lands - t
            if falling >= self.DROP_S:
                continue  # not dropped yet; the rest of its row and those above it land later
            # Falling under gravity: from DROP_ROWS sizes up to its slot, landing at `lands`.
            k = max(0.0, falling / self.DROP_S)
            y0 = top - round(self.DROP_ROWS * n * k * k)
            for i in range(n):
                for j in range(n):
                    x, y = left + i, y0 + j
                    if 0 <= x < w and 0 <= y < h:
                        shade = self.shade.get((i, j), 1.0)
                        # Brightening also lifts toward white, so Joy's yellow and Anger's red still get a shine.
                        lift = max(0.0, shade - 1.0) * 255
                        out[(x, y)] = tuple(min(255, int((c * min(shade, 1.0) + lift) * g)) for c in rgb)
