"""The fly-by base, shared by Tink, Figment and Dumbo."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FLYBYS, FakeCanvas, fill


@pytest.mark.parametrize("reveal_cls", FLYBYS)
@pytest.mark.parametrize("height", [32, 64])
def test_flyby_finishes_and_its_trail_settles(reveal_cls, height):
    reveal = reveal_cls(64, height, random.Random(1))
    canvas = FakeCanvas(64, height)
    frame = 0
    while reveal.overlay(canvas, frame / animation.FPS):
        frame += 1
        assert frame < 5 * animation.FPS, "reveal never ended"
    assert frame >= reveal.duration * animation.FPS
    assert not reveal.particles


@pytest.mark.parametrize("reveal_cls", FLYBYS)
def test_flyby_reveals_what_is_behind_the_character(reveal_cls):
    reveal = reveal_cls(64, 64, random.Random(2))
    canvas = FakeCanvas(64, 64)
    mid = reveal.duration / 2
    for f in range(int(mid * animation.FPS)):
        canvas.Clear()
        reveal.overlay(canvas, f / animation.FPS)
    canvas.Clear()
    fill((9, 9, 9))(canvas, 0)
    reveal.overlay(canvas, mid)
    assert canvas.px[(0, 0)] == (9, 9, 9), "left of the character is revealed"
    assert canvas.px[(63, 63)] == (0, 0, 0), "right of the character is still dark"


@pytest.mark.parametrize("reveal_cls", FLYBYS)
@pytest.mark.parametrize("height", [32, 64])
def test_flyby_crosses_the_whole_board_and_stays_vertically_on_it(reveal_cls, height):
    reveal = reveal_cls(64, height, random.Random(3))
    start_x, _ = reveal.position(0)
    end_x, _ = reveal.position(reveal.duration)
    assert start_x + reveal.sprite_w <= 0 and end_x >= 64, "enters and leaves off screen"
    for f in range(int(reveal.duration * animation.FPS)):
        _, y = reveal.position(f / animation.FPS)
        assert 0 <= y and y + reveal.sprite_h <= height
