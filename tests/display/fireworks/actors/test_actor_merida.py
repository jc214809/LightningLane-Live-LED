import random

import pytest

from display.fireworks.actors.merida import MeridaShoots
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue, Lips

START, END = 268.0, 303.0  # Touch the Sky


def _scene():
    return Cue("s", "Touch the Sky", START, END, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", ("merida",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _at(t, height=64, lips=None):
    show = MusicShow(64, height, random.Random(1), lips)
    actor = MeridaShoots(show)
    _frame(show, actor, _scene(), START)
    return actor, _frame(show, actor, _scene(), t)


def _her(out):
    return {xy for xy, rgb in out.items() if rgb in MeridaShoots.COLORS.values()}


def test_merida_rises_at_the_bottom_left_and_stands_there():
    _, early = _at(START + 0.1)
    actor, standing = _at(START + 5)
    her = _her(standing)
    assert len(_her(early)) < len(her), "still rising"
    assert max(y for _, y in her) == 63 and min(x for x, _ in her) == 0, "bottom left"
    assert max(x for x, _ in her) < 26, "left of the castle's middle"
    assert all(0 <= x < 64 and 0 <= y < 64 for x, y in standing)
    _, gone = _at(END - 0.001)
    assert not _her(gone), "sunk away by her scene's end"


def test_on_64x32_she_stays_off():
    _, out = _at(START + 5, height=32)
    assert out == {}
    _, shot = _at(START + MeridaShoots.HIT_S - 0.3, height=32)
    assert shot == {}


def test_she_mouths_her_line_by_the_clock():
    track = "0" * 15 + "1" * 15 + "2" * 15  # a second each of closed, half, open
    lips = {"merida": Lips(START + 5, 15.0, track)}
    actor = None
    mouths = []
    for t in (5.5, 6.5, 7.5):
        actor, out = _at(START + t, lips=lips)
        mouths.append({xy for xy, rgb in out.items() if rgb == MeridaShoots.COLORS["D"]})
    assert len(mouths[0]) == 0 < len(mouths[1]) < len(mouths[2]), "shut (her smile), then half, then open"
    _, smiling = _at(START + 5.5, lips=lips)
    assert MeridaShoots.COLORS["m"] in smiling.values(), "a closed smile"


def test_on_touch_the_sky_her_arrow_hits_the_bullseye_and_it_shatters():
    cx, cy = MeridaShoots.TARGET
    gold = MeridaShoots.RINGS[0][1]
    _, before = _at(START + MeridaShoots.TARGET_S - 0.1)
    assert (cx, cy) not in before, "no target before its burst"
    _, hanging = _at(START + MeridaShoots.LOOSE_S - 0.1)
    r, g, b = hanging[(cx, cy)]
    assert r > 150 and g > 3 * b, "its gold centre (twinkling)"
    actor, flying = _at(START + (MeridaShoots.LOOSE_S + MeridaShoots.HIT_S) / 2)
    (x, y), _ = actor.arrow_at(actor.elapsed())
    assert actor.nock[0] < x < cx and flying.get((round(x), round(y))) == MeridaShoots.TIP, "in flight, toward it"
    actor, hit = _at(START + MeridaShoots.HIT_S - 0.01)
    (x, y), _ = actor.arrow_at(actor.elapsed())
    assert abs(x - cx) <= 1 and abs(y - cy) <= 1, "it strikes the centre"
    _, shattered = _at(START + MeridaShoots.HIT_S + 0.4)
    ring = {(x, y) for x in range(cx - 4, cx + 5) for y in range(cy - 4, cy + 5)}
    assert gold not in [shattered.get(xy) for xy in ring], "the target's gone"
    assert any(abs(x - cx) > 4 or abs(y - cy) > 4 for x, y in shattered if (x, y) not in _her(shattered)), \
        "its sparks fly out"
    _, after = _at(START + MeridaShoots.HIT_S + MeridaShoots.SHATTER_S + 0.1)
    assert set(after) == set(_at(START + 20)[1]), "then only Merida again"


def test_merida_follows_the_clock_not_the_frames():
    frames = []
    for fps in (30, 7):
        show = MusicShow(64, 64, random.Random(2))
        actor, cue = MeridaShoots(show), _scene()
        i = 0
        while START + i / fps <= START + MeridaShoots.LOOSE_S + 0.4:
            out = _frame(show, actor, cue, START + i / fps)
            i += 1
        frames.append(_frame(show, actor, cue, START + MeridaShoots.LOOSE_S + 0.4))
    assert frames[0] == frames[1]


def test_merida_draws_nothing_when_inactive():
    show = MusicShow(64, 64, random.Random(3))
    actor = MeridaShoots(show)
    assert _frame(show, actor, _scene(), START + 5, active=False) == {}
