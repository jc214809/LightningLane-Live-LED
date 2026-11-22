"""
The Very Merry Christmas Party's Santa train: Santa drives a steam engine left to right across a snowy
night, pulling Mickey, a gift car, Donald, a tree car, Goofy and Pluto. Mickey, Donald and Goofy ride in
Christmas sweaters and Santa hats, their gloves on the rim; Pluto wears a green collar. It replaces the
castle on party nights (utils/special_events.py SPECIAL_EVENTS).

64x64 draws the full train, 258 px long; 64x32 a half-size one: the engine and cars halved (each 2x2 block's
most common colour, which kept Santa's face; the wheels redrawn), the riders mini bead heads.
The wheels turn as it goes: a spoke bar on 64x64, a bright spot round the rim on 64x32's 4x3 wheels, and the
engine's side rod goes round with its drivers (the art leaves the rod out; spin_pixels draws it). Smoke puffs
from the stack as it goes, each left where it was puffed, rising and fading up off the board.

The riders move as it goes (rider_patch): Mickey, Donald, Goofy and Pluto bob in their seats with the track,
rippling down the train; everyone blinks now and then; Pluto wags his tail and pants; on 64x64 Mickey waves his
back glove beside his cheek and Santa waves from the cab the whole time (SANTA_WAVE_64, drawn by the user).

The riders come from real charts, cleaned up: Mickey a cross-stitch Christmas chart, Donald Kandi Patterns
22347 with a Santa hat for his sailor cap, Goofy a colour-by-number, Pluto Kandi Patterns 19213 turned to
face the way the train drives; on 64x32 the DIY Candy mini heads (easy-disney-perler-beads).

Last comes a billboard car as wide as the board: the train brakes to a stop with it filling the screen and
holds there, the sign saying the party's name and tonight's hours (the park's schedule; the name alone
without them; on 64x32 the hours lead, as "TONIGHT 7PM-12AM"), a ring of bulbs chasing round its red frame.
"""

import math

from display.landmarks.santa_train_art import (  # noqa: F401  the art and palette lived here: tests and tools read them from this module
    BULBS,
    COLORS,
    DONALD_32,
    DONALD_64,
    ENGINE_32,
    ENGINE_64,
    GIFT_32,
    GIFT_64,
    GOOFY_32,
    GOOFY_64,
    MICKEY_32,
    MICKEY_64,
    PLUTO_32,
    PLUTO_64,
    RIDERS,
    SANTA_WAVE_64,
    SANTA_WAVE_AT,
    TRAIN_32,
    TRAIN_64,
    TREE_32,
    TREE_64,
)
from display.landmarks.santa_train_riders import (  # noqa: F401  the riders' code lived here too
    BLINKS,
    RIM_EDGE,
    RIM_ROW,
    blink_times,
    mickey_wave,
    pluto_tail,
    rider_patch,
    rider_state,
)
from display.landmarks.santa_train_sign import (  # noqa: F401  and the billboard's
    FRAME_PX,
    NAME,
    SIGN_INK,
    SIGN_RGB,
    TONIGHT_SPACE_PX,
    billboard,
    line_pixels,
    ring,
    sign_lines,
    sign_pixels,
    text_width,
)
from display.landmarks.santa_train_wheels import (  # noqa: F401  and the wheels'
    RIM_32,
    SPIN_STEPS,
    spin_pixels,
    wheels,
)
from display.landmarks.scene import SKY_RGB, Landmark
from display.landmarks.three_caballeros import SMALL_FONT, TINY_FONT  # noqa: F401  the sign's fonts, which tests read here
from display.pixels import blend
from utils.special_events import special_event_hours

RAIL_RGB, SNOW_RGB = (110, 70, 35), (225, 228, 240)
COVER_AND_WIPE_S = 1.2  # of the screen, before the scene's clock starts
CRUISE = {True: 45.0, False: 26.25}  # px/s, by whether the board is 64 tall
STOP_PX = {True: 48, False: 24}  # the train brakes evenly over this much, stopping with the billboard filling the board
HOLD_S = 4.0  # stopped, for the billboard to be read
GROUND_ROWS = {True: 3, False: 1}  # snow under the rail
FLAKES = 14  # falling snow, behind the train, per 64 rows
WHEEL_ROWS = {True: 9, False: 3}  # the train's bottom rows, where the wheels are
ROLL_R = {True: 4, False: 2}  # the radius the wheels roll at, so they turn with the train's speed
# The billboard: its flatcar is Mickey's red car from this row down, stretched to the board's width.
DECK_ROW = {True: 48, False: 25}
CHASE_HZ = 6  # bulb steps per second round the frame
STACK = {True: (44.5, 21), False: (22, 10)}  # the smoke's start in the engine art: over its stack's middle
PUFF_S = 0.3  # one puff this often
PUFF_RISE = {True: 14.0, False: 8.0}  # px/s
PUFF_R = {True: (1.5, 4.5), False: (1.0, 2.5)}  # its radius when puffed and when it leaves the top
PUFF_FADE = 0.6  # how much of it is gone by then
# The art is in santa_train_art.py, santa_train_cars_64.py and santa_train_cars_32.py; the riders' poses in
# santa_train_riders.py, the wheels in santa_train_wheels.py, the sign in santa_train_sign.py.
EDITOR_SPRITES = [
    "ENGINE_64",
    "SANTA_WAVE_64",
    "ENGINE_32",
]  # art tools/build_sprite_editor.py puts in the sprite editor


class SantaTrainLandmark(Landmark):
    """Very Merry Christmas Party: Santa's train drives across, the riders in Santa hats and Christmas
    sweaters, and stops on a billboard with the party's name and hours."""

    SCREEN_S = 16.0  # 64x64's; each board sets its own in build: the sweep and wipe, the drive and the hold

    def build(self):
        w, h = self.width, self.height
        big = h >= 64
        train = TRAIN_64 if big else TRAIN_32
        pieces = [flatcar(MICKEY_64 if big else MICKEY_32, DECK_ROW[big], w)] + list(train)
        art = ["".join(rows) for rows in zip(*pieces)]
        self._place(art, big)
        self.bulbs = ring(w, self.sign_h)[::2]
        self._index_columns(art, billboard(w, self.sign_h, big, self.hours), big)
        self._set_timing(big)
        self._set_smoke(train, big)
        self._precompute_wheels(pieces, big)
        for y in range(h):
            rgb = SKY_RGB if y < self.rail_y else RAIL_RGB if y == self.rail_y else SNOW_RGB
            for x in range(w):
                self.base[(x, y)] = rgb
        self.flakes = [
            (self.rng.randrange(w), self.rng.uniform(0, self.rail_y), self.rng.uniform(3, 7))
            for _ in range(FLAKES * h // 64)
        ]
        self._seat_riders(pieces, big)
        self._poses = {}

    def _place(self, art, big):
        """Where the train and its sign sit on the board: the wheels on the rail, the sign over the flatcar's deck."""
        self.train_w, self.train_h = len(art[0]), len(art)
        self.rail_y = self.height - GROUND_ROWS[big] - 1
        self.train_y = self.rail_y - self.train_h  # the wheels on the rail
        self.hours = special_event_hours(self.park)
        self.sign_h = self.train_y + DECK_ROW[big]  # the sign fills the board above the flatcar's deck

    def _index_columns(self, art, sign, big):
        """self.columns: [(y, rgb)] per column of the train and its sign, so a frame only walks the columns on the board."""
        self.columns = [
            [(self.train_y + r, COLORS[row[c]]) for r, row in enumerate(art) if row[c] != "."]
            for c in range(self.train_w)
        ]
        # The dark under each car, between its wheels, is sky the snow and stars don't show through.
        for c, column in enumerate(self.columns):
            body = next((r for r, row in enumerate(art) if row[c] != "."), self.train_h)
            column += [
                (self.train_y + r, SKY_RGB)
                for r in range(max(body + 1, self.train_h - WHEEL_ROWS[big]), self.train_h)
                if art[r][c] == "."
            ]
        for (x, y), rgb in sign.items():
            self.columns[x].append((y, rgb))

    def _set_timing(self, big):
        """The drive's speed and length, and how long the screen runs: the sweep and wipe, the drive, the hold."""
        self.cruise, self.stop_px = CRUISE[big], STOP_PX[big]
        self.drive_s = (self.train_w - self.stop_px) / self.cruise + 2 * self.stop_px / self.cruise
        self.SCREEN_S = COVER_AND_WIPE_S + self.drive_s + HOLD_S
        self.roll_r = ROLL_R[big]

    def _set_smoke(self, train, big):
        """Where the smoke starts on the board (over the engine's stack) and how long a puff lives."""
        stack_x, stack_y = STACK[big]
        self.stack = (self.train_w - len(train[-1][0]) + stack_x, self.train_y + stack_y)
        self.puff_r = PUFF_R[big]
        self.puff_life = (self.stack[1] + self.puff_r[1] + 1) / PUFF_RISE[big]  # up off the top

    def _precompute_wheels(self, pieces, big):
        """Every wheel position, worked out once: self.spin[step] = [(x along the train, y on the board, rgb)]."""
        self.spin = [[] for _ in range(SPIN_STEPS)]
        x0 = 0
        for i, piece in enumerate(pieces):
            for step in range(SPIN_STEPS):
                for (x, y), rgb in spin_pixels(piece, big, step, engine=i == len(pieces) - 1).items():
                    self.spin[step].append((x0 + x, self.train_y + y, rgb))
            x0 += len(piece[0])

    def _seat_riders(self, pieces, big):
        """self.riders: [(x along the train, its art, what it does, its blink times)]."""
        self.riders, x0 = [], 0
        for piece in pieces:
            kind = RIDERS[big].get(id(piece))
            if kind:
                self.riders.append((x0, piece, kind, blink_times(self.rng, self.SCREEN_S)))
            x0 += len(piece[0])

    def travelled(self, t):
        """How far the train has come by scene time t: at cruising speed, then braking evenly over STOP_PX to
        stop with the billboard filling the board."""
        v, stop = self.cruise, self.stop_px
        cruise_s = (self.train_w - stop) / v
        if t <= cruise_s:
            return v * t
        brake = min(t - cruise_s, 2 * stop / v)
        return self.train_w - stop + v * brake - v * v * brake * brake / (4 * stop)

    def train_x(self, t):
        """The train's left edge at scene time t: off the left edge at 0, at 0 (the billboard filling the board)
        once stopped."""
        return round(-self.train_w + self.travelled(t))

    def puffs(self, t):
        """{(x, y): rgb} of the smoke at scene time t (off the board too): a puff every PUFF_S from the stack,
        staying where it was puffed as the train goes on, growing and fading into the sky as it rises; the
        newest on top."""
        rise, (r0, r1) = PUFF_RISE[self.height >= 64], self.puff_r
        out = {}
        for k in range(max(0, math.ceil((t - self.puff_life) / PUFF_S)), int(t / PUFF_S) + 1):
            age = t - k * PUFF_S
            share = age / self.puff_life
            cx = self.train_x(k * PUFF_S) + self.stack[0]
            cy = self.stack[1] - rise * age
            r = r0 + (r1 - r0) * share
            alpha = 1 - PUFF_FADE * share
            for y in range(math.floor(cy - r), math.ceil(cy + r) + 1):
                for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
                    d = math.hypot(x - cx, y - cy)
                    if d <= r:
                        out[(x, y)] = blend(COLORS["W"] if d <= r - 1 else COLORS["S"], SKY_RGB, alpha)
        return out

    def rider_pixels(self, t):
        """[(x along the train, y on the board, rgb)] the riders' poses change at scene time t."""
        big, out = self.height >= 64, []
        for i, (x0, piece, kind, blinks) in enumerate(self.riders):
            state = rider_state(kind, big, t, self.travelled(t), len(self.riders) - i, blinks)
            key = (x0, state)
            if key not in self._poses:
                posed = rider_patch(piece, kind, big, state)
                self._poses[key] = [
                    (x0 + x, self.train_y + y, SKY_RGB if posed[y][x] == "." else COLORS[posed[y][x]])
                    for y, row in enumerate(piece)
                    for x, ch in enumerate(row)
                    if posed[y][x] != ch
                ]
            out += self._poses[key]
        return out

    def spin_step(self, t):
        """Which of the SPIN_STEPS wheel positions shows at scene time t: they roll, turning clockwise."""
        return int(self.travelled(t) / self.roll_r / (2 * math.pi) * SPIN_STEPS) % SPIN_STEPS

    def frame(self, t):
        out = dict(self.base)
        self._sky_and_snow(out, t)
        for (x, y), rgb in self.puffs(t).items():
            if 0 <= x < self.width and 0 <= y < self.height:
                out[(x, y)] = rgb
        left = self.train_x(t)
        self._draw_train(out, left)
        for x, y, rgb in self.rider_pixels(t) + self.spin[self.spin_step(t)]:
            if 0 <= left + x < self.width and y >= 0:
                out[(left + x, y)] = rgb
        chase = int(t * CHASE_HZ)
        for i, (x, y) in enumerate(self.bulbs):
            if 0 <= left + x < self.width:
                out[(left + x, y)] = BULBS[(i + chase) % len(BULBS)]
        return out

    def _sky_and_snow(self, out, t):
        """The twinkling stars above the rail and the falling snow, behind the train."""
        for x, y, phase in self.stars:
            if y < self.rail_y:
                level = 20 + int(25 * (1 + math.sin(t * 3 + phase)))
                out[(x, y)] = (level, level, level + 10)
        for x, y0, fall in self.flakes:
            out[(x, int(y0 + fall * t) % self.rail_y)] = SNOW_RGB

    def _draw_train(self, out, left):
        """The train's columns that are on the board, its left edge at `left`."""
        for x in range(max(0, left), min(self.width, left + self.train_w)):
            for y, rgb in self.columns[x - left]:
                if y >= 0:
                    out[(x, y)] = rgb


def flatcar(car, deck_row, width):
    """The billboard's flatcar: `car` from `deck_row` down (blank above), stretched to `width` by repeating
    its middle column, which falls between its wheels."""
    mid = len(car[0]) // 2
    grow = width - len(car[0])
    return [("." * width) if r < deck_row else row[:mid] + row[mid] * grow + row[mid:] for r, row in enumerate(car)]
