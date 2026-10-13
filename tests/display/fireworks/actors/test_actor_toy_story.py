import random

import pytest

from display.animation.characters.aliens import AliensToysReveal
from display.animation.characters.buzz import BuzzReveal
from display.fireworks.actors.toy_story import BuzzAndWoody
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue


def _scene(start=453.0, end=459.0):
    return Cue("s", "scene", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", ("buzz_woody",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _buzz_xs(out):
    """Columns of Buzz's suit (his purple wings and white suit both, not Woody's or the trail's)."""
    buzz = {BuzzReveal.colors["P"], BuzzReveal.colors["D"]}
    return [x for (x, _), rgb in out.items() if rgb in buzz]


@pytest.mark.parametrize("height", [32, 64])
def test_buzz_crosses_left_to_right_while_woody_waves_on_the_ground(height):
    show = MusicShow(64, height, random.Random(1))
    actor, cue = BuzzAndWoody(show), _scene()
    centres = []
    for i in range(1, 12):
        t = cue.start + i * 0.5
        out = _frame(show, actor, cue, t)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out), "stays on the board"
        xs = _buzz_xs(out)
        if xs:
            centres.append(sum(xs) / len(xs))
        left, top = actor.buzz_top_left(actor.elapsed())
        assert top + actor.buzz_h <= show.castle_y + show.castle_h // 2, "Buzz is in the sky"
        wx, wy = actor.woody_at
        assert wy + actor.woody_h == height, "Woody stands on the ground"
        assert wx + actor.woody_w <= show.castle_x + 5, "beside the castle, on its left"
        assert out.get((wx + 5, wy + 6)) == AliensToysReveal.colors["O"], "Woody's face is drawn"
    assert len(centres) >= 8 and centres == sorted(centres), "Buzz flies left to right"
    assert centres[0] < 16 and centres[-1] > 48, "across the whole sky"
    assert actor.buzz_top_left(0)[0] + actor.buzz_w <= 0 and actor.buzz_top_left(6)[0] >= 64, "off edge to off edge"


def test_they_are_their_ride_art_size_on_both_boards():
    small, big = BuzzAndWoody(MusicShow(64, 32)), BuzzAndWoody(MusicShow(64, 64))
    assert (small.buzz_w, small.buzz_h) == (15, 13), "Buzz's big fly-by art, 1x on 64x32"
    assert (big.buzz_w, big.buzz_h) == (22, 18), "his small one doubled on 64x64, as on his ride screen"
    assert (small.woody_w, small.woody_h) == (big.woody_w, big.woody_h) == (14, 18), "Woody 1x on both"


def test_woody_waves_by_the_clock():
    actor = BuzzAndWoody(MusicShow(64, 32))
    poses = {tuple(actor.woody_pose(i * 0.1)) for i in range(12)}
    assert len(poses) == 2, "his arm swings between two poses"
    assert actor.woody_pose(0.0) != actor.woody_pose(BuzzAndWoody.WAVE_S)


def test_they_follow_the_clock_not_the_frames():
    cue = _scene()
    seen = []
    for fps in (30, 7):
        show = MusicShow(64, 64, random.Random(2))
        actor = BuzzAndWoody(show)
        i = 0
        while cue.start + i / fps < cue.start + 4:
            _frame(show, actor, cue, cue.start + i / fps)
            i += 1
        seen.append(_frame(show, actor, cue, cue.start + 4))
    assert seen[0] == seen[1]


def test_nothing_is_drawn_when_inactive():
    show = MusicShow(64, 32, random.Random(3))
    actor, cue = BuzzAndWoody(show), _scene()
    _frame(show, actor, cue, cue.start + 2)
    assert _frame(show, actor, cue, cue.start + 6.5, active=False) == {}
