import random

import pytest

from display.fireworks.actors.canoe import CanoeSails
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, END = 370.0, 398.0  # How Far I'll Go (climax): the canoe's only scene


def _climax():
    return Cue("s", "How Far I'll Go (climax)", START, END, ((255, 0, 0),), 0.0, None, (), frozenset(), "off",
               ("canoe",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _play(height, until, fps=30, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    actor = CanoeSails(show)
    cue = _climax()
    i, out = 0, {}
    while START + i / fps <= until:
        t = START + i / fps
        out = _frame(show, actor, cue, t)
        i += 1
    return show, actor, out


def _canoe(out):
    """The canoe's pixels, with Moana standing in it on 64x64."""
    colours = set(CanoeSails.COLORS.values()) | set(CanoeSails.BIG_COLORS.values()) | set(CanoeSails.MOANA_COLORS.values())
    return {xy for xy, rgb in out.items() if rgb in colours}


@pytest.mark.parametrize("height", [32, 64])
def test_canoe_floats_on_the_water_line(height):
    show, actor, out = _play(height, START + 14.0)
    surface = show.castle_y + show.castle_h * 0.6  # show_effects.Water at full
    bottom = max(y for _, y in _canoe(out))
    assert abs(bottom - surface) <= 1 + actor.scale, "hull's underside rides on the surface"
    assert len(_canoe(out)) > 60 * actor.scale ** 2, "the whole canoe mid-crossing"


@pytest.mark.parametrize("height", [32, 64])
def test_canoe_sails_left_to_right_on_the_board(height):
    show = MusicShow(64, height, random.Random(2))
    actor = CanoeSails(show)
    cue = _climax()
    xs = []
    for i in range(int((END - START) * 10)):
        t = START + i / 10
        out = _frame(show, actor, cue, t)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
        at = actor.top_left(actor.elapsed())
        if at is not None:
            assert 0 <= at[1] <= height - actor.h + actor.scale
            xs.append(at[0])
    assert xs[0] <= -actor.w + 1, "enters off the left edge as the castle goes"
    assert xs[-1] >= 64 - 1, "leaves off the right edge"
    assert xs == sorted(xs), "one crossing, always sailing right"
    _, _, mid = _play(height, START + 14)
    assert len(_canoe(mid)) > 60 * actor.scale ** 2, "mid-board halfway through"
    _, _, last = _play(height, END - 0.05)
    assert not _canoe(last), "gone by 398 s"


def test_canoe_bobs_by_the_clock():
    actor = CanoeSails(MusicShow(64, 64, random.Random(3)))
    q = CanoeSails.BOB_S / 4
    assert actor.top_left(10 + q)[1] != actor.top_left(10 + 3 * q)[1]


def test_canoe_draws_nothing_when_inactive():
    show, actor, _ = _play(32, START + 10.0)
    assert _frame(show, actor, _climax(), START + 10.1, active=False) == {}


def test_canoe_follows_the_clock_not_the_frames():
    _, fast, a = _play(64, START + 13.0, fps=30)
    _, slow, b = _play(64, START + 13.0, fps=7)
    assert fast.elapsed() == pytest.approx(slow.elapsed())
    assert fast.top_left(fast.elapsed()) == pytest.approx(slow.top_left(slow.elapsed()))


def test_on_64x64_moana_stands_in_the_canoe_and_on_64x32_its_tiny_figure_stays():
    show, actor, out = _play(64, START + 14.0)
    left, top = (int(v + 0.5) for v in actor.top_left(actor.elapsed()))
    moana = {xy for xy, rgb in out.items() if rgb in (CanoeSails.MOANA_COLORS["A"], CanoeSails.MOANA_COLORS["O"])}
    assert len(moana) > 60, "her face and red top"
    assert all(left + CanoeSails.MOANA_LEFT <= x < left + actor.w for x, _ in moana), "aboard"
    assert max(y for _, y in moana) <= top + CanoeSails.BIG_DECK, "standing on the deck, not under it"
    assert CanoeSails.COLORS["H"] not in out.values(), "the toy's canoe, not the small one with its tiny figure"
    assert CanoeSails.BIG_COLORS["X"] in out.values(), "the heart of Te Fiti's spiral on the sail"
    hair = [rgb for rgb in out.values() if rgb in (CanoeSails.MOANA_COLORS["K"], CanoeSails.MOANA_COLORS["k"])]
    assert hair and all(max(rgb) >= 50 for rgb in hair), "hair lifted so the LEDs show it"
    _, _, small = _play(32, START + 14.0)
    assert CanoeSails.COLORS["H"] in small.values() and CanoeSails.MOANA_COLORS["A"] not in small.values()
