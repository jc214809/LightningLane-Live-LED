"""
Jollywood Nights' Tower of Terror: the Hollywood Tower Hotel decked out for the party. It replaces the
plain tower on party nights (utils/special_events.py SPECIAL_EVENTS).

The plain tower's story (display/landmarks/tower_of_terror.py), dressed up: red, green and gold bulbs chase
round the pillars, roofs and dome (the wing roofs the other way), the windows glow red and green, a red bow
sits on the cupola and two wreaths hang either side of the elevator doors, their bows resting on a pink neon
"JOLLYWOOD" sign that flickers on. Tonight's hours light up in green neon in the top-corner storm clouds
(start left, end right; nothing without them), so 64x32 shows them too. The lightning is red and green, two
searchlights sweep the sky (never the hotel) and snow falls. The elevator car is a red gift with a gold
ribbon: it drops and bursts into confetti.

64x32 keeps the tower's tilt up to the dome; the sign and hours wait for it, and the gift lands just under
the sign and bursts there, in view.
"""

import math

from utils.special_events import special_event_hours

from display.landmarks.tower_of_terror import TowerOfTerrorLandmark

RED, GREEN, GOLD, WHITE = (230, 30, 30), (40, 200, 60), (255, 200, 60), (255, 255, 255)
BULBS = (RED, GREEN, GOLD, WHITE)  # the chase order
CHASE_HZ = 8  # bulb steps a second
WINDOW_RED, WINDOW_GREEN = (255, 60, 60), (70, 230, 100)
BOW_RGB, BOW_KNOT_RGB = RED, (150, 15, 25)
WREATH_KNOT_RGB = (160, 15, 25)
GIFT_RGB, RIBBON_RGB = (210, 30, 40), GOLD
NEON_RGB, NEON_OFF_RGB = (255, 70, 150), (70, 30, 55)
HOURS_RGB, HOURS_OFF_RGB = (80, 240, 110), (25, 60, 35)
SIGN_BACK_RGB = (25, 15, 30)
CLOUD_SHADOW_RGB = (40, 34, 52)  # round the hours, so they read against the cloud
PINE_RGB, PINE_DARK_RGB, BERRY_RGB = (30, 150, 55), (15, 95, 35), (240, 40, 40)
BEAM_RGB = (110, 105, 80)
SNOW_RGB, SNOW_BRIGHT_RGB = (190, 200, 225), WHITE

SIGN, SIGN_Y = "JOLLYWOOD", 23
HOURS_Y = 2
HOURS_X = (7, 56)  # centres of the start and end times, in the top-corner clouds
WREATH_Y = 15
SIGN_ON_AT, HOURS_ON_AT = 0.25, (0.55, 0.8)  # when each starts flickering on, after the sign delay
FLICKER_S = 0.35
BURST_S = 0.15  # the white flash when the gift bursts
BEAM_LENGTH, BEAM_WIDTH = 70, 0.1
CONFETTI = 44
FLAKES = 35

# 3x5 neon letters (a 1px "1", so "11PM" and "12AM" fit in a corner cloud).
FONT = {
    "J": ["..#", "..#", "..#", "#.#", ".#."], "O": [".#.", "#.#", "#.#", "#.#", ".#."],
    "L": ["#..", "#..", "#..", "#..", "###"], "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "W": ["#.#", "#.#", "#.#", "###", "#.#"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "M": ["#.#", "###", "###", "#.#", "#.#"],
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": ["#", "#", "#", "#", "#"],
    "2": ["##.", "..#", ".#.", "#..", "###"], "3": ["##.", "..#", ".#.", "..#", "##."],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "##.", "..#", "##."],
    "6": [".##", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "##."],
}

BOW = {  # on the cupola, over its two windows
    (29, 6): BOW_RGB, (30, 6): BOW_RGB, (33, 6): BOW_RGB, (34, 6): BOW_RGB,
    (29, 7): BOW_RGB, (30, 7): BOW_RGB, (31, 7): BOW_KNOT_RGB, (32, 7): BOW_KNOT_RGB, (33, 7): BOW_RGB, (34, 7): BOW_RGB,
    (29, 8): BOW_RGB, (30, 8): BOW_RGB, (33, 8): BOW_RGB, (34, 8): BOW_RGB,
    (30, 9): BOW_RGB, (33, 9): BOW_RGB, (29, 10): BOW_RGB, (34, 10): BOW_RGB,
}


def text_pixels(text, x, y):
    """[(x, y)] lit by text in FONT with its top-left at (x, y), one column between letters."""
    out = []
    for ch in text:
        glyph = FONT[ch]
        out += [(x + k, y + r) for r, row in enumerate(glyph) for k, v in enumerate(row) if v == "#"]
        x += len(glyph[0]) + 1
    return out


def text_width(text):
    return sum(len(FONT[ch][0]) + 1 for ch in text) - 1


def neon_on(t, at):
    """Whether a neon sign that starts at `at` is lit at t: it stutters on, then holds."""
    if t < at:
        return False
    return t >= at + FLICKER_S or int(t * 30) % 3 != 0


class JollywoodTowerLandmark(TowerOfTerrorLandmark):
    """The Tower of Terror decked out for Jollywood Nights: bulbs, wreaths, a neon sign, tonight's hours in
    the clouds, red and green lightning, searchlights, snow, and a gift for the car that bursts."""

    BOLT_RGB, BOLT_EDGE_RGB = (255, 70, 70), (60, 230, 90)

    def __init__(self, width, height, rng=None, park=None):
        # Where the gift's bow lands: 64x32 just under the sign, where the board can see it burst.
        self.CAR_FLOOR = 28 if height < 64 else 50
        super().__init__(width, height, rng, park)

    def build(self):
        super().build()
        L, R, SL, SR = self.TOWER_L, self.TOWER_R, self.STRIP_L, self.STRIP_R
        self.sign_delay = self.PAN_S - 0.2 if self.pans else 0.0  # 64x32: the signs wait for the tilt
        self.outline, self.wing_outline = self._outline()
        self.hotel = {(x, y) for x in range(self.width) for y in range(self.height) if self._on_hotel(x, y)}
        # (sky it reaches, which way it swings, phase): one each side, swinging in and out of step.
        self.beams = [(self._beam_cells(4), 1, 0.0), (self._beam_cells(self.width - 4), -1, 1.3)]
        self.lit_windows = {(x, y + dy): WINDOW_RED if (x // 2 + y // 3) % 2 else WINDOW_GREEN
                            for x, y, _ in self.windows if y > 8 for dy in (0, 1)}
        self.wreaths = [self._wreath((L + SL) / 2, WREATH_Y), self._wreath((SR + R) / 2 + 0.5, WREATH_Y)]
        sign_x = self.width // 2 - text_width(SIGN) // 2
        self.sign_back = {(x, y): SIGN_BACK_RGB for x in range(sign_x - 2, sign_x + text_width(SIGN) + 2)
                          for y in range(SIGN_Y - 1, SIGN_Y + 6)}
        self.sign = text_pixels(SIGN, sign_x, SIGN_Y)
        self.hours = special_event_hours(self.park)
        self.hour_signs = []
        for time, cx, at in zip(self.hours or (), HOURS_X, HOURS_ON_AT):
            lit = text_pixels(time, cx - text_width(time) // 2, HOURS_Y)
            shadow = {(x + dx, y + dy) for x, y in lit for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
            self.hour_signs.append((lit, shadow, at))
        # The confetti's origin, at the landed gift (on 64x32 a row lower, so the flash stays off the sign).
        self.burst_y = self.CAR_FLOOR + (1 if self.pans else 0)
        self.confetti = [(self.rng.uniform(-1, 1) * 2.4, self.rng.uniform(-3.2, -1.2), BULBS[i % 4])
                         for i in range(CONFETTI)]
        self.flakes = [(self.rng.uniform(0, self.width), self.rng.uniform(0, self.height), self.rng.uniform(5, 10),
                        self.rng.uniform(0, 2 * math.pi), self.rng.random() < 0.3) for _ in range(FLAKES)]

    def _outline(self):
        """The bulbs' places round the hotel, in chase order: the left pillar up, its spire, the left roof,
        over the dome, the right roof and spire, the right pillar down; and the two wing roofs."""
        L, R, SL, SR = self.TOWER_L, self.TOWER_R, self.STRIP_L, self.STRIP_R
        pts = [(L - 1, y) for y in range(57, 5, -1)]
        pts += [(L + 1, 3), (L + 1, 2)]
        pts += [(x, 8) for x in range(L + 4, SL - 2)]
        pts += [(SL - 2 + k, 4 - k) for k in range(4)] + [(x, 0) for x in range(SL + 2, SR - 1)]
        pts += [(SR - 1 + k, 1 + k) for k in range(4)]
        pts += [(x, 8) for x in range(SR + 3, R - 3)]
        pts += [(R - 1, 2), (R - 1, 3)]
        pts += [(R + 1, y) for y in range(6, 58)]
        wings = [(L - 10 + i, 45 - i) for i in range(4)] + [(x, 41) for x in range(L - 6, L)]
        wings += [(R + 1 + i, 37) for i in range(5)] + [(R + 6 + i, 38 + i) for i in range(4)]
        return pts[::2], wings[::2]

    def _on_hotel(self, x, y):
        """True on the hotel, its outline and the trees: the searchlights light only the sky."""
        L, R, SL, SR = self.TOWER_L, self.TOWER_R, self.STRIP_L, self.STRIP_R
        return (y >= 55 or (L - 9 <= x <= L - 1 and y >= 42) or (R + 1 <= x <= R + 9 and y >= 38)
                or (L <= x <= R and y >= 5) or SL - 1 <= x <= SR + 1 or x in (L + 1, R - 1))

    def _beam_cells(self, x0):
        """The sky a searchlight at (x0, bottom) can reach: [(angle, half width, x, y, strength)] by angle,
        so a frame looks up only the cells near where it points."""
        cells = []
        for x, y in ((x, y) for x in range(self.width) for y in range(self.height) if (x, y) not in self.hotel):
            dx, dy = x - x0, self.height - 1 - y
            d = math.hypot(dx, dy)
            if dy > 0 and d < BEAM_LENGTH:
                cells.append((math.atan2(dx, dy), BEAM_WIDTH * (0.4 + d / BEAM_LENGTH) / 1.4, x, y, 1 - d / BEAM_LENGTH))
        cells.sort()
        return cells

    def _wreath(self, cx, cy):
        """A 9px wreath: ({(x, y): rgb} of its two-tone pine ring with the wall cleared round it, [(x, y, kind)]
        round the ring: berries (None) and twinkling bulbs (their place in the chase), and {(x, y): rgb} of its
        bow, drawn over the berries."""
        still = {}
        outline = set(self.outline)
        for y in range(int(cy) - 5, int(cy) + 6):
            for x in range(int(cx) - 5, int(cx) + 6):
                d = math.hypot(x - cx, y - cy)
                if 1.8 <= d <= 4.2:
                    still[(x, y)] = PINE_RGB if (x * 3 + y * 5) % 4 else PINE_DARK_RGB
                elif d < 4.9 and (x, y) not in outline:
                    still[(x, y)] = self.COLORS["wall"]  # no windows peeking round it
        dots = [(round(cx + 3.0 * math.cos(a)), round(cy - 3.0 * math.sin(a)), None if k % 2 else k)
                for k, a in enumerate((0.3, 1.2, 2.3, 3.0, 4.0, 5.2))]
        by = round(cy + 4)
        bow = {(round(cx) + x, by + y): WREATH_KNOT_RGB if (x, y) == (0, 0) else BOW_RGB
               for x, y in ((-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-2, -1), (2, -1), (-1, 1), (1, 1), (-2, 2), (2, 2))}
        return still, dots, bow

    def draw_car(self, out, left, top):
        """The car is a red gift with a gold ribbon and a bow on top."""
        self.put(out, left + 1, top, RIBBON_RGB)
        self.put(out, left + 3, top, RIBBON_RGB)
        for y in range(top + 1, top + 5):
            for x in range(left, left + 5):
                self.put(out, x, y, RIBBON_RGB if x == left + 2 or y == top + 2 else GIFT_RGB)

    def gift_left(self):
        return (self.STRIP_L + self.STRIP_R + 1) // 2 - 2

    def animate(self, out, t):
        super().animate(out, t)
        for cells, swing, phase in self.beams:
            self._beam(out, cells, swing * (0.3 + 0.3 * math.sin(t * 1.2 + phase)))
        for p, rgb in self.lit_windows.items():
            if out.get(p) == self.COLORS["win_lit"]:
                out[p] = rgb
        chase = int(t * CHASE_HZ)
        for i, p in enumerate(self.outline):
            self.put(out, *p, BULBS[(i + chase) % 4])
        for i, p in enumerate(self.wing_outline):
            self.put(out, *p, BULBS[(i - chase) % 4])
        out.update(BOW)
        if self.DOORS_AT + 0.12 <= t < self.DROP_AT:  # the gift waits behind the opening doors
            self.draw_car(out, self.gift_left(), self.doors[1] + 1)
        out.update(self.sign_back)
        lit = neon_on(t - self.sign_delay, SIGN_ON_AT)
        for p in self.sign:
            out[p] = NEON_RGB if lit else NEON_OFF_RGB
        for pixels, shadow, at in self.hour_signs:
            for p in shadow:
                self.put(out, *p, CLOUD_SHADOW_RGB)
            lit = neon_on(t - self.sign_delay, at)
            for p in pixels:
                self.put(out, *p, HOURS_RGB if lit else HOURS_OFF_RGB)
        for still, dots, bow in self.wreaths:
            out.update(still)
            for x, y, k in dots:
                self.put(out, x, y, BERRY_RGB if k is None else BULBS[(k + int(t * 4)) % 4])
            out.update(bow)
        self._burst(out, t)
        for x, y, speed, phase, bright in self.flakes:
            self.put(out, int((x + 1.2 * math.sin(t * 1.5 + phase)) % self.width), int((y + t * speed) % self.height),
                     SNOW_BRIGHT_RGB if bright else SNOW_RGB)

    def _beam(self, out, cells, angle):
        """Add a searchlight's glow, pointing `angle` radians off straight up, to the sky it reaches."""
        lo = _bisect(cells, angle - BEAM_WIDTH)
        for a, half, x, y, f in cells[lo:]:
            if a > angle + BEAM_WIDTH:
                break
            if abs(a - angle) < half:
                r, g, b = out.get((x, y), (0, 0, 0))
                out[(x, y)] = (min(255, int(r + BEAM_RGB[0] * f)), min(255, int(g + BEAM_RGB[1] * f)),
                               min(255, int(b + BEAM_RGB[2] * f)))

    def _burst(self, out, t):
        """Once the gift lands: a white flash, then confetti thrown up that falls (not into the trees)."""
        b = t - self.LAND_AT
        if b < 0:
            return
        cx, cy = self.gift_left() + 2, self.burst_y
        for vx, vy, rgb in self.confetti:
            y = cy + vy * b * 11 + 16 * b * b
            if y < 58:
                self.put(out, int(cx + vx * b * 11), int(y), rgb if int(t * 12 + vx * 5) % 3 else WHITE)
        if b < BURST_S:
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx * dx + dy * dy <= 9:
                        self.put(out, cx + dx, cy + 2 + dy, WHITE)


def _bisect(cells, angle):
    """The first index in `cells` (sorted by angle) at or past `angle`."""
    lo, hi = 0, len(cells)
    while lo < hi:
        mid = (lo + hi) // 2
        if cells[mid][0] < angle:
            lo = mid + 1
        else:
            hi = mid
    return lo
