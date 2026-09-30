"""Putting pixel art on the board."""

import display.animation as animation

from tests.display.animation.support import FLYBYS, FakeCanvas


def test_sprite_art_rows_are_even_and_use_defined_colors():
    for cls in FLYBYS:
        assert len({len(row) for row in cls.art}) == 1
        assert {ch for row in cls.art for ch in row} - {"."} <= set(cls.colors)


def test_art_pixels_scales_each_lit_cell_and_skips_empty_ones():
    got = dict(animation.art_pixels(["A.", ".B"], 10, 20, {"A": (1, 1, 1), "B": (2, 2, 2)}, scale=2))
    assert got == {(10, 20): (1, 1, 1), (11, 20): (1, 1, 1), (10, 21): (1, 1, 1), (11, 21): (1, 1, 1),
                   (12, 22): (2, 2, 2), (13, 22): (2, 2, 2), (12, 23): (2, 2, 2), (13, 23): (2, 2, 2)}


def test_paint_sets_only_pixels_on_the_board_from_a_dict_or_pairs():
    canvas = FakeCanvas(4, 3)
    animation.paint(canvas, {(0, 0): (9, 9, 9), (4, 0): (1, 1, 1), (-1, 2): (1, 1, 1)}, 4, 3)
    animation.paint(canvas, [((3, 2), (5, 5, 5)), ((3, 3), (1, 1, 1))], 4, 3)
    assert canvas.px == {(0, 0): (9, 9, 9), (3, 2): (5, 5, 5)}
