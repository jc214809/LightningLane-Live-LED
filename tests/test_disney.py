import json
import os
import tempfile
from datetime import datetime

import pytest

import disney  # Import your main module (disney.py)


# ---- Helper/Fake Classes ----

class FakeImage:
    def __init__(self):
        self.closed = False
    def convert(self, mode):
        return "converted_image"
    def close(self):
        self.closed = True

class FakeMatrix2:
    def __init__(self):
        self.clear_count = 0
        self.image_set = None
    def Clear(self):
        self.clear_count += 1
    def SetImage(self, img):
        self.image_set = img


class FakeMatrix:
    def __init__(self):
        self.clear_count = 0
        self.mickey_rendered = False
        self.park_info_rendered = False
        self.attraction_info_rendered = False
        self.countdown_rendered = False
        self.rendered_attractions = []
        self.countdown_called = False

    def Clear(self):
        self.clear_count += 1

    # Stub method to satisfy if SetImage is called.
    def SetImage(self, img):
        pass

# ---- Tests for load_config and validate_date ----

def test_load_config():
    # Create a temporary config file
    config_data = {"debug": True, "trip_countdown": {"trip_date": "2023-10-01", "enabled": True}}
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        json.dump(config_data, tmp)
        tmp_path = tmp.name

    # Use load_config from disney.py to read the file
    loaded_config = disney.load_config(tmp_path)
    os.unlink(tmp_path)  # Clean up

    assert loaded_config == config_data

def test_validate_date_valid():
    date_str = "2023-10-01"
    result = disney.validate_date(date_str)
    # Check that result is a datetime object with the expected date
    assert isinstance(result, datetime)
    assert result.year == 2023 and result.month == 10 and result.day == 1

def test_validate_date_invalid():
    invalid_date = "not-a-date"
    with pytest.raises(ValueError) as excinfo:
        disney.validate_date(invalid_date)
    assert "Invalid date format" in str(excinfo.value)

# ---- Tests for rendering functions ----

@pytest.fixture(autouse=True)
def disable_sleep(monkeypatch):
    # Override time.sleep globally to avoid delays during tests
    monkeypatch.setattr(__import__("time"), "sleep", lambda x: None)

def test_render_logo_without_image(monkeypatch):
    fake_matrix = FakeMatrix()
    # Ensure logo is not used by forcing os.path.exists to return False
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    # Override render_mickey_logo to record that it was called
    def fake_render_mickey_logo(matrix):
        matrix.mickey_rendered = True
    monkeypatch.setattr(disney, "render_mickey_logo", fake_render_mickey_logo)
    # Call render_logo; since use_image_logo is False by default, it should go to the else branch
    disney.render_logo(fake_matrix)
    assert fake_matrix.mickey_rendered is True

def test_initialize_park_information_screen(monkeypatch):
    fake_matrix = FakeMatrix()
    # Override render_park_information_screen to record the call
    called = False
    def fake_render_park_information_screen(matrix, park):
        nonlocal called
        called = True
    monkeypatch.setattr(disney, "render_park_information_screen", fake_render_park_information_screen)
    park = {"name": "Magic Kingdom"}
    disney.initialize_park_information_screen(fake_matrix, park)
    assert called is True
    # Also, ensure that Clear was called (at least once)
    assert fake_matrix.clear_count > 0

def test_loop_through_attractions(monkeypatch):
    fake_matrix = FakeMatrix()
    # Override render_attraction_info to mark call on the matrix
    def fake_render_attraction_info(matrix, attraction_info):
        matrix.attraction_info_rendered = True
    monkeypatch.setattr(disney, "render_attraction_info", fake_render_attraction_info)
    # Create a dummy park with one attraction that is operating
    park = {
        "name": "Magic Kingdom",
        "attractions": [
            {"name": "Space Mountain", "waitTime": "30", "status": "OPERATING"}
        ]
    }
    disney.loop_through_attractions(fake_matrix, park)
    assert fake_matrix.attraction_info_rendered is True

def test_show_trip_countdown(monkeypatch):
    fake_matrix = FakeMatrix()
    # Override render_countdown_to_disney to record the call
    def fake_render_countdown_to_disney(matrix, next_trip_time):
        matrix.countdown_rendered = True
    monkeypatch.setattr(disney, "render_countdown_to_disney", fake_render_countdown_to_disney)
    next_trip_time = datetime(2023, 12, 25)
    disney.show_trip_countdown(fake_matrix, next_trip_time)
    assert fake_matrix.countdown_rendered is True


# Test that loop_through_attractions only renders operating attractions.
def test_loop_through_attractions_skips_closed(monkeypatch):
    fake_matrix = FakeMatrix()

    # Create a fake version of render_attraction_info that records the attraction name.
    def fake_render_attraction_info(matrix, attraction_info):
        matrix.rendered_attractions.append(attraction_info['name'])

    monkeypatch.setattr(disney, "render_attraction_info", fake_render_attraction_info)

    # Build a dummy park with one closed and one operating attraction.
    park = {
        "name": "Magic Kingdom",
        "attractions": [
            {"name": "Haunted Mansion", "waitTime": "N/A", "status": "CLOSED"},
            {"name": "Splash Mountain", "waitTime": "20", "status": "OPERATING"}
        ]
    }
    disney.loop_through_attractions(fake_matrix, park)

    # Only the operating attraction should be rendered.
    assert "Splash Mountain" in fake_matrix.rendered_attractions
    assert "Haunted Mansion" not in fake_matrix.rendered_attractions


# Test that show_trip_countdown passes along the correct next_trip_time.
def test_show_trip_countdown_format(monkeypatch):
    fake_matrix = FakeMatrix()
    recorded_time = None

    def fake_render_countdown(matrix, next_trip_time):
        nonlocal recorded_time
        recorded_time = next_trip_time

    monkeypatch.setattr(disney, "render_countdown_to_disney", fake_render_countdown)

    test_date = datetime(2023, 12, 31)
    disney.show_trip_countdown(fake_matrix, test_date)
    assert recorded_time == test_date


# Optionally, test validate_date boundary conditions more thoroughly.
def test_validate_date_leap_year():
    # Test a valid leap year date.
    date_str = "2020-02-29"
    result = disney.validate_date(date_str)
    assert result.year == 2020 and result.month == 2 and result.day == 29


def test_load_config_nonexistent(tmp_path):
    # Test that load_config raises FileNotFoundError when the file doesn't exist.
    non_existent = tmp_path / "nonexistent_config.json"
    with pytest.raises(FileNotFoundError):
        disney.load_config(str(non_existent))


def test_render_logo_with_image(monkeypatch):
    """
    Test the branch in render_logo that loads and displays an image.
    We set use_image_logo to True, force os.path.exists to return True, and
    monkey-patch PIL.Image.open to return a FakeImage instance.
    Then, we verify that FakeMatrix2.SetImage is called with the
    "converted_image" value.
    """
    fake_matrix = FakeMatrix2()
    disney.use_image_logo = True
    # Force os.path.exists to return True regardless of the path
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    # Monkey-patch PIL.Image.open to return a FakeImage instance
    monkeyatch_target = "PIL.Image.open"
    monkeypatch.setattr(monkeyatch_target, lambda path: FakeImage())
    # Override time.sleep to avoid delay (if not already patched by a global fixture)
    monkeypatch.setattr(disney, "time", type("t", (), {"sleep": lambda x: None}))

    disney.render_logo(fake_matrix)

    # Check that SetImage was called and it received "converted_image"
    assert fake_matrix.image_set == "converted_image"


def test_validate_date_error_message():
    """
    Test validate_date to ensure that it raises a ValueError with the expected message.
    """
    with pytest.raises(ValueError) as excinfo:
        disney.validate_date("invalid-date")
    assert "Invalid date format:" in str(excinfo.value)

# Note: Testing main() is more challenging because it runs an infinite loop.
# If needed, you could refactor main() for better testability (e.g., extract functionality into smaller functions)a