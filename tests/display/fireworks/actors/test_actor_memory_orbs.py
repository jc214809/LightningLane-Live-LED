import random

import pytest

from display.fireworks.actors.memory_orbs import MemoryOrbs
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue


S, E = MemoryOrbs.START_S, MemoryOrbs.END_S


def _scene(start=473.3, end=514.0):
    return Cue("s", "Friendship mash-up", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", ())


def _frame(height, at, fps=30, seed=1, active=True):
    """Step fresh orbs at fps from the scene's start to `at` seconds in; their pixels then."""
    show = MusicShow(64, height, random.Random(seed))
    orbs = MemoryOrbs(show)
    cue = _scene()
    i = 0
    while i / fps < at:
        show.set_cue(cue, cue.start + i / fps)
        orbs.follow(True)
        orbs.step(True)
        i += 1
    show.set_cue(cue, cue.start + at)
    orbs.follow(active)
    orbs.step(active)
    out = {}
    orbs.draw(lambda *a: None, out, active)
    return orbs, out


@pytest.mark.parametrize("height", [32, 64])
def test_orbs_are_drawn_only_in_their_window(height):
    assert not _frame(height, S - 0.1)[1]
    assert _frame(height, S + 5.0)[1]
    assert not _frame(height, E)[1]


@pytest.mark.parametrize("height", [32, 64])
def test_orbs_stay_on_the_board(height):
    orbs = _frame(height, 0.0)[0]
    assert orbs.r == (5 if height == 64 else 3)
    for at in [0.2, 1.5, 4.0, 4.5, 6.0, 8.0, 9.4]:
        out = _frame(height, S + at)[1]
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)


@pytest.mark.parametrize("height", [32, 64])
def test_orbs_roll_in_from_opposite_sides_meet_and_float_up(height):
    orbs = _frame(height, 0.0)[0]
    (jx0, jy0), (sx0, _) = orbs.centres(0.0)
    (jx1, _), (sx1, _) = orbs.centres(2.0)
    (jx2, _), (sx2, _) = orbs.centres(5.0)
    assert jx0 < 0 and sx0 > 63, "both start off the board"
    assert jx0 < jx1 < jx2 and sx0 > sx1 > sx2, "Joy from the left, Sadness from the right"
    assert sx2 - jx2 == pytest.approx(2 * orbs.r + 1), "touching in the middle"
    assert orbs.gap(4.4) > orbs.gap(5.0), "bump apart then settle"
    assert jy0 == orbs.ground
    assert orbs.centres(8.0)[0][1] < jy0 - height * 0.3, "float up together"
    out = _frame(height, S + 2.0)[1]
    left = [rgb for (x, _), rgb in out.items() if x < 32]
    right = [rgb for (x, _), rgb in out.items() if x >= 32]
    yellow = lambda rgb: rgb[0] > 150 and rgb[1] > 100 and rgb[2] < 80
    blue = lambda rgb: rgb[2] > 150 and rgb[0] < 80
    assert any(map(yellow, left)) and not any(map(blue, left)), "Joy on the left"
    assert any(map(blue, right)) and not any(map(yellow, right)), "Sadness on the right"


def test_orbs_fade_by_the_end():
    bright = max(max(rgb) for rgb in _frame(64, S + 5.0)[1].values())
    late = max(max(rgb) for rgb in _frame(64, E - 0.3)[1].values())
    assert late < bright * 0.2


def test_orbs_follow_the_clock_not_the_frames():
    for at in [0.4, 3.75, 4.3, 7.1, 9.1]:
        assert _frame(64, S + at, fps=30)[1] == _frame(64, S + at, fps=7)[1]


def test_nothing_when_inactive():
    assert not _frame(64, S + 5.0, active=False)[1]
