"""The Wine & Dine 10K landmark: the Three Caballeros hop in turn under a gold 10K, then confetti falls."""

import random

import pytest

import display.landmarks as landmarks
from display.landmarks import three_caballeros as tc

from tests.display.landmarks.support import _scene_s

BOARDS = [(64, 32), (64, 64)]


def _scene(w, h):
    return landmarks.ThreeCaballeros10KLandmark(w, h, random.Random(3))


def _times(scene, step=1 / 30):
    return [i * step for i in range(int(_scene_s(type(scene)) / step))]


def _box(pixels):
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    return min(xs), min(ys), max(xs), max(ys)


def _drawn(scene, name, t=0.0):
    """The pixels a character covers at scene time t."""
    x, y = scene.positions(t)[name]
    return {p for p, _ in tc.art_pixels(scene.art[name], x, y, tc.COLORS)}


@pytest.mark.parametrize("w, h", BOARDS)
def test_they_stand_on_the_bottom_edge_with_panchito_in_the_middle(w, h):
    scene = _scene(w, h)
    for name in tc.ORDER:
        _, y = scene.positions(0)[name]
        assert y + scene.size[name][1] == h, name
    centres = {n: (_box(_drawn(scene, n))[0] + _box(_drawn(scene, n))[2]) / 2 for n in tc.ORDER}
    assert centres["jose"] < centres["panchito"] < centres["donald"]
    assert abs(centres["panchito"] - w / 2) <= 4, "centre stage"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_fits_and_stays_clear_of_them_at_rest(w, h):
    scene = _scene(w, h)
    assert all(0 <= x < w and 0 <= y < h for x, y in scene.text), "the title isn't clipped"
    for name in tc.ORDER:
        assert not set(scene.text) & _drawn(scene, name), name
    texts = "".join(text for _, text, *_ in scene.title_spec).replace(" ", "")
    assert "10K" in texts and "WINE&" in texts and "DINE" in texts
    assert any(rgb == tc.GOLD for rgb in scene.text.values())


@pytest.mark.parametrize("w, h", BOARDS)
def test_each_hops_in_turn_then_all_three_together(w, h):
    scene = _scene(w, h)
    first = {}
    for t in _times(scene, 1 / 60):
        up = [n for n in tc.ORDER if scene.hop(n, t) > 0]
        for n in up:
            first.setdefault(n, t)
        if t < tc.ALL_HOP:
            assert len(up) <= 1, (t, up)
    assert sorted(first, key=first.get) == ["jose", "panchito", "donald"]
    mid = tc.ALL_HOP + tc.HOP_S / 2
    assert all(scene.hop(n, mid) > 0 for n in tc.ORDER)
    assert all(scene.hop(n, _scene_s(type(scene)) - 0.1) == 0 for n in tc.ORDER), "back down to end"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_confetti_falls_from_the_top_once_they_all_hop(w, h):
    scene = _scene(w, h)
    assert not scene.confetti_pixels(tc.CONFETTI_FROM[0] - 0.01)
    seen = set()
    for t in _times(scene, 0.1):
        seen |= set(scene.confetti_pixels(t))
    x0, y0, x1, y1 = _box(seen)
    assert x0 < w // 4 and x1 > 3 * w // 4, "across the whole board"
    assert y0 == 0 and y1 > h // 2, "from the top down"
    assert len(set(scene.confetti_pixels(4.0).values())) >= 3, "in several colours"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_and_confetti_draw_over_them(w, h):
    scene = _scene(w, h)
    frame = scene.frame(4.0)
    confetti = scene.confetti_pixels(4.0)
    assert all(frame[p] == rgb for p, rgb in scene.text.items() if p not in confetti)
    assert all(frame[p] == rgb for p, rgb in confetti.items())


def test_the_sprites_are_rectangular_and_use_only_the_palette():
    for art in (tc.JOSE_64, tc.PANCHITO_64, tc.DONALD_64, tc.JOSE_32, tc.PANCHITO_32, tc.DONALD_32):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(tc.COLORS)


def test_64x32_uses_the_smaller_sprites_and_fits_them_whole():
    scene = _scene(64, 32)
    assert scene.art["panchito"] is tc.PANCHITO_32
    assert all(h <= 32 for _, h in scene.size.values())


def test_it_plays_for_six_seconds():
    assert landmarks.ThreeCaballeros10KLandmark.SCREEN_S == 6.0
    assert landmarks.landmark_screen(_scene(64, 32)).plays_under_reveal is False


def test_its_race_day_name_finds_it():  # the date itself: tests/utils/test_special_events.py
    assert landmarks.landmark_for("EPCOT", dated="ThreeCaballeros10KLandmark") is tc.ThreeCaballeros10KLandmark
