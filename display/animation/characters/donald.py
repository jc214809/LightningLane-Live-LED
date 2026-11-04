import math
import random

from display.animation.drawing import _blackout, walking_pixels
from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS
from display.pixels import blend, paint


class DonaldReveal(CapturesScreens):
    """
    Donald Duck boils over. He walks in from the right over the old ride and stops; red fills
    his face from the neck up while he trembles harder and harder and steam puffs from his
    head; then a flash, and the old screen blasts apart outward from him in a burst of
    feathers, leaving the new ride, while he hops on one foot with his fists pumping. The red
    drains away, a last puff of steam, and he storms off to the left. Needs the old screen's
    pixels, so it opts in via wants_prev; it blacks out the board under them, so the new ride
    can't show through before he blows.
    """

    wants_prev = True
    STEP = 2  # pixels a frame, steady: uneven steps judder at 1x (see Figment)
    POSE_S = 3 / FPS  # each pose of his walk (drawing.WALK_CYCLE)
    # The story, in whole frames so his steps stay even.
    BOIL_FRAMES = 36  # red rising, trembling, steaming
    TANTRUM_FRAMES = 27  # hopping on one foot, fists pumping, the screen blown apart
    COOL_FRAMES = 18  # the red draining away
    FLASH_FRAMES = 2
    RED_FILLS = 0.75  # the share of the boil it takes the red to reach the top of his head
    TREMBLE_FROM = 0.35  # when in the boil he starts shaking
    STEAM_FROM = 0.5  # and steaming
    PUFF_EVERY = 4  # frames between puffs of steam
    PUFF_FRAMES = 14  # how long a puff lasts
    PUMP_FRAMES = 3  # fists up, fists higher
    HOP_FRAMES = 8
    HOP_H = 2  # cells
    FEATHERS = 16
    GRAVITY = 0.055  # on the feathers
    FEATHER_FALL = 0.6  # the fastest a feather falls, pixels a frame: they float
    BLAST = (2.0, 3.5)  # how fast the old screen's pieces fly out from him, pixels a frame
    BLAST_GRAVITY = 0.05

    # Copied cell for cell from the user's pixel-art Donald (Dodocraft), facing left: sailor
    # hat with its ribbon, white feathers, yellow-and-orange bill, red bow, blue shirt, his
    # big yellow feet. Black lifted to charcoal, since LEDs draw black as off. 1x on 64x32,
    # 2x on 64x64. '.' empty, K outline, W white, G grey shading, U blue, L light blue,
    # Y yellow, P pale yellow, O orange, R red; Q is his face gone red with rage.
    ART = [
        "......KKKKK.......",
        "......KUUUUKKK....",
        "......KUUUUUUUK...",
        ".......KGGUUUUK...",
        "......KKWGGGUUKGG.",
        ".....KWWWWWGGKGGGG",
        "....KLWWLLLWK..GG.",
        "....KLWLLLLWWK..GG",
        ".KKKKKWLLKLWWK....",
        ".KYYYYYLLKLWWK....",
        "..KPPPPPPKPWK.....",
        "...KYOOOOPWWK.....",
        "...KYOOOYWWK......",
        "....KYYYUUK.......",
        ".....KUWUYK.......",
        "...KRRYRRUK.......",
        "..KURRRRRUUK......",
        ".KYURRURRGUUK.....",
        "KWWYGUUUGUUUK..KK.",
        "KWWWGUUGYUUUGKKWK.",
        "KWWWGWWWGYYGWWWWK.",
        ".KKKGWWWWGGWWWWK..",
        "....KWWWGWWWWWWK..",
        "....KGGGGGWWGWK...",
        "....KGWWWWGYGK....",
        "....KYGKKKGYK.....",
        "....KYK...KYK.....",
        "...KKYK...KYYKKK..",
        "..KYYYK...KYYYYYK.",
        "..KKKKK....KKKKKK.",
    ]
    # His tantrum, drawn from ART: the hanging wing raised into a fist in front of his chest and
    # the far one up behind his head. TANTRUM_HIGH_ART has both a row higher, to pump them.
    TANTRUM_ART = [
        "......KKKKK.......",
        "......KUUUUKKK....",
        "......KUUUUUUUK...",
        ".......KGGUUUUK...",
        "......KKWGGGUUKGG.",
        ".....KWWWWWGGKGGGG",
        "....KLWWLLLWK..GG.",
        "....KLWLLLLWWK..GG",
        ".KKKKKWLLKLWWK.KK.",
        ".KYYYYYLLKLWWKKWWK",
        "..KPPPPPPKPWK.KWWK",
        "...KYOOOOPWWK..KK.",
        ".KKKYOOOYWWK..KW..",
        "KWWKKYYYUUK...WK..",
        "KWWK.KUWUYK..WK...",
        ".KWKRRYRRUK..K....",
        ".KWURRRRRUUK.K....",
        ".KWWRRURRGUUK.....",
        "..KYGUUUGUUUK..KK.",
        "..KWGUUGYUUUGKKWK.",
        "..KWGWWWGYYGWWWWK.",
        "..KKGWWWWGGWWWWK..",
        "....KWWWGWWWWWWK..",
        "....KGGGGGWWGWK...",
        "....KGWWWWGYGK....",
        "....KYGKKKGYK.....",
        "....KYK...KYK.....",
        "...KKYK...KYYKKK..",
        "..KYYYK...KYYYYYK.",
        "..KKKKK....KKKKKK.",
    ]
    TANTRUM_HIGH_ART = [
        "......KKKKK.......",
        "......KUUUUKKK....",
        "......KUUUUUUUK...",
        ".......KGGUUUUK...",
        "......KKWGGGUUKGG.",
        ".....KWWWWWGGKGGGG",
        "....KLWWLLLWK..GG.",
        "....KLWLLLLWWK.KKG",
        ".KKKKKWLLKLWWKKWWK",
        ".KYYYYYLLKLWWKKWWK",
        "..KPPPPPPKPWK..KK.",
        ".KKKYOOOOPWWK.KW..",
        "KWWKYOOOYWWK..WK..",
        "KWWKKYYYUUK.......",
        ".KK..KUWUYK..WK...",
        ".KWKRRYRRUK..K....",
        ".KWURRRRRUUK.K....",
        ".KWWRRURRGUUK.....",
        "..KYGUUUGUUUK..KK.",
        "..KWGUUGYUUUGKKWK.",
        "..KWGWWWGYYGWWWWK.",
        "..KKGWWWWGGWWWWK..",
        "....KWWWGWWWWWWK..",
        "....KGGGGGWWGWK...",
        "....KGWWWWGYGK....",
        "....KYGKKKGYK.....",
        "....KYK...KYK.....",
        "...KKYK...KYYKKK..",
        "..KYYYK...KYYYYYK.",
        "..KKKKK....KKKKKK.",
    ]
    # (first foot row, columns of the foot behind, columns of the foot ahead): he faces left.
    FEET = (26, range(9, 18), range(0, 9))
    # The white of his face and head that goes red, rows top to neck and the columns of his
    # head (so his raised fists stay white).
    FACE_ROWS, FACE_COLS = (4, 12), range(4, 14)
    COLORS = {"K": (62, 54, 50), "W": (255, 255, 255), "G": (121, 135, 143), "U": (0, 66, 194),
              "L": (0, 196, 222), "Y": (255, 228, 0), "P": (242, 236, 145), "O": (255, 96, 0),
              "R": (255, 35, 42), "Q": (235, 30, 25)}
    FEATHER_RGB = ((255, 255, 255), (215, 220, 225))
    STEAM_RGB, STEAM_FADED_RGB = (235, 235, 235), (90, 90, 95)
    FLASH_RGB = (255, 245, 215)

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.ART[0]) * self.scale
        self.sprite_h = len(self.ART) * self.scale
        # Mid-board, on a whole step from just off the right edge.
        self.stop_x = (width - self.sprite_w) // 2
        self.stop_x -= (width - self.stop_x) % 2
        frame = 1 / FPS
        self.boil_at = (width - self.stop_x) / (self.STEP * FPS)
        self.blow_at = self.boil_at + self.BOIL_FRAMES * frame
        self.cool_at = self.blow_at + self.TANTRUM_FRAMES * frame
        self.leave_at = self.cool_at + self.COOL_FRAMES * frame
        off = self.stop_x + self.sprite_w
        self.duration = self.leave_at + (off + off % 2) / (self.STEP * FPS)
        # Puffs of steam: from partway into the boil until he's blown, and one last one as
        # he cools.
        first = self.boil_at + self.STEAM_FROM * self.BOIL_FRAMES * frame
        n = int((self.cool_at - first) * FPS) // self.PUFF_EVERY
        self.puffs = [first + i * self.PUFF_EVERY * frame for i in range(n)] + [self.cool_at + 4 * frame]
        self._faces = {}
        self.debris, self.feathers = [], []
        self.blown = False
        self._frames_stepped = 0
        self.prev_px = {}

    def _frame(self, t, since):
        return int(round((t - since) * FPS))

    def donald_x(self, t):
        step = self.STEP * FPS
        if t < self.boil_at:
            return self.width - step * t
        if t < self.leave_at:
            return self.stop_x
        return self.stop_x - step * (t - self.leave_at)

    def red(self, t):
        """How much of his face has gone red, 0..1: rising through the boil, draining as he cools."""
        if t < self.boil_at or t >= self.leave_at:
            return 0.0
        if t < self.blow_at:
            return min(1.0, self._frame(t, self.boil_at) / (self.RED_FILLS * self.BOIL_FRAMES))
        if t < self.cool_at:
            return 1.0
        return 1.0 - self._frame(t, self.cool_at) / self.COOL_FRAMES

    def tremble(self, t):
        """Columns he's shaken sideways: from partway into the boil, faster as it goes on."""
        if not self.boil_at <= t < self.blow_at:
            return 0
        f = self._frame(t, self.boil_at)
        start = int(self.TREMBLE_FROM * self.BOIL_FRAMES)
        if f < start:
            return 0
        every = 3 if f < (start + self.BOIL_FRAMES) / 2 else 1  # faster near the end
        return 1 if ((f - start) // every) % 2 == 0 else -1

    def tantruming(self, t):
        return self.blow_at <= t < self.cool_at

    def lift(self, t):
        """Rows off the ground: hopping on one foot through the tantrum."""
        if not self.tantruming(t):
            return 0
        p = (self._frame(t, self.blow_at) % self.HOP_FRAMES) / self.HOP_FRAMES
        return round(math.sin(p * math.pi) * self.HOP_H * self.scale)

    def pose(self, t):
        """His walk pose, the back foot up while he hops, or None standing."""
        if t < self.boil_at or t >= self.leave_at:
            return int(t / self.POSE_S)
        return 1 if self.tantruming(t) else None

    def art_at(self, t):
        """His art at t, his face as red as he is."""
        if self.tantruming(t):
            high = (self._frame(t, self.blow_at) // self.PUMP_FRAMES) % 2
            art = self.TANTRUM_HIGH_ART if high else self.TANTRUM_ART
        else:
            art = self.ART
        top, neck = self.FACE_ROWS
        level = neck + 1 - round(self.red(t) * (neck + 1 - top))  # red from this row down to the neck
        key = (id(art), level)
        if key not in self._faces:
            self._faces[key] = [
                "".join("Q" if k == "W" and level <= row <= neck and col in self.FACE_COLS else k
                        for col, k in enumerate(line))
                for row, line in enumerate(art)]
        return self._faces[key]

    def steam(self, t):
        """((x, y), rgb) of the puffs of steam at t, rising off either side of his hat."""
        x0 = self.donald_x(t)
        top = self.height - self.sprite_h - self.lift(t)
        for i, at in enumerate(self.puffs):
            age = self._frame(t, at)
            if not 0 <= age < self.PUFF_FRAMES:
                continue
            side = 1 if i % 2 else -1
            p = age / self.PUFF_FRAMES
            hx = x0 + (13 if side > 0 else 6) * self.scale  # the hat's back and front
            x = int(round(hx + side * age * 0.35 * self.scale))
            y = int(round(top + 2 * self.scale - age * 0.8 * self.scale))
            size = max(1, round((2 - p) * self.scale))
            rgb = blend(self.STEAM_FADED_RGB, self.STEAM_RGB, p)
            for dx in range(size):
                for dy in range(size):
                    yield (x + dx, y + dy), rgb

    def _blow(self):
        """The old screen blasts outward from him, and feathers fly."""
        self.blown = True
        cx = self.stop_x + self.sprite_w / 2
        cy = self.height - self.sprite_h * 0.55
        for (x, y), rgb in self.prev_px.items():
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist < 0.5:  # right at his middle: any way out
                angle = self.rng.uniform(0, 2 * math.pi)
                dx, dy, dist = math.cos(angle), math.sin(angle), 1.0
            speed = self.rng.uniform(*self.BLAST)
            self.debris.append([float(x), float(y), dx / dist * speed, dy / dist * speed, rgb])
        for _ in range(self.FEATHERS):
            self.feathers.append([
                self.stop_x + self.rng.uniform(0, self.sprite_w),
                self.height - self.sprite_h + self.rng.uniform(0, self.sprite_h * 0.6),
                self.rng.uniform(-1.2, 1.2) * self.scale, self.rng.uniform(-1.4, -0.5) * self.scale,
                self.rng.uniform(0, 2 * math.pi), self.rng.choice(self.FEATHER_RGB)])

    def _step(self, t):
        """Advance the blast and the feathers to the frame t seconds after he blew."""
        target = int((t - self.blow_at) * FPS)
        while self._frames_stepped < target:
            self._frames_stepped += 1
            for d in self.debris:
                d[0] += d[2]
                d[1] += d[3]
                d[3] += self.BLAST_GRAVITY
            for f in self.feathers:
                f[4] += 0.35
                f[0] += f[2] + math.sin(f[4]) * 0.4 * self.scale  # rocking side to side
                f[1] += f[3]
                f[2] *= 0.9
                f[3] = min(self.FEATHER_FALL * self.scale, f[3] + self.GRAVITY)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        if t < self.blow_at:
            # The old screen, whole: every pixel of it, black included.
            _blackout(canvas, 0, self.width, self.height)
            paint(canvas, self.prev_px, self.width, self.height)
        else:
            if not self.blown:
                self._blow()
            self._step(t)
            paint(canvas, (((int(round(x)), int(round(y))), rgb) for x, y, _, _, rgb in self.debris),
                  self.width, self.height)
            if self._frame(t, self.blow_at) < self.FLASH_FRAMES:  # over the blast, under him
                flash = self.FLASH_RGB
                paint(canvas, (((x, y), flash) for x in range(self.width) for y in range(self.height)),
                      self.width, self.height)
            for x, y, _, _, _, rgb in self.feathers:
                fx, fy = int(round(x)), int(round(y))
                paint(canvas, (((fx + i, fy + j), rgb) for i in range(self.scale + 1)
                               for j in range(self.scale)), self.width, self.height)
        x = int(round(self.donald_x(t))) + self.tremble(t) * self.scale
        y = self.height - self.sprite_h - self.lift(t)
        paint(canvas, walking_pixels(self.art_at(t), x, y, self.COLORS, self.FEET, self.pose(t), facing=-1,
                                     scale=self.scale), self.width, self.height)
        paint(canvas, self.steam(t), self.width, self.height)
        return True
