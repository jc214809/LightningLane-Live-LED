"""The Seven Dwarfs Mine Train."""
import random

import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill

VARIANTS = {"mine_train": animation.MineTrainReveal, "mine_train_all": animation.MineTrainAllReveal,
            "mine_train_snow": animation.MineTrainSnowReveal}


def _sprites(cls):
    yield from (cls.CAR_ART, cls.CAR_SHORT_ART, cls.GEMS_ART, cls.LANTERN_ART, cls.DRAWBAR_ART, cls.SNOW_ART)
    yield from cls.DWARFS
    yield from cls.WHEEL_ART


@pytest.mark.parametrize("name, cls", VARIANTS.items())
def test_each_train_is_registered(name, cls):
    assert animation.TRANSITIONS[name] is cls


def test_the_art_is_well_formed():
    cls = animation.MineTrainReveal
    for art in _sprites(cls):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(cls.COLORS)
    assert len(cls.DWARFS) == len(cls.BUCKLE) == 7
    assert len(cls.CAR_ART) - len(cls.CAR_SHORT_ART) == 4, "64x64's car is 4 rows taller"


def test_a_few_random_dwarfs_ride_with_the_gem_car_at_the_back():
    seen = set()
    for seed in range(20):
        train = animation.MineTrainReveal(64, 32, random.Random(seed))
        assert train.cars[0] == "gems"
        riders = train.cars[1:]
        assert len(riders) == 3 and len(set(riders)) == 3 and "snow" not in riders
        seen.update(riders)
    assert seen == set(range(7)), "every dwarf gets his turn"


def test_the_whole_train_carries_all_seven():
    train = animation.MineTrainAllReveal(64, 32, random.Random(1))
    assert train.cars[0] == "gems" and sorted(train.cars[1:]) == list(range(7))


def test_snow_white_rides_the_lead_car_only_on_her_train():
    train = animation.MineTrainSnowReveal(64, 32, random.Random(1))
    assert train.cars[-1] == "snow" and sorted(train.cars[1:-1]) == list(range(7))
    assert "snow" not in animation.MineTrainAllReveal(64, 32, random.Random(1)).cars


@pytest.mark.parametrize("cls", VARIANTS.values())
@pytest.mark.parametrize("height", [32, 64])
def test_the_train_rolls_in_from_the_left_and_off_the_right(cls, height):
    train = cls(64, height, random.Random(0))
    xs = [train.back_x(i / 10) for i in range(int(train.duration * 10) + 1)]
    assert xs == sorted(xs), "travelling right"
    blank = FakeCanvas(64, height)
    train.overlay(blank, 0.0)
    assert set(blank.px.values()) <= {(0, 0, 0)}, "starts wholly off the left edge"
    assert train.back_x(train.duration) >= 64, "the gem car leaves last"
    assert train.overlay(FakeCanvas(64, height), train.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_every_frame_stays_on_the_board(height):
    train = animation.MineTrainSnowReveal(64, height, random.Random(0))
    for f in range(int(train.duration * animation.FPS)):
        c = FakeCanvas(64, height)
        train.overlay(c, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)


def test_the_ride_is_uncovered_behind_the_train_and_dark_ahead_of_it():
    train = animation.MineTrainReveal(64, 64, random.Random(0))
    ride = (0, 140, 0)
    # When the lead car's front reaches column 40.
    back = 40 - (len(train.cars) - 1) * train.GAP - train.CAR_W
    t = (back + train.length) / train.SPEED
    canvas = FakeCanvas(64, 64)
    fill(ride)(canvas, 0)
    train.overlay(canvas, t)
    assert canvas.px[(63, 0)] == (0, 0, 0), "still dark ahead"
    assert canvas.px[(0, 0)] == ride, "the ride shows where the train has been"


@pytest.mark.parametrize("height", [32, 64])
def test_every_rider_fits_under_the_top_of_the_board(height):
    train = animation.MineTrainSnowReveal(64, height, random.Random(0))
    assert train.top - train.show + 2 >= 0 and train.top - train.snow_show + 2 >= 0
    if height == 64:
        assert (train.show, train.snow_show) == (train.SHOW, train.SNOW_SHOW), "shoulders up on 64x64"
        assert train.car_art is train.CAR_ART
    else:
        assert train.car_art is train.CAR_SHORT_ART, "64x32 gets the short car"


def test_the_wheels_turn_as_the_train_rolls():
    train = animation.MineTrainReveal(64, 32, random.Random(0))
    a, b = FakeCanvas(64, 32), FakeCanvas(64, 32)
    t = train.length / train.SPEED  # the gem car at the left edge
    train.overlay(a, t)
    train.overlay(b, t + 3 / train.SPEED)  # 3px on: the next eighth of a turn
    wheel_rows = range(train.base - len(train.WHEEL_ART[0]), train.base)
    assert any(a.px.get((x, y)) != b.px.get((x + 3, y)) for x in range(64 - 3) for y in wheel_rows)


def test_the_full_train_asks_for_the_ride_screen_to_outlast_it():
    train = animation.MineTrainSnowReveal(64, 32, random.Random(0))
    assert train.duration > 8, "longer than a ride screen's usual hold"
    assert train.hold_after_s > 0
