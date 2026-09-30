"""Wreck-It Ralph."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, _striped_screen


def test_ralph_shatters_the_previous_screen_into_falling_debris():
    ralph = animation.RalphReveal(64, 32, random.Random(1))
    ralph.capture_prev(_striped_screen, 0.0)
    assert len(ralph.prev_px) == 64 * 32, "captured every pixel of the old screen"
    canvas = FakeCanvas(64, 32)
    before = ralph.RISE_S + ralph.WIND_S - 0.01
    ralph.overlay(canvas, before)
    assert not ralph.shattered, "screen is still whole until the fists land"
    ralph.overlay(FakeCanvas(64, 32), before + 0.02)
    assert ralph.shattered and ralph.debris


def test_ralph_debris_falls_and_clears_the_board():
    ralph = animation.RalphReveal(64, 32, random.Random(2))
    ralph.capture_prev(_striped_screen, 0.0)
    impact = ralph.RISE_S + ralph.WIND_S
    ralph.overlay(FakeCanvas(64, 32), impact + 0.01)
    early = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    ralph.overlay(FakeCanvas(64, 32), impact + 0.35)
    mid = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    ralph.overlay(FakeCanvas(64, 32), impact + 0.9)
    late = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    assert mid < early, "the blast throws it upward and outward first"
    assert late > mid, "then gravity pulls it back down"
    canvas = FakeCanvas(64, 32)
    ralph.overlay(canvas, ralph.duration - 0.01)
    leftover = [p for p, rgb in canvas.px.items() if rgb == (200, 100, 50)]
    assert len(leftover) < 64 * 32 * 0.25, "most of the old screen has fallen away"


def test_ralph_finishes_and_never_draws_off_board():
    for height in (32, 64):
        ralph = animation.RalphReveal(64, height, random.Random(3))
        ralph.capture_prev(_striped_screen, 0.0)
        for f in range(int(ralph.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            assert ralph.overlay(canvas, f / animation.FPS) is True
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height
        assert ralph.overlay(FakeCanvas(64, height), ralph.duration) is False


def test_ralph_rises_into_frame_then_drops_away():
    ralph = animation.RalphReveal(64, 64, random.Random(4))
    assert ralph.ralph_y(0.0) >= ralph.height - 1, "starts below the board"
    peak = ralph.ralph_y(ralph.RISE_S + ralph.WIND_S / 2)
    assert peak == pytest.approx(ralph.height - ralph.sprite_h)
    assert ralph.ralph_y(ralph.duration - 0.01) > peak, "drops back down at the end"


def test_ralph_opts_into_receiving_the_previous_screen():
    assert animation.RalphReveal.wants_prev is True
    assert not getattr(animation.Wipe, "wants_prev", False)
    assert "ralph" in animation.TRANSITIONS
