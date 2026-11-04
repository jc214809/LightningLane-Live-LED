import math
import random

from display.animation.drawing import _rotate_art, art_pixels, paint
from display.animation.motion import _hops, progress


class LuxoBallReveal:
    """
    The Pixar Ball and Luxo Jr. over the finished ride screen, one of three stories at random
    (STORY pins one): "bat", the ball bounces in and Luxo hops in and bats it away; "chase",
    the ball bounces across and Luxo hops after it; "light", a searchlight: the board is dark
    with the ball somewhere in it, Luxo hops in, switches his light on and sweeps a narrow
    beam looking for it, his head turning with it (the ball shows only where the beam
    touches it), finds it, the ball hops happily, and the beam widens over the ride, whose wait counts
    up once they've left. The ball turns a quarter each hop, like
    it's rolling (exact pixel turns: other rotations smear pixel art). Both are 1x on both
    boards, transcribed cell for cell from pixel art the user shared.
    """

    over_screen = True
    STORIES = ("bat", "chase", "light")
    STORY = None
    DURATIONS = {"bat": 4.2, "chase": 3.6, "light": 5.8}
    # Story "light": he hops in through the dark, his light switches on once he's landed,
    # he searches until he finds the ball, the ball hops, the beam widens, and they leave.
    LIGHT_ON, FOUND, WIDEN, LEAVE = 1.2, 3.1, 3.8, 4.9

    # '.' empty, Y yellow, R red star, B blue band.
    BALL_ART = [
        ".......YYYYYY........",
        ".....YYYYYYYYYY......",
        "....RYYRRRRYYYYBB....",
        "...RRRRRRRYYYYYYBB...",
        "..YRRRRRYYYYYYYYBBB..",
        ".YRRRRRYYYYYYYYYBBB..",
        ".RRRRRRRYYYYYYYYBBBB.",
        "RRRRRRRRRYYYYYYYBBBBY",
        "RRRRRRRRRRYYYYYYBBBBY",
        "YYRRRYRRRRRYYYYYBBBBY",
        "YYRRYYYYYYRYYYYYBBBBY",
        "YYRRYYYYYYYYYYYBBBBBY",
        "YYRRYYYYYYYYYYYBBBBYY",
        ".YYRYYYYYYYYYYBBBBBY.",
        ".YYRYYYYYYYYYBBBBBBY.",
        ".YYYYYYYYYYYBBBBBBYY.",
        "..YYYYYYYYYBBBBBBYY..",
        "...YYYYYYYBBBBBBYY...",
        "....YYYYBBBBBBBYY....",
        ".....BBBBBBBBBB......",
        "........BBBBB........",
    ]
    # Facing left. '.' empty, K outline, W shade's inside, Y bulb, L light grey, D dark grey.
    LUXO_ART = [
        "...KKKKK...............",
        "..KWWKDDKK.............",
        ".KWWWWKDLLK............",
        "KWWWWWKDDLLK...........",
        "KWWWWKKKDLLKK..........",
        "KWWWKYYKDLLLKKK........",
        "KWWKYYYKDLLLLWLK.......",
        "KWWKYYYKDLLLLWLKK......",
        "KWWKYYYKDLLLLWLKK......",
        "KWWKYYYKDLLDDWDK.......",
        "KWWWKYYKDLDDKKK........",
        "KWWWWKKKDLDKK..........",
        ".KWWWWKDDDDKWDD........",
        ".KWWWWKDDDKWWWWDD......",
        "..KWWKDDKK.DDWWWDDD....",
        "...KKKKK.....DDDDWWDD..",
        "...............DDDWWD..",
        ".................DDDD..",
        ".................DWWD..",
        "................DWWD...",
        "................DDWD...",
        "...............DWDD....",
        "...............DWWD....",
        "..............DDDD.....",
        "...............DD......",
        "...............K.......",
        "..............KLK......",
        ".........KKKKKKLKKKKKK.",
        "........KLLLLLLLLLLLLLK",
    ]
    BALL_SCALE = LUXO_SCALE = 1
    colors = {"Y": (240, 195, 65), "R": (190, 50, 30), "B": (45, 100, 180),
              "K": (20, 20, 22), "W": (250, 250, 250), "L": (170, 169, 165), "D": (98, 95, 90)}
    BULB = (4.5, 8.0)  # the bulb's centre in LUXO_ART (col, row), where his light comes from
    # Story "light": the bulb is dark until he switches on, then bright pale yellow, so it never matches
    # the ball's yellow or his white shade, and the light can't look on from the start.
    BULB_OFF, BULB_ON = (70, 62, 45), (255, 240, 140)
    # His head is the shade: every row down to 11, and on the rows it shares with the arm, the
    # columns up to these. It tilts about the joint where it meets the arm (PIVOT), sampled
    # nearest-neighbour, which reads cleanly up to about 30 degrees either way.
    HEAD_ENDS = {12: 11, 13: 10, 14: 9, 15: 7}
    PIVOT = (12.5, 12.0)
    AIM = math.pi - 0.35  # which way his untilted shade points: left and a little down
    MAX_TILT = 0.55

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.story = self.STORY or self.rng.choice(self.STORIES)
        self.duration = self.DURATIONS[self.story]
        if self.story == "light":
            # The ride is dark until the beam widens, so its wait counts up after they've left,
            # and the screen stays up to read it, however slowly a board plays the search.
            self.over_screen = False
            self.hold_after_s = 3.0
        self.ball_size = len(self.BALL_ART)
        self.luxo_w, self.luxo_h = len(self.LUXO_ART[0]), len(self.LUXO_ART)
        self.hop = 5 if height < 64 else 9  # how high the ball bounces
        self.ball_rest = round(width * 0.3)  # where the ball settles (its centre)
        self.luxo_rest = self._touching_x()  # where Luxo stops: his bat just reaches the ball
        self.search_x = round(width * 0.78)  # where he stands to search with his light
        self._poses = {}

    LUNGE = 4  # how far Luxo lunges to bat the ball, in pixels
    HIT_S = 2.5  # the moment his shade meets the ball

    def _touching_x(self):
        """
        Luxo's resting centre x from which his lunge brings his shade right up against the
        ball (the nearest pair of pixels on any row they share end up side by side), so the
        bat visibly lands instead of knocking the ball away from a few pixels off.
        """
        ball_top = self.height - self.ball_size
        luxo_top = self.height - self.luxo_h
        ball_left = self.ball_rest - self.ball_size // 2
        resting = _rotate_art(self.BALL_ART, -3)  # turned three quarters by the hops in
        gaps = []
        for y in range(max(ball_top, luxo_top), self.height):
            b = resting[y - ball_top]
            l = self.LUXO_ART[y - luxo_top]
            if b.strip(".") and l.strip("."):
                ball_right = ball_left + len(b.rstrip(".")) - 1
                luxo_first = len(l) - len(l.lstrip("."))  # his leftmost pixel on this row
                gaps.append(luxo_first - ball_right)
        # With his art's left edge at x0, the nearest gap on a shared row is x0 + min(gaps);
        # at the lunge's peak that must be 1 (touching).
        x0 = 1 - min(gaps) + self.LUNGE
        return x0 + self.luxo_w / 2

    def ball(self, t):
        """(centre x, top y, quarter turns) of the ball at t, or None when it's off the board."""
        n, s = self.ball_size, self.story
        off_left, off_right = -n / 2 - 1, self.width + n / 2 + 1
        if s == "chase":
            x, lift, done = _hops(t, 0.0, 3.0, off_left, off_right, 6, self.hop)
            turns = -done  # rolling right: clockwise
        elif s == "light":
            # Sitting in the dark until the beam finds it; a happy hop, then off to the left.
            if t < self.LEAVE:
                x, lift, done = _hops(t, self.FOUND, self.FOUND + 0.5, self.ball_rest, self.ball_rest,
                                      2, self.hop * 0.7)
                turns = -3 - done
            else:
                x, lift, done = _hops(t, self.LEAVE, self.duration, self.ball_rest, off_left, 3, self.hop)
                turns = -5 + done
        elif t < 1.2:
            x, lift, done = _hops(t, 0.0, 1.2, off_left, self.ball_rest, 3, self.hop)
            turns = -done
        else:
            # Batted: it bounces off the left edge, rolling the other way.
            x, lift, done = _hops(t, self.HIT_S, self.HIT_S + 1.0, self.ball_rest, off_left, 3, self.hop)
            turns = -3 + done
        if x < off_left + 0.5 or x > off_right - 0.5:
            return None
        return x, self.height - n - lift, turns

    def luxo(self, t):
        """(centre x, top y, facing left) of Luxo at t, or None when he's off the board."""
        where = self._luxo(t)
        if where is None or abs(where[0] - self.width / 2) >= (self.width + self.luxo_w) / 2:
            return None
        return where

    def _luxo(self, t):
        w, s = self.luxo_w, self.story
        off_left, off_right = -w / 2 - 1, self.width + w / 2 + 1
        ground = self.height - self.luxo_h
        if s == "chase":
            if t < 0.6:
                return None
            x, lift, _ = _hops(t, 0.6, 3.6, off_left, off_right, 5, 4)
            return x, ground - lift, False  # turned round to chase it
        if s == "light":
            if t < 1.0:
                x, lift, _ = _hops(t, 0.0, 1.0, off_right, self.search_x, 2, 4)
            elif t < self.LEAVE:
                x, lift = self.search_x, 0.0
            else:
                x, lift, _ = _hops(t, self.LEAVE, self.duration, self.search_x, off_right, 2, 4)
            return x, ground - lift, True
        if t < 1.0:
            return None
        if t < 2.0:
            x, lift, _ = _hops(t, 1.0, 2.0, off_right, self.luxo_rest, 2, 4)
        elif t < 2.4:
            x, lift = self.luxo_rest, 0.0  # looking down at the ball (head_tilt)
        elif t < 2.6:
            x, lift = self.luxo_rest - self.LUNGE * math.sin((t - 2.4) / 0.2 * math.pi), 0.0  # the bat
        elif t < 3.4:
            x, lift = self.luxo_rest, 0.0
        else:
            x, lift, _ = _hops(t, 3.4, self.duration, self.luxo_rest, off_right, 2, 4)
        return x, ground - lift, True

    def beam(self, t):
        """
        (bulb x, bulb y, aim, half-angle) of Luxo's light at t in story "light", else None.
        A narrow beam sweeps back and forth, settles on the ball, then widens over the board.
        """
        if self.story != "light" or t < self.LIGHT_ON:
            return None
        x, y, _ = self._luxo(min(t, self.LEAVE))  # it stays where he stood as he hops off
        left = x - self.luxo_w / 2
        px_, py_ = left + self.PIVOT[0], y + self.PIVOT[1]
        on_ball = math.atan2(self.height - self.ball_size / 2 - py_, self.ball_rest - px_)
        # Full swings to start, easing to a stop on the ball by FOUND.
        sweep = 0.7 * max(0.0, min(1.0, (self.FOUND - t) / 0.6))
        aim = on_ball + sweep * math.cos(2 * math.pi * (t - self.LIGHT_ON) / 1.2)
        # His head turns to point the beam (as far as it can tilt); the light comes from the bulb.
        tilt = max(-self.MAX_TILT, min(self.MAX_TILT, aim - self.AIM))
        aim = self.AIM + tilt
        bx, by = self._turn(self.BULB, tilt)
        half = 0.3 + (math.pi + 0.2) * progress(t, self.WIDEN, self.WIDEN + 1.1) ** 1.5
        return left + bx, y + by, aim, half

    def head_tilt(self, t):
        """How far his head is turned at t, in radians: following his light, or nodding at the ball."""
        if self.story == "light":
            return self.beam(t)[2] - self.AIM if self.beam(t) else 0.0
        if self.story == "bat" and 2.05 < t < 2.35:
            return -0.3  # looking down at the ball
        return 0.0

    def _turn(self, point, tilt):
        """An art (col, row) point turned about the pivot by `tilt`."""
        dx, dy = point[0] - self.PIVOT[0], point[1] - self.PIVOT[1]
        c, s_ = math.cos(tilt), math.sin(tilt)
        return self.PIVOT[0] + dx * c - dy * s_, self.PIVOT[1] + dx * s_ + dy * c

    def _is_head(self, row, col):
        return row <= 11 or col <= self.HEAD_ENDS.get(row, -1)

    def luxo_pose(self, tilt):
        """{(col, row): kind} of Luxo facing left with his head turned by `tilt` (cached)."""
        key = round(tilt, 2)
        if key not in self._poses:
            art, out = self.LUXO_ART, {}
            for r, line in enumerate(art):
                for c, k in enumerate(line):
                    if k != "." and not self._is_head(r, c):
                        out[(c, r)] = k
            cs, sn = math.cos(key), math.sin(key)
            for y in range(-8, len(art)):
                for x in range(-8, len(art[0]) + 4):
                    dx, dy = x + 0.5 - self.PIVOT[0], y + 0.5 - self.PIVOT[1]
                    sx, sy = self.PIVOT[0] + dx * cs + dy * sn, self.PIVOT[1] - dx * sn + dy * cs
                    c, r = int(math.floor(sx)), int(math.floor(sy))
                    if 0 <= r < len(art) and 0 <= c < len(art[0]) and art[r][c] != "." and self._is_head(r, c):
                        out[(x, y)] = art[r][c]
            self._poses[key] = out
        return self._poses[key]

    def lit(self, t):
        """The set of board pixels the beam is lighting at t (story "light")."""
        out = set()
        if self.beam(t) is None:
            return out  # not switched on yet
        bx, by, aim, half = self.beam(t)
        for y in range(self.height):
            for x in range(self.width):
                a = math.atan2(y - by, x - bx)
                if abs(math.atan2(math.sin(a - aim), math.cos(a - aim))) <= half:
                    out.add((x, y))
        return out

    def pixels(self, t):
        """{(x, y): rgb} of everything the scene draws at t (the dark board and beam included)."""
        out = {}
        lit = None
        if self.story == "light":
            lit = self.lit(t)
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) not in lit:
                        out[(x, y)] = (0, 0, 0)
        ball = self.ball(t)
        if ball:
            x, y, turns = ball
            art = _rotate_art(self.BALL_ART, turns)
            # In the dark, the ball shows only where the beam touches it.
            self._stamp(out, art, int(round(x - self.ball_size / 2)), int(round(y)), only=lit)
        lux = self.luxo(t)
        if lux:
            x, y, facing_left = lux
            x0, y0 = int(round(x - self.luxo_w / 2)), int(round(y))
            colors = self.colors
            if self.story == "light":
                colors = {**colors, "Y": self.BULB_ON if t >= self.LIGHT_ON else self.BULB_OFF}
            for (c, r), kind in self.luxo_pose(self.head_tilt(t) if facing_left else 0.0).items():
                if not facing_left:
                    c = self.luxo_w - 1 - c
                if 0 <= x0 + c < self.width and 0 <= y0 + r < self.height:
                    out[(x0 + c, y0 + r)] = colors[kind]
        return out

    def _stamp(self, out, art, x0, y0, only=None):
        """Add art to the scene's pixels, keeping to the board (and to `only`, if given)."""
        out.update(((x, y), rgb) for (x, y), rgb in art_pixels(art, x0, y0, self.colors)
                   if 0 <= x < self.width and 0 <= y < self.height and (only is None or (x, y) in only))

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        paint(canvas, self.pixels(t), self.width, self.height)
        return True
