"""The Millennium Falcon."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, _striped_screen, fill


def _falcon(height=32, seed=1):
    falcon = animation.FalconReveal(64, height, random.Random(seed))
    falcon.capture_prev(_striped_screen, 0.0)
    falcon.capture_new(fill((10, 20, 30)), 0.0)
    return falcon


@pytest.mark.parametrize("height", [32, 64])
def test_falcon_finishes_and_never_draws_off_board(height):
    falcon = _falcon(height)
    for f in range(int(falcon.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert falcon.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert falcon.overlay(FakeCanvas(64, height), falcon.duration) is False


def test_falcon_art_is_uniform_and_every_cell_has_a_colour():
    art = animation.FalconReveal.ART
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.FalconReveal.COLORS)


def test_falcon_keeps_her_silhouette():
    art = animation.FalconReveal.ART
    mid = len(art) // 2
    assert art[mid].rstrip(".").endswith("K") and art[mid].rstrip(".") != art[mid], "the gap between the mandibles"
    assert art[mid - 1].rstrip(".") > art[mid].rstrip(".") and len(art[mid - 1].rstrip(".")) > len(art[mid].rstrip(".")) + 5
    assert "W" in art[-2], "the cockpit tube hangs off the bottom edge, her starboard side seen from above"
    assert all(row.lstrip(".").startswith("E") for row in art[5:16]), "the engine band runs along her back"


def test_falcon_features_stand_out_from_her_hull():
    colors = animation.FalconReveal.COLORS

    def distance(a, b):
        return sum(abs(x - y) for x, y in zip(colors[a], colors[b]))

    assert distance("W", "K") > 150, "cockpit windows against the tube's outline, not holes in it"
    assert distance("E", "H") > 200, "the engine band against the hull"
    assert distance("R", "H") > 200, "red markings against the hull"
    assert distance("D", "L") > 250, "the turret ring against its light centre"


def test_falcon_opts_into_receiving_both_screens():
    assert animation.FalconReveal.wants_prev is True
    assert animation.FalconReveal.wants_new is True
    assert "falcon" in animation.TRANSITIONS


@pytest.mark.parametrize("height,scale", [(32, 1), (64, 2)])
def test_falcon_doubles_on_64x64_and_stays_whole_while_she_cruises(height, scale):
    falcon = _falcon(height)
    assert falcon.scale == scale
    assert falcon.ship_h <= height
    for name in ("cruise", "charge"):
        for f in range(10):
            rear, nose = falcon.ship_span(falcon.phase_start(name) + f / 10 * dict(falcon.PHASES)[name])
            assert rear >= 0 and nose <= 64, "her mandibles and engine band stay on the board"


def test_falcon_arrives_as_a_streak_that_snaps_into_the_ship():
    falcon = _falcon()
    rear, nose = falcon.ship_span(0.1)
    assert nose - rear > falcon.ship_w * 3, "a long streak first"
    rear, nose = falcon.ship_span(falcon.phase_start("cruise"))
    assert nose - rear == falcon.ship_w, "her own length once she's braked"


def test_falcon_story_plays_in_order():
    falcon = _falcon()
    assert [n for n, _ in falcon.PHASES] == ["arrive", "cruise", "charge", "jump", "flash"]
    cool, hot = falcon.engine_rgb(falcon.phase_start("cruise")), falcon.engine_rgb(falcon.phase_start("jump"))
    assert sum(hot) > sum(cool) + 150, "the engine band flares before she jumps"
    assert falcon.old_stretch(falcon.phase_start("jump") - 0.01) == (0.0, 1.0), "the old screen holds still until the jump"
    shift, stretch = falcon.old_stretch(falcon.phase_start("jump") + falcon.JUMP_S * 0.7)
    assert shift > 0 and stretch > 2, "then streaks off to the right"


def test_falcon_old_screen_is_gone_by_the_end_of_the_jump():
    falcon = _falcon()
    canvas = FakeCanvas(64, 32)
    falcon.overlay(canvas, falcon.phase_start("flash") - 0.01)
    assert (200, 100, 50) not in canvas.px.values()


def test_falcon_flash_fades_to_the_new_screen():
    falcon = _falcon()
    new = (10, 20, 30)
    start, end = FakeCanvas(64, 32), FakeCanvas(64, 32)
    falcon.overlay(start, falcon.phase_start("flash") + 0.01)
    falcon.overlay(end, falcon.duration - 0.01)
    assert sum(start.px[(5, 5)]) > 600, "a white flash"
    assert sum(abs(a - b) for a, b in zip(end.px[(5, 5)], new)) < 10, "fading to the new ride"


def test_falcon_stars_snap_from_streaks_to_points_then_fade():
    falcon = _falcon()

    def stars(p):
        canvas = FakeCanvas(64, 32)
        falcon._draw_stars(canvas, p)
        return canvas.px

    assert len(stars(0.02)) > 3 * falcon.STARS, "streaks at first"
    assert len(stars(0.6)) == falcon.STARS, "then one point each"
    assert not any(sum(rgb) for rgb in stars(1.0).values()), "and gone by the time she's braked"
