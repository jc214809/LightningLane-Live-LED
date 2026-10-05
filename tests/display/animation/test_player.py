"""show_screen, the frame loop and the shared canvas."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeMatrix, fill


def test_run_frames_stops_redrawing_once_static_and_sleeps_out_the_rest(clock):
    matrix = FakeMatrix()
    calls = []
    animation.run_frames(matrix, lambda canvas, t: calls.append(t) or len(calls) < 5, duration_s=8)
    assert len(calls) == 5 == len(matrix.frames)
    assert clock.now == pytest.approx(8)


def test_run_frames_reports_frames_drawn_and_time_spent_animating(clock):
    calls = []
    drawn, spent = animation.run_frames(FakeMatrix(), lambda canvas, t: calls.append(t) or len(calls) < 30, duration_s=8)
    assert drawn == 30 and drawn / spent == pytest.approx(animation.FPS), "a board that keeps up reports 30 fps"

    def slow(canvas, t):
        clock.now += 0.1
        return True

    drawn, spent = animation.run_frames(FakeMatrix(), slow, duration_s=2)
    assert drawn / spent == pytest.approx(10, rel=0.1), "a board three times too slow reports ~10 fps"


def test_character_transitions_log_their_frame_rate(clock, monkeypatch):
    logged = []
    monkeypatch.setattr(animation.debug, "info", logged.append)
    animation.show_screen(FakeMatrix(), fill((1, 2, 3)), 1.0, transition="baymax", rng=random.Random(0))
    animation.show_screen(FakeMatrix(), fill((1, 2, 3)), 1.0, transition="wipe")
    assert len(logged) == 1 and logged[0].startswith("baymax: 30 fps"), "only characters log, not every wipe"


def test_slow_frames_do_not_stretch_the_screen(clock):
    matrix = FakeMatrix()

    def slow(canvas, t):
        clock.now += 0.1  # each frame takes 3x its budget
        return True

    animation.run_frames(matrix, slow, duration_s=8)
    assert clock.now == pytest.approx(8, abs=0.11)


def test_a_slow_board_plays_the_reveal_in_full_then_gets_the_rest_of_the_screen(clock):
    seen = []

    def slow(canvas, t):
        seen.append(t)
        clock.now += 0.1  # each frame takes 3x its budget
        return True

    animation.run_frames(FakeMatrix(), slow, duration_s=8, play_s=6)
    assert max(seen) >= 6, "the whole reveal played, though it took three times as long"
    assert clock.now == pytest.approx(3 * 6 + 2, abs=0.11), "then the 2s after it, by the clock"


def test_canvas_is_created_once_and_reused_across_screens():
    matrix = FakeMatrix()
    for _ in range(3):
        animation.show_screen(matrix, fill((255, 0, 0)), 1)
    assert matrix.canvases_created == 1


def test_network_badge_is_drawn_over_every_frame_while_offline():
    from updater.shared import note_network_result
    note_network_result(False)
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((0, 0, 255)), 1)
    assert all(frame[(63, 31)] == (255, 0, 0) for frame in matrix.frames), "badge over the wipe and the screen"
    assert matrix.frames[-1][(56, 31)] == (0, 0, 255), "screen untouched outside the badge"


def test_first_screen_wipes_in_from_black():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((255, 0, 0)), 2)
    first = matrix.frames[0]
    assert all(first.get((x, 5)) in (None, (0, 0, 0)) for x in range(10, 64)), "right side still dark"
    assert matrix.frames[-1][(63, 5)] == (255, 0, 0)
    assert all(rgb != animation.EDGE_RGB for rgb in matrix.frames[-1].values()), "edge gone once revealed"


def test_next_screen_first_sweeps_the_previous_one_away():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((255, 0, 0)), 1)
    matrix.frames.clear()
    animation.show_screen(matrix, fill((0, 0, 255)), 2)
    first = matrix.frames[0]
    assert first[(60, 5)] == (255, 0, 0), "old screen still visible ahead of the sweep"
    assert matrix.frames[-1][(60, 5)] == (0, 0, 255)


def test_previous_screen_is_swept_away_as_it_was_last_shown():
    matrix = FakeMatrix()
    drawn_at = []

    def pulsing(canvas, t):
        drawn_at.append(t)
        return True

    animation.show_screen(matrix, pulsing, 1)
    last_shown = drawn_at[-1]
    drawn_at.clear()
    animation.show_screen(matrix, fill((0, 0, 255)), 1)
    assert drawn_at and set(drawn_at) == {last_shown}, "redrawn at a real, finite time"


def test_forget_screen_skips_the_sweep():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((255, 0, 0)), 1)
    animation.forget_screen(matrix)
    matrix.frames.clear()
    animation.show_screen(matrix, fill((0, 0, 255)), 2)
    assert (255, 0, 0) not in matrix.frames[0].values()


def test_screen_time_starts_after_the_reveal():
    matrix = FakeMatrix()
    seen = []
    animation.show_screen(matrix, lambda canvas, t: seen.append(t) or t < 0.5, 2)
    reveal_frames = int(animation.WIPE_S * animation.FPS)
    assert seen[:reveal_frames] == [0.0] * reveal_frames
    assert seen[reveal_frames + 3] > 0


def test_surprises_let_the_screen_underneath_keep_animating():
    def times(transition):
        seen = []
        matrix = FakeMatrix()
        # A new matrix can reuse a collected one's id() and inherit its last screen.
        animation.forget_screen(matrix)
        animation.show_screen(matrix, lambda canvas, t: seen.append(t) or True, 0.5,
                              transition=transition, rng=random.Random(0))
        return seen
    assert max(times("baymax")) > 0.3, "under a surprise the ride screen plays on"
    assert max(times("wipe")) == 0, "a reveal still holds it at its first frame"


def _half_lit_screen(canvas, t):
    """An old screen lit only on its left half: its dark right half must stay dark."""
    for y in range(canvas.height):
        for x in range(canvas.width // 2):
            canvas.SetPixel(x, y, 200, 100, 50)
    return False


@pytest.mark.parametrize("transition,t", [("army_men", 0.3), ("falcon", 1.2), ("ralph", 0.3), ("pooh", 1.0)])
def test_new_screen_never_shows_through_the_old_screens_dark_pixels(transition, t):
    # show_screen draws the new screen first and the transition paints over it, so a
    # transition that draws only the old screen's lit pixels lets the new one bleed through.
    matrix = FakeMatrix()
    animation.show_screen(matrix, _half_lit_screen, 0.05)
    matrix.frames.clear()
    new = (1, 2, 3)
    animation.show_screen(matrix, fill(new), t + 0.1, transition=transition, rng=random.Random(1))
    frame = matrix.frames[int(t * animation.FPS)]
    low = [(x, y) for (x, y), rgb in frame.items() if rgb == new and x >= 40 and y >= 26]
    assert not low, "the new screen leaked into the old screen's dark half"


@pytest.mark.parametrize("plays_under", [False, True])
def test_a_screen_can_ask_to_keep_playing_while_the_wipe_uncovers_it(plays_under):
    seen = []

    def screen(canvas, t):
        seen.append(t)
        return True
    if plays_under:
        screen.plays_under_reveal = True
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((1, 2, 3)), 0.1)  # something for the sweep to cover
    seen.clear()
    animation.show_screen(matrix, screen, animation.COVER_S + animation.WIPE_S + 0.2)
    # The screen isn't drawn during the sweep, so its first frames are the wipe's.
    during_wipe = [t for t in seen[:int(animation.WIPE_S * animation.FPS) - 1] if t > 0]
    if plays_under:
        assert during_wipe, "its clock runs from the start of the wipe"
    else:
        assert not during_wipe, "held at its first frame until it's uncovered"


def test_a_reveal_longer_than_the_screen_keeps_the_screen_up_after_it(monkeypatch):
    holds = []
    monkeypatch.setattr(animation.player, "run_frames", lambda matrix, frame, hold_s, play_s: holds.append(hold_s) or (0, 0))
    animation.show_screen(FakeMatrix(), fill((1, 2, 3)), 8, transition="mine_train_snow", rng=random.Random(0))
    train = animation.MineTrainSnowReveal(64, 32, random.Random(0))
    assert holds[-1] >= train.duration + train.hold_after_s
    animation.show_screen(FakeMatrix(), fill((1, 2, 3)), 8, transition="mater")
    assert holds[-1] == 8, "a reveal that doesn't ask keeps the usual hold"
