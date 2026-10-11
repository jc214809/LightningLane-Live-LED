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


def _house(out):
    colours = set(UpHouseFloats.COLORS.values())
    return {xy for xy, rgb in out.items() if rgb in colours}


def _balloons(out):
    colours = set(UpHouseFloats.BALLOON_COLOURS)
    return {xy for xy, rgb in out.items() if rgb in colours}


@pytest.mark.parametrize("height", [32, 64])
def test_up_house_rises_from_behind_the_castle(height):
    show, actor, out = _play(height, START)
    assert out == {}, "hidden behind the castle at first"
    for i in range(0, int(actor.RISE_S * 10) + 1):
        out = _frame(show, actor, _scene(), START + i / 10)
        assert all(y < actor.clip[x] for x, y in out), "nothing drawn below the castle's roofline"
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
    assert _balloons(_play(height, START + 2.0)[2]), "the balloons come up first"


@pytest.mark.parametrize("height", [32, 64])
def test_up_house_hangs_on_the_board_with_balloons_above(height):
    show, actor, out = _play(height, START + 10.0)
    house, balloons = _house(out), _balloons(out)
    s = actor.scale
    assert len(house) == sum(c != "." for row in actor.ART for c in row) * s * s, "the whole house shows"
    assert len(balloons) > 50 * s * s * 0.8, "a dense bunch"
    assert max(y for _, y in balloons) < min(y for _, y in house), "the balloons are above the house"
    assert all(0 <= x < 64 and 0 <= y < height for x, y in out)


@pytest.mark.parametrize("height", [32, 64])
def test_up_house_drifts_up_and_right_and_is_gone_by_the_end(height):
    show = MusicShow(64, height, random.Random(2))
    actor = UpHouseFloats(show)
    cue = _scene()
    spots = []
    for i in range(int(actor.DRIFT_FROM_S * 10), int((END - START) * 10) + 1):
        _frame(show, actor, cue, START + i / 10)
        spots.append(actor.top_left(actor.elapsed()))
    assert spots[-1][0] + actor.min_dx >= 64, "off to the right"
    assert spots[-1][1] < spots[0][1], "and up"
    assert _frame(show, actor, cue, START + actor.DRIFT_END_S) == {}, "gone by the scene's end"
    assert _frame(show, actor, cue, END - 0.01) == {}


def test_up_house_sways_while_it_hangs():
    actor = UpHouseFloats(MusicShow(64, 64, random.Random(3)))
    xs = {round(actor.top_left(e)[0]) for e in (7.0, 7.8, 8.6, 9.4)}
    assert len(xs) > 1


def test_up_house_draws_nothing_when_inactive():
    show, actor, _ = _play(64, START + 10.0)
    assert _frame(show, actor, _scene(), END + 0.1, active=False) == {}


def test_up_house_follows_the_clock_not_the_frames():
    _, fast, a = _play(64, START + 9.0, fps=30)
    _, slow, b = _play(64, START + 9.0, fps=7)
    assert fast.elapsed() == pytest.approx(slow.elapsed())
    assert fast.top_left(fast.elapsed()) == pytest.approx(slow.top_left(slow.elapsed()))
