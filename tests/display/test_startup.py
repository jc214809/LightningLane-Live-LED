# tests/display/test_startup.py
import pytest
from display.startup import render_mickey_logo
from driver import graphics
from utils import debug

# Create a FakeMatrix for testing.
class FakeMatrix:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.draw_calls = []  # Record calls to DrawLine.
    def Clear(self):
        pass

def fake_draw_line(matrix, x1, y1, x2, y2, color):
    # Record the call parameters.
    matrix.draw_calls.append((x1, y1, x2, y2, color))

@pytest.fixture(autouse=True)
def patch_draw_line(monkeypatch):
    # Instead of monkeypatch.setattr (which fails if DrawLine doesn't exist),
    # we inject the attribute into graphics.__dict__
    monkeypatch.setitem(graphics.__dict__, "DrawLine", fake_draw_line)

@pytest.fixture
def record_debug(monkeypatch):
    messages = []
    monkeypatch.setattr(debug, "info", lambda msg: messages.append(msg))
    return messages

def test_render_mickey_logo(record_debug):
    # Create a FakeMatrix with arbitrary size so centering occurs. For example, 80x80.
    fake_matrix = FakeMatrix(width=80, height=80)

    # Call render_mickey_logo, which should draw a 40x40 Mickey silhouette in the center.
    render_mickey_logo(fake_matrix)

    # Check that some DrawLine calls were made.
    assert len(fake_matrix.draw_calls) > 0, "No pixels were drawn."

    # Calculate expected offsets
    shape_width = 40
    shape_height = 40
    offset_x = (fake_matrix.width - shape_width) // 2
    offset_y = (fake_matrix.height - shape_height) // 2

    # Verify that at least one drawn pixel lies within the expected region.
    drawn_pixels = fake_matrix.draw_calls
    in_region = any(
        offset_x <= x <= offset_x + shape_width and offset_y <= y <= offset_y + shape_height
        for (x, y, _, _, _) in drawn_pixels
    )
    assert in_region, "No drawn pixel is within the expected 40x40 centered region."

    # Verify the debug message was logged.
    assert any("Rendered fixed-size Mickey silhouette" in msg for msg in record_debug), \
        "Expected debug message not logged."