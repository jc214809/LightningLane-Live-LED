import random

import pytest

from display.fireworks.actors.memory_orbs import EMOTIONS, MemoryOrbs
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue


S, E = MemoryOrbs.START_S, MemoryOrbs.END_S


def _scene(start=473.3, end=514.0):
    return Cue("s", "Friendship mash-up", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "castle", ())


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
    assert _frame(height, S + 3.0)[1]
    assert not _frame(height, E)[1]


@pytest.mark.parametrize("height", [32, 64])
def test_the_orbs_fit_inside_the_castle_and_leave_the_doorway(height):
    orbs, _ = _frame(height, S)
    show = orbs.show
    inside = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind != "D"}
    n = orbs.size
    assert n == (3 if height == 64 else 2)
    assert len(orbs.orbs) > 20, "enough to fill it"
    for left, top, rgb, _ in orbs.orbs:
        assert rgb in EMOTIONS
        assert all((left + i, top + j) in inside for i in range(n) for j in range(n))
    assert len({rgb for *_, rgb, _ in orbs.orbs}) == len(EMOTIONS), "all five emotions"


@pytest.mark.parametrize("height", [32, 64])
def test_the_castle_fills_from_its_base_up(height):
    orbs, early = _frame(height, S + MemoryOrbs.FILL_S * 0.3)
    _, full = _frame(height, S + MemoryOrbs.FILL_S + 0.1)
    landed = [o for o in orbs.orbs if o[3] <= MemoryOrbs.FILL_S * 0.3]
    assert landed and max(top for _, top, _, _ in landed) == max(top for _, top, _, _ in orbs.orbs), "bottom first"
    assert len(early) < len(full)
    assert min(y for _, y in full) == min(top for _, top, _, _ in orbs.orbs), "up to the top by the end of the fill"
    lands = [o[3] for o in orbs.orbs]
    tops = [o[1] for o in orbs.orbs]
    assert all(tops[i] >= tops[i + 1] for i in range(len(tops) - 1)) and lands == sorted(lands)


@pytest.mark.parametrize("height", [32, 64])
def test_orbs_stay_on_the_board(height):
    for at in (S + 0.2, S + 3.0, S + MemoryOrbs.FILL_S):
        _, out = _frame(height, at)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)


def test_orbs_fade_by_the_end_before_mike_and_sulley():
    _, full = _frame(64, E - MemoryOrbs.FADE_S - 0.1)
    _, fading = _frame(64, E - MemoryOrbs.FADE_S / 2)
    bright = lambda px: sum(sum(rgb) for rgb in px.values())  # noqa: E731
    assert 0 < bright(fading) < bright(full)
    assert S + MemoryOrbs.FILL_S < E - MemoryOrbs.FADE_S, "full before it fades"


def test_orbs_follow_the_clock_not_the_frames():
    assert _frame(64, S + 2.0, fps=30)[1] == _frame(64, S + 2.0, fps=7)[1]


def test_nothing_when_inactive():
    assert _frame(64, S + 3.0, active=False)[1] == {}
