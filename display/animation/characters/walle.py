import math
import random

from display.animation.drawing import _blackout
from display.animation.mechanics import CapturesScreens
from display.animation.motion import ease_out


class WallEReveal(CapturesScreens):
    """
    WALL-E rolls in along the bottom over the old screen, stops in a puff of dust, tilts
    his head and blinks at us, then opens his compactor hatch and vacuums the old screen
    up: its pixels fly into the hatch nearest-first, leaving the board black. The hatch
    closes, a trash cube with a sprout on top drops into the gap between his treads, and
    he trundles off the right edge carrying it, uncovering the new screen in his wake.

    Needs the previous screen's pixels, so it opts in via wants_prev, like Ralph.
    He stays 1x on both boards: doubled he'd cover most of the screen he's compacting.
    """

    wants_prev = True
    SCALE = 1
    ENTER_S, LOOK_S, SWEEP_S, FLY_S, DROP_S, LEAVE_S = 0.8, 0.9, 0.9, 0.3, 0.3, 1.0
    COMPACT_S = SWEEP_S + FLY_S
    # The visit, in order; "compact" is when the old screen is eaten and "leave" is last.
    PHASES = (("enter", ENTER_S), ("look", LOOK_S), ("compact", COMPACT_S), ("drop", DROP_S),
              ("leave", LEAVE_S))
    duration = sum(s for _, s in PHASES)
    STOP_X = 3
    BLINK_AT, BLINK_S = 0.55, 0.14  # into the look
    TILT_S = 0.4  # the look's first part: head tilted, then level for the blink

    # WALL-E in three-quarter view: binocular eyes on a short neck, a boxy yellow body
    # (front face lit, right side shaded) with a dark charge panel and the compactor
    # hatch's seam, grey arms on both sides, and a tread on each side with a gap between.
    # '.' empty, K outline, E eye housing, L lens, G glint, N neck, Y body front,
    # D body side (shade), S charge panel, A arm, T tread, W tread highlight.
    ART = [
        "..KKKKKK...KKKKKK...",
        ".KEEEEEEK.KEEEEEEK..",
        ".KELLLLEK.KELLLLEK..",
        ".KELGLLEK.KELGLLEK..",
        ".KEELLEEK.KEELLEEK..",
        "..KKKKKK...KKKKKK...",
        ".......KNNK.........",
        ".......KNNK.........",
        "..KKKKKKKKKKKKKKKK..",
        "..KYYYYYYYYYYYDDDK..",
        "KKKYSSYYYYYYYYDDDKKK",
        "KAKYYYYYYYYYYYDDDKAK",
        "KAKYKKKKKKKKKYDDDKAK",
        "KAKYYYYYYYYYYYDDDKAK",
        "KKKYYYYYYYYYYYDDDKKK",
        "..KKKKKKKKKKKKKKKK..",
        "KKKKKKK......KKKKKKK",
        "KTWTWTK......KTWTWTK",
        "KWTWTWK......KWTWTWK",
        "KKKKKKK......KKKKKKK",
    ]
    COLORS = {
        "K": (30, 26, 20),
        "E": (175, 175, 185),
        "L": (60, 80, 120),
        "G": (255, 255, 255),
        "N": (140, 140, 150),
        "Y": (240, 190, 40),
        "D": (180, 125, 20),
        "S": (70, 70, 75),
        "A": (150, 150, 160),
        "T": (80, 80, 85),
        "W": (160, 160, 165),
    }
    EYE_ROWS = range(0, 6)
    HATCH_ROWS, HATCH_COLS = (12, 13), range(5, 12)  # the seam drops open into a slot while compacting
    INTAKE = (8, 12)  # sprite cell the old screen is vacuumed into
    CUBE_COLS, CUBE_ROWS = range(7, 13), range(14, 20)  # sits in the gap between the treads
    # The sprout on top of the cube, as (col, row) sprite cells: a Y of two leaves on a stem.
    PLANT = [(9, 11, "leaf"), (11, 11, "leaf"), (10, 12, "stem"), (10, 13, "stem")]
    PLANT_RGB = {"leaf": (120, 255, 120), "stem": (40, 170, 60)}
    CUBE_EDGE_RGB = (110, 110, 115)  # lighter than his outline, so the cube stands clear of him
    DUST_RGB = (150, 135, 110)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.sprite_w, self.sprite_h = len(self.ART[0]), len(self.ART)
        self.y0 = height - self.sprite_h
        self.prev_px = {}
        self.flights = []
        self.cube = [self.CUBE_EDGE_RGB] * 4  # an empty screen makes a plain grey cube
        self.dust = []
        self._dusted = set()

    def capture_prev(self, prev_draw, prev_t):
        """The old screen's pixels get vacuumed up."""
        super().capture_prev(prev_draw, prev_t)
        ix, iy = self.intake()
        # Nearest first: each pixel lifts off when the sweep front reaches it.
        self.flights = sorted(
            (math.hypot(x - ix, y - iy), x, y, rgb) for (x, y), rgb in self.prev_px.items())
        # The cube is made of what he ate: its most common colours, dimmed by the squash.
        counts = {}
        for rgb in self.prev_px.values():
            counts[rgb] = counts.get(rgb, 0) + 1
        common = sorted(counts, key=counts.get, reverse=True)[:4]
        if common:
            self.cube = [tuple(int(c * 0.8) for c in common[i % len(common)]) for i in range(4)]

    # --- timeline ---

    def _phase(self, t):
        """(phase name, seconds into it) at t."""
        for name, length in self.PHASES[:-1]:
            if t < length:
                return name, t
            t -= length
        return self.PHASES[-1][0], t

    def phase_start(self, name):
        """When a phase begins, in seconds from the start of the visit."""
        start = 0.0
        for phase, length in self.PHASES:
            if phase == name:
                return start
            start += length
        raise KeyError(name)

    def walle_x(self, t):
        """His left edge: rolls in from off the left, stops, then drives off the right."""
        phase, p = self._phase(t)
        if phase == "enter":
            return -self.sprite_w + ease_out(p / self.ENTER_S) * (self.STOP_X + self.sprite_w)
        if phase == "leave":
            q = min(1.0, p / self.LEAVE_S)
            return self.STOP_X + q * q * (self.width - self.STOP_X + 1)  # pulls away slowly, then goes
        return float(self.STOP_X)

    def intake(self):
        """Where the sweep starts from, on the board."""
        return self.STOP_X + self.INTAKE[0], self.y0 + self.INTAKE[1]

    def flight_target(self, t):
        """Where the old screen's pixels fly to this frame."""
        return self.intake()

    def sweep_radius(self, t):
        """How far from the hatch the old screen has been taken; -1 before compacting."""
        phase, p = self._phase(t)
        if t < self.phase_start("compact"):
            return -1.0
        if phase == "compact" and p < self.SWEEP_S:
            far = self.flights[-1][0] if self.flights else 0.0
            return p / self.SWEEP_S * (far + 1)
        return float("inf")

    # --- drawing ---

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        self._draw_old_screen(canvas, t)
        self._draw_flights(canvas, t)
        self._step_dust(t)
        x = self.walle_x(t)
        self._draw_walle(canvas, t, x)
        self._draw_dust(canvas)
        return True

    def _draw_old_screen(self, canvas, t):
        """
        Until he leaves, the board is his: black, with whatever of the old screen he hasn't
        eaten yet. As he rolls out, the new screen is uncovered in his wake.
        """
        if self._phase(t)[0] == "leave":
            _blackout(canvas, int(self.walle_x(t)), self.width, self.height)
            return
        _blackout(canvas, 0, self.width, self.height)
        radius = self.sweep_radius(t)
        for dist, x, y, rgb in reversed(self.flights):
            if dist <= radius:
                break
            canvas.SetPixel(x, y, *rgb)

    def _draw_flights(self, canvas, t):
        """Pixels the front has passed, accelerating into the hatch."""
        phase, p = self._phase(t)
        if phase != "compact" or not self.flights:
            return
        far = self.flights[-1][0] + 1
        ix, iy = self.flight_target(t)
        for dist, x, y, rgb in self.flights:
            lift = self.SWEEP_S * dist / far  # when the front passed it
            q = (p - lift) / self.FLY_S
            if q < 0:
                break
            if q >= 1:
                continue
            q = q * q
            canvas.SetPixel(int(round(x + (ix - x) * q)), int(round(y + (iy - y) * q)), *rgb)

    def _step_dust(self, t):
        """A puff from the treads as he stops, and again as he pulls away."""
        for at in (self.ENTER_S - 0.1, self.phase_start("leave")):
            if t >= at and at not in self._dusted:
                self._dusted.add(at)
                x = self.walle_x(at)
                for side_x, push in ((x, -1), (x + self.sprite_w - 1, 1)):
                    for _ in range(4):
                        self.dust.append([side_x, self.height - 1.5, at,
                                          push * self.rng.uniform(4, 10), -self.rng.uniform(2, 6)])
        self.dust = [d for d in self.dust if t - d[2] < 0.5]
        self._t = t

    def _draw_dust(self, canvas):
        under = getattr(canvas, "px", {})
        for x0, y0, born, vx, vy in self.dust:
            age = self._t - born
            px, py = int(round(x0 + vx * age)), int(round(y0 + vy * age))
            if not (0 <= px < self.width and 0 <= py < self.height):
                continue
            f = 1 - age / 0.5
            base = under.get((px, py), (0, 0, 0))
            canvas.SetPixel(px, py, *(min(255, int(b + c * f)) for b, c in zip(base, self.DUST_RGB)))

    def _cell(self, t, row, col, kind):
        """The colour key at one sprite cell this frame: treads roll, eyes blink, hatch opens."""
        phase, p = self._phase(t)
        if kind in "TW" and phase in ("enter", "leave"):
            if int(self.walle_x(t)) % 2:
                kind = "W" if kind == "T" else "T"
        if row in self.EYE_ROWS and phase == "look" and self.BLINK_AT <= p < self.BLINK_AT + self.BLINK_S:
            if kind in "LG":
                kind = "K" if row == 3 else "E"
        if phase == "compact" and row in self.HATCH_ROWS and col in self.HATCH_COLS:
            kind = "K"
        return kind

    def _draw_walle(self, canvas, t, x):
        x0 = int(round(x))
        phase, p = self._phase(t)
        tilt = phase == "look" and p < self.TILT_S
        for row, line in enumerate(self.ART):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                kind = self._cell(t, row, col, kind)
                # The curious tilt: his left eye lifts a row while the right stays put.
                dy = -1 if tilt and row in self.EYE_ROWS and col < 10 else 0
                self._px(canvas, x0 + col, self.y0 + row + dy, self.COLORS[kind])
        if phase in ("drop", "leave"):
            self._draw_cube(canvas, x0, min(1.0, p / self.DROP_S) if phase == "drop" else 1.0)

    def _draw_cube(self, canvas, x0, drop):
        """The trash cube, sliding down out of the hatch into the gap between his treads."""
        lift = int(round((1 - drop) * 3))
        top = self.y0 + self.CUBE_ROWS[0] - lift
        left = x0 + self.CUBE_COLS[0]
        n = len(self.CUBE_COLS)
        for r in range(n):
            for c in range(n):
                edge = r in (0, n - 1) or c in (0, n - 1)
                rgb = self.CUBE_EDGE_RGB if edge else self.cube[(r // 2 + c // 2) % len(self.cube)]
                self._px(canvas, left + c, top + r, rgb)
        if drop >= 1:
            for col, row, part in self.PLANT:
                self._px(canvas, x0 + col, self.y0 + row, self.PLANT_RGB[part])

    def _px(self, canvas, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            canvas.SetPixel(x, y, *rgb)


class WallESideReveal(WallEReveal):
    """
    WALL-E in profile, drawn from a side-on photo of him, working like the trash baler he
    is. He rolls in facing his travel, swivels his head round to look at us (a bob and a
    blink), then turns back and gets to work:

    1. Collect: his chest door drops open and the whole old screen flies in through it,
       nearest pixels first, leaving the board black.
    2. Compress: the door shuts and he jolts as the press inside crushes it all.
    3. Eject: the door opens and the finished cube slides out and drops to the ground.
    4. Pick up: his arm reaches down, grabs the cube and lifts it.

    Then he drives off the right edge carrying it, uncovering the new screen in his wake.
    """

    ENTER_S, LOOK_S, SWEEP_S, FLY_S, LEAVE_S = 0.8, 0.8, 0.9, 0.3, 1.0
    OPEN_S, CLOSE_S, PRESS_S, EJECT_S, PICKUP_S = 0.15, 0.15, 0.5, 0.45, 0.45
    COMPACT_S = SWEEP_S + FLY_S
    PHASES = (("enter", ENTER_S), ("look", LOOK_S), ("open", OPEN_S), ("compact", COMPACT_S),
              ("close", CLOSE_S), ("press", PRESS_S), ("eject", EJECT_S), ("pickup", PICKUP_S),
              ("leave", LEAVE_S))
    duration = sum(s for _, s in PHASES)
    BLINK_AT = 0.45

    # Facing left as in the photo, and mirrored when drawn so he faces right, the way he
    # travels: a boxy head on a bent neck, the body's grey top rim, his arm tucked against
    # his front (yellow cuff, small grey claw), the big triangular tread over the body's
    # lower front, and the round disc on his back. The photo's long striped forearm is left
    # out: drawn at this size it read as a row of dots.
    # '.' empty, K outline, H head, L lens, G glint, N neck, R rim, Y body, D body shade,
    # M back disc, C claw and forearm, U cuff, T tread, V tread wheel.
    ART = [
        "..KKKKKKKKKKKK.....",
        "..KGLHHHHHHHHK.....",
        "..KLLHHHHHHHHK.....",
        "..KKKKKKKKKKKK.....",
        "..........KNK......",
        "...........KNK.....",
        ".....KRRRRRRRRRRRK.",
        "...KKKKYYYYYYYYYDK.",
        "..KCUUKYYYYYYYYYDKM",
        "..KCKKKYYYYYYYYYDKM",
        "..KK.KYYYYYYYYYYDKM",
        ".....KYYYYYKVKYYDKM",
        ".....KYYYYKVTVKYDKM",
        ".....KYYYYKVVTVKDKM",
        ".....KYYYKVTTTVKDK.",
        ".....KYYKVTTTTTVKK.",
        ".....KYKVVTTTTVTVK.",
        ".....KKVTTTTTTTTVK.",
        ".....KVVVVVVVVVVVVK",
        "....KKKKKKKKKKKKKKK",
    ]
    COLORS = {
        "K": (30, 26, 20),
        "H": (175, 175, 185),
        "E": (175, 175, 185),
        "L": (60, 80, 120),
        "G": (255, 255, 255),
        "N": (140, 140, 150),
        "R": (150, 150, 155),
        "Y": (240, 190, 40),
        "D": (180, 125, 20),
        "M": (200, 145, 30),
        "C": (150, 150, 160),
        "U": (255, 220, 60),
        "T": (55, 55, 60),
        "V": (160, 160, 165),
    }
    # His head turned to face us: both binocular lenses, in the same box.
    HEAD_FRONT = [
        "KKKKKKKKKKKK",
        "KELLEKKELLEK",
        "KELGEKKEGLEK",
        "KKKKKKKKKKKK",
    ]
    HEAD_ROWS, HEAD_COL = range(0, 4), 2
    TURN_S = 0.12  # into the look: the head swivels round, and back at the end
    BOB_S = 0.3  # one bob of the head on its neck
    # All in drawn (mirrored) sprite cells, where his front is on the right.
    FRONT_COL = 13  # the front face of his body
    DOOR_ROWS, DOOR_COLS = range(11, 15), (12, 13)  # the chest opening, dark while the door's open
    # The door: a panel hinged at the bottom of the opening that swings down and out until it
    # lies flat. Shut, it's edge-on (his outline); open, we see its yellow inside face.
    DOOR_HINGE, DOOR_LEN, DOOR_SWING_S = (13, 15), 3, 0.12
    INTAKE = (13, 12)  # the old screen flies in here
    ARM_ROWS, ARM_COLS = range(7, 11), range(13, 17)  # the tucked arm: cuff and claw
    ARM_DROP = 5  # how far the claw reaches down to the cube on the ground
    CUBE_SIZE = 4  # fits the door
    CUBE_GROUND = (16, 16)  # the cube's top-left once it's out, on the ground just past the flap
    CUBE_OUT_ROW = 11  # the row it slides out at, level with the door
    PRESS_JOLT_S = 0.1
    # The sprout on the cube's top, clear of the claw's grip: (col, row) from its top-left.
    PLANT = [(2, -2, "leaf"), (4, -2, "leaf"), (3, -1, "stem")]

    def __init__(self, width, height, rng=None):
        super().__init__(width, height, rng)
        self.art = [row[::-1] for row in self.ART]

    def intake(self):
        return self.STOP_X + self.INTAKE[0], self.y0 + self.INTAKE[1]

    # --- the look ---

    def facing_us(self, t):
        phase, p = self._phase(t)
        return phase == "look" and self.TURN_S <= p < self.LOOK_S - self.TURN_S

    def head_bob(self, t):
        """The curious bob: his head dips a row on its neck and comes back up, once."""
        phase, p = self._phase(t)
        return 1 if phase == "look" and self.TURN_S <= p < self.TURN_S + self.BOB_S else 0

    # --- the baler ---

    def door_angle(self, t):
        """0 shut to 1 lying flat open: it swings open to collect and to eject, and shut after each."""
        phase, p = self._phase(t)
        swing = lambda q: ease_out(min(1.0, q / self.DOOR_SWING_S))
        if phase == "open":
            return swing(p)
        if phase == "compact":
            return 1.0
        if phase == "close":
            return 1 - swing(p)
        if phase == "eject":
            return swing(p)
        if phase == "pickup":
            return 1 - swing(p)
        return 0.0

    def door_open(self, t):
        return self.door_angle(t) > 0

    def door_cells(self, angle):
        """The door panel's cells (col, row), swung `angle` (0-1) from shut toward flat."""
        hx, hy = self.DOOR_HINGE
        a = angle * math.pi / 2
        return [(hx + round(i * math.sin(a)), hy - round(i * math.cos(a))) for i in range(1, self.DOOR_LEN + 1)]

    def jolt(self, t):
        """The press working: his whole body jolts back and forth a column."""
        phase, p = self._phase(t)
        return 1 if phase == "press" and int(p / self.PRESS_JOLT_S) % 2 == 0 else 0

    def arm_drop(self, t):
        """How far the claw has reached down: down to the cube and back up with it."""
        phase, p = self._phase(t)
        if phase != "pickup":
            return 0
        q = p / self.PICKUP_S
        down = ease_out(q * 2) if q < 0.5 else 1 - ease_out((q - 0.5) * 2)
        return round(self.ARM_DROP * down)

    def cube_at(self, t):
        """The cube's top-left in sprite cells, or None while it's still inside him."""
        phase, p = self._phase(t)
        ground_x, ground_y = self.CUBE_GROUND
        if phase == "eject":
            q = p / self.EJECT_S
            if q < 0.6:  # slides out of the door...
                return self.FRONT_COL - self.CUBE_SIZE + ease_out(q / 0.6) * (ground_x - self.FRONT_COL + self.CUBE_SIZE), \
                    self.CUBE_OUT_ROW
            fall = ((q - 0.6) / 0.4) ** 2  # ...and drops to the ground
            return ground_x, self.CUBE_OUT_ROW + fall * (ground_y - self.CUBE_OUT_ROW)
        if phase == "pickup" and p < self.PICKUP_S / 2:
            return ground_x, ground_y
        if phase in ("pickup", "leave"):
            claw_tip = self.ARM_ROWS[-1] + self.arm_drop(t)
            return ground_x, claw_tip + 1  # hanging from the claw
        return None

    # --- drawing ---

    def _draw_walle(self, canvas, t, x):
        x0 = int(round(x)) + self.jolt(t)
        phase, p = self._phase(t)
        rolling = phase in ("enter", "leave") and int(x) % 2
        blinking = phase == "look" and self.BLINK_AT <= p < self.BLINK_AT + self.BLINK_S
        front, bob, drop = self.facing_us(t), self.head_bob(t), self.arm_drop(t)
        door = self.door_open(t)
        for row, line in enumerate(self.art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                dy = 0
                if row in self.HEAD_ROWS:
                    dy = bob
                    if front:
                        continue  # drawn below, turned toward us
                    if blinking and kind in "LG":
                        kind = "H"
                if self._is_arm(row, col, kind):
                    continue  # the arm is drawn on top of everything, below
                if door and row in self.DOOR_ROWS and col in self.DOOR_COLS:
                    kind = "K"  # the dark inside of his chest
                if door and (col, row) == self.DOOR_HINGE:
                    kind = "Y"  # the hinge: yellow, joining the open door to his body
                if rolling and kind in "TV":
                    kind = "V" if kind == "T" else "T"
                self._px(canvas, x0 + col, self.y0 + row + dy, self.COLORS[kind])
        if front:
            left = x0 + self.sprite_w - self.HEAD_COL - len(self.HEAD_FRONT[0])
            for row, line in enumerate(self.HEAD_FRONT):
                for col, kind in enumerate(line):
                    if blinking and kind in "LG":
                        kind = "K" if row == 2 else "E"
                    self._px(canvas, left + col, self.y0 + row + bob, self.COLORS[kind])
        if door:
            for col, row in self.door_cells(self.door_angle(t)):
                self._px(canvas, x0 + col, self.y0 + row, self.COLORS["Y"])
        cube = self.cube_at(t)
        if cube:
            self._draw_cube(canvas, x0, cube, clip=phase == "eject")
        self._draw_arm(canvas, x0, drop)

    def _draw_arm(self, canvas, x0, drop):
        """The cuff and claw, lowered by `drop`, on a grey forearm down from his shoulder."""
        for i in range(drop):
            self._px(canvas, x0 + self.ARM_COLS[1], self.y0 + self.ARM_ROWS[1] + i, self.COLORS["C"])
        for row in self.ARM_ROWS:
            for col in self.ARM_COLS:
                kind = self.art[row][col]
                if self._is_arm(row, col, kind):
                    self._px(canvas, x0 + col, self.y0 + row + drop, self.COLORS[kind])

    def _is_arm(self, row, col, kind):
        """A cell of the tucked arm. Its first column is also his front: there only the cuff moves."""
        if kind == "." or row not in self.ARM_ROWS or col not in self.ARM_COLS:
            return False
        return col != self.FRONT_COL or kind in "CU"

    def _draw_cube(self, canvas, x0, at, clip=False):
        """The trash cube; while it's coming out, only the part past his front shows."""
        left, top = x0 + int(round(at[0])), self.y0 + int(round(at[1]))
        n = self.CUBE_SIZE
        for r in range(n):
            for c in range(n):
                if clip and left + c <= x0 + self.FRONT_COL:
                    continue
                edge = r in (0, n - 1) or c in (0, n - 1)
                rgb = self.CUBE_EDGE_RGB if edge else self.cube[(r + c) % len(self.cube)]
                self._px(canvas, left + c, top + r, rgb)
        if not clip or left > x0 + self.FRONT_COL:
            for col, row, part in self.PLANT:
                self._px(canvas, left + col, top + row, self.PLANT_RGB[part])
