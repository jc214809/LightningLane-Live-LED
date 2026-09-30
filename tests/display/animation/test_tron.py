"""The TRON light cycles."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def test_tron_is_a_registered_flyby():
    assert animation.TRANSITIONS["tron"] is animation.TronReveal
    assert issubclass(animation.TronReveal, animation.FlyByReveal)


def _tron_frame(tron, height, t, new=(0, 140, 0)):
    canvas = FakeCanvas(64, height)
    for x in range(64):
        for y in range(height):
            canvas.SetPixel(x, y, *new)
    more = tron.overlay(canvas, t)
    return canvas.px, more


@pytest.mark.parametrize("height", [32, 64])
def test_tron_races_blue_on_top_and_red_along_the_bottom(height):
    tron = animation.TronReveal(64, height, random.Random(1))
    (blue, bx, by), (red, rx, ry) = tron.bikes(tron.CROSS_S / 2)
    assert (blue, red) == ("blue", "red")
    assert by == 0 and ry == height - tron.sprite_h, "blue across the top, red along the bottom"
    assert rx < bx, "red is behind mid-race"
    assert tron.bikes(0)[0][1] - tron.bikes(0)[1][1] == tron.RED_LAG
    assert tron.bikes(tron.CROSS_S)[1][1] == tron.bikes(tron.CROSS_S)[0][1] >= 64, "level and gone by the end"
    px, _ = _tron_frame(tron, height, tron.CROSS_S / 2)
    colors = set(px.values())
    assert tron.BLUE["C"] in colors and tron.RED["C"] in colors, "both bikes drawn"
    assert tron.TRAILS["blue"][0] in colors and tron.TRAILS["red"][0] in colors, "and both trails"


@pytest.mark.parametrize("height", [32, 64])
def test_tron_uncovers_the_new_screen_behind_the_bikes_and_the_trails_derez(height):
    tron = animation.TronReveal(64, height, random.Random(1))
    new = (0, 140, 0)
    trails = {rgb for pair in tron.TRAILS.values() for rgb in pair}
    px, _ = _tron_frame(tron, height, tron.CROSS_S / 2)
    assert px[(0, height // 2)] == new, "behind the bikes, the new ride"
    assert px[(63, height // 2)] == (0, 0, 0), "ahead of them, not yet"

    px, _ = _tron_frame(tron, height, tron.CROSS_S + tron.HOLD_S / 2)
    held = [rgb for rgb in px.values() if rgb != new]
    assert held and set(held) <= trails, "the bikes are gone, the trails hold"
    px, _ = _tron_frame(tron, height, tron.CROSS_S + tron.HOLD_S + tron.FADE_S / 2)
    left = [rgb for rgb in px.values() if rgb != new]
    assert 0 < len(left) < len(held), "the trails drop out pixel by pixel"
    assert set(left) <= trails, "whole pixels, never dimmed over the screen"
    px, more = _tron_frame(tron, height, tron.duration)
    assert not more and set(px.values()) == {new}, "all gone at the end"
