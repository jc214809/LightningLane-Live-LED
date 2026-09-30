"""display.pixels: putting pixels on the board, shared across the board."""
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


def test_noise_is_repeatable_and_spread_over_zero_to_one():
    values = [pixels.noise(x, y) for x in range(40) for y in range(40)]
    assert values == [pixels.noise(x, y) for x in range(40) for y in range(40)]
    assert 0.0 <= min(values) < 0.1 and 0.9 < max(values) <= 1.0
