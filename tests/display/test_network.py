# tests/display/test_network.py
import display.network as network
from updater.shared import note_network_result


class FakeCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        assert 0 <= x < self.width and 0 <= y < self.height, f"({x}, {y}) is off the board"
        self.px[(x, y)] = (r, g, b)


def test_badge_sits_in_the_bottom_right_corner_on_both_boards():
    for height in (32, 64):
        canvas = FakeCanvas(64, height)
        network.draw_network_badge(canvas)
        xs = {x for x, _ in canvas.px}
        ys = {y for _, y in canvas.px}
        assert (min(xs), max(xs)) == (57, 63)
        assert (min(ys), max(ys)) == (height - 7, height - 1)


def test_badge_is_red_with_a_white_exclamation_mark():
    canvas = FakeCanvas(64, 32)
    network.draw_network_badge(canvas)
    assert canvas.px[(57, 25)] == (255, 0, 0)
    stroke = [canvas.px[(60, y)] for y in range(26, 29)]
    assert stroke == [(255, 255, 255)] * 3
    assert canvas.px[(60, 29)] == (255, 0, 0), "gap between the stroke and the dot"
    assert canvas.px[(60, 30)] == (255, 255, 255)


def test_draws_nothing_while_online():
    canvas = FakeCanvas(64, 32)
    network.draw_if_offline(canvas)
    assert canvas.px == {}


def test_draws_the_badge_once_offline_and_stops_once_back():
    note_network_result(False)
    canvas = FakeCanvas(64, 32)
    network.draw_if_offline(canvas)
    assert canvas.px[(63, 31)] == (255, 0, 0)

    note_network_result(True)
    canvas = FakeCanvas(64, 32)
    network.draw_if_offline(canvas)
    assert canvas.px == {}
