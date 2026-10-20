import random

import pytest

from display.animation.characters.ralph import RalphReveal
from display.fireworks.actors.ralph import RalphSmashes
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue


S, E = RalphSmashes.START_S, RalphSmashes.END_S


def _scene(start=473.3, end=514.0):
    return Cue("s", "Friendship mash-up", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", ())


def _frame(height, at, fps=30, seed=1, active=True):
    """Step a fresh Ralph at fps from the scene's start to `at` seconds in; his pixels then."""
    show = MusicShow(64, height, random.Random(seed))
    ralph = RalphSmashes(show)
    cue = _scene()
    i = 0
    while i / fps < at:
        show.set_cue(cue, cue.start + i / fps)
        ralph.follow(True)
        ralph.step(True)
        i += 1
    show.set_cue(cue, cue.start + at)
    ralph.follow(active)
    ralph.step(active)
    out = {}
    ralph.draw(lambda *a: None, out, active)
    return ralph, out


@pytest.mark.parametrize("height", [32, 64])
def test_ralph_is_drawn_only_in_his_window(height):
    assert not _frame(height, S - 0.5)[1]
    assert _frame(height, S + 2.0)[1]
    assert not _frame(height, E + 0.2)[1]
    assert not _frame(height, 30.0)[1]


@pytest.mark.parametrize("height", [32, 64])
def test_ralph_stays_on_the_board_and_is_his_reveal_size(height):
    ralph = RalphSmashes(MusicShow(64, height, random.Random(1)))
    assert (ralph.w, ralph.h) == (25, 34)
    assert ralph.raised is (RalphReveal.UP_ART if height == 64 else RalphReveal.SHOULDER_ART)
    for at in [0.5, 2.0, 3.3, 4.5, 5.5, 5.9]:
        out = _frame(height, S + at)[1]
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)


@pytest.mark.parametrize("height", [32, 64])
def test_ralph_walks_in_then_stands_at_the_bottom_centre(height):
    ralph = RalphSmashes(MusicShow(64, height))
    assert ralph.left_top(0.0)[0] == -25
    assert ralph.left_top(1.0) == ralph.left_top(3.0) == (ralph.mid, ralph.ground)
    assert ralph.left_top(E - S - 0.1)[1] > ralph.ground, "drops away at the end"


@pytest.mark.parametrize("height", [32, 64])
def test_bricks_fall_onto_his_fists_and_burst(height):
    ralph = RalphSmashes(MusicShow(64, height, random.Random(4)))
    hit, left, colors, _ = ralph.bricks[0]
    assert ralph.swinging(hit) and not ralph.swinging(hit - 0.5)
    falling = _frame(height, S + hit - 0.1, seed=4)[1]
    assert falling.get((left, int(ralph.land_top) + 1)) in colors.values() or \
        any(rgb in colors.values() for (x, y), rgb in falling.items() if left <= x < left + 3 and y < ralph.land_top + 2)
    assert len(ralph.bricks) >= 3


def test_ralph_follows_the_clock_not_the_frames():
    for at in [0.4, 2.75, 4.1, 5.6]:
        assert _frame(64, S + at, fps=30, seed=2)[1] == _frame(64, S + at, fps=7, seed=2)[1]


def test_nothing_when_inactive():
    assert not _frame(64, S + 2.0, active=False)[1]
