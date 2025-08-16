import sys
import types

# Provide a minimal 'driver' module before importing attraction_info
graphics_stub = types.SimpleNamespace()


class Font:
    def CharacterWidth(self, _):
        return 1

    def LoadFont(self, _):
        pass


graphics_stub.Font = Font
graphics_stub.DrawText = lambda *a, **k: None
graphics_stub.Color = lambda r, g, b: (r, g, b)

sys.modules['driver'] = types.SimpleNamespace(graphics=graphics_stub)

from display.attractions.attraction_info import (
    get_longest_line_width,
    calculate_x_position,
    calculate_y_position,
    render_attraction_info,
    loaded_fonts,
    wrap_text  # Assuming wrap_text is used inside render_attraction_info
)


class DummyFont:
    def __init__(self, width, height=10):
        self.width = width
        self.height = height

    def CharacterWidth(self, _):
        return self.width


class DummyMatrix:
    def __init__(self, width, height):
        self.width = width
        self.height = height


def test_get_longest_line_width():
    ride_font = DummyFont(width=2)
    wait_font = DummyFont(width=1)
    wrapped = ["RideA"]
    combined = ["RideA", "10"]
    result = get_longest_line_width(wrapped, combined, ride_font, wait_font)
    expected = max(len("RideA") * 2, len("10") * 1)
    assert result == expected


def test_calculate_x_position():
    matrix = DummyMatrix(20, 10)
    assert calculate_x_position(matrix, 10, 2) == 3
    matrix = DummyMatrix(10, 10)
    assert calculate_x_position(matrix, 10, 2) == 0


def test_calculate_y_position():
    matrix = DummyMatrix(10, 32)
    assert calculate_y_position(matrix, 10) == 11


def test_render_attraction_info(monkeypatch):
    # Ensure the 'ride' font is defined in loaded_fonts.
    loaded_fonts["ride"] = DummyFont(width=5, height=10)
    # Optionally, also patch other fonts if needed.
    loaded_fonts["waittime"] = DummyFont(width=5, height=10)
    loaded_fonts["info"] = DummyFont(width=5, height=10)

    # Create a FakeMatrix instance.
    class FakeMatrix:
        def __init__(self, width, height):
            self.width = width
            self.height = height
            self.draw_calls = []

        def Clear(self):
            pass

    fake_matrix = FakeMatrix(width=100, height=32)

    # Call render_attraction_info.
    dummy_attraction = {"name": "Space Mountain", "entityType": "ATTRACTION", "waitTime": "45", "status": "OPERATING"}
    render_attraction_info(fake_matrix, dummy_attraction)

    # For basic test purposes, just check that render_attraction_info runs without KeyError.
    # (More in-depth tests would patch graphics.DrawText to record draw calls.)
    assert True