import json
import os
import tempfile
from datetime import datetime, date

import pytest

import disney  # Import your main module (disney.py)
import display.animation as disney_animation


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
        self.width, self.height = 64, 32
        self.clear_count = 0
        self.rendered_attractions = []

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
    # Check result is a date-like or datetime object with the expected date
    assert isinstance(result, (datetime, date))
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

def test_render_logo_without_image_plays_castle_fireworks(monkeypatch):
    fake_matrix = FakeMatrix()
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    played = []
    monkeypatch.setattr(disney, "render_castle_fireworks", lambda matrix: played.append(matrix))
    disney.render_logo(fake_matrix)
    assert played == [fake_matrix]

class PixelCanvas:
    def SetPixel(self, x, y, r, g, b):
        pass


FAKE_CANVAS = PixelCanvas()


@pytest.fixture
def screens(monkeypatch):
    """Replace the animation player: draw each screen once and record how it was played."""
    played = []

    def fake_show_screen(matrix, draw, hold_s, transition="wipe"):
        played.append({"hold": hold_s, "transition": transition, "animating": draw(FAKE_CANVAS, 0.0)})

    monkeypatch.setattr(disney, "show_screen", fake_show_screen)
    return played


def test_initialize_park_information_screen(monkeypatch, screens):
    fake_matrix = FakeMatrix()
    drawn_on = []
    monkeypatch.setattr(disney, "render_park_information_screen", lambda canvas, park: drawn_on.append((canvas, park)))
    park = {"name": "Magic Kingdom"}
    disney.initialize_park_information_screen(fake_matrix, park)
    assert drawn_on == [(FAKE_CANVAS, park)]
    landmark, title = screens
    assert landmark == {"hold": disney.LANDMARK_S, "transition": "wipe", "animating": True}
    assert title["hold"] == 8 and title["animating"] is False
    assert title["transition"] in disney.PARK_REVEALS


def test_parks_without_a_landmark_go_straight_to_the_title(monkeypatch, screens):
    monkeypatch.setattr(disney, "render_park_information_screen", lambda canvas, park: None)
    disney.initialize_park_information_screen(FakeMatrix(), {"name": "Cedar Point"})
    assert len(screens) == 1 and screens[0]["hold"] == 8


def test_park_screens_are_revealed_by_both_tink_and_buzz(monkeypatch, screens):
    monkeypatch.setattr(disney, "render_park_information_screen", lambda canvas, park: None)
    for _ in range(60):
        disney.initialize_park_information_screen(FakeMatrix(), {"name": "Magic Kingdom"})
    titles = [s for s in screens if s["hold"] == 8]
    assert {s["transition"] for s in titles} == {"tink", "buzz"}
    assert set(disney.PARK_REVEALS) <= set(disney_animation.TRANSITIONS)

def test_loop_through_attractions(monkeypatch, screens):
    fake_matrix = FakeMatrix()
    drawn = []
    monkeypatch.setattr(disney, "draw_attraction_frame", lambda canvas, ride, t, expected: drawn.append(ride) or True)
    attraction = {"name": "Space Mountain", "waitTime": 30, "status": "OPERATING"}
    park = {"name": "Magic Kingdom", "attractions": [attraction]}
    disney.loop_through_attractions(fake_matrix, park)
    assert drawn == [attraction]
    assert drawn[0] is not attraction, "the updater threads mutate the live dict; animate a snapshot"
    assert screens == [{"hold": 8, "transition": "wipe", "animating": True}]

def test_loop_through_attractions_passes_this_hours_forecast(monkeypatch, screens):
    seen = []
    monkeypatch.setattr(disney, "draw_attraction_frame", lambda canvas, ride, t, expected: seen.append(expected))
    monkeypatch.setattr(disney, "forecast_wait_now", lambda forecast: forecast[0]["waitTime"] if forecast else None)
    park = {"name": "MK", "attractions": [
        {"name": "Space Mountain", "waitTime": 30, "status": "OPERATING", "forecast": [{"time": "x", "waitTime": 40}]},
        {"name": "Haunted Mansion", "waitTime": 10, "status": "OPERATING"},
    ]}
    disney.loop_through_attractions(FakeMatrix(), park)
    assert seen == [40, None]

def test_each_attraction_screen_keeps_its_own_ride(monkeypatch):
    """The next screen's sweep redraws the previous one; it must still show the previous ride."""
    screens = []
    monkeypatch.setattr(disney, "show_screen", lambda matrix, draw, hold_s, transition="wipe": screens.append(draw))
    drawn = []
    monkeypatch.setattr(disney, "draw_attraction_frame", lambda canvas, ride, t, expected: drawn.append(ride["name"]))
    park = {"name": "MK", "attractions": [
        {"name": "Space Mountain", "waitTime": 30, "status": "OPERATING"},
        {"name": "Haunted Mansion", "waitTime": 10, "status": "OPERATING"},
    ]}
    disney.loop_through_attractions(FakeMatrix(), park)
    screens[0]("canvas", 1.0)
    assert drawn == ["Space Mountain"]

def test_show_trip_countdown(monkeypatch, screens):
    fake_matrix = FakeMatrix()
    drawn = []
    monkeypatch.setattr(disney, "render_countdown_to_disney", lambda canvas, when: drawn.append(when))
    next_trip_time = datetime(2023, 12, 25)
    disney.show_trip_countdown(fake_matrix, next_trip_time)
    assert drawn == [next_trip_time]
    assert screens[0]["hold"] == 7


def test_show_trip_countdown_skips_when_no_trip(screens):
    disney.show_trip_countdown(FakeMatrix(), None)
    assert screens == []


# Test that loop_through_attractions only renders operating attractions.
def test_loop_through_attractions_skips_closed(monkeypatch, screens):
    fake_matrix = FakeMatrix()

    def fake_draw(canvas, attraction_info, t, expected):
        fake_matrix.rendered_attractions.append(attraction_info['name'])

    monkeypatch.setattr(disney, "draw_attraction_frame", fake_draw)

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


def test_loop_through_attractions_skips_empty_wait_time(monkeypatch, screens):
    fake_matrix = FakeMatrix()

    def fake_draw(canvas, attraction_info, t, expected):
        fake_matrix.rendered_attractions.append(attraction_info['name'])

    monkeypatch.setattr(disney, "draw_attraction_frame", fake_draw)

    park = {
        "name": "Hollywood Studios",
        "attractions": [
            {"name": "Meet Disney Jr. Stars", "waitTime": "", "status": ""},
            {"name": "Tron", "waitTime": "25", "status": "OPERATING"}
        ]
    }
    disney.loop_through_attractions(fake_matrix, park)

    assert "Tron" in fake_matrix.rendered_attractions
    assert "Meet Disney Jr. Stars" not in fake_matrix.rendered_attractions


def test_park_filter_limits_parks(monkeypatch):
    from api.disney_api import clean_park_name
    all_parks = [
        {"name": "Disney's Animal Kingdom Theme Park", "id": "ak-id"},
        {"name": "Magic Kingdom Park", "id": "mk-id"},
        {"name": "Disney's Hollywood Studios", "id": "hs-id"},
        {"name": "EPCOT", "id": "ep-id"},
    ]
    park_filter = ["Animal Kingdom"]
    filtered = [p for p in all_parks if clean_park_name(p["name"]) in park_filter]
    assert len(filtered) == 1
    assert filtered[0]["id"] == "ak-id"


# Test that show_trip_countdown passes along the correct next_trip_time.
def test_show_trip_countdown_format(monkeypatch, screens):
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