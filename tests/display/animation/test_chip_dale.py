"""Chip 'n' Dale."""
import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill


@pytest.mark.parametrize("attr", ["CHIP_ART", "DALE_ART"])
def test_chip_and_dale_art_is_uniform_and_every_cell_has_a_colour(attr):
    art = getattr(animation.ChipDaleReveal, attr)
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.ChipDaleReveal.colors)


def test_chip_and_dale_are_registered_and_tell_apart_by_their_outfits():
    cls = animation.TRANSITIONS["chip_dale"]
    assert cls is animation.ChipDaleReveal
    chip, dale = "".join(cls.CHIP_ART), "".join(cls.DALE_ART)
    assert "Y" in chip and "R" not in chip, "Chip's fedora"
    assert "R" in dale, "Dale's red nose and Hawaiian shirt"


@pytest.mark.parametrize("height", [32, 64])
def test_they_run_in_from_opposite_sides_meet_in_the_middle_and_run_back(height):
    run = animation.ChipDaleReveal(64, height)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS) + 1)]
    for x_at in (run.chip_x, run.dale_x):
        steps = {abs(round(x_at(b) - x_at(a), 6)) for a, b in zip(frames, frames[1:])}
        assert steps <= {float(run.STEP), 0.0}, "every step steady"
    assert run.chip_x(0) <= -run.chip_w and run.dale_x(0) >= 64, "each starts off his own side"
    meet = run.run_s
    assert run.chip_x(meet) + run.chip_w + run.GAP == run.dale_x(meet), "nose to nose"
    assert abs(run.chip_x(meet) + run.chip_w / 2 + run.dale_x(meet) + run.dale_w / 2 - 64) <= 2, "mid-board"
    assert run.facing(0) == (1, -1) and run.facing(run.duration - 0.01) == (-1, 1)
    assert round(run.chip_x(run.duration)) <= -run.chip_w and round(run.dale_x(run.duration)) >= 64, \
        "each gone off his own side"


def test_they_stand_nose_to_nose_then_turn_round_before_running_off():
    run = animation.ChipDaleReveal(64, 32)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS))]
    standing = [t for t in frames if not run.running(t)]
    assert len(standing) >= (run.MEET_S + run.TURN_S) * animation.FPS - 1
    assert all(run.pose(t) is None and run.hop(t) == 0 for t in standing), "standing still"
    assert run.facing(run.run_s) == (1, -1) and run.facing(run.leave_at) == (-1, 1), "turned round"


def test_chip_and_dale_run_feet_stepping_and_out_of_step_with_each_other():
    run = animation.ChipDaleReveal(64, 32)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS))]
    for art, feet in ((run.CHIP_ART, run.CHIP_FEET), (run.DALE_ART, run.DALE_FEET)):
        poses = {frozenset(animation.walking_pixels(art, 0, 0, run.colors, feet, p)) for p in range(4)}
        assert len(poses) == 4, "every pose of the run moves the feet"
    running = [t for t in frames if run.running(t)]
    assert {run.hop(t) for t in running} == {0, 1}, "a bob in the stride"
    assert any(run.pose(t) % 2 != run.pose(t, 1) % 2 for t in running), "not in lockstep"


@pytest.mark.parametrize("height", [32, 64])
def test_the_ride_is_uncovered_behind_each_and_they_stay_on_the_board(height):
    run = animation.ChipDaleReveal(64, height)
    ride = (0, 140, 0)
    t = run.run_s / 2
    canvas = FakeCanvas(64, height)
    fill(ride)(canvas, t)
    run.overlay(canvas, t)
    assert canvas.px[(0, 0)] == ride and canvas.px[(63, 0)] == ride, "behind each of them"
    assert canvas.px[(32, 0)] == (0, 0, 0), "still dark between them"
    for f in range(int(run.duration * animation.FPS)):
        c = FakeCanvas(64, height)
        fill(ride)(c, f / animation.FPS)
        run.overlay(c, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
        if f / animation.FPS >= run.run_s:
            assert c.px[(32, 0)] == ride, "all of it once they meet"
    assert run.overlay(FakeCanvas(64, height), run.duration) is False
