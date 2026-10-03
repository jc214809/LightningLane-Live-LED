"""Wreck-It Ralph."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, _striped_screen

Ralph = animation.RalphReveal


def _ralph(height, seed=1):
    ralph = Ralph(64, height, random.Random(seed))
    ralph.capture_prev(_striped_screen, 0.0)
    return ralph


def _distance(a, b):
    return sum(abs(x - y) for x, y in zip(Ralph.COLORS[a], Ralph.COLORS[b]))


@pytest.mark.parametrize("height", [32, 64])
def test_the_old_screen_stays_whole_until_his_fists_land(height):
    ralph = _ralph(height)
    assert len(ralph.prev_px) == 64 * height, "captured every pixel of the old screen"
    ralph.overlay(FakeCanvas(64, height), ralph.impact_at - 0.01)
    assert not ralph.shattered, "still whole while he walks in and winds up"
    ralph.overlay(FakeCanvas(64, height), ralph.impact_at + 0.01)
    assert ralph.shattered and ralph.debris


@pytest.mark.parametrize("height", [32, 64])
def test_the_debris_is_thrown_then_falls_clear_of_the_board(height):
    ralph = _ralph(height, seed=2)
    impact = ralph.impact_at
    ralph.overlay(FakeCanvas(64, height), impact + 0.01)
    early = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    ralph.overlay(FakeCanvas(64, height), impact + 0.3)
    mid = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    assert mid < early, "the slam throws it up and outward first"
    ralph.overlay(FakeCanvas(64, height), ralph.duration - 0.01)
    on_board = [d for d in ralph.debris if 0 <= d[0] < 64 and 0 <= d[1] < height]
    assert len(on_board) < len(ralph.debris) * 0.05, \
        "almost all of it has fallen off by the end, so nothing vanishes at once when he finishes"


@pytest.mark.parametrize("height", [32, 64])
def test_he_walks_in_from_the_left_stops_and_walks_off_the_right(height):
    ralph = _ralph(height)
    assert ralph.ralph_x(0.0) <= -ralph.art_w, "starts off the left side"
    mid = ralph.ralph_x(ralph.WALK_S)
    assert abs(mid + ralph.art_w / 2 - 32) <= 1, "stops in the middle"
    assert ralph.ralph_x(ralph.impact_at) == mid, "and stays put for the slam"
    xs = [ralph.ralph_x(t / 100) for t in range(int(ralph.duration * 100))]
    assert xs == sorted(xs), "always left to right"
    assert ralph.ralph_x(ralph.duration - 0.01) >= 64, "gone off the right by the end"


@pytest.mark.parametrize("height, pose", [(32, "SHOULDER_ART"), (64, "UP_ART")])
def test_his_fists_go_up_before_the_slam(height, pose):
    ralph = _ralph(height)
    assert ralph.raised is getattr(Ralph, pose)
    winding = FakeCanvas(64, height)
    ralph.overlay(winding, ralph.WALK_S + ralph.WIND_S / 2)
    standing = FakeCanvas(64, height)
    _ralph(height).overlay(standing, ralph.WALK_S - 0.01)
    skin = Ralph.COLORS["S"]
    top_skin = lambda canvas: min(y for (x, y), rgb in canvas.px.items() if rgb == skin)
    assert top_skin(winding) <= top_skin(standing), "his fists are up at or above his face"
    if height == 64:
        hair = Ralph.COLORS["H"]
        hair_top = min(y for (x, y), rgb in winding.px.items() if rgb == hair)
        assert top_skin(winding) < hair_top, "on 64x64 they're up over his head"


def test_his_feet_step_while_he_walks():
    ralph = _ralph(32)
    frames = []
    for i in range(6):
        canvas = FakeCanvas(64, 32)
        ralph._draw_ralph(canvas, 0.3 + i / ralph.STEPS_PER_S / 2)
        frames.append(frozenset(canvas.px))
    assert len({f for f in frames}) > 1
    still = set()
    for t in (ralph.WALK_S + ralph.WIND_S + 0.3, ralph.WALK_S + ralph.WIND_S + 0.4):
        canvas = FakeCanvas(64, 32)
        ralph._draw_ralph(canvas, t)
        still.add(frozenset(canvas.px))
    assert len(still) == 1, "standing still after the slam (once the shake is over)"


@pytest.mark.parametrize("height", [32, 64])
def test_he_fits_the_board_and_never_draws_off_it(height):
    ralph = _ralph(height, seed=3)
    for art in (Ralph.STAND_ART, ralph.raised):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(Ralph.COLORS)
    hidden = len(Ralph.STAND_ART) - height
    assert hidden <= 2, "on 64x32 only his outline rows hang off the board"
    for f in range(int(ralph.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert ralph.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert ralph.overlay(FakeCanvas(64, height), ralph.duration) is False


def test_his_face_and_clothes_stand_out():
    assert _distance("W", "S") > 80, "eyes and teeth against his skin"
    assert _distance("H", "S") > 200, "hair against his face"
    assert _distance("R", "D") > 120, "shirt against overalls"
    assert _distance("G", "R") > 100, "the strap across his shirt"
    assert min(Ralph.COLORS["K"]) > 20, "the outline is a lifted charcoal, not black, over the old screen"


def test_ralph_opts_into_receiving_the_previous_screen():
    assert Ralph.wants_prev is True
    assert not getattr(animation.Wipe, "wants_prev", False)
    assert animation.TRANSITIONS["ralph"] is Ralph
