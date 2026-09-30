"""
The Halloween-party jack-o'-lanterns: the scary one (triangle eyes, toothy grin) and
the friendly Mickey one built on it, which replaces Magic Kingdom's castle on party days.
"""

from datetime import datetime
import math

from utils.special_events import special_event_now

from display.landmarks.scene import Landmark
from display.motion import ramp, smooth


class ScaryJackOLanternLandmark(Landmark):
    """A scary Mickey-shaped jack-o'-lantern (triangle eyes, toothy grin) under a purple Halloween sky: it sits dark, then its
    candle catches and the carved face flickers, over a drifting green ground mist."""

    # The sweep takes 0.55s of the screen and the scene's clock starts with the wipe, leaving
    # 5.45s: dark, the candle catches (0.4-0.9s, while the wipe is still uncovering it), the wink
    # or hop, then the party's hours fade in and hold long enough to read.
    SCREEN_S = 6.0
    # The candle catches while the wipe is still uncovering it, rather than after.
    PLAYS_UNDER_WIPE = True
    STAR_SPACING = 2  # twice the other landmarks' stars: a clear Halloween night
    IGNITE_AT, IGNITE_S = 0.4, 0.5
    OUTLINE = (70, 24, 4)
    STEM = (60, 120, 40)
    GLOW_HOT, GLOW_EDGE = (255, 245, 170), (255, 205, 60)
    CUT_RIM = (55, 16, 2)
    CARVED_DARK = (22, 8, 2)

    def build(self):
        w, h = self.width, self.height
        self.R, self.cx, self.cy = self._layout()
        ear_r = self.R * 0.56
        ears = [(self.cx + dx * self.R, self.cy - self.R * 1.22, ear_r) for dx in (-0.95, 0.95)]
        self.sky = {}
        for y in range(h):
            p = y / (h - 1)
            rgb = (int(34 - 20 * p), int(6 + 2 * p), int(52 - 22 * p))
            for x in range(w):
                self.sky[(x, y)] = rgb
        self.shell = {}  # (x, y) -> full-brightness pumpkin colour
        for ex, ey, er in ears:
            self._paint_pumpkin(ex, ey, er)
        self._paint_pumpkin(self.cx, self.cy, self.R)
        self._paint_stem()
        self.carved = [(x, y) for x in range(w) for y in range(h) if self._is_carved(x, y)]
        carved = set(self.carved)
        for p in carved:
            self.shell.pop(p, None)
        # A dark cut wall around each carving keeps the glow from bleeding into the orange shell.
        for x, y in self.carved:
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in self.shell and n not in carved:
                    self.shell[n] = self.CUT_RIM
        self.flicker = [(self.rng.uniform(5, 9), self.rng.uniform(11, 17), self.rng.uniform(0, 6.3)) for _ in range(2)]
        self.mist = [(self.rng.uniform(0, w), self.rng.uniform(0.6, 1.4), self.rng.uniform(3, 7))
                     for _ in range(4)]

    def _layout(self):
        """Head radius and centre. Proportions follow the height so the pumpkin fills the board."""
        w, h = self.width, self.height
        r = h * 0.28
        return r, w / 2 - 0.5, h - 0.5 - r - h * 0.06

    def _paint_pumpkin(self, cx, cy, r):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, y - cy)
                if d > r:
                    continue
                if d > r - 1.2:
                    self.shell[(x, y)] = self.OUTLINE
                    continue
                u, v = (x - cx) / r, (y - cy) / r
                # Ribs: vertical grooves that bunch toward the sides like a real pumpkin's.
                angle = math.asin(max(-1.0, min(1.0, u / math.sqrt(max(1e-6, 1 - v * v)))))
                rib = 0.5 + 0.5 * math.cos(angle * 7)
                light = 0.62 + 0.38 * (1 - d / r) + 0.12 * (-u - v) / 2
                k = light * (0.72 + 0.28 * rib)
                self.shell[(x, y)] = (min(255, int(250 * k)), min(255, int(115 * k)), int(10 * k))

    def _paint_stem(self):
        s = self.R / 18
        top = self.cy - self.R
        for i in range(max(3, round(5 * s))):
            y = int(top) - i
            x = int(self.cx + i * 0.35)
            for dx in range(max(2, round(3 * s))):
                self.shell[(x + dx - 1, y)] = self.STEM if dx else (40, 85, 28)

    def _is_carved(self, x, y):
        """Triangle eyes, a triangle nose and a toothy grin, in head-relative coordinates."""
        u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
        for ex in (-0.4, 0.4):
            # Eyes: upward-pointing triangles, apex tilted toward the nose for a sly look.
            if -0.5 <= v <= -0.05:
                q = (v + 0.5) / 0.45
                apex = ex - 0.08 * (1 if ex > 0 else -1) * -1
                if abs(u - (apex + (ex - apex) * q)) <= 0.23 * q:
                    return True
        if 0.02 <= v <= 0.24 and abs(u) <= 0.12 * (v - 0.02) / 0.22:
            return True
        if abs(u) <= 0.66:
            m = 1 - (u / 0.66) ** 2
            top, bottom = 0.3 + 0.16 * m, 0.42 + 0.3 * m
            if top <= v <= bottom:
                if -0.3 <= u <= -0.14 and v <= top + 0.12:
                    return False  # a tooth hanging from the top lip
                if 0.14 <= u <= 0.3 and v >= bottom - 0.12:
                    return False  # a tooth standing on the bottom lip
                return True
        return False

    def frame(self, t):
        out = dict(self.sky)
        self.draw_stars(out, t)
        self.animate(out, t)
        return out

    def draw_stars(self, out, t):
        for x, y, phase in self.stars:
            level = 30 + int(40 * (1 + math.sin(t * 3 + phase)))
            out[(x, y)] = (level + 20, level + 15, level + 40)

    def _lit(self, t):
        """0 while the pumpkin sits dark, easing to 1 as the candle catches."""
        return smooth((t - self.IGNITE_AT) / self.IGNITE_S)

    def animate(self, out, t):
        self._draw_pumpkin(out, t)
        self._draw_mist(out, t)

    def _draw_pumpkin(self, out, t):
        lit = self._lit(t)
        # Flicker in -1..1. It mostly swells and shrinks the candle's hot spot; brightness only
        # dips a little, so the glow never sinks to the shell's orange.
        flicker = sum(0.5 * math.sin(t * a + ph) * math.sin(t * b) for a, b, ph in self.flicker)
        # The shell warms with the candle but stays well under the glow, so the carved face pops.
        shell_k = 0.3 + 0.52 * lit
        for (x, y), (r, g, b) in self.shell.items():
            out[(x, y)] = (int(r * shell_k), int(g * shell_k), int(b * shell_k))
        glow = lit * (0.94 + 0.06 * flicker)
        reach = self.R * (0.9 + 0.3 * flicker)
        hot_x, hot_y = self.cx, self.cy + self.R * 0.25
        for x, y in self.carved:
            near = max(0.0, 1 - math.hypot(x - hot_x, y - hot_y) / reach)
            base = tuple(e + (hc - e) * near for hc, e in zip(self.GLOW_HOT, self.GLOW_EDGE))
            out[(x, y)] = tuple(min(255, int(d + (c - d) * glow)) for c, d in zip(base, self.CARVED_DARK))

    # Two layers of ground mist: (height as a share of the board, wave number, speed, brightness).
    # The back layer is taller and dimmer and rolls left; the front one is lower and brighter and
    # rolls right, so the tops weave through each other.
    MIST_LAYERS = ((0.2, 0.17, -1.3, 0.4), (0.13, 0.26, 1.7, 0.6))
    MIST_RGB = (60, 150, 80)

    def _draw_mist(self, out, t):
        h, w = self.height, self.width
        for i, (depth, k, speed, strength) in enumerate(self.MIST_LAYERS):
            top_max = depth * h
            phase = self.mist[i][0]
            for x in range(w):
                # Two sine waves at different scales give a rolling, uneven top edge.
                wave = 0.55 + 0.35 * math.sin(k * x + speed * t + phase) \
                    + 0.15 * math.sin(2.3 * k * x - 1.7 * speed * t + 2 * phase)
                top = top_max * wave
                # Brighter and fainter wisps drift along the band, so it swirls rather than sits.
                swirl = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(0.6 * k * x + 1.4 * speed * t + phase + 1))
                for y in range(h - 1, max(-1, h - 2 - int(top)), -1):
                    rise = (h - 1 - y) / max(top, 1e-6)
                    if rise > 1:
                        break
                    a = strength * swirl * (1 - rise) ** 0.7
                    r, g, b = out.get((x, y), (0, 0, 0))
                    mr, mg, mb = self.MIST_RGB
                    out[(x, y)] = (min(255, int(r + mr * a)), min(255, int(g + mg * a)), min(255, int(b + mb * a)))


class FriendlyJackOLanternLandmark(ScaryJackOLanternLandmark):
    """The friendly Mickey pumpkin: ribbed ears and head, pie-cut eyes, an oval nose and an open
    smile with a pink tongue. Once the candle catches it either winks or hops, picked at random
    each showing unless MOTION pins one."""

    MOTIONS = ("wink", "bounce")
    MOTION = None
    GOLD, GHOST, ORANGE = (255, 200, 60), (175, 255, 170), (255, 130, 20)
    # The party's name: three lines over the pumpkin on 64x64, and a narrow column beside it
    # on 64x32.
    TITLE_TALL = (("MICKEY'S", GOLD), ("NOT-SO-SCARY", GHOST), ("HALLOWEEN PARTY", ORANGE))
    TITLE_SHORT = (("MICKEY'S", GOLD), ("NOT-SO-", GHOST), ("SCARY", GHOST), ("HALLOWEEN", ORANGE), ("PARTY", ORANGE))
    TITLE_ROW_H = 6
    TITLE_COLUMN_X = 18  # centre of the 64x32 text column: HALLOWEEN, the widest line, starts at x=0
    # The party's hours on 64x64: down in the mist either side of the pumpkin's base ("7PM" left,
    # "12AM" right), fading in slowly from the moment the wink or hop starts. (64x32: see JUMP_AT.)
    MIST_HOURS_FADE_S = 1.2
    HOURS_RGB = ORANGE
    GROOVE = (150, 52, 4)
    TONGUE = (225, 40, 110)
    TONGUE_DARK = (30, 6, 10)
    EYES = (-0.25, 0.25)
    EYE_V, EYE_HW, EYE_HH = -0.38, 0.15, 0.31
    WINK_AT, WINK_S = 1.4, 0.6
    HOP_AT, HOP_S = 1.1, 0.45
    # 64x32 tells its own story on a longer screen (5.95s of scene): the title holds to be read,
    # then the pumpkin jumps left in an arc and its ear shoves the title off the board, landing in
    # its place; "TONIGHT / 7PM TO / 12AM" fades in where the pumpkin was, and it winks once landed.
    SHORT_SCREEN_S = 6.5
    JUMP_AT, JUMP_S = 2.0, 0.8
    SHORT_WINK_AT = 3.0
    TONIGHT_AT, TONIGHT_FADE_S = 2.6, 0.8  # from the moment the pumpkin clears the right half
    TITLE_COLUMN_RIGHT = 37  # the text column's right edge: HALLOWEEN, its widest line, ends here

    def build(self):
        self.motion = self.MOTION or self.rng.choice(self.MOTIONS)
        self.short = self.height < 64
        if self.short:
            # The jump is its move; it winks after landing.
            self.motion, self.SCREEN_S = "wink", self.SHORT_SCREEN_S
        self.wink_at = self.SHORT_WINK_AT if self.short else self.WINK_AT
        self.hours = self._party_hours()
        super().build()
        # Where the jump lands: in the title's spot, its left ear just inside the board's edge.
        self.land_cx = self.R * self.EAR_REACH + 0.5
        tongue = set(p for p in self.carved if self._is_tongue(*p))
        self.tongue = sorted(tongue)
        self.carved = [p for p in self.carved if p not in tongue]
        self.eye_of = {}
        for x, y in self.carved:
            u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
            if v < -0.02:
                self.eye_of[(x, y)] = 0 if u < 0 else 1
        # Uncarved pumpkin under the winking eye and its cut rim, shown as the lid covers them.
        wink = [p for p, e in self.eye_of.items() if e == 1]
        rim = {(x + dx, y + dy) for x, y in wink for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        self.wink_rim = sorted(p for p in rim if p in self.shell and self.shell[p] == self.CUT_RIM)
        self.eye_skin = {p: self._shade(self.cx, self.cy, self.R, *p) for p in wink + self.wink_rim}

    def _shade(self, cx, cy, r, x, y, axis=(0.0, 1.0), grooves=(-1.0, -0.45, 0.45, 1.0)):
        """Pumpkin colour at (x, y): lit toward the upper left, with 1px grooves between the ribs.
        `axis` is the pumpkin's up-down direction, so tilted ears get grooves that follow them."""
        ax, ay = axis
        du, dv = x - cx, y - cy
        along, across = du * ax + dv * ay, du * ay - dv * ax
        d = math.hypot(du, dv)
        half = r * math.sqrt(max(0.0, 1 - (along / r) ** 2))
        light = 0.62 + 0.38 * (1 - d / r) + 0.12 * (-du - dv) / (2 * r)
        if any(abs(across - half * math.sin(g)) < 0.55 for g in grooves):
            base = self.GROOVE
        else:
            base = (250, 115, 10)
        return tuple(min(255, int(c * light)) for c in base)

    EAR_REACH = 0.95 + 0.56  # head radii from the centre to the outside of an ear

    def _layout(self):
        """Shrunk to leave room for the title: under its three lines on 64x64, sitting on the bottom
        edge; to its right on 64x32, until it jumps into the title's spot."""
        if self.height >= 64:
            r = 14.5
            return r, self.width / 2 - 0.5, self.height - 1.5 - r
        r = 8.5
        return r, self.width - 14.0, self.height - 1.0 - r

    def _motion_start(self):
        """When the wink or hop begins, in scene seconds."""
        return self.WINK_AT if self.motion == "wink" else self.HOP_AT

    def _head_half_width(self, y):
        """Half the head's width at row y (0 above or below it)."""
        dy = abs(y - self.cy)
        return math.sqrt(self.R ** 2 - dy ** 2) if dy < self.R else 0.0

    def _party_hours(self):
        """The special event's (start, end) like ("7PM", "12AM"), from the park's schedule, or None."""
        event = special_event_now(self.park) if self.park else None
        times = []
        for key in ("openingTime", "closingTime"):
            try:
                times.append(datetime.fromisoformat(event[key]).strftime("%I%p").lstrip("0"))
            except (TypeError, KeyError, ValueError):
                return None
        return tuple(times)

    def title(self, t):
        lit = self._lit(t)
        if not lit:
            return []
        fade = lambda rgb, k=lit: tuple(int(c * k) for c in rgb)
        if self.short:
            return self._short_title(t, fade)
        lines = [(text, self.width / 2, 1 + i * (self.TITLE_ROW_H + 1), fade(rgb))
                 for i, (text, rgb) in enumerate(self.TITLE_TALL)]
        shown = ramp(t, self._motion_start(), self.MIST_HOURS_FADE_S)
        if self.hours and shown:
            # In the mist on the bottom rows, centred in the gaps beside the pumpkin's base.
            start, end = self.hours
            rgb = fade(self.HOURS_RGB, shown)
            top = self.height - 1 - self.TITLE_ROW_H
            half = self._head_half_width(top)
            left_gap, right_gap = self.cx - half - 1, self.cx + half + 1
            lines += [(start, left_gap / 2, top, rgb), (end, (right_gap + self.width) / 2, top, rgb)]
        return lines

    def _short_title(self, t, fade):
        """64x32: the title column, shoved left off the board by the jumping pumpkin, then the hours
        fading in on the right where the pumpkin stood."""
        dx, _ = self._jump(t)
        ear_left = self.cx + dx - self.R * self.EAR_REACH
        # Only once it's moving: at rest its ear may sit right up against the column.
        shove = min(0.0, ear_left - 1 - self.TITLE_COLUMN_RIGHT) if dx < 0 else 0.0
        lines = []
        for i, (text, rgb) in enumerate(self.TITLE_SHORT):
            x = self.TITLE_COLUMN_X + shove
            if x + len(text) * 2 > 0:  # still partly on the board
                lines.append((text, x, 1 + i * self.TITLE_ROW_H, fade(rgb)))
        shown = ramp(t, self.TONIGHT_AT, self.TONIGHT_FADE_S)
        if self.hours and shown:
            start, end = self.hours
            rows = (("TONIGHT", self.GOLD), (f"{start} TO", self.HOURS_RGB), (end, self.HOURS_RGB))
            top = (self.height - len(rows) * self.TITLE_ROW_H) // 2 + 1
            lines += [(text, self.width - 16, top + i * self.TITLE_ROW_H, fade(rgb, shown * self._lit(t)))
                      for i, (text, rgb) in enumerate(rows)]
        return lines

    def _paint_pumpkin(self, cx, cy, r):
        if r < self.R:
            # An ear: it leans out from the head, with its ribs running along the lean.
            ax, ay = self.cx - cx, self.cy - cy
            n = math.hypot(ax, ay)
            axis, grooves = (ax / n, ay / n), (-0.7, 0.0, 0.7)
        else:
            axis, grooves = (0.0, 1.0), (-1.0, -0.45, 0.45, 1.0)
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, y - cy)
                if d > r:
                    continue
                if d > r - 1.2:
                    self.shell[(x, y)] = self.OUTLINE
                else:
                    self.shell[(x, y)] = self._shade(cx, cy, r, x, y, axis, grooves)

    def _paint_stem(self):
        s = self.R / 18
        top = self.cy - self.R
        # Centred on the head: an even width when its centre falls between two columns, odd when
        # it's on one, so the base sits square in the middle; the top leans a little to the right.
        w = max(3, round(4 * s))
        if (w % 2 == 0) != (self.cx % 1 == 0.5):
            w += 1
        for i in range(max(4, round(6 * s))):
            y = int(top) - i
            left = round(self.cx - (w - 1) / 2 + i * 0.3)
            for dx in range(w):
                self.shell[(left + dx, y)] = (40, 85, 28) if dx in (0, w - 1) else self.STEM

    def _mouth(self, u, v):
        if abs(u) > 0.6:
            return False
        m = 1 - (u / 0.6) ** 2
        return 0.36 * m <= v <= 0.82 * math.sqrt(m)

    def _is_tongue(self, x, y):
        u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
        return self._mouth(u, v) and abs(u) < 0.36 and v >= 0.56 + 0.12 * (u / 0.3) ** 2

    def _is_carved(self, x, y):
        """Mickey's pie-cut eyes, oval nose and open smile (tongue included), head-relative."""
        u, v = (x - self.cx) / self.R, (y - self.cy) / self.R
        for ex in self.EYES:
            if ((u - ex) / self.EYE_HW) ** 2 + ((v - self.EYE_V) / self.EYE_HH) ** 2 <= 1:
                # The pie cut: a rounded bump of pumpkin rising into the inner bottom of the eye.
                nx = ex - 0.06 * (1 if ex > 0 else -1)
                if ((u - nx) / 0.08) ** 2 + ((v - (self.EYE_V + 0.2)) / 0.15) ** 2 <= 1:
                    return False
                return True
        if (u / 0.26) ** 2 + ((v - 0.1) / 0.12) ** 2 <= 1:
            return True
        return self._mouth(u, v)

    def _winking(self, t):
        """How closed the winking eye is, 0 open to 1 shut."""
        if self.motion != "wink":
            return 0.0
        p = (t - self.wink_at) / self.WINK_S
        return math.sin(math.pi * p) ** 0.5 if 0 < p < 1 else 0.0

    def _wink(self, pumpkin, shut, lit):
        """Lower a lid over the right-hand eye; shut tight, it's a happy upturned arc."""
        ecx, ecy = self.cx + self.EYES[1] * self.R, self.cy + self.EYE_V * self.R
        hh, hw = self.EYE_HH * self.R, self.EYE_HW * self.R
        glow = max((pumpkin[p] for p, e in self.eye_of.items() if e == 1), key=sum)
        lid = ecy - hh + 2 * hh * shut
        open_px = {(x, y) for (x, y), e in self.eye_of.items() if e == 1 and y > lid and shut < 0.8}
        skin_k = 0.3 + 0.52 * lit
        for p, rgb in self.eye_skin.items():
            if p in open_px:
                continue
            near_open = any((p[0] + dx, p[1] + dy) in open_px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            pumpkin[p] = self.CUT_RIM if near_open else tuple(int(c * skin_k) for c in rgb)
        if shut >= 0.8:
            for i in range(-round(hw), round(hw) + 1):
                x = round(ecx + i)
                y = round(ecy + hh * 0.45 - 2 * (1 - (i / hw) ** 2))
                pumpkin[(x, y)] = glow
                pumpkin[(x, y + 1)] = self.CUT_RIM

    def _hop(self, t):
        """Rows the pumpkin is lifted: one hop as the candle catches and a smaller rebound."""
        if self.motion != "bounce":
            return 0
        p = (t - self.HOP_AT) / self.HOP_S
        if 0 < p < 1:
            return round(self.R * 0.24 * math.sin(math.pi * p))
        if 1 <= p < 1.6:
            return round(self.R * 0.08 * math.sin(math.pi * (p - 1) / 0.6))
        return 0

    def _jump(self, t):
        """64x32's leap into the title's spot: (columns moved left, rows lifted) at time t."""
        if not self.short:
            return 0.0, 0
        p = ramp(t, self.JUMP_AT, self.JUMP_S)
        ease = smooth(p)
        return (self.land_cx - self.cx) * ease, round(self.R * 0.5 * math.sin(math.pi * p))

    def _draw_pumpkin(self, out, t):
        pumpkin = {}
        super()._draw_pumpkin(pumpkin, t)
        lit = self._lit(t)
        for x, y in self.tongue:
            pumpkin[(x, y)] = tuple(int(d + (c - d) * lit) for c, d in zip(self.TONGUE, self.TONGUE_DARK))
        shut = self._winking(t)
        if shut:
            self._wink(pumpkin, shut, lit)
        dx, jump_lift = self._jump(t)
        shift, lift = round(dx), self._hop(t) + jump_lift
        for (x, y), rgb in pumpkin.items():
            self.put(out, x + shift, y - lift, rgb)
