"""Tigger."""
import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill


@pytest.mark.parametrize("attr", ["BOUNCE_ART", "SQUASHED_ART", "LYING_ART"])
def test_tigger_art_is_uniform_and_every_cell_has_a_colour(attr):
    art = getattr(animation.TiggerReveal, attr)
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.TiggerReveal.colors)


def test_tigger_fits_each_board_at_1x():
    assert len(animation.TiggerReveal.LYING_ART) == 32 and len(animation.TiggerReveal.LYING_ART[0]) <= 64
    assert len(animation.TiggerReveal.SQUASHED_ART) < len(animation.TiggerReveal.BOUNCE_ART) < 64
    assert animation.TiggerReveal(64, 32).lying and not animation.TiggerReveal(64, 64).lying
    assert animation.TRANSITIONS["tigger"] is animation.TiggerReveal


def test_tigger_bounces_across_at_a_steady_step_landing_between_hops():
    tigger = animation.TiggerReveal(64, 64)
    frames = [f / animation.FPS for f in range(int(tigger.duration * animation.FPS))]
    xs = [tigger.x_at(t) for t in frames]
    assert {round(b - a, 6) for a, b in zip(xs, xs[1:])} == {float(tigger.STEP)}
    lifts = [tigger.bounce(t)[0] for t in frames]
    assert max(lifts) == tigger.bounce_h >= 2, "he leaves the ground"
    squashes = [t for t in frames if tigger.bounce(t)[1]]
    assert squashes, "and lands, tail squashed"
    assert all(tigger.bounce(t)[0] == 0 for t in squashes), "on the ground when squashed"
    assert max(lifts) + len(tigger.BOUNCE_ART) <= 64, "never bounces off the top"


def test_lying_tigger_stalks_in_wiggles_his_tail_then_pounces_off():
    tigger = animation.TiggerReveal(64, 32)
    frames = [f / animation.FPS for f in range(int(tigger.duration * animation.FPS))]
    steps = {round(tigger.x_at(b) - tigger.x_at(a), 6) for a, b in zip(frames, frames[1:])}
    assert steps <= {float(tigger.STEP), 0.0, float(tigger.POUNCE_STEP)}, "every step steady"
    waiting = [t for t in frames if tigger.creep_s <= t < tigger.pounce_at]
    assert waiting and all(tigger.x_at(t) == tigger.REST_X for t in waiting)
    assert {tigger.tail_sway(t) for t in waiting} >= {-2, 2}, "his tail sways both ways"
    assert all(tigger.tail_sway(t) == 0 for t in frames if t < tigger.creep_s or t >= tigger.pounce_at)
    assert all(tigger.pounce_lift(t) == 0 for t in frames if t < tigger.pounce_at)
    assert max(tigger.pounce_lift(t) for t in frames) == tigger.POUNCE_H, "he leaps"
    assert tigger.x_at(tigger.duration) == 64, "and is gone off the right"


@pytest.mark.parametrize("height", [32, 64])
def test_tigger_uncovers_the_ride_behind_him_and_stays_on_the_board(height):
    tigger = animation.TiggerReveal(64, height)
    ride = (0, 140, 0)
    t = tigger.creep_s / 2 if tigger.lying else tigger.duration / 4
    canvas = FakeCanvas(64, height)
    fill(ride)(canvas, t)
    tigger.overlay(canvas, t)
    assert canvas.px[(63, height - 1)] == (0, 0, 0), "still dark ahead of him"
    for f in range(int(tigger.duration * animation.FPS)):
        c = FakeCanvas(64, height)
        fill(ride)(c, f / animation.FPS)
        tigger.overlay(c, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
    c = FakeCanvas(64, height)
    fill(ride)(c, tigger.duration - 1 / animation.FPS)
    tigger.overlay(c, tigger.duration - 1 / animation.FPS)
    assert c.px[(0, 0)] == ride, "the ride is showing behind him"
    assert tigger.overlay(FakeCanvas(64, height), tigger.duration) is False


def test_lying_tigger_walks_in_then_stands_still_to_wiggle():
    tigger = animation.TiggerReveal(64, 32)

    def drawn(t):
        c = FakeCanvas(64, 32)
        tigger.overlay(c, t)
        x = int(round(tigger.x_at(t)))
        return {(px - x, py) for (px, py) in c.px if py >= 30}  # his paws, relative to him

    pose_s = tigger.STALK_POSE_S
    walking = {frozenset(drawn(0.5 + i * pose_s)) for i in range(4)}
    assert len(walking) == 4, "his paws step as he walks in"
    still = tigger.creep_s + 0.01
    assert drawn(still) == drawn(still + pose_s), "and stand still while he waits"
