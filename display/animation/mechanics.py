"""
The kinds of transition the characters are built on: a plain wipe, a fly-by, a peek,
and the screen capture that reveals needing a screen's pixels share.
"""

import random

from display.capture import capture_screen

from display.animation.drawing import _blackout, _edge, art_pixels, paint
from display.animation.motion import FLYBY_S, FPS, WIPE_S, ease_out


class CapturesScreens:
    """
    For reveals that need a screen's pixels (wants_prev / wants_new): show_screen hands them
    over through these, recorded off a Capture canvas (a Pi's own canvas can't be read back).
    """

    prev_px = {}
    new_px = {}

    def capture_prev(self, prev_draw, prev_t):
        """The outgoing screen's pixels."""
        self.prev_px = capture_screen(prev_draw, prev_t, self.width, self.height)

    def capture_new(self, draw_new, new_t):
        """The incoming screen's pixels."""
        self.new_px = capture_screen(draw_new, new_t, self.width, self.height)


class Wipe:
    """Reveals the new screen left to right behind a gold edge."""

    duration = WIPE_S

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = int(ease_out(t / self.duration) * (self.width + 1))
        _blackout(canvas, x + 1, self.width, self.height)
        _edge(canvas, x, self.width, self.height)
        return True


class FlyByReveal:
    """
    A character flies across the board and the new screen appears behind them and
    their particle trail. Subclasses supply the sprite, flight path and trail.
    """

    duration = FLYBY_S
    art = []
    colors = {}

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.art[0]) * self.scale
        self.sprite_h = len(self.art) * self.scale
        # Each particle: [x, y, vx, vy, frames_left, rgb]
        self.particles = []
        self.last_frame = -1

    def progress_x(self, t):
        # Starts just off the left edge and ends just off the right.
        return -self.sprite_w + (t / self.duration) * (self.width + 2 * self.sprite_w)

    def position(self, t):
        raise NotImplementedError

    def spawn(self, x, y):
        """New trail particles for a frame where the sprite's top-left corner is at (x, y)."""
        raise NotImplementedError

    def _step_particles(self, t):
        frame = int(t * FPS)
        while self.last_frame < frame:
            self.last_frame += 1
            if self.last_frame / FPS < self.duration:
                self.particles.extend(self.spawn(*self.position(self.last_frame / FPS)))
            for p in self.particles:
                p[0] += p[2]
                p[1] += p[3]
                p[4] -= 1
            self.particles = [p for p in self.particles if p[4] > 0]

    def overlay(self, canvas, t):
        self._step_particles(t)
        if t < self.duration:
            x, _ = self.position(t)
            _blackout(canvas, int(x) + self.sprite_w // 2 + 1, self.width, self.height)
        for px, py, _, _, life, rgb in self.particles:
            f = min(1.0, life / 12)
            px, py = int(round(px)), int(round(py))
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *(int(c * f) for c in rgb))
        if t < self.duration:
            self._draw_sprite(canvas, t)
        return t < self.duration or bool(self.particles)

    def _draw_sprite(self, canvas, t):
        x0, y0 = self.position(t)
        paint(canvas, art_pixels(self.art, int(round(x0)), int(round(y0)), self.colors, self.scale),
              self.width, self.height)


class PeekReveal:
    """
    A character pops up from the bottom edge over the already-revealed screen, looks
    around, and ducks back down — no blackout, no particle trail, no travel across
    the board. Subclasses supply the art and how far up "peeking" rises.
    """

    duration = 0
    over_screen = True
    art = []
    colors = {}
    rise_frac = 0.55  # fraction of the sprite's height that stays visible at the peek's peak

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        # self.art is either one pose (a list of row-strings) or several poses
        # (a list of those); measure the first pose's rows either way.
        first_pose = self.art[0] if isinstance(self.art[0], list) else self.art
        self.sprite_w = len(first_pose[0]) * self.scale
        self.sprite_h = len(first_pose) * self.scale
        self.cx = rng.uniform(0.3, 0.7) * width if rng else width / 2

    def rise(self, t):
        """0 (hidden below the edge) to 1 (fully risen) over the whole duration, holding at the top."""
        raise NotImplementedError

    def look_frame(self, t):
        """Index into self.art's alternate poses (e.g. head turned) for this t, or 0 if art has only one."""
        return 0

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        rise = max(0.0, min(1.0, self.rise(t)))
        if rise <= 0:
            return True
        # y0 slides from `height` (sprite entirely below the board, hidden) up to
        # `height - rise_frac * sprite_h` (his top rise_frac risen above the edge).
        # Rows that land at py >= height are still "underground" — the bounds check
        # below simply doesn't draw them, no separate clipping needed.
        y0 = self.height - rise * self.rise_frac * self.sprite_h
        x0 = int(self.cx - self.sprite_w / 2)
        art = self.art[self.look_frame(t)] if isinstance(self.art[0], list) else self.art
        paint(canvas, art_pixels(art, x0, int(round(y0)), self.colors, self.scale), self.width, self.height)
        return True
