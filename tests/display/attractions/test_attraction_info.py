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

# ---- Animated attraction screen ----

import pytest

import display.attractions.attraction_info as attraction_mod
import display.display as display_mod


class RecordingCanvas:
    def __init__(self, width=64, height=32):
        self.width, self.height = width, height


@pytest.fixture
def frame_recorder(monkeypatch):
    loaded_fonts["ride"] = DummyFont(width=4, height=6)
    loaded_fonts["waittime"] = DummyFont(width=4, height=6)
    record = {"text": [], "lines": []}
    fake = type("G", (), {
        "Color": staticmethod(lambda r, g, b: (r, g, b)),
        "DrawText": staticmethod(lambda c, font, x, y, color, text: record["text"].append((text, color))),
        "DrawLine": staticmethod(lambda c, x0, y0, x1, y1, color: record["lines"].append((x0, y0, x1, y1, color))),
    })
    # Ride text is drawn through display.display.draw_text, so fake graphics in both modules.
    monkeypatch.setattr(attraction_mod, "graphics", fake)
    monkeypatch.setattr(display_mod, "graphics", fake)
    return record


def test_wait_counts_up_from_zero_and_lands_exactly():
    assert attraction_mod.counted_wait(45, 0) == 0
    samples = [attraction_mod.counted_wait(45, t / 30) for t in range(40)]
    assert samples == sorted(samples)
    assert attraction_mod.counted_wait(45, attraction_mod.COUNT_UP_S) == 45
    assert attraction_mod.counted_wait(45, 99) == 45


@pytest.mark.parametrize("wait", ["Down 12:41", "Down", "Groups 40-55", "Group 12+", ""])
def test_non_numeric_waits_are_shown_as_is(wait):
    assert attraction_mod.counted_wait(wait, 0) == wait


def test_pulse_stays_visible():
    levels = [attraction_mod.pulse_level(t / 30) for t in range(200)]
    assert min(levels) >= 0.5 - 1e-9 and max(levels) <= 1.0 + 1e-9


@pytest.mark.parametrize("minutes, band", [(5, 0), (20, 0), (21, 1), (45, 1), (46, 2), (240, 2)])
def test_wait_bar_color_bands(minutes, band):
    assert attraction_mod.wait_bar_color(minutes) == attraction_mod.BAR_BANDS[band][1]


def test_wait_bar_length_tracks_minutes_and_caps_at_full_width(frame_recorder):
    attraction_mod.draw_wait_bar(RecordingCanvas(64, 32), 45)
    (x0, y0, x1, y1, _), = frame_recorder["lines"]
    assert (x0, x1, y0, y1) == (0, 31, 31, 31)
    frame_recorder["lines"].clear()
    attraction_mod.draw_wait_bar(RecordingCanvas(64, 64), 500)
    assert [(l[0], l[2]) for l in frame_recorder["lines"]] == [(0, 63), (0, 63)], "2 rows tall on 64-row boards"
    frame_recorder["lines"].clear()
    attraction_mod.draw_wait_bar(RecordingCanvas(), 0)
    assert frame_recorder["lines"] == []


def test_numeric_ride_counts_up_then_goes_static(frame_recorder):
    ride = {"name": "Space Mountain", "waitTime": 45}
    assert attraction_mod.draw_attraction_frame(RecordingCanvas(), ride, 0.1) is True
    assert attraction_mod.draw_attraction_frame(RecordingCanvas(), ride, 5.0) is False
    assert [text for text, _ in frame_recorder["text"][-2:]] == ["45", "Mins"]
    assert ride["waitTime"] == 45, "the caller's ride dict is not modified"


def test_down_ride_pulses_red_and_keeps_animating(frame_recorder):
    ride = {"name": "Big Thunder", "waitTime": "Down 12:41"}
    colors = []
    for t in (0.0, attraction_mod.PULSE_PERIOD_S / 2):
        frame_recorder["text"].clear()
        assert attraction_mod.draw_attraction_frame(RecordingCanvas(), ride, t) is True
        colors.append(next(c for text, c in frame_recorder["text"] if "Down" in text))
    bright, dim = colors
    assert bright == attraction_mod.DOWN_RGB
    assert dim[0] < bright[0] and dim[1:] == (0, 0)
    assert frame_recorder["lines"] == [], "no wait bar for a DOWN ride"


def test_boarding_group_ride_is_static(frame_recorder):
    ride = {"name": "TRON", "waitTime": "Groups 40-55"}
    assert attraction_mod.draw_attraction_frame(RecordingCanvas(), ride, 0) is False
    assert frame_recorder["lines"] == []


def test_forecast_tick_marks_the_expected_wait_and_stands_taller(frame_recorder):
    attraction_mod.draw_wait_bar(RecordingCanvas(64, 32), 30, expected=45)
    bar, tick = frame_recorder["lines"]
    assert bar[:4] == (0, 31, 20, 31)
    assert tick[:4] == (31, 30, 31, 31), "at 45/90 of the width, 1px taller than the bar"
    assert tick[4] == attraction_mod.FORECAST_TICK_RGB


@pytest.mark.parametrize("expected, x", [(0, 0), (500, 63)])
def test_forecast_tick_stays_on_the_board(frame_recorder, expected, x):
    attraction_mod.draw_wait_bar(RecordingCanvas(64, 64), 30, expected=expected)
    tick = frame_recorder["lines"][-1]
    assert tick[0] == tick[2] == x
    assert (tick[1], tick[3]) == (61, 63)


def test_no_tick_without_a_forecast(frame_recorder):
    attraction_mod.draw_wait_bar(RecordingCanvas(64, 32), 30)
    assert len(frame_recorder["lines"]) == 1


def test_a_name_that_only_just_overflows_keeps_the_bar_by_tightening(frame_recorder):
    # 4 name lines + the wait is 3px over on a 32-row board with normal spacing, but
    # fits once the blank row and the name/wait gap are dropped.
    long_ride = {"name": "Meet Beloved Disney Pals at Mickey and Friends", "waitTime": 35}
    canvas = RecordingCanvas(64, 32)
    reserve, gap = attraction_mod.bar_layout(canvas, long_ride)
    assert reserve == attraction_mod.bar_reserve_rows(32, tight=True)
    assert gap == 0, "the gap above the wait is given up to make room"
    assert attraction_mod.text_fits_above_bar(canvas, long_ride)
    attraction_mod.draw_attraction_frame(canvas, long_ride, 5.0, expected=40)
    assert len(frame_recorder["lines"]) == 2, "bar and tick are drawn"


def test_roomy_names_keep_normal_spacing(frame_recorder):
    canvas = RecordingCanvas(64, 32)
    reserve, gap = attraction_mod.bar_layout(canvas, {"name": "Space Mountain", "waitTime": 35})
    assert reserve == attraction_mod.bar_reserve_rows(32), "no tightening when there's room"
    assert gap == attraction_mod.GAP_BETWEEN_RIDE_AND_WAIT


def test_names_too_long_even_when_tightened_drop_the_bar(frame_recorder):
    # 6 name lines can't fit however the spacing is squeezed; the text wins.
    huge = {"name": " ".join(["Halloween"] * 9), "waitTime": 35}
    canvas = RecordingCanvas(64, 32)
    assert attraction_mod.bar_layout(canvas, huge) == (0, attraction_mod.GAP_BETWEEN_RIDE_AND_WAIT)
    assert not attraction_mod.text_fits_above_bar(canvas, huge)
    attraction_mod.draw_attraction_frame(canvas, huge, 0.1, expected=40)
    assert frame_recorder["lines"] == [], "no bar or tick"


def test_short_names_keep_the_bar_and_move_up_to_clear_it(frame_recorder, monkeypatch):
    ride = {"name": "Space Mountain", "waitTime": 35}
    baselines = {}
    for reserve in (0, attraction_mod.bar_reserve_rows(32)):
        ys = []
        monkeypatch.setattr(attraction_mod.graphics, "DrawText", staticmethod(lambda c, f, x, y, color, text: ys.append(y)))
        attraction_mod.render_attraction_info(RecordingCanvas(64, 32), ride, reserve_bottom=reserve)
        baselines[reserve] = max(ys)
    assert baselines[attraction_mod.bar_reserve_rows(32)] < baselines[0]
    attraction_mod.draw_attraction_frame(RecordingCanvas(64, 32), ride, 5.0, expected=40)
    assert len(frame_recorder["lines"]) == 2, "bar and tick"


def test_ride_names_are_drawn_with_plain_characters(frame_recorder):
    attraction_mod.render_attraction_info(RecordingCanvas(64, 64), {"name": "Star Tours – Buzz Lightyear’s", "waitTime": 5})
    drawn = " ".join(text for text, _ in frame_recorder["text"])
    assert "–" not in drawn and "’" not in drawn
    assert "Lightyear's" in drawn


def test_scroll_pauses_scrolls_to_the_end_and_back():
    over = 16
    travel = over / attraction_mod.SCROLL_PX_PER_S
    p = attraction_mod.SCROLL_PAUSE_S
    assert attraction_mod.scroll_offset(0, over) == 0
    assert attraction_mod.scroll_offset(p - 0.01, over) == 0
    assert attraction_mod.scroll_offset(p + travel / 2, over) == over // 2
    assert attraction_mod.scroll_offset(p + travel + 0.1, over) == over
    assert attraction_mod.scroll_offset(2 * (p + travel) + 0.1, over) == 0, "repeats"
    assert all(0 <= attraction_mod.scroll_offset(t / 30, over) <= over for t in range(300))


def test_names_too_tall_for_the_board_scroll_and_short_ones_do_not(frame_recorder, monkeypatch):
    long_ride = {"name": " ".join(["Halloween Party Parade"] * 6), "waitTime": 20}
    short_ride = {"name": "Space Mountain", "waitTime": 20}
    assert attraction_mod.overflow_rows(RecordingCanvas(64, 32), long_ride) > 0
    assert attraction_mod.overflow_rows(RecordingCanvas(64, 32), short_ride) == 0
    tops = []
    monkeypatch.setattr(attraction_mod.graphics, "DrawText", staticmethod(lambda c, f, x, y, color, text: tops.append(y)))
    p = attraction_mod.SCROLL_PAUSE_S
    for t in (0, p + 1.0):
        tops.clear()
        assert attraction_mod.draw_attraction_frame(RecordingCanvas(64, 32), long_ride, t) is True, "keeps animating"
        first = tops[0]
        if t == 0:
            start = first
    assert first < start, "text has moved up"
    assert attraction_mod.draw_attraction_frame(RecordingCanvas(64, 32), short_ride, 5.0) is False


def test_meet_and_greet_venue_is_dropped_when_the_gap_would_push_it_off_the_board(frame_recorder):
    # 8px lines on a 64-row board: "Meet" + five one-per-line words + "at Venue" is 7 lines,
    # and 7 name lines + the wait + the gap is 66px, so the venue has to go.
    loaded_fonts["ride"] = DummyFont(width=4, height=8)
    loaded_fonts["waittime"] = DummyFont(width=4, height=8)
    words = " ".join(["Abcdefghijklmn"] * 5)
    ride = {"name": f"Meet {words} at Venue", "waitTime": 10}
    lines, name_lines, *_ = attraction_mod._layout(RecordingCanvas(64, 64), ride)
    assert not any("Venue" in line for line in name_lines)
    assert attraction_mod.overflow_rows(RecordingCanvas(64, 64), ride) == 0, "fits without scrolling"


def test_ride_name_is_white_and_wait_is_cyan(frame_recorder, monkeypatch):
    monkeypatch.setitem(attraction_mod.color_dict, "white", "WHITE")
    monkeypatch.setitem(attraction_mod.color_dict, "wait", "CYAN")
    monkeypatch.setitem(attraction_mod.color_dict, "down", "RED")
    attraction_mod.render_attraction_info(RecordingCanvas(64, 32), {"name": "Space Mountain", "waitTime": 45})
    colors = dict(frame_recorder["text"])
    assert colors["Space"] == colors["Mountain"] == "WHITE"
    assert colors["45"] == colors["Mins"] == "CYAN"
    frame_recorder["text"].clear()
    attraction_mod.render_attraction_info(RecordingCanvas(64, 32), {"name": "Big Thunder", "waitTime": "Down 100"})
    colors = dict(frame_recorder["text"])
    assert colors["Big"] == "WHITE" and colors["Down"] == colors["100"] == "RED"
