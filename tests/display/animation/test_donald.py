"""Donald Duck."""
import random

import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, _striped_screen, fill

NEW = (0, 140, 0)


def _donald(height, seed=1):
    donald = animation.DonaldReveal(64, height, random.Random(seed))
    donald.capture_prev(_striped_screen, 0.0)
    return donald


def _frame(donald, t):
    canvas = FakeCanvas(64, donald.height)
    fill(NEW)(canvas, t)
    donald.overlay(canvas, t)
    return canvas


@pytest.mark.parametrize("attr", ["ART", "TANTRUM_ART", "TANTRUM_HIGH_ART"])
def test_donald_art_is_uniform_and_every_cell_has_a_colour(attr):
    art = getattr(animation.DonaldReveal, attr)
    assert len({len(row) for row in art}) == 1 and len(art) == len(animation.DonaldReveal.ART) <= 32
    assert set("".join(art)) - {"."} <= set(animation.DonaldReveal.COLORS)


def test_donald_is_registered_and_takes_the_old_screen():
    assert animation.TRANSITIONS["donald"] is animation.DonaldReveal
    assert animation.DonaldReveal.wants_prev


@pytest.mark.parametrize("height", [32, 64])
def test_donald_walks_in_and_out_at_a_steady_step(height):
    donald = _donald(height)
    frames = [f / animation.FPS for f in range(int(donald.duration * animation.FPS) + 1)]
    xs = [donald.donald_x(t) for t in frames]
    assert {abs(round(b - a, 6)) for a, b in zip(xs, xs[1:])} <= {0.0, float(donald.STEP)}
    assert xs[0] >= 64 and round(donald.donald_x(donald.duration)) <= -donald.sprite_w, "in from the right, off the left"
    assert abs(donald.stop_x + donald.sprite_w / 2 - 32) <= 2, "boils over mid-board"
    assert donald.scale == (2 if height == 64 else 1)


def test_his_face_goes_red_from_the_neck_up_then_drains():
    donald = _donald(32)
    frames = [f / animation.FPS for f in range(int(donald.duration * animation.FPS))]
    reds = [donald.red(t) for t in frames]
    boiling = [donald.red(t) for t in frames if donald.boil_at <= t < donald.blow_at]
    assert boiling == sorted(boiling) and boiling[-1] == 1.0, "rising through the boil"
    cooling = [donald.red(t) for t in frames if donald.cool_at <= t < donald.leave_at]
    assert cooling == sorted(cooling, reverse=True) and cooling[-1] < 0.1, "draining as he cools"
    assert reds[0] == 0 and donald.red(donald.leave_at) == 0, "white walking in and out"
    half = donald.art_at(donald.boil_at + donald.RED_FILLS * donald.BOIL_FRAMES / 2 / animation.FPS)
    rows = [i for i, line in enumerate(half) if "Q" in line]
    assert rows and max(rows) == donald.FACE_ROWS[1] and min(rows) > donald.FACE_ROWS[0], "neck first"
    tantrum = donald.art_at(donald.blow_at)
    assert all("Q" not in line[:4] and "Q" not in line[14:] for line in tantrum), "his fists stay white"


def test_he_trembles_steams_then_hops_on_one_foot_fists_pumping():
    donald = _donald(32)
    frames = [f / animation.FPS for f in range(int(donald.duration * animation.FPS))]
    boiling = [t for t in frames if donald.boil_at <= t < donald.blow_at]
    assert {donald.tremble(t) for t in boiling} == {-1, 0, 1}
    assert all(donald.tremble(t) == 0 for t in frames if not donald.boil_at <= t < donald.blow_at)
    assert any(list(donald.steam(t)) for t in boiling), "steam before he blows"
    assert not list(donald.steam(donald.boil_at)), "but not as he arrives"
    assert any(list(donald.steam(t)) for t in frames if donald.cool_at <= t < donald.leave_at), "one last puff"
    tantrum = [t for t in frames if donald.tantruming(t)]
    assert {donald.pose(t) for t in tantrum} == {1}, "on one foot"
    assert max(donald.lift(t) for t in tantrum) == donald.HOP_H * donald.scale
    arts = {id(donald.art_at(t)) for t in tantrum}
    assert len(arts) == 2, "fists pumping"


@pytest.mark.parametrize("height", [32, 64])
def test_the_old_screen_stays_whole_black_included_until_he_blows(height):
    donald = _donald(height)
    canvas = _frame(donald, donald.blow_at - 1 / animation.FPS)
    assert NEW not in canvas.px.values(), "no new ride showing through the old screen"
    assert not donald.blown


@pytest.mark.parametrize("height", [32, 64])
def test_blowing_up_flashes_and_blasts_the_old_screen_out_with_feathers(height):
    donald = _donald(height, seed=2)
    flash = _frame(donald, donald.blow_at)
    assert donald.blown and len(donald.feathers) == donald.FEATHERS
    assert flash.px[(0, 0)] == donald.FLASH_RGB
    cx = donald.stop_x + donald.sprite_w / 2
    before = [abs(x - cx) for x, _, _, _, _ in donald.debris]
    landed = _frame(donald, donald.blow_at + 4 / animation.FPS)
    after = [abs(x - cx) for x, _, _, _, _ in donald.debris]
    assert sum(after) > sum(before), "outward from him"
    assert NEW in landed.px.values(), "the new ride shows through"
    _frame(donald, donald.cool_at)
    assert all(not (0 <= x < 64 and 0 <= y < height) for x, y, _, _, _ in donald.debris), \
        "the old screen is gone by the end of his tantrum"

@pytest.mark.parametrize("height", [32, 64])
def test_donald_finishes_and_never_draws_off_board(height):
    donald = _donald(height, seed=3)
    for f in range(int(donald.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert donald.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert donald.overlay(FakeCanvas(64, height), donald.duration) is False


def test_donald_without_an_old_screen_just_reveals_the_new_one():
    donald = animation.DonaldReveal(64, 32, random.Random(4))
    canvas = _frame(donald, donald.duration - 1 / animation.FPS)
    assert NEW in canvas.px.values()
