import random

from display.animation.drawing import art_pixels, paint
from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS, ease_out


class RalphReveal(CapturesScreens):
    """
    Wreck-It Ralph stomps in from the left over the old ride, raises both fists and slams
    them down: the old screen shatters into falling pixels, leaving the new one behind, and
    he stomps off the right. Needs the previous screen's pixels, so it opts in via wants_prev.
    """

    wants_prev = True
    WALK_S, WIND_S, POST_S, EXIT_S = 1.1, 0.55, 0.6, 0.9
    duration = WALK_S + WIND_S + POST_S + EXIT_S
    SHAKE_S = 0.15     # he judders from the slam
    CLEAR_S = 0.4      # on 64x64, after he's gone, for the last pieces to fall off the taller board
    STEPS_PER_S = 7
    GRAVITY = 0.055    # per frame, on 64x32; scaled with the board's height, so pieces clear a 64x64 board in time too

    # From the user's pattern (docs/references/Ralph.jpg), copied cell for cell: facing us,
    # spiky brown hair, a big grin, red shirt with the grey strap, dark overalls, bare feet,
    # his huge fists hanging at his sides. 1x on both boards: on 64x32 he's two rows taller
    # than the board, so the tip of his hair and the outline under his feet hang off it.
    # UP_ART (64x64) has both fists raised over his head for the slam; SHOULDER_ART (64x32,
    # with no room overhead) has them up beside his face. Their arms are drawn as thick
    # outlined lines from the shoulder, the rest of him is the pattern.
    # '.' empty, K outline, H hair, S skin, P cheeks, W eyes and teeth, R shirt, G strap,
    # D overalls.
    STAND_ART = [
        ".........KK..............",
        "........KHK.KK.KK........",
        "......KKKHKKHKKHK........",
        ".....KHHHHHHHHHHHKK......",
        "....KHHHHHHHHHHHHHKKK....",
        "....KHHHHHHHHHHHHHHHK....",
        "...KHHHHHHHHHHHHHHHK.....",
        "...KKHHSSSHSHSHSSSHKK....",
        "....KHHSSSSSSSSSSSHHK....",
        "...KKHHSHHHSSSHHHSHK.....",
        "...KHHHSWKWSSSWKWSHSK....",
        "....KSHSSSPPPPPSSSHKK....",
        ".....KKSSSPPPPPSSSSK.....",
        ".....KSSSSSSSSSSWSK......",
        ".....KSSSSWWWWWWSSK......",
        ".....KSSSSSSSSSSSSK......",
        "......KSSSSSSSSSSK.......",
        ".....KKKKKKKKKKKKKKK.....",
        "....KRRDDRRGGGRRRRRRK....",
        "...KRRRDDRRRGRRRRRRRRK...",
        "..KRRRRDDRRRRRRRRRRRRRK..",
        ".KRRRRKGGRRRRRRRRRKRRRRK.",
        ".KRRRRKDDGGRRRRRRRKRRRRK.",
        ".KSSSSKDDGGGRRRRRRKSSSSK.",
        ".KSSSSKDDDGGGGRRRRKSSSSK.",
        "KSSSSSKDDDDGGGGGGGKSSSSSK",
        "KSSSSSSKDDDDDGGGGKSSSSSSK",
        "KSSSSSSKDDDDDDDDDKSSSSSSK",
        "KSSSSSSKDDDDDDDDDKSSSSSSK",
        "KSSSSSSKDDDDKDDDDKSSSSSSK",
        "KKKKKKKKDDDK.KDDDKKKKKKKK",
        ".....KSSSSSK.KSSSSSK.....",
        "....KSSSSSSK.KSSSSSSK....",
        "....KKKKKKKK.KKKKKKKK....",
    ]
    UP_ART = [
        ".KKKKKK.................KKKKKK.",
        "KSSSSSSK...............KSSSSSSK",
        "KSSSSSSK...............KSSSSSSK",
        "KSSSSSSK...............KSSSSSSK",
        "KSSSSSSK....KK.........KSSSSSSK",
        "KSSSSSSK...KHK.KK.KK...KSSSSSSK",
        ".KSSSSKK.KKKHKKHKKHK...KKSSSSK.",
        ".KSSSSSKKHHHHHHHHHHHKK.KSSSSSK.",
        "..KSSSSKHHHHHHHHHHHHHKKKSSSSK..",
        "..KSSSSKHHHHHHHHHHHHHHHKSSSSK..",
        "..KSSSSSHHHHHHHHHHHHHHKSSSSSK..",
        "..KSSSSSHHSSSHSHSHSSSHKSSSSSK..",
        "...KSSSSHHSSSSSSSSSSSHHSSSSK...",
        "...KSSSSHHSHHHSSSHHHSHKSSSSK...",
        "...KSSSSSHSWKWSSSWKWSHSSSSSK...",
        "...KSSSSSHSSSPPPPPSSSHSSSSSK...",
        "...KSSSSSKSSSPPPPPSSSSSSSSSK...",
        "....KSSSSSSSSSSSSSSWSKSSSSK....",
        "....KSSSSSSSSWWWWWWSSKSSSSK....",
        "....KSRRRRSSSSSSSSSSSRRRRSK....",
        "....KRRRRRSSSSSSSSSSKRRRRRK....",
        ".....KRRRRKKKKKKKKKKKRRRRK.....",
        ".....KRRRRDDRRGGGRRRRRRRRK.....",
        ".....KRRRRRDRRRGRRRRRRRRRK.....",
        ".....KRRRRRDRRRRRRRRRRRRRK.....",
        ".....KKRRRGGRRRRRRRRRRRRKK.....",
        "......KKRKDDGGRRRRRRRKRKK......",
        ".......KKKDDGGGRRRRRRKKK.......",
        ".........KDDDGGGGRRRRK.........",
        ".........KDDDDGGGGGGGK.........",
        "..........KDDDDDGGGGK..........",
        "..........KDDDDDDDDDK..........",
        "..........KDDDDDDDDDK..........",
        "...............KDDDDK..........",
        "..........KDDDK.KDDDK..........",
        "........KSSSSSK.KSSSSSK........",
        ".......KSSSSSSK.KSSSSSSK.......",
        ".......KKKKKKKK.KKKKKKKK.......",
    ]
    SHOULDER_ART = [
        "..............KK...................",
        ".............KHK.KK.KK.............",
        "...........KKKHKKHKKHK.............",
        "..........KHHHHHHHHHHHKK...........",
        ".........KHHHHHHHHHHHHHKKK.........",
        ".........KHHHHHHHHHHHHHHHK.........",
        "........KHHHHHHHHHHHHHHHK..........",
        "........KKHHSSSHSHSHSSSHKK.........",
        ".KKKKKK..KHHSSSSSSSSSSSHHK..KKKKKK.",
        "KSSSSSSKKKHHSHHHSSSHHHSHK..KSSSSSSK",
        "KSSSSSSKKHHHSWKWSSSWKWSHSK.KSSSSSSK",
        "KSSSSSSK.KSHSSSPPPPPSSSHKK.KSSSSSSK",
        "KSSSSSSK..KKSSSPPPPPSSSSK..KSSSSSSK",
        "KSSSSSSK..KSSSSSSSSSSWSK...KSSSSSSK",
        ".KSSSSKSK.KSSSSWWWWWWSSK..KSKSSSSK.",
        ".KKSSSSSSKKSSSSSSSSSSSSK.KSSSSSSKK.",
        "..KSSSSSSSKKSSSSSSSSSSK.KSSSSSSSK..",
        "...KSSSSSSRKKKKKKKKKKKKKRSSSSSSK...",
        "....KSSSSRRRDDRRGGGRRRRRRRSSSSK....",
        ".....KSSRRRRDDRRRGRRRRRRRRRSSK.....",
        "......KRRRRRRDRRRRRRRRRRRRRRK......",
        ".......KRRRRGGRRRRRRRRRRRRRK.......",
        "........KKRKDDGGRRRRRRRKRKK........",
        ".........KKKDDGGGRRRRRRKKK.........",
        "...........KDDDGGGGRRRRK...........",
        "...........KDDDDGGGGGGGK...........",
        "............KDDDDDGGGGK............",
        "............KDDDDDDDDDK............",
        "............KDDDDDDDDDK............",
        ".................KDDDDK............",
        "............KDDDK.KDDDK............",
        "..........KSSSSSK.KSSSSSK..........",
        ".........KSSSSSSK.KSSSSSSK.........",
        ".........KKKKKKKK.KKKKKKKK.........",
    ]
    SCALE = 1
    COLORS = {
        "K": (40, 30, 32), "H": (125, 80, 52), "S": (232, 184, 162), "P": (248, 152, 120),
        "W": (248, 248, 248), "R": (216, 92, 56), "G": (160, 144, 144), "D": (125, 48, 48),
    }
    FEET_ROW = 31      # the first row of his feet in STAND_ART
    MID_COL = 12       # the gap between his feet

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.tall = height >= 64
        self.duration = type(self).duration + (self.CLEAR_S if self.tall else 0)
        self.raised = self.UP_ART if self.tall else self.SHOULDER_ART
        self.art_w, self.art_h = len(self.STAND_ART[0]), len(self.STAND_ART)
        # His feet on the bottom row; on 64x32 the outline under them hangs off the board.
        self.ground = self.height - self.art_h + (0 if self.tall else 1)
        self.debris = []
        self.shattered = False
        self._frames_stepped = 0
        self.prev_px = {}

    @property
    def impact_at(self):
        return self.WALK_S + self.WIND_S

    def ralph_x(self, t):
        """The left edge of STAND_ART: walks in from off the left, stops mid-board, walks off the right."""
        mid = (self.width - self.art_w) // 2
        if t < self.WALK_S:
            return int(round(-self.art_w + ease_out(t / self.WALK_S) * (mid + self.art_w)))
        leave = self.impact_at + self.POST_S
        if t < leave:
            return mid
        p = min(1.0, (t - leave) / self.EXIT_S)
        return int(round(mid + p * p * (self.width - mid + 1)))

    def walking(self, t):
        return t < self.WALK_S or t >= self.impact_at + self.POST_S

    def _shatter(self):
        """Turn the captured screen into debris, thrown outward from where his fists land."""
        self.shattered = True
        impact_x = self.width / 2
        impact_y = self.ground + 26  # his fists, at his sides
        for (x, y), rgb in self.prev_px.items():
            dx, dy = x - impact_x, y - impact_y
            dist = max(2.0, (dx * dx + dy * dy) ** 0.5)
            power = self.rng.uniform(1.2, 2.4) / dist * 14
            self.debris.append([
                float(x), float(y),
                dx / dist * power + self.rng.uniform(-0.2, 0.2),
                dy / dist * power - self.rng.uniform(0.2, 0.8),
                rgb,
            ])

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        if not self.shattered and t >= self.impact_at:
            self._shatter()
        if t < self.impact_at:
            # The old screen whole, every pixel of it, black included: show_screen has
            # already drawn the new screen underneath.
            frame = {(x, y): (0, 0, 0) for x in range(self.width) for y in range(self.height)}
            frame.update(self.prev_px)
            paint(canvas, frame, self.width, self.height)
        else:
            self._step_debris(t - self.impact_at)
            for x, y, _, _, rgb in self.debris:
                px, py = int(round(x)), int(round(y))
                if 0 <= px < self.width and 0 <= py < self.height:
                    canvas.SetPixel(px, py, *rgb)
        self._draw_ralph(canvas, t)
        return True

    def _step_debris(self, since_impact):
        """Advance the falling pixels to the frame matching `since_impact` seconds."""
        target = int(since_impact * FPS)
        while self._frames_stepped < target:
            self._frames_stepped += 1
            for d in self.debris:
                d[0] += d[2]
                d[1] += d[3]
                d[3] += self.GRAVITY * self.height / 32

    def _draw_ralph(self, canvas, t):
        x0 = self.ralph_x(t)
        if self.WALK_S <= t < self.impact_at:
            # Fists up: the raised pose is wider (and on 64x64 taller), centred on him.
            art = self.raised
            ax = x0 - (len(art[0]) - self.art_w) // 2
            ay = self.ground - (len(art) - self.art_h)
            paint(canvas, art_pixels(art, ax, ay, self.COLORS), self.width, self.height)
            return
        shake = 0
        if self.impact_at <= t < self.impact_at + self.SHAKE_S:
            shake = 1 if int((t - self.impact_at) * FPS) % 2 == 0 else -1
        lifted = None
        if self.walking(t):
            lifted = int(t * self.STEPS_PER_S) % 2  # 0: his left foot up, 1: his right
        px = {}
        for (x, y), rgb in art_pixels(self.STAND_ART, x0 + shake, self.ground, self.COLORS):
            row, col = y - self.ground, x - x0 - shake
            if lifted is not None and row >= self.FEET_ROW - 1 and (col < self.MID_COL) == (lifted == 0):
                y -= 1  # this foot's off the ground
            px[(x, y)] = rgb
        paint(canvas, px, self.width, self.height)
