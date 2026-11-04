"""Figment."""
import random

import pytest

import display.animation as animation


def test_figment_art_is_uniform_and_every_cell_has_a_colour():
    art = animation.FigmentReveal.art
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.FigmentReveal.colors)


@pytest.mark.parametrize("height", [32, 64])
def test_all_of_figment_fits_at_1x_with_room_to_flutter(height):
    figment = animation.FigmentReveal(64, height, random.Random(0))
    assert figment.scale == 1 and figment.sprite_h <= height - 4


def test_figment_has_his_horns_eyes_grin_wing_and_tail_tuft():
    art = animation.FigmentReveal.art
    cols_with = lambda keys: [c for row in art for c, k in enumerate(row) if k in keys]
    width = len(art[0])
    assert min(cols_with("Y")) > width / 2, "his eyes are up front, on the right"
    assert min(cols_with("T")) > width / 2, "and his grin"
    assert min(cols_with("Oo")) < 3, "the tuft at the end of his tail, far left"
    assert any(set(row) & {"P"} for row in art), "his pink belly"


@pytest.mark.parametrize("height", [32, 64])
def test_figment_moves_a_steady_whole_step_every_frame_and_bobs_gently(height):
    figment = animation.FigmentReveal(64, height, random.Random(1))
    xs = [figment.position(f / animation.FPS)[0] for f in range(int(figment.duration * animation.FPS))]
    steps = {round(b - a, 6) for a, b in zip(xs, xs[1:])}
    assert steps == {float(figment.STEP)}, "the same whole-pixel step every frame"
    ys = [figment.position(f / animation.FPS)[1] for f in range(int(figment.duration * animation.FPS))]
    assert max(ys) - min(ys) <= 2, "a gentle bob, not a hop"
