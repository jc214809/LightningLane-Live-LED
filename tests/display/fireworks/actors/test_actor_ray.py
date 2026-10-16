import math
import random

import pytest

from display.fireworks.actors.ray import RayGlows
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, MID, END = 147.0, 171.0, 192.0


def _scenes():
    return (Cue("p", "Down in New Orleans (prologue)", START, MID, ((255, 200, 120),), 0.0, None, (),
                frozenset({"evening_star"}), "ghost", ("ray",)),
            Cue("f", "When You Wish Upon a Star (fanfare)", MID, END, ((255, 255, 255),), 0.0, None, (),
                frozenset({"comet_fan"}), "castle", ("ray",)))


def _frame(show, actor, t, active=True):
    first, second = _scenes()
    show.set_cue(first if t < MID else second, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _play(height, until, fps=30, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    actor = RayGlows(show)
    first, second = _scenes()
    i, out = 0, {}
    while START + i / fps <= until:
        t = START + i / fps
        # The same Cue objects across frames, as the show hands them out.
        show.set_cue(first if t < MID else second, t)
        actor.follow(True)
        actor.step(True)
        out = {}
        actor.draw(lambda *a: None, out, True)
        i += 1
    return show, actor, out


def _core(actor, out):
    return {xy for xy, rgb in out.items() if rgb[1] > 150}


@pytest.mark.parametrize("height", [32, 64])
def test_ray_stays_on_the_board_through_both_scenes(height):
    show = MusicShow(64, height, random.Random(2))
    actor = RayGlows(show)
    first, second = _scenes()
    for i in range(int((END - START) * 10) + 1):
        t = START + i / 10
        show.set_cue(first if t < MID else second, t)
        actor.follow(True)
        out = {}
        actor.draw(lambda *a: None, out, True)
        assert out and all(0 <= x < 64 and 0 <= y < height for x, y in out)
        assert len(_core(actor, out)) == actor.size ** 2
    assert actor.elapsed() == pytest.approx(END - START), "carries across the cut"


@pytest.mark.parametrize("height", [32, 64])
def test_ray_flies_by_the_evening_star_then_circles_the_spire(height):
    show = MusicShow(64, height, random.Random(3))
    actor = RayGlows(show)
    sx, sy = actor.star
    for e in [i * 0.5 for i in range(0, 42)]:  # the prologue
        x, y = actor.at(e)
        assert math.hypot(x - sx, y - sy) < (24 if actor.big else 16)
    px, py = show.spire
    for e in [25.0 + i * 0.5 for i in range(0, 34)]:  # the fanfare, once he's drifted over
        x, y = actor.at(e)
        assert math.hypot(x - px, y - py) <= max(actor.orbit_r) + 2
    xs = [actor.at(e)[0] for e in (25.0, 26.5, 28.0, 29.5)]
    assert len(set(round(x) for x in xs)) > 2, "circles, doesn't sit still"


def test_ray_glow_pulses_by_the_clock():
    actor = RayGlows(MusicShow(64, 64, random.Random(4)))
    p = actor.PULSE_S
    assert actor.glow(p / 4) == pytest.approx(1.0)
    assert actor.glow(3 * p / 4) == pytest.approx(0.55)
    _, _, bright = _play(64, START + p / 4)
    _, _, dim = _play(64, START + 3 * p / 4)
    assert sum(map(sum, bright.values())) > sum(map(sum, dim.values()))


def test_ray_follows_the_clock_not_the_frames():
    _, fast, a = _play(64, START + 23.0, fps=30)
    _, slow, b = _play(64, START + 23.0, fps=7)
    assert fast.elapsed() == pytest.approx(slow.elapsed(), abs=0.15)
    assert fast.at(10.0) == pytest.approx(slow.at(10.0))


def test_ray_draws_nothing_when_inactive():
    show, actor, out = _play(32, START + 5.0)
    assert out
    assert _frame(show, actor, END + 0.1, active=False) == {}
    assert actor.elapsed() == 0.0
