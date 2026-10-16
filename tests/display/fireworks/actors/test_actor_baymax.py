import random

import pytest

from display.animation.characters.baymax import BaymaxReveal
from display.fireworks.actors.baymax import BaymaxInflates
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

COLOURS = {BaymaxReveal.WHITE, BaymaxReveal.SHADE, BaymaxReveal.EDGE, BaymaxReveal.DARK}


S, E = BaymaxInflates.START_S, BaymaxInflates.END_S


def _scene(start=473.3, end=514.0):
    return Cue("s", "Friendship mash-up", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", ())


def _frame(height, at, fps=30, active=True):
    """Step a fresh Baymax at fps from the scene's start to `at` seconds in; his pixels then."""
    show = MusicShow(64, height, random.Random(1))
    baymax = BaymaxInflates(show)
    cue = _scene()
    i = 0
    while i / fps < at:
        show.set_cue(cue, cue.start + i / fps)
        baymax.follow(True)
        baymax.step(True)
        i += 1
    show.set_cue(cue, cue.start + at)
    baymax.follow(active)
    baymax.step(active)
    out = {}
    baymax.draw(lambda *a: None, out, active)
    return out


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_is_drawn_only_in_his_window(height):
    assert not _frame(height, S - 0.5)
    assert _frame(height, S + 3.0)
    assert not _frame(height, E + 0.1)


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_inflates_from_the_bottom_on_the_board_in_his_colours(height):
    early, full = _frame(height, S + 0.2), _frame(height, S + 2.0)
    assert len(early) < len(full)
    assert max(y for _, y in full) == height - 1, "his base on the bottom edge"
    for out in (early, full, _frame(height, E - 0.4)):
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
        assert set(out.values()) <= COLOURS


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_deflates_in_his_last_moments(height):
    assert len(_frame(height, E - 0.2)) < len(_frame(height, E - 2.0))


def test_baymax_waves_while_he_is_up():
    baymax = BaymaxInflates(MusicShow(64, 64)).baymax
    assert any(abs(baymax.wave(t / 10)) > 0.5 for t in range(14, 30))
    assert any(abs(baymax.wave(t / 10)) > 0.5 for t in range(36, 51)), "and again later"


def test_baymax_follows_the_clock_not_the_frames():
    for at in [0.3, 2.45, 6.0]:
        assert _frame(64, S + at, fps=30) == _frame(64, S + at, fps=7)


def test_nothing_when_inactive():
    assert not _frame(64, S + 3.0, active=False)
