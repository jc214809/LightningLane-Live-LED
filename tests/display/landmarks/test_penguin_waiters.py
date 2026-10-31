"""The Wine & Dine half marathon landmark: three penguin waiters flap and hop in turn under a gold Half Marathon."""

import random

import pytest

import display.landmarks as landmarks
from display.landmarks import penguin_waiters as pw

from tests.display.landmarks.support import _scene_s

BOARDS = [(64, 32), (64, 64)]


def _scene(w, h, seed=3):
    return landmarks.PenguinWaitersHalfLandmark(w, h, random.Random(seed))


def _times(scene, step=1 / 60):
    return [i * step for i in range(int(_scene_s(type(scene)) / step))]


def _box(pixels):
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    return min(xs), min(ys), max(xs), max(ys)


def _drawn(scene, name, t=0.0):
    """The pixels a penguin covers at scene time t, its raised flipper included."""
    x, y = scene.positions(t)[name]
    cells = {p for p, _ in pw.art_pixels(scene.art[name], x, y, pw.COLORS)}
    if scene.waving(name, t):
        cells |= {(x + c, y + r) for c, r in scene.wave}
    return cells


@pytest.mark.parametrize("w, h", BOARDS)
def test_they_stand_on_the_bottom_edge_left_to_right_without_overlapping(w, h):
    scene = _scene(w, h)
    for name in pw.ORDER:
        _, y = scene.positions(0)[name]
        assert y + scene.size[name][1] == h, name
    boxes = [_box(_drawn(scene, n)) for n in pw.ORDER]
    assert all(a[2] < b[0] for a, b in zip(boxes, boxes[1:])), boxes


@pytest.mark.parametrize("w, h", BOARDS)
def test_waving_flippers_stay_on_the_board_and_off_the_next_penguin(w, h):
    scene = _scene(w, h)
    for t in _times(scene, 0.05):
        drawn = {n: _drawn(scene, n, t) for n in pw.ORDER}
        for n, cells in drawn.items():
            assert all(0 <= x < w for x, _ in cells), (n, t)
        for a, b in zip(pw.ORDER, pw.ORDER[1:]):
            assert not drawn[a] & drawn[b], (a, b, t)


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_says_half_marathon_and_stays_clear_of_them_at_rest(w, h):
    scene = _scene(w, h)
    assert all(0 <= x < w and 0 <= y < h for x, y in scene.text), "the title isn't clipped"
    for name in pw.ORDER:
        assert not set(scene.text) & _drawn(scene, name), name
    by_colour = {rgb: " ".join(text for _, text, _, _, c in scene.title_spec if c == rgb) for rgb in (pw.WHITE, pw.GOLD)}
    assert by_colour[pw.GOLD] == "HALF MARATHON"
    assert by_colour[pw.WHITE].replace(" ", "") == "WINE&DINE"


@pytest.mark.parametrize("w, h", BOARDS)
def test_each_hops_in_turn_then_all_three_together(w, h):
    scene = _scene(w, h)
    first = {}
    for t in _times(scene):
        up = [n for n in pw.ORDER if scene.hop(n, t) > 0]
        for n in up:
            first.setdefault(n, t)
        if t < pw.ALL_AT:
            assert len(up) <= 1, (t, up)
    assert sorted(first, key=first.get) == list(pw.ORDER)
    mid = pw.ALL_AT + pw.HOP_S / 2
    assert all(scene.hop(n, mid) > 0 for n in pw.ORDER)
    assert all(scene.hop(n, _scene_s(type(scene)) - 0.1) == 0 for n in pw.ORDER), "back down to end"


@pytest.mark.parametrize("w, h", BOARDS)
def test_each_penguin_flaps_through_its_turn(w, h):
    scene = _scene(w, h)
    for name in pw.ORDER:
        turn = [scene.waving(name, t) for t in _times(scene) if pw.TURN_AT[name] <= t < pw.TURN_AT[name] + pw.FLAP_S]
        assert any(turn) and not all(turn), "up and down, not held"
        assert not scene.waving(name, 0.0) and not scene.waving(name, _scene_s(type(scene)) - 0.1)


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_draws_over_them(w, h):
    scene = _scene(w, h)
    frame = scene.frame(pw.ALL_AT + pw.HOP_S / 2)
    assert all(frame[p] == rgb for p, rgb in scene.text.items())
    assert len(frame) == w * h, "the sky fills the board"


def test_the_sprites_are_rectangular_and_use_only_the_palette():
    for art in (pw.PENGUIN_64, pw.PENGUIN_32):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(pw.COLORS)


def test_64x64_fills_the_board_under_the_title_with_tall_penguins():
    scene = _scene(64, 64)
    title_bottom = max(y for _, y in scene.text)
    assert min(y for _, y in scene.home.values()) - title_bottom <= 8, "no empty band under the title"


def test_title_pixels_drops_a_full_width_lines_shadow_off_the_edge():
    spec = pw.TITLES[True]
    assert all(0 <= x < 64 for x, _ in pw.title_pixels(spec, 64, 64))
    assert max(x for x, _ in pw.title_pixels(spec, 64, 64)) == 63, "edge to edge"


def test_it_plays_for_six_seconds():
    assert landmarks.PenguinWaitersHalfLandmark.SCREEN_S == 6.0
    assert landmarks.landmark_screen(_scene(64, 32)).plays_under_reveal is False


def test_its_race_day_name_finds_it():  # the date itself: tests/utils/test_special_events.py
    assert landmarks.landmark_for("EPCOT", dated="PenguinWaitersHalfLandmark") is pw.PenguinWaitersHalfLandmark
