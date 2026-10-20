import random

import pytest

from display.fireworks.actors.castle_mouth import CastleSings
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue, Lips

START, END = 514.0, 527.0
TRACK = "0" * 15 + "1" * 15 + "2" * 15  # a second each: shut, half, open


def _scene():
    return Cue("s", "That's What Friends Are For", START, END, ((255, 210, 100),), 0.0, "friends", (),
               frozenset(), "castle", ("castle_sings",))


def _show(height, track=TRACK):
    show = MusicShow(64, height, random.Random(1))
    show.lips = {"castle_sings": Lips(START, 15, track)} if track else {}
    return show, CastleSings(show)


def _at(show, actor, t, active=True):
    show.set_cue(_scene(), t)
    actor.follow(active)
    actor.step(active)
    return show.castle_shape


def _door(shape):
    return [(dx, dy) for dx, dy, kind in shape if kind == "D"]


def _height(shape):
    return max(dy for _, dy, _ in shape) - min(dy for _, dy, _ in shape) + 1


def _width(shape):
    return max(dx for dx, _, _ in shape) - min(dx for dx, _, _ in shape) + 1


@pytest.mark.parametrize("height", [32, 64])
def test_the_doorway_opens_and_the_castle_stretches_with_the_mouth(height):
    show, actor = _show(height)
    shut, half, wide = (list(_at(show, actor, START + s + 0.5)) for s in (0, 1, 2))
    door_rows = [len({dy for _, dy in _door(s)}) for s in (shut, half, wide)]
    assert 0 < door_rows[0] < door_rows[1] < door_rows[2], "the doorway opens"
    assert _height(shut) == show.castle_h and _height(shut) < _height(half) < _height(wide), "taller as it opens"
    assert _width(wide) < _width(shut), "and thinner"


@pytest.mark.parametrize("height", [32, 64])
def test_the_castle_stretches_from_its_base_and_stays_on_the_board(height):
    show, actor = _show(height)
    wide = _at(show, actor, START + 2.5)
    assert max(dy for _, dy, _ in wide) == show.castle_h - 1, "its bottom stays on the ground"
    assert all(0 <= show.castle_x + dx < 64 and 0 <= show.castle_y + dy < height for dx, dy, _ in wide)
    show.set_cue(_scene(), START + 2.5)
    show.step()
    assert show.frame_pixels(), "it draws"


def test_without_a_track_the_mouth_stays_shut():
    show, actor = _show(64, track=None)
    assert _at(show, actor, START + 3.0) is actor.shapes[0]


def test_the_castle_is_itself_again_once_the_scene_is_over():
    show, actor = _show(64)
    _at(show, actor, START + 2.5)
    assert _at(show, actor, END + 0.5, active=False) is None


def test_the_shut_castle_keeps_its_own_outline():
    show, actor = _show(32)
    shut = {(dx, dy) for dx, dy, kind in actor.shapes[0]}
    assert shut == {(dx, dy) for dx, dy, _ in show.castle_pixels}, "only the doorway changes when shut"
