import random

import pytest

from display.animation.characters.walle import WallEReveal
from display.fireworks.actors.walle import WallEFloats
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, END = 607.0, 623.0


def _scene():
    return Cue("s", "Can You Feel the Love Tonight", START, END, ((255, 0, 0),), 0.0, None, (), frozenset(),
               "ghost", ("walle",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _play(height, until, fps=30, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    actor = WallEFloats(show)
    cue = _scene()
    i, out = 0, {}
    while START + i / fps <= until:
        out = _frame(show, actor, cue, START + i / fps)
        i += 1
    return show, actor, out


def _him(out):
    colours = set(WallEReveal.COLORS.values())
    return {xy for xy, rgb in out.items() if rgb in colours}


@pytest.mark.parametrize("height", [32, 64])
def test_walle_floats_across_on_the_board_from_left_to_right(height):
    show = MusicShow(64, height, random.Random(2))
    actor = WallEFloats(show)
    assert (actor.w, actor.h) == (20, 20), "his ride-reveal size, 1x on both boards"
    cue = _scene()
    xs = []
    for i in range(0, int((END - START) * 10) + 1):
        out = _frame(show, actor, cue, START + i / 10)
        left, top = actor.top_left(actor.elapsed())
        assert 0 <= top <= height - actor.h, "never off the top or bottom"
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
        xs.append(left)
    assert xs[0] <= -actor.w + 1, "starts off the left edge"
    assert xs[-1] >= 64, "off the right edge by the scene's end"
    assert xs == sorted(xs), "always drifting right"
    _, _, mid = _play(height, START + 9.5)
    assert len(_him(mid)) > 150, "his whole sprite mid-crossing"


def test_walle_bobs_and_arcs():
    actor = WallEFloats(MusicShow(64, 64, random.Random(3)))
    tops = [actor.top_left(e)[1] for e in (0.0, 9.5, 19.0)]
    assert tops[1] < tops[0] - 5 and tops[1] < tops[2] - 5, "rises toward the middle of the crossing"
    assert actor.top_left(0.65)[1] != actor.top_left(1.95)[1], "bobs"


def test_walle_squirts_specks_behind_him():
    show, actor, out = _play(64, START + 0.3)
    left, _ = actor.top_left(actor.elapsed())
    assert actor.specks and all(s[0] < left for s in actor.specks), "behind him, to his left"


def test_walle_draws_nothing_when_inactive_and_his_specks_fade():
    show, actor, _ = _play(64, START + 10.3)
    cue = _scene()
    out = _frame(show, actor, cue, END + 0.1, active=False)
    assert not _him(out)
    for i in range(30):
        out = _frame(show, actor, cue, END + 0.2 + i / 30, active=False)
    assert out == {} and not actor.specks


def test_walle_follows_the_clock_not_the_frames():
    _, fast, _ = _play(64, START + 7.0, fps=30)
    _, slow, _ = _play(64, START + 7.0, fps=7)
    assert fast.elapsed() == pytest.approx(slow.elapsed())
    assert fast.top_left(fast.elapsed()) == pytest.approx(slow.top_left(slow.elapsed()))
