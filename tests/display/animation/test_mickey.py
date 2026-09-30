"""Sorcerer Mickey."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, FakeMatrix, _striped_screen, fill


def test_mickey_materializes_the_new_screen_out_of_magic_dust():
    mickey = animation.MickeyReveal(64, 32, random.Random(1))
    mickey.capture_new(_striped_screen, 0.0)
    assert len(mickey.new_px) == 64 * 32, "captured every pixel of the incoming screen"
    assert len(mickey.motes) == len(mickey.new_px), "one mote per pixel to summon"
    landed = []
    for t in (mickey.RISE_S, mickey.RISE_S + mickey.CAST_S / 2, mickey.duration - 0.01):
        canvas = FakeCanvas(64, 32)
        mickey.overlay(canvas, t)
        landed.append(sum(1 for rgb in canvas.px.values() if rgb == (200, 100, 50)))
    assert landed == sorted(landed), "more of the screen has settled as the cast goes on"
    assert landed[0] < landed[-1] * 0.2, "almost nothing is there when he starts"
    assert landed[-1] > 64 * 32 * 0.4, "most of the screen has arrived by the end"


def test_mickey_summons_left_to_right_in_the_wake_of_the_wand():
    mickey = animation.MickeyReveal(64, 32, random.Random(2))
    mickey.capture_new(_striped_screen, 0.0)
    left = [m for m in mickey.motes if m[0] < 20]
    right = [m for m in mickey.motes if m[0] > 55]
    assert max(m[4] for m in left) <= min(m[4] for m in right), "the sweep reaches the left first"
    assert mickey._sweep_t(0) == 0.0 and mickey._sweep_t(63) == pytest.approx(1.0, abs=0.05)


def test_mickey_wand_tip_sweeps_across_the_board():
    mickey = animation.MickeyReveal(64, 64, random.Random(3))
    start_x, _ = mickey.wand_tip(mickey.RISE_S)
    end_x, _ = mickey.wand_tip(mickey.RISE_S + mickey.CAST_S)
    assert end_x > start_x >= 0, "the tip travels rightward across the board"
    xs = [mickey.wand_tip(mickey.RISE_S + i / animation.FPS)[0]
          for i in range(int(mickey.CAST_S * animation.FPS))]
    assert xs == sorted(xs), "and never doubles back"
    for f in range(int(mickey.duration * animation.FPS)):
        _, y = mickey.wand_tip(f / animation.FPS)
        assert 0 <= y < mickey.height


def test_mickey_finishes_and_never_draws_off_board():
    for height in (32, 64):
        mickey = animation.MickeyReveal(64, height, random.Random(4))
        mickey.capture_new(_striped_screen, 0.0)
        assert mickey.sprite_h <= height and mickey.sprite_w <= 64, "he fits the board"
        for f in range(int(mickey.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            assert mickey.overlay(canvas, f / animation.FPS) is True
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height
        assert mickey.overlay(FakeCanvas(64, height), mickey.duration) is False


def test_mickey_rises_into_frame_and_then_holds():
    mickey = animation.MickeyReveal(64, 64, random.Random(5))
    assert mickey.mickey_y(0.0) >= mickey.height - 1, "starts below the board"
    settled = mickey.height - mickey.sprite_h
    assert mickey.mickey_y(mickey.RISE_S) == pytest.approx(settled)
    assert mickey.mickey_y(mickey.duration - 0.01) == pytest.approx(settled), "stays for the cast"


def test_mickey_art_rows_are_even_and_use_defined_colors():
    art = animation.MickeyReveal.ART
    assert len({len(row) for row in art}) == 1
    assert {ch for row in art for ch in row} - {"."} == set(animation.MickeyReveal.COLORS)


def test_mickey_opts_into_receiving_the_new_screen():
    assert animation.MickeyReveal.wants_new is True
    assert not getattr(animation.RalphReveal, "wants_new", False)
    assert "mickey" in animation.TRANSITIONS


def test_show_screen_hands_mickey_the_new_screens_pixels():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((120, 30, 200)), animation.MickeyReveal.duration + 0.5,
                          transition="mickey", rng=random.Random(6))
    assert matrix.frames[0].get((63, 5)) in (None, (0, 0, 0)), "far side still unformed at the start"
    assert matrix.frames[-1][(63, 5)] == (120, 30, 200), "screen fully materialized by the end"
