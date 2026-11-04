from display.animation.drawing import _blackout
from display.motion import ease_out, progress
from display.pixels import art_pixels, paint


class McQueenReveal:
    """
    Lightning McQueen zooms in from the left and skids to a stop mid-board, holds a beat, then
    peels out off the right edge. Orange-and-yellow speed
    streaks trail him while he's moving, longer the faster he goes, and the new ride is
    uncovered behind him.
    """

    ZOOM_S, PEEL_S = 0.6, 1.4  # when he stops, when he goes (a sparkle across his side read as a "+")
    duration = 2.1

    # From the user's pixel-art McQueen, side on and facing right: his lightning bolt, a
    # cleaned-up 95 (the source's digits were a scramble at this size), the eye in his
    # windshield, and flames at his tail. 1x on both boards. '.' empty, R red, r dark red,
    # O orange, Y yellow, D the 95's digits, N windows and hubs, K tyres, W white, L grey,
    # E his blue eye.
    ART = [
        "RR..............RRRRRRRRRRRR...................",
        "RRORR........RRRRRNNNNNNRRRrr..................",
        "ROROOR.....RRRDDDDRNNNNNNRrWWL.................",
        "..RR.....RRRDDDDDDRNNNNNNRRWWEK................",
        ".RRORRRRRrrrRDDDDDDRNNNNNNRRWEKL...............",
        ".ORROOOROOOOrrrRRRRRRRRRRRRRRRRRRRRRRRRRR......",
        "RROORROOOOOOOOrrORRRrRRRRRRRRWRRRRRRRRRRRRR....",
        "RRRROOOKKKKKKOOYrOOYYrOYYRRRLRWWRRKKKKKKRRRRO..",
        "ROROOOKKKKKKKKOOOrYDDDYDDDYrRRRRRKKKKKKKKRRROO.",
        ".ROROKKKKNNKKKKOYOYDYDYDYYYYRRRLKKKKNNKKKKRRRRR",
        ".RRROKKKNNNNKKKOOOYDDDYDDDYYYrRRKKKNNNNKKKRRrRR",
        "..RORKKNNKKNNKKOOYYYYDYYYDYYYYRRKKNNKKNNKKRRRrr",
        "....RKKNNKKNNKKYOYYDDDYDDDYYYYrRKKNNKKNNKKRRRRR",
        ".....KKKNNNNKKKOOOOYRRrYRRrRrYYRKKKNNNNKKKRRRR.",
        ".....KKKKNNKKKKKNNKNRRRrRrRRRKrrKKKKNNKKKKRRRR.",
        "......KKKKKKKK.KKNKKNRRRRRRRRRRR.KKKKKKKK.RRR..",
        ".......KKKKKK.....................KKKKKK.......",
    ]
    colors = {"R": (236, 36, 37), "r": (127, 21, 23), "O": (245, 136, 34), "Y": (250, 196, 43),
              "D": (40, 40, 44), "N": (76, 77, 80), "K": (28, 28, 32), "W": (253, 252, 252),
              "L": (150, 153, 150), "E": (1, 130, 190)}
    STREAKS = ((245, 136, 34), (250, 196, 43))

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.w, self.h = len(self.ART[0]), len(self.ART)
        self.y0 = height - self.h - 1  # on the ground
        self.stop_x = (width - self.w) // 2

    def x_at(self, t):
        """His left edge at t: fast in, braking hard to a skid, then accelerating away."""
        if t < self.ZOOM_S:
            return -self.w + (self.stop_x + self.w) * ease_out(t / self.ZOOM_S)
        if t < self.PEEL_S:
            return float(self.stop_x)
        p = progress(t, self.PEEL_S, self.duration)
        return self.stop_x + (self.width + 1 - self.stop_x) * p * p  # flooring it

    def speed(self, t, dt=1 / 60):
        return abs(self.x_at(t + dt) - self.x_at(t)) / dt

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = int(round(self.x_at(t)))
        _blackout(canvas, x + self.w, self.width, self.height)
        px = {}
        # Speed streaks behind him, as long as he's fast.
        length = int(min(self.width, self.speed(t) * 0.12))
        for i, row in enumerate((4, 7, 10, 13)):
            rgb = self.STREAKS[i % 2]
            start = x - 2 - (i % 2) * 3
            for sx in range(max(0, start - length), max(0, start)):
                px[(sx, self.y0 + row)] = rgb
        px.update(art_pixels(self.ART, x, self.y0, self.colors))
        paint(canvas, px, self.width, self.height)
        return True
