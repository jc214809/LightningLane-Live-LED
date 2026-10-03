"""Zero, then Jack and Sally."""
import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill

J = animation.JackSallyReveal


def _frames(run):
    return [f / animation.FPS for f in range(round(run.duration * animation.FPS))]


def distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


@pytest.mark.parametrize("attr", ["ZERO_ART", "PAIR_ART", "HEART_ART"])
def test_art_is_uniform_and_every_cell_has_a_colour(attr):
    art = getattr(J, attr)
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(J.colors)


def test_registered_and_the_pair_fits_64x32_whole():
    assert animation.TRANSITIONS["jack_sally"] is J
    assert "O" in "".join(J.ZERO_ART), "Zero's nose"
    assert len(J.PAIR_ART[0]) <= 64 and len(J.PAIR_ART) <= 32


def test_the_pair_splits_into_sally_and_jack_with_nothing_lost():
    run = J(64, 32)
    pair = {(x, y) for y, row in enumerate(J.PAIR_ART) for x, c in enumerate(row) if c != "."}
    assert set(run.sally) | set(run.jack) == pair and not set(run.sally) & set(run.jack)
    sally, jack = set(run.sally.values()), set(run.jack.values())
    assert {"R", "S"} <= sally and "D" not in sally, "her hair and skin, none of his suit"
    assert {"W", "D"} <= jack and not jack & J.SALLY_COLORS, "his skull and suit, none of her"
    assert max(x for x, _ in run.sally) < max(x for x, _ in run.jack), "she's on the left"
    assert any(c == "W" for (x, _), c in run.sally.items()), "her white shoes stay hers"


def test_zeros_nose_glows_and_never_fades_into_white_or_black():
    run = J(64, 64)
    noses = {run.nose_rgb(t) for t in _frames(run)}
    assert len(noses) > 5, "it pulses"
    assert all(distance(n, J.colors["W"]) > 200 and distance(n, (0, 0, 0)) > 300 for n in noses)


def test_the_heart_stands_out_from_sallys_hair_and_the_board():
    c = J.colors
    assert distance(c["X"], c["R"]) > 100 and distance(c["X"], c["H"]) > 150


@pytest.mark.parametrize("height", [32, 64])
def test_zero_floats_steadily_across_first(height):
    run = J(64, height)
    crossing = [t for t in _frames(run) if t < run.zero_s] + [run.zero_s]
    steps = {round(run.zero_x(b) - run.zero_x(a), 6) for a, b in zip(crossing, crossing[1:])}
    assert steps == {float(run.ZERO_STEP)}, "every step steady"
    assert run.zero_x(0) <= -run.zero_w and round(run.zero_x(run.zero_s)) >= 64
    assert all(run.apart(t) is None for t in crossing[:-1]), "Jack and Sally wait for him"


@pytest.mark.parametrize("height", [32, 64])
def test_they_walk_in_from_opposite_sides_lean_in_kiss_and_walk_back_off(height):
    run = J(64, height)
    frames = _frames(run)
    first = run.figures(run.walk_in_at)
    assert all(x < 1 for x, _ in first["sally"]) and all(x >= 63 for x, _ in first["jack"]), \
        "each starts at their own edge"
    walk = [t for t in frames if run.walk_in_at <= t < run.lean_at] + [run.lean_at]
    steps = {round(run.apart(a) - run.apart(b), 6) for a, b in zip(walk, walk[1:])}
    assert steps == {float(run.STEP)}, "every step steady"
    assert run.apart(run.lean_at) == run.APART, "a step apart"
    assert run.apart(run.kiss_at) == 0, "then lean in"
    kiss = run.figures(run.kiss_at + 0.1)
    pair = {(run.pair_x + x, run.pair_y + y): J.colors[c] for y, row in enumerate(J.PAIR_ART)
            for x, c in enumerate(row) if c != "."}
    assert {**kiss["sally"], **kiss["jack"]} == pair, "the kiss is the pattern's pose"
    gone = run.figures(frames[-1])
    assert not gone["sally"] or max(x for x, _ in gone["sally"]) < 4, "Sally off the left"
    assert not gone["jack"] or min(x for x, _ in gone["jack"]) > 59, "Jack off the right"


def test_they_bob_out_of_step_while_walking_and_stand_still_for_the_kiss():
    run = J(64, 32)
    frames = _frames(run)
    walking = [t for t in frames if run.walking(t)]
    assert {run.bob(t, 0) for t in walking} == {0, 1}
    assert all(run.bob(t, 0) != run.bob(t, 1) for t in walking)
    assert all(run.bob(t, 0) == run.bob(t, 1) == 0 for t in frames if run.lean_at <= t < run.leave_at)


@pytest.mark.parametrize("height", [32, 64])
def test_a_heart_floats_up_from_the_kiss_and_stays_on_the_board(height):
    run = J(64, height)
    during = [t for t in _frames(run) if run.kiss_at <= t < run.leave_at]
    spots = [run.heart(t) for t in during]
    assert all(spots), "throughout the kiss"
    assert spots[-1][1] < spots[0][1], "it floats up"
    assert all(y >= 0 and 0 <= x and x + len(J.HEART_ART[0]) <= 64 for x, y in spots)
    lips_x = run.pair_x + J.LIPS[0]
    assert all(x <= lips_x < x + len(J.HEART_ART[0]) for x, _ in spots), "above the kiss"
    assert run.heart(run.kiss_at - 0.01) is None and run.heart(run.leave_at) is None


@pytest.mark.parametrize("height", [32, 64])
def test_the_meet_is_uncovered_behind_zero_and_everything_stays_on_the_board(height):
    run = J(64, height)
    meet = (0, 140, 0)
    t = run.zero_s / 2
    c = FakeCanvas(64, height)
    fill(meet)(c, t)
    run.overlay(c, t)
    assert c.px[(0, 0)] == meet, "behind him"
    assert c.px[(63, 0)] == (0, 0, 0), "still dark ahead of him"
    for t in _frames(run):
        c = FakeCanvas(64, height)
        fill(meet)(c, t)
        assert run.overlay(c, t) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
        if run.zero_s <= t < run.walk_in_at:
            assert set(c.px.values()) == {meet}, "all of the meet once he's gone"
    assert run.overlay(FakeCanvas(64, height), run.duration) is False


def test_it_leaves_the_meets_wait_time_on_screen_a_while():
    assert J(64, 32).duration < 8 - animation.COVER_S - 3, "ride screens hold 8s; leave 3s of the wait"
