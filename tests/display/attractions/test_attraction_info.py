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


def test_boarding_group_3digit_fits_32row(monkeypatch):
    """Groups 100-200 on a 32-row board: all draw calls must land within board height."""
    import display.attractions.attraction_info as mod

    loaded_fonts["ride"] = DummyFont(width=5, height=8)
    loaded_fonts["waittime"] = DummyFont(width=4, height=6)

    calls = []
    monkeypatch.setattr(mod.graphics, "DrawText", lambda matrix, font, x, y, color, text: calls.append((y, text)))

    class FakeMatrix:
        width, height = 32, 32
        def Clear(self): pass

    mod.render_attraction_info(
        FakeMatrix(),
        {"name": "Tron", "entityType": "ATTRACTION", "waitTime": "Groups 100-200", "status": "OPERATING"}
    )
    assert calls, "No DrawText calls were made"
    for y, text in calls:
        assert y <= 32, f"Text '{text}' drawn at y={y}, outside 32-row board"


def test_boarding_group_3digit_fits_64row(monkeypatch):
    """Groups 100-200 on a 64-row board: all draw calls must land within board height."""
    import display.attractions.attraction_info as mod

    loaded_fonts["ride"] = DummyFont(width=5, height=8)
    loaded_fonts["waittime"] = DummyFont(width=5, height=8)

    calls = []
    monkeypatch.setattr(mod.graphics, "DrawText", lambda matrix, font, x, y, color, text: calls.append((y, text)))

    class FakeMatrix:
        width, height = 64, 64
        def Clear(self): pass

    mod.render_attraction_info(
        FakeMatrix(),
        {"name": "Tron", "entityType": "ATTRACTION", "waitTime": "Groups 100-200", "status": "OPERATING"}
    )
    assert calls, "No DrawText calls were made"
    for y, text in calls:
        assert y <= 64, f"Text '{text}' drawn at y={y}, outside 64-row board"


def test_wait_time_formatting_integer():
    """Numeric wait times get ' Mins' appended."""
    from display.attractions.attraction_info import _format_wait_time
    assert _format_wait_time(45) == "45 Mins"

def test_wait_time_formatting_down():
    """'Down X' strings still get ' Mins' appended."""
    from display.attractions.attraction_info import _format_wait_time
    assert _format_wait_time("Down 15") == "Down 15 Mins"

def test_wait_time_formatting_boarding_group_range():
    """Boarding group range strings are used as-is."""
    from display.attractions.attraction_info import _format_wait_time
    assert _format_wait_time("Groups 1-50") == "Groups 1-50"

def test_wait_time_formatting_boarding_group_single():
    """Single boarding group strings are used as-is."""
    from display.attractions.attraction_info import _format_wait_time
    assert _format_wait_time("Group 1+") == "Group 1+"