"""The archer."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas

Archer = animation.ArcherReveal


def _archer(height=64):
    return Archer(64, height, random.Random(1))


def _frame(archer, t):
    canvas = FakeCanvas(archer.width, archer.height)
    for y in range(archer.height):  # a lit screen under the overlay, so a blackout shows
        for x in range(archer.width):
            canvas.px[(x, y)] = (10, 20, 60)
    archer.overlay(canvas, t)
    return canvas.px


def _distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def test_the_archer_is_a_registered_transition_and_fits_a_64x64_board():
    assert animation.TRANSITIONS["archer"] is Archer and Archer.SCALE == 1
    assert len({len(row) for row in Archer.ART}) == 1
    assert {ch for row in Archer.ART for ch in row} - {"."} <= set(Archer.COLORS)
    assert len(Archer.ART) <= 64 and len(Archer.ART[0]) + Archer.LEFT <= 64


def test_she_rises_from_the_bottom_holds_at_full_draw_and_sinks_away():
    archer = _archer()
    top = lambda t: min(y for (x, y), rgb in _frame(archer, t).items() if rgb == Archer.COLORS["O"])  # noqa: E731
    assert top(0.2) > top(0.4) > top(archer.RISE_S + 0.01) - 1, "climbing"
    assert top(archer.RISE_S + 0.1) == top(archer.release_at - 0.01), "still while she aims"
    assert top(archer.sink_at + 0.2) < top(archer.sink_at + 0.4), "sinking"
    assert Archer.COLORS["O"] not in _frame(archer, archer.duration - 0.001).values() or \
        top(archer.duration - 0.001) > 60, "all but gone at the end"
    assert archer.overlay(FakeCanvas(64, 64), archer.duration) is False


def test_the_screen_is_black_until_she_looses_then_uncovered_behind_the_arrow():
    archer = _archer()
    lit = lambda t: sum(rgb == (10, 20, 60) for rgb in _frame(archer, t).values())  # noqa: E731
    assert lit(archer.release_at - 0.01) == 0, "the new screen is hidden while she aims"
    fronts = [archer.front(archer.release_at + s / 100) for s in range(0, 60)]
    assert fronts[0] <= 1 and fronts == sorted(fronts)
    assert archer.front(archer.release_at + 0.5) >= 64, "all of it uncovered"
    assert lit(archer.release_at + 0.2) < lit(archer.release_at + 0.4), "more of it as the arrow goes"
    assert lit(archer.duration - 0.001) > 64 * 64 * 0.9


def test_the_arrow_flies_out_across_the_board_and_fast():
    archer = _archer()
    tails = [archer.arrow_tail(archer.release_at + s / 100) for s in range(0, 50)]
    assert tails[0] == archer.tail0 and tails == sorted(tails)
    assert tails[-1] > 64 + archer.TRAIL, "right off the other edge"
    assert max(b - a for a, b in zip(tails, tails[1:])) * 100 > 100, "an arrow, not a drift"
    nocked = archer.arrow_pixels(archer.release_at - 0.01, 0)
    assert min(x for x, _ in nocked) == archer.tail0, "nocked on the string until then"


def test_the_string_is_drawn_back_then_snaps_straight_and_rings():
    archer = _archer()
    pull = lambda t: archer.string_pixels(t, 0, 0)  # noqa: E731
    xs = lambda t: {x for x, _ in pull(t)}  # noqa: E731
    assert min(xs(0.5)) < max(xs(0.5)), "a V at full draw"
    straight = archer.release_at + 1 / (4 * Archer.RING_HZ)
    assert len(xs(straight)) <= 2, "straight a quarter of a swing after the release"
    assert max(xs(archer.release_at + 1 / (2 * Archer.RING_HZ))) > max(xs(0.5)), "it swings past, ahead of the bow's tips"
    assert len(xs(archer.release_at + 1.0)) <= 2, "and has settled"


def test_she_rocks_back_a_pixel_on_the_shot_only():
    archer = _archer()
    assert [archer.recoil(t) for t in (0.5, archer.release_at + 0.05, archer.release_at + 0.3)] == [0, -1, 0]


def test_the_arrow_and_string_show_against_the_screen_and_each_other():
    assert _distance(Archer.SHAFT_RGB, (0, 0, 0)) > 400
    assert _distance(Archer.TIP_RGB, Archer.SHAFT_RGB) > 60
    assert _distance(Archer.FLETCH_RGB, Archer.SHAFT_RGB) > 200
    assert _distance(Archer.STRING_RGB, Archer.COLORS["O"]) > 150, "the string against her hair and bow"


def test_the_arrow_passes_behind_her_bow_hand():
    archer = _archer()
    cols = {x for x, _ in archer.arrow_pixels(archer.release_at - 0.01, 0)}
    lo, hi = Archer.LEFT + Archer.HAND_COLS[0], Archer.LEFT + Archer.HAND_COLS[1]
    assert not cols & set(range(lo, hi + 1)) and min(cols) < lo and max(cols) > hi


def test_it_follows_the_clock_not_the_frames():
    archer = _archer()
    for t in (0.3, 1.0, archer.release_at + 0.2, archer.sink_at + 0.2):
        assert _frame(archer, t) == _frame(_archer(), t)


@pytest.mark.parametrize("height", [32, 64])
def test_nothing_is_drawn_off_the_board_on_either_size(height):
    archer = _archer(height)
    for step in range(int(archer.duration * 30) + 1):
        for x, y in _frame(archer, step / 30):
            assert 0 <= x < 64 and 0 <= y < height


def _face():
    cells = {(x, y): k for y, row in enumerate(Archer.ART) for x, k in enumerate(row)}
    eyes = sorted(x for (x, y), k in cells.items() if k == "e")
    return cells, eyes


def test_she_has_a_face_two_blue_eyes_ringed_by_skin_with_brows_and_a_mouth_below():
    cells, eyes = _face()
    assert len(eyes) == 2 and eyes[1] - eyes[0] >= 2, "two eyes with skin between"
    skin = {"F", "h"}
    for (x, y), k in cells.items():
        if k == "e":
            assert cells[(x - 1, y)] in skin | {"w", "E"} and cells[(x, y - 1)] in skin | {"R"}
    eye_rows = {y for (x, y), k in cells.items() if k in "eE"}
    mouth_rows = {y for (x, y), k in cells.items() if k == "m"}
    brow_rows = {y for (x, y), k in cells.items() if k == "R" and y < min(eye_rows) and cells[(x, y + 1)] in skin | {"w"}}
    assert mouth_rows and min(mouth_rows) > max(eye_rows), "the mouth is below the eyes"
    assert brow_rows and max(brow_rows) < min(eye_rows), "brows above them"


def test_her_nose_sits_between_her_eyes_and_mouth_with_skin_under_it():
    cells, eyes = _face()
    (nx, ny), = [p for p, k in cells.items() if k == "n"]
    eye_rows = {y for (x, y), k in cells.items() if k in "eE"}
    mouth = [(x, y) for (x, y), k in cells.items() if k == "m"]
    assert max(eye_rows) < ny < min(y for _, y in mouth)
    assert eyes[0] < nx < eyes[1] + 1, "between the eyes"
    assert cells[(nx, ny + 1)] == "F", "a row of skin, or nose and mouth close into a kiss"
    assert _distance(Archer.COLORS["n"], Archer.COLORS["F"]) > 100


def test_the_eyes_and_mouth_show_against_her_skin():
    skin = Archer.COLORS["F"]
    for key in ("e", "E", "m", "p"):
        assert _distance(Archer.COLORS[key], skin) > 100, key
    assert _distance(Archer.COLORS["E"], Archer.COLORS["e"]) > 60, "the pupil against the iris"
