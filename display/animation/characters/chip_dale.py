from display.animation.drawing import _blackout, walking_pixels
from display.animation.motion import FPS
from display.pixels import paint


class ChipDaleReveal:
    """
    Chip runs in from the left and Dale from the right, each uncovering the new ride behind
    him, their feet stepping and a bob in their stride. They meet nose to nose in the middle,
    then turn round and scurry back off their own sides.
    """

    STEP = 2  # pixels a frame, steady: uneven steps judder at 1x (see Figment)
    GAP = 2  # columns between their noses when they meet
    MEET_S = 15 / FPS  # nose to nose in the middle; whole frames, so every step stays even
    TURN_S = 5 / FPS  # turned round, a beat before they run
    POSE_S = 2 / FPS  # each pose of the run (drawing.WALK_CYCLE); they bob a row as a foot lifts
    # (first foot row, columns of the back foot, columns of the front foot) in each one's art.
    CHIP_FEET = (22, range(0, 8), range(8, 17))
    DALE_FEET = (21, range(0, 8), range(8, 16))

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
    colors = {"K": (62, 54, 50), "P": (12, 12, 14), "B": (153, 98, 67), "C": (205, 164, 142),
              "W": (250, 250, 250), "R": (231, 29, 39), "Y": (250, 201, 18)}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
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
        return True
