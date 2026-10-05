"""
Playing a screen: the shared canvas, the frame loop, and show_screen, which sweeps the
previous screen away and reveals the next with a transition from TRANSITIONS.
"""

import time

from display.network import draw_if_offline
from utils import debug

from display.animation.characters import TRANSITIONS
from display.animation.drawing import _blackout, _edge
from display.animation.motion import COVER_S, FPS, ease_out


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
    # Every frame on the board passes through here, so the badge sits on top of all of them.
    draw_if_offline(canvas)
    _canvases[id(matrix)] = matrix.SwapOnVSync(canvas)
    return _canvases[id(matrix)]


def forget_screen(matrix):
    """The next screen should reveal from black rather than cover whatever played last."""
    _last_screen.pop(id(matrix), None)


def run_frames(matrix, draw_frame, duration_s, fps=FPS, play_s=0.0):
    """
    Call draw_frame(canvas, t) each frame for duration_s; once it returns False the image
    is static and we sleep out the rest. The first play_s seconds of t always play in full:
    a board too slow to keep up with them gets the time it lost added on after them. Returns
    (frames drawn, seconds spent animating) so callers can see how close a board gets to `fps`.
    """
    frame_time = 1.0 / fps
    canvas = frame_canvas(matrix)
    began = time.monotonic()
    drawn = 0
    behind = 0.0  # how far a slow board fell behind during play_s

    def animated_s():
        # A board that keeps up spends a whole frame slot on its last frame too.
        return max(time.monotonic() - began, drawn * frame_time)

    i = 0
    while i < int((duration_s + behind) * fps):
        start = time.monotonic()
        if i / fps < play_s:
            behind = max(behind, start - began - i / fps)
        # A slow board drops frames rather than stretching the screen past duration_s.
        elif start - began >= duration_s + behind:
            return drawn, animated_s()
        canvas.Clear()
        animating = draw_frame(canvas, i / fps)
        canvas = present(matrix, canvas)
        drawn += 1
        i += 1
        if not animating:
            spent = animated_s()
            time.sleep(max(0.0, duration_s + behind - (time.monotonic() - began)))
            return drawn, spent
        remaining = frame_time - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)
    return drawn, animated_s()


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
    # A reveal longer than the screen (the full Mine Train) asks for the screen to stay up this long after it.
    after_s = getattr(reveal, "hold_after_s", None)
    if after_s is not None:
        hold_s = max(hold_s, cover_s + reveal.duration + after_s)

    # A reveal that shatters the old screen needs its pixels; hand it the previous
    # draw function and let it keep the sweep from running.
    if getattr(reveal, "wants_prev", False) and prev:
        reveal.capture_prev(*prev)
        cover_s = 0.0

    # A reveal that materializes the new screen needs its pixels up front; it draws
    # them itself (over a blackout) instead of uncovering what draw_screen painted.
    if getattr(reveal, "wants_new", False):
        reveal.capture_new(draw_screen, 0.0)

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
        # A surprise that plays over a finished screen lets it keep animating underneath, and
        # so does a screen that asks to (plays_under_reveal: the Halloween pumpkin lights up as
        # it's uncovered); otherwise a reveal holds the screen at its first frame until it's
        # been uncovered.
        over = getattr(reveal, "over_screen", False) or getattr(draw_screen, "plays_under_reveal", False)
        last_t[0] = t_reveal if over else max(0.0, t_reveal - reveal.duration)
        moving = draw_screen(canvas, last_t[0])
        revealing = reveal.overlay(canvas, t_reveal)
        return bool(moving or revealing)

    # A slow board plays frames in slow motion; one that asks for the screen after it is never cut short.
    play_s = cover_s + reveal.duration if after_s is not None else 0.0
    drawn, spent = run_frames(matrix, frame, hold_s, play_s=play_s)
    _last_screen[id(matrix)] = (draw_screen, last_t[0])
    if transition != "wipe" and spent > 0:
        # A readout for checking characters on real boards: journalctl shows how close each gets.
        debug.info(f"{transition}: {drawn / spent:.0f} fps over {spent:.1f}s of animation (target {FPS})")
