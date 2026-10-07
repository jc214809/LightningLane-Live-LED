import math
import random

from display.animation.drawing import _blackout, walking_pixels
from display.animation.motion import FPS
from display.motion import ease_out, progress
from display.pixels import paint


class ChipDaleReveal:
    """
    One of two stories at random (STORY pins one). "meet": Chip runs in from the left and Dale
    from the right, each uncovering the new ride behind him, their feet stepping and a bob in
    their stride. They meet nose to nose in the middle, then turn round and scurry back off
    their own sides. "swing": Chip swings in on a rope from above the top left, Rescue Rangers
    style, uncovering the ride behind him, lets go at the bottom of the arc and skids to a
    stop. Dale swings in after him, doesn't let go in time and bonks into his back; Chip
    lurches forward, they wobble, and both scurry off the right edge.
    """

    STORIES = ("meet", "swing")
    STORY = None

    STEP = 2  # pixels a frame, steady: uneven steps judder at 1x (see Figment)
    GAP = 2  # columns between their noses when they meet
    MEET_S = 15 / FPS  # nose to nose in the middle; whole frames, so every step stays even
    TURN_S = 5 / FPS  # turned round, a beat before they run
    POSE_S = 2 / FPS  # each pose of the run (drawing.WALK_CYCLE); they bob a row as a foot lifts
    # (first foot row, columns of the back foot, columns of the front foot) in each one's art.
    CHIP_FEET = (22, range(0, 8), range(8, 17))
    DALE_FEET = (21, range(0, 8), range(8, 16))

    # Story "swing".
    SWING_S = 0.7  # from the top of the arc to the bottom, where Chip lets go
    ROPE_LEN = 40  # at least: a long rope's arc is too flat, a short one's too tight
    ROPE_ABOVE = 2  # the anchor is at least this far above the top edge (on 64x64, just this)
    PEEK = 2  # columns of each that show as he grabs the rope (the swing's start angle)
    HAND = (2, 4)  # where the rope meets each one's hand in the hang art
    ROPE = (150, 118, 84)  # dim tan twine
    SLIDE_S = 0.35  # Chip's skid after he lets go
    DALE_AFTER_S = 0.15  # Dale grabs his rope this long after Chip lets go
    BONK_S = 0.25  # Chip lurches forward and up, Dale knocked back
    LURCH, LURCH_UP, RECOIL = 4, 2, 2
    NOSE_IN = 3  # columns of Chip's back Dale's nose reaches when he bonks into him
    WOBBLE_S = 0.4  # both wobble a pixel, then run

    # From the user's pixel-art Rescue Rangers: Chip in his fedora and bomber jacket, Dale with
    # his red nose and Hawaiian shirt (mirrored to face the way he runs). Their black is lifted
    # to a charcoal, since LEDs draw black as off and Chip's jacket would be a hole; the pupils
    # stay near-black. 1x on both boards. '.' empty, K outline and jacket, P pupils, B brown fur,
    # C tan, W white, R red, Y yellow.
    CHIP_ART = [
        ".........KKK.....",
        ".......KKYYYK....",
        "......KYYBBBBK...",
        ".....KBBBKKKKKKK.",
        ".....KKKKYYYYYYYK",
        "....KYYYYKKKKKYK.",
        "...KYYKKKCWWWBK..",
        "...KYKBBBWWWKCK..",
        "....KKKKBWWPKCKKK",
        "....KBBBBBWWPWPKK",
        "....KBBCCBCWWWWK.",
        ".....KBCCCWPPWWK.",
        "....KKKKCCCWWPK..",
        "...KKKKKKKCCBK...",
        "...KKKKKCCCKK....",
        "..KKKKKKCCCCKK...",
        "..KKKKKKKCCCKK...",
        "..KCKKKKKCCKKKK..",
        "..KCCKKKKCCKKCK..",
        "..KKKBBCCCCKKCK..",
        "..KBBBBCCCCKBK...",
        "..KKKBBKCCKBKK...",
        ".KBBBBKKKKBBBBK..",
        "KKKKKKK..KKKKKK..",
    ]
    DALE_ART = [
        ".......KK.K.....",
        "......KBCKC.....",
        "......KBKKKK....",
        ".....KBBBBBBK...",
        ".....KBBBCCCBK..",
        "....KBBBCWWWBK..",
        "....KBBBWWWKCK..",
        "....KKKBWWPKCKRR",
        "...KBBBBBWWPWKRR",
        "...KBBCCBCWWWWKK",
        "....KBCCCWPPWWK.",
        "...KKKKCCCWWPK..",
        "..KRRKKKKCCBK...",
        "..KRYRKCCCKK....",
        ".KRRRRKCCCKRK...",
        ".KRRKRRKCKKRK...",
        ".KCKKRRRKKRKK...",
        ".KCCKRYRRYRKCK..",
        ".KKKKRRRRRRKCK..",
        ".KBBKKKKKKKKK...",
        ".KKKBBKCCKBKK...",
        "KBBBBKKKKBBBBK..",
        "KKKKKK..KKKKKK..",
    ]

    # Hanging from the rope: the same art with the back arm lifted from the shoulder, the hand
    # beside the head (Chip's sleeve charcoal like his jacket, Dale's arm bare with a short red
    # sleeve); the arm by their side is gone.
    CHIP_HANG_ART = [
        ".........KKK.....",
        ".......KKYYYK....",
        "......KYYBBBBK...",
        ".....KBBBKKKKKKK.",
        "..KK.KKKKYYYYYYYK",
        ".KCCKYYYYKKKKKYK.",
        ".KBKYYKKKCWWWBK..",
        ".KKKYKBBBWWWKCK..",
        ".KKKKKKKBWWPKCKKK",
        "..KKKBBBBBWWPWPKK",
        "..KKKBBCCBCWWWWK.",
        "..KKKKBCCCWPPWWK.",
        "...KKKKKCCCWWPK..",
        "...KKKKKKKCCBK...",
        "...KKKKKCCCKK....",
        "..KKKKKKCCCCKK...",
        "..KKKKKKKCCCKK...",
        "..KKKKKKKCCKKKK..",
        "..KKKKKKKCCKKCK..",
        "..KKKBBCCCCKKCK..",
        "..KBBBBCCCCKBK...",
        "..KKKBBKCCKBKK...",
        ".KBBBBKKKKBBBBK..",
        "KKKKKKK..KKKKKK..",
    ]
    DALE_HANG_ART = [
        ".......KK.K.....",
        "......KBCKC.....",
        "......KBKKKK....",
        ".....KBBBBBBK...",
        "..KK.KBBBCCCBK..",
        ".KCCKBBBCWWWBK..",
        ".KBKKBBBWWWKCK..",
        ".KBKKKKBWWPKCKRR",
        ".KBKBBBBBWWPWKRR",
        ".KBKBBCCBCWWWWKK",
        ".KRRKBCCCWPPWWK.",
        ".KRYRKKCCCWWPK..",
        "..KRRKKKKCCBK...",
        "...KRKKCCCKK....",
        "..KRRRKCCCKRK...",
        "..KRRKRKCKKRK...",
        "..KRYRRRKKRKK...",
        "..KRRRYRRYRKCK..",
        ".KKKKRRRRRRKCK..",
        ".KBBKKKKKKKKK...",
        ".KKKBBKCCKBKK...",
        "KBBBBKKKKBBBBK..",
        "KKKKKK..KKKKKK..",
    ]
    colors = {"K": (62, 54, 50), "P": (12, 12, 14), "B": (153, 98, 67), "C": (205, 164, 142),
              "W": (250, 250, 250), "R": (231, 29, 39), "Y": (250, 201, 18)}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.story = self.STORY or self.rng.choice(self.STORIES)
        self.chip_w, self.dale_w = len(self.CHIP_ART[0]), len(self.DALE_ART[0])
        self.chip_stop = width // 2 - self.GAP // 2 - self.chip_w
        self.dale_stop = width // 2 + self.GAP - self.GAP // 2
        # Both run the same even distance, so they arrive together on whole steps, each
        # starting just off his own edge.
        far = max(self.chip_stop + self.chip_w, width - self.dale_stop)
        self.distance = far + far % 2
        self.run_s = self.distance / (self.STEP * FPS)
        self.turn_at = self.run_s + self.MEET_S
        self.leave_at = self.turn_at + self.TURN_S
        self.duration = self.leave_at + self.run_s
        self.chip_art = {1: self.CHIP_ART, -1: [row[::-1] for row in self.CHIP_ART]}
        self.dale_art = {1: self.DALE_ART, -1: [row[::-1] for row in self.DALE_ART]}
        if self.story == "swing":
            self._plan_swing()

    def _plan_swing(self):
        hx, hy = self.HAND
        self.chip_floor = self.height - len(self.CHIP_ART)
        self.dale_floor = self.height - len(self.DALE_ART)
        # Chip skids to a stop just left of the middle; both ropes hang from one anchor, where
        # Dale, at the bottom of his arc, has his nose in Chip's back.
        self.chip_rest = self.width // 2 - 2
        above = max(self.ROPE_ABOVE, self.ROPE_LEN - self.chip_floor - hy)
        self.anchor = (self.chip_rest + self.NOSE_IN + 1 - self.dale_w + hx, -above)
        self.bottom_x = self.anchor[0] - hx
        self.rope_len = {"chip": self.chip_floor + hy + above, "dale": self.dale_floor + hy + above}
        # Steep enough that each grabs the rope just off the left edge.
        reach = self.bottom_x + self.chip_w - self.PEEK
        self.swing_angle = math.asin(min(1.0, reach / self.rope_len["chip"]))
        self.chip_grab, self.chip_lets_go = 0.0, self.SWING_S
        self.dale_grab = self.chip_lets_go + self.DALE_AFTER_S
        self.bonk_at = self.dale_grab + self.SWING_S
        self.run_at = self.bonk_at + self.BONK_S + self.WOBBLE_S
        self.chip_after = self.chip_rest + self.LURCH
        self.dale_after = self.bottom_x - self.RECOIL
        self.duration = self.run_at + (self.width - self.dale_after) / (self.STEP * FPS)

    def rope_angle(self, t, grab):
        """
        The rope's angle from straight down (radians, negative behind) for whoever grabbed it at
        grab: it swings down from swing_angle, fastest at the bottom, and once let go carries on
        up and away the other side. None before it's on the board or once it's gone.
        """
        if t < grab:
            return None
        p = (t - grab) / self.SWING_S
        if p <= 1:
            return -self.swing_angle * math.cos(math.pi / 2 * p)
        if p <= 2:
            return self.swing_angle * math.sin(math.pi / 2 * (p - 1))
        return None

    def rope_end(self, who, angle):
        ax, ay = self.anchor
        length = self.rope_len[who]
        return ax + length * math.sin(angle), ay + length * math.cos(angle)

    def swing_place(self, who, t):
        """(x, y, hanging) of who's art at t in story "swing", or None before he grabs the rope."""
        hx, hy = self.HAND
        grab, let_go = ((self.chip_grab, self.chip_lets_go) if who == "chip"
                        else (self.dale_grab, self.bonk_at))
        floor = self.chip_floor if who == "chip" else self.dale_floor
        if t < grab:
            return None
        if t < let_go:
            ex, ey = self.rope_end(who, self.rope_angle(t, grab))
            return ex - hx, ey - hy, True
        if who == "chip":
            if t < self.bonk_at:
                p = ease_out(progress(t, self.chip_lets_go, self.chip_lets_go + self.SLIDE_S))
                return self.bottom_x + (self.chip_rest - self.bottom_x) * p, floor, False
            p = progress(t, self.bonk_at, self.bonk_at + self.BONK_S)
            x = self.chip_rest + self.LURCH * ease_out(p)
            y = floor - self.LURCH_UP * math.sin(math.pi * p)
            start = self.chip_after
        else:
            p = progress(t, self.bonk_at, self.bonk_at + self.BONK_S)
            x, y = self.bottom_x - self.RECOIL * ease_out(p), floor
            start = self.dale_after
        if t >= self.run_at:
            return start + self.STEP * FPS * (t - self.run_at), floor, False
        return x, y, False

    def wobble(self, t, offset=0):
        """A pixel left or right while they're dazed after the bonk, the two out of step."""
        if not self.bonk_at + self.BONK_S <= t < self.run_at:
            return 0
        return 1 if (int((t - self.bonk_at) * FPS / 3) + offset) % 2 else -1

    def chip_x(self, t):
        step = self.STEP * FPS
        if t < self.run_s:
            return self.chip_stop - self.distance + step * t
        if t < self.leave_at:
            return self.chip_stop
        return self.chip_stop - step * (t - self.leave_at)

    def dale_x(self, t):
        step = self.STEP * FPS
        if t < self.run_s:
            return self.dale_stop + self.distance - step * t
        if t < self.leave_at:
            return self.dale_stop
        return self.dale_stop + step * (t - self.leave_at)

    def facing(self, t):
        """(Chip's, Dale's): 1 facing right, -1 left. Towards each other, then away."""
        return (1, -1) if t < self.turn_at else (-1, 1)

    def running(self, t):
        return t < self.run_s or t >= self.leave_at

    def pose(self, t, offset=0):
        """Which pose of the run each is in at t (None standing); offset keeps Dale out of step."""
        return int(t / self.POSE_S) + offset if self.running(t) else None

    def hop(self, t, offset=0):
        """Rows lifted at t: one, while a foot is up."""
        pose = self.pose(t, offset)
        return 0 if pose is None else pose % 2

    def _mirror_feet(self, feet, w):
        top, behind, ahead = feet
        return top, {w - 1 - c for c in behind}, {w - 1 - c for c in ahead}

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        if self.story == "swing":
            self._overlay_swing(canvas, t)
        else:
            self._overlay_meet(canvas, t)
        return True

    def _rope_pixels(self, who, t, grab):
        angle = self.rope_angle(t, grab)
        if angle is None:
            return []
        (ax, ay), (ex, ey) = self.anchor, self.rope_end(who, angle)
        n = max(1, int(max(abs(ex - ax), abs(ey - ay))))
        return [((int(round(ax + (ex - ax) * i / n)), int(round(ay + (ey - ay) * i / n))), self.ROPE)
                for i in range(n + 1)]

    def reveal_x(self, t):
        """Story "swing": the first column still dark at t, from Chip's middle (his wobble doesn't
        count); None once they run and the ride is all uncovered."""
        if t >= self.run_at:
            return None
        return max(0, int(round(self.swing_place("chip", t)[0])) + self.chip_w // 2)

    def _overlay_swing(self, canvas, t):
        edge = self.reveal_x(t)
        if edge is not None:
            _blackout(canvas, edge, self.width, self.height)
        for who, grab in (("chip", self.chip_grab), ("dale", self.dale_grab)):
            paint(canvas, self._rope_pixels(who, t, grab), self.width, self.height)
        running = t >= self.run_at
        for who, offset in (("chip", 0), ("dale", 1)):
            place = self.swing_place(who, t)
            if place is None:
                continue
            x, y, hanging = place
            x, y = int(round(x)) + self.wobble(t, offset), int(round(y))
            if hanging:
                art = self.CHIP_HANG_ART if who == "chip" else self.DALE_HANG_ART
                feet, pose = (len(art), (), ()), None
            else:
                art = self.CHIP_ART if who == "chip" else self.DALE_ART
                feet = self.CHIP_FEET if who == "chip" else self.DALE_FEET
                pose = int((t - self.run_at) / self.POSE_S) + offset if running else None
                y -= 0 if pose is None else pose % 2
            paint(canvas, walking_pixels(art, x, y, self.colors, feet, pose), self.width, self.height)

    def _overlay_meet(self, canvas, t):
        cx, dx = int(round(self.chip_x(t))), int(round(self.dale_x(t)))
        if t < self.run_s:  # still dark between them, from each one's middle
            _blackout(canvas, cx + self.chip_w // 2, min(self.width, dx + self.dale_w // 2), self.height)
        chip_facing, dale_facing = self.facing(t)
        for who, x, offset in (("dale", dx, 1), ("chip", cx, 0)):
            w = self.dale_w if who == "dale" else self.chip_w
            facing = dale_facing if who == "dale" else chip_facing
            feet = self.DALE_FEET if who == "dale" else self.CHIP_FEET
            art = (self.dale_art if who == "dale" else self.chip_art)[facing]
            if facing < 0:
                feet = self._mirror_feet(feet, w)
            y = self.height - len(art) - self.hop(t, offset)
            pixels = walking_pixels(art, x, y, self.colors, feet, self.pose(t, offset), facing)
            paint(canvas, pixels, self.width, self.height)


class ChipDaleSwingReveal(ChipDaleReveal):
    """Chip 'n' Dale's rope swing every time, for force_surprise ("chip_dale_swing")."""

    STORY = "swing"
