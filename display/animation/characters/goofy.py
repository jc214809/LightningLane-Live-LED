import math
import random

from display.animation.drawing import _blackout, _letters, _rotate_art, art_pixels, paint
from display.animation.motion import FPS


class GoofyReveal:
    """
    Goofy flies his biplane in from the left, towing a "YAHOOEY!" banner, loops the loop and
    flies off the right edge; the new ride is uncovered behind the banner's tail. On 64x32 the
    loop goes out the top of the board and comes back in. The plane turns in exact quarter
    steps (level, climbing, upside down, diving), since rotating pixel art any other way
    smears it; the banner follows the plane's path column by column, bending round the loop
    like cloth.
    """

    # Goofy's head is transcribed from a pixel-art Goofy the user shared (a code-drawn one
    # read as a generic dog), then touched up by the user in the sprite editor: his green
    # hat with a blue band, both eyes, the big peach muzzle with his nose on top and tongue
    # out, and his ear swept back, sitting up tall in his orange shirt. His black head and
    # outline are a lifted charcoal, since LEDs draw black as off; his pupils stay
    # near-black. The plane is the pin's biplane, repainted red and yellow like the Great
    # Goofini's at The Barnstormer. Nose right. '.' empty, K head and outline, H hat,
    # A hat band, W white, E pupil, S skin, M tongue, O shirt, G glove, R red body,
    # r red shade, Y yellow wing, y wing shade, T strut, c cowl, P propeller.
    art = [
        "..........................",
        "...........HHHHH..........",
        "...........HHHHH..........",
        "...........AAAAA..........",
        "...........HHHHH..........",
        ".......KKKKKKKKK..........",
        ".......KKKKWWKWW..........",
        ".....KKKKKKWWWWW..KK......",
        "....KKKK.KKWEWEW..KK......",
        "...KKKK..KKWEWEW..SS......",
        "...KKK..KSSSSSSSSSSS......",
        "...KK...KSSSSSSSSSSS......",
        ".......KKSSMSSSSSSS.......",
        "......KKOSSMMKSSW.W.......",
        "......KOOOSSSS............",
        ".......OOOOO..............",
        ".......OOOOO..............",
        "Y......OOOGGYYYYYYYYYYY..P",
        "YY.....OOOGGyyyyyyyyyyy..P",
        "YYY.RRRROOOORTRRRRTRRRRc.P",
        "YYYRRRRRRRRRRRTRRTRRRRRRcP",
        "YYYRRRRRRRRRRRRTTRRRRRRRcP",
        ".y.rrrrrrrrrrrT..TrrrrrrrP",
        "....rrrrrr...YYYYYYYYY...P",
        ".............yyyyyyyyy....",
    ]
    FONT = {
        "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], "A": [".#.", "#.#", "###", "#.#", "#.#"],
        "H": ["#.#", "#.#", "###", "#.#", "#.#"], "O": ["###", "#.#", "#.#", "#.#", "###"],
        "E": ["###", "#..", "##.", "#..", "###"], "!": ["#", "#", "#", ".", "#"],
    }
    BANNER_ART = _letters("YAHOOEY!", FONT)
    colors = {"R": (220, 40, 40), "r": (150, 25, 25), "Y": (255, 210, 40), "y": (190, 150, 20),
              "T": (140, 90, 50), "P": (200, 200, 210), "c": (90, 90, 100), "K": (70, 70, 82),
              "S": (250, 205, 140), "M": (240, 130, 150), "W": (250, 250, 250), "E": (20, 20, 24),
              "G": (245, 245, 245), "O": (255, 150, 20), "H": (140, 190, 70), "A": (59, 132, 255),
              "Q": (245, 235, 205), "X": (210, 30, 30)}
    ROPE = (160, 150, 130)

    SCALE = 1  # 1x on both boards: doubled, his loop runs off a 64x64 board
    SPEED = 75  # pixels a second along his path, at 1x

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        s = self.scale = self.SCALE
        base = self.art
        self.poses = [_rotate_art(base, q) for q in range(4)]
        self.sprite_w, self.sprite_h = len(base[0]) * s, len(base) * s
        self.rope = 5 * s
        self.banner_w, self.banner_h = len(self.BANNER_ART[0]) * s, len(self.BANNER_ART) * s
        # He cruises low, then loops: the loop's bottom is his cruising height, and on 64x32
        # its top is above the board.
        self.cruise_y = height - self.sprite_h / 2 - 2
        self.radius = (11 if height < 64 else 17) * s
        self.loop_x = width * 0.45
        self.start_x = -self.sprite_w / 2 - 1
        self.approach = self.loop_x - self.start_x
        self.loop_len = 2 * math.pi * self.radius
        # Past the loop he flies on until the banner's tail is off the right edge.
        # (plus two frames' travel, so the last frames before he's gone have uncovered it all)
        exit_x = width + self.sprite_w / 2 + self.rope + self.banner_w + 2 + 2 * self.SPEED * s / FPS
        self.length = self.approach + self.loop_len + (exit_x - self.loop_x)
        self.duration = self.length / (self.SPEED * s)
        # Running furthest-right x along the path, for the reveal edge (sampled every half pixel).
        self._reach = []
        best = -math.inf
        for i in range(int(self.length * 2) + 2):
            best = max(best, self.point(i / 2)[0])
            self._reach.append(best)

    def point(self, d):
        """(x, y, heading) at distance d along his path; heading 0 is right, pi/2 up."""
        if d < self.approach:
            return self.start_x + d, self.cruise_y, 0.0
        d -= self.approach
        if d < self.loop_len:
            a = d / self.radius  # counter-clockwise: up the near side, over the top, down
            return (self.loop_x + self.radius * math.sin(a),
                    self.cruise_y - self.radius + self.radius * math.cos(a), a)
        return self.loop_x + d - self.loop_len, self.cruise_y, 0.0

    def travelled(self, t):
        return min(t, self.duration) * self.SPEED * self.scale

    def reveal_x(self, t):
        """Everything left of this is the new ride: the furthest right the banner's tail has been."""
        tail = self.travelled(t) - self.sprite_w / 2 - self.rope - self.banner_w
        if tail < 0:
            return -1
        return max(-1, self._reach[min(len(self._reach) - 1, int(tail * 2))])

    def pose(self, t):
        """The plane's art for t: turned to the nearest quarter of its heading, propeller spinning."""
        _, _, heading = self.point(self.travelled(t))
        art = self.poses[int(round(heading / (math.pi / 2))) % 4]
        if int(t * 24) % 2:
            art = [row.replace("P", ".") for row in art]
        return art

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        s = self.scale
        _blackout(canvas, int(self.reveal_x(t)) + 1, self.width, self.height)
        d = self.travelled(t)
        px = {}
        # The banner, column by column along the path behind him, its front at the rope's end.
        front = d - self.sprite_w / 2 - self.rope
        for half in range(self.banner_w * 2):  # half-pixel steps, so it doesn't tear on the bends
            u = half / 2
            x, y, a = self.point(front - u)
            col = len(self.BANNER_ART[0]) - 1 - int(u) // s
            nx, ny = math.sin(a), math.cos(a)  # across the path, "down" when flying level
            for v in range(self.banner_h):
                off = v - self.banner_h / 2
                px[(int(round(x + nx * off)), int(round(y + ny * off)))] = self.colors[self.BANNER_ART[v // s][col]]
        for k in range(0, self.rope, 2):
            x, y, _ = self.point(d - self.sprite_w / 2 - k)
            px[(int(round(x)), int(round(y)))] = self.ROPE
        # The plane, centred on its point on the path.
        x, y, _ = self.point(d)
        art = self.pose(t)
        x0, y0 = int(round(x - len(art[0]) * s / 2)), int(round(y - len(art) * s / 2))
        px.update(art_pixels(art, x0, y0, self.colors, s))
        paint(canvas, px, self.width, self.height)
        return True
