import random

import pytest

from display.animation.characters.mike import MikeReveal
from display.fireworks.actors.mike import MikePeeks
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

MIKE = {MikeReveal.GREEN, MikeReveal.LIGHT, MikeReveal.DARK, MikeReveal.EDGE, MikeReveal.WHITE,
        MikeReveal.IRIS, MikeReveal.PUPIL, MikeReveal.HORN, MikeReveal.MOUTH}


def _scene(start=514.0, end=527.0):
    return Cue("s", "That's What Friends Are For", start, end, ((0, 200, 200),), 0.0, "monsters", (),
               frozenset(), "castle", ("mike",))


def _at(show, mike, cue, e, active=True):
    """Mike's drawing e seconds into the scene, stepping only this one frame."""
    show.set_cue(cue, cue.start + e)
    mike.follow(active)
    mike.step(active)
    out = {}
    mike.draw(None, out, active)
    return out


@pytest.mark.parametrize("height", [32, 64])
def test_mike_peeks_over_the_left_turret_then_the_right_one(height):
    show = MusicShow(64, height, random.Random(1))
    mike = MikePeeks(show)
    cue = _scene()
    (left_x, left_line), (right_x, right_line) = mike.turrets
    assert left_x < show.spire[0] < right_x
    castle = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, _ in show.castle_pixels}
    for e, (x, line) in ((3.0, mike.turrets[0]), (9.5, mike.turrets[1])):
        out = _at(show, mike, cue, e)
        assert out and set(out.values()) <= MIKE
        assert all(0 <= px < 64 and 0 <= py < height for px, py in out), "stays on the board"
        assert max(py for _, py in out) < line, "hidden below the turret's top line: he's behind it"
        assert not set(out) & castle, "the castle covers him"
        xs = [px for px, _ in out]
        assert min(xs) <= x <= max(xs), "over his turret"
        assert MikeReveal.IRIS in out.values(), "his eye clears the roof"


@pytest.mark.parametrize("height", [32, 64])
def test_mike_ducks_down_between_peeks_and_before_the_scene_ends(height):
    show = MusicShow(64, height, random.Random(2))
    mike = MikePeeks(show)
    cue = _scene()
    assert _at(show, mike, cue, 0.0) == {}, "starts hidden"
    assert _at(show, mike, cue, 6.2) == {}, "between peeks"
    assert _at(show, mike, cue, 12.8) == {}, "gone before the scene ends"


def test_mike_blinks_and_grins_wider():
    show = MusicShow(64, 64, random.Random(3))
    mike = MikePeeks(show)
    assert mike.pose(0.6)[1] == 0 and mike.pose(1.15)[1] == 1, "lid shuts mid-blink"
    assert mike.pose(2.0)[2] == 0 and mike.pose(4.0)[2] == 1, "grin widens and stays"
    assert mike.pose(2.0)[0] == -1 and mike.pose(2.4)[0] == 1, "looks left, then right"


def test_mike_follows_the_clock_not_the_frames():
    """A slow board steps fewer frames; he's still where the music says."""
    cue = _scene()
    fast, slow = (MusicShow(64, 64, random.Random(4)) for _ in range(2))
    a, b = MikePeeks(fast), MikePeeks(slow)
    for i in range(30 * 3):
        _at(fast, a, cue, i / 30)
    for i in range(5 * 3):
        _at(slow, b, cue, i / 5)
    assert _at(fast, a, cue, 3.0) == _at(slow, b, cue, 3.0)


def test_mike_draws_nothing_when_his_scene_is_off():
    show = MusicShow(64, 32, random.Random(5))
    mike = MikePeeks(show)
    cue = _scene()
    assert _at(show, mike, cue, 3.0)
    assert _at(show, mike, cue, 3.1, active=False) == {}
    assert mike.since is None
