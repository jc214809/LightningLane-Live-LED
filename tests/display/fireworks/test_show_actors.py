import random

import pytest

from display.animation.characters.genie import GenieReveal
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue
from display.fireworks.show_actors import GenieOrbit, stamp

ART = ["A.", ".B"]
COLORS = {"A": (255, 0, 0), "B": (0, 0, 255)}


def test_stamp_covers_what_is_behind_and_leaves_its_gaps():
    out = {(1, 0): (9, 9, 9), (0, 0): (0, 255, 0)}
    stamp(out, ART, COLORS, 0, 0, 1, 64, 32)
    assert out == {(0, 0): (255, 0, 0), (1, 1): (0, 0, 255), (1, 0): (9, 9, 9)}


def test_stamp_scales_each_cell_and_rounds_its_corner():
    out = {}
    stamp(out, ART, COLORS, 0.6, 0.4, 2, 64, 32)
    assert sorted(out) == [(1, 0), (1, 1), (2, 0), (2, 1), (3, 2), (3, 3), (4, 2), (4, 3)]


def test_stamp_skips_cells_off_the_board():
    out = {}
    stamp(out, ART, COLORS, -1, 31, 1, 64, 32)
    assert out == {}, "A is off the left edge, B off the bottom"
    stamp(out, ART, COLORS, 63, -1, 1, 64, 32)
    assert out == {}, "A is off the top, B off the right"


def _scene(actors, start=100.0, end=127.0):
    return Cue("s", "scene", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", tuple(actors))


def _play(show, cue, until, fps=30, from_t=None):
    """Step the show at fps from from_t (default the cue's start) up to until."""
    i = 0
    t0 = cue.start if from_t is None else from_t
    while t0 + i / fps < until:
        t = t0 + i / fps
        show.set_cue(cue, t)
        show.step()
        i += 1


def _genie_pixels(show):
    colours = set(GenieReveal.COLORS.values())
    return {xy for xy, rgb in show.frame_pixels().items() if rgb in colours}


@pytest.mark.parametrize("height", [32, 64])
def test_genie_forms_at_the_spire_then_circles_it_on_the_board(height):
    show = MusicShow(64, height, random.Random(1))
    cue = _scene(["genie"])
    genie = show.actors["genie"]
    _play(show, cue, cue.start + 0.3)
    assert genie.grow(0.3) == 0, "only smoke at first"
    xs, ys = [], []
    for t in range(3, 27):
        _play(show, cue, cue.start + t, from_t=show.t)
        left, top = genie.top_left(t)
        assert 0 <= left <= 64 - genie.w and 0 <= top <= height - genie.h, "his whole sprite stays on the board"
        xs.append(left + genie.w / 2)
        ys.append(top)
    assert max(xs) - min(xs) > 30, "wide side to side, round the spire"
    assert min(xs) < show.spire[0] < max(xs)
    assert (max(ys) - min(ys) > 10) == (height == 64), "on 64x32 he fills the height: a side-to-side swing"
    assert _genie_pixels(show), "drawn in front of everything"


def test_genie_is_his_ride_reveal_size_on_both_boards():
    assert (GenieOrbit(MusicShow(64, 32)).w, GenieOrbit(MusicShow(64, 32)).h) == (21, 26)
    assert (GenieOrbit(MusicShow(64, 64)).w, GenieOrbit(MusicShow(64, 64)).h) == (21, 28), "1x on 64x64 too"


def test_genie_follows_the_clock_not_the_frames():
    """A slow board steps fewer frames; he's still where the music says."""
    fast, slow = MusicShow(64, 64, random.Random(2)), MusicShow(64, 64, random.Random(2))
    cue = _scene(["genie"])
    _play(fast, cue, cue.start + 10, fps=30)
    _play(slow, cue, cue.start + 10, fps=7)
    fast.set_cue(cue, cue.start + 10)
    slow.set_cue(cue, cue.start + 10)
    assert fast.actors["genie"].top_left(fast.actors["genie"].elapsed()) == \
        slow.actors["genie"].top_left(slow.actors["genie"].elapsed())


def test_genie_vanishes_in_a_puff_when_his_scene_ends():
    show = MusicShow(64, 32, random.Random(3))
    cue = _scene(["genie"])
    _play(show, cue, cue.end)
    after = _scene([], start=cue.end, end=cue.end + 10)
    show.set_cue(after, cue.end)
    before = len(show.actors["genie"].puffs)
    show.step()
    assert len(show.actors["genie"].puffs) > before, "a puff where he was"
    assert not _genie_pixels(show)
    _play(show, after, cue.end + 3, from_t=cue.end)
    assert not show.actors["genie"].puffs, "and the smoke clears"
