"""Zero in a Santa hat, then Sandy Claws and Sally under the snow (and, on 64x64, the mistletoe)."""

import random

import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill

X = animation.JackSallyChristmasReveal
J = animation.JackSallyReveal
CHRISTMAS = set("CcFGNB")


def _frames(run):
    return [f / animation.FPS for f in range(round(run.duration * animation.FPS))]


def distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def run_of(height):
    return X(64, height, random.Random(7))


@pytest.mark.parametrize("attr", ["ZERO_ART", "PAIR_ART", "PAIR_ART_64", "MISTLETOE_ART"])
def test_art_is_uniform_and_every_cell_has_a_colour(attr):
    art = getattr(X, attr)
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(X.colors)


def test_registered_and_the_pair_still_fits_64x32_whole():
    assert animation.TRANSITIONS["jack_sally_christmas"] is X
    assert len(X.PAIR_ART[0]) <= 64 and len(X.PAIR_ART) <= 32


@pytest.mark.parametrize(("christmas", "halloween", "top"), [("ZERO_ART", "ZERO_ART", 5), ("PAIR_ART", "PAIR_ART", 0)])
def test_only_christmas_is_added_to_the_halloween_charts(christmas, halloween, top):
    """Copied from the Halloween charts cell for cell; every changed cell is the hat, beard, suit or holly."""
    new, old = getattr(X, christmas)[top:], getattr(J, halloween)
    assert len(new) == len(old)
    changed = {new[y][x] for y, row in enumerate(old) for x, c in enumerate(row) if new[y][x] != c}
    assert changed and changed <= CHRISTMAS | {"K"}
    assert not set("".join(getattr(X, christmas)[:top])) - CHRISTMAS - {"K", "."}, "Zero's hat above his head"


def test_the_64x64_pair_only_adds_a_taller_crown():
    rows = X.HAT_ROWS_64
    assert rows > 0 and X.PAIR_ART_64[rows + 2 :] == X.PAIR_ART[2:]
    crown = "".join(X.PAIR_ART_64[:rows])
    assert set(crown) <= {".", "K", "C"} and "C" in crown


def test_the_beard_and_fur_stand_out_from_his_skull_and_the_red_from_sallys_hair():
    c = X.colors
    assert distance(c["F"], c["W"]) > 60, "ivory, not his skull's white"
    assert distance(c["C"], c["R"]) > 20 and distance(c["C"], c["H"]) > 60


@pytest.mark.parametrize("height", [32, 64])
def test_the_pair_splits_into_sally_with_holly_and_jack_in_red(height):
    run = run_of(height)
    art = run.PAIR_ART
    pair = {(x, y) for y, row in enumerate(art) for x, c in enumerate(row) if c != "."}
    assert set(run.sally) | set(run.jack) == pair and not set(run.sally) & set(run.jack)
    sally, jack = set(run.sally.values()), set(run.jack.values())
    assert {"G", "B"} <= sally and not sally & set("CcF"), "her holly, none of his Santa suit"
    assert {"W", "C", "F"} <= jack and not jack & X.SALLY_COLORS


@pytest.mark.parametrize("height", [32, 64])
def test_zeros_hat_shows_as_he_floats_across(height):
    run = run_of(height)
    t = run.zero_s / 2
    c = FakeCanvas(64, height)
    run.overlay(c, t)
    assert X.colors["C"] in c.px.values() and X.colors["F"] in c.px.values()
    if height == 32:
        assert run.zero_y == -2, "only the pom's top rows and his tail's tip are off the board"


@pytest.mark.parametrize("height", [32, 64])
def test_the_kiss_is_the_christmas_pose_with_the_heart_above_it(height):
    run = run_of(height)
    kiss = run.figures(run.kiss_at + 0.1)
    pair = {
        (run.pair_x + x, run.pair_y + y): X.colors[c]
        for y, row in enumerate(run.PAIR_ART)
        for x, c in enumerate(row)
        if c != "."
    }
    assert {**kiss["sally"], **kiss["jack"]} == pair
    assert run.pair_y + len(run.PAIR_ART) == height, "standing on the bottom edge"
    x, y = run.heart(run.kiss_at)
    lips_x, lips_y = run.pair_x + run.LIPS[0], run.pair_y + run.LIPS[1]
    assert x <= lips_x < x + len(X.HEART_ART[0]) and y + len(X.HEART_ART) == lips_y, "from her lips"


@pytest.mark.parametrize("height", [32, 64])
def test_snow_falls_only_while_they_are_on_and_stays_on_the_board(height):
    run = run_of(height)
    assert run.snow(run.walk_in_at - 0.01) == {} and run.snow(run.duration) == {}
    falling = [run.snow(t) for t in _frames(run) if t >= run.walk_in_at]
    assert all(0 < len(s) <= len(run.flakes) for s in falling)
    assert all(0 <= x < 64 and 0 <= y < height for s in falling for x, y in s)
    assert falling[0] != falling[len(falling) // 2], "it moves"
    assert len(run_of(64).flakes) == 2 * len(run_of(32).flakes)


def test_the_mistletoe_hangs_from_the_top_over_the_kiss_on_64x64_only():
    assert run_of(32).mistletoe_at is None, "no rows for it above them on 64x32"
    run = run_of(64)
    x, y = run.mistletoe_at
    w = len(X.MISTLETOE_ART[0])
    assert y == 0 and x + w // 2 == run.pair_x + run.LIPS[0]
    assert y + len(X.MISTLETOE_ART) < run.pair_y, "clear of Jack's hat"
    settled = run.zero_s + run.DROP_S + run.SETTLE_S
    for t, shown in ((run.zero_s / 2, False), (settled, True), (run.kiss_at, True)):
        c = FakeCanvas(64, 64)
        run.overlay(c, t)
        assert (c.px.get((x + w // 2, 6)) == X.colors["n"]) is shown


def test_the_mistletoe_pops_down_from_above_dips_and_springs_back():
    run = run_of(64)
    h = len(X.MISTLETOE_ART)
    dropping = [run.mistletoe_top(t) for t in _frames(run) if run.zero_s <= t < run.zero_s + run.DROP_S]
    assert dropping[0] == -h, "starts just above the board"
    assert all(b >= a for a, b in zip(dropping, dropping[1:])), "only ever down"
    settle_at = run.zero_s + run.DROP_S
    settling = [run.mistletoe_top(t) for t in _frames(run) if settle_at <= t < settle_at + run.SETTLE_S]
    assert max(dropping + settling) == run.DIP, "dips past its place"
    assert all(b <= a for a, b in zip(settling, settling[1:])), "then springs back up"
    assert run.mistletoe_top(settle_at + run.SETTLE_S) == 0


def test_the_mistletoe_is_pulled_up_off_the_top_as_they_walk_away():
    run = run_of(64)
    assert run_of(32).mistletoe_top(run.kiss_at) is None
    assert run.mistletoe_top(run.zero_s / 2) is None, "not while Zero crosses"
    settled = run.zero_s + run.DROP_S + run.SETTLE_S
    assert settled < run.lean_at, "hanging before they lean in"
    assert {run.mistletoe_top(t) for t in _frames(run) if settled <= t <= run.leave_at} == {0}, "still till then"
    leaving = [run.mistletoe_top(t) for t in _frames(run) if t >= run.leave_at]
    assert all(b <= a for a, b in zip(leaving, leaving[1:])), "only ever up"
    assert leaving[0] == 0 and leaving[-1] + len(X.MISTLETOE_ART) <= 1, "from the top edge to all but gone"
    assert run.mistletoe_top(run.duration) is None


@pytest.mark.parametrize("height", [32, 64])
def test_everything_stays_on_the_board_and_leaves_the_wait_time_showing(height):
    run = run_of(height)
    meet = (0, 140, 0)
    for t in _frames(run):
        c = FakeCanvas(64, height)
        fill(meet)(c, t)
        assert run.overlay(c, t) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
    assert run.overlay(FakeCanvas(64, height), run.duration) is False
    assert run.duration < 8 - animation.COVER_S - 3, "ride screens hold 8s; leave 3s of the wait"
