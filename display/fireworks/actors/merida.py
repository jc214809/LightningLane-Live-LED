"""Merida for the synced show's Touch the Sky (see show_actors.py)."""
import math

from display.fireworks.actors.base import Actor, stamp
from display.motion import ease_out


class MeridaShoots(Actor):
    """
    Touch the Sky: Merida (docs/references/Brave.jpg, 1x; 64x64 only, as 64x32 is too short for her)
    rises at the bottom left in her first ENTER_S and says her line, "Your destiny lies within you...",
    to the score's mouth track (MOUTHS: closed smile, half, open). On "touch the sky" a firework bursts
    into a bullseye high on the right (TARGET_S) and hangs there; she looses an arrow (LOOSE_S) that
    flies up across the board, trailing white, and hits its centre (HIT_S), and the target shatters
    into sparks of its own colours.
    She sinks away in her scene's last ENTER_S. Times are seconds into her scene.
    """
    NAME = "Merida"
    ENTER_S = 0.6
    TARGET_S = 26.3  # 294.3: "chase the wind"
    BURST_S = 0.35  # the bullseye opening
    LOOSE_S = 27.36  # 295.36: "touch"
    HIT_S = 28.34  # 296.34: "sky"
    SHATTER_S = 1.3  # the sparks' fall
    # Brave.jpg's chart less its top two rows (her hair's tufts), with a row of skin added under her
    # cheeks for her mouth, so her face sits higher in her hair. '.' empty, O and R her hair, W skin,
    # p her cheeks, w white, b and B her eyes, K her bow (the chart's black, lifted so the LEDs show
    # it), r its wood, Y and y her collar and sleeves' gold, C her dress, c its shadow, o her quiver.
    ART = (
        ".......ROROORORRORR.......",
        "......ROROOOOROOROOR......",
        ".....ROROOROROOOOROR......",
        "..rK.ROOORWOWWWRRROOR.....",
        "..rwKwRORWWWWWRWWWOROR....",
        "..rwRKOOWWbwWWWwbWWROR....",
        "...rOOKOWpBBWWWBBpWROOR...",
        "..RrOOOKWpWWWWWWWpWOROR...",
        "..RrOROOKWWWWWWWWWOROR....",
        "..RrOROOKWWWWWWWWWOROR....",
        "..ROrOOROKWWWWWWWROOORO...",
        ".ROOrOROOOKOWWWOROOROOR...",
        "ROOORrOOYWWWWWWWWWYOROOR..",
        "ROROOOryyYWWWWWWWYyyOOROR.",
        ".RORORYYCCYYYYYYYCCYYROOOR",
        ".ROOROCCCCCCCCCCCCCCCORROR",
        "..R.RCCCCrCCCCCCCOCCCCO.R.",
        ".....CyyROrCCCCCRKOyyCO...",
        "...K.yYYwwwCCCCCwwKYYy....",
        "..KwKYCCCwwCCCCrwwCCCY....",
        "...KwKWWWWCCCCrrCWWWWK....",
        "....KooWWCCCrrrCCCWWwwK...",
        ".....ooorrrrrCCCCCCrrwwK..",
        "......oCCCCCCCCCCCCCwrrrr.",
        "......CCCCCCCCCCCCCCC.....",
        "......CCCCCCCCCCCCCCC.....",
        "......CCCCCCCCCCCCCCC.....",
        ".....CCCCCCCCCCCCCCCCC....",
        ".....CCCCCCCCCCCCCCCCC....",
        "....cCCCCCCCCCCCCCCCCCc...",
        "....cCCCCCCCCCCCCCCCCCc...",
        "...cCCCCCCcCCCCCcCCCCCCc..",
        "...cCCCCCCcCCCCCcCCCCCCc..",
        "...cCCCCCcCCCCCCCcCCCCCc..",
        "....cCCCcCCCCCCCCCcCCCc...",
        ".....cCcCCCCCCCCCCCcCc....",
        "......cccCCCCCCCCCccc.....",
        ".........ccccccccc........",
    )
    COLORS = {
        "C": (0, 150, 138), "c": (36, 73, 82), "O": (255, 127, 62), "R": (226, 91, 69),
        "W": (242, 228, 214), "p": (250, 175, 170), "w": (255, 255, 255), "b": (38, 137, 202),
        "B": (1, 101, 179), "K": (75, 70, 65), "r": (107, 82, 77), "Y": (249, 215, 55),
        "y": (251, 239, 141), "o": (158, 113, 84),
        "m": (200, 90, 95), "D": (110, 35, 40),  # her lips' line and the inside of her mouth
    }
    # Her mouth under her cheeks (row 9, the added one), by shape: (x, y, kind) over ART. 0 closed is
    # a small smile.
    MOUTH_ROW = 9
    MOUTHS = {
        0: [(12, 9, "m"), (13, 9, "m"), (14, 9, "m"), (11, 8, "m"), (15, 8, "m")],
        1: [(12, 9, "D"), (13, 9, "D"), (14, 9, "D")],
        2: [(12, 9, "D"), (13, 9, "D"), (14, 9, "D"), (13, 10, "D"), (12, 10, "m"), (14, 10, "m")],
    }
    LEFT = 0
    TARGET = (49, 12)  # the bullseye's centre, high over the castle's right
    # Its rings from the centre out: gold, red, white, red.
    RINGS = ((1.2, (255, 210, 60)), (2.4, (230, 40, 40)), (3.6, (245, 245, 245)), (4.8, (230, 40, 40)))
    # The arrow, bright so it shows through the scene's fireworks: a pale shaft, a white tip, red
    # fletching and a fading white trail (TRAIL px) behind it.
    SHAFT = (235, 205, 150)
    FLETCH = (240, 60, 50)
    TIP = (255, 255, 255)
    TRAIL = 8
    SPARKS = 28

    def __init__(self, show):
        super().__init__(show)
        self.w, self.h = len(self.ART[0]), len(self.ART)
        self.top = show.height - self.h
        self.arts = {}
        for shape, cells in self.MOUTHS.items():
            g = [list(row) for row in self.ART]
            for x, y, k in cells:
                g[y][x] = k
            self.arts[shape] = ["".join(row) for row in g]
        # Where the arrow leaves her: her raised bow hand, at the top of her bow.
        self.nock = (self.LEFT + 4, self.top + 4)

    def scene_s(self):
        cue = self.show.cue
        return cue.end - self.since if cue is not None and self.since is not None else 35.0

    def drop(self, e):
        """Rows below her standing place e seconds in: rising in her first ENTER_S, sinking in her last."""
        p = min(1.0, e / self.ENTER_S, max(0.0, (self.scene_s() - e) / self.ENTER_S))
        return int(math.floor(self.h * (1 - ease_out(max(0.0, p))) + 0.5))

    def arrow_at(self, e):
        """The arrow's head (x, y) and direction e seconds in, or None before it's loosed or once the
        target has shattered. It flies on a shallow arc from her bow to the target's centre."""
        if e < self.LOOSE_S or e >= self.HIT_S + self.SHATTER_S * 0.3:
            return None
        k = min(1.0, (e - self.LOOSE_S) / (self.HIT_S - self.LOOSE_S))
        (x0, y0), (x1, y1) = self.nock, self.TARGET
        lift = 6.0  # the arc's height over the straight line
        x = x0 + (x1 - x0) * k
        y = y0 + (y1 - y0) * k - lift * 4 * k * (1 - k)
        dx = x1 - x0
        dy = (y1 - y0) - lift * 4 * (1 - 2 * k)
        n = math.hypot(dx, dy)
        return (x, y), (dx / n, dy / n)

    def draw(self, put, out, active):
        if not active or not self.big:
            return
        e = self.elapsed()
        self.draw_target(out, e)
        dy = self.drop(e)
        if dy < self.h:
            shape = self.mouth("merida")
            stamp(out, self.arts[0 if shape is None else shape], self.COLORS, self.LEFT, self.top + dy, 1,
                  self.show.width, self.show.height)
        self.draw_arrow(out, e)

    def _put(self, out, x, y, rgb):
        x, y = int(math.floor(x + 0.5)), int(math.floor(y + 0.5))
        if 0 <= x < self.show.width and 0 <= y < self.show.height:
            out[(x, y)] = rgb

    def draw_target(self, out, e):
        """The bullseye: bursting open from TARGET_S, hanging with a twinkle, shattering at HIT_S."""
        if e < self.TARGET_S:
            return
        cx, cy = self.TARGET
        if e < self.HIT_S:
            grow = ease_out(min(1.0, (e - self.TARGET_S) / self.BURST_S))
            outer = self.RINGS[-1][0] * grow
            for y in range(cy - 5, cy + 6):
                for x in range(cx - 5, cx + 6):
                    d = math.hypot(x - cx, y - cy) * (self.RINGS[-1][0] / outer if outer > 0.01 else 99)
                    for r, rgb in self.RINGS:
                        if d < r:
                            twinkle = 0.85 + 0.15 * math.sin(e * 9 + x * 1.7 + y * 2.3)
                            self._put(out, x, y, tuple(int(c * twinkle) for c in rgb))
                            break
            return
        # Shattered: gold sparks flying out from the centre and falling, dimming as they go.
        s = e - self.HIT_S
        if s >= self.SHATTER_S:
            return
        fade = 1 - s / self.SHATTER_S
        for i in range(self.SPARKS):
            a = 2 * math.pi * i / self.SPARKS
            speed = 9 + 5 * ((i * 7) % 3)
            x = cx + math.cos(a) * speed * s
            y = cy + math.sin(a) * speed * s + 10 * s * s
            rgb = self.RINGS[i % len(self.RINGS)][1]  # in the target's own colours
            self._put(out, x, y, tuple(int(c * fade) for c in rgb))

    def draw_arrow(self, out, e):
        at = self.arrow_at(e)
        if at is None:
            return
        (x, y), (ux, uy) = at
        if e < self.HIT_S:  # the trail, fading back toward her bow
            for i in range(6, 6 + self.TRAIL):
                g = 0.6 * (1 - (i - 6) / self.TRAIL)
                self._put(out, x - ux * i, y - uy * i, tuple(int(255 * g) for _ in range(3)))
        self._put(out, x, y, self.TIP)
        for i in range(1, 5):
            self._put(out, x - ux * i, y - uy * i, self.SHAFT)
        self._put(out, x - ux * 5, y - uy * 5, self.FLETCH)
