"""Dumbo."""

import random

import display.animation as animation

from tests.display.animation.support import FakeCanvas


def test_dumbo_ears_alternate_between_the_two_flap_poses():
    dumbo = animation.DumboReveal(64, 32, random.Random(1))
    frames = [dumbo.flap_frame(i * dumbo.FLAP_S / 2) for i in range(8)]
    assert set(frames) == {0, 1}, "both ear poses are used"
    assert dumbo.flap_frame(0.0) == 0, "starts on the upstroke"
    assert dumbo.flap_frame(dumbo.FLAP_S * 1.5) == 1, "ears are down half a cycle later"
    assert dumbo.EARS_UP != dumbo.EARS_DOWN, "the poses actually differ"


def test_dumbo_draws_a_different_sprite_when_his_ears_are_down():
    dumbo = animation.DumboReveal(64, 32, random.Random(2))
    up, down = FakeCanvas(64, 32), FakeCanvas(64, 32)
    # Same horizontal position for both, so only the pose differs.
    t_up = dumbo.duration / 2
    t_down = t_up + dumbo.FLAP_S
    dumbo._draw_sprite(up, t_up)
    dumbo._draw_sprite(down, t_down)
    assert up.px and down.px
    assert up.px != down.px, "the ears visibly flap between frames"


def test_dumbo_bobs_with_the_flap_and_stays_on_both_boards():
    for height in (32, 64):
        dumbo = animation.DumboReveal(64, height, random.Random(3))
        ys = [dumbo.position(f / animation.FPS)[1] for f in range(int(dumbo.duration * animation.FPS))]
        assert max(ys) - min(ys) > 0.5, "he bobs rather than flying flat"
        assert min(ys) >= 0 and max(ys) + dumbo.sprite_h <= height


def test_dumbo_art_rows_are_uniform_and_every_colour_is_defined():
    for pose in animation.DumboReveal.poses:
        assert len({len(row) for row in pose}) == 1, "all rows the same width"
        assert {ch for row in pose for ch in row} - {"."} <= set(animation.DumboReveal.colors)
    assert len(animation.DumboReveal.poses[0]) == len(animation.DumboReveal.poses[1])
    assert len(animation.DumboReveal.poses[0][0]) == len(animation.DumboReveal.poses[1][0])


def test_dumbo_trails_feather_puffs_behind_him():
    dumbo = animation.DumboReveal(64, 64, random.Random(4))
    x, y = dumbo.position(dumbo.duration / 2)
    puffs = dumbo.spawn(x, y)
    assert puffs, "sheds a trail"
    assert all(p[2] < 0 for p in puffs), "puffs drift back behind him"
    assert all(p[5] in dumbo.feather_colors for p in puffs)


def test_dumbo_is_registered_as_a_transition():
    assert animation.TRANSITIONS["dumbo"] is animation.DumboReveal
    assert issubclass(animation.DumboReveal, animation.FlyByReveal)
