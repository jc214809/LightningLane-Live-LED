"""Stitch surfs the new ride in."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def _old_screen(height):
    """Two lines of 3x5 'letters' with a blank column between each, and a bar along the bottom."""
    px = {}
    for line, (top, count, rgb) in enumerate(((2, 5, (255, 255, 255)), (12, 3, (80, 200, 255)))):
        for i in range(count):
            for dx in range(3):
                for dy in range(5):
                    px[(10 + i * 4 + dx, top + dy)] = rgb
    for x in range(40):
        px[(x, height - 1)] = (250, 120, 0)
    px[(20, height - 2)] = (255, 255, 255)  # the forecast tick
    return px


Surf = animation.StitchSurfReveal


def _surfing(height, seed=1):
    surf = Surf(64, height, random.Random(seed))
    surf.capture_prev(lambda canvas, t: [canvas.SetPixel(x, y, *rgb) for (x, y), rgb in _old_screen(height).items()], 0)
    return surf


@pytest.mark.parametrize("height, art", [(32, "SIT_ART"), (64, "STAND_ART")])
def test_each_board_gets_a_surfer_that_fits(height, art):
    surf = Surf(64, height)
    assert surf.art is getattr(Surf, art)
    assert len({len(row) for row in surf.art}) == 1 and set("".join(surf.art)) - {"."} <= set(Surf.colors)
    ride_top = height - round(surf.surface(surf.face * surf.RIDE_AT)) - 2 - surf.art_h - 1
    assert ride_top >= 0, "standing on his board on the wave, his ears stay on the board"


@pytest.mark.parametrize("height", [32, 64])
def test_the_wave_washes_the_old_ride_away_left_to_right(height):
    surf = _surfing(height)
    new_rgb = (1, 2, 3)
    crests = []
    for f in range(int(surf.duration * animation.FPS)):
        t = f / animation.FPS
        canvas = FakeCanvas(64, height)
        for x in range(64):
            for y in range(height):
                canvas.SetPixel(x, y, *new_rgb)
        surf.overlay(canvas, t)
        xc = int(surf.crest_x(t))
        crests.append(xc)
        ahead = [(x, y) for x in range(max(0, xc + 1), 64) for y in range(height)]
        assert all(canvas.px[p] != new_rgb for p in ahead), f"the new ride shows ahead of the wave at t={t:.2f}"
    assert crests == sorted(crests) and crests[0] < 0 and crests[-1] > 64, "it crosses the whole board"


@pytest.mark.parametrize("height", [32, 64])
def test_he_crosses_the_board_and_is_all_there_midway(height):
    surf = _surfing(height)
    canvas = FakeCanvas(64, height)
    assert surf.overlay(canvas, 0.0) is True
    assert surf.colors["E"] not in canvas.px.values(), "he starts off the board"
    seen = False
    for f in range(int(surf.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        surf.overlay(canvas, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
        seen |= list(canvas.px.values()).count(surf.colors["E"]) == "".join(surf.art).count("E")
    assert seen, "both eyes on the board at some point"
    assert surf.overlay(FakeCanvas(64, height), surf.duration) is False


def test_his_board_stands_out_from_the_water_and_from_him():
    def distance(a, b):
        return sum(abs(x - y) for x, y in zip(a, b))
    for water in (Surf.WATER, Surf.FACE, Surf.WATER_DEEP):
        assert distance(Surf.BOARD, water) > 250
    assert min(distance(Surf.BOARD, rgb) for rgb in Surf.colors.values()) > 150, "red against all of his blues and pinks"
    assert distance(Surf.colors["B"], Surf.FACE) > 80, "his fur against the face of the wave he rides"
    assert animation.TRANSITIONS["stitch_surf"] is Surf and Surf.wants_prev


def test_only_the_surfing_scene_is_left():
    assert {name for name in animation.TRANSITIONS if name.startswith("stitch")} == {"stitch_surf"}, \
        "the chomp peek and the screen-eating scene were scrapped"
