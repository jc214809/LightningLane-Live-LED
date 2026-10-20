import random

import pytest

from display.fireworks.actors.lantern_boat import LANTERN_RGB, LanternBoat
from display.fireworks.music_show import LANTERN_RGB as SHOW_LANTERN_RGB, MusicShow
from display.fireworks.score import Cue

START, MID, END = 668.0, 697.0, 724.0


def _scenes():
    song = Cue("s", "I See the Light", START, MID, ((255, 255, 255),), 0.35, "blue", (), frozenset(),
               "ghost", ("lantern_boat",))
    lanterns = Cue("s", "I See the Light (lanterns)", MID, END, ((255, 211, 107),), 0.15, "blue", (),
                   frozenset({"lanterns"}), "ghost", ("lantern_boat",))
    return song, lanterns


def _cue_at(t):
    song, lanterns = _SCENES
    return song if t < MID else lanterns


_SCENES = _scenes()


def _frame(show, actor, t, active=True):
    show.set_cue(_cue_at(t), t)
    actor.follow(active)
    actor.step(active)
    out = {}

    def put(x, y, rgb):
        if 0 <= x < show.width and 0 <= y < show.height:
            out[(x, y)] = rgb
    actor.draw(put, out, active)
    return out


def _play(height, until, fps=30, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    actor = LanternBoat(show)
    i, out = 0, {}
    while START + i / fps <= until:
        out = _frame(show, actor, START + i / fps)
        i += 1
    return show, actor, out


def _boat(out):
    colours = set(LanternBoat.COLORS.values())
    return {xy for xy, rgb in out.items() if rgb in colours}


def test_her_lantern_is_the_shows_lantern_colour():
    assert LANTERN_RGB == SHOW_LANTERN_RGB


@pytest.mark.parametrize("height", [32, 64])
def test_boat_drifts_in_from_the_left_and_settles_at_the_castle(height):
    show = MusicShow(64, height, random.Random(2))
    actor = LanternBoat(show)
    assert (actor.w, actor.h) == ((16, 8) if height == 32 else (32, 16))
    lefts = []
    for i in range(0, int((END - START) * 10) + 1):
        out = _frame(show, actor, START + i / 10)
        left, top = actor.top_left(actor.elapsed())
        assert 0 <= top <= height - actor.h, "never off the top or bottom"
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out), "on the board"
        lefts.append(left)
    assert lefts[0] <= -actor.w + 1, "starts off the left edge"
    assert lefts == sorted(lefts), "always drifting right, never back"
    middle = show.castle_x + show.castle_w / 2
    assert abs(lefts[-1] + actor.w / 2 - middle) <= 1, "at rest in front of the castle's middle"
    assert actor.top_left(actor.SETTLE_S)[0] == pytest.approx(lefts[-1]), "settled by mid-song"
    assert actor.top_left(actor.SETTLE_S)[1] + actor.h >= height - actor.rock - 1, "at the bottom"
    _, _, mid = _play(height, START + 20)
    assert len(_boat(mid)) > 50 * actor.scale ** 2, "the whole boat on the board"


def test_boat_rocks_by_the_clock():
    actor = LanternBoat(MusicShow(64, 32, random.Random(3)))
    tops = {round(actor.top_left(e)[1]) for e in (20.0, 20.85, 21.7, 22.55)}
    assert len(tops) > 1, "rocks up and down"
    assert max(tops) - min(tops) <= 2 * actor.rock, "gently"


@pytest.mark.parametrize("height", [32, 64])
def test_her_lantern_lights_late_and_rises_from_the_boat(height):
    actor = LanternBoat(MusicShow(64, height, random.Random(4)))
    assert actor.lantern_at(actor.HOLD_S - 0.1) is None, "not before she lights it"
    held = actor.lantern_at(actor.RELEASE_S - 0.1)
    left, top = actor.top_left(actor.RELEASE_S - 0.1)
    assert left <= held[0] <= left + actor.w and held[1] <= top + actor.h, "in the boat"
    ys = [actor.lantern_at(actor.RELEASE_S + k)[1] for k in range(0, 12)]
    assert ys == sorted(ys, reverse=True), "rising"
    assert ys[0] - ys[-1] > height * 0.6, "well up the sky by the end"
    _, _, out = _play(height, START + actor.RELEASE_S + 3)
    assert any(rgb == LANTERN_RGB and y < height - actor.h - actor.rock for (x, y), rgb in out.items()), \
        "drawn above the boat"


def test_boat_draws_nothing_when_inactive():
    show, actor, _ = _play(64, START + 10)
    assert _frame(show, actor, END + 0.1, active=False) == {}


def test_boat_follows_the_clock_not_the_frames():
    _, fast, a = _play(64, START + 45.0, fps=30)
    _, slow, b = _play(64, START + 45.0, fps=7)
    assert fast.elapsed() == pytest.approx(slow.elapsed())
    assert fast.top_left(fast.elapsed()) == pytest.approx(slow.top_left(slow.elapsed()))
    assert fast.lantern_at(fast.elapsed()) == pytest.approx(slow.lantern_at(slow.elapsed()))
