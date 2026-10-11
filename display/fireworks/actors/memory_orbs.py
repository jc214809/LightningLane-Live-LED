import math

from display.fireworks.actors.base import Actor

JOY = (255, 210, 40)
SADNESS = (40, 110, 255)


def _ease_out(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


class MemoryOrbs(Actor):
    """
    Friendship mash-up, elapsed 35-54 s: two Inside Out memory orbs, Joy's yellow rolling in from the
    left and Sadness's blue from the right along the bottom (a shine highlight turns as they roll). They
    meet in the middle, bump apart a little and settle touching, then float up together glowing and fade
    out over the last 3 s. Placed by the clock: positions are functions of (elapsed - 35) s.
    """
    NAME = "Joy and Sadness's memory orbs"
    START_S, END_S = 35.0, 54.0
    ENTERS_S = START_S
    ROLL_S, BUMP_S, RISE_FROM_S, FADE_S = 4.0, 0.8, 5.5, 3.0

    def __init__(self, show):
        super().__init__(show)
        self.r = 5 if self.big else 3
        r = self.r
        self.ground = show.height - 1 - r  # centre y when resting on the bottom edge
        self.top = int(show.height * 0.38)
        self.mid = show.width / 2.0
        # (dx, dy, distance) over the orb plus a 2px glow ring, worked out once.
        self.disc = [(dx, dy, math.hypot(dx, dy)) for dy in range(-r - 2, r + 3) for dx in range(-r - 2, r + 3)
                     if math.hypot(dx, dy) <= r + 2]

    def local(self, e):
        return e - self.START_S if self.START_S <= e < self.END_S else None

    def gap(self, t):
        """How far each orb's centre is from the middle at t s in."""
        r = self.r
        touch = r + 0.5
        if t < self.ROLL_S:
            start = self.mid + r + 1
            return start + (touch - start) * _ease_out(t / self.ROLL_S)
        b = t - self.ROLL_S
        if b < self.BUMP_S:
            return touch + 2.0 * math.sin(math.pi * b / self.BUMP_S)
        return touch

    def centres(self, t):
        """((joy x, y), (sadness x, y)) at t s in."""
        d = self.gap(t)
        rise = (t - self.RISE_FROM_S) / (self.END_S - self.START_S - self.RISE_FROM_S - 1.0)
        y = self.ground + (self.top - self.ground) * (1 - math.cos(math.pi * max(0.0, min(1.0, rise)))) / 2
        if rise > 0:
            y += 0.6 * math.sin((t - self.RISE_FROM_S) * 2.4)
        return (self.mid - d, y), (self.mid + d, y)

    def fade(self, t):
        span = self.END_S - self.START_S
        return max(0.0, min(1.0, (span - t) / self.FADE_S, t / 0.3))

    def draw(self, put, out, active):
        if not active:
            return
        t = self.local(self.elapsed())
        if t is None:
            return
        g = self.fade(t)
        if g <= 0:
            return
        pulse = 0.85 + 0.15 * math.sin(t * 3.0)
        for (cx, cy), rgb, sign in zip(self.centres(t), (JOY, SADNESS), (1, -1)):
            # Rolling: the shine turns with the distance covered; afloat it drifts slowly round.
            angle = sign * (cx - self.mid) / self.r - math.pi * 0.75 + 0.6 * max(0.0, t - self.RISE_FROM_S)
            self._orb(out, cx, cy, rgb, angle, g, pulse)

    def _orb(self, out, cx, cy, rgb, angle, g, pulse):
        r = self.r
        w, h = self.show.width, self.show.height
        ox, oy = int(round(cx)), int(round(cy))
        sx = ox + int(round(math.cos(angle) * r * 0.5))
        sy = oy + int(round(math.sin(angle) * r * 0.5))
        for dx, dy, d in self.disc:
            x, y = ox + dx, oy + dy
            if not (0 <= x < w and 0 <= y < h):
                continue
            if d <= r - 0.6:
                k = (1.0 - 0.45 * d / r) * pulse
                col = tuple(min(255, int(c * k + 70 * (1 - d / r))) for c in rgb)
            elif d <= r + 0.4:
                col = tuple(int(c * 0.45) for c in rgb)  # darker rim
            else:
                k = 0.22 * (r + 2 - d) / 1.6 * pulse  # glow, added over what's behind
                under = out.get((x, y), (0, 0, 0))
                out[(x, y)] = tuple(min(255, int(u + c * k * g)) for u, c in zip(under, rgb))
                continue
            out[(x, y)] = tuple(int(c * g) for c in col)
        if 0 <= sx < w and 0 <= sy < h:
            out[(sx, sy)] = tuple(int(255 * g) for _ in range(3))
