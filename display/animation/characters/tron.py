from display.animation.drawing import _blackout, art_pixels, paint
from display.animation.mechanics import FlyByReveal


class TronReveal(FlyByReveal):
    """
    Two TRON light cycles race left to right, blue across the top of the board and red
    along the bottom, red starting a length behind and closing to level by the far edge.
    Each lays a solid light trail at wheel height; everything behind the trailing bike, top
    to bottom, is already the new ride. The trails hang on a beat after the bikes are gone,
    then de-rez.
    """

    CROSS_S, HOLD_S, FADE_S = 1.1, 0.2, 0.4
    duration = CROSS_S + HOLD_S + FADE_S
    SCALE = 1  # 1x on both boards: doubled, one bike filled half of a 64x64 board
    RED_LAG = 10  # how far behind red starts, in pixels; it's level by the end

    # Side view, nose right, from the user's mockup (mirrored): ring wheels, a tall fin over
    # the rear wheel with a lit square front edge, a small rounded cowl over the front one,
    # and a low body between whose light stripe climbs into the cowl. Two ring wheels under a
    # plain bar read as a pair of glasses; the fin and cowl are what make it a light cycle.
    # The shell is a lifted charcoal, since LEDs draw black as off. '.' empty, C wheel ring,
    # D wheel's inside, B shell, H highlight, L light stripe.
    art = [
        "........BBHHH.................",
        "......BBBBBBH.................",
        "....BBBBBBBBH......BBBBBB.....",
        "...CCCCBBBBBH.....BLBBBCCCC...",
        "..CCDDCCBBBBH.....LBBBCCDDCC..",
        ".CDDDDDDCBBBBBBBBLBBBCDDDDDDC.",
        ".CDDDDDDCLLLLLLLLBBBBCDDDDDDC.",
        ".CDDDHDDCCBBBBBBBBB.CCDDDHDDC.",
        ".CDDDDDDC............CDDDDDDC.",
        ".CDDDDDDC............CDDDDDDC.",
        "..CCDDCC..............CCDDCC..",
        "...CCCC................CCCC...",
    ]
    TRAIL_ROWS = (5, 10)  # the art rows the trail spans, its edges one pixel darker
    BLUE = {"C": (0, 200, 255), "D": (16, 18, 24), "B": (38, 44, 54), "H": (95, 105, 118),
            "L": (120, 240, 255)}
    RED = {"C": (255, 45, 25), "D": (24, 16, 16), "B": (54, 38, 38), "H": (118, 100, 95),
           "L": (255, 150, 110)}
    TRAILS = {"blue": ((0, 200, 230), (0, 110, 210)), "red": ((235, 35, 20), (150, 15, 10))}
    colors = BLUE  # the sprite editor previews the art in blue

    def __init__(self, width, height, rng=None):
        super().__init__(width, height, rng)
        self.scale = self.SCALE
        self.sprite_w, self.sprite_h = len(self.art[0]) * self.scale, len(self.art) * self.scale

    def bikes(self, t):
        """[(name, x, y)] for the blue bike on top and the red one on the bottom at time t."""
        # Linear, like light cycles holding their lines; both tails clear the right edge at CROSS_S.
        p = min(t, self.CROSS_S) / self.CROSS_S
        x = -self.sprite_w + p * (self.width + self.sprite_w + self.RED_LAG)
        return [("blue", x, 0), ("red", x - self.RED_LAG * (1 - p), self.height - self.sprite_h)]

    def position(self, t):
        _, x, y = self.bikes(t)[0]
        return x, y

    def spawn(self, x, y):
        return []

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        bikes = [(name, int(round(x)), y) for name, x, y in self.bikes(t)]
        if t < self.CROSS_S:
            _blackout(canvas, min(x for _, x, _ in bikes) + self.sprite_w, self.width, self.height)
        # The trails de-rez rather than dimming: dimming would darken the new screen under
        # them (a Pi canvas can't be read back to blend with), so each pixel drops out whole,
        # in a fixed scattered order.
        left = 1.0 if t < self.CROSS_S + self.HOLD_S else 1.0 - (t - self.CROSS_S - self.HOLD_S) / self.FADE_S
        for name, x, y in bikes:
            core, edge = self.TRAILS[name]
            top, bottom = (y + r * self.scale for r in self.TRAIL_ROWS)
            for py in range(top, bottom):
                rgb = edge if py in (top, bottom - 1) else core
                for px in range(0, min(self.width, x + self.scale)):
                    if ((px * 73856093) ^ (py * 19349663)) % 1000 < left * 1000:
                        canvas.SetPixel(px, py, *rgb)
        if t < self.CROSS_S:
            for name, x, y in bikes:
                self._draw_bike(canvas, x, y, self.BLUE if name == "blue" else self.RED)
        return True

    def _draw_bike(self, canvas, x0, y0, colors):
        paint(canvas, art_pixels(self.art, x0, y0, colors, self.scale), self.width, self.height)
