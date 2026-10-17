import random

import pytest

from display.fireworks.actors.monsters import MikeAndSulley
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, END = 473.3, 514.0  # the friendship mash-up
SULLEY = set(MikeAndSulley.SULLEY_COLORS.values())
MIKE = set(MikeAndSulley.MIKE_COLORS.values())


def _scene():
    return Cue("s", "Friendship mash-up", START, END, ((255, 0, 0),), 0.0, "monsters", (), frozenset(),
               "castle", ("mike_sulley",))


def _at(show, actor, cue, e, active=True):
    """Their drawing e seconds into the scene, stepping only this one frame."""
    show.set_cue(cue, cue.start + e)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(None, out, active)
    return out


def _up(height, e=MikeAndSulley.START_S + 1.0):
    show = MusicShow(64, height, random.Random(1))
    actor = MikeAndSulley(show)
    return show, actor, _at(show, actor, _scene(), e)


@pytest.mark.parametrize("name", ["SULLEY_ART", "SULLEY_SMALL_ART", "MIKE_ART", "MIKE_SMALL_ART"])
def test_every_sprite_is_square_edged_and_coloured(name):
    art = getattr(MikeAndSulley, name)
    colors = MikeAndSulley.SULLEY_COLORS if name.startswith("SULLEY") else MikeAndSulley.MIKE_COLORS
    assert len({len(row) for row in art}) == 1
    assert {k for row in art for k in row} - {"."} <= set(colors)


@pytest.mark.parametrize("height", [32, 64])
def test_they_stand_side_by_side_over_the_gate(height):
    show, actor, out = _up(height)
    assert out and set(out.values()) <= SULLEY | MIKE
    assert all(0 <= x < 64 and 0 <= y < height for x, y in out), "stays on the board"
    assert max(y for _, y in out) == height - 2, "feet just above the board's last row"
    sulley = [x for (x, _), rgb in out.items() if rgb in SULLEY - MIKE]
    mike = [x for (x, _), rgb in out.items() if rgb in MIKE - SULLEY]
    assert max(sulley) < min(mike), "Sulley on the left, Mike on the right"
    door = [show.castle_x + dx for dx, _, kind in show.castle_pixels if kind == "D"]
    assert min(sulley) < min(door) and max(mike) > max(door), "the pair spans the gate"


def test_mike_stands_a_head_shorter_than_sulley_on_both_boards():
    for sulley, mike in ((MikeAndSulley.SULLEY_ART, MikeAndSulley.MIKE_ART),
                         (MikeAndSulley.SULLEY_SMALL_ART, MikeAndSulley.MIKE_SMALL_ART)):
        assert len(mike) < len(sulley)


@pytest.mark.parametrize("height", [32, 64])
def test_they_pop_up_out_of_the_gate_and_sink_back_only_in_their_window(height):
    show = MusicShow(64, height, random.Random(1))
    actor = MikeAndSulley(show)
    cue = _scene()
    s = MikeAndSulley
    assert _at(show, actor, cue, s.START_S - 0.5) == {}, "not before their moment"
    half = _at(show, actor, cue, s.START_S + s.POP_S / 3)
    full = _at(show, actor, cue, s.START_S + 1.0)
    assert 0 < len(half) < len(full), "still rising"
    assert max(y for _, y in half) <= height - 2, "they come up out of their feet's line, not the board's edge"
    assert _at(show, actor, cue, s.END_S + 0.1) == {}, "gone after it"
    assert _at(show, actor, cue, s.START_S + 1.0, active=False) == {}


@pytest.mark.parametrize("height", [32, 64])
def test_they_each_blink(height):
    s = MikeAndSulley
    white = (242, 250, 247), (248, 249, 244)  # Sulley's and Mike's
    _, _, open_eyes = _up(height, s.START_S + 1.0)
    for blink, rgb in ((s.SULLEY_BLINKS[0], white[0]), (s.MIKE_BLINKS[0], white[1])):
        _, _, shut = _up(height, s.START_S + blink + s.BLINK_S / 2)
        assert sum(v == rgb for v in shut.values()) < sum(v == rgb for v in open_eyes.values())


@pytest.mark.parametrize("height", [32, 64])
def test_mikes_raised_hand_rocks_as_he_waves(height):
    s = MikeAndSulley
    frames = [_up(height, s.START_S + s.WAVE[0] + (i + 0.5) * s.WAVE_S)[2] for i in range(2)]
    assert frames[0] != frames[1]
    _, _, still = _up(height, s.START_S + s.WAVE[1] + 0.2)
    _, _, also_still = _up(height, s.START_S + s.WAVE[1] + 0.5)
    assert still == also_still, "no wave after it"


def test_they_follow_the_clock_not_the_frames():
    s = MikeAndSulley
    frames = {}
    for fps in (30, 7):
        show = MusicShow(64, 64, random.Random(1))
        actor = MikeAndSulley(show)
        cue = _scene()
        for i in range(int((s.START_S + 2.0) * fps)):
            _at(show, actor, cue, i / fps)
        frames[fps] = _at(show, actor, cue, s.START_S + 2.0)
    assert frames[30] == frames[7]
