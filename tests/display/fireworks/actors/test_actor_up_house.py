import random

import pytest

from display.fireworks.actors.up_house import UpHouseFloats
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, END = 303.0, 325.0


def _scene():
    return Cue("s", "Touch the Sky / Up", START, END, ((255, 0, 0),), 0.0, None, (), frozenset(),
               "ghost", ("up_house",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _play(height, until, fps=30, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    actor = UpHouseFloats(show)
    cue = _scene()
    i, out = 0, {}
    while START + i / fps <= until:
        out = _frame(show, actor, cue, START + i / fps)
        i += 1
    return show, actor, out


def _split(actor, out):
    """out's pixels as (house, balloons and strings): the house is everything from its top row down."""
    top = round(actor.top_left(actor.elapsed())[1])
    return {xy for xy in out if xy[1] >= top}, {xy for xy in out if xy[1] < top}


@pytest.mark.parametrize("height", [32, 64])
def test_up_house_floats_in_from_the_left_edge(height):
    show, actor, out = _play(height, START)
    assert out == {}, "off the left edge at first"
    first = None
    for i in range(0, 80):
        out = _frame(show, actor, _scene(), START + i / 10)
        assert all(y < actor.clip[x] for x, y in out), "nothing drawn below the castle's roofline"
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
        if out and first is None:
            first = out
    assert first and max(x for x, _ in first) < 3, "it comes in at the left edge"


@pytest.mark.parametrize("height", [32, 64])
def test_up_house_crosses_with_balloons_above(height):
    show, actor, out = _play(height, START + 8.0)
    house, balloons = _split(actor, out)
    left, top = (round(v) for v in actor.top_left(actor.elapsed()))
    chimney = {(left + col, top + row) for row in range(4) for col in (11, 12, 13)}
    assert chimney <= house, "the chimney shows"
    assert len(house) > 60, "and the top of the house"
    assert len(balloons) > 40, "a dense bunch (climbing off the top on 64x32)"
    assert max(y for _, y in balloons) < min(y for _, y in house), "the balloons are above the house"


@pytest.mark.parametrize("height", [32, 64])
def test_up_house_leaves_off_the_top_right_corner(height):
    show = MusicShow(64, height, random.Random(2))
    actor = UpHouseFloats(show)
    cue = _scene()
    spots = [actor.top_left(e / 2) for e in range(0, int(actor.CROSS_S * 2) + 1)]
    assert all(b[0] > a[0] for a, b in zip(spots, spots[1:])), "always left to right"
    assert spots[-1][1] < spots[len(spots) // 2][1] < spots[0][1] + 1, "climbing"
    assert spots[-1][0] + actor.min_dx >= 64 and spots[-1][1] + actor.h <= 1, "out past the top-right corner"
    assert _frame(show, actor, cue, START + actor.CROSS_S) == {}, "gone by the scene's end"
    assert _frame(show, actor, cue, END - 0.01) == {}


def test_up_house_bobs_as_it_goes():
    actor = UpHouseFloats(MusicShow(64, 64, random.Random(3)))
    assert {round(actor.top_left(e)[1]) for e in (0.0, 0.8, 1.6, 2.4)} != {actor.hover}


def test_up_house_is_the_chart_on_64x64_and_its_house_on_64x32():
    big, small = UpHouseFloats(MusicShow(64, 64, random.Random(1))), UpHouseFloats(MusicShow(64, 32, random.Random(1)))
    art = {(col, row - len(UpHouseFloats.BALLOONS_ART)): UpHouseFloats.COLORS[c]
           for row, line in enumerate(UpHouseFloats.BALLOONS_ART + UpHouseFloats.ART)
           for col, c in enumerate(line) if c != "."}
    assert {(dx, dy): rgb for dx, dy, rgb in big.cells} == art
    assert (big.w, big.h, big.above) == (24, 24, 22)
    house = {(dx, dy): rgb for dx, dy, rgb in small.cells if dy >= 0}
    assert house == {xy: rgb for xy, rgb in art.items() if xy[1] >= 0}
    bunch = {rgb for dx, dy, rgb in small.cells if dy < 0} - {UpHouseFloats.STRING_RGB}
    assert bunch <= set(UpHouseFloats.BALLOON_COLOURS)
    assert all(-small.above <= dy for _, dy, _ in small.cells)


def test_up_house_strings_meet_its_chimney():
    for height in (32, 64):
        actor = UpHouseFloats(MusicShow(64, height, random.Random(1)))
        cells = {(dx, dy) for dx, dy, _ in actor.cells}
        assert (actor.CHIMNEY_COL, -1) in cells and (actor.CHIMNEY_COL, 0) in cells


def test_up_house_draws_nothing_when_inactive():
    show, actor, _ = _play(64, START + 8.0)
    assert _frame(show, actor, _scene(), END + 0.1, active=False) == {}


def test_up_house_follows_the_clock_not_the_frames():
    _, fast, a = _play(64, START + 9.0, fps=30)
    _, slow, b = _play(64, START + 9.0, fps=7)
    assert fast.elapsed() == pytest.approx(slow.elapsed())
    assert fast.top_left(fast.elapsed()) == pytest.approx(slow.top_left(slow.elapsed()))
