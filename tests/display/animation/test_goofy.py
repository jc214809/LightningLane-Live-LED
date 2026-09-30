"""Goofy and his biplane."""

import math
import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def test_goofy_is_registered_and_his_banner_says_yahooey():
    assert animation.TRANSITIONS["goofy"] is animation.GoofyReveal
    banner = animation.GoofyReveal.BANNER_ART
    assert len({len(row) for row in banner}) == 1 and len(banner) == 7, "one cloth rectangle, 5 rows of text"
    assert all(row.startswith("Q") and row.endswith("Q") for row in banner)


def test_goofys_plane_turns_in_exact_quarter_steps():
    goofy = animation.GoofyReveal(64, 32, random.Random(1))
    level, climbing, upside_down, diving = goofy.poses
    assert upside_down == [row[::-1] for row in level[::-1]], "over the top of the loop he's upside down"
    assert len(climbing) == len(level[0]) and len(climbing[0]) == len(level)
    assert animation._rotate_art(level, 4) == level


@pytest.mark.parametrize("height", [32, 64])
def test_goofy_loops_the_loop_out_the_top_of_64x32(height):
    goofy = animation.GoofyReveal(64, height, random.Random(2))
    path = [goofy.point(d / 2) for d in range(int(goofy.length * 2))]
    assert any(a > 3 for _, _, a in path) and max(a for _, _, a in path) < 2 * math.pi, "one full loop"
    top = min(y for _, y, _ in path)
    if height == 32:
        assert top - goofy.sprite_h / 2 < 0, "on 64x32 the loop goes out the top of the board"
    xs = [x for x, _, _ in path]
    assert xs[0] < 0 and xs[-1] > 64 + goofy.banner_w, "in from the left, off the right with his banner"


@pytest.mark.parametrize("height", [32, 64])
def test_goofy_uncovers_the_new_ride_behind_his_banner_and_never_covers_it_back(height):
    goofy = animation.GoofyReveal(64, height, random.Random(3))
    edges = [goofy.reveal_x(f / animation.FPS) for f in range(int(goofy.duration * animation.FPS))]
    assert edges == sorted(edges), "the reveal only moves right, even while he loops back"
    assert edges[0] < 0 and edges[-1] >= 63, "starts hidden, ends fully uncovered"
    for f in range(int(goofy.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        goofy.overlay(canvas, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert goofy.overlay(FakeCanvas(64, height), goofy.duration) is False
