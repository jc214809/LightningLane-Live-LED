import random

import pytest

from display.fireworks.actors.dumbo import DumboFlies
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

SCENE_S = 14.0


def _scene(start=623.0, end=623.0 + SCENE_S):
    return Cue("s", "You'll Be in My Heart", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost",
               ("dumbo",))


def _frame(show, dumbo, cue, t, active=True):
    show.set_cue(cue, t)
    dumbo.follow(active)
    dumbo.step(active)
    out = {}
    dumbo.draw(lambda *a: None, out, active)
    return out


def _play(height, fps, until, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    dumbo, cue = DumboFlies(show), _scene()
    i, out = 0, {}
    while cue.start + i / fps <= cue.start + until:
        out = _frame(show, dumbo, cue, cue.start + i / fps)
        i += 1
    return show, dumbo, cue, out


@pytest.mark.parametrize("height", [32, 64])
def test_dumbo_crosses_the_board_left_to_right_over_his_scene(height):
    show = MusicShow(64, height, random.Random(1))
    dumbo, cue = DumboFlies(show), _scene()
    xs, seen = [], []
    for i in range(int(SCENE_S * 30)):
        out = _frame(show, dumbo, cue, cue.start + i / 30)
        xs.append(dumbo.top_left(dumbo.elapsed())[0])
        if out:
            seen.append((min(x for x, _ in out), max(x for x, _ in out)))
    assert xs[0] == -dumbo.w, "enters from off the left edge"
    assert seen[0][0] == 0 and seen[-1][1] == 63, "seen coming in at the left, going out at the right"
    assert xs == sorted(xs), "always heading right, the way he faces"
    assert not _frame(show, dumbo, cue, cue.end), "gone by the scene's end"


@pytest.mark.parametrize("height", [32, 64])
def test_dumbo_stays_on_the_board_and_swoops(height):
    show = MusicShow(64, height, random.Random(2))
    dumbo, cue = DumboFlies(show), _scene()
    tops = []
    for i in range(int(SCENE_S * 30)):
        out = _frame(show, dumbo, cue, cue.start + i / 30)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
        left, top = dumbo.top_left(dumbo.elapsed())
        assert 0 <= top <= height - dumbo.h, "his whole height stays on the board"
        tops.append(top)
    mid = len(tops) // 2
    if height == 64:  # 64x32 spends its spare rows on his raised ear instead
        assert sum(tops[mid - 15:mid + 15]) / 30 > sum(tops[:30]) / 30 + 2, "lower mid-scene than as he enters"


def test_dumbo_is_his_whole_flying_body_from_the_reference_in_its_own_colours():
    """Flying Dumbo.jpg's body and tail (his ride-reveal sprite has neither), with the paper cleaned away."""
    show = MusicShow(64, 64, random.Random(3))
    dumbo, cue = DumboFlies(show), _scene()
    assert (dumbo.w, dumbo.h) == (47, 28), "1x on both boards; 28 rows fit 64x32 too"
    out = _frame(show, dumbo, cue, cue.start + SCENE_S / 2)
    assert set(out.values()) <= set(DumboFlies.COLORS.values()), "no new colours"
    left, top = (int(round(v)) for v in dumbo.top_left(dumbo.elapsed()))
    body = [(x, y) for (x, y), rgb in out.items() if rgb == DumboFlies.COLORS["s"]]
    assert sum(1 for x, y in body if y > top + 17) > 40, "a body under his head, not just ears and a face"
    for x, y in ((left, top + 27), (left + 46, top + 27), (left + 3, top + 13)):
        assert (x, y) not in out, "no paper left in the corners"


def test_dumbo_glides_up_and_down_by_the_clock():
    show = MusicShow(64, 64, random.Random(4))
    dumbo, cue = DumboFlies(show), _scene()
    _frame(show, dumbo, cue, cue.start)
    half = DumboFlies.BOB_S / 2
    tops = [dumbo.top_left(7.0 + k * half)[1] for k in range(3)]
    assert abs(tops[0] - tops[1]) > 2 and abs(tops[0] - tops[2]) < 1, "down and back up (plus the slow swoop), one glide each BOB_S"


def test_dumbo_follows_the_clock_not_the_frames():
    """A slow board steps fewer frames; he's still where the music says."""
    _, fast, _, fast_out = _play(64, 30, 8.0)
    _, slow, _, slow_out = _play(64, 7, 8.0)
    assert fast.elapsed() == slow.elapsed() == 8.0
    assert fast.top_left(8.0) == slow.top_left(8.0)
    assert fast_out == slow_out


def test_nothing_when_his_scene_is_off():
    show = MusicShow(64, 32, random.Random(5))
    dumbo, cue = DumboFlies(show), _scene()
    _frame(show, dumbo, cue, cue.start + 5)
    assert not _frame(show, dumbo, cue, cue.start + 5.5, active=False)
    assert dumbo.elapsed() == 0.0


def test_dumbo_flaps_both_ears_over_his_hat_and_paddles_his_legs():
    dumbo = DumboFlies(MusicShow(64, 64, random.Random(6)))
    level, up, down = (dumbo.frames[i] for i in (0, 2, 6))
    cells = lambda art, keys: {(x, y) for y, row in enumerate(art) for x, k in enumerate(row) if k in keys}
    pink = "Ii"  # the near ear's insides
    assert min(y for _, y in cells(up, pink)) < min(y for _, y in cells(level, pink)) - 2, "the near ear lifts"
    tip = lambda art: sum(y for x, y in cells(art, pink) if x < 12) / len([1 for x, _ in cells(art, pink) if x < 12])
    assert tip(down) > tip(level) + 1, "and drops"
    far = lambda art: min(y for x, y in cells(art, "BD") if x > 40)
    assert far(up) < far(level), "the far ear lifts too"
    ears = cells(up, "sSKkIiABD")  # wherever an ear lies over the hat in the raised frame
    assert cells(level, "YO") - ears <= cells(up, "YO"), "the hat stays put; the ear only covers it"
    legs = lambda art: cells(art[len(art) - 6:], "sSKkA")
    assert legs(dumbo.frames[1]) != legs(dumbo.frames[5]), "the legs step"
    assert [dumbo.frame(e) for e in (0, DumboFlies.FLAP_S / 4, DumboFlies.FLAP_S)] == [0, 2, 0], "by the clock"


@pytest.mark.parametrize("height", [32, 64])
def test_his_raised_ear_stays_on_the_board(height):
    show = MusicShow(64, height, random.Random(7))
    dumbo, cue = DumboFlies(show), _scene()
    for i in range(int(SCENE_S * 10)):
        out = _frame(show, dumbo, cue, cue.start + i / 10)
        if 8 < dumbo.top_left(dumbo.elapsed())[0] < 64 - dumbo.w - 8 and dumbo.frame(dumbo.elapsed()) == 2:
            pink_top = min((y for (x, y), rgb in out.items() if rgb == DumboFlies.COLORS["I"]), default=None)
            assert pink_top is not None and pink_top >= 0

