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


def test_walking_pixels_steps_the_feet_and_leaves_the_body():
    art = ["BBBB", "BBBB", "F..G"]
    colors = {"B": (1, 1, 1), "F": (2, 2, 2), "G": (3, 3, 3)}
    feet = (2, range(0, 2), range(2, 4))
    standing = dict(animation.walking_pixels(art, 0, 0, colors, feet, None))
    assert standing == dict(animation.art_pixels(art, 0, 0, colors))
    apart = dict(animation.walking_pixels(art, 0, 0, colors, feet, 0))
    assert apart[(-1, 2)] == (2, 2, 2) and apart[(4, 2)] == (3, 3, 3), "striding apart"
    lifted = dict(animation.walking_pixels(art, 0, 0, colors, feet, 1))
    assert lifted[(0, 1)] == (2, 2, 2) and (0, 2) not in lifted, "back foot up, over the leg"
    assert lifted[(3, 2)] == (3, 3, 3), "front foot planted"
    assert dict(animation.walking_pixels(art, 0, 0, colors, feet, 5)) == lifted, "the cycle repeats"


def test_walking_pixels_steps_the_other_way_facing_left():
    art = ["BBBB", "G..F"]
    colors = {"B": (1, 1, 1), "F": (2, 2, 2), "G": (3, 3, 3)}
    feet = (1, range(2, 4), range(0, 2))  # facing left, the foot behind is on the right
    apart = dict(animation.walking_pixels(art, 0, 0, colors, feet, 0, facing=-1))
    assert apart[(4, 1)] == (2, 2, 2) and apart[(-1, 1)] == (3, 3, 3)


def test_walking_pixels_steps_whole_cells_at_scale():
    art = ["BB", "FG"]
    colors = {"B": (1, 1, 1), "F": (2, 2, 2), "G": (3, 3, 3)}
    feet = (1, range(0, 1), range(1, 2))
    lifted = dict(animation.walking_pixels(art, 0, 0, colors, feet, 1, scale=2))
    assert lifted[(0, 0)] == (2, 2, 2) and lifted[(1, 1)] == (2, 2, 2), "back foot up a whole cell"
    assert lifted[(2, 2)] == (3, 3, 3) and lifted[(3, 3)] == (3, 3, 3), "front foot planted"
