"""display.pixels: putting pixels on the board, shared across the board."""
import math

import pytest

from display import pixels


class Canvas:
    def __init__(self):
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        self.px[(x, y)] = (r, g, b)


def test_put_and_set_pixel_keep_to_the_board():
    scene, canvas = {}, Canvas()
    for x, y in ((0, 0), (3, 2), (4, 0), (-1, 1), (0, 3)):
        pixels.put(scene, x, y, (1, 2, 3), 4, 3)
        pixels.set_pixel(canvas, x, y, (1, 2, 3), 4, 3)
    assert set(scene) == set(canvas.px) == {(0, 0), (3, 2)}


def test_blend_lays_a_colour_over_what_is_beneath():
    assert pixels.blend((200, 100, 0), (0, 0, 100), 0.0) == (0, 0, 100)
    assert pixels.blend((200, 100, 0), (0, 0, 100), 1.0) == (200, 100, 0)
    assert pixels.blend((200, 100, 0), (0, 0, 100), 0.5) == (100, 50, 50)


def test_rotate_art_turns_exactly_and_four_turns_come_back():
    art = ["AB", ".C"]
    assert pixels.rotate_art(art, 1) == ["BC", "A."]
    assert pixels.rotate_art(art, 2) == ["C.", "BA"]
    assert pixels.rotate_art(art, 4) == art


def test_turn_takes_a_point_above_the_pivot_to_the_left():
    x, y = pixels.turn((0, -10), (0, 0), 90)
    assert (round(x, 6), round(y, 6)) == (-10, 0)
    x, y = pixels.turn((3, 4), (1, 1), -30)
    assert pixels.turn((x, y), (1, 1), 30) == pytest.approx((3, 4))


def test_rotate_cells_keeps_a_line_whole_and_on_its_new_angle():
    line = {(x, 10): "K" for x in range(10, 20)}
    turned = pixels.rotate_cells(line, (10.5, 10.5), 30)
    assert 8 <= len(turned) <= 12, "still about ten cells long"
    for x, y in turned:  # each cell near the line 30 degrees up from the pivot
        assert abs((10.5 - (y + 0.5)) - (x + 0.5 - 10.5) * math.tan(math.radians(30))) < 1.5
    rows = sorted({y for _, y in turned})
    assert rows == list(range(rows[0], rows[-1] + 1)), "no gaps: every row between its ends has a cell"
    assert max(x for x, _ in turned) > 16 and min(y for _, y in turned) < 7, "up and to the right"


def test_rotate_cells_keeps_kinds_and_moves_by_the_offset():
    art = {(0, 0): "A", (1, 0): "B", (0, 1): "C", (1, 1): "D"}
    assert pixels.rotate_cells(art, (1, 1), 0) == art
    assert pixels.rotate_cells(art, (1, 1), 0, offset=(3.0, -2.0)) == {(x + 3, y - 2): k for (x, y), k in art.items()}
    half = pixels.rotate_cells(art, (1, 1), 180)
    assert half == {(0, 0): "D", (1, 0): "C", (0, 1): "B", (1, 1): "A"}
    assert pixels.rotate_cells({}, (0, 0), 45) == {}


def test_noise_is_repeatable_and_spread_over_zero_to_one():
    values = [pixels.noise(x, y) for x in range(40) for y in range(40)]
    assert values == [pixels.noise(x, y) for x in range(40) for y in range(40)]
    assert 0.0 <= min(values) < 0.1 and 0.9 < max(values) <= 1.0
