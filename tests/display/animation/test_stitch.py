"""Stitch."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FLYBYS, FakeCanvas


def test_stitch_starts_and_ends_fully_hidden_below_the_board():
    stitch = animation.StitchReveal(64, 32, random.Random(1))
    canvas = FakeCanvas(64, 32)
    stitch.overlay(canvas, 0.0)
    assert not canvas.px, "nothing drawn at rise=0"
    canvas.Clear()
    stitch.overlay(canvas, stitch.duration - 0.001)
    ys_near_end = set(y for _, y in canvas.px)
    canvas.Clear()
    stitch.overlay(canvas, stitch.UP_S + stitch.HOLD_S)
    ys_at_peak = set(y for _, y in canvas.px)
    assert ys_at_peak, "something visible at the peak of the rise"
    assert max(ys_near_end, default=32) >= max(ys_at_peak) if ys_near_end else True


def test_stitch_rises_then_holds_then_descends():
    stitch = animation.StitchReveal(64, 64, random.Random(2))
    rises = [stitch.rise(t / 100) for t in range(int(stitch.duration * 100))]
    peak = max(rises)
    assert peak == pytest.approx(1.0, abs=0.01)
    up_phase = rises[: int(stitch.UP_S * 100)]
    assert up_phase == sorted(up_phase), "rises monotonically at first"
    down_phase = rises[-int(stitch.UP_S * 100):]
    assert down_phase == sorted(down_phase, reverse=True), "descends monotonically at the end"
    assert rises[0] == pytest.approx(0.0, abs=0.01)
    assert rises[-1] < 0.05, "back down by the end"


def test_stitch_never_draws_outside_the_board():
    for height in (32, 64):
        stitch = animation.StitchReveal(64, height, random.Random(3))
        for f in range(int(stitch.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            stitch.overlay(canvas, f / animation.FPS)
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height


def test_stitch_looks_left_then_right_while_settled():
    stitch = animation.StitchReveal(64, 64, random.Random(4))
    frames = [stitch.look_frame(stitch.UP_S + i * 0.1) for i in range(int(stitch.LOOK_S * 2 / 0.1) + 2)]
    assert 0 in frames and 1 in frames, "alternates between both poses"
    assert stitch.look_frame(0.0) == 0, "still looking forward/left while rising"


def test_stitch_finishes_and_is_excluded_from_flyby_tests():
    stitch = animation.StitchReveal(64, 32, random.Random(5))
    canvas = FakeCanvas(64, 32)
    assert stitch.overlay(canvas, stitch.duration) is False
    assert "stitch" in animation.TRANSITIONS
    assert animation.StitchReveal not in FLYBYS, "peek reveals aren't fly-bys"
