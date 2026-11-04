"""The Wine & Dine Two Course Challenge landmark: Grumpy, arms folded, taps a foot under the half's title,
then gives one grudging hop."""

import random

import pytest

import display.landmarks as landmarks
from display.landmarks import grumpy as gr

from tests.display.landmarks.support import _scene_s

BOARDS = [(64, 32), (64, 64)]


def _scene(w, h):
    return landmarks.GrumpyTwoCourseLandmark(w, h, random.Random(3))


def _times(scene, step=1 / 60):
    return [i * step for i in range(int(_scene_s(type(scene)) / step))]


def _drawn(scene, t=0.0):
    x, y = scene.position(t)
    art = scene.tapping_art if scene.tapping(t) else scene.art
    return {p for p, _ in gr.art_pixels(art, x, y, gr.COLORS)}


@pytest.mark.parametrize("w, h", BOARDS)
def test_he_stands_whole_on_the_bottom_edge(w, h):
    scene = _scene(w, h)
    cells = _drawn(scene)
    assert max(y for _, y in cells) == h - 1
    assert all(0 <= x < w and 0 <= y < h for x, y in cells), "nothing off the board"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_names_his_race_and_stays_clear_of_him_on_the_ground(w, h):
    scene = _scene(w, h)
    by_colour = {rgb: " ".join(text for _, text, _, _, c in scene.title_spec if c == rgb) for rgb in (gr.WHITE, gr.GOLD)}
    assert by_colour[gr.GOLD] == "CHALLENGE 19.3", "not the half: his race is the 10K and the half, 19.3 miles"
    assert by_colour[gr.WHITE].replace(" ", "") == "WINE&DINE"
    assert all(0 <= x < w and 0 <= y < h for x, y in scene.text), "the title isn't clipped"
    for t in _times(scene, 0.05):
        if scene.hop(t) == 0:  # mid-hop the title may draw over his hat, as the 10K's does
            assert not set(scene.text) & _drawn(scene, t), t


@pytest.mark.parametrize("w, h", BOARDS)
def test_he_taps_a_foot_then_hops_once(w, h):
    scene = _scene(w, h)
    taps = [t for t in _times(scene) if scene.tapping(t)]
    assert taps and min(taps) >= gr.TAP_FROM and max(taps) < gr.TAP_TO
    assert not all(scene.tapping(t) for t in _times(scene) if gr.TAP_FROM <= t < gr.TAP_TO), "up and down, not held"
    up = [t for t in _times(scene) if scene.hop(t) > 0]
    assert up and min(up) > gr.TAP_TO, "after the tapping"
    assert max(up) - min(up) < gr.HOP_S, "just the one"
    assert scene.hop(_scene_s(type(scene)) - 0.1) == 0, "back down to end"


@pytest.mark.parametrize("w, h", BOARDS)
def test_a_tap_lifts_only_the_toe(w, h):
    scene = _scene(w, h)
    top, bottom, left, right = gr.TOE_64 if h >= 64 else gr.TOE_32
    changed = {(c, r) for r, (a, b) in enumerate(zip(scene.art, scene.tapping_art))
               for c, (x, y) in enumerate(zip(a, b)) if x != y}
    assert changed, "the toe moves"
    assert all(left <= c <= right and top - 1 <= r <= bottom for c, r in changed)


@pytest.mark.parametrize("w, h", BOARDS)
def test_his_shoes_are_outlined_all_round_and_the_tapping_toe_moves_whole(w, h):
    scene = _scene(w, h)
    top, bottom, left, right = gr.TOE_64 if h >= 64 else gr.TOE_32
    for art in (scene.art, scene.tapping_art):  # both shoes
        for r in range(len(art)):
            for c in range(len(art[0])):
                if art[r][c] == "T":
                    around = [art[r + dr][c + dc] if 0 <= c + dc < len(art[0]) and 0 <= r + dr < len(art) else "."
                              for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
                    assert "." not in around, ("the shoe touches the sky", r, c)
    for r in range(top, bottom + 1):  # the toe, outline and all, a row up
        assert scene.tapping_art[r - 1][left:right + 1] == "".join(
            ch if (r > top or ch != ".") else scene.art[r - 1][left + i]
            for i, ch in enumerate(scene.art[r][left:right + 1]))
    assert set(scene.tapping_art[bottom][left:right + 1]) == {"."}, "nothing left behind"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_draws_over_the_sky(w, h):
    scene = _scene(w, h)
    frame = scene.frame(1.0)
    assert all(frame[p] == rgb for p, rgb in scene.text.items())
    assert len(frame) == w * h


def test_the_sprites_are_rectangular_and_use_only_the_palette():
    for art in (gr.GRUMPY_64, gr.GRUMPY_32):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(gr.COLORS)
    assert len(gr.GRUMPY_64) > 40, "big on 64x64"


def test_it_plays_for_six_seconds():
    assert landmarks.GrumpyTwoCourseLandmark.SCREEN_S == 6.0
    assert landmarks.landmark_screen(_scene(64, 32)).plays_under_reveal is False


def test_its_race_day_name_finds_it():
    assert landmarks.landmark_for("EPCOT", dated="GrumpyTwoCourseLandmark") is gr.GrumpyTwoCourseLandmark
