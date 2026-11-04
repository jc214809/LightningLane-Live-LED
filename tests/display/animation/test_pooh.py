"""Pooh floats up on his balloon."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, fill


Pooh = animation.PoohReveal
OLD, NEW = (0, 40, 90), (70, 0, 70)


def _floating(height, seed=1):
    pooh = Pooh(64, height, random.Random(seed))
    pooh.capture_prev(fill(OLD), 0)
    return pooh


def _frames(pooh):
    return [f / animation.FPS for f in range(int(pooh.duration * animation.FPS))]


def _drawn(pooh, t):
    canvas = FakeCanvas(64, pooh.height)
    fill(NEW)(canvas, t)
    pooh.overlay(canvas, t)
    return canvas


def test_pooh_art_is_uniform_and_every_cell_has_a_colour():
    assert len({len(row) for row in Pooh.ART}) == 1
    assert set("".join(Pooh.ART)) - {"."} <= set(Pooh.colors)
    assert animation.TRANSITIONS["pooh"] is Pooh and Pooh.wants_prev and Pooh.SCALE == 1


def test_the_art_splits_into_balloon_string_and_pooh():
    balloon, string = Pooh.ART[:Pooh.BALLOON_ROWS], Pooh.ART[Pooh.BALLOON_ROWS:Pooh.POOH_ROW]
    assert set("".join(balloon)) - {"."} >= {"R", "K"}, "a red balloon, outlined"
    assert all(row.strip(".") == "S" and row[Pooh.STRING_COL] == "S" for row in string), "only string between them"
    assert "Y" in "".join(Pooh.ART[Pooh.POOH_ROW:]), "Pooh under it"


def test_colours_read_against_each_other():
    def distance(a, b):
        return sum(abs(x - y) for x, y in zip(Pooh.colors[a], Pooh.colors[b]))
    assert distance("R", "Y") > 150, "his shirt against his fur"
    assert distance("Y", "K") > 300 and distance("R", "K") > 150, "the outline against both"


@pytest.mark.parametrize("height", [32, 64])
def test_he_rises_hovers_and_drifts_off_the_top_within_the_ride_screen(height):
    pooh = _floating(height)
    tops = [pooh.top_y(t) for t in _frames(pooh)]
    assert tops[0] >= height - 1, "starts below the board"
    assert all(b <= a for a, b in zip(tops, tops[1:])), "only ever goes up"
    hovering = [t for t in _frames(pooh) if pooh.rise_s <= t < pooh.leave_at]
    assert len(hovering) >= animation.FPS * 0.9 and {pooh.top_y(t) for t in hovering} == {height - len(Pooh.ART)}
    assert pooh.top_y(pooh.duration) == -len(Pooh.ART) - Pooh.GAP, "all of him and the edge off the top at the end"
    assert pooh.duration < 6, "leaves the ride screen time to read"
    assert not pooh.overlay(FakeCanvas(64, height), pooh.duration)


@pytest.mark.parametrize("height", [32, 64])
def test_he_floats_never_faster_than_a_couple_of_rows_a_frame(height):
    pooh = Pooh(64, height)
    tops = [pooh.top_y(t) for t in _frames(pooh)]
    assert max(a - b for a, b in zip(tops, tops[1:])) <= 1.6 * Pooh.RISE_SPEED / animation.FPS


def test_rising_and_leaving_take_their_time_by_distance():
    short, tall = Pooh(64, 32), Pooh(64, 64)
    assert tall.rise_s == short.rise_s, "the same rise up to the hover"
    assert tall.leave_s - short.leave_s == 32 / Pooh.RISE_SPEED, "the extra half board to leave"


def test_on_64x64_all_of_him_is_on_the_board_while_he_hovers():
    pooh = _floating(64)
    canvas = _drawn(pooh, pooh.rise_s + 0.5)
    balloon_red = [y for (x, y), rgb in canvas.px.items() if rgb == Pooh.colors["R"] and y < 20]
    pooh_yellow = [y for (x, y), rgb in canvas.px.items() if rgb == Pooh.colors["Y"] and y > 50]
    assert balloon_red and pooh_yellow, "balloon at the top, his feet at the bottom"


def test_the_balloon_sways_and_pooh_swings_a_beat_behind():
    pooh = _floating(64)
    sways = [pooh.sway(t) for t in _frames(pooh)]
    assert {b for b, _ in sways} == set(range(-Pooh.SWAY, Pooh.SWAY + 1)), "both ways, as far as SWAY"
    assert any(b != p for b, p in sways), "Pooh isn't stuck to the balloon"


@pytest.mark.parametrize("height", [32, 64])
@pytest.mark.parametrize("seed", range(6))
def test_he_stays_on_the_board_sideways(height, seed):
    pooh = _floating(height, seed)
    for t in _frames(pooh):
        canvas = FakeCanvas(64, height)
        pooh.overlay(canvas, t)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    xs = set()
    for t in _frames(pooh):
        balloon, swing = pooh.sway(t)
        xs |= {pooh.x0 + min(balloon, swing), pooh.x0 + len(Pooh.ART[0]) - 1 + max(balloon, swing)}
    assert min(xs) >= 0 and max(xs) < 64, "none of him clipped at the sides"


@pytest.mark.parametrize("height", [32, 64])
def test_the_old_ride_stays_above_his_feet_and_the_new_one_shows_below(height):
    pooh = _floating(height)
    t = pooh.leave_at + pooh.leave_s / 2
    seam = round(pooh.top_y(t)) + len(Pooh.ART) + Pooh.GAP
    canvas = _drawn(pooh, t)
    assert canvas.px[(0, 0)] == OLD and canvas.px[(63, seam - 1)] == OLD, "the old ride above, edge to edge"
    assert canvas.px[(0, seam)] == animation.EDGE_RGB, "a gold edge under his feet"
    feet = round(pooh.top_y(t)) + len(Pooh.ART) - 1
    assert seam - feet > 2, "with a gap of the old ride between them, not right on him"
    assert canvas.px[(0, height - 1)] == NEW, "the new ride below"
    first = _drawn(pooh, 0)
    assert NEW not in first.px.values(), "nothing of the new ride before he's come up"
    last = _drawn(pooh, _frames(pooh)[-1])
    assert list(last.px.values()).count(OLD) <= 64, "no more than a row of the old ride left as he goes"
