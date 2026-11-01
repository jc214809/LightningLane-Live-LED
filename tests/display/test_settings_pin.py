import pytest

import display.settings_pin as overlay
from display.settings_pin import BLACK, GOLD, WHITE, draw_pin


class FakeCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        assert 0 <= x < self.width and 0 <= y < self.height, f"({x}, {y}) is off the board"
        self.px[(x, y)] = (r, g, b)


@pytest.mark.parametrize("height", [32, 64])
def test_the_pin_sits_centred_in_a_gold_edged_box_on_both_boards(height):
    canvas = FakeCanvas(64, height)
    draw_pin(canvas, "8888")
    xs = sorted({x for x, _ in canvas.px})
    ys = sorted({y for _, y in canvas.px})
    w, h = xs[-1] - xs[0] + 1, ys[-1] - ys[0] + 1
    assert (w, h) == (36, 16)
    assert xs[0] == (64 - w) // 2 and ys[0] == (height - h) // 2
    assert canvas.px[(xs[0], ys[0])] == GOLD and canvas.px[(xs[-1], ys[-1])] == GOLD
    assert canvas.px[(xs[0] + 1, ys[0] + 1)] == BLACK


def test_each_digit_is_drawn_twice_size():
    canvas = FakeCanvas(64, 32)
    draw_pin(canvas, "1000")
    left, top = (64 - 36) // 2 + 3, (32 - 16) // 2 + 3
    # "1" is .#. on its first row: its middle column, 2x2
    assert [canvas.px[(left + 2 + dx, top + dy)] for dx in (0, 1) for dy in (0, 1)] == [WHITE] * 4
    assert canvas.px[(left, top)] == BLACK


def test_only_while_a_pin_is_up(monkeypatch):
    canvas = FakeCanvas(64, 32)
    overlay.draw_if_pin_shown(canvas)
    assert canvas.px == {}
    monkeypatch.setattr(overlay, "shown_pin", lambda: "4321")
    overlay.draw_if_pin_shown(canvas)
    assert WHITE in canvas.px.values()
