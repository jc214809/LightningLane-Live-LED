import math
import random

from display.animation.drawing import art_pixels, paint
from display.animation.mechanics import CapturesScreens
from display.animation.motion import ease_out, progress
from display.motion import smooth
from display.pixels import blend, set_pixel


class ArmyMenReveal(CapturesScreens):
    """
    Three green army men parachute in, the way Andy's toys drop in on a mission. Each
    hangs under a camo canopy on rigging lines that swing like a pendulum as he falls, and
    the new screen is uncovered top-down in step with the lead soldier's feet, like a
    curtain coming down with him. They touch down one after another, each with a puff of
    dust off his base; each chute deflates and slumps to the ground downwind behind him.
    Then all three hop off the right edge in step on their bases, as they move in the
    films (the toys can't walk, their feet are molded to the base).

    Needs both the old screen (visible below the curtain) and the new one (uncovered above
    it), so it opts into both wants_prev and wants_new, the first transition to need both.
    Nothing else on the board reveals top-down.

    Stays 1x on both boards: three at 2x collide and clip the edges of 64x64.
    """

    wants_prev = True
    wants_new = True
    SCALE = 1
    FALL_S = 0.8  # each soldier's time in the air, from above the board to touchdown
    # 64x64 is twice the drop: at 0.8s they plummeted. Longer, but still a touch quicker
    # per row than on 64x32, which reads right there.
    FALL_S_TALL = 1.3
    COLLAPSE_S = 0.6  # a landed chute deflating and slumping to the ground
    DUST_S = 0.35  # a landing puff, from kick-up to gone
    LAND_S = 0.45  # everyone holds, after the last lands, before the hop-off
    HOPS, HOP_S = 4, 0.32  # the hop-off: hops across and the time for each
    MARCH_S = HOPS * HOP_S
    SWAY_HZ = 1.1  # pendulum swings per second while falling

    # Each soldier: (x as a fraction of the board width, delay before he starts falling).
    # Staggered delays land them one after another, left to right.
    UNITS = [(0.18, 0.0), (0.5, 0.17), (0.82, 0.34)]
    DROP_S = max(delay for _, delay in UNITS) + FALL_S  # the last touchdown
    duration = DROP_S + LAND_S + MARCH_S

    # The camo canopy from the reference: an olive dome with gold patches and a dark
    # roundel carrying a white star. Its own keys so it never shares the soldier's greens.
    # '.' empty, C rim, N canopy olive, O gold patch, M roundel, * star.
    CANOPY_ART = [
        ".....CCCCC.....",
        "...CCNNNNNCC...",
        "..COOMM*MMNNC..",
        ".COOMM***MMNOC.",
        ".CNM*******MOC.",
        "CNNMM*****MMNNC",
        "CNOOM**M**MOONC",
        "COOOM*MMM*MOOOC",
        "CCCCCCCCCCCCCCC",
    ]
    # Where the rigging lines leave the hem (columns of the canopy's last row).
    RIG_COLS = (1, 4, 10, 13)

    # A green army man, front-on, in bright toy-plastic green: helmet with a dark brim
    # shading his face, rifle held across his chest and poking out past his shoulder and
    # hip (the only way it reads at this size), legs apart, feet on the molded base.
    # '.' empty, K outline, L highlight, G plastic, D shade, R rifle over his body,
    # S rifle against the sky, B base.
    SOLDIER_ART = [
        "....KKK.....",
        "...KLLGK....",
        "..KLGGGDK...",
        ".KDDDDDDDK.S",
        "..KGDGDDK.S.",
        "...KGGDKSS..",
        "..KLGGGRK...",
        ".KLGGGRGDK..",
        ".KLGGRGGDK..",
        ".KLGRGGGDK..",
        ".KRRGGGGDK..",
        ".SKGGKGGDK..",
        "SKGGK.KGDK..",
        ".KLGK.KGDK..",
        "KBBBBBBBBBK.",
        ".KKKKKKKKK..",
    ]
    HELMET_COL = 5  # his centre line: the rigging meets above it
    BASE_COLS = (0, 10)  # the base's two ends, where landing dust kicks out

    COLORS = {
        "C": (22, 34, 16), "N": (72, 110, 45), "O": (170, 145, 60), "M": (40, 62, 28),
        "*": (250, 250, 240),
        "K": (12, 50, 16), "L": (140, 215, 100), "G": (70, 165, 60), "D": (35, 105, 38),
        "R": (20, 68, 24), "S": (60, 140, 55), "B": (45, 120, 45),
    }
    RIG_RGB = (170, 170, 160)
    DUST_RGB = (190, 170, 120)
    RIG_GAP = 5  # rows between the canopy's hem and the top of his helmet

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = s = self.SCALE
        self.canopy_w, self.canopy_h = len(self.CANOPY_ART[0]) * s, len(self.CANOPY_ART) * s
        self.soldier_w, self.soldier_h = len(self.SOLDIER_ART[0]) * s, len(self.SOLDIER_ART) * s
        if height >= 64:
            self.FALL_S = self.FALL_S_TALL
            self.DROP_S = max(delay for _, delay in self.UNITS) + self.FALL_S
            self.duration = self.DROP_S + self.LAND_S + self.MARCH_S
        self.unit_h = self.canopy_h + self.RIG_GAP * s + self.soldier_h
        self.ground_top = height - self.soldier_h  # his top row once he's standing
        # The hop-off carries the leftmost soldier's whole sprite past the right edge.
        left = min(int(f * width) for f, _ in self.UNITS)
        self.march_dist = width - left + self.soldier_w
        self.prev_px = {}
        self.new_px = {}
        # Each soldier swings on his own phase so the three never sway in lockstep.
        self.sway_phase = [self.rng.uniform(0, 2 * math.pi) for _ in self.UNITS]

    # --- timing -------------------------------------------------------------------

    def _unit_land_time(self, delay):
        """When this soldier's base touches the ground."""
        return delay + self.FALL_S

    def _fall(self, delay, t):
        """0 before he starts falling, 1 at touchdown."""
        return progress(t, delay, delay + self.FALL_S)

    def _soldier_top(self, delay, t):
        """
        Top of his helmet: from just above the board down to standing on the bottom row.
        A parachute falls at a near-steady rate, so this only eases a little at the end
        rather than racing down and crawling in.
        """
        p = self._fall(delay, t)
        start = -self.soldier_h
        return start + (1 - (1 - p) ** 2) * (self.ground_top - start)

    def _sway(self, i, delay, t):
        """
        (canopy offset, soldier offset) for the pendulum: the canopy leads and the
        soldier trails it by a fraction of a swing, so the rigging tilts. The swing dies
        away over the last quarter of the fall so he lands upright.
        """
        p = self._fall(delay, t)
        amp = 2.0 * self.scale * min(1.0, (1 - p) / 0.25)
        a = self.sway_phase[i] + t * self.SWAY_HZ * 2 * math.pi
        return amp * math.sin(a), amp * 0.4 * math.sin(a - 0.9)

    def _curtain_y(self, t):
        """
        How far down the new screen is uncovered, 0 to height: the lead soldier's feet,
        so the board uncovers only what he's fallen past.
        """
        lead = min(delay for _, delay in self.UNITS)
        feet = self._soldier_top(lead, t) + self.soldier_h
        return max(0, min(self.height, int(feet)))

    def _march_start(self):
        return self.DROP_S + self.LAND_S

    def _hop(self, t):
        """
        (x offset, lift) for the hop-off, the same for all three so they move in step:
        HOPS hops, each easing across and arcing up HOP_H, landing flat between them.
        """
        since = t - self._march_start()
        if since <= 0:
            return 0, 0
        k, p = divmod(since / self.HOP_S, 1.0)
        if k >= self.HOPS:
            return self.march_dist, 0
        step = self.march_dist / self.HOPS
        eased = smooth(p)
        lift = 4 * p * (1 - p) * 4 * self.scale
        return int((k + eased) * step), int(round(lift))

    def _march_x(self, t):
        return self._hop(t)[0]

    def _last_hop_landing(self, t):
        """Seconds since his base last came down in the hop-off, or None mid-air/before."""
        since = t - self._march_start()
        if since <= 0:
            return None
        k, p = divmod(since / self.HOP_S, 1.0)
        if k < 1 or k > self.HOPS:
            return None
        return p * self.HOP_S

    # --- drawing -----------------------------------------------------------------

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        self._cy = self._curtain_y(t)
        for (x, y), rgb in self.new_px.items():
            if y < self._cy:
                canvas.SetPixel(x, y, *rgb)
        # Below the curtain, every pixel is the old screen's, black included: show_screen
        # has already drawn the new screen underneath, and it mustn't show through.
        for y in range(self._cy, self.height):
            for x in range(self.width):
                canvas.SetPixel(x, y, *self.prev_px.get((x, y), (0, 0, 0)))

        march, lift = self._hop(t)
        hop_age = self._last_hop_landing(t)
        # Slumped chutes lie on the ground behind the soldiers, so draw them all first.
        for i, (frac, delay) in enumerate(self.UNITS):
            since = t - self._unit_land_time(delay)
            if 0 <= since < self.COLLAPSE_S:
                self._draw_collapsing_chute(canvas, int(frac * self.width), since / self.COLLAPSE_S)
        for i, (frac, delay) in enumerate(self.UNITS):
            home = int(frac * self.width)
            since = t - self._unit_land_time(delay)
            if since < 0:
                canopy_dx, soldier_dx = self._sway(i, delay, t)
                top = int(round(self._soldier_top(delay, t)))
                self._draw_hanging(canvas, home + canopy_dx, home + soldier_dx, top)
            else:
                x = home + march
                self._draw_soldier(canvas, x, self.ground_top - lift)
                if since < self.DUST_S:
                    self._draw_dust(canvas, x, since / self.DUST_S, 1.0)
                elif hop_age is not None and hop_age < self.DUST_S * 0.7:
                    self._draw_dust(canvas, x, hop_age / (self.DUST_S * 0.7), 0.6)
        return True

    def _draw_hanging(self, canvas, canopy_cx, soldier_cx, soldier_top):
        """A falling soldier: canopy, rigging converging above his helmet, and him."""
        s = self.scale
        cx0 = int(round(canopy_cx)) - self.canopy_w // 2
        hem_y = soldier_top - self.RIG_GAP * s
        canopy_top = hem_y - self.canopy_h
        scx = int(round(soldier_cx))
        # The lines meet in a riser just above his helmet, as in the reference photo.
        meet = (scx, soldier_top - 2 * s)
        for col in self.RIG_COLS:
            self._line(canvas, cx0 + col * s, hem_y, meet[0], meet[1], self.RIG_RGB)
        self._line(canvas, meet[0], meet[1], scx, soldier_top - 1, self.RIG_RGB)
        self._blit(canvas, self.CANOPY_ART, cx0, canopy_top)
        self._draw_soldier(canvas, scx, soldier_top)

    def _draw_soldier(self, canvas, cx, top):
        self._blit(canvas, self.SOLDIER_ART, cx - self.HELMET_COL * self.scale, top)

    def _draw_collapsing_chute(self, canvas, home, p):
        """
        The landed chute losing its air: it blows downwind (the way they'll hop off),
        sinks behind him, flattens and spreads into a heap on the ground, then fades.
        """
        s = self.scale
        eased = ease_out(p)
        w = int(self.canopy_w * (1 + 0.2 * eased))
        h = max(2 * s, int(self.canopy_h * (1 - 0.75 * eased)))
        cx = home + int(7 * s * eased)
        landed_top = self.ground_top - self.RIG_GAP * s - self.canopy_h
        ground_heap = self.height - h
        top = int(round(landed_top + (ground_heap - landed_top) * eased))
        fade = 1.0 if p < 0.5 else 1 - (p - 0.5) / 0.5
        # Crumpled, the star is folded away: squashed, it would sample into a white bar.
        slumped = [row.replace("*", "M") for row in self.CANOPY_ART]
        self._blit_scaled(canvas, slumped, cx - w // 2, top, w, h, fade)

    def _draw_dust(self, canvas, cx, p, size):
        """A puff kicked out sideways from both ends of his base, spreading and fading."""
        x0 = cx - self.HELMET_COL * self.scale
        ends = (x0 + self.BASE_COLS[0] * self.scale, x0 + self.BASE_COLS[1] * self.scale)
        spread = (0.6 + 1.4 * p) * size * self.scale
        rise = int(round(p * 1.5 * self.scale))
        alpha = 0.75 * (1 - p)
        ground = self.height - 1
        for side, end in zip((-1, 1), ends):
            for dx, dy in ((1, 0), (2, 0), (2, -1), (3, 0), (3, -1), (4, -1), (5, -2)):
                x = end + side * int(round(dx * spread))
                y = ground + dy * self.scale - rise
                self._px_blend(canvas, x, y, self.DUST_RGB, alpha)

    # --- pixels ------------------------------------------------------------------

    def _under(self, x, y):
        """What's on the board beneath (x, y): the new screen above the curtain, the old below."""
        return (self.new_px if y < self._cy else self.prev_px).get((x, y), (0, 0, 0))

    def _px_blend(self, canvas, x, y, rgb, alpha):
        """Draw rgb at alpha over the screen beneath: soft things mustn't punch black holes."""
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *blend(rgb, self._under(x, y), alpha))

    def _line(self, canvas, x0, y0, x1, y1, rgb):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self._px(canvas, x0, y0, rgb)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def _blit(self, canvas, art, x0, y0):
        paint(canvas, art_pixels(art, x0, y0, self.COLORS, self.scale), self.width, self.height)

    def _blit_scaled(self, canvas, art, x0, y0, target_w, target_h, alpha=1.0):
        """Nearest-neighbour scale of art into a target_w x target_h box, faded to alpha."""
        src_w, src_h = len(art[0]), len(art)
        for py in range(target_h):
            row = art[min(src_h - 1, py * src_h // target_h)]
            for px in range(target_w):
                kind = row[min(src_w - 1, px * src_w // target_w)]
                if kind != ".":
                    self._px_blend(canvas, x0 + px, y0 + py, self.COLORS[kind], alpha)

    def _px(self, canvas, x, y, rgb):
        set_pixel(canvas, x, y, rgb, self.width, self.height)
