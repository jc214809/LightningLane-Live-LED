"""Spaceship Earth, lit by Tinker Bell."""

import math
import random

import pytest

import display.landmarks as landmarks

from tests.display.landmarks.support import _scene_s


def _earth(height=64):
    return landmarks.SpaceshipEarthLandmark(64, height, random.Random(3))


def test_spaceship_earth_lights_up_under_the_wipe_and_within_its_screen():
    earth = _earth()
    assert landmarks.landmark_screen(earth).plays_under_reveal is True
    assert earth.LIGHT_S < _scene_s(landmarks.SpaceshipEarthLandmark) - 1.0, "time for the colour wave after"


@pytest.mark.parametrize("height", [32, 64])
def test_spaceship_earth_lights_come_on_from_the_bottom_to_the_top(height):
    earth = _earth(height)
    cells = [(x, y) for facet in earth.facets for x, y, _, _ in facet[0]]
    bottom = [p for p in cells if p[1] > earth.cy + earth.r * 0.5]
    top = [p for p in cells if p[1] < earth.cy - earth.r * 0.5]

    def mean(t, pixels):
        frame = earth.frame(t)
        return sum(sum(frame[p]) for p in pixels) / len(pixels)

    half = earth.LIGHT_S * 0.5
    assert mean(half, bottom) > 1.5 * mean(half, top), "the base lit while the top is still dark"
    assert mean(earth.LIGHT_S + 0.1, top) > 1.5 * mean(0.0, top), "all lit once the lights are on"


def test_spaceship_earth_facets_alternate_lit_and_shaded_faces():
    earth = _earth()
    frame = earth.frame(earth.LIGHT_S + 0.5)
    ups = [sum(frame[c[0][0][:2]]) for c in earth.facets if c[1]]
    downs = [sum(frame[c[0][0][:2]]) for c in earth.facets if not c[1]]
    assert ups and downs
    assert sum(ups) / len(ups) > 1.8 * sum(downs) / len(downs), "the triangles read as bright and dark"


def _facet_at(earth, x, y):
    for facet in earth.facets:
        if any((cx, cy) == (x, y) for cx, cy, _, _ in facet[0]):
            return facet
    raise KeyError((x, y))


def test_spaceship_earth_facets_shrink_toward_the_rim():
    earth = _earth()
    centre = len(_facet_at(earth, int(earth.cx), int(earth.cy))[0])
    rim = len(_facet_at(earth, int(earth.cx + earth.r * 0.93), int(earth.cy))[0])
    assert rim < centre, "foreshortened as the sphere curves away"


def test_spaceship_earth_colours_roll_around_the_sphere():
    earth = _earth()
    frame = earth.frame(earth.LIGHT_S + 0.5)
    hues = {max(range(3), key=lambda i: frame[c[0][0][:2]][i]) for c in earth.facets if c[1]}
    assert len(hues) >= 2, "bands of different colours across the face at once"
    p = (int(earth.cx), int(earth.cy))
    assert earth.frame(2.0)[p] != earth.frame(3.0)[p], "and they move"


def test_spaceship_earth_fills_the_64x32_board_with_just_the_tops_of_its_legs():
    earth = _earth(32)
    sphere_rows = {y for facet in earth.facets for _, y, _, _ in facet[0]}
    assert min(sphere_rows) == 0 and max(sphere_rows) == 31, "the sphere fills the height"
    assert earth.legs and all(y > earth.cy for _, y in earth.legs), "legs only below the middle"


def test_spaceship_earth_legs_are_even_slabs_not_beams():
    earth = _earth()
    rows = {}
    for x, y in earth.legs:
        if x < earth.cx:
            rows.setdefault(y, []).append(x)
    widths = [len(v) for _, v in sorted(rows.items())]
    assert max(widths) - min(widths) <= 2, "the same width top to foot"


@pytest.mark.parametrize("height", [32, 64])
def test_spaceship_earth_stays_a_perfect_sphere_with_the_legs_behind_it(height):
    earth = _earth(height)
    frame = earth.frame(earth.LIGHT_S + 0.5)
    leg_colours = {earth.LEG_RGB, earth.LEG_LIT_RGB}
    disc = [(x, y) for facet in earth.facets for x, y, _, _ in facet[0]]
    assert not any(frame[p] in leg_colours for p in disc), "no leg pixel on the ball"
    assert any(frame.get(p) in leg_colours for p in earth.legs), "but the legs still show beside it"


def test_spaceship_earth_on_64x64_stands_on_short_legs_not_a_water_tower():
    earth = _earth(64)
    frame = earth.frame(earth.LIGHT_S + 0.5)
    sphere_bottom = max(y for facet in earth.facets for _, y, _, _ in facet[0])
    assert 64 - 1 - sphere_bottom <= 5, "the legs just peek out under the sphere"
    assert earth.r * 2 >= 54, "a big sphere, not a tank on stilts"


def test_spaceship_earth_tink_circles_three_even_laps_ending_where_she_began():
    earth = _earth()
    assert earth.TURNS == 3
    start, end = earth.angle(0.0), earth.angle(1.0)
    assert math.isclose(math.sin(start), math.sin(end), abs_tol=1e-9) and \
        math.isclose(math.cos(start), math.cos(end), abs_tol=1e-9), "whole laps: same spot, higher up"
    ys = [earth.tink_at(earth.SPIRAL_S * k / 3 - (1e-6 if k == 3 else 0))[1] for k in range(4)]
    gaps = [a - b for a, b in zip(ys, ys[1:])]
    assert all(g > 0 for g in gaps), "climbing"
    assert max(gaps) - min(gaps) < 1.0, "evenly: each lap rises the same"


def test_spaceship_earth_tink_is_hidden_while_behind_the_sphere():
    earth = _earth()
    wing = earth.tink_colors["W"]
    for f in range(int(earth.SPIRAL_S * 30)):
        t = f / 30
        x, y, front = earth.tink_at(t)
        if not front and earth._on_sphere(x, y):
            frame = earth.frame(t)
            near = [frame.get((int(x) + dx, int(y) + dy)) for dx in range(-2, 3) for dy in range(-2, 3)
                    if earth._on_sphere(int(x) + dx, int(y) + dy)]
            assert wing not in near, f"her wings show through the sphere at t={t:.2f}"


def test_spaceship_earth_facets_light_in_tinks_wake():
    earth = _earth()
    for facet in earth.facets:
        lit_at = facet[5]
        before = earth.facet_rgb(facet, max(0.0, lit_at - 0.01))
        after = earth.facet_rgb(facet, lit_at + earth.FADE_S)
        assert sum(after) > sum(before), "dark until her dust reaches it, lit after"
    assert max(f[5] for f in earth.facets) <= earth.SPIRAL_S


@pytest.mark.parametrize("height", [32, 64])
def test_spaceship_earth_tink_lands_on_its_shoulder_inside_the_board(height):
    earth = _earth(height)
    end = _scene_s(landmarks.SpaceshipEarthLandmark)
    assert earth.SPIRAL_S + earth.FLIT_S + 0.5 <= end, "time to see her land and pose"
    x, y, front = earth.tink_at(end)
    assert front
    assert earth.tink_w / 2 <= x <= earth.width - earth.tink_w / 2
    assert earth.tink_h / 2 - 1 <= y <= earth.height - earth.tink_h / 2
    assert x > earth.cx and y < earth.cy, "on its upper right shoulder"


def test_spaceship_earth_palette_wraps_a_hair_below_zero():
    # -1e-18 % 1.0 == 1.0 in Python: it indexed past the palette on CI for the centre facet.
    earth = _earth(32)
    assert earth._palette(-1e-18) == earth._palette(0.0) == earth.PALETTE[0]
    assert earth._palette(1.0) == earth.PALETTE[0]
