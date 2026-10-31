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
without them), a ring of bulbs chasing round its red frame.
"""

import math

from utils.special_events import special_event_hours

from display.pixels import blend
from display.landmarks.scene import SKY_RGB, Landmark
from display.landmarks.three_caballeros import SMALL_FONT, TINY_FONT
from display.landmarks.wine_and_dine import _text_pixels


RAIL_RGB, SNOW_RGB = (110, 70, 35), (225, 228, 240)
COVER_AND_WIPE_S = 1.2  # of the screen, before the scene's clock starts
CRUISE = {True: 45.0, False: 26.25}  # px/s, by whether the board is 64 tall
STOP_PX = {True: 48, False: 24}  # the train brakes evenly over this much, stopping with the billboard filling the board
HOLD_S = 4.0  # stopped, for the billboard to be read
GROUND_ROWS = {True: 3, False: 1}  # snow under the rail
FLAKES = 14  # falling snow, behind the train, per 64 rows
SPIN_STEPS = 16  # wheel positions per turn: the spoke bar repeats every half turn, the rod every turn
WHEEL_ROWS = {True: 9, False: 3}  # the train's bottom rows, where the wheels are
ROLL_R = {True: 4, False: 2}  # the radius the wheels roll at, so they turn with the train's speed
CRANK = {True: 1.5, False: 1}  # how far the side rod swings round each driver's hub
RIM_32 = [(1, 0), (2, 0), (3, 1), (2, 2), (1, 2), (0, 1)]  # a 64x32 wheel's rim, clockwise from the top left

# The billboard: its flatcar is Mickey's red car from this row down, stretched to the board's width.
DECK_ROW = {True: 48, False: 25}
FRAME_PX = {True: 2, False: 1}
SIGN_RGB = (215, 215, 220)  # white, a little down from full: it's most of the board
CHASE_HZ = 6  # bulb steps per second round the frame
BOB_PX = {True: 15, False: 9}  # px travelled per bob: about 3 a second at cruising speed
BOB_DOWN = 0.35  # the share of each bob a rider spends sunk 1px into the car
BOB_STAGGER = 0.37  # each car a little out of step with the one ahead
BLINK_S, BLINK_GAP = 0.15, (2.0, 4.0)  # eyes shut this long, this often (s)
WAVE_HZ = 6  # glove positions a second
MICKEY_WAVE_S = (2.0, 1.0)  # waving, then resting
WAG_HZ = 8  # tail positions a second: left, middle, right, middle
PANT_HZ = 6  # tongue tip out, in
STACK = {True: (44.5, 21), False: (22, 10)}  # the smoke's start in the engine art: over its stack's middle
PUFF_S = 0.3  # one puff this often
PUFF_RISE = {True: 14.0, False: 8.0}  # px/s
PUFF_R = {True: (1.5, 4.5), False: (1.0, 2.5)}  # its radius when puffed and when it leaves the top
PUFF_FADE = 0.6  # how much of it is gone by then
NAME = {True: ["MICKEY'S", "VERY MERRY", "CHRISTMAS", "PARTY"],  # 5x8: one word or two a line
        False: ["MICKEY'S", "VERY MERRY", "CHRISTMAS PARTY"]}  # 4x6: "CHRISTMAS PARTY" is 60 of 62 px
# The art (COLORS, TRAIN_64, TRAIN_32) is at the end of the file.


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
        self.train_w, self.train_h = len(art[0]), len(art)
        self.rail_y = h - GROUND_ROWS[big] - 1
        self.train_y = self.rail_y - self.train_h  # the wheels on the rail
        self.hours = special_event_hours(self.park)
        self.sign_h = self.train_y + DECK_ROW[big]  # the sign fills the board above the flatcar's deck
        font = SMALL_FONT if big else TINY_FONT
        names = NAME[big] + (["-".join(self.hours)] if self.hours else [])
        lines = [(font, text, COLORS["R" if i % 2 == 0 else "G"]) for i, text in enumerate(names)]
        sign = sign_pixels(w, self.sign_h, lines, FRAME_PX[big])
        self.bulbs = ring(w, self.sign_h)[::2]
        # Column by column, so a frame only walks the columns on the board.
        self.columns = [[(self.train_y + r, COLORS[row[c]]) for r, row in enumerate(art) if row[c] != "."]
                        for c in range(self.train_w)]
        # The dark under each car, between its wheels, is sky the snow and stars don't show through.
        for c, column in enumerate(self.columns):
            body = next((r for r, row in enumerate(art) if row[c] != "."), self.train_h)
            column += [(self.train_y + r, SKY_RGB) for r in range(max(body + 1, self.train_h - WHEEL_ROWS[big]),
                                                                  self.train_h) if art[r][c] == "."]
        for (x, y), rgb in sign.items():
            self.columns[x].append((y, rgb))
        self.cruise, self.stop_px = CRUISE[big], STOP_PX[big]
        self.drive_s = (self.train_w - self.stop_px) / self.cruise + 2 * self.stop_px / self.cruise
        self.SCREEN_S = COVER_AND_WIPE_S + self.drive_s + HOLD_S
        self.roll_r = ROLL_R[big]
        stack_x, stack_y = STACK[big]
        self.stack = (self.train_w - len(train[-1][0]) + stack_x, self.train_y + stack_y)
        self.puff_r = PUFF_R[big]
        self.puff_life = (self.stack[1] + self.puff_r[1] + 1) / PUFF_RISE[big]  # up off the top
        # Every wheel position, worked out once: [(x along the train, y on the board, rgb)] per step.
        self.spin = [[] for _ in range(SPIN_STEPS)]
        x0 = 0
        for i, piece in enumerate(pieces):
            for step in range(SPIN_STEPS):
                for (x, y), rgb in spin_pixels(piece, big, step, engine=i == len(pieces) - 1).items():
                    self.spin[step].append((x0 + x, self.train_y + y, rgb))
            x0 += len(piece[0])
        for y in range(h):
            rgb = SKY_RGB if y < self.rail_y else RAIL_RGB if y == self.rail_y else SNOW_RGB
            for x in range(w):
                self.base[(x, y)] = rgb
        self.flakes = [(self.rng.randrange(w), self.rng.uniform(0, self.rail_y), self.rng.uniform(3, 7))
                       for _ in range(FLAKES * h // 64)]
        # The riders: [(x along the train, its art, what it does, its blink times)].
        self.riders, x0 = [], 0
        for piece in pieces:
            kind = RIDERS[big].get(id(piece))
            if kind:
                blinks, at = [], self.rng.uniform(0.3, BLINK_GAP[0])
                while at < self.SCREEN_S:
                    blinks.append(at)
                    at += self.rng.uniform(*BLINK_GAP)
                self.riders.append((x0, piece, kind, blinks))
            x0 += len(piece[0])
        self._poses = {}

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
                self._poses[key] = [(x0 + x, self.train_y + y, SKY_RGB if posed[y][x] == "." else COLORS[posed[y][x]])
                                    for y, row in enumerate(piece) for x, ch in enumerate(row) if posed[y][x] != ch]
            out += self._poses[key]
        return out

    def spin_step(self, t):
        """Which of the SPIN_STEPS wheel positions shows at scene time t: they roll, turning clockwise."""
        return int(self.travelled(t) / self.roll_r / (2 * math.pi) * SPIN_STEPS) % SPIN_STEPS

    def frame(self, t):
        out = dict(self.base)
        for x, y, phase in self.stars:
            if y < self.rail_y:
                level = 20 + int(25 * (1 + math.sin(t * 3 + phase)))
                out[(x, y)] = (level, level, level + 10)
        for x, y0, fall in self.flakes:
            out[(x, int(y0 + fall * t) % self.rail_y)] = SNOW_RGB
        for (x, y), rgb in self.puffs(t).items():
            if 0 <= x < self.width and 0 <= y < self.height:
                out[(x, y)] = rgb
        left = self.train_x(t)
        for x in range(max(0, left), min(self.width, left + self.train_w)):
            for y, rgb in self.columns[x - left]:
                if y >= 0:
                    out[(x, y)] = rgb
        for x, y, rgb in self.rider_pixels(t) + self.spin[self.spin_step(t)]:
            if 0 <= left + x < self.width and y >= 0:
                out[(left + x, y)] = rgb
        chase = int(t * CHASE_HZ)
        for i, (x, y) in enumerate(self.bulbs):
            if 0 <= left + x < self.width:
                out[(left + x, y)] = BULBS[(i + chase) % len(BULBS)]
        return out


def wheels(piece, big):
    """[(cx, cy, r)] of a piece's wheels in its own coordinates (a centre can fall between pixels), found
    from the rims along its bottom row."""
    h, out, start = len(piece), [], None
    for c, ch in enumerate(piece[-1] + "."):
        if ch in "SW" and start is None:
            start = c
        if ch not in "SW" and start is not None:
            w = c - start
            if big and w >= 5:  # 7 wide (6 where the rim's shine is off the row), the engine's drivers 8 wide
                r = 4 if w >= 7 else 3
                out.append(((start + c - 1) / 2 + (0.5 if w == 6 else 0), h - 1 - r, r))
            elif not big and w >= 2:  # the 4x3 wheels' ".SS." bottom
                out.append(((start + c - 1) / 2, h - 2, 1.5))
            start = None
    return out


def spin_pixels(piece, big, step, engine=False):
    """{(x, y): rgb} drawn over a piece with its wheels at `step` of SPIN_STEPS turned clockwise. 64x64: a spoke
    bar through each hub, only on the wheel's dark inside (its rim and shine stay put); 64x32: one rim pixel
    lit white. The engine's side rod joins its drivers through cranks at the same angle."""
    phase = 2 * math.pi * step / SPIN_STEPS
    hub, rim, shine = COLORS["Y"], COLORS["S"], COLORS["W"]
    out, found = {}, wheels(piece, big)
    for cx, cy, r in found:
        if big:
            for s in range(-r + 1, r):
                x, y = round(cx + s * math.cos(phase) - 0.01), round(cy + s * math.sin(phase))
                if piece[y][x] == "k":
                    out[(x, y)] = rim
        else:
            lit = step * len(RIM_32) // SPIN_STEPS
            for i, (dx, dy) in enumerate(RIM_32):
                out[(int(cx - 1.5) + dx, int(cy - 1) + dy)] = shine if i == lit else rim
        out[(round(cx - 0.01), round(cy))] = hub
    if engine:
        crank = CRANK[big]
        dx, dy = crank * math.cos(phase), crank * math.sin(phase) if big else 0
        y = round(found[0][1] + dy)
        for x in range(round(found[0][0] + dx), round(found[-1][0] + dx) + 1):
            out[(x, y)] = COLORS["R"]
        for cx, _, _ in found:
            out[(round(cx + dx), y)] = hub
    return out


def rider_state(kind, big, t, travelled, order, blinks):
    """What a rider is doing at scene time t, as a hashable (bob, blink, wave, wag, pant): order counts cars from
    the engine, for the bob's ripple."""
    bob = kind in RIM_EDGE and (travelled / BOB_PX[big] + order * BOB_STAGGER) % 1 < BOB_DOWN
    blink = any(at <= t < at + BLINK_S for at in blinks) if (big or kind != "santa") else False
    wave = None
    if big and kind == "santa":
        wave = int(t * WAVE_HZ) % 2
    elif big and kind == "mickey" and t % sum(MICKEY_WAVE_S) < MICKEY_WAVE_S[0]:
        wave = int(t * WAVE_HZ) % 2
    wag = [0, 1, 2, 1][int(t * WAG_HZ) % 4] if kind == "pluto" else None
    pant = int(t * PANT_HZ) % 2 == 0 if kind == "pluto" else None
    return bob, blink, wave, wag, pant


def rider_patch(piece, kind, big, state):
    """The rider's art in `state` (rider_state's): the wave, blink, tail and tongue laid over it, then the bob."""
    bob, blink, wave, wag, pant = state
    rows = [list(row) for row in piece]
    def lay(changes):
        for (x, y), ch in changes.items():
            if 0 <= y < len(rows) and 0 <= x < len(rows[0]):
                rows[y][x] = ch
    if wave is not None and kind == "santa":
        x0, y0 = SANTA_WAVE_AT
        frame = SANTA_WAVE_64[wave]
        lay({(x0 + x, y0 + y): ch for y, row in enumerate(frame) for x, ch in enumerate(row)})
    elif wave is not None:
        lay(mickey_wave(piece, wave))
    if blink:
        lay(BLINKS[big, kind](piece))
    if wag is not None:
        lay(pluto_tail(piece, big, wag))
    if pant:
        lay({(22, 34): "v", (23, 34): "v"} if big else {(7, 15): "v"})
    art = ["".join(r) for r in rows]
    if bob:  # sunk 1px into the car: everything above its rim moves down, the car's raised ends stay
        rim, edge = RIM_ROW[big], RIM_EDGE[kind]
        sunk = [list(r) for r in art]
        for y in range(rim - 1, 0, -1):
            for x in range(len(art[0])):
                if not (y == rim - 1 and art[y][x] == edge):
                    sunk[y][x] = art[y - 1][x]
        sunk[0] = ["."] * len(art[0])
        art = ["".join(r) for r in sunk]
    return art


def _where(piece, ch, x0, x1, y0, y1):
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if piece[y][x] == ch]


def _line(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(round(max(abs(x1 - x0), abs(y1 - y0))), 1)
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def _outline_sky(piece, changes, body):
    """Outline `body` in K wherever it meets sky in the piece, without covering anything already changed."""
    for x, y in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if (q not in body and q not in changes and 0 <= q[1] < len(piece) and 0 <= q[0] < len(piece[0])
                        and piece[q[1]][q[0]] == "."):
                    changes[q] = "K"


# Eyes shut: {(x, y): ch} over each rider's art.
BLINKS = {
    (True, "mickey"): lambda p: {**{q: "a" for q in _where(p, "W", 13, 19, 21, 24) + _where(p, "K", 15, 16, 21, 24)},
                                 **{q: "K" for q in _where(p, "W", 13, 19, 25, 25)}},  # skin lids, a lash line
    (True, "donald"): lambda p: {**{q: "W" for q in _where(p, "K", 8, 12, 17, 23) + _where(p, "K", 15, 19, 17, 23)},
                                 **{(x, 22): "K" for x in [*range(7, 13), *range(14, 20)]}},  # white lids, lash lines
    (True, "goofy"): lambda p: {q: "K" for q in _where(p, "W", 16, 24, 20, 24)},
    (True, "pluto"): lambda p: {**{q: "y" for q in _where(p, "W", 17, 25, 18, 21)},
                                **{q: "K" for q in _where(p, "W", 17, 25, 22, 23)}, **{(x, 21): "K" for x in range(18, 25)}},
    (True, "santa"): lambda p: {q: "d" for q in _where(p, "k", 9, 15, 32, 32)},
    (False, "mickey"): lambda p: {(6, 13): "i", (8, 13): "i"},
    (False, "donald"): lambda p: {**{q: "m" for q in _where(p, "K", 5, 9, 13, 14)}, **{(x, 13): "K" for x in (5, 6, 8, 9)}},
    (False, "goofy"): lambda p: {q: "K" for q in _where(p, "W", 4, 10, 11, 12)},
    (False, "pluto"): lambda p: {**{q: "o" for q in _where(p, "K", 6, 8, 10, 10) + _where(p, "W", 5, 9, 10, 11)},
                                 **{(x, 11): "K" for x in (5, 6, 8, 9)}},
}
RIM_ROW = {True: 41, False: 21}  # the first row of the cars' sides: a bob moves only what's above it
RIM_EDGE = {"mickey": "G", "donald": "R", "goofy": "R", "pluto": "R"}  # the colour of each car's raised ends
# Pluto's 64x64 tail, base (on his back) last; it wags by shearing, so it keeps its curl.
PLUTO_TAIL_64 = [(6, 26), (6, 27), (6, 28), (6, 29), (7, 29), (7, 30), (8, 30), (8, 31), (8, 32), (9, 32), (9, 33),
                 (9, 34), (8, 35), (9, 35), (7, 36), (8, 36)]
PLUTO_TAIL_32 = [{(3, 19): "o", (2, 18): "o", (2, 17): "o"}, {(3, 19): "o", (3, 18): "o", (3, 17): "o"},
                 {(3, 19): "o", (2, 18): "o", (1, 18): "o"}]  # his bead head has none: a short one on his car
MICKEY_GLOVE_OFF = {(8, 39): ".", (9, 39): "K", (10, 39): "x", (11, 39): "X", (8, 40): "G", (9, 40): "K",
                    (10, 40): "x", (11, 40): "X", (12, 40): "X"}  # his back glove up off the rim: sweater and rim show


def pluto_tail(piece, big, wag):
    """Pluto's tail at wag 0, 1 or 2 (left, middle, right)."""
    if not big:
        return PLUTO_TAIL_32[wag]
    swing = (wag - 1) * 3  # px at the tip
    out = {q: "." for q in PLUTO_TAIL_64}
    top = min(y for _, y in PLUTO_TAIL_64)
    pts = [(x + swing * (36 - y) / (36 - top), y) for x, y in PLUTO_TAIL_64]
    for a, b in zip(pts, pts[1:]):
        for q in _line(a, b):
            out[q] = "K"
    return out


def mickey_wave(piece, frame):
    """Mickey's back glove up beside his cheek on a green sleeve from his shoulder, rocking 1px (frame 0 or 1);
    the sleeve stays put."""
    out = dict(MICKEY_GLOVE_OFF)
    gx = 2 - frame
    glove = {(gx + dx, 29 + dy) for dx in range(3) for dy in range(3)}
    sleeve = set()
    for x, y in _line((9, 36), (3, 32)):
        sleeve |= {(x + dx, y + dy) for dx in (0, 1, 2) for dy in (0, 1)}
    sleeve -= glove
    out.update({q: "W" for q in glove})
    _outline_sky(piece, out, sleeve | glove)
    out.update({q: "X" if (q[0] - 1, q[1]) in sleeve else "x" for q in sleeve})
    return out


def flatcar(car, deck_row, width):
    """The billboard's flatcar: `car` from `deck_row` down (blank above), stretched to `width` by repeating
    its middle column, which falls between its wheels."""
    mid = len(car[0]) // 2
    grow = width - len(car[0])
    return [("." * width) if r < deck_row else row[:mid] + row[mid] * grow + row[mid:]
            for r, row in enumerate(car)]


def ring(width, height):
    """The (x, y) round a width x height box's edge, clockwise from the top left."""
    top = [(x, 0) for x in range(width)]
    right = [(width - 1, y) for y in range(1, height)]
    bottom = [(x, height - 1) for x in range(width - 2, -1, -1)]
    left = [(0, y) for y in range(height - 2, 0, -1)]
    return top + right + bottom + left


def sign_pixels(width, height, lines, frame):
    """{(x, y): rgb} of the billboard: a red frame `frame` px wide round white, and `lines` [(font, text, rgb)]
    centred on it, spaced evenly down it."""
    out = {(x, y): COLORS["R"] if min(x, y, width - 1 - x, height - 1 - y) < frame else SIGN_RGB
           for x in range(width) for y in range(height)}
    inside = height - 2 * frame
    ink = sum(font[1] for font, _, _ in lines)
    gap = max(1, (inside - ink) // (len(lines) + 1))
    top = frame + (inside - ink - gap * (len(lines) - 1)) // 2
    for font, text, rgb in lines:
        out.update(_text_pixels(font, text, width / 2, top, rgb, shadow=False))
        top += font[1] + gap
    return out


# The art: each piece's rows, all the same height on a board, joined side by side.
COLORS = {  # the unnamed shades come from the riders' charts
    "A": (160, 15, 25),
    "B": (70, 130, 255),  # blue cars
    "C": (0, 128, 0),
    "G": (30, 145, 50),  # green: cars, the cab, the tree
    "H": (215, 25, 32),  # Santa hats, red sweaters
    "I": (75, 75, 90),  # iron grey
    "K": (58, 56, 72),  # outlines (black lifted to charcoal so it lights)
    "N": (110, 60, 25),  # brown: the cab's wood, the teddy
    "O": (245, 144, 38),  # Donald's bill
    "R": (235, 30, 30),  # red: cars, the engine, Santa
    "S": (185, 190, 200),  # silver: wheel rims, smoke shade
    "T": (245, 245, 250),  # sweater bands
    "W": (255, 255, 255),  # white: gloves, smoke, beards, eyes
    "X": (30, 150, 60),  # green sweaters
    "Y": (255, 195, 30),  # gold: hubs, trim, the star
    "a": (234, 207, 183),
    "b": (30, 70, 200),  # the blue cars' shade
    "c": (200, 200, 210),
    "d": (250, 195, 160),
    "e": (176, 195, 216),
    "f": (247, 189, 145),
    "g": (10, 85, 28),  # dark green
    "h": (150, 15, 22),  # the hats' and red sweaters' shade
    "i": (236, 180, 140),
    "j": (182, 171, 148),
    "k": (40, 40, 52),  # iron: wheels, smokestack
    "l": (230, 140, 120),
    "m": (150, 150, 160),
    "n": (135, 135, 145),
    "o": (230, 140, 40),
    "p": (200, 120, 20),
    "q": (185, 110, 45),
    "r": (150, 15, 20),  # dark red
    "s": (190, 70, 30),
    "t": (200, 42, 45),
    "u": (247, 4, 5),
    "v": (255, 0, 0),
    "w": (80, 80, 90),
    "x": (15, 95, 35),  # the green sweaters' shade
    "y": (238, 183, 0),  # Pluto's yellow
    "z": (139, 69, 19),
}

PLUTO_64 = [
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "...............................",
    "..................KKKKKK.......",
    "...............KKKKKKKKKK......",
    "...............KKKKKKKKKKK.....",
    "...............KKKKKK..KKK.....",
    "...........KK...KKK.....KKK....",
    "..........KKKKKK......yy.KK....",
    "..........KKKKKKKKyy.yyyyyK....",
    ".........KKKK..KKyyyyyWWWyKy...",
    "........KKKKK....yWWyWWWWyKyy..",
    "........KKKK......WWWWWWWyyyy..",
    ".........KK........WWWWWWyyy...",
    ".............KK....KKWKKWyy....",
    ".............KKK...KKWKKyyy....",
    ".............KKKzz.zzzyyyyyy...",
    ".............yKKyyzzyyzyKKyyy..",
    "......K.....yyyyyyyyzyyyKyyyy..",
    "......K.....yyzyyyyyyyyKKyyy...",
    "......K......zyzyyyyyyKKKyy....",
    "......KK........zzzzKKKvvy.....",
    ".......KK...........CvKvvy.....",
    "........K..........CCvKvvyC....",
    "........KK.........CCvvvvyCC...",
    ".........K..........CCvvCCCC...",
    ".........K.........yyCCCCCCC...",
    "........KK........yyyyyCCCC....",
    ".......KK........yyyyyyyyyyz...",
    "...KKKKK........yyyyyyyyyyyz...",
    "..KK...yyyy.....yyyyyyyyyyyz...",
    "..K...yyyyyyyyyyyyyyyyyyyyyz...",
    "..KRRyyyyyyyyyyyyyyyyyyyyyzRRRR",
    "..RRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "IIIBBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "IIIBBBBBBBBBBBBBBBBBBBBBBBBBBBI",
    "IIkBBBBSSSBBBBbbbbbBBBISSSBBBbk",
    "kkIbbISkkkSbbbbbbbbbbbSkkkSbbbI",
    "...IbSkkkkkSbbbbbbbbbSkkkkkSk..",
    ".....SkkYkkS.........SkkYkkS...",
    ".....SkkYkkS.........SkkYkkS...",
    ".....SSkkkSS.........SSkkkSS...",
    "......SSSSS...........SSSSS....",
]

GOOFY_64 = [
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "................AHHHAA..............",
    "................AHHHAA..............",
    "..............AAHHHHHHHHH...........",
    "..........AAAHHHHHHHHHHHHH..........",
    "..........AAAHHHHHHHHHHHHH..........",
    ".....WWWAAHHHHHHHHHHHHHHHH..........",
    ".....WWW...WWWWWWWWWWWWWWWWW........",
    ".....WWW...WWWWWWWWWWWWWWWWW........",
    "...........ccccccccccccccccc........",
    "........KKKKKKKKKWWWKKWWW...........",
    "........KKKKKKKKKWWWKKWWW...........",
    ".....KKKKKK..KKKWWWWWWWWW......KKK..",
    ".....KKK...KKKKKWKKWWWKWW...fffKKK..",
    ".....KKK...KKKKKWKKWWWKWW...fffKKK..",
    ".....KK...KKKKffWKKWWWKWW.ffffff....",
    "........KKK..fffffffffffffffffffff..",
    "........KKK..fffffffffffffffffffff..",
    ".......KKKK..Kffffffffffffffffffff..",
    ".......KKKK..KKKffffffffffffffff....",
    ".......KKKK..KKKffffffffffffffff....",
    ".......KKKK..KKKfKKKKKf..WWW.WWW....",
    ".......KKKK..KKKKffuuuKffWWW.WWW....",
    ".......KKKKKHKKKKffuuuKffWWW.WWW....",
    "........KKHHHKKKKfffuuuff...........",
    ".......KhHHHHHHHHHHHHhK.............",
    "......KhHHTTTTTTTTTTHHhK............",
    "......KhHTXTTXTTXTTXTHhK............",
    "......KhHHTTTTTTTTTTHHhK............",
    ".....KWWWHHHHHHHHHHHHWWWK...........",
    "..RRRKWWWKHHHHHHHHHHKWWWKRRRRRRRRRRR",
    "..RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "IIIGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "IIIGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGI",
    "IIkGGGGSSSGGGGggggggggggGGGISSSGGGgk",
    "kkIggISkkkSggggggggggggggggSkkkSgggI",
    "...IgSkkkkkSggggggggggggggSkkkkkSk..",
    ".....SkkYkkS..............SkkYkkS...",
    ".....SkkYkkS..............SkkYkkS...",
    ".....SSkkkSS..............SSkkkSS...",
    "......SSSSS................SSSSS....",
]

TREE_64 = [
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "..........................Y........",
    "........................YYYYY......",
    ".........................YYY.......",
    ".........................Y.Y.......",
    "..........................g........",
    ".........................Ggg.......",
    "........................GYGgg......",
    ".......................GGGGRgg.....",
    "..RRWR..................GGGgg......",
    ".RRRRWR...qq....qq.....GGGGGgg.....",
    "WRR..RWR.qlqqqqqqlq...GGRGGGYgg....",
    "RW....RW.qqqqqqqqqq..GGGGGGGGGgg...",
    "RR....RR..qqqqqqqq....GGGGGGGgg....",
    "......WR..qkqqqqkq...GGYGGGGGRgg...",
    "......RW..qqddddqq..GGGGGGGGGGGgg..",
    "......RR..qqdkkdqq.GGGRGGGGGGGGGgg.",
    "......WR...qddddq...GGGGGGGGGGYgg..",
    "......RW.qqRRrrRRqqGGGGGGGRGGGGGgg.",
    "......RR.NqqqqqqqqNGGGGGGGGGGGGGgg.",
    "......WR.NqqqqqqqqNGGGRGYGGGGGRGgg.",
    "......RW.NqqqqqqqqNGGGGGGGGGGGGGgg.",
    "......RR.NNqqqqqqNN......NNN.......",
    "..GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "..GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "...rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    ".IIRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRk",
    ".IkRRRRSSSRRRRRRRRRRRRRRRRSSSSRRRRk",
    "...rrrSkkkSrrrrrrrrrrrrrrSkkkkSNrr.",
    "...IrSkkkkkSrrrrrrrrrrrrSkkkkkkSr..",
    "....ISkkYkkS............SkkYYkkS...",
    ".....SkkYkkS............SkkYYkkS...",
    ".....SSkkkSS............SSkkkkSS...",
    "......SSSSS..............SSSSSS....",
]

DONALD_64 = [
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "...........AHHA...............",
    "..........AHHHHHH.............",
    ".......AAHHHHHHHHH............",
    "....WWAHHHHHHHHHHH............",
    "....WW..WWWWWWWWWWW...........",
    "........cccccccccccK..........",
    ".......KWWWKKWWWWWWWK.........",
    "......KKWWKWWKWWWWKKK.........",
    "......KWWKWWWKWWWKWWK.........",
    "......KWWKWWWWKWWKWWK.........",
    "......KWWKWWWWKWWKWWK.........",
    "......KWWKKKWWKWWKKWK.........",
    "......KWWKKKWWKWWKKWK.........",
    "......KOOKKKWWKWWKKWK.........",
    "......KOOKKKWKOOOOKKKKKK......",
    ".......KKOOKKOOOOOOOOOOOK.....",
    ".......KOKOOOOOOOKKKKKOOK.....",
    ".......KOOKKOOOKKOOKKKKK......",
    "........KOOOKKKWsKOK..........",
    ".........KOOKsWWsKOK..........",
    "..........KOOKssKKOK..........",
    "...........KOOKKKOOK..........",
    "..........KHKOOOOOK...........",
    ".......KKHHHHKKKKKHKK.........",
    "......KhHHHHHHHHHHHHhK........",
    ".....KhHHTTTTTTTTTTHHhK.......",
    ".....KhHTXTTXTTXTTXTHhK.......",
    ".....KhHHTTTTTTTTTTHHhK.......",
    "....KWWWHHHHHHHHHHHHWWWK......",
    "..RRKWWWKHHHHHHHHHHKWWWKRRRRRR",
    "..RRRRRRRRRRRRRRRRRRRRRRRRRRRR",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "...BBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "IIIBBBBBBBBBBBBBBBBBBBBBBBBBB.",
    "IIIBBBBBBBBBBBBBBBBBBBBBBBBBBI",
    "IIkBBBBSSSBBBBbbbbBBBISSSBBBbk",
    "kkIbbISkkkSbbbbbbbbbbSkkkSbbbI",
    "...IbSkkkkkSbbbbbbbbSkkkkkSk..",
    ".....SkkYkkS........SkkYkkS...",
    ".....SkkYkkS........SkkYkkS...",
    ".....SSkkkSS........SSkkkSS...",
    "......SSSSS..........SSSSS....",
]

GIFT_64 = [
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    ".............GG.GG............",
    "............GWGGGWG..RR..RR...",
    ".............GGgGG...RWRRWR...",
    "..........rRRRGRRRR..rRRRRr...",
    "...GG..GG.rRRRGRRRR.pYYrRYYYY.",
    "...GWGGWG.rRRRGRRRR.pYYrRYYYY.",
    "..rRRgGRRRrRRRGRRRR.pYYrRYYYY.",
    "..rRRgGRRRrRRRGRRRR.pYYrRYYYY.",
    "..rRRgGRRRrRRRGRRRR.pYYrRYYYY.",
    "..rRRgGRRRrRRRGRRRR.pYYrRYYYY.",
    "..rRRRRRRRRRRRRRRRRRRRRRRRRRRr",
    "..RRRRRRRRRRRRRRRRRRRRRRRRRRRr",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "IIIGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "IIIGGGGGGGGGGGGGGGGGGGGGGGGGGI",
    "IIkGGGGSSSGGGGggggGGGISSSGGGgk",
    "kkIggISkkkSggggggggggSkkkSgggI",
    "...IgSkkkkkSggggggggSkkkkkSk..",
    ".....SkkYkkS........SkkYkkS...",
    ".....SkkYkkS........SkkYkkS...",
    ".....SSkkkSS........SSkkkSS...",
    "......SSSSS..........SSSSS....",
]

MICKEY_64 = [
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "...................................",
    "..............KKK..................",
    ".............KtttKK................",
    "............KttttttKK..............",
    "...........KtttttttttK.............",
    ".......KKKKtttttttttttKKKKK........",
    ".....KKKKKKeeeetttttttKKKKKK.......",
    "....KKKKKKeeWWWWWtttttKKKKKKK......",
    "...KKKKKKKeWWWWWWWWtttWKKKKKK......",
    "...KKKKKKeeeeeeWWWWWWWWWKKKKKK.....",
    "...KKKKKKeeeKKeeeWWWWWWWeKKKKK.....",
    "...KKKKKKeeeKKKKeeeWWWWeeKKKKK.....",
    "...KKKKKKKeKKaKaKKeeeeeeKKKKKK.....",
    "....KKKKKKKaaKWKKWKKKKKKKKKKK......",
    ".....KKK.KKaaKWWKWWKaaKKKKKK.......",
    ".........KKaaKWWKWWKaaKKtttK.......",
    ".........KKaaaKWKKWKaaKKtttK.......",
    ".........KKKaaKWKKKaaKKKttttK......",
    "........KaaKaKaKaaKaaaaKetttK......",
    ".......KaaaaaaaKKKaaaKaKTTttKKK....",
    ".......KaaKaaaaKKKaaaKKKeTTTKTeK...",
    "........KaaaaaaaaaaaKaaaKeTTTeK....",
    ".........KaaajaaaaaaaaaK.KeeeK.....",
    "..........KaaaKKKKKaaKK...KKK......",
    "...........KKKalllaKK..............",
    "..............KaaaKXXK.............",
    "...........KKXXKKKXXXXXKK..........",
    "..........KxXXXXXXXXXXXXxK.........",
    ".........KxXXTTTTTTTTTTXXxK........",
    ".........KxXTHTTHTTHTTHTXxK........",
    ".........KxXXTTTTTTTTTTXXxK........",
    "........KWWWXXXXXXXXXXXXWWWK.......",
    "..GGGGGGKWWWKXXXXXXXXXXKWWWKGGGGGGG",
    "..GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "...RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "IIIRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.",
    "IIIRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRI",
    "IIkRRRRSSSRRRRrrrrrrrrrRRRISSSRRRrk",
    "kkIrrISkkkSrrrrrrrrrrrrrrrSkkkSrrrI",
    "...IrSkkkkkSrrrrrrrrrrrrrSkkkkkSk..",
    ".....SkkYkkS.............SkkYkkS...",
    ".....SkkYkkS.............SkkYkkS...",
    ".....SSkkkSS.............SSkkkSS...",
    "......SSSSS...............SSSSS....",
]

ENGINE_64 = [
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    ".............................................................",
    "..GGGGGGGGGGGGGGGGGGGGG...................kkkkkk.............",
    ".GGGGGGGGGGGGGGGGGGGGGGG.................kkkkkkkk............",
    "RRRRRRRRRRRRRRRRRRRRRRRRRR..............YYYYYYYYYY...........",
    "rrrrrrrrrrrrrrrrrrrrrrrrr...............pppppppppp...........",
    "..gGNNNNNrRRRRRRNNNNpYGg.................kkkIIIkk............",
    "..gGNNNNrRRRRRRRRNNNpYGg.......Y..........kkkIkk.............",
    "..gGNNNrRrWWWWWSRNNNpYGg......YYY..........kkIIk.............",
    "..gGNNNNSWWWWWWWSrNNpYGg.....YYYYY.........kIIIk.............",
    "..gGIINnWSllddSnWwNNpYGg.....pYYYp.........kIIIk.............",
    "..gGNINnndddddddnnNNpYGg.....rrrrr.........kIIIk.............",
    "..gGNkNNwdkdddkdlINNpYGg.....RRRRR.........kIIIk.............",
    "..gGNSNnSllnlNllSSNNpYGg.....RRRRR.........kIIIk.............",
    "..gGNRNSSSWWwnSSWWNNpYGgpYY.rRRRRRr.YYY..IkkkkkpYp...........",
    "..gGNRRnSSWWWSSSSSNNpYGgrpqrrrrprrrrNqprkkkkkkpYkkk..........",
    "..gGNRRRWWWWWWWWWrrrpYGgNYrrRRrYrrRRRYrrIIIIIYYkkkkk.........",
    "..gGNRRRSWWWWWWWSrRRpYGgYYRRRRYYRRRRYYrIIIIIpYkIIIIkk........",
    "..gGNNRRrnWWWWWSrRRRpYGgYrRRRrYrRRRYYRGIIIIIYYkIIIIIk........",
    "..gGNNNNRrwWWWnrRrrRpYGgYRRRRrYRRRRYYRgIIIIIYkIIIYNIkk.......",
    ".ggGNNNNRRrnnNRRRSwRpYGgYRRRRrYRRRRYYRgIIIIIYkIIIYNIIk.......",
    ".ggGNNNrRRRWSRrIISWrpYGgYrRRRrYRRRRYYRgIIIIIYkIIYYYYIk.......",
    ".ggpppppppppppppppppGGGgYrRRRrYRRRRYYrgIIIIIYkIIIYYIIk.......",
    ".ggGGGGGGGGGGGGGGGGGGGGgYrRRRrYrRRRYYRIIIIIIYkIIYIYIIk.......",
    ".ggGGgggggggggggggggGGGgYrRRRrYrrRRrYqrIIIIIYkkIIIIkkk.......",
    ".ggGGGGGGGGGGGGGGGGgGGGgpprrRrYprrrrYYrkIIIIpYkIIIIkk........",
    ".ggGGGGGGGGGGGGGGGGgGGGgrYrrrrNYrrrrrYpkkkkIrYrkkkkkk........",
    ".ggGGGGGGGGGGGGGGGGgGGGgIIIIIIIIIIIIIIIIIkkkkNpkkkkk.........",
    ".ggGGGGGGGGGGGGGGGGgGGGgkkkkkkkkkIkkkkkIIII.RRRRRRRRR........",
    "ISggkGgkSSkkkkSSkkkkkkkISSSkkkkkkkkSSSSkkII.rrrrrrrrr........",
    "IIggkgkSSkkkkkkSkkkkkkSSkkkSkkkkkkSSkkkSkkk.RRkRRkRRkR.......",
    "IkkgggkSkkkYYkkkSkkkkSSkkkkkkkkkkSSkkkkkSkk.RkRRkRRkRRk......",
    "kSSggkkkkkkkkkkkSkkkkSkkpkkkSkkkkSkkpkkkSSk.RRRkRRkRRkR......",
    ".....IkSkkpkkkkkkkkkkkkkkkkkkkkkkkkkkkkkSSk.RRkRRkRRkRRk.....",
    ".......SkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkISk.RkRRkRRkRRkRR....",
    ".......SSkkkkkkSS...SSIkkkkkSI...SkkkkkkSSI.RRRkRRkRRkRRk....",
    ".......SSSkkkkSSS....SSSkkkSS....SSSkkkSS...rrrrrrrrrrrr.....",
    "........SSSSSSSS.....SSSSSSS......SSSSSSS..........I.........",
]

PLUTO_32 = [
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "......ooo......",
    ".....ooooo.....",
    "....oWWWWWo....",
    "...KoWKWKWoK...",
    "...KoWKWKWoK...",
    "...K.ooooo.K...",
    "...KooKKKooK...",
    "...KooKKKooK...",
    "...KoooooooK...",
    "...KK.ooo.KK...",
    "...KK.ooo.KK...",
    ".....XXXXX.....",
    "....ooooooo....",
    ".RRoooRoRoooRRR",
    ".BBBBBBBBBBBBBB",
    ".BBBBBBBBBBBBBB",
    ".BBBBBBBBBBBBBB",
    "IBBBBBBBBBBBBBB",
    "IBBBBBBBBBBBBBB",
    "kI.SS.bbbb.SSb.",
    "..SkYS....SkYS.",
    "...SS......SS..",
]

GOOFY_32 = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "......HHA.......",
    ".....HHHHHA.....",
    ".....HHHHHHHW...",
    "....WWWWWWW.....",
    ".....KKKKK......",
    "....KKWWWKK.....",
    "....KWKWKWK.....",
    "...KKWKWKWKK....",
    "...KKiiiiiKK....",
    "...KiiKKKiiK....",
    "...KiiiiiiiK....",
    ".....iW.Wi......",
    ".....KHHHHHHK...",
    "...KhTXTXTXThK..",
    ".RKWWHHHHHHWWKRR",
    ".GGGGGGGGGGGGGGG",
    ".GGGGGGGGGGGGGGG",
    ".GGGGGGGGGGGGGGG",
    "IGGGGGGGGGGGGGGG",
    "IGGGGGGGGGGGGGGI",
    "kI.SS.ggggg.SSg.",
    "..SkYS.....SkYS.",
    "...SS.......SS..",
]

TREE_32 = [
    ".................",
    ".................",
    ".................",
    ".................",
    ".................",
    ".................",
    ".................",
    ".................",
    ".................",
    "............YY...",
    "............YY...",
    ".............g...",
    "............GGg..",
    ".RW..q..q...GGg..",
    "W..Wqqqqqq.GGGGg.",
    "R..R.qqqq..GGGGg.",
    "...R.qddq.GGGGGGg",
    "...W.qddq.GGGGGGg",
    "...RNqqqqGGGGGGGg",
    "...RNqqqqNGGGGGGg",
    ".GGGGGGGGGGGGGGGG",
    "..RRRRRRRRRRRRRRR",
    ".RRRRRRRRRRRRRRRR",
    ".RRRRRRRRRRRRRRRR",
    ".RRRRRRRRRRRRRRRR",
    "WRRRRRRRRRRRRRRRR",
    "..r.SSrrrrrr.SS.r",
    "..SSkYS.....SkYS.",
    "....SS.......SS..",
]

DONALD_32 = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "......HHA.......",
    ".....HHHHHA.....",
    ".....HHHHHHHW...",
    "....WWWWWWW.....",
    "....WmmWmmW.....",
    "....WmKWKmW.....",
    "...OWmKOKmWO....",
    "....OOOOOOO.....",
    ".....OOOOO......",
    "......OOO.......",
    ".....KHHHHHHK...",
    "...KhTXTXTXThK..",
    ".RKWWHHHHHHWWKRR",
    ".BBBBBBBBBBBBBBB",
    ".BBBBBBBBBBBBBBB",
    ".BBBBBBBBBBBBBBB",
    "IBBBBBBBBBBBBBBB",
    "IBBBBBBBBBBBBBBB",
    "kI.SS.bbbbb.SSb.",
    "..SkYS.....SkYS.",
    "...SS.......SS..",
]

GIFT_32 = [
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "...............",
    "......GGG......",
    "......RGR..RR..",
    ".GGGGRRRRRYYYYY",
    ".RRRRRRRRRYYYYY",
    ".RRRRRRRRRYYYYY",
    ".RRRRRRRRRRRRRR",
    ".GGGGGGGGGGGGGG",
    ".GGGGGGGGGGGGGG",
    ".GGGGGGGGGGGGGG",
    "IGGGGGGGGGGGGGG",
    "IGGGGGGGGGGGGGI",
    "kI.SS.gggg.SSg.",
    "..SkYS....SkYS.",
    "...SS......SS..",
]

MICKEY_32 = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "......HHA.......",
    ".....HHHHHA.....",
    ".....HHHHHHHW...",
    "...KWWWWWWWK....",
    "..KKKKK.KKKKK...",
    "..KKKKKKKKKKK...",
    "..KKKKiKiKKKK...",
    "...KKiiiiiKK....",
    "....KiKiKiK.....",
    "....KiKiKiK.....",
    "....iiiKiii.....",
    ".....iiiii......",
    "......iii.......",
    ".....KXXXXXXK...",
    "...KxTHTHTHTxK..",
    ".GKWWXXXXXXWWKGG",
    ".RRRRRRRRRRRRRRR",
    ".RRRRRRRRRRRRRRR",
    ".RRRRRRRRRRRRRRR",
    "IRRRRRRRRRRRRRRR",
    "IRRRRRRRRRRRRRRR",
    "kI.SS.rrrrr.SSr.",
    "..SkYS.....SkYS.",
    "...SS.......SS..",
]

ENGINE_32 = [
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    ".GGGGGGGGGGG.........kkk......",
    "RRRRRRRRRRRRR.......YYYYY.....",
    ".GNNrRRRNNYG.........kIk......",
    ".GNNWWWWSNYG...YY....kII......",
    ".WInWdddnNYG...Yr....kII......",
    "SWWNdddlSNYG..RRR....kII......",
    ".WRSSWWSWNYGpYrRRrYYkkkpk.....",
    ".GRRWWWWrRYGYRRYRRYrIIYkIk....",
    ".GNRrWWWRRYGYRRYRYYIIIYIIIk...",
    "gGNNRWSRSWYGYRRYRYYIIIYIYYI...",
    "ggppppppppGGYRRYRYYIIIYIYYI...",
    "gGGGGGGGGgGGpRRYrrYrIIYIIIk...",
    "gGGGGGGGGGGGIIIIIIIIkkYkkk....",
    "SgGGWGGGGkGIWkkkkkWkIIRRRR....",
    "IggSkkkkkkkkkkkkkkkkkkRRRRR...",
    "..Ik.SS.....SS....SS.kRRRRRR..",
    "...SSkkkkkkkkkkkkkkkS.RRRRRR..",
    ".....SS.....SS....SS..rrrrrr..",
]

BULBS = [COLORS["Y"], COLORS["G"], COLORS["W"], COLORS["B"]]  # round the billboard, chasing

# Left to right: the train drives right, so the engine leads; the billboard car goes on behind Pluto.
TRAIN_64 = [PLUTO_64, GOOFY_64, TREE_64, DONALD_64, GIFT_64, MICKEY_64, ENGINE_64]
TRAIN_32 = [PLUTO_32, GOOFY_32, TREE_32, DONALD_32, GIFT_32, MICKEY_32, ENGINE_32]
RIDERS = {  # who rides in which piece, by board
    True: {id(PLUTO_64): "pluto", id(GOOFY_64): "goofy", id(DONALD_64): "donald", id(MICKEY_64): "mickey",
           id(ENGINE_64): "santa"},
    False: {id(PLUTO_32): "pluto", id(GOOFY_32): "goofy", id(DONALD_32): "donald", id(MICKEY_32): "mickey",
            id(ENGINE_32): "santa"},
}

# Santa waving (not drawn yet): his forearm up out of his coat sleeve to a white mitten by his cheek, rocking
# between these two frames. Each is ENGINE_64's cab, rows 22-44 and columns 0-25, and replaces it whole.
SANTA_WAVE_AT = (0, 22)
SANTA_WAVE_64 = [
    [
        "..GGGGGGGGGGGGGGGGGGGGG...",
        ".GGGGGGGGGGGGGGGGGGGGGGG..",
        "RRRRRRRRRRRRRRRRRRRRRRRRRR",
        "rrrrrrrrrrrrrrrrrrrrrrrrr.",
        "..gGNNNNNrRRRRRRNNNNpYGg..",
        "..gGNNNNrRRRRRRRRNNNpYGg..",
        "..gGNNNrRrWWWWWSRNNNpYGg..",
        "..gGNNNNSWWWWWWWSrNNpYGg..",
        "..gGWWWnWSllddSnWwNNpYGg..",
        "..gGWWWnndddddddnnNNpYGg..",
        "..gGWWWIldkdddkdlINNpYGg..",
        "..gGrRNnSllnlNllSSNNpYGg..",
        "..gGRRNSSSWWwnSSWWNNpYGgpY",
        "..gGRRRnSSWWWSSSSSNNpYGgrp",
        "..gGRRRRWWWWWWWWWrrNpYGgNY",
        "..gGNRRRSWWWWWWWSrRRpYGgYY",
        "..gGNNRRrnWWWWWSrRRRpYGgYr",
        "..gGNNNRRrwWWWnrRrrRpYGgYR",
        ".ggGNNNRRRrnnRRRRSwRpYGgYR",
        ".ggGNNNrRRRWSRrHHSWrpYGgYr",
        ".ggpppppppppppppppppGGGgYr",
        ".ggGGGGGGGGGGGGGGGGGGGGgYr",
        ".ggGGgggggggggggggggGGGgYr",
    ],
    [
        "..GGGGGGGGGGGGGGGGGGGGG...",
        ".GGGGGGGGGGGGGGGGGGGGGGG..",
        "RRRRRRRRRRRRRRRRRRRRRRRRRR",
        "rrrrrrrrrrrrrrrrrrrrrrrrr.",
        "..gGNNNNNrRRRRRRNNNNpYGg..",
        "..gGNNNNrRRRRRRRRNNNpYGg..",
        "..gGNNNrRrWWWWWSRNNNpYGg..",
        "..gGNNNNSWWWWWWWSrNNpYGg..",
        "..gWWWNnWSllddSnWwNNpYGg..",
        "..gWWWNnndddddddnnNNpYGg..",
        "..gWWWNIldkdddkdlINNpYGg..",
        "..grRRNnSllnlNllSSNNpYGg..",
        "..gRRRNSSSWWwnSSWWNNpYGgpY",
        "..gRRRRnSSWWWSSSSSNNpYGgrp",
        "..gGRRRRWWWWWWWWWrrNpYGgNY",
        "..gGNRRRSWWWWWWWSrRRpYGgYY",
        "..gGNNRRrnWWWWWSrRRRpYGgYr",
        "..gGNNNRRrwWWWnrRrrRpYGgYR",
        ".ggGNNNRRRrnnRRRRSwRpYGgYR",
        ".ggGNNNrRRRWSRrRRSWrpYGgYr",
        ".ggpppppppppppppppppGGGgYr",
        ".ggGGGGGGGGGGGGGGGGGGGGgYr",
        ".ggGGgggggggggggggggGGGgYr",
    ],
]

# Art tools/build_sprite_editor.py puts in the sprite editor.
EDITOR_SPRITES = ["ENGINE_64", "SANTA_WAVE_64", "ENGINE_32"]
