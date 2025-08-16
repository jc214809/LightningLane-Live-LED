# tests/display/countdown/test_countdown.py
from datetime import datetime, timedelta
import pytest

from display.countdown.countdown import (
    wrap_text_in_lines,
    draw_countdown_text,
    render_countdown_to_disney
)
import display.countdown.countdown as countdown


# Define a dummy font for testing.
class DummyFont:
    def __init__(self, height, char_width):
        self.height = height
        self.char_width = char_width


# Dummy get_text_width function: each character is font.char_width pixels.
def dummy_get_text_width(font, text):
    return len(text) * font.char_width


# Patch the get_text_width in the countdown module.
@pytest.fixture(autouse=True)
def patch_get_text_width(monkeypatch):
    monkeypatch.setattr(countdown, "get_text_width", dummy_get_text_width)


# Create a DummyFont instance for the countdown font.
dummy_countdown_font = DummyFont(height=10, char_width=5)
# Also, patch loaded_fonts to include a dummy countdown font.
countdown.loaded_fonts["countdown"] = dummy_countdown_font

# Create a dummy color_dict for testing.
dummy_color_dict = {
    "mickey_mouse_red": (242, 5, 5)  # using a tuple as a dummy color representation
}
monkeypatch = pytest.MonkeyPatch()
monkeypatch.setattr(countdown, "color_dict", dummy_color_dict)


# Create a FakeMatrix for testing draw functions.
class FakeMatrix:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.draw_text_calls = []

    def Clear(self):
        pass

    def SetImage(self, image, x=0, y=0):
        pass


# Test for wrap_text_in_lines:
def test_wrap_text_in_lines():
    # Our dummy get_text_width returns len(text)*font.char_width.
    # Use a font with char_width 5.
    dummy_font = DummyFont(height=10, char_width=5)
    # Example: text that can be wrapped.
    text = "This is a test"
    # Set max_width such that words fit normally.
    # For our dummy font: "This" -> 4*5 = 20, "is" -> 2*5 = 10, etc.
    max_width = 50  # Allow up to 10 characters.
    lines = wrap_text_in_lines(dummy_font, text, max_width)
    # Depending on spacing, we expect the function to break the text into multiple lines
    # For instance, if "This is" fits but adding "a" might reach exactly 10 chars.
    # We'll simply assert that the returned value is a non-empty list.
    assert isinstance(lines, list)
    assert len(lines) > 0


# Test for draw_countdown_text:
def test_draw_countdown_text(monkeypatch):
    # Create a FakeMatrix with set width
    fake_matrix = FakeMatrix(width=200, height=64)
    calls = []

    # Patch graphics.DrawText to record its calls.
    def fake_draw_text(matrix, font, x, y, color, text):
        calls.append({"x": x, "y": y, "color": color, "text": text})

    monkeypatch.setattr(countdown, "graphics", type("DummyGraphics", (), {"DrawText": fake_draw_text}))

    # Call draw_countdown_text with a sample text.
    sample_text = "COUNTDOWN TO DISNEY 5 Days"
    # Assuming the font height is 10, total lines = 1 (if wrapped doesn't split).
    draw_countdown_text(fake_matrix, 40, sample_text)

    # Verify that at least one DrawText call was made.
    assert len(calls) > 0
    # Also, check that the text drawn equals sample_text (if wrapping doesn't split).
    # If wrapping does split, then the combined lines should equal sample_text split appropriately.
    drawn_texts = [call["text"] for call in calls]
    combined = " ".join(drawn_texts)
    # Normalize whitespace for comparison.
    assert "COUNTDOWN TO DISNEY" in combined


# Test for render_countdown_to_disney:
def test_render_countdown_to_disney_future(monkeypatch):
    # We'll patch draw_countdown_text to capture the countdown string.
    recorded = {}

    def fake_draw_countdown_text(matrix, y, text):
        recorded["text"] = text

    monkeypatch.setattr(countdown, "draw_countdown_text", fake_draw_countdown_text)

    # Set a future trip_date.
    future_date = datetime.now() + timedelta(days=7)
    fake_matrix = FakeMatrix(width=200, height=64)

    render_countdown_to_disney(fake_matrix, future_date)

    # We expect the countdown_string to be: "COUNTDOWN TO DISNEY 7 Days"
    # (Depending on singular/plural formatting – it's "Day" for 1 and "Days" for >1)
    text = recorded.get("text", "")
    assert "COUNTDOWN TO DISNEY" in text
    assert "7 Day" in text  # either "7 Day" or "7 Days" should be present


def test_render_countdown_to_disney_non_future(monkeypatch):
    # Test when trip_date is not in the future
    recorded = {}

    def fake_draw_countdown_text(matrix, y, text):
        recorded["text"] = text

    monkeypatch.setattr(countdown, "draw_countdown_text", fake_draw_countdown_text)

    # Set a trip_date that is today or in the past.
    past_date = datetime.now() - timedelta(days=1)
    fake_matrix = FakeMatrix(width=200, height=64)

    render_countdown_to_disney(fake_matrix, past_date)

    # Expect the default message.
    assert recorded.get("text", "") == "Have a Magical Trip!"


# Clean up monkeypatch fixture (if necessary)
@pytest.fixture(autouse=True)
def restore_monkeypatch(monkeypatch):
    yield
    monkeypatch.undo()