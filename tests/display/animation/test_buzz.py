"""Buzz Lightyear."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, fill


def test_buzz_launches_from_below_hovers_then_blasts_off_the_top():
    for height in (32, 64):
        buzz = animation.BuzzReveal(64, height, random.Random(4))
        assert buzz.position(0)[1] >= height, "starts below the board"
        hover = buzz.position(buzz.RISE_S + buzz.HOVER_S / 2)[1]
        assert 0 <= hover and hover + buzz.sprite_h <= height, "hovers on the board"
        assert buzz.position(buzz.duration)[1] + buzz.sprite_h <= 0, "gone off the top"
        xs = {buzz.position(f / animation.FPS)[0] for f in range(int(buzz.duration * animation.FPS))}
        assert xs == {(64 - buzz.sprite_w) / 2}, "straight up the middle"
        ys = [buzz.position(buzz.RISE_S + buzz.HOVER_S + f / animation.FPS)[1] for f in range(int(buzz.BLAST_S * animation.FPS))]
        steps = [a - b for a, b in zip(ys, ys[1:])]
        assert steps == sorted(steps), "accelerating as he blasts off"


def test_buzz_uncovers_the_screen_from_the_bottom_up_behind_him():
    buzz = animation.BuzzReveal(64, 64, random.Random(2))
    canvas = FakeCanvas(64, 64)
    t = buzz.RISE_S + buzz.HOVER_S / 2
    fill((9, 9, 9))(canvas, 0)
    buzz.overlay(canvas, t)
    _, y = buzz.position(t)
    feet = int(y + buzz.sprite_h)
    assert canvas.px[(0, 63)] == (9, 9, 9), "below him is revealed"
    assert canvas.px[(0, 0)] == (0, 0, 0), "above him is still dark"
    assert feet < 63


@pytest.mark.parametrize("height", [32, 64])
def test_buzz_finishes_and_his_flame_settles(height):
    buzz = animation.BuzzReveal(64, height, random.Random(1))
    canvas = FakeCanvas(64, height)
    frame = 0
    while buzz.overlay(canvas, frame / animation.FPS):
        frame += 1
        assert frame < 5 * animation.FPS, "reveal never ended"
    assert frame >= buzz.duration * animation.FPS and not buzz.particles


def test_buzz_wings_snap_open_with_a_flash_as_he_hovers():
    buzz = animation.BuzzReveal(64, 32, random.Random(3))

    def drawn(t):
        canvas = FakeCanvas(64, 32)
        buzz._draw_sprite(canvas, t)
        return canvas.px

    before, after = drawn(buzz.RISE_S - 0.05), drawn(buzz.RISE_S + buzz.FLASH_S + 0.05)
    width = lambda px: max(x for x, _ in px) - min(x for x, _ in px)
    assert width(after) > width(before) + 6, "folded, then spread"
    assert buzz.FLASH_RGB in drawn(buzz.RISE_S + 0.02).values(), "a flash at the wing tips as they open"
    assert buzz.FLASH_RGB not in after.values()


def test_buzz_flame_streams_down_from_under_his_feet():
    buzz = animation.BuzzReveal(64, 64, random.Random(4))
    x, y = buzz.position(buzz.RISE_S + buzz.HOVER_S)
    flame = buzz.spawn(x, y)
    assert flame and all(p[1] >= y + buzz.sprite_h - 0.01 and p[3] > 0 for p in flame), "under his feet, falling away"
    assert all(x <= p[0] <= x + buzz.sprite_w for p in flame)
    assert all(p[5] in buzz.flame_colors for p in flame)


def test_buzz_is_big_on_64x32_and_the_small_one_doubled_on_64x64():
    assert (animation.BuzzReveal(64, 32).sprite_w, animation.BuzzReveal(64, 32).sprite_h) == (15, 13)
    assert (animation.BuzzReveal(64, 64).sprite_w, animation.BuzzReveal(64, 64).sprite_h) == (22, 18)


def test_buzz_art_rows_are_even_and_use_defined_colors():
    for art in animation.BuzzReveal.SIZES.values():
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(animation.BuzzReveal.colors)
