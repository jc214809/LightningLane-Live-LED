import math
import random

from display.animation.drawing import _blackout, art_pixels, paint
from display.animation.motion import ease_out
from display.pixels import set_pixel


def _fit(slinky, height):
    """Give a Slinky his halves and spring for the board: the BIG_ ones on 64x64."""
    big = "BIG_" if height >= 64 else ""
    slinky.front_art, slinky.rear_art = getattr(slinky, big + "FRONT_ART"), getattr(slinky, big + "REAR_ART")
    slinky.front_look_art = getattr(slinky, big + "FRONT_LOOK_ART", slinky.front_art)
    slinky.rear_wag_art = getattr(slinky, big + "REAR_WAG_ART", slinky.rear_art)
    s = slinky.scale
    slinky.front_w, slinky.front_h = len(slinky.front_art[0]) * s, len(slinky.front_art) * s
    slinky.rear_w, slinky.rear_h = len(slinky.rear_art[0]) * s, len(slinky.rear_art) * s
    coil_h, rise, front_at, rear_back = slinky.BIG_SPRING if big else slinky.SPRING
    slinky.coil_h, slinky.rise, slinky.front_at, slinky.rear_back = coil_h * s, rise * s, front_at * s, rear_back * s


class SlinkyReveal:
    """
    Slinky Dog stretched from one side of the board to the other: his rear sits on the
    left edge while his front half walks right until his nose reaches the right edge,
    pulling his spring out across the whole board. He holds there, then the rear snaps
    across to catch up and both halves bound off the right edge.

    The new screen is revealed behind his front half as it walks, so the spring and rear
    are drawn over it; ahead of him the board stays dark.
    """
    STRETCH_S, HOLD_S, SNAP_S, EXIT_S = 1.3, 0.5, 0.35, 0.55
    duration = STRETCH_S + HOLD_S + SNAP_S + EXIT_S

    # From the user's pixel-art Slinky, mirrored to face right: orange coat, floppy dark ears,
    # big eyes, a long tan muzzle with a black nose, green collar with a red tag; his rear with
    # the spring's grey rings on it and his spring tail, red at the tip. The BIG_ halves are
    # copied cell for cell, for 64x64; on 64x32 they'd fill the board and leave the spring no
    # room, so FRONT_ART and REAR_ART are smaller ones drawn after them. 1x on both boards.
    # '.' empty, A outline, N ear, D dark brown, B orange, F shading, H red-orange, E tan,
    # G white, J black, K collar, L collar shade, C spring grey.
    FRONT_ART = [
        "......DDDDDD.AA...",
        "....AADBBBBBDANNA.",
        "...ANNABFFBBBFANNA",
        "...ANABGJGBGJGBANA",
        "..AANABGJGBGJGBANA",
        "..ANNABGGGBGGGBANA",
        "..ANNABFFFFFFFFANA",
        "..ANABFEEEEEEEEEAA",
        ".AANABFEEEEEEJJJEA",
        ".ANNAAFEEFEEEJJJEA",
        ".ANAHLAAEEFFEEEEEA",
        ".ANAHLKKAAEEEEEDA.",
        ".AANHLKKKNAADDDA..",
        "..AAHLKKKNKLBA....",
        "....ABLKKKLBBA....",
        "...AABBLLLBBBAA...",
        "...AFABBBBBBAFA...",
        "...AFADDDDDDAFA...",
        "..AAAAA....AAAAA..",
        "..DEFED....DEFED..",
    ]
    REAR_ART = [
        "..NN........",
        "..NN........",
        ".CCN........",
        "CGC.........",
        "CC...DDDDD..",
        ".CDABBFHCHD.",
        "..DBBBFHCHCD",
        "..DBBBFHCHCD",
        "..DBBBFHCHCD",
        ".ABDBBFHCHCA",
        "..DBDBFHHHDA",
        "..AFADDDDFA.",
        "..AFA...AFA.",
        ".AAAAA.AAAAA",
        ".DEFED.DEFED",
    ]
    BIG_FRONT_ART = [
        "..............DDDDDDD.AAA.....",
        "............DABBBBBBBDANNA....",
        "........AAADBBBBBBBBBBBANNA...",
        ".......ANNABBFFFFBBBFFFBANA...",
        "......AAANABFBBBBFBFBBBFANNA..",
        "......ANNABFBBFFFFBFFFFFBANA..",
        "......ANNABFFFGJJGBGJJGBBANA..",
        ".....AANNABBBBGJJGBGJJGBBBANA.",
        ".....ANNNABBBBBGGGBGGGBBBBANA.",
        ".....ANANABBBBBBBFFFFFFFBBANA.",
        ".....AANABBBBFFFFEEEEEEEFANNA.",
        ".....ANNABBBFEEEEEEEEEEEEAANA.",
        "....AANNAABBFEEEEEEEJJJJJEANNA",
        "....ANNNAHABFEEFEEEEJJJJJEANNA",
        "....ANNAHLKAAAEEFFEEEEEEEEANNA",
        "...AANNAHLKKKNAAEEFFEEEFFEANNA",
        "...ANNNAHLKKAANNAAEEFFFEEDANNA",
        "...ANANAHLKKNNNALBDDEEEED..AA.",
        "...AANABBLKKKNNKLBA.DDDD......",
        "....AABBBBLKKKKLBBD...........",
        ".....DBBBBBLLLLBBBD...........",
        "....AABBBBBBBBBBBBD...........",
        "...AFFABBBBBBFBBBADA..........",
        "...AFFABBBBBBFBBBAFA..........",
        "...AFFADBBBBBBBAAFFA..........",
        "..AFFFA.DDDDDDDAFFA...........",
        "..AFFA.........AFFA...........",
        ".AAAAAA........AAAAA..........",
        "DEFEEFED......DEFEEFD.........",
        "DEFEEFED......DEFEEFED........",
        "DDDDDDDD......DDDDDDDD........",
    ]
    BIG_REAR_ART = [
        "...NNN..........",
        "...NNN..........",
        "...NNN..........",
        "..CCN...........",
        ".CGC............",
        ".CCC............",
        "CCC.............",
        "CCC.............",
        "CGC.............",
        ".CCC..DDDDD.....",
        ".CCGDABFHHHD....",
        "..CDBBBFHCCHD...",
        "..DBBBFHCHHC....",
        "..DBBBFHCHHCD...",
        "..DBBBFHCHHCD...",
        "..DBBBFHCHHCD...",
        "..DBBBFHCHHCD...",
        "..DDBBFHCHHCD...",
        ".ABBDBFHHCHCA...",
        ".DBBDBBFHCCHD...",
        "..DBBDBFHHHDA...",
        "..AFFADDDDDFA...",
        "..AFFA...AFFA...",
        ".AAAAA...AAAAA..",
        "DEFEFED..AEFEFD.",
        "DEFEFED..DEFEFED",
        "DDDDDDD..DDDDDDD",
    ]
    COLORS = {
        "A": (104, 10, 3), "N": (135, 0, 3), "D": (142, 38, 5), "B": (247, 127, 6), "F": (179, 69, 6),
        "H": (226, 71, 3), "E": (251, 217, 103), "G": (245, 246, 247), "J": (12, 12, 14),
        "K": (39, 137, 39), "L": (1, 77, 1), "C": (128, 128, 128),
    }
    # Where the spring runs for each size of halves: (coil height, its middle's height above
    # the ground, how far into the front half it starts, how far in from the rear's back it
    # ends), in pixels.
    SPRING = (7, 7, 5, 2)
    BIG_SPRING = (9, 10, 6, 4)
    COIL_FRONT, COIL_BACK = (215, 220, 230), (110, 118, 132)
    COILS = 11
    # 1x on both boards: doubled, the two halves eat the 64x64 board and the spring can't stretch.
    SCALE = 1

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.scale = self.SCALE
        s = self.scale
        _fit(self, height)
        self.ground = height  # feet stand on the bottom row
        self.spring_y = self.ground - self.rise  # the coil runs through both bodies
        self.home_rear = 0
        self.min_gap = 3 * s  # a squashed spring between the halves
        self.far_front = width - self.front_w

    def rear_x(self, t):
        snap_at = self.STRETCH_S + self.HOLD_S
        if t < snap_at:
            return self.home_rear
        caught = self.far_front - self.min_gap - self.rear_w
        if t < snap_at + self.SNAP_S:
            p = (t - snap_at) / self.SNAP_S
            return self.home_rear + (caught - self.home_rear) * ease_out(p)
        return caught + self._exit(t)

    def front_x(self, t):
        start = self.home_rear + self.rear_w + self.min_gap
        if t < self.STRETCH_S:
            # Walks out, easing to a stop with his nose at the right edge.
            return start + (self.far_front - start) * ease_out(t / self.STRETCH_S)
        return self.far_front + self._exit(t)

    def _exit(self, t):
        begin = self.STRETCH_S + self.HOLD_S + self.SNAP_S
        p = max(0.0, (t - begin) / self.EXIT_S)
        return p * p * (self.width + self.rear_w + self.min_gap)

    def bob(self, t):
        """A small step-bounce while the front half walks."""
        if t >= self.STRETCH_S:
            return 0
        return -round(abs(math.sin(t * math.pi * 6)) * self.scale)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        fx, rx = self.front_x(t), self.rear_x(t)
        _blackout(canvas, int(fx + self.front_w * 0.5), self.width, self.height)
        self._draw_spring(canvas, rx + self.rear_w - self.rear_back, fx + self.front_at)
        self._draw(canvas, self.rear_art, rx, self.ground - self.rear_h)
        self._draw(canvas, self.front_art, fx, self.ground - self.front_h + self.bob(t))
        return True

    def _draw_spring(self, canvas, x0, x1):
        """
        A row of tilted rings: each coil's back arc in shadow, its front arc bright on
        top. Squashed, the rings overlap into a solid banded tube; stretched, they
        separate into loops you can count.
        """
        if x1 <= x0:
            return
        ry = self.coil_h / 2
        step = (x1 - x0) / self.COILS
        rx = max(1.0, min(step * 0.55, 2.5 * self.scale))
        steps = 8 * self.coil_h
        for front, colour in ((False, self.COIL_BACK), (True, self.COIL_FRONT)):
            for i in range(self.COILS + 1):
                cx = x0 + i * step
                for k in range(steps + 1):
                    a = math.pi * k / steps - math.pi / 2  # top to bottom
                    dx = math.cos(a) * rx
                    x = cx + (dx if front else -dx)
                    # The ring leans: its top sits a little behind its bottom.
                    x += (math.sin(a)) * rx * 0.6
                    self._px(canvas, x, self.spring_y + math.sin(a) * ry, colour)

    def _px(self, canvas, x, y, rgb):
        set_pixel(canvas, int(round(x)), int(round(y)), rgb, self.width, self.height)

    def _draw(self, canvas, art, x0, y0):
        paint(canvas, art_pixels(art, int(round(x0)), int(round(y0)), self.COLORS, self.scale),
              self.width, self.height)


class SlinkyWrapReveal:
    """
    A surprise over a ride screen: Slinky walks in along the bottom, his rear stops in
    the bottom-right corner, and his front half keeps going off the right edge. After a
    random pause his front peeks back in at the top-left, as if the spring ran around
    behind the board. He looks down at his own rear, which wags its tail; then his front
    walks across the top, and his rear follows the same way round: off the right edge at
    the bottom, back in at the top-left, catching up behind him. Then the whole dog walks
    off the right edge.

    No blackout: the ride screen stays readable, and keeps animating, underneath him.
    """

    over_screen = True
    WALK_IN_S, WALK_OFF_S, PEEK_S, LOOK_S = 0.8, 0.5, 0.4, 0.6
    CROSS_S, FOLLOW_S, EXIT_S = 0.7, 0.9, 0.5
    FOLLOW_OUT = 0.4  # share of the follow spent leaving the bottom-right; the rest re-entering
    PAUSE_S = (1.0, 3.0)
    # The longest visit; each one rolls its own pause. With the 0.55s sweep it fits
    # inside the 8s ride screen.
    duration = WALK_IN_S + WALK_OFF_S + PEEK_S + LOOK_S + CROSS_S + FOLLOW_S + EXIT_S + PAUSE_S[1]

    FRONT_ART, REAR_ART = SlinkyReveal.FRONT_ART, SlinkyReveal.REAR_ART
    BIG_FRONT_ART, BIG_REAR_ART = SlinkyReveal.BIG_FRONT_ART, SlinkyReveal.BIG_REAR_ART
    COLORS = SlinkyReveal.COLORS
    SPRING, BIG_SPRING = SlinkyReveal.SPRING, SlinkyReveal.BIG_SPRING
    COIL_FRONT, COIL_BACK = SlinkyReveal.COIL_FRONT, SlinkyReveal.COIL_BACK
    # His front half with the pupils dropped to the bottom-right of each eye: looking
    # down at his rear in the opposite corner.
    FRONT_LOOK_ART = [
        "......DDDDDD.AA...",
        "....AADBBBBBDANNA.",
        "...ANNABFFBBBFANNA",
        "...ANABGGGBGGGBANA",
        "..AANABGGJBGGJBANA",
        "..ANNABGGJBGGJBANA",
        "..ANNABFFFFFFFFANA",
        "..ANABFEEEEEEEEEAA",
        ".AANABFEEEEEEJJJEA",
        ".ANNAAFEEFEEEJJJEA",
        ".ANAHLAAEEFFEEEEEA",
        ".ANAHLKKAAEEEEEDA.",
        ".AANHLKKKNAADDDA..",
        "..AAHLKKKNKLBA....",
        "....ABLKKKLBBA....",
        "...AABBLLLBBBAA...",
        "...AFABBBBBBAFA...",
        "...AFADDDDDDAFA...",
        "..AAAAA....AAAAA..",
        "..DEFED....DEFED..",
    ]
    BIG_FRONT_LOOK_ART = [
        "..............DDDDDDD.AAA.....",
        "............DABBBBBBBDANNA....",
        "........AAADBBBBBBBBBBBANNA...",
        ".......ANNABBFFFFBBBFFFBANA...",
        "......AAANABFBBBBFBFBBBFANNA..",
        "......ANNABFBBFFFFBFFFFFBANA..",
        "......ANNABFFFGGGGBGGGGBBANA..",
        ".....AANNABBBBGGJJBGGJJBBBANA.",
        ".....ANNNABBBBBGJJBGGJBBBBANA.",
        ".....ANANABBBBBBBFFFFFFFBBANA.",
        ".....AANABBBBFFFFEEEEEEEFANNA.",
        ".....ANNABBBFEEEEEEEEEEEEAANA.",
        "....AANNAABBFEEEEEEEJJJJJEANNA",
        "....ANNNAHABFEEFEEEEJJJJJEANNA",
        "....ANNAHLKAAAEEFFEEEEEEEEANNA",
        "...AANNAHLKKKNAAEEFFEEEFFEANNA",
        "...ANNNAHLKKAANNAAEEFFFEEDANNA",
        "...ANANAHLKKNNNALBDDEEEED..AA.",
        "...AANABBLKKKNNKLBA.DDDD......",
        "....AABBBBLKKKKLBBD...........",
        ".....DBBBBBLLLLBBBD...........",
        "....AABBBBBBBBBBBBD...........",
        "...AFFABBBBBBFBBBADA..........",
        "...AFFABBBBBBFBBBAFA..........",
        "...AFFADBBBBBBBAAFFA..........",
        "..AFFFA.DDDDDDDAFFA...........",
        "..AFFA.........AFFA...........",
        ".AAAAAA........AAAAA..........",
        "DEFEEFED......DEFEEFD.........",
        "DEFEEFED......DEFEEFED........",
        "DDDDDDDD......DDDDDDDD........",
    ]
    # His rear with the spring tail leaning forward over his back: alternated with REAR_ART
    # it wags.
    REAR_WAG_ART = [
        ".....NN.....",
        "....NN......",
        "...CCN......",
        ".CGC........",
        ".CC..DDDDD..",
        ".CDABBFHCHD.",
        "..DBBBFHCHCD",
        "..DBBBFHCHCD",
        "..DBBBFHCHCD",
        ".ABDBBFHCHCA",
        "..DBDBFHHHDA",
        "..AFADDDDFA.",
        "..AFA...AFA.",
        ".AAAAA.AAAAA",
        ".DEFED.DEFED",
    ]
    BIG_REAR_WAG_ART = [
        ".........NNN....",
        "........NNN.....",
        "........NNN.....",
        "......CCN.......",
        ".....CGC........",
        "....CCC.........",
        "...CCC..........",
        "..CCC...........",
        "..CGC...........",
        "..CCC.DDDDD.....",
        "..CCDABFHHHD....",
        "..CDBBBFHCCHD...",
        "..DBBBFHCHHC....",
        "..DBBBFHCHHCD...",
        "..DBBBFHCHHCD...",
        "..DBBBFHCHHCD...",
        "..DBBBFHCHHCD...",
        "..DDBBFHCHHCD...",
        ".ABBDBFHHCHCA...",
        ".DBBDBBFHCCHD...",
        "..DBBDBFHHHDA...",
        "..AFFADDDDDFA...",
        "..AFFA...AFFA...",
        ".AAAAA...AAAAA..",
        "DEFEFED..AEFEFD.",
        "DEFEFED..DEFEFED",
        "DDDDDDD..DDDDDDD",
    ]
    SCALE = 1
    COILS = 11
    STUB_COILS = 2  # coils showing beside each piece while the spring is round the back

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        rng = rng or random.Random()
        s = self.scale = self.SCALE
        _fit(self, height)
        self.gap = 3 * s
        self.coil_step = 3 * s  # ring spacing on the stubs that run off an edge
        self.bottom = height  # ground lines: feet on the bottom row, or under the top-left peek
        self.top = self.front_h
        self.rear_home = width - self.rear_w - self.STUB_COILS * self.coil_step
        # One extra step: the ring nearest the left edge is half cut off by it.
        self.peek_x = (self.STUB_COILS + 1) * self.coil_step - 4 * s
        self.pause = rng.uniform(*self.PAUSE_S)
        self.duration = self.visit_s()
        b = [self.WALK_IN_S, self.WALK_OFF_S, self.pause, self.PEEK_S, self.LOOK_S,
             self.CROSS_S, self.FOLLOW_S, self.EXIT_S]
        self.beats = [sum(b[:i + 1]) for i in range(len(b))]

    def visit_s(self):
        return (self.WALK_IN_S + self.WALK_OFF_S + self.pause + self.PEEK_S + self.LOOK_S
                + self.CROSS_S + self.FOLLOW_S + self.EXIT_S)

    def phase(self, t):
        """(name, 0..1 progress through it) for time t."""
        names = ("walk_in", "walk_off", "pause", "peek", "look", "cross", "follow", "exit")
        start = 0.0
        for name, end in zip(names, self.beats):
            if t < end:
                return name, (t - start) / (end - start)
            start = end
        return "done", 1.0

    def pose(self, t):
        """
        Where both halves are: {"front": (x, ground) or None, "rear": (x, ground)}, where
        ground is the row under his feet. The front is None while it's off the board.
        """
        name, p = self.phase(t)
        W = self.width
        cross_end = W - self.front_w
        landed = cross_end - self.gap - self.rear_w
        if name == "walk_in":
            rear = -self.rear_w - self.gap - self.front_w + (self.rear_home + self.rear_w + self.gap + self.front_w) * ease_out(p)
            return {"rear": (rear, self.bottom), "front": (rear + self.rear_w + self.gap, self.bottom)}
        if name == "walk_off":
            start = self.rear_home + self.rear_w + self.gap
            return {"rear": (self.rear_home, self.bottom), "front": (start + (W - start) * p * p, self.bottom)}
        if name == "pause":
            return {"rear": (self.rear_home, self.bottom), "front": None}
        if name == "peek":
            return {"rear": (self.rear_home, self.bottom),
                    "front": (-self.front_w + (self.peek_x + self.front_w) * ease_out(p), self.top)}
        if name == "look":
            return {"rear": (self.rear_home, self.bottom), "front": (self.peek_x, self.top)}
        if name == "cross":
            return {"rear": (self.rear_home, self.bottom),
                    "front": (self.peek_x + (cross_end - self.peek_x) * ease_out(p), self.top)}
        if name == "follow":
            # The rear goes the way his front went: off the right edge along the bottom...
            if p < self.FOLLOW_OUT:
                q = p / self.FOLLOW_OUT
                return {"rear": (self.rear_home + (W - self.rear_home) * q * q, self.bottom),
                        "front": (cross_end, self.top)}
            # ...then back in from the left along the top, catching up behind him.
            q = (p - self.FOLLOW_OUT) / (1 - self.FOLLOW_OUT)
            x = -self.rear_w + (landed + self.rear_w) * ease_out(q)
            return {"rear": (x, self.top), "front": (cross_end, self.top)}
        if name == "exit":
            dx = p * p * (W + self.rear_w)
            return {"rear": (landed + dx, self.top), "front": (cross_end + dx, self.top)}
        return {"rear": (W, self.top), "front": (W, self.top)}

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        name, _ = self.phase(t)
        pose, s = self.pose(t), self.scale
        rx, rg = pose["rear"]
        rear_art = self.rear_wag_art if name == "look" and int(t * 8) % 2 else self.rear_art
        walking = name in ("walk_in", "walk_off", "cross", "follow", "exit")
        bob = -round(abs(math.sin(t * math.pi * 6)) * s) if walking else 0
        rear_attach = (rx + self.rear_w - self.rear_back, rg - self.rise)
        # Split while the rear is still on the bottom: until it re-enters at the top-left.
        split = name in ("pause", "peek", "look", "cross") or (name == "follow" and rg == self.bottom)
        if split:
            # The spring runs off the right edge from his rear, and back in from the left
            # edge to his front: the middle of it is round the back of the board.
            self._spring(canvas, rear_attach, (self.width + self.coil_step, rear_attach[1]), self.coil_step)
            if pose["front"]:
                fx, fg = pose["front"]
                self._spring(canvas, (-self.coil_step, fg - self.rise), (fx + self.front_at, fg - self.rise),
                             self.coil_step)
        elif pose["front"]:
            fx, fg = pose["front"]
            span = max(1.0, fx + self.front_at - rear_attach[0])
            self._spring(canvas, rear_attach, (fx + self.front_at, fg - self.rise),
                         max(1.5 * s, min(span / self.COILS, 3.5 * s)))
        self._draw(canvas, rear_art, rx, rg - self.rear_h)
        if pose["front"]:
            fx, fg = pose["front"]
            art = self.front_look_art if name == "look" else self.front_art
            self._draw(canvas, art, fx, fg - self.front_h + bob)
        return True

    def _spring(self, canvas, a, b, step):
        """Tilted rings every `step` pixels from a to b: shaded backs, then bright fronts."""
        (x0, y0), (x1, y1) = a, b
        length = math.hypot(x1 - x0, y1 - y0)
        if length <= 0:
            return
        count = max(1, int(length / step))
        ry = self.coil_h / 2
        rx = max(1.0, min(step * 0.55, 2.5 * self.scale))
        steps = 8 * self.coil_h
        for front, colour in ((False, self.COIL_BACK), (True, self.COIL_FRONT)):
            for i in range(count + 1):
                f = i / count
                cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                for k in range(steps + 1):
                    ang = math.pi * k / steps - math.pi / 2
                    dx = math.cos(ang) * rx
                    x = cx + (dx if front else -dx) + math.sin(ang) * rx * 0.6
                    self._px(canvas, x, cy + math.sin(ang) * ry, colour)

    def _px(self, canvas, x, y, rgb):
        set_pixel(canvas, int(round(x)), int(round(y)), rgb, self.width, self.height)

    def _draw(self, canvas, art, x0, y0):
        paint(canvas, art_pixels(art, int(round(x0)), int(round(y0)), self.COLORS, self.scale),
              self.width, self.height)
