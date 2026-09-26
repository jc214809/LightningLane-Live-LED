# tests/display/countdown/test_countdown.py
from datetime import date, timedelta

import pytest

import display.countdown.countdown as countdown
from display.countdown.countdown import countdown_message, counted, layout, render_countdown_to_disney
from utils.trips import Trip

TODAY = date(2026, 9, 26)


def day(offset):
    return TODAY + timedelta(days=offset)


def trip_in(days, end=None, name=None):
    return Trip(day(days), day(end) if end is not None else None, name)


class DummyFont:
    def __init__(self, name, baseline, char_width):
        self.name, self.baseline, self.char_width = name, baseline, char_width

    def CharacterWidth(self, code):
        return self.char_width


FONTS = {
    "countdown_number": DummyFont("number", 11, 7),
    "countdown_label": DummyFont("label", 5, 4),
    "countdown_message": DummyFont("message", 7, 5),
}
COLORS = {"gold": "gold", "mickey_mouse_red": "red"}


class FakeCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.px = {}
        self.text = []

    def SetPixel(self, x, y, r, g, b):
        self.px[(x, y)] = (r, g, b)


@pytest.fixture(autouse=True)
def fake_drawing(monkeypatch):
    monkeypatch.setattr(countdown, "loaded_fonts", FONTS)
    monkeypatch.setattr(countdown, "color_dict", COLORS)
    monkeypatch.setattr(countdown, "get_text_width", text_width)

    def draw_text(canvas, font, x, y, color, text, space_px):
        canvas.text.append({"font": font.name, "x": x, "y": y, "color": color, "text": text,
                            "right": x + text_width(font, text, space_px), "top": y - font.baseline})

    monkeypatch.setattr(countdown, "draw_text", draw_text)


def text_width(font, text, space_px):
    return sum(space_px if ch == " " else font.char_width for ch in text)


def render(days, height=32, t=5.0, **trip):
    canvas = FakeCanvas(64, height)
    assert render_countdown_to_disney(canvas, trip_in(days, **trip), t, today=TODAY) is True
    return canvas


# --- what it says ---

@pytest.mark.parametrize("trip, expected", [
    (trip_in(42), ("42", ("DAYS TO", "DISNEY"))),
    (trip_in(2), ("2", ("DAYS TO", "DISNEY"))),
    (trip_in(42, name="Fall Trip"), ("42", ("DAYS TO", "FALL TRIP"))),
    (trip_in(1, name="Fall Trip"), (None, ("DISNEY", "TOMORROW"))),
    (trip_in(0, end=5), (None, ("IT'S", "DISNEY", "DAY!"))),
    (trip_in(-2, end=3), ("DAY 3", ("OF 6",))),
    (trip_in(-5, end=0), ("DAY 6", ("OF 6",))),
    (trip_in(-6, end=-1), (None, ("WELCOME", "HOME!"))),
    (trip_in(-3), (None, ("HAVE A", "MAGICAL", "TRIP!"))),
])
def test_countdown_message(trip, expected):
    assert countdown_message(trip, TODAY) == expected


def test_countdown_message_defaults_to_today():
    assert countdown_message(Trip(date.today()))[1] == ("IT'S", "DISNEY", "DAY!")


def test_day_count_rolls_up_then_holds():
    assert counted("42", 0.0) == "0"
    assert 0 < int(counted("42", countdown.COUNT_UP_S / 3)) < 42
    assert counted("42", countdown.COUNT_UP_S) == "42"
    assert counted("42", 9.0) == "42"
    assert counted("DAY 3", 0.0) == "DAY 3", "only a bare count rolls"


def test_castle_windows_twinkle():
    frames = [render(42, t=t).px for t in (0.0, 0.4, 0.8)]
    windows = [p for p, rgb in frames[0].items() if rgb[0] > 200 and rgb[2] < 120]
    assert windows, "lit windows drawn"
    assert len({tuple(f[p] for p in windows) for f in frames}) > 1, "windows change brightness"


# --- how it's drawn ---

def test_days_left_are_drawn_big_and_gold_over_a_red_label():
    drawn = render(42).text
    assert [(t["font"], t["color"], t["text"]) for t in drawn] == [
        ("number", "gold", "42"), ("label", "red", "DAYS TO"), ("label", "red", "DISNEY"),
    ]
    assert drawn[0]["y"] < drawn[1]["y"] < drawn[2]["y"], "stacked top to bottom"


def test_special_days_draw_a_gold_message_without_a_number():
    drawn = render(1).text
    assert [t["text"] for t in drawn] == ["DISNEY", "TOMORROW"]
    assert {t["color"] for t in drawn} == {"gold"}


def test_message_uses_the_biggest_font_that_fits():
    big, small = FONTS["countdown_message"], FONTS["countdown_label"]
    assert countdown._fitting_font([big, small], ["DISNEY", "TOMORROW"], 40) is big, "8 x 5px = 40"
    assert countdown._fitting_font([big, small], ["DISNEY", "TOMORROW!"], 40) is small
    assert countdown._fitting_font([big, small], ["X" * 20], 40) is small, "last resort"
    assert {t["font"] for t in render(1, height=32).text} == {"message"}


def test_trip_name_replaces_disney_under_the_count():
    assert [t["text"] for t in render(42, name="Fall Trip").text] == ["42", "DAYS TO", "FALL TRIP"]


def test_trip_name_too_long_for_the_board_falls_back_to_disney():
    drawn = render(42, name="Spring Break Extravaganza").text
    assert [t["text"] for t in drawn] == ["42", "DAYS TO", "DISNEY"]


def test_count_is_laid_out_once_for_its_final_value():
    early, late = render(180, t=0.1).text, render(180, t=5.0).text
    assert early[0]["text"] != "180" and late[0]["text"] == "180"
    assert [t["y"] for t in early] == [t["y"] for t in late], "label holds still while the number rolls"


def test_spaces_are_half_a_cell():
    drawn = render(-2, end=3, height=64).text
    number = drawn[0]
    assert number["text"] == "DAY 3"
    assert number["right"] - number["x"] == 4 * 7 + 3, "7px cell, 3px space"


@pytest.mark.parametrize("height", [32, 64])
@pytest.mark.parametrize("trip", [
    dict(days=180), dict(days=42, name="Fall Trip"), dict(days=1), dict(days=0),
    dict(days=-2), dict(days=-2, end=3), dict(days=-6, end=-1),
])
def test_everything_stays_on_the_board_and_off_the_castle(height, trip):
    canvas = render(height=height, **trip)
    (cx, cy), (bx, by, bw, bh) = layout(64, height)
    assert canvas.px, "castle drawn"
    assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    for t in canvas.text:
        assert bx <= t["x"] and t["right"] <= bx + bw, f"{t['text']} fits across"
        assert by <= t["top"] and t["y"] <= by + bh, f"{t['text']} fits down"
    castle_right = max(x for x, _ in canvas.px)
    castle_bottom = max(y for _, y in canvas.px)
    if height >= 64:
        assert castle_bottom < by, "castle above the text"
    else:
        assert castle_right < bx, "castle beside the text"


def test_castle_stays_1x_on_64_row_boards():
    small, big = render(42, 32).px, render(42, 64).px
    width = lambda px: max(x for x, _ in px) - min(x for x, _ in px)
    assert width(small) == width(big)
