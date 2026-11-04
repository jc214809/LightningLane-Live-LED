"""Baymax."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FLYBYS, FakeCanvas, FakeMatrix, fill


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_finishes_within_his_duration(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(1))
    canvas = FakeCanvas(64, height)
    assert baymax.overlay(canvas, baymax.duration - 0.01) is True
    assert baymax.overlay(FakeCanvas(64, height), baymax.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_never_draws_outside_the_board(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(2))
    for f in range(int(baymax.duration * animation.FPS) + 1):
        canvas = FakeCanvas(64, height)
        baymax.overlay(canvas, f / animation.FPS)
        for x, y in canvas.px:
            assert 0 <= x < 64 and 0 <= y < height


def _baymax_span(reveal, height, t):
    """Width and height in pixels of everything Baymax draws at time t."""
    canvas = FakeCanvas(64, height)
    reveal.overlay(canvas, t)
    if not canvas.px:
        return 0, 0
    xs = [x for x, _ in canvas.px]
    ys = [y for _, y in canvas.px]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_inflates_then_deflates_away(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(3))
    sizes = [_baymax_span(baymax, height, t) for t in (0.05, 0.3, 0.6, baymax.INFLATE_S)]
    heights = [h for _, h in sizes]
    assert heights == sorted(heights), "grows steadily while inflating"
    assert heights[0] * 3 < heights[-1], "starts as a flat puddle, ends full size"
    assert sizes[0][0] > sizes[0][1], "a deflated Baymax is wider than he is tall"
    full_w, full_h = sizes[-1]
    late_w, late_h = _baymax_span(baymax, height, baymax.duration - 0.3)
    assert late_h < full_h and late_w < full_w, "shrinks again as the air goes out"
    assert _baymax_span(baymax, height, baymax.duration - 0.01) == (0, 0), "gone by the end"


def test_baymax_inflation_curve_peaks_at_full_size_and_returns_to_nothing():
    baymax = animation.BaymaxReveal(64, 64, random.Random(4))
    inflations = [baymax.inflation(t / 100) for t in range(int(baymax.duration * 100))]
    assert inflations[0] < 0.15, "starts deflated"
    assert max(inflations) == pytest.approx(1.0, abs=0.12), "settles at full size, give or take the wobble"
    assert inflations[-1] < 0.05, "back to nothing by the end"
    rising = inflations[: int(baymax.INFLATE_S * 100)]
    assert rising == sorted(rising), "fills monotonically"
    falling = inflations[-int(baymax.DEFLATE_S * 100):]
    assert falling == sorted(falling, reverse=True), "empties monotonically"


def test_baymax_wobbles_as_he_settles():
    baymax = animation.BaymaxReveal(64, 64, random.Random(5))
    settling = [baymax.inflation(baymax.INFLATE_S + i / 100) for i in range(60)]
    assert max(settling) > 1.0 and min(settling) < 1.0, "overshoots and springs back"


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_has_two_eyes_joined_by_a_line_once_inflated(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(6))
    canvas = FakeCanvas(64, height)
    baymax.overlay(canvas, baymax.INFLATE_S + 0.05)
    dark = {(x, y) for (x, y), rgb in canvas.px.items() if rgb == baymax.DARK}
    assert dark, "the face is drawn"
    rows = {y for _, y in dark}
    line_y = max(rows, key=lambda y: len([1 for x, yy in dark if yy == y]))
    line = sorted(x for x, y in dark if y == line_y)
    assert line == list(range(line[0], line[-1] + 1)), "the eyes are joined by a solid line"
    # Above the line the dark pixels fall into exactly two separate eyes.
    above = sorted(x for x, y in dark if y == line_y - 1)
    groups = []
    for x in above:
        if groups and x - groups[-1][-1] == 1:
            groups[-1].append(x)
        else:
            groups.append([x])
    assert len(groups) == 2, "two eyes, with white between them"
    assert abs((groups[0][0] + groups[0][-1]) / 2 + (groups[1][0] + groups[1][-1]) / 2 - 2 * baymax.cx) <= 1.5, \
        "the eyes sit symmetrically about his centre"


def test_baymax_blinks_and_waves_while_he_holds():
    baymax = animation.BaymaxReveal(64, 64, random.Random(7))
    opens = [baymax.eye_open(baymax.INFLATE_S + i / 100) for i in range(int(baymax.HOLD_S * 100))]
    assert min(opens) < 0.15 and max(opens) == pytest.approx(1.0), "eyes close and reopen"
    assert baymax.eye_open(0.0) == 1.0, "no blink while he is still filling"
    waves = [baymax.wave(baymax.INFLATE_S + i / 100) for i in range(int(baymax.HOLD_S * 100))]
    assert max(waves) > 0.5 and min(waves) < -0.5, "the arm swings both ways"
    assert baymax.wave(baymax.duration - 0.01) == 0.0, "arm is back down before he deflates"


def test_baymax_is_big_on_both_boards():
    for height in (32, 64):
        baymax = animation.BaymaxReveal(64, height, random.Random(8))
        w, h = _baymax_span(baymax, height, baymax.INFLATE_S)
        assert h >= height * 0.75, "he fills most of the board's height"
        assert w >= 18, "and is genuinely wide"


def test_baymax_leaves_the_rest_of_the_new_screen_visible():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((0, 140, 200)), animation.BaymaxReveal.duration + 0.5,
                          transition="baymax", rng=random.Random(9))
    assert matrix.frames[0][(0, 0)] == (0, 140, 200), "no blackout: he pops up over the new screen"
    assert matrix.frames[-1][(32, 31)] == (0, 140, 200), "and he is gone by the end"


def test_baymax_is_registered_and_is_not_a_flyby():
    assert animation.TRANSITIONS["baymax"] is animation.BaymaxReveal
    assert animation.BaymaxReveal not in FLYBYS
    assert not getattr(animation.BaymaxReveal, "wants_prev", False)
