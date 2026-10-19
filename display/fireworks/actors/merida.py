"""Merida for the synced show's Touch the Sky (see show_actors.py)."""
import math

from display.animation.characters.archer import ArcherReveal as Archer
from display.fireworks.actors import merida_poses as poses
from display.fireworks.actors.base import Actor, stamp
from display.motion import ease_out
from utils import debug


class MeridaShoots(Actor):
    """
    Touch the Sky: Merida, the archer's art full size at the bottom left (64x64 only, as 64x32 is too short
    for her), rises in her first ENTER_S and says her line, "Your destiny lies within you...", to the
    score's mouth track, holding her bow by its top, its foot planted at her side, her other hand on her
    hip. Then she tosses it up, catches it, draws and leans back to aim; on "chase the wind" a firework
    bursts into a bullseye high on the right (TARGET_S) and hangs there; on "touch" (LOOSE_S) she lets go:
    the string snaps, her hand flies back and drops to her side, and the arrow flies off the string at the
    archer's speed into the bullseye's centre, which shatters into sparks of its own colours. LEAVE_S after
    the hit she sinks away, over ENTER_S (sooner if her scene ends first). Her poses (merida_poses.py has the scene's timings) are baked, so a
    frame only stamps one. Times are seconds into her scene.
    """
    NAME = "Merida"
    ENTER_S = 0.6
    TARGET_S = 26.3  # 294.3: "chase the wind"
    BURST_S = 0.35  # the bullseye opening
    LOOSE_S = poses.RELEASE  # 295.36: "touch"
    SHATTER_S = 1.3  # the sparks' fall
    LEAVE_S = 2.0  # after the hit, she sinks away
    COLORS = poses.COLORS
    LEFT = 3  # her art's first column on the board: as far left as she goes whole (her hand flung back past
    # her ear after the shot reaches 3 columns left of it)
    TARGET_X = 49  # the bullseye's centre column, high over the castle's right (its row is on her aim)
    # Its rings from the centre out: gold, red, white, red.
    RINGS = ((1.2, (255, 210, 60)), (2.4, (230, 40, 40)), (3.6, (245, 245, 245)), (4.8, (230, 40, 40)))
    TRAIL = 9
    SPARKS = 28
    _frames = None  # the baked poses, loaded once

    def __init__(self, show):
        super().__init__(show)
        self.top = show.height - poses.H
        if MeridaShoots._frames is None:
            MeridaShoots._frames = poses.load()
        self.built = {}  # frames missing from the bake, built once (slow) if ever needed
        # Where the arrow leaves the string at full aim, and the bullseye on that line.
        _, chest = poses.chest_transform(poses.AIM)
        x, y = chest((Archer.NOCK[0] + 0.5, Archer.NOCK[1] + 0.5))
        self.nock = (x + self.LEFT, y + self.top)
        self.aim = (math.cos(math.radians(poses.AIM)), -math.sin(math.radians(poses.AIM)))
        ty = self.nock[1] + self.aim[1] / self.aim[0] * (self.TARGET_X + 0.5 - self.nock[0]) - 0.5
        self.target = (self.TARGET_X, int(round(ty)))
        # The arrow's head reaches the bullseye's centre HIT_S into her scene.
        reach = math.hypot(self.target[0] + 0.5 - self.nock[0], self.target[1] + 0.5 - self.nock[1])
        reach -= Archer.ARROW_LEN - 1
        s = 0.0
        while self.flown(s) < reach:
            s += 0.001
        self.hit_s = self.LOOSE_S + s

    @staticmethod
    def flown(s):
        """How far the arrow has gone s seconds after the release (the archer's: a pick-up, then its speed)."""
        if s <= 0:
            return 0.0
        if s < Archer.PICKUP_S:
            return Archer.FLY_PX_S * s * s / (2 * Archer.PICKUP_S)
        return Archer.FLY_PX_S * (s - Archer.PICKUP_S / 2)

    def scene_s(self):
        cue = self.show.cue
        return cue.end - self.since if cue is not None and self.since is not None else 35.0

    def drop(self, e):
        """Rows below her standing place e seconds in: rising in her first ENTER_S, sinking over ENTER_S from
        LEAVE_S after the hit (or in her scene's last ENTER_S, if that comes first)."""
        gone = min(self.hit_s + self.LEAVE_S + self.ENTER_S, self.scene_s())
        p = min(1.0, e / self.ENTER_S, max(0.0, (gone - e) / self.ENTER_S))
        return int(math.floor(poses.H * (1 - ease_out(max(0.0, p))) + 0.5))

    def frame(self, key):
        """A pose packed as {"x", "y", "rows"}: baked, or built (and kept) if the bake lacks it."""
        packed = self._frames.get(key) or self.built.get(key)
        if packed is None:
            debug.warning(f"Merida's {key} isn't baked: run python3 tools/build_merida_poses.py")
            packed = self.built[key] = poses.pack(poses.build(key))
        return packed

    def draw(self, put, out, active):
        if not active or not self.big:
            return
        e = self.elapsed()
        self.draw_target(out, e)
        dy = self.drop(e)
        if dy < poses.H:
            f = self.frame(poses.frame_key(e, self.mouth("merida")))
            stamp(out, f["rows"], self.COLORS, self.LEFT + f["x"], self.top + f["y"] + dy, 1,
                  self.show.width, self.show.height)
        self.draw_arrow(out, e)

    def _put(self, out, x, y, rgb):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.show.width and 0 <= y < self.show.height:
            out[(x, y)] = rgb

    def draw_target(self, out, e):
        """The bullseye: bursting open from TARGET_S, hanging with a twinkle, shattering when hit."""
        if e < self.TARGET_S:
            return
        cx, cy = self.target
        if e < self.hit_s:
            grow = ease_out(min(1.0, (e - self.TARGET_S) / self.BURST_S))
            outer = self.RINGS[-1][0] * grow
            for y in range(cy - 5, cy + 6):
                for x in range(cx - 5, cx + 6):
                    d = math.hypot(x - cx, y - cy) * (self.RINGS[-1][0] / outer if outer > 0.01 else 99)
                    for r, rgb in self.RINGS:
                        if d < r:
                            twinkle = 0.85 + 0.15 * math.sin(e * 9 + x * 1.7 + y * 2.3)
                            self._put(out, x, y, tuple(int(c * twinkle) for c in rgb))
                            break
            return
        # Shattered: sparks flying out from the centre and falling, dimming as they go.
        s = e - self.hit_s
        if s >= self.SHATTER_S:
            return
        fade = 1 - s / self.SHATTER_S
        for i in range(self.SPARKS):
            a = 2 * math.pi * i / self.SPARKS
            speed = 9 + 5 * ((i * 7) % 3)
            x = cx + 0.5 + math.cos(a) * speed * s
            y = cy + 0.5 + math.sin(a) * speed * s + 10 * s * s
            rgb = self.RINGS[i % len(self.RINGS)][1]  # in the target's own colours
            self._put(out, x, y, tuple(int(c * fade) for c in rgb))

    def arrow_tail(self, e):
        """How far along her aim the arrow's tail is from the string e seconds in (None before the release
        or once it's struck)."""
        if not self.LOOSE_S <= e < self.hit_s:
            return None
        return self.flown(e - self.LOOSE_S)

    def draw_arrow(self, out, e):
        """The loosed arrow along her aim, off the string from where it sat: a fading white wake behind its
        red fletching, a pale shaft, a white head."""
        d = self.arrow_tail(e)
        if d is None:
            return
        (nx, ny), (ux, uy) = self.nock, self.aim
        for i in range(1, self.TRAIL):
            if d - i > 0:
                g = int(230 * (1 - i / self.TRAIL))
                self._put(out, nx + ux * (d - i), ny + uy * (d - i), (g, g, g))
        for (x, y), i in poses.arrow_cells((nx + ux * d, ny + uy * d), poses.AIM):
            rgb = Archer.TIP_RGB if i == Archer.ARROW_LEN - 1 else Archer.FLETCH_RGB if i < 3 else Archer.SHAFT_RGB
            self._put(out, x, y, rgb)
