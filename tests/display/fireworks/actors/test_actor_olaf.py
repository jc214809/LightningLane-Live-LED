import random

import pytest

from display.animation.characters.olaf import OlafReveal
from display.fireworks.actors.olaf import OlafStands
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue


def _scene(start=563.0, end=576.0):
    return Cue("Olaf: some people are worth melting for", "scene", start, end, ((255, 255, 255),), 0.0, None,
               ("snow",), frozenset(), "ghost", ("olaf",))


def _run(actor, show, cue, until, fps=30):
    """Step him at fps from the cue's start up to until; his pixels on the last frame."""
    out = {}
    i = 0
    while cue.start + i / fps <= until:
        show.set_cue(cue, cue.start + i / fps)
        actor.follow(True)
        actor.step(True)
        i += 1
    show.set_cue(cue, until)
    actor.follow(True)
    actor.draw(None, out, True)
    return out


@pytest.mark.parametrize("height", [32, 64])
def test_olaf_pops_up_then_stands_waving_on_the_board(height):
    show = MusicShow(64, height, random.Random(1))
    actor = OlafStands(show)
    cue = _scene()
    early = _run(actor, show, cue, cue.start + 0.1)
    standing = _run(OlafStands(show), show, cue, cue.start + 5.0)
    assert standing and all(0 <= x < 64 and 0 <= y < height for x, y in standing)
    assert set(standing.values()) <= set(OlafReveal.colors.values()) | {OlafReveal.SHADE}
    assert max(y for _, y in standing) == height - 1, "he stands on the bottom row"
    assert sum(1 for _ in early) < len(standing), "still popping up from the bottom"
    assert min(x for x, _ in standing) >= 0 and max(x for x, _ in standing) < show.castle_x + show.castle_w


@pytest.mark.parametrize("height", [32, 64])
def test_olaf_waves(height):
    show = MusicShow(64, height, random.Random(2))
    actor = OlafStands(show)
    cue = _scene()
    poses = {frozenset(_run(actor, show, cue, cue.start + 2 + k * 0.25)) for k in range(4)}
    assert len(poses) > 1, "his arm moves"


def test_olaf_draws_nothing_when_off():
    show = MusicShow(64, 32, random.Random(3))
    actor = OlafStands(show)
    show.set_cue(_scene(), 570.0)
    actor.follow(False)
    actor.step(False)
    out = {}
    actor.draw(None, out, False)
    assert out == {}


@pytest.mark.parametrize("height", [32, 64])
def test_olaf_follows_the_clock_not_the_frame_rate(height):
    cue = _scene()
    frames = []
    for fps in (30, 7):
        show = MusicShow(64, height, random.Random(4))
        frames.append(_run(OlafStands(show), show, cue, cue.start + 3.3, fps=fps))
    assert frames[0] == frames[1]
    for fps in (30, 7):
        show = MusicShow(64, height, random.Random(4))
        frames.append(_run(OlafStands(show), show, cue, cue.start + 0.4, fps=fps))
    assert frames[2] == frames[3]


def test_on_64x64_his_head_stands_over_his_jaw_and_on_64x32_it_is_as_drawn():
    olaf = OlafReveal(64, 64, random.Random(0))
    def lean(art):  # the dome's left edge, averaged over its rows (3-8, under the twig hair)
        return sum(len(r) - len(r.lstrip(".")) for r in art[3:9]) / 6
    straight = list(OlafReveal.BIG_HEAD_ART)
    straight[:len(OlafStands.BIG_DOME)] = OlafStands.BIG_DOME
    assert lean(straight) < lean(OlafReveal.BIG_HEAD_ART) - 2, "the dome rounds out left, over his jaw"
    assert straight[len(OlafStands.BIG_DOME):] == OlafReveal.BIG_HEAD_ART[len(OlafStands.BIG_DOME):], "face as drawn"
    assert all(len(r) == len(OlafReveal.BIG_HEAD_ART[0]) for r in OlafStands.BIG_DOME)
    small = OlafStands(MusicShow(64, 32, random.Random(2)))
    assert len(set(map(lambda p: tuple(sorted(p[0].items())), small.poses.values()))) == 1, "64x32: one head"
    assert olaf.head_art is OlafReveal.BIG_HEAD_ART, "his ride screen keeps its own head"


def test_on_64x64_he_mouths_his_line_by_the_clock_and_grins_either_side():
    from display.fireworks.score import Lips
    # 2 s quiet, then a second each of half, closed and open, then quiet again
    track = "0" * 30 + "1" * 15 + "0" * 15 + "2" * 15 + "0" * 30
    show = MusicShow(64, 64, random.Random(3), {"olaf": Lips(563.0, 15.0, track)})
    cue = _scene()
    frames = [_run(OlafStands(show), show, cue, cue.start + t) for t in (1.5, 2.5, 3.5, 4.5)]
    before, half, shut, wide = ({xy for xy, rgb in m.items() if rgb == OlafReveal.MOUTH} for m in frames)
    assert len(shut) < len(half) < len(wide), "more of his mouth shows as it opens"
    shape = lambda cells: {(x, y - min(y for _, y in cells)) for x, y in cells}  # wherever he's sunk to
    assert shape(before) == shape(wide), "his big open grin before his first word"
    actor = OlafStands(show)
    _run(actor, show, cue, cue.start + 5.5)
    assert actor.shape(5.5) == 2, "and after his last"


@pytest.mark.parametrize("height", [32, 64])
def test_he_melts_as_he_says_his_line_his_face_last_into_a_puddle_gone_by_his_scene_end(height):
    from display.fireworks.score import Lips
    track = "0" * 120 + "2" * 30  # his line: 8-10 s into his 13 s scene, as his real one is
    show = MusicShow(64, height, random.Random(5), {"olaf": Lips(563.0, 15.0, track)})
    cue = _scene()
    actor = OlafStands(show)
    _run(actor, show, cue, cue.start)
    body, head, gone = actor.melt_s()
    assert (body, head, gone) == pytest.approx((8.0, 10.0, 13.0 - OlafStands.PUDDLE_S))
    face = lambda out: {xy for xy, rgb in out.items() if rgb in (OlafReveal.CARROT, OlafReveal.EYE_RING)}
    standing = _run(OlafStands(show), show, cue, cue.start + 7.9)
    talking = _run(OlafStands(show), show, cue, cue.start + 9.9)
    melting = _run(OlafStands(show), show, cue, cue.start + 11.8)
    puddle = _run(OlafStands(show), show, cue, cue.start + gone + 0.05)
    top = lambda out: min(y for _, y in out)
    assert top(standing) < top(talking) < top(melting) < top(puddle), "he sinks down"
    drop = top(talking) - top(standing)
    assert drop > 0 and {(x, y + drop) for x, y in face(standing)} == face(talking), \
        "his face rides down whole while he talks"
    assert len(face(melting)) < len(face(standing)), "then it melts too"
    assert max(y for _, y in puddle) == height - 1 and top(puddle) >= height - 3, "a puddle on the bottom rows"
    near = lambda ref: any(all(abs(a - b) <= 0.1 * b + 1 for a, b in zip(rgb, ref)) for rgb in puddle.values())
    assert near(OlafStands.WATER) and near(OlafReveal.CARROT), "his carrot in it"
    assert not near(OlafReveal.WHITE), "no snow left"
    assert not _run(OlafStands(show), show, cue, cue.end - 0.01), "the puddle's gone by his scene's end"


def test_without_a_track_he_melts_in_his_scene_last_seconds():
    show = MusicShow(64, 64, random.Random(6))
    cue = _scene()
    actor = OlafStands(show)
    _run(actor, show, cue, cue.start)
    start = 13.0 - OlafStands.MELT_S - OlafStands.PUDDLE_S
    assert actor.melt_s()[:2] == pytest.approx((start, start))
    assert not _run(OlafStands(show), show, cue, cue.end - 0.01)


def test_on_64x32_his_mouth_stays_as_drawn_even_with_a_track():
    from display.fireworks.score import Lips
    cue = _scene()
    with_track = MusicShow(64, 32, random.Random(4), {"olaf": Lips(563.0, 15.0, "0" * 90)})
    without = MusicShow(64, 32, random.Random(4))
    assert _run(OlafStands(with_track), with_track, cue, cue.start + 3) == \
        _run(OlafStands(without), without, cue, cue.start + 3)
