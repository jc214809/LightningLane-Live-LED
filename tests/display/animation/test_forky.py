"""Forky."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, _striped_screen

Forky = animation.ForkyReveal


def _forky(height, seed=1):
    forky = Forky(64, height, random.Random(seed))
    forky.capture_prev(_striped_screen, 0.0)
    return forky


def _old_screen_left(canvas):
    return sum(1 for rgb in canvas.px.values() if rgb == (200, 100, 50))


@pytest.mark.parametrize("height", [32, 64])
def test_the_old_screen_stays_whole_until_he_dives_in_then_goes_down_the_hole(height):
    forky = _forky(height)
    whole = FakeCanvas(64, height)
    forky.overlay(whole, forky.suck_at - 0.01)
    assert _old_screen_left(whole) > 64 * height * 0.6, "all there, but for Forky on top of it"
    left = []
    for t in (forky.suck_at + 0.1, forky.suck_at + forky.SUCK_S / 2, forky.duration - 0.01):
        canvas = FakeCanvas(64, height)
        forky.overlay(canvas, t)
        left.append(_old_screen_left(canvas))
    assert left == sorted(left, reverse=True) and left[0] > left[-1]
    assert left[-1] < 64 * height * 0.02, "practically all gone by the end, nothing vanishes at once"


@pytest.mark.parametrize("height", [32, 64])
def test_the_hole_eats_the_old_screen_nearest_first(height):
    forky = _forky(height)
    canvas = FakeCanvas(64, height)
    forky.overlay(canvas, forky.suck_at + forky.SUCK_S * 0.5)
    hx = forky.hole_x
    far = (max(hx, 64 - hx) ** 2 + height ** 2) ** 0.5

    def left_within(lo, hi):
        ring = [(x, y) for x in range(64) for y in range(height) if lo <= ((x - hx) ** 2 + (y - height) ** 2) ** 0.5 < hi]
        return sum(canvas.px.get(p) == (200, 100, 50) for p in ring) / len(ring)
    assert left_within(0, far * 0.2) < 0.5, "round the hole most has gone (his feet and what is still falling in cover some)"
    assert left_within(far * 0.8, far + 1) > 0.9, "the far corners are still there"


@pytest.mark.parametrize("height", [32, 64])
def test_he_waddles_in_from_the_left_and_stops_hops_and_dives_out_the_bottom(height):
    forky = _forky(height)
    assert forky.forky_x(0.0) <= -forky.w, "starts off the left side"
    xs = [forky.forky_x(t / 100) for t in range(int(forky.WALK_S * 100) + 1)]
    assert xs == sorted(xs) and forky.forky_x(forky.WALK_S) == forky.stop_x
    assert forky.forky_y(forky.hop_at) == forky.ground, "feet on the ground until the hop"
    assert forky.forky_y(forky.dive_at - 0.01) < forky.ground, "springs up"
    assert forky.forky_y(forky.suck_at) == height - forky.FEET_OUT * forky.scale, "only his feet left out"
    assert forky.forky_y(forky.duration - 0.001) >= height - forky.scale, "and they slip in too"
    assert not forky.flipped(forky.dive_at - 0.01) and forky.flipped(forky.dive_at), "head first"


@pytest.mark.parametrize("height", [32, 64])
def test_only_his_base_and_feet_stick_out_of_the_hole(height):
    forky = _forky(height)
    px = {(x, y): rgb for (x, y), rgb in forky._forky_px(forky.suck_at + 0.1).items() if y < height}
    assert px and all(y >= height - Forky.FEET_OUT * forky.scale for _, y in px)
    assert Forky.COLORS["R"] not in px.values(), "not the ends of his arms"
    assert Forky.COLORS["F"] in px.values(), "his feet, kicking"


@pytest.mark.parametrize("height", [32, 64])
def test_trash_is_shouted_clear_of_him_and_on_the_board(height):
    forky = _forky(height)
    canvas = FakeCanvas(64, height)
    forky.overlay(canvas, forky.spot_at + 0.3)
    yellow = {p for p, rgb in canvas.px.items() if rgb == Forky.TEXT_RGB}
    assert len(yellow) == len(forky.text), "all of TRASH! on the board"
    body = forky._forky_px(forky.spot_at + 0.3)
    assert not yellow & body.keys()
    canvas = FakeCanvas(64, height)
    forky.overlay(canvas, forky.dive_at + 0.1)
    assert Forky.TEXT_RGB not in canvas.px.values(), "gone once he's diving"


def test_his_googly_eyes_roll_as_he_waddles_and_look_down_at_the_trash():
    forky = _forky(32)
    eyes = set()
    for i in range(8):
        art = forky._art(i * 0.15)
        eyes.add(tuple((r, c) for r, row in enumerate(art) for c, k in enumerate(row) if k == "P"))
    assert len(eyes) > 1, "the pupils move"
    art = forky._art(forky.hop_at - 0.05)
    for col, row, size in Forky.EYES:
        pupil = [r for r in range(row, row + size) for c in range(col, col + size) if art[r][c] == "P"]
        assert pupil and min(pupil) > row, "looking down"
        ring = [1 for r in range(row, row + size) for c in range(col, col + size) if art[r][c] == "G"]
        assert ring, "a grey ring round the pupil, so the eye doesn't vanish into his white head"


def test_his_arms_flap_as_he_shouts():
    forky = _forky(32)
    shapes = {tuple(forky._art(forky.spot_at + i / 16)) for i in range(4)}
    assert len(shapes) > 1


@pytest.mark.parametrize("height", [32, 64])
def test_he_fits_the_board_and_never_draws_off_it(height):
    forky = _forky(height, seed=3)
    assert len({len(row) for row in Forky.ART}) == 1
    assert set("".join(Forky.ART)) - {"."} <= set(Forky.COLORS) | {"E"}
    assert forky.ground >= 0, "all of him on the board: 1x on 64x32, 2x on 64x64"
    assert forky.scale == (2 if height == 64 else 1)
    for f in range(int(forky.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert forky.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert forky.overlay(FakeCanvas(64, height), forky.duration) is False


def test_forky_opts_into_receiving_the_previous_screen():
    assert Forky.wants_prev is True
    assert animation.TRANSITIONS["forky"] is Forky


def test_forky_is_a_rare_surprise_anywhere():
    import disney
    assert 0 < disney.SURPRISES["forky"] <= 0.005
