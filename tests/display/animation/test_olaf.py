"""Olaf."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def test_olaf_is_a_registered_visitor_over_the_finished_screen():
    cls = animation.TRANSITIONS["olaf"]
    assert cls is animation.OlafReveal and cls.over_screen
    assert not getattr(cls, "wants_prev", False) and not getattr(cls, "wants_new", False)


@pytest.mark.parametrize("height", [32, 64])
def test_olaf_stays_on_the_board_and_walks_off_by_the_end(height):
    olaf = animation.OlafReveal(64, height, random.Random(1))
    for f in range(int(olaf.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert olaf.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert not any(rgb == olaf.WHITE for rgb in olaf.pixels(olaf.duration - 0.01).values()), "walked off"
    assert olaf.overlay(FakeCanvas(64, height), olaf.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_olaf_stacks_bottom_from_the_left_middle_from_the_right_head_from_the_top(height):
    olaf = animation.OlafReveal(64, height, random.Random(2))
    first = {name: x for name, x, _ in olaf.parts(olaf.BOTTOM[0] + 0.01)}
    assert list(first) == ["bottom"] and first["bottom"] < 0, "the bottom ball rolls in from off the left"
    early = {name: x for name, x, _ in olaf.parts(olaf.MIDDLE[0] + 0.01)}
    assert early["middle"] > 63, "the middle one from off the right"
    head_y = {name: y for name, _, y in olaf.parts(olaf.HEAD[0] + 0.01)}["head"]
    assert head_y + olaf.head[1] <= 0.5, "the head drops in from above the board"
    stacked = olaf.parts(olaf.FACE_S)
    assert [name for name, _, _ in stacked] == ["bottom", "middle", "head"]
    assert all(abs(x - olaf.cx) < 0.5 for _, x, _ in stacked), "stacked up in one column"
    ys = [y for _, _, y in stacked]
    assert ys == sorted(ys, reverse=True), "bottom, then middle on it, then the head on top"


def test_olafs_face_arms_and_hair_pop_on_once_hes_stacked():
    olaf = animation.OlafReveal(64, 64, random.Random(3))
    before = set(olaf.pixels(olaf.FACE_S - 0.05).values())
    after = set(olaf.pixels(olaf.HAIR_S + 0.05).values())
    for part in (olaf.CARROT, olaf.MOUTH, olaf.COAL, olaf.TWIG):
        assert part not in before and part in after


@pytest.mark.parametrize("height", [32, 64])
def test_snow_falls_over_the_whole_board_and_stops_once_he_walks_off(height):
    olaf = animation.OlafReveal(64, height, random.Random(4))
    flakes = set()
    for f in range(int(olaf.WALK[0] * 10)):
        flakes |= set(olaf.snow(f / 10))
    xs, ys = [x for x, _ in flakes], [y for _, y in flakes]
    assert max(xs) - min(xs) > 48 and max(ys) - min(ys) > height * 0.75, "all over the board"
    assert olaf.FLAKE in olaf.pixels(1.0).values()
    during = len(olaf.snow(olaf.WALK[0] - 0.05))
    assert during > 0 and len(olaf.snow(olaf.duration - 0.01)) < during, "no new flakes once he goes"


@pytest.mark.parametrize("height", [32, 64])
def test_olaf_pops_up_onto_his_feet_and_walks_off_stepping(height):
    olaf = animation.OlafReveal(64, height, random.Random(6))
    assert olaf.feet(olaf.FEET[0] - 0.01) == [], "no feet while the bottom ball rolls in"
    rolling = {n: y for n, _, y in olaf.parts(olaf.BOTTOM[1] - 0.01)}["bottom"]
    standing = {n: y for n, _, y in olaf.parts(olaf.FEET[1])}["bottom"]
    assert standing < rolling, "the bottom ball rises onto its feet"
    (lx, ly), (rx, ry) = olaf.feet(olaf.FEET[1])
    assert lx < olaf.cx < rx and ly == ry and ly + olaf.foot[1] <= height + 0.5, "two feet on the ground"
    # Walking: the feet take turns lifting, and he ends up off the right edge.
    lifts = []
    for i in range(1, 20):
        t = olaf.WALK[0] + i * (olaf.WALK[1] - olaf.WALK[0]) / 20
        (_, ly), (_, ry) = olaf.feet(t)
        lifts.append(("left" if ly < ry else "right") if ly != ry else None)
    assert {"left", "right"} <= set(lifts), "each foot steps"
    assert olaf.walk(olaf.WALK[0] - 0.01)[0] == 0.0
    assert olaf.walk(olaf.duration)[0] + olaf.cx - olaf.bottom[0] > 64, "walked off the right edge"


def test_olaf_waves_only_while_he_holds():
    olaf = animation.OlafReveal(64, 64, random.Random(5))
    waves = [olaf.waving(olaf.WAVE[0] + i / 100) for i in range(int((olaf.WAVE[1] - olaf.WAVE[0]) * 100))]
    assert max(waves) > 0.9 and min(waves) < -0.9
    assert olaf.waving(olaf.WAVE[0] - 0.01) == 0.0 and olaf.waving(olaf.WALK[0]) == 0.0
