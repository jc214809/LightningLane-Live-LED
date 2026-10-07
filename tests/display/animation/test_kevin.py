"""Kevin and Dug, and Dug's balloons."""

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


Kevin = animation.KevinReveal
BLUE = Kevin.colors["B"]
GOLD = Kevin.colors["D"]


def _frames(scene):
    return [f / animation.FPS for f in range(int(scene.duration * animation.FPS))]


def _rows(scene, t, rgb):
    return [y for (x, y), c in scene.pixels(t).items() if c == rgb]


def test_kevin_is_a_registered_visitor_over_the_finished_screen():
    assert animation.TRANSITIONS["kevin"] is Kevin and Kevin.over_screen and Kevin.SCALE == 1
    assert not getattr(Kevin, "wants_prev", False) and not getattr(Kevin, "wants_new", False)


def test_art_is_uniform_and_every_cell_has_a_colour():
    for art in (Kevin.KEVIN_ART, Kevin.DUG_ART):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(Kevin.colors)
    assert (len(Kevin.DUG_ART[0]), len(Kevin.DUG_ART)) == (14, 17), "Dug shrunk from the pattern's 22 x 27"


def test_no_black_cells_that_would_show_the_ride_through_them():
    assert all(sum(rgb) >= 90 for rgb in Kevin.colors.values())


@pytest.mark.parametrize("height", [32, 64])
def test_everyone_stays_on_the_board_and_is_gone_by_the_end(height):
    scene = Kevin(64, height)
    for t in _frames(scene):
        canvas = FakeCanvas(64, height)
        assert scene.overlay(canvas, t) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    last = scene.pixels(_frames(scene)[-1])
    assert not [p for p, rgb in last.items() if 0 <= p[0] < 64 and 0 <= p[1] < height], "nobody left on the board"
    assert scene.overlay(FakeCanvas(64, height), scene.duration) is False
    assert scene.duration < 7, "leaves the ride screen time to read"


def test_kevin_fits_64x32_with_her_neck_cut_and_stands_full_size_on_64x64():
    assert len(Kevin(64, 32).kevin_art(False)) == 32
    assert len(Kevin(64, 64).kevin_art(False)) == len(Kevin.KEVIN_ART)


@pytest.mark.parametrize("height", [32, 64])
def test_kevin_struts_straight_across_on_the_ground_without_stopping(height):
    scene = Kevin(64, height)
    xs = [scene.kevin(f)[0] for f in range(scene.frames)]
    assert xs[0] == -scene.kevin_w and xs[-1] >= 64, "in from off the left, off the right"
    assert all(b - a == Kevin.STEP for a, b in zip(xs, xs[1:])), "steady steps, no stop"
    feet = [y for t in _frames(scene) for (x, y), c in scene.pixels(t).items() if c == Kevin.colors["G"]]
    assert max(feet) == height - 1, "her feet on the bottom row"


@pytest.mark.parametrize("height", [32, 64])
def test_dug_chases_behind_her_from_the_ground_rising_as_he_goes_right(height):
    scene = Kevin(64, height)
    spots = [scene.dug(f) for f in range(scene.frames)]
    assert all(x + scene.dug_w < scene.kevin(f)[0] for f, (x, _) in enumerate(spots)), "always behind her"
    on = [(x, y) for x, y in spots if x + scene.dug_w > 0]
    assert on[0][1] >= scene.ground - 1, "on the ground as he comes on"
    assert on[-1][0] >= 64 - 1 and on[-1][1] <= 0, "off the right edge, up high"
    lifts = [y for x, y in on if y < scene.ground - 1]
    assert all(b <= a for a, b in zip(lifts, lifts[1:])), "once off the ground, only ever up"
    assert max(a - b for a, b in zip(lifts, lifts[1:])) <= 2, "slowly"


def test_dug_trots_only_while_his_feet_are_on_the_ground():
    scene = Kevin(64, 64)
    early = {scene.dug(f)[1] for f in range(scene.frames // 3)}
    assert early == {scene.ground, scene.ground - 1}, "bobbing a row as he trots"


def test_her_head_pumps_forward_on_a_lifted_foot():
    scene = Kevin(64, 64)
    flat, pumped = scene.kevin_art(False), scene.kevin_art(True)
    assert pumped[0] == "." + flat[0][:-1] and pumped[-1] == flat[-1]


def test_the_balloons_sway_and_are_strung_to_dug():
    scene = Kevin(64, 64)
    assert {scene.sway(t) for t in _frames(scene)} == {-1, 0, 1}
    px = scene.balloon_pixels(20, 40, 0)
    assert px[(20 + scene.dug_w // 2, 40)] == Kevin.STRING, "the string reaches his head"
    assert len({rgb for rgb in px.values() if rgb in Kevin.BALLOON_RGB}) == len(Kevin.BALLOON_RGB), "every colour"
