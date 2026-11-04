"""Mike Wazowski."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def test_mike_is_a_registered_peek_over_the_finished_screen():
    cls = animation.TRANSITIONS["mike"]
    assert cls is animation.MikeReveal and cls.over_screen
    assert not getattr(cls, "wants_prev", False) and not getattr(cls, "wants_new", False)


@pytest.mark.parametrize("height", [32, 64])
def test_mike_stays_on_the_board_and_is_gone_by_the_end(height):
    mike = animation.MikeReveal(64, height, random.Random(1))
    for f in range(int(mike.duration * animation.FPS) + 1):
        canvas = FakeCanvas(64, height)
        assert mike.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert mike.pixels(mike.duration - 0.01) == {}, "ducked out of sight"
    assert mike.overlay(FakeCanvas(64, height), mike.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_mike_shows_his_whole_round_body_once_up(height):
    mike = animation.MikeReveal(64, height, random.Random(2))
    px = mike.pixels(mike.UP_S + 0.05)
    body = [(x, y) for (x, y), rgb in px.items() if rgb in (mike.GREEN, mike.LIGHT, mike.EDGE)]
    assert max(y for _, y in body) < height - 1, "his body clears the bottom edge"
    assert max(x for x, _ in body) - min(x for x, _ in body) >= 2 * mike.r - 3


def _eye_whites(mike, t):
    return sum(1 for rgb in mike.pixels(t).values() if rgb == mike.WHITE)


def test_mike_blinks_looks_around_then_scares():
    mike = animation.MikeReveal(64, 64, random.Random(3))
    open_eye = _eye_whites(mike, mike.BLINK[0] - 0.05)
    mid_blink = (mike.BLINK[0] + mike.BLINK[1]) / 2
    assert mike.lid(mid_blink) == 1.0 and _eye_whites(mike, mid_blink) < open_eye / 2, "the lid covers the eye"
    looks = [mike.look(mike.LOOK[0] + i / 100) for i in range(int((mike.LOOK[1] - mike.LOOK[0]) * 100))]
    assert min(looks) == -1.0 and max(looks) == 1.0
    assert looks.index(-1.0) < looks.index(1.0), "left first, then right"
    assert mike.grin(mike.SCARE[0]) == 1.0 and mike.grin(0) == 0.0

    def top(t, rgb=None):
        return min(y for (_, y), c in mike.pixels(t).items() if rgb is None or c == rgb)

    before, scaring = mike.SCARE[0] - 0.05, mike.SCARE[0] + 0.2
    assert top(scaring) <= top(before) - 2, "he jumps at the scare"

    def hands_up(t):
        # Arm pixels out past his sides, above his eye.
        px = mike.pixels(t)
        cx = sum(x for x, _ in px) / len(px)
        return any(rgb == mike.DARK and abs(x - cx) > mike.r + 1 and y < top(t, mike.IRIS)
                   for (x, y), rgb in px.items())

    assert hands_up(scaring) and not hands_up(before), "arms thrown up only for the scare"


@pytest.mark.parametrize("height", [32, 64])
def test_mikes_hands_are_three_spread_fingers_and_a_thumb(height):
    mike = animation.MikeReveal(64, height, random.Random(5))
    body = mike._body(scare=True, look=0.0, lid=0.0, grin=0.0)
    green = {p for p, rgb in body.items() if rgb == mike.DARK}
    top = min(y for _, y in green)
    tips = sorted(x for x, y in green if y == top)
    assert len(tips) == 6, "three fingertips on each raised hand"
    for side in (-1, 1):
        xs = [x for x in tips if x * side > 0]
        assert all(b - a >= 2 for a, b in zip(xs, xs[1:])), "gaps between them, not one blob"
    assert not any(rgb == (120, 115, 130) for rgb in body.values()), "no grey claws"


@pytest.mark.parametrize("r", [8, 12, 16])
def test_mikes_scare_mouth_has_sharp_teeth_top_and_fangs_below(r):
    mike = animation.MikeReveal(64, 64, random.Random(4))
    mike.r, mike.ry = r, r * 1.08
    body = mike._body(scare=True, look=0.0, lid=0.0, grin=1.0)
    mouth = {p: rgb for p, rgb in body.items() if p[1] > 0 and rgb in (mike.MOUTH, mike.WHITE)}

    def column(x):
        return [mouth[(x, y)] for y in sorted(y for (bx, y) in mouth if bx == x)]

    def tooth(x):
        c = column(x)
        return next(i for i, rgb in enumerate(c) if rgb != mike.WHITE)

    assert tooth(0) > tooth(1), "pointed: the middle tooth hangs lower than its neighbour"
    assert all(column(x)[0] == mike.WHITE for x in (-1, 0, 1)), "teeth along the whole top"
    assert column(2)[-1] == mike.WHITE and column(0)[-1] == mike.MOUTH, "fangs below, apart"
    assert all(mike.MOUTH in column(x) for x in (-2, -1, 0, 1, 2)), "still an open mouth"
