import math
import random

from display.animation.drawing import paint
from display.animation.motion import ease_out


class BaymaxReveal:
    """
    Baymax inflates up from the bottom edge over the already-revealed screen,
    settles with a wobble, blinks and waves, then deflates away. Unlike the other
    characters he is drawn procedurally rather than from ASCII art: inflating means
    scaling him smoothly from a flat puddle to full size, and fixed art can only be
    scaled in whole-pixel steps, which reads as popping rather than filling with air.
    """

    over_screen = True
    INFLATE_S, HOLD_S, DEFLATE_S = 0.9, 2.2, 0.7
    duration = INFLATE_S + HOLD_S + DEFLATE_S

    WHITE = (250, 250, 252)
    SHADE = (150, 158, 172)
    EDGE = (86, 92, 108)
    DARK = (12, 12, 16)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        # Full-size half-width/half-height of each part, in pixels, at inflation 1.0.
        # Height drives every radius so his proportions are identical on a 32- and a
        # 64-row board; he just fills less of the width on the short one. Width only
        # clamps him, so a narrow board can't push his arms off the edge.
        unit = min(height * 0.95, width * 0.88)
        self.body_ry = unit * 0.33
        self.body_rx = unit * 0.26
        self.head_rx = self.body_rx * 0.82
        self.head_ry = self.body_ry * 0.50
        self.cx = width / 2.0

    def inflation(self, t):
        """0 (a flat deflated puddle) up to 1 (full size), wobbling as he settles."""
        if t < self.INFLATE_S:
            return 0.06 + 0.94 * ease_out(t / self.INFLATE_S)
        if t < self.INFLATE_S + self.HOLD_S:
            since = t - self.INFLATE_S
            # A decaying overshoot right after he fills, then a slow idle breath.
            wobble = math.exp(-since * 3.2) * 0.10 * math.sin(since * 11.0)
            breathe = 0.012 * math.sin(since * 2.0)
            return 1.0 + wobble + breathe
        deflating = (t - self.INFLATE_S - self.HOLD_S) / self.DEFLATE_S
        return max(0.0, 1.0 - ease_out(deflating))

    def eye_open(self, t):
        """1 wide open, 0 fully shut — a slow blink every couple of seconds."""
        since = t - self.INFLATE_S
        if since < 0:
            return 1.0
        phase = since % 2.0
        return abs(phase - 0.08) / 0.08 if phase < 0.16 else 1.0

    def wave(self, t):
        """-1..1 for his raised right arm, 0 when it is back at his side."""
        since = t - self.INFLATE_S - 0.35
        if since < 0 or since > 1.6:
            return 0.0
        return math.sin(since * 7.0)

    def _blob(self, px, cx, cy, rx, ry, shade=True):
        """One filled ellipse, rimmed and shaded so it reads as soft, not as a slab."""
        if rx < 0.7 or ry < 0.7:
            return
        for y in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
            for x in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d > 1.0:
                    continue
                # A grey rim all round, and a grey crescent inside the lower right,
                # which gives him a light source instead of a flat white silhouette.
                if d > 0.82:
                    px[(x, y)] = self.EDGE
                elif shade and d > 0.52 and dx + dy > 0.55:
                    px[(x, y)] = self.SHADE
                else:
                    px[(x, y)] = self.WHITE

    def _face(self, px, cy, rx, open_frac):
        """Two small dark eyes joined by a single 1px line — the instantly-Baymax bit."""
        fy = int(round(cy))
        er = max(1, int(round(rx * 0.12)))
        # Keep a clear white gap between the eyes, or the face smears into one bar.
        eye_dx = max(er + 3, int(round(rx * 0.44)))
        lx, rx_ = int(round(self.cx)) - eye_dx, int(round(self.cx)) + eye_dx
        for x in range(lx, rx_ + 1):
            px[(x, fy)] = self.DARK
        # A blink squashes the eyes vertically; the line between them stays put.
        eh = max(0, int(round((er + 1) * open_frac)))
        for ex in (lx, rx_):
            for dy in range(-eh, eh + 1):
                for dx in range(-er, er + 1):
                    if (dx / er) ** 2 + (dy / max(1, eh)) ** 2 <= 1.0:
                        px[(ex + dx, fy + dy)] = self.DARK

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        inf = self.inflation(t)
        if inf <= 0.02:
            return True
        # Parts are drawn into a dict first so later blobs paint over earlier ones
        # (arms behind body, face over head) before anything reaches the canvas.
        px = {}
        # His base stays pinned to the bottom edge and he grows upward from it,
        # which is what sells air going in rather than a sprite sliding up.
        body_ry = self.body_ry * inf
        # Deflated he is wide and flat; inflated he is nearly round.
        squash = 1.0 + 0.55 * (1.0 - min(1.0, inf))
        body_rx = self.body_rx * (0.35 + 0.65 * inf) * squash
        body_cy = self.height - body_ry

        head_ry = self.head_ry * inf
        head_rx = self.head_rx * (0.4 + 0.6 * inf) * squash
        # The head overlaps the body just enough to fuse into one soft mass while
        # leaving the whole face clear of the shoulders.
        head_cy = body_cy - body_ry - head_ry * 0.62

        arm_ry, arm_rx = body_ry * 0.46, body_rx * 0.36
        w = self.wave(t)
        for side in (-1, 1):
            ax = self.cx + side * body_rx * 0.92
            ay = body_cy - body_ry * 0.25
            if side == 1 and w:
                ay -= arm_ry * 1.1 * abs(w)
                ax += arm_rx * 0.5 * w
            self._blob(px, ax, ay, arm_rx, arm_ry)

        self._blob(px, self.cx, body_cy, body_rx, body_ry)
        # The head takes no interior shading: the face needs a clean white field
        # behind it or the eyes and line smear into grey at this resolution.
        self._blob(px, self.cx, head_cy, head_rx, head_ry, shade=False)
        if head_rx >= 3.0 and head_ry >= 1.5:
            # Centre the face on the part of the head that clears the body, not on
            # the head ellipse, whose lower half is buried in the shoulders.
            self._face(px, (head_cy - head_ry + body_cy - body_ry) / 2, head_rx, self.eye_open(t))

        paint(canvas, px, self.width, self.height)
        return True
