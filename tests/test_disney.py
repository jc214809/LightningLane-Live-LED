import json
import os
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

import disney  # Import your main module (disney.py)
from utils.trips import Trip
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

# ---- Tests for load_config ----

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
    assert landmark == {"hold": disney.landmark_for("Magic Kingdom").SCREEN_S, "transition": "wipe", "animating": True}
    assert title["hold"] == 8 and title["animating"] is False
    assert title["transition"] in disney.PARK_REVEALS


def test_each_landmark_is_held_for_its_own_screen_length(monkeypatch, screens):
    monkeypatch.setattr(disney, "render_park_information_screen", lambda canvas, park: None)
    disney.initialize_park_information_screen(FakeMatrix(), {"name": "Disney's Hollywood Studios"})
    assert screens[0]["hold"] == 3.5, "the tower needs longer for its tilt, strike and drop"


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
    # Pin the surprise roll: Baymax or Genie fire on a few percent of runs and would
    # otherwise fail this "wipe" assertion now and then.
    monkeypatch.setattr(disney.random, "random", lambda: 1.0)
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
    drawn = []
    monkeypatch.setattr(disney, "render_countdown_to_disney", lambda canvas, trip, t: drawn.append((trip, t)))
    trip = Trip(date(2023, 12, 25))
    disney.show_trip_countdown(FakeMatrix(), trip)
    assert screens[0]["hold"] == 7
    assert drawn == [(trip, 0.0)], "the screen animates, so it passes t through"


def test_show_trip_countdown_skips_when_no_trip(screens):
    disney.show_trip_countdown(FakeMatrix(), None)
    assert screens == []


def _trip_config(enabled=True, *entries):
    return {"trip_countdown": {"enabled": enabled, "trip_dates": list(entries)}}


@pytest.fixture
def infos(monkeypatch):
    logged = []
    monkeypatch.setattr(disney.debug, "info", lambda msg, *a: logged.append(msg))
    return logged


def test_play_trip_countdown_shows_the_next_trip_and_logs_it_once(monkeypatch, infos):
    shown = []
    monkeypatch.setattr(disney, "show_trip_countdown", lambda matrix, trip: shown.append(trip))
    soon, later = date.today() + timedelta(days=5), date.today() + timedelta(days=90)
    config = _trip_config(True, later.isoformat(), {"start": soon.isoformat(), "name": "Fall Trip"})

    first = disney.play_trip_countdown(FakeMatrix(), config)
    again = disney.play_trip_countdown(FakeMatrix(), config, first)

    assert first == again == Trip(soon, None, "Fall Trip")
    assert shown == [first, first]
    assert infos == [f"Trip countdown showing: Fall Trip ({soon.isoformat()})"]


def test_play_trip_countdown_skipped_when_disabled_or_no_trip(monkeypatch):
    monkeypatch.setattr(disney, "show_trip_countdown", lambda matrix, trip: pytest.fail("nothing to show"))
    previous = Trip(date(2020, 1, 1))
    future = (date.today() + timedelta(days=5)).isoformat()
    assert disney.play_trip_countdown(FakeMatrix(), _trip_config(False, future), previous) is previous
    assert disney.play_trip_countdown(FakeMatrix(), _trip_config(True, "2020-01-01"), previous) is previous
    assert disney.play_trip_countdown(FakeMatrix(), {}) is None


def test_log_configured_trips(infos):
    disney.log_configured_trips(_trip_config(True, "2026-11-10", {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring"}))
    disney.log_configured_trips({})
    assert infos == [
        "Configured trips: ['2026-11-10', 'Spring (2027-03-14 to 2027-03-19)']",
        "No trip dates configured.",
    ]


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


# Note: Testing main() is more challenging because it runs an infinite loop.
# If needed, you could refactor main() for better testability (e.g., extract functionality into smaller functions)a

def _roll_for(name):
    """A roll in the middle of `name`'s slice of SURPRISES, whatever order they're in."""
    start = 0.0
    for visitor, chance in disney.SURPRISES.items():
        if visitor == name:
            return start + chance / 2
        start += chance
    raise KeyError(name)


@pytest.mark.parametrize("visitor", list(disney.SURPRISES))
def test_each_surprise_visitor_turns_up_on_their_own_roll(monkeypatch, screens, visitor):
    monkeypatch.setattr(disney, "draw_attraction_frame", lambda canvas, ride, t, expected: False)
    park = {"name": "MK", "attractions": [{"name": "Space Mountain", "waitTime": 30, "status": "OPERATING"}]}
    monkeypatch.setattr(disney.random, "random", lambda: _roll_for(visitor))
    disney.loop_through_attractions(FakeMatrix(), park)
    assert screens[-1]["transition"] == visitor
    assert visitor in disney_animation.TRANSITIONS


def test_surprise_slices_match_their_chances_and_stay_rare():
    chances = disney.SURPRISES
    assert all(0 < c < 0.05 for c in chances.values()), "each kept rare on purpose"
    assert sum(chances.values()) < 0.1, "so the plain wipe is still the norm"
    samples = [i / 100000 for i in range(100000)]
    seen = [disney._surprise(r) for r in samples]
    for name, chance in chances.items():
        assert seen.count(name) / len(samples) == pytest.approx(chance, abs=1e-4), \
            "a visitor's odds are its own chance, not shifted by where it sits in the map"
    assert disney._surprise(sum(chances.values())) == "wipe"
    assert disney._surprise(0.999) == "wipe"


# ---- Happily Ever After fireworks ----

HEA_START = datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc)
HEA_PARKS = [{"name": "Magic Kingdom", "attractions": [
    {"name": "Happily Ever After", "status": "OPERATING", "waitTime": None, "showtimes": [HEA_START]}]}]


@pytest.fixture
def fireworks_played(monkeypatch):
    played = []
    monkeypatch.setattr(disney, "render_castle_fireworks",
                        lambda matrix, duration, title=True: played.append((duration, title)))
    monkeypatch.setattr(disney, "_shows_played", set())
    return played


def test_fireworks_play_without_the_title_once_per_performance(fireworks_played):
    now = HEA_START + timedelta(seconds=8)
    assert disney.play_fireworks_show_if_due(FakeMatrix(), HEA_PARKS, now=now) is True
    assert fireworks_played == [(disney.FIREWORKS_SHOW_S - 8, False)], "until the window ends, no title"
    assert disney.play_fireworks_show_if_due(FakeMatrix(), HEA_PARKS, now=now + timedelta(seconds=40)) is False
    assert len(fireworks_played) == 1, "the same performance never plays twice"


def test_no_fireworks_outside_the_show_or_without_magic_kingdom(fireworks_played):
    assert not disney.play_fireworks_show_if_due(FakeMatrix(), HEA_PARKS, now=HEA_START - timedelta(minutes=1))
    assert not disney.play_fireworks_show_if_due(
        FakeMatrix(), HEA_PARKS, now=HEA_START + timedelta(seconds=disney.FIREWORKS_SHOW_S))
    epcot = [{"name": "EPCOT", "attractions": [{"name": "Spaceship Earth", "status": "OPERATING", "waitTime": 15}]}]
    assert not disney.play_fireworks_show_if_due(FakeMatrix(), epcot, now=HEA_START + timedelta(seconds=5))
    assert fireworks_played == []


def test_ride_loop_checks_for_the_show_before_each_screen(monkeypatch, screens):
    order = []
    monkeypatch.setattr(disney, "play_fireworks_show_if_due", lambda matrix, parks: order.append("check"))
    monkeypatch.setattr(disney, "draw_attraction_frame", lambda canvas, ride, t, expected: order.append("ride"))
    monkeypatch.setattr(disney.random, "random", lambda: 1.0)
    park = {"name": "MK", "attractions": [
        {"name": "Space Mountain", "waitTime": 30, "status": "OPERATING"},
        {"name": "Haunted Mansion", "waitTime": 10, "status": "OPERATING"},
    ]}
    disney.loop_through_attractions(FakeMatrix(), park, HEA_PARKS)
    assert order == ["check", "ride", "check", "ride"]


# ---- force_surprise ----

def test_force_surprise_plays_that_visitor_on_every_ride_screen(monkeypatch, screens):
    monkeypatch.setattr(disney, "draw_attraction_frame", lambda canvas, ride, t, expected: False)
    monkeypatch.setattr(disney.random, "random", lambda: 0.99)
    park = {"name": "MK", "attractions": [{"name": n, "waitTime": 30, "status": "OPERATING"} for n in ("A", "B", "C")]}
    disney.set_forced_surprise("genie")
    try:
        disney.loop_through_attractions(FakeMatrix(), park)
    finally:
        disney.set_forced_surprise(None)
    assert [s["transition"] for s in screens] == ["genie"] * 3


def test_force_surprise_ignores_names_that_are_not_characters(monkeypatch):
    warnings = []
    monkeypatch.setattr(disney.debug, "warning", warnings.append)
    for bad in ("gennie", "wipe"):
        disney.set_forced_surprise(bad)
        assert disney.forced_surprise is None
    assert len(warnings) == 2 and "slinky_wrap" in warnings[0], "the warning lists the valid choices"
    disney.set_forced_surprise("")
    assert disney.forced_surprise is None and len(warnings) == 2, "unset is silent"
