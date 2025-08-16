# tests/display/park/test_park_details.py

from display.park import park_details
from display.park.park_details import (
    render_special_ticketed_events,
    render_park_hours,
    render_weather_icon,
    display_weather_icon_and_description,
    format_iso_time,
    draw_multi_line_park_name_text_block,
    draw_single_line_park_name_text
)

# --- Set up dummy dependencies ---
# Fake font used for testing.
class FakeFont:
    def __init__(self, height, text_width=5):
        self.height = height
        self.text_width = text_width

# Fake implementations for get_text_width and wrap_text.
def fake_get_text_width(font, text):
    # Let's assume each character is 'font.text_width' wide.
    return len(text) * font.text_width

def fake_wrap_text(font, text, board_width, pad):
    # For simplicity, split the text by spaces.
    return text.split()

# Dummy color dictionary.
dummy_color_dict = {
    "gold": "#FFD700",
    "disney_blue": "#0033A0",
    "white": "#FFFFFF",
    "mickey_mouse_red": "#E41A1C"
}

# Dummy loaded_fonts dictionary.
dummy_loaded_fonts = {
    "info": FakeFont(height=10, text_width=5),
    "park": FakeFont(height=12, text_width=6)
}

# Override dependencies in park_details.
park_details.get_text_width = fake_get_text_width
park_details.wrap_text = fake_wrap_text
park_details.color_dict = dummy_color_dict
park_details.loaded_fonts = dummy_loaded_fonts

# Create a FakeMatrix for testing.
class FakeMatrix:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.clear_called = 0
        self.image_set = None
    def Clear(self):
        self.clear_called += 1
    def SetImage(self, image, x=0, y=0):
        self.image_set = {"image": image, "x": x, "y": y}

# Use a recorder to capture calls to graphics.DrawText.
class TextRecorder:
    def __init__(self):
        self.calls = []
    def record(self, matrix, font, x, y, color, text):
        self.calls.append({
            "matrix": matrix,
            "font": font,
            "x": x,
            "y": y,
            "color": color,
            "text": text
        })

text_recorder = TextRecorder()
# Patch the graphics.DrawText function.
park_details.graphics.DrawText = lambda matrix, font, x, y, color, text: text_recorder.record(matrix, font, x, y, color, text)

# --- Tests ---

def test_render_lightning_lane_multi_pass_price():
    fake_matrix = FakeMatrix(width=100, height=32)
    text_recorder.calls = []
    # Test with price missing '$'
    park_details.render_lightning_lane_multi_pass_price(20, 5, fake_matrix, "15")
    assert any(call["text"] == "$15" for call in text_recorder.calls)
    # Test with price already starting with '$'
    text_recorder.calls = []
    park_details.render_lightning_lane_multi_pass_price(20, 5, fake_matrix, "$20")
    assert any(call["text"] == "$20" for call in text_recorder.calls)

def test_format_iso_time_valid():
    iso_str = "2025-03-17T09:00:00-04:00"
    formatted = format_iso_time(iso_str)
    # Expect the formatted time to end with AM or PM.
    assert formatted.endswith("AM") or formatted.endswith("PM")

def test_format_iso_time_invalid(monkeypatch):
    # Create a dummy datetime class that always raises a ValueError.
    class DummyDatetime:
        @staticmethod
        def fromisoformat(s):
            raise ValueError("bad format")
    # Patch park_details.datetime with our dummy.
    monkeypatch.setattr(park_details, "datetime", DummyDatetime)
    formatted = format_iso_time("badtime")
    assert formatted == "badtime"

def test_draw_multi_line_park_name_text_block():
    fake_matrix = FakeMatrix(width=200, height=64)
    lines = ["Magic", "Kingdom"]
    text_recorder.calls = []
    draw_multi_line_park_name_text_block(fake_matrix, lines)
    # Expect at least two DrawText calls.
    assert len(text_recorder.calls) >= 2
    texts = [call["text"] for call in text_recorder.calls]
    assert "Magic" in texts or "Kingdom" in texts

def test_draw_single_line_park_name_text():
    fake_matrix = FakeMatrix(width=200, height=64)
    text_recorder.calls = []
    draw_single_line_park_name_text(fake_matrix, dummy_loaded_fonts["info"], "Disney", 200, 64)
    assert any(call["text"] == "Disney" for call in text_recorder.calls)

def test_render_special_ticketed_events():
    fake_matrix = FakeMatrix(width=200, height=64)
    text_recorder.calls = []
    render_special_ticketed_events(50, fake_matrix, "9AM-10PM")
    assert any("*" in call["text"] for call in text_recorder.calls)

def test_render_park_hours():
    fake_matrix = FakeMatrix(width=200, height=64)
    text_recorder.calls = []
    park_obj = {
        "openingTime": "2025-03-17T09:00:00-04:00",
        "closingTime": "2025-03-17T22:00:00-04:00",
        "specialTicketedEvent": False
    }
    render_park_hours(60, 10, fake_matrix, park_obj)
    assert any("-" in call["text"] for call in text_recorder.calls)

def test_render_weather_icon_success(monkeypatch):
    # Create a dummy response for requests.get.
    class DummyResponse:
        def __init__(self, content):
            self.content = content
        def raise_for_status(self):
            pass
    def dummy_get(url):
        return DummyResponse(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(park_details, "requests", type("r", (), {"get": dummy_get, "RequestException": Exception}))
    # Patch PIL.Image.open to return a fake image.
    class FakeImage:
        def __init__(self):
            self.width = 15
        def resize(self, size):
            self.width = size[0]
            return self
    monkeypatch.setattr(park_details, "Image", type("PILImage", (), {"open": lambda f: FakeImage()}))
    park_details.icon_cache.clear()
    img = render_weather_icon("01d")
    assert img is not None
    # Ensure caching: calling again returns the same object.
    cached = render_weather_icon("01d")
    assert cached is img

def test_render_weather_icon_failure(monkeypatch):
    # Dummy get that simulates a network failure.
    def dummy_get(url):
        raise Exception("Network error")
    monkeypatch.setattr(park_details, "requests", type("r", (), {"get": dummy_get, "RequestException": Exception}))
    park_details.icon_cache.clear()
    img = render_weather_icon("badcode")
    assert img is None

def test_display_weather_icon_and_description(monkeypatch):
    fake_matrix = FakeMatrix(width=128, height=32)
    text_recorder.calls = []
    weather_info = {
        "temperature": "75°F",
        "icon": "01d",
        "short_description": "Sunny"
    }
    class FakeImage:
        def __init__(self):
            self.width = 15
            self.height = 15
        def convert(self, mode):
            return self
    monkeypatch.setattr(park_details, "render_weather_icon", lambda code: FakeImage())
    display_weather_icon_and_description(fake_matrix, weather_info, font_height=10, show_icon=True)
    texts = [call["text"] for call in text_recorder.calls]
    assert any("75°F" in t for t in texts) or any("Sunny" in t for t in texts)


def test_display_weather_icon_and_description_high_resolution(monkeypatch):
    """
    Test display_weather_icon_and_description for a high-resolution LED matrix (height >= 64).
    We expect the branch for matrix.height >= 64 to execute.
    """
    # Create a FakeMatrix with height >= 64.
    fake_matrix = FakeMatrix(width=128, height=64)
    text_recorder.calls = []  # Clear any previous DrawText records.

    # Dummy weather info:
    weather_info = {
        "temperature": "75°F",
        "icon": "01d",
        "short_description": "Sunny"
    }

    # Define a FakeImage with known dimensions.
    class FakeImage:
        def __init__(self):
            self.width = 15
            self.height = 15

        def convert(self, mode):
            return self

    # Patch render_weather_icon to return our FakeImage.
    monkeypatch.setattr(park_details, "render_weather_icon", lambda code: FakeImage())

    # Call display_weather_icon_and_description with show_icon=True.
    display_weather_icon_and_description(fake_matrix, weather_info, font_height=10, show_icon=True)

    # Expect the weather branch for high resolution to construct a combined weather text.
    expected_weather_text = "75°F Sunny"
    # Check that at least one DrawText call used this expected_weather_text.
    assert any(expected_weather_text in call["text"] for call in text_recorder.calls), \
        "Expected weather text not found in DrawText calls for high resolution matrix."


# Test render_park_information_screen for low resolution (height == 32)
def test_render_park_information_screen_low_res(monkeypatch):
    calls = {"draw_multi": None, "display_weather": None, "render_hours": None, "render_llmp": None}

    # Fake implementation to record the lines for the park name.
    def fake_draw_multi_line(matrix, lines):
        calls["draw_multi"] = lines

    monkeypatch.setattr(park_details, "draw_multi_line_park_name_text_block", fake_draw_multi_line)

    # Capture call to display_weather_icon_and_description.
    def fake_display_weather(matrix, weather, font_height):
        calls["display_weather"] = (weather, font_height)

    monkeypatch.setattr(park_details, "display_weather_icon_and_description", fake_display_weather)

    # Record render_park_hours call.
    def fake_render_hours(vertical, horizontal, matrix, park_obj):
        calls["render_hours"] = (vertical, horizontal)

    monkeypatch.setattr(park_details, "render_park_hours", fake_render_hours)

    # Record render_lightning_lane_multi_pass_price call.
    def fake_render_llmp(vertical, horizontal, matrix, price):
        calls["render_llmp"] = (vertical, horizontal, price)

    monkeypatch.setattr(park_details, "render_lightning_lane_multi_pass_price", fake_render_llmp)

    # Force wrap_text to simply return the park name as a single line.
    monkeypatch.setattr(park_details, "wrap_text", lambda font, text, board_width, pad: [text])

    # Construct a park object that includes weather and llmpPrice.
    park_obj = {
        "name": "Test Park",
        "weather": {"temperature": "70°F", "icon": "01d", "short_description": "Sunny"},
        "llmpPrice": "15",
        "openingTime": "2020-01-01T09:00:00-00:00",
        "closingTime": "2020-01-01T20:00:00-00:00"
    }
    # Create a FakeMatrix with height 32.
    fake_matrix = FakeMatrix(width=64, height=32)
    baseline = fake_matrix.height - 1
    info_font_height = getattr(park_details.loaded_fonts["info"], "height")

    # Call render_park_information_screen.
    park_details.render_park_information_screen(fake_matrix, park_obj)

    # For board_height == 32 branch:
    # 1. draw_multi_line_park_name_text_block should have been called with wrapped name ["Test Park"].
    # 2. Because park_obj contains weather, display_weather_icon_and_description should be called with the weather dict and info_font_height.
    # 3. render_park_hours is called with vertical = baseline, horizontal = 1.
    # 4. render_lightning_lane_multi_pass_price is called with vertical = baseline - info_font_height, horizontal = 1, and price "15".
    assert calls["draw_multi"] == ["Test Park"]
    assert calls["display_weather"] == (park_obj["weather"], info_font_height)
    assert calls["render_hours"] == (baseline, 1)
    assert calls["render_llmp"] == (baseline - info_font_height, 1, "15")


# Test render_park_information_screen for high resolution (height >= 64)
def test_render_park_information_screen_high_res(monkeypatch):
    calls = {"draw_multi": None, "display_weather": None, "render_hours": None, "render_llmp": None}

    def fake_draw_multi_line(matrix, lines):
        calls["draw_multi"] = lines

    monkeypatch.setattr(park_details, "draw_multi_line_park_name_text_block", fake_draw_multi_line)

    def fake_display_weather(matrix, weather, font_height):
        calls["display_weather"] = (weather, font_height)

    monkeypatch.setattr(park_details, "display_weather_icon_and_description", fake_display_weather)

    def fake_render_hours(vertical, horizontal, matrix, park_obj):
        calls["render_hours"] = (vertical, horizontal)

    monkeypatch.setattr(park_details, "render_park_hours", fake_render_hours)

    def fake_render_llmp(vertical, horizontal, matrix, price):
        calls["render_llmp"] = (vertical, horizontal, price)

    monkeypatch.setattr(park_details, "render_lightning_lane_multi_pass_price", fake_render_llmp)

    monkeypatch.setattr(park_details, "wrap_text", lambda font, text, board_width, pad: [text])

    park_obj = {
        "name": "Test Park",
        "weather": {"temperature": "70°F", "icon": "01d", "short_description": "Sunny"},
        "llmpPrice": "15",
        "openingTime": "2020-01-01T09:00:00-00:00",
        "closingTime": "2020-01-01T20:00:00-00:00"
    }

    # Create a FakeMatrix with height 64.
    fake_matrix = FakeMatrix(width=128, height=64)
    baseline = fake_matrix.height - 1
    # Calculate expected horizontal for lightning lane price:
    expected_horizontal = fake_matrix.width - park_details.get_text_width(park_details.loaded_fonts["info"],
                                                                          park_obj["llmpPrice"])

    park_details.render_park_information_screen(fake_matrix, park_obj)

    # For high resolution branch:
    # 1. draw_multi_line_park_name_text_block is called with ["Test Park"].
    # 2. Because weather exists, display_weather_icon_and_description is called with the weather dict and info_font_height.
    # 3. render_lightning_lane_multi_pass_price is called with vertical = baseline, horizontal = expected_horizontal, and price "15".
    # 4. render_park_hours is called with vertical = baseline, horizontal = 1.
    info_font_height = getattr(park_details.loaded_fonts["info"], "height")
    assert calls["draw_multi"] == ["Test Park"]
    assert calls["display_weather"] == (park_obj["weather"], info_font_height)
    assert calls["render_llmp"] == (baseline, expected_horizontal, "15")
    assert calls["render_hours"] == (baseline, 1)
