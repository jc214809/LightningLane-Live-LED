"""The Pixar Ball and Luxo Jr.."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def test_luxo_ball_is_registered_and_picks_one_of_three_stories():
    cls = animation.TRANSITIONS["luxo_ball"]
    assert cls is animation.LuxoBallReveal and cls.over_screen
    stories = {cls(64, 32, random.Random(seed)).story for seed in range(40)}
    assert stories == set(cls.STORIES) == {"bat", "chase", "light"}


@pytest.mark.parametrize("story", ["bat", "chase", "light"])
@pytest.mark.parametrize("height", [32, 64])
def test_luxo_ball_stays_on_the_board_and_leaves_by_the_end(monkeypatch, story, height):
    monkeypatch.setattr(animation.LuxoBallReveal, "STORY", story)
    scene = animation.LuxoBallReveal(64, height, random.Random(1))
    for f in range(0, int(scene.duration * animation.FPS), 3):
        canvas = FakeCanvas(64, height)
        assert scene.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    end = scene.duration - 0.01
    assert scene.ball(end) is None and scene.luxo(end) is None, "both gone"
    assert scene.overlay(FakeCanvas(64, height), scene.duration) is False


def test_the_ball_turns_a_quarter_each_hop_the_way_it_rolls(monkeypatch):
    monkeypatch.setattr(animation.LuxoBallReveal, "STORY", "bat")
    scene = animation.LuxoBallReveal(64, 32, random.Random(2))
    rolling_in = [scene.ball(i / 20)[2] for i in range(1, 24) if scene.ball(i / 20)]
    assert rolling_in == sorted(rolling_in, reverse=True) and min(rolling_in) <= -2, "clockwise, rolling right"
    batted = [scene.ball(2.4 + i / 20)[2] for i in range(1, 19) if scene.ball(2.4 + i / 20)]
    assert batted == sorted(batted) and batted[-1] > batted[0], "counter-clockwise, rolling back left"
    assert scene.ball(1.2)[1] == 32 - len(scene.BALL_ART), "resting on the bottom edge"


def test_luxo_bats_the_ball_away(monkeypatch):
    monkeypatch.setattr(animation.LuxoBallReveal, "STORY", "bat")
    scene = animation.LuxoBallReveal(64, 32, random.Random(3))
    assert scene.luxo(2.0)[0] > scene.ball(2.0)[0], "he's on the right of the ball, facing it"
    assert scene.luxo(2.5)[0] < scene.luxo(2.0)[0], "he lunges at it"
    assert scene.ball(3.0)[0] < scene.ball(2.4)[0], "and it rolls away"


def test_luxo_chases_the_ball_facing_it(monkeypatch):
    monkeypatch.setattr(animation.LuxoBallReveal, "STORY", "chase")
    scene = animation.LuxoBallReveal(64, 64, random.Random(4))
    x, _, facing_left = scene.luxo(1.5)
    assert not facing_left and x < scene.ball(1.5)[0], "behind the ball, turned round after it"


def test_luxo_searches_the_dark_with_his_light_finds_the_ball_then_lights_the_ride(monkeypatch):
    monkeypatch.setattr(animation.LuxoBallReveal, "STORY", "light")
    scene = animation.LuxoBallReveal(64, 32, random.Random(5))
    ball_colors = set(scene.colors[k] for k in "YRB")

    def dark(t):
        return sum(1 for rgb in scene.pixels(t).values() if rgb == (0, 0, 0))

    def ball_shown(t):
        return sum(1 for rgb in scene.pixels(t).values() if rgb in ball_colors)

    assert scene.beam(scene.LIGHT_ON - 0.01) is None, "no light while he hops in"
    assert scene.luxo(scene.LIGHT_ON - 0.1)[1] == 32 - len(scene.LUXO_ART), "he's landed before it's on"
    ball_area = {(x, y) for x in range(scene.ball_rest - 10, scene.ball_rest + 11) for y in range(11, 32)}
    assert dark(0.5) > 64 * 32 * 0.7, "dark"
    assert all(scene.pixels(0.5).get(p) == (0, 0, 0) for p in ball_area), "the ball hidden in it"
    search = [scene.LIGHT_ON + 0.1 + i / 20 for i in range(20)]
    aims = [scene.beam(t)[2] for t in search]
    assert max(aims) - min(aims) > 0.8, "the beam sweeps back and forth"
    tilts = [scene.head_tilt(t) for t in search]
    assert tilts == [a - scene.AIM for a in aims], "his head turns with it"
    assert max(abs(t) for t in tilts) <= scene.MAX_TILT + 1e-9
    up, down = scene.luxo_pose(-scene.MAX_TILT), scene.luxo_pose(scene.MAX_TILT)
    assert up != down and scene.luxo_pose(0.0) == {(c, r): k for r, row in enumerate(scene.LUXO_ART)
                                                   for c, k in enumerate(row) if k != "."}
    whole = len("".join(scene.BALL_ART).replace(".", ""))
    assert min(ball_shown(t) for t in search) < whole * 0.3, "in the dark between passes: it shows only where lit"
    assert ball_shown(scene.FOUND - 0.05) > whole * 0.6, "the beam settles on it"
    widen = scene.WIDEN
    assert dark(widen - 0.1) > dark(widen + 0.5) > dark(widen + 0.8) > 0, "then the beam widens"
    assert dark(widen + 1.15) == 0, "until the whole ride is lit"
