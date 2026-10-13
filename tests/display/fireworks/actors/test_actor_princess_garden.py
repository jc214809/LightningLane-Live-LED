import random

import pytest

from display.fireworks.actors.princess_garden import ARIEL, NAVEEN, ROCK_COLORS, PrincessGarden
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, END = 637.0, 668.0  # Princess garden
SLOT = (END - START) / 4


def _scene():
    return Cue("s", "Princess garden", START, END, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost",
               ("princess_garden",))


def _frame(show, actor, t, active=True):
    show.set_cue(_scene(), t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _at(t, height=32):
    show = MusicShow(64, height, random.Random(1))
    actor = PrincessGarden(show)
    _frame(show, actor, START)
    return actor, _frame(show, actor, t)


def _colours(art_colors):
    return set(art_colors.values()) - {art_colors["K"]}


@pytest.mark.parametrize("height", [32, 64])
def test_each_couple_has_its_quarter_of_the_garden_in_order(height):
    for i, (_, _, her_colors, _, _, him_colors) in enumerate(PrincessGarden.COUPLES):
        _, out = _at(START + i * SLOT + 3.0, height)
        seen = set(out.values())
        assert _colours(her_colors) & seen and _colours(him_colors) & seen, f"couple {i} on in its slot"
        assert all(0 <= x < 64 and 0 <= y < height for x, y in out)
        assert max(y for _, y in out) == height - 1, "on the ground"


def test_they_walk_in_from_their_own_sides_meet_in_the_middle_and_walk_off():
    actor, _ = _at(START + 0.2)
    lefts = [actor.places(0, s) for s in (0.2, 1.0, 2.5, 6.5)]
    her = [p["her"][0] for p in lefts]
    him = [p["him"][0] for p in lefts]
    assert her[0] < her[1] < her[2] and her[3] < her[2], "she comes in from the left and goes back"
    assert him[0] > him[1] > him[2] and him[3] > him[2], "he comes in from the right and goes back"
    w = len(PrincessGarden.COUPLES[0][1][0])
    assert her[2] + w <= 32 <= him[2] + 1, "they meet either side of the middle"
    _, gone = _at(START + SLOT - 0.05)
    assert gone == {}, "off before the next couple"


def test_a_heart_floats_up_between_them_while_they_lean_together():
    actor, _ = _at(START)
    met, leaving, _ = actor.times()
    assert actor.heart(0, met - 0.1) is None and actor.heart(0, leaving) is None
    early, late = actor.heart(0, met + 0.1), actor.heart(0, leaving - 0.1)
    assert late[1] < early[1], "it rises"
    assert abs(early[0] + len(PrincessGarden.HEART[0]) / 2 - 32) <= 1, "between them"
    _, out = _at(START + met + 1.0)
    assert PrincessGarden.HEART_RGB in out.values()


def test_naveen_hops_in_as_a_frog():
    actor, _ = _at(START + SLOT)
    assert PrincessGarden.COUPLES[1][4] is NAVEEN
    heights = {actor.places(1, s)["him"][1] for s in [k * 0.05 for k in range(1, 40)]}
    assert len(heights) > 2, "up and down in arcs as he comes in"
    standing = actor.places(1, 4.0)["him"][1]
    assert standing == 32 - len(NAVEEN), "sitting on the ground once he's there"


def test_ariel_sits_on_a_rock_from_the_start_of_her_slot_and_fades_out_after_eric_leaves():
    i = 2
    assert PrincessGarden.COUPLES[i][1] is ARIEL
    actor, early = _at(START + i * SLOT + 0.5)
    assert set(ROCK_COLORS.values()) & set(early.values()), "her rock"
    rock_left, rock_top = actor.places(i, 0.5)["rock"]
    her_left, her_top = actor.places(i, 0.5)["her"]
    assert her_top + len(ARIEL) > rock_top, "sitting on it"
    assert actor.places(i, 0.5)["her"] == actor.places(i, 2.5)["her"], "she doesn't move"
    _, _, gone = actor.times()
    _, fading = _at(START + i * SLOT + gone + 0.1)
    _, after = _at(START + (i + 1) * SLOT - 0.005)
    assert fading and not after, "she fades out once Eric's gone, by the end of her slot"


def test_the_garden_follows_the_clock_not_the_frames():
    frames = []
    for fps in (30, 7):
        show = MusicShow(64, 64, random.Random(2))
        actor = PrincessGarden(show)
        i = 0
        while START + i / fps <= START + 10:
            _frame(show, actor, START + i / fps)
            i += 1
        frames.append(_frame(show, actor, START + 10.3))
    assert frames[0] == frames[1]


def test_the_garden_draws_nothing_when_inactive():
    show = MusicShow(64, 32, random.Random(3))
    actor = PrincessGarden(show)
    assert _frame(show, actor, START + 3, active=False) == {}
