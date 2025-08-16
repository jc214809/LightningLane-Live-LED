# tests/display/test_display.py
import os
import tempfile
import pytest
from display.display import fonts, initialize_fonts, colors, get_text_width, wrap_text
from display.display import loaded_fonts  # Import the global loaded_fonts variable

# Create dummy implementations for graphics.Font and graphics.Color
class DummyFont:
    def __init__(self):
        self.loaded = False
    def LoadFont(self, path):
        if not os.path.exists(path):
            raise Exception("Font file not found")
        self.loaded = True
    def CharacterWidth(self, char_code):
        return 5

class DummyColor:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

# --- Tests for fonts() ---
def test_fonts():
    font_dict = fonts()
    assert 32 in font_dict
    assert 64 in font_dict
    for board_size in font_dict:
        assert isinstance(font_dict[board_size], dict)
        for key in ["park", "info", "waittime", "ride", "countdown"]:
            assert key in font_dict[board_size]

# --- Fixture to patch graphics and os.path.exists ---
@pytest.fixture(autouse=True)
def patch_graphics(monkeypatch):
    import display.display as disp
    dummy_graphics = type("DummyGraphics", (), {})()
    dummy_graphics.Font = lambda: DummyFont()
    dummy_graphics.Color = lambda r, g, b: DummyColor(r, g, b)
    monkeypatch.setattr(disp, "graphics", dummy_graphics)
    # Patch os.path.exists to always return True for font files.
    monkeypatch.setattr(os.path, "exists", lambda path: True)

def test_initialize_fonts_success(monkeypatch):
    # Reset loaded_fonts from display.display.
    from display.display import loaded_fonts
    loaded_fonts.clear()
    dummy_loaded = initialize_fonts(32)
    assert dummy_loaded is not None
    expected_keys = set(fonts()[32].keys())
    assert set(dummy_loaded.keys()) == expected_keys
    for font in dummy_loaded.values():
        assert font.loaded is True

def test_initialize_fonts_no_definition(monkeypatch):
    import display.display as disp
    messages = []
    monkeypatch.setattr(disp, "debug", type("DummyDebug", (), {"error": lambda self, msg: messages.append(msg)})())
    result = initialize_fonts(999)
    assert result is None
    assert any("No font definitions found for height" in msg for msg in messages)

def test_colors():
    color_dict = colors()
    for expected in ["mickey_mouse_red", "disney_blue", "white", "down", "gold"]:
        assert expected in color_dict
        c = color_dict[expected]
        assert hasattr(c, "r") and hasattr(c, "g") and hasattr(c, "b")

def test_get_text_width():
    class Dummy:
        def CharacterWidth(self, char):
            return 5
    dummy_font = Dummy()
    width = get_text_width(dummy_font, "abc")
    assert width == 15

def test_wrap_text():
    class Dummy:
        def CharacterWidth(self, char):
            return 5
    dummy_font = Dummy()
    result = wrap_text(dummy_font, "Hello World", 40, 5)
    assert result == ["Hello", "World"]

def test_initialize_fonts_font_load_failure(monkeypatch):
    """
    Test that initialize_fonts() correctly catches exceptions during font loading.
    It forces Font.LoadFont() to always raise an exception, and then verifies that
    debug.error() is called and that loaded_fonts remains empty.
    """
    from display.display import initialize_fonts, fonts, loaded_fonts, debug

    # Clear any previously loaded fonts.
    loaded_fonts.clear()

    # Patch os.path.exists so that every font file is considered to exist.
    monkeypatch.setattr("os.path.exists", lambda path: True)

    # Create a fake Font class whose LoadFont method always raises an exception.
    class FailingFont:
        def LoadFont(self, path):
            raise Exception("Test load error")
        def CharacterWidth(self, char):
            return 5

    # Patch the graphics.Font in display.display to always return FailingFont.
    monkeypatch.setattr("display.display.graphics.Font", lambda: FailingFont())

    # Capture debug.error messages.
    error_messages = []
    monkeypatch.setattr(debug, "error", lambda msg: error_messages.append(msg))

    # Call initialize_fonts() with a supported board height (e.g., 32).
    result = initialize_fonts(32)

    # Since all font loads fail, result should be an empty dict.
    assert result == {}

    # The fonts() dictionary for board height 32 should have a number of keys.
    expected_count = len(fonts()[32])
    # We expect an error for each font attempted.
    assert len(error_messages) == expected_count, f"Expected {expected_count} error messages, got {len(error_messages)}: {error_messages}"

    # Optionally, ensure at least one of the error messages contains the expected text.
    for msg in error_messages:
        assert "Error loading font from path" in msg


def test_wrap_text_word_too_long():
    # Dummy font where every character is 10 pixels wide.
    class DummyFont:
        def CharacterWidth(self, char):
            return 10

    dummy_font = DummyFont()

    # Case 1: Test when current_line is non-empty and word doesn't fit.
    # For example, "Hi Hello world":
    # "Hi" width: 2*10 = 20, so it fits if max_width is 40.
    # "Hello" width: 5*10 = 50, which is > 40.
    # According to the code, if current_line exists (i.e. "Hi"), it is appended and then "Hello" is appended.
    # Continuing with "world" (which is 5*10 = 50), since current_line is empty, it's appended directly.
    text1 = "Hi Hello world"
    result1 = wrap_text(dummy_font, text1, 40, 0)
    # Expected output: ["Hi", "Hello", "world"]
    assert result1 == ["Hi", "Hello", "world"]

    # Case 2: When the first word itself is too long (current_line is empty).
    # For example, "Hello world" with max_width 40:
    # "Hello" (50) is too long and so goes on its own line, followed by "world" (50) on its own line.
    text2 = "Hello world"
    result2 = wrap_text(dummy_font, text2, 40, 0)
    assert result2 == ["Hello", "world"]