"""Chip 'n' Dale."""
import random

import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill


@pytest.fixture
def meet(monkeypatch):
    monkeypatch.setattr(animation.ChipDaleReveal, "STORY", "meet")


@pytest.mark.parametrize("attr", ["CHIP_ART", "DALE_ART", "CHIP_HANG_ART", "DALE_HANG_ART"])
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
def test_they_run_in_from_opposite_sides_meet_in_the_middle_and_run_back(meet, height):
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


def test_they_stand_nose_to_nose_then_turn_round_before_running_off(meet):
    run = animation.ChipDaleReveal(64, 32)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS))]
    standing = [t for t in frames if not run.running(t)]
    assert len(standing) >= (run.MEET_S + run.TURN_S) * animation.FPS - 1
    assert all(run.pose(t) is None and run.hop(t) == 0 for t in standing), "standing still"
    assert run.facing(run.run_s) == (1, -1) and run.facing(run.leave_at) == (-1, 1), "turned round"


def test_chip_and_dale_run_feet_stepping_and_out_of_step_with_each_other(meet):
    run = animation.ChipDaleReveal(64, 32)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS))]
    for art, feet in ((run.CHIP_ART, run.CHIP_FEET), (run.DALE_ART, run.DALE_FEET)):
        poses = {frozenset(animation.walking_pixels(art, 0, 0, run.colors, feet, p)) for p in range(4)}
        assert len(poses) == 4, "every pose of the run moves the feet"
    running = [t for t in frames if run.running(t)]
    assert {run.hop(t) for t in running} == {0, 1}, "a bob in the stride"
    assert any(run.pose(t) % 2 != run.pose(t, 1) % 2 for t in running), "not in lockstep"


@pytest.mark.parametrize("height", [32, 64])
def test_the_ride_is_uncovered_behind_each_and_they_stay_on_the_board(meet, height):
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


def test_each_visit_picks_a_story_and_the_swing_can_be_forced():
    stories = {animation.ChipDaleReveal(64, 32, random.Random(seed)).story for seed in range(40)}
    assert stories == {"meet", "swing"}
    assert animation.TRANSITIONS["chip_dale_swing"] is animation.ChipDaleSwingReveal
    assert animation.ChipDaleSwingReveal(64, 32).story == "swing"


@pytest.mark.parametrize("stand, hang", [("CHIP_ART", "CHIP_HANG_ART"), ("DALE_ART", "DALE_HANG_ART")])
def test_hanging_lifts_one_short_arm_to_beside_the_head(stand, hang):
    cls = animation.ChipDaleReveal
    stand, hang = getattr(cls, stand), getattr(cls, hang)
    assert len(hang) == len(stand) and len(hang[0]) == len(stand[0])
    hx, hy = cls.HAND
    assert hang[hy + 1][hx:hx + 2] == "CC", "the hand the rope meets"
    assert all(row[:hx + 2].strip(".") == "" for row in hang[:hy]), "not above the head"
    assert all("C" not in row[:5] for row in hang[hy + 2:]), "the arm by his side is gone"
    assert hang[-5:] == stand[-5:], "legs and feet untouched"


@pytest.mark.parametrize("height", [32, 64])
def test_chip_swings_in_skids_and_dale_bonks_into_his_back(height):
    run = animation.ChipDaleSwingReveal(64, height)
    x, _, hanging = run.swing_place("chip", 0)
    assert hanging and -run.chip_w < round(x) <= -run.chip_w + run.PEEK, "just coming in at the left"
    assert run.swing_place("dale", run.dale_grab - 0.01) is None, "Dale waits his turn off the board"
    x, y, hanging = run.swing_place("chip", run.chip_lets_go)
    assert not hanging and y == run.chip_floor and round(x) == run.bottom_x, "lets go at the bottom"
    assert round(run.swing_place("chip", run.bonk_at - 0.01)[0]) == run.chip_rest, "skidded to a stop"
    dale_x, dale_y, hanging = run.swing_place("dale", run.bonk_at - 1e-6)
    assert hanging and dale_y > run.dale_floor - 2
    assert round(dale_x) + run.dale_w - 1 >= run.chip_rest + run.NOSE_IN, "nose in Chip's back"
    lurch = run.swing_place("chip", run.bonk_at + run.BONK_S / 2)
    assert lurch[0] > run.chip_rest and lurch[1] < run.chip_floor, "Chip knocked forward and up"
    assert run.wobble(run.run_at - 0.1) != 0 and run.wobble(run.run_at) == 0
    assert run.swing_place("chip", run.duration)[0] >= 64 and run.swing_place("dale", run.duration)[0] >= 64


def test_each_rope_swings_on_with_him_and_off_after_he_lets_go():
    run = animation.ChipDaleSwingReveal(64, 32)
    assert run.rope_angle(0, run.chip_grab) == pytest.approx(-run.swing_angle)
    assert run.rope_angle(run.chip_lets_go, run.chip_grab) == pytest.approx(0)
    assert run.rope_angle(run.chip_lets_go + run.SWING_S / 2, run.chip_grab) > 0, "carries on, empty"
    assert run.rope_angle(run.chip_lets_go + run.SWING_S + 0.01, run.chip_grab) is None
    assert run.rope_angle(run.dale_grab - 0.01, run.dale_grab) is None


@pytest.mark.parametrize("height", [32, 64])
def test_the_swing_uncovers_the_ride_behind_chip_and_stays_on_the_board(height):
    run = animation.ChipDaleSwingReveal(64, height)
    ride = (0, 140, 0)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS))]
    edges = [run.reveal_x(t) for t in frames if t < run.run_at]
    assert edges == sorted(edges), "the dark never comes back"
    assert edges[0] == 0 and edges[-1] > 32
    t = run.chip_lets_go
    c = FakeCanvas(64, height)
    fill(ride)(c, t)
    run.overlay(c, t)
    assert c.px[(0, 0)] == ride and c.px[(63, 0)] == (0, 0, 0), "uncovered behind him, dark ahead"
    for t in frames:
        c = FakeCanvas(64, height)
        fill(ride)(c, t)
        run.overlay(c, t)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
        if t >= run.run_at:
            assert (0, 0, 0) not in c.px.values(), "all of it once they run"
    assert run.overlay(FakeCanvas(64, height), run.duration) is False
