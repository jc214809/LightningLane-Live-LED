import math
import random
import time

from driver import graphics

FPS = 30
COVER_S = 0.25
WIPE_S = 0.3
FLYBY_S = 1.2
EDGE_RGB = (255, 215, 0)

_canvases = {}
_last_screen = {}


def frame_canvas(matrix):
    """One reusable offscreen canvas per matrix; rgbmatrix never frees canvases from CreateFrameCanvas."""
    key = id(matrix)
    if key not in _canvases:
        _canvases[key] = matrix.CreateFrameCanvas()
    return _canvases[key]


def present(matrix, canvas):
    """Show canvas and keep the returned back buffer for the next frame."""
    _canvases[id(matrix)] = matrix.SwapOnVSync(canvas)
    return _canvases[id(matrix)]


def forget_screen(matrix):
    """The next screen should reveal from black rather than cover whatever played last."""
    _last_screen.pop(id(matrix), None)


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def run_frames(matrix, draw_frame, duration_s, fps=FPS):
    """Call draw_frame(canvas, t) each frame for duration_s; once it returns False the image is static and we sleep out the rest."""
    frame_time = 1.0 / fps
    frames = int(duration_s * fps)
    canvas = frame_canvas(matrix)
    began = time.monotonic()
    for i in range(frames):
        start = time.monotonic()
        # A slow board drops frames rather than stretching the screen past duration_s.
        if start - began >= duration_s:
            return
        canvas.Clear()
        animating = draw_frame(canvas, i / fps)
        canvas = present(matrix, canvas)
        if not animating:
            time.sleep(max(0.0, duration_s - (time.monotonic() - began)))
            return
        remaining = frame_time - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)


def _blackout(canvas, x0, x1, height):
    black = graphics.Color(0, 0, 0)
    for x in range(max(0, x0), x1):
        graphics.DrawLine(canvas, x, 0, x, height - 1, black)


def _edge(canvas, x, width, height):
    if 0 <= x < width:
        graphics.DrawLine(canvas, x, 0, x, height - 1, graphics.Color(*EDGE_RGB))


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
        x0, y0 = int(round(x0)), int(round(y0))
        for row, line in enumerate(self.art):
            for col, kind in enumerate(line):
                if kind == ".":
                    continue
                for sy in range(self.scale):
                    for sx in range(self.scale):
                        px, py = x0 + col * self.scale + sx, y0 + row * self.scale + sy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            canvas.SetPixel(px, py, *self.colors[kind])


class TinkReveal(FlyByReveal):
    """Tinker Bell bobs across leaving a drifting trail of pixie dust."""

    # '.' empty, W wing, Y glow, G dress.
    art = [
        "WW.WW",
        "WWYWW",
        "..Y..",
        ".GGG.",
        "..G..",
    ]
    colors = {"W": (170, 220, 255), "Y": (255, 245, 170), "G": (60, 220, 90)}
    dust_colors = [(255, 235, 140), (255, 255, 255), (255, 200, 90)]

    def position(self, t):
        p = t / self.duration
        return self.progress_x(t), self.height * 0.45 + math.sin(p * math.pi * 3) * self.height * 0.18

    def spawn(self, x, y):
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w / 2), y + r.uniform(0, self.sprite_w / 2),
                 r.uniform(-0.15, 0.15), r.uniform(0.05, 0.35), r.randint(12, 24), r.choice(self.dust_colors)]
                for _ in range(2 * self.scale)]


class BuzzReveal(FlyByReveal):
    """Buzz Lightyear climbs across, to infinity, on a short rocket-flame trail."""

    # Side view flying right. '.' empty, W suit/wings, G green chest and wing tips,
    # P purple hood, S face, R wing light.
    art = [
        "..GG....",
        "...WWR..",
        "WWWWGWPS",
        "...WWR..",
        "..GG....",
    ]
    colors = {"W": (235, 235, 245), "G": (60, 210, 60), "P": (140, 70, 210), "S": (255, 205, 170), "R": (255, 40, 40)}
    flame_colors = [(255, 240, 150), (255, 170, 30), (255, 90, 20), (230, 40, 20)]

    def position(self, t):
        # A steady climb from low left to high right.
        p = t / self.duration
        return self.progress_x(t), self.height * (0.62 - 0.4 * p) - self.sprite_h / 2

    def spawn(self, x, y):
        r = self.rng
        tail_y = y + self.sprite_h / 2 - 0.5
        return [[x - 1, tail_y + r.uniform(-0.5, 0.5) * self.scale,
                 r.uniform(-0.7, -0.2) * self.scale, r.uniform(-0.05, 0.1), r.randint(12, 20), r.choice(self.flame_colors)]
                for _ in range(4 * self.scale)]


TRANSITIONS = {"wipe": Wipe, "tink": TinkReveal, "buzz": BuzzReveal}


def show_screen(matrix, draw_screen, hold_s, transition="wipe", rng=None):
    """
    Play a screen for hold_s seconds: sweep the previous screen away, reveal this one,
    then let it animate. draw_screen(canvas, t) draws the screen t seconds after the
    reveal finished (t is 0 during the reveal) and returns True while it is still moving.
    """
    prev = _last_screen.get(id(matrix))
    reveal = TRANSITIONS[transition](matrix.width, matrix.height, rng)
    cover_s = COVER_S if prev else 0.0
    last_t = [0.0]

    def frame(canvas, t):
        if t < cover_s:
            # Redraw the previous screen exactly as it was last shown, then sweep it away.
            prev_draw, prev_t = prev
            prev_draw(canvas, prev_t)
            x = int(ease_out(t / cover_s) * (matrix.width + 1))
            _blackout(canvas, 0, x, matrix.height)
            _edge(canvas, x, matrix.width, matrix.height)
            return True
        t_reveal = t - cover_s
        last_t[0] = max(0.0, t_reveal - reveal.duration)
        moving = draw_screen(canvas, last_t[0])
        revealing = reveal.overlay(canvas, t_reveal)
        return bool(moving or revealing)

    run_frames(matrix, frame, hold_s)
    _last_screen[id(matrix)] = (draw_screen, last_t[0])
