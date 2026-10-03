import math
from collections import deque

from display.animation.drawing import _blackout
from display.animation.motion import FPS, ease_out
from display.pixels import art_pixels, paint


class JackSallyReveal:
    """
    The Nightmare Before Christmas, on the Jack and Sally meet's own screen on Halloween party
    nights. Zero floats across with his nose glowing, the meet appearing behind him. Then Sally
    walks in from the left and Jack from the right, bobbing as they go; they stop a step apart,
    lean in and kiss, a heart floats up from the kiss, and they walk back off their own sides.
    """

    # 1x on both boards: Zero doubled is wider than the board, and so is the pair.
    ZERO_SCALE = 1
    PAIR_SCALE = 1
    HEART_SCALE = 1
    ZERO_STEP = 3  # pixels a frame across the board, steady: uneven steps judder at 1x
    ZERO_BOB_S = 1.0  # one float up and down
    NOSE_S = 0.6  # one pulse of Zero's glowing nose
    PAUSE_S = 6 / FPS  # after Zero's gone, before they walk in
    STEP = 2  # pixels a frame as they walk, steady
    STRIDE_S = 4 / FPS  # each bob of their walk
    APART = 2  # columns each stops short of the kiss before leaning in
    LEAN_S = 8 / FPS  # leaning in, a column at a time
    KISS_S = 36 / FPS  # holding the kiss while the heart floats up
    HEART_RISE = 14  # rows the heart floats up over the kiss
    # Where the kiss is in PAIR_ART: Sally's lips, against Jack's cheek.
    LIPS = (21, 14)
    # Sally's white shoes are hers; every other white is Jack's.
    SALLY_COLORS, JACK_COLORS = set("HRSVTEYQUA"), set("WD")
    SALLY_SHOES_LEFT_OF = 19

    # Zero, from docs/references/Zero.jpg, copied cell for cell: '.' empty, K outline and eye,
    # W white, M mouth, O nose (it glows).
    ZERO_ART = [
        "....KK.........KKKK...................",
        "....KWKKKKKKKKKKWWKKK.................",
        "....KKWWWWWWWWWWKKKKKKKK..............",
        "KKK..KKWWWWWWWKKKWWWWWWKK.............",
        "KWWKKKKKKKWWKKKWWWWWWWWWKK............",
        "KWWWWWWWWKKKKWWWWWWWWWWWWKK...........",
        "KKWWWWWWWWWWWWWWWWWWWWWWWWKK..........",
        ".KKWWWWWWWWWWWWWWWWWWWWWWWWK..........",
        "..KKKWWWWWWWKWWWWWWWWWWWWWWKK.........",
        "....KKKWWWWKKWWWWWWWKKKWWWWWK.........",
        "......KKKKKKWWWWWWWKKKKKWWWWK....KKK..",
        ".........KWWWWWWWWWKKKKKWWWWKK..KKOKK.",
        ".........KWWWWWWWWWKKKKKWWWWWK.KKOOOK.",
        "KK.......KWWWWWWWWWKKKKKWWWWWKKKOOOOOK",
        "KWK......KKWWWWWKKWWKKKWWWWWWWWKOOOOOK",
        "KWWKKKK...KKWWWWWKKWWWWWWWWWWWWKKOOOKK",
        "KWWWWWKKKK.KWWWWWWKKWWWWWWWWWWWWKKOKK.",
        "KWWWWWWWWKKKKKWWWWWKKKKWWWWWWKKK.KKK..",
        ".KWWWWWWWWWKKKKKKKWWWWKKKKKKKK........",
        ".KWWWWWWWWWKMMMMMKKKKKKKKK............",
        ".KKWWWWWWWWWKKMMMMMMMMMMMK............",
        "..KKWWWWWWWWWKKKMMMMMMMKKKKK..........",
        "...KWWWWWWWWWWWKKKKKKKKKWWWKK.........",
        "...KKWWWWWWWWWWWWWWWWWWWWWWWKK........",
        "....KWWWWWWWWWWWWWWWWWWWWWWWWKK.......",
        "....KWWWWWWWWWWWWWWWWWWWWWWWWWKK......",
        "....KKWWWWWWWWWWWWWWWWWWWWWWWWWK......",
        ".....KWWWWWWWWWWWWWWWWWWWWWWWWKK......",
        ".....KWWWWWWWWWWWWWWWWWWWWWWKKK.......",
        ".....KKWWWWWWWWWWWWWWWWKKKKKK.........",
        "......KKKKKWWWWWWWWWWWKK..............",
        "..........KKKWWWWWWWWKK...............",
        "............KKKWWWWWKK................",
        "..............KKKKKKK.................",
    ]
    # Sally leaning on Jack for the kiss, from the user's bead pattern (docs/references/Sally and
    # Jack pair.png), copied cell for cell, then shortened to 43 x 32 so it fits 64x32 whole: rows
    # out of their clothes and legs, with hair and hands kept whole. It's their pose when they
    # meet; split() pulls it into Sally and Jack for the walk. '.' empty, K outline, Jack's eye
    # sockets and suit, W white, D his dark grey; R Sally's hair and H its darker strands, S her
    # skin, V her eyelid, and her patchwork dress: T teal, E dark teal, Y yellow, Q magenta,
    # U purple, A amber.
    PAIR_SCALE = 1
    PAIR_ART = [
        "........HHHHHH.HHH........KKKKKKKKK........",
        "......HHRRRRRRHRRRHH....KKWWWWWWWWWKK......",
        ".....HRRRHHHRRRHRRRRH..KWWWWWWWWWWWWWK.....",
        "....HHRRHHRRHHRHRHHRRHKWWKKWWWWKKKWWWWK....",
        "...HHRRHRRRRRRRKRRRHRHKWKKKKWWKKKKKWWWK....",
        "...HHRHRRRRKKKKSKKKRRKWKKKKKWWKKKKKKWWWK...",
        "..HRHRHRRRKKSSSSSSSKRKWKKKKKWWKKKKKKWWWK...",
        "..HRHRHRRKKSSSSSSSSKKKWKKKKKWWKKKKKKWWWWK..",
        ".HRRHRRHRKSSSVVVVSSSKWWWKKKWKKWKKKKWWWKWK..",
        ".HRRHRRHRKSSKVVVVVSSKWKWWWWWWWWWWWWWWWKWK..",
        ".HRRRHRHRKSSVKKKKKVSKWKWWWWWWWWWWWWWWKWWK..",
        ".HRRRHRHRKSSKSSSSKSSSKKKWWWWWWWWWWWWKKWWK..",
        ".HRRRHRHRKSSSSSSSSSSSKWKWKWKWKWKWKWKKWWK...",
        ".HRRHRRHRKSSSKSSSSSSSKWWKKKKKKKKKKKWWWWK...",
        ".HRRHRRHRKSSSSKKSSKKKHKWWWWKWKWKWWWWWWK....",
        ".HRRHRRHRKSSSSSSKKSSSK.KWWWWWWWWWWWWWK.....",
        ".HRRHRRHRRKSSSSSSSSSK...KKWWWWWWWWKKK......",
        ".HHRRHRRHRKSSSSSSSKK......KKKKKKKK.........",
        ".HHRRHRRHRKSSSSKKKRH..KKKK..KWWK..KKKKK....",
        ".HHHRHRRHHRKKSKKRRRH.KDDDDKKKWWKKKDDDDDK...",
        ".HRHRHRRHKKKSKSKKKRH.KKKKKDDKKKKDDKKKKKK...",
        ".HRHRRRRKTTTYSSQKYKRH....KKDKDDKDKDDK......",
        ".HRHHRRKTKTKYYSKUKYKRH..KDKKWKKWKDKDDK.....",
        ".HRHHRRKSTKYKYKQQKYKRH..KDKDKWWKDK.KDDK....",
        ".HRHHRKSSKHKYYYQKYSSKH.KDDKDKWKDDK.KDDK....",
        ".HHRRKSKHKTUTTKEEEKKSSKDDK.KDKDDDK...KWWKKK",
        ".KKKKSSKHKUKQUQEEEK.KSSKK.KDKDKKDDK..KWWWWK",
        ".KSSSSKHKKSKKKKSKK..WKKKKKDKDDKDDKDK.KWKKK.",
        "..KKKSKHKSSSK.KSSK..KWWWKDDKDDKDDKDDKKK....",
        ".HRRRRRHKSSK.KSSK....KKKDDKKDDKDDKKDDK.....",
        "HHHHHHHKWWK..KWWK.......KK.KDDKDDK.KK......",
        "......KKKK....KKKK........KKKK.KKKK........",
    ]
    HEART_ART = [
        ".XX.XX.",
        "XXXXXXX",
        "XXXXXXX",
        ".XXXXX.",
        "..XXX..",
        "...X...",
    ]
    colors = {"K": (0, 0, 0), "W": (250, 250, 250), "M": (225, 50, 60), "O": (255, 125, 40),
              "D": (85, 85, 100), "R": (210, 25, 50), "H": (140, 25, 45), "S": (140, 200, 225),
              "V": (190, 160, 230), "T": (20, 200, 140), "E": (0, 120, 140), "Y": (225, 225, 50),
              "Q": (190, 80, 170), "U": (90, 60, 180), "A": (245, 170, 20), "X": (255, 60, 110)}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.zero_w, self.zero_h = len(self.ZERO_ART[0]), len(self.ZERO_ART)
        # Zero floats through the middle of the board; on 64x32 he's two rows too tall, so his
        # top and bottom outline rows (black, so unseen) hang off.
        self.zero_y = (height - self.zero_h) // 2
        self.zero_bob = 2 if height - self.zero_h >= 4 else 0
        crossing = width + self.zero_w
        self.zero_s = (crossing + -crossing % self.ZERO_STEP) / (self.ZERO_STEP * FPS)

        # The kiss stands centred on the bottom edge (it fills 64x32 exactly).
        pair_w, pair_h = len(self.PAIR_ART[0]), len(self.PAIR_ART)
        self.pair_x, self.pair_y = (width - pair_w) // 2, height - pair_h
        self.sally, self.jack = self.split()
        # Each walks the same whole, even distance to stand APART short of the kiss, starting
        # just off their own side.
        sally_right = max(x for x, _ in self.sally) + self.pair_x + 1
        jack_left = min(x for x, _ in self.jack) + self.pair_x
        far = max(sally_right - self.APART, width - jack_left - self.APART)
        self.distance = far + far % 2
        self.walk_in_at = self.zero_s + self.PAUSE_S
        self.walk_s = self.distance / (self.STEP * FPS)
        self.lean_at = self.walk_in_at + self.walk_s
        self.kiss_at = self.lean_at + self.LEAN_S
        self.leave_at = self.kiss_at + self.KISS_S
        # Walking off: far enough for each to clear their own side from the kiss.
        out = max(sally_right, width - jack_left)
        self.out = out + out % 2
        self.duration = self.leave_at + self.out / (self.STEP * FPS)

    def split(self):
        """
        PAIR_ART pulled into Sally's cells and Jack's, {(x, y): kind} each. Coloured cells go by
        colour; each outline cell goes to whoever's colour is nearest, so outlines stay with
        their owner.
        """
        art = self.PAIR_ART
        owner = {}
        queue = deque()
        for y, row in enumerate(art):
            for x, kind in enumerate(row):
                sally = kind in self.SALLY_COLORS or (kind == "W" and x < self.SALLY_SHOES_LEFT_OF)
                if sally or kind in self.JACK_COLORS:
                    owner[(x, y)] = "sally" if sally else "jack"
                    queue.append((x, y))
        while queue:
            x, y = queue.popleft()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                nx, ny = n
                if 0 <= ny < len(art) and 0 <= nx < len(art[0]) and n not in owner and art[ny][nx] == "K":
                    owner[n] = owner[(x, y)]
                    queue.append(n)
        cells = {"sally": {}, "jack": {}}
        for (x, y), who in owner.items():
            cells[who][(x, y)] = art[y][x]
        return cells["sally"], cells["jack"]

    def zero_x(self, t):
        """Zero's left edge: from just off the left to just off the right."""
        return -self.zero_w + self.ZERO_STEP * FPS * t

    def zero_top(self, t):
        return self.zero_y + round(self.zero_bob * math.sin(2 * math.pi * t / self.ZERO_BOB_S))

    def nose_rgb(self, t):
        """Zero's nose, pulsing around a bright floor so it never fades into his face."""
        glow = 0.5 + 0.5 * math.sin(2 * math.pi * t / self.NOSE_S)
        return 255, int(110 + 100 * glow), int(20 + 50 * glow)

    def apart(self, t):
        """
        How far each stands from the kiss at t, in columns: Sally that far left of it and Jack
        that far right. None before they walk in and once they've gone.
        """
        speed = self.STEP * FPS
        if t < self.walk_in_at or t >= self.duration:
            return None
        if t < self.lean_at:
            return self.APART + self.distance - speed * (t - self.walk_in_at)
        if t < self.kiss_at:
            return self.APART - int(self.APART * (t - self.lean_at) / self.LEAN_S)
        if t < self.leave_at:
            return 0
        return speed * (t - self.leave_at)

    def walking(self, t):
        return self.walk_in_at <= t < self.lean_at or t >= self.leave_at

    def bob(self, t, phase):
        """Rows dropped mid-stride (0 or 1); phase keeps them out of step. Down, so heads stay on."""
        return (int(t / self.STRIDE_S) + phase) % 2 if self.walking(t) else 0

    def heart(self, t):
        """The heart's top-left corner at t, floating up from the kiss; None outside the kiss."""
        if not self.kiss_at <= t < self.leave_at:
            return None
        lips_x, lips_y = self.LIPS
        start = self.pair_y + lips_y - len(self.HEART_ART)
        # It floats up as far as the board allows: on 64x32 it stops at the top edge.
        rise = round(min(self.HEART_RISE, start) * ease_out((t - self.kiss_at) / self.KISS_S))
        x = self.pair_x + lips_x - len(self.HEART_ART[0]) // 2
        return x, start - rise

    def figures(self, t):
        """{"sally": {(x, y): rgb}, "jack": {...}} on the board at t (empty when they're not on)."""
        gap = self.apart(t)
        drawn = {"sally": {}, "jack": {}}
        if gap is None:
            return drawn
        gap = int(round(gap))
        for who, cells, dx, phase in (("sally", self.sally, -gap, 0), ("jack", self.jack, gap, 1)):
            dy = self.bob(t, phase)
            for (x, y), kind in cells.items():
                px, py = self.pair_x + x + dx, self.pair_y + y + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    drawn[who][(px, py)] = self.colors[kind]
        return drawn

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        if t < self.zero_s:
            x = int(round(self.zero_x(t)))
            # Still dark ahead of him, from his middle.
            _blackout(canvas, max(0, x + self.zero_w // 2), self.width, self.height)
            colors = dict(self.colors, O=self.nose_rgb(t))
            paint(canvas, art_pixels(self.ZERO_ART, x, self.zero_top(t), colors), self.width, self.height)
            return True
        for pixels in self.figures(t).values():
            paint(canvas, pixels, self.width, self.height)
        heart = self.heart(t)
        if heart:
            paint(canvas, art_pixels(self.HEART_ART, *heart, self.colors), self.width, self.height)
        return True
