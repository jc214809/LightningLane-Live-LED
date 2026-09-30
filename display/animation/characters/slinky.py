import math
import random

from display.animation.drawing import _blackout, art_pixels, paint
from display.animation.motion import ease_out


class SlinkyReveal:
    """
    Slinky Dog stretched from one side of the board to the other: his rear sits on the
    left edge while his front half walks right until his nose reaches the right edge,
    pulling his spring out across the whole board. He holds there, then the rear snaps
    across to catch up and both halves bound off the right edge.

    The new screen is revealed behind his front half as it walks, so the spring and rear
    are drawn over it; ahead of him the board stays dark.
    """
    STRETCH_S, HOLD_S, SNAP_S, EXIT_S = 1.3, 0.5, 0.35, 0.55
    duration = STRETCH_S + HOLD_S + SNAP_S + EXIT_S

    # Front half facing right: long dark ear down the back of his head, big eye,
    # tan muzzle out front ending in a black nose, chest and two front legs.
    FRONT_ART = [
        "....KKKKKK......",
        "...KBBBBBBK.....",
        "..KBBBBBBBBK....",
        ".KDKBEEBEEBBK...",
        "KDDKBEPBEPBBBKK.",
        "KDDKBEPBEPBTTTTK",
        "KDDKBBBBBBTTTTNK",
        "KDDDKBBBBTTTTTNK",
        "KDDDKBBBTTTTMMK.",
        ".KDDKKBBTTTTTK..",
        ".KDDK.KBBBBBK...",
        "..KK..KBBBBBK...",
        "....KKBTTTBBBK..",
        "...KBBTTTTBBBK..",
        "...KBBBTTBBBBK..",
        "...KBBBBBBBBBK..",
        "...KBBKKKKBBBK..",
        "...KBBK..KBBK...",
        "...KTTK..KTTK...",
        "...KKKK..KKKK...",
    ]
    # Rear half: round rump, two back legs, and a coiled spring tail curling up.
    REAR_ART = [
        "SWS.........",
        ".SWS........",
        "..SWS.......",
        "...KKKKKKK..",
        "..KBBBBBBBK.",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBKKKKBBBK",
        ".KBBK..KBBK.",
        ".KTTK..KTTK.",
        ".KKKK..KKKK.",
    ]
    COLORS = {
        "K": (70, 40, 18), "B": (176, 108, 48), "D": (100, 58, 26), "T": (238, 200, 140),
        "N": (18, 14, 14), "E": (248, 246, 240), "P": (30, 22, 20), "M": (160, 50, 45),
        "S": (215, 220, 230), "W": (120, 128, 142),
    }
    COIL_FRONT, COIL_BACK = (215, 220, 230), (110, 118, 132)
    COILS = 11
    # 1x on both boards: doubled, the two halves eat the 64x64 board and the spring can't stretch.
    SCALE = 1

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.scale = self.SCALE
        s = self.scale
        self.front_w, self.front_h = len(self.FRONT_ART[0]) * s, len(self.FRONT_ART) * s
        self.rear_w, self.rear_h = len(self.REAR_ART[0]) * s, len(self.REAR_ART) * s
        self.ground = height  # feet stand on the bottom row
        self.spring_y = self.ground - 7 * s  # the coil runs through both bodies
        self.coil_h = 7 * s
        self.home_rear = 0
        self.min_gap = 3 * s  # a squashed spring between the halves
        self.far_front = width - self.front_w

    def rear_x(self, t):
        snap_at = self.STRETCH_S + self.HOLD_S
        if t < snap_at:
            return self.home_rear
        caught = self.far_front - self.min_gap - self.rear_w
        if t < snap_at + self.SNAP_S:
            p = (t - snap_at) / self.SNAP_S
            return self.home_rear + (caught - self.home_rear) * ease_out(p)
        return caught + self._exit(t)

    def front_x(self, t):
        start = self.home_rear + self.rear_w + self.min_gap
        if t < self.STRETCH_S:
            # Walks out, easing to a stop with his nose at the right edge.
            return start + (self.far_front - start) * ease_out(t / self.STRETCH_S)
        return self.far_front + self._exit(t)

    def _exit(self, t):
        begin = self.STRETCH_S + self.HOLD_S + self.SNAP_S
        p = max(0.0, (t - begin) / self.EXIT_S)
        return p * p * (self.width + self.rear_w + self.min_gap)

    def bob(self, t):
        """A small step-bounce while the front half walks."""
        if t >= self.STRETCH_S:
            return 0
        return -round(abs(math.sin(t * math.pi * 6)) * self.scale)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        fx, rx = self.front_x(t), self.rear_x(t)
        _blackout(canvas, int(fx + self.front_w * 0.5), self.width, self.height)
        self._draw_spring(canvas, rx + self.rear_w - 2 * self.scale, fx + 4 * self.scale)
        self._draw(canvas, self.REAR_ART, rx, self.ground - self.rear_h)
        self._draw(canvas, self.FRONT_ART, fx, self.ground - self.front_h + self.bob(t))
        return True

    def _draw_spring(self, canvas, x0, x1):
        """
        A row of tilted rings: each coil's back arc in shadow, its front arc bright on
        top. Squashed, the rings overlap into a solid banded tube; stretched, they
        separate into loops you can count.
        """
        if x1 <= x0:
            return
        ry = self.coil_h / 2
        step = (x1 - x0) / self.COILS
        rx = max(1.0, min(step * 0.55, 2.5 * self.scale))
        steps = 8 * self.coil_h
        for front, colour in ((False, self.COIL_BACK), (True, self.COIL_FRONT)):
            for i in range(self.COILS + 1):
                cx = x0 + i * step
                for k in range(steps + 1):
                    a = math.pi * k / steps - math.pi / 2  # top to bottom
                    dx = math.cos(a) * rx
                    x = cx + (dx if front else -dx)
                    # The ring leans: its top sits a little behind its bottom.
                    x += (math.sin(a)) * rx * 0.6
                    self._px(canvas, x, self.spring_y + math.sin(a) * ry, colour)

    def _px(self, canvas, x, y, rgb):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)

    def _draw(self, canvas, art, x0, y0):
        paint(canvas, art_pixels(art, int(round(x0)), int(round(y0)), self.COLORS, self.scale),
              self.width, self.height)


class SlinkyWrapReveal:
    """
    A surprise over a ride screen: Slinky walks in along the bottom, his rear stops in
    the bottom-right corner, and his front half keeps going off the right edge. After a
    random pause his front peeks back in at the top-left, as if the spring ran around
    behind the board. He looks down at his own rear, which wags its tail; then his front
    walks across the top, and his rear follows the same way round: off the right edge at
    the bottom, back in at the top-left, catching up behind him. Then the whole dog walks
    off the right edge.

    No blackout: the ride screen stays readable, and keeps animating, underneath him.
    """

    over_screen = True
    WALK_IN_S, WALK_OFF_S, PEEK_S, LOOK_S = 0.8, 0.5, 0.4, 0.6
    CROSS_S, FOLLOW_S, EXIT_S = 0.7, 0.9, 0.5
    FOLLOW_OUT = 0.4  # share of the follow spent leaving the bottom-right; the rest re-entering
    PAUSE_S = (1.0, 3.0)
    # The longest visit; each one rolls its own pause. With the 0.55s sweep it fits
    # inside the 8s ride screen.
    duration = WALK_IN_S + WALK_OFF_S + PEEK_S + LOOK_S + CROSS_S + FOLLOW_S + EXIT_S + PAUSE_S[1]

    FRONT_ART = SlinkyReveal.FRONT_ART
    REAR_ART = SlinkyReveal.REAR_ART
    COLORS = SlinkyReveal.COLORS
    COIL_FRONT, COIL_BACK = SlinkyReveal.COIL_FRONT, SlinkyReveal.COIL_BACK
    # His front half with the pupils dropped to the bottom-right of each eye: looking
    # down at his rear in the opposite corner.
    FRONT_LOOK_ART = [
        "....KKKKKK......",
        "...KBBBBBBK.....",
        "..KBBBBBBBBK....",
        ".KDKBEEBEEBBK...",
        "KDDKBEEBEEBBBKK.",
        "KDDKBEPBEPBTTTTK",
        "KDDKBBBBBBTTTTNK",
        "KDDDKBBBBTTTTTNK",
        "KDDDKBBBTTTTMMK.",
        ".KDDKKBBTTTTTK..",
        ".KDDK.KBBBBBK...",
        "..KK..KBBBBBK...",
        "....KKBTTTBBBK..",
        "...KBBTTTTBBBK..",
        "...KBBBTTBBBBK..",
        "...KBBBBBBBBBK..",
        "...KBBKKKKBBBK..",
        "...KBBK..KBBK...",
        "...KTTK..KTTK...",
        "...KKKK..KKKK...",
    ]
    # His rear with the spring tail swung forward over his back: alternated with
    # REAR_ART it wags.
    REAR_WAG_ART = [
        ".....SWS....",
        "....SWS.....",
        "...SWS......",
        "...KKKKKKK..",
        "..KBBBBBBBK.",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBBBBBBBBK",
        ".KBBKKKKBBBK",
        ".KBBK..KBBK.",
        ".KTTK..KTTK.",
        ".KKKK..KKKK.",
    ]
    SCALE = 1
    COILS = 11
    STUB_COILS = 2  # coils showing beside each piece while the spring is round the back

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        rng = rng or random.Random()
        s = self.scale = self.SCALE
        self.front_w, self.front_h = len(self.FRONT_ART[0]) * s, len(self.FRONT_ART) * s
        self.rear_w, self.rear_h = len(self.REAR_ART[0]) * s, len(self.REAR_ART) * s
        self.gap = 3 * s
        self.coil_step = 3 * s  # ring spacing on the stubs that run off an edge
        self.coil_h = 7 * s
        self.bottom = height  # ground lines: feet on the bottom row, or under the top-left peek
        self.top = self.front_h
        self.rear_home = width - self.rear_w - self.STUB_COILS * self.coil_step
        # One extra step: the ring nearest the left edge is half cut off by it.
        self.peek_x = (self.STUB_COILS + 1) * self.coil_step - 4 * s
        self.pause = rng.uniform(*self.PAUSE_S)
        self.duration = self.visit_s()
        b = [self.WALK_IN_S, self.WALK_OFF_S, self.pause, self.PEEK_S, self.LOOK_S,
             self.CROSS_S, self.FOLLOW_S, self.EXIT_S]
        self.beats = [sum(b[:i + 1]) for i in range(len(b))]

    def visit_s(self):
        return (self.WALK_IN_S + self.WALK_OFF_S + self.pause + self.PEEK_S + self.LOOK_S
                + self.CROSS_S + self.FOLLOW_S + self.EXIT_S)

    def phase(self, t):
        """(name, 0..1 progress through it) for time t."""
        names = ("walk_in", "walk_off", "pause", "peek", "look", "cross", "follow", "exit")
        start = 0.0
        for name, end in zip(names, self.beats):
            if t < end:
                return name, (t - start) / (end - start)
            start = end
        return "done", 1.0

    def pose(self, t):
        """
        Where both halves are: {"front": (x, ground) or None, "rear": (x, ground)}, where
        ground is the row under his feet. The front is None while it's off the board.
        """
        name, p = self.phase(t)
        W = self.width
        cross_end = W - self.front_w
        landed = cross_end - self.gap - self.rear_w
        if name == "walk_in":
            rear = -self.rear_w - self.gap - self.front_w + (self.rear_home + self.rear_w + self.gap + self.front_w) * ease_out(p)
            return {"rear": (rear, self.bottom), "front": (rear + self.rear_w + self.gap, self.bottom)}
        if name == "walk_off":
            start = self.rear_home + self.rear_w + self.gap
            return {"rear": (self.rear_home, self.bottom), "front": (start + (W - start) * p * p, self.bottom)}
        if name == "pause":
            return {"rear": (self.rear_home, self.bottom), "front": None}
        if name == "peek":
            return {"rear": (self.rear_home, self.bottom),
                    "front": (-self.front_w + (self.peek_x + self.front_w) * ease_out(p), self.top)}
        if name == "look":
            return {"rear": (self.rear_home, self.bottom), "front": (self.peek_x, self.top)}
        if name == "cross":
            return {"rear": (self.rear_home, self.bottom),
                    "front": (self.peek_x + (cross_end - self.peek_x) * ease_out(p), self.top)}
        if name == "follow":
            # The rear goes the way his front went: off the right edge along the bottom...
            if p < self.FOLLOW_OUT:
                q = p / self.FOLLOW_OUT
                return {"rear": (self.rear_home + (W - self.rear_home) * q * q, self.bottom),
                        "front": (cross_end, self.top)}
            # ...then back in from the left along the top, catching up behind him.
            q = (p - self.FOLLOW_OUT) / (1 - self.FOLLOW_OUT)
            x = -self.rear_w + (landed + self.rear_w) * ease_out(q)
            return {"rear": (x, self.top), "front": (cross_end, self.top)}
        if name == "exit":
            dx = p * p * (W + self.rear_w)
            return {"rear": (landed + dx, self.top), "front": (cross_end + dx, self.top)}
        return {"rear": (W, self.top), "front": (W, self.top)}

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        name, _ = self.phase(t)
        pose, s = self.pose(t), self.scale
        rx, rg = pose["rear"]
        rear_art = self.REAR_WAG_ART if name == "look" and int(t * 8) % 2 else self.REAR_ART
        walking = name in ("walk_in", "walk_off", "cross", "follow", "exit")
        bob = -round(abs(math.sin(t * math.pi * 6)) * s) if walking else 0
        rear_attach = (rx + self.rear_w - 2 * s, rg - 7 * s)
        # Split while the rear is still on the bottom: until it re-enters at the top-left.
        split = name in ("pause", "peek", "look", "cross") or (name == "follow" and rg == self.bottom)
        if split:
            # The spring runs off the right edge from his rear, and back in from the left
            # edge to his front: the middle of it is round the back of the board.
            self._spring(canvas, rear_attach, (self.width + self.coil_step, rear_attach[1]), self.coil_step)
            if pose["front"]:
                fx, fg = pose["front"]
                self._spring(canvas, (-self.coil_step, fg - 7 * s), (fx + 4 * s, fg - 7 * s), self.coil_step)
        elif pose["front"]:
            fx, fg = pose["front"]
            span = max(1.0, fx + 4 * s - rear_attach[0])
            self._spring(canvas, rear_attach, (fx + 4 * s, fg - 7 * s),
                         max(1.5 * s, min(span / self.COILS, 3.5 * s)))
        self._draw(canvas, rear_art, rx, rg - self.rear_h)
        if pose["front"]:
            fx, fg = pose["front"]
            art = self.FRONT_LOOK_ART if name == "look" else self.FRONT_ART
            self._draw(canvas, art, fx, fg - self.front_h + bob)
        return True

    def _spring(self, canvas, a, b, step):
        """Tilted rings every `step` pixels from a to b: shaded backs, then bright fronts."""
        (x0, y0), (x1, y1) = a, b
        length = math.hypot(x1 - x0, y1 - y0)
        if length <= 0:
            return
        count = max(1, int(length / step))
        ry = self.coil_h / 2
        rx = max(1.0, min(step * 0.55, 2.5 * self.scale))
        steps = 8 * self.coil_h
        for front, colour in ((False, self.COIL_BACK), (True, self.COIL_FRONT)):
            for i in range(count + 1):
                f = i / count
                cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                for k in range(steps + 1):
                    ang = math.pi * k / steps - math.pi / 2
                    dx = math.cos(ang) * rx
                    x = cx + (dx if front else -dx) + math.sin(ang) * rx * 0.6
                    self._px(canvas, x, cy + math.sin(ang) * ry, colour)

    def _px(self, canvas, x, y, rgb):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)

    def _draw(self, canvas, art, x0, y0):
        paint(canvas, art_pixels(art, int(round(x0)), int(round(y0)), self.COLORS, self.scale),
              self.width, self.height)
