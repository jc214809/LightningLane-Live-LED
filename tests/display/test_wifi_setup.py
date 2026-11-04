import pytest

import display.countdown.countdown as countdown
import display.wifi_setup as wifi_setup
from display.wifi_setup import render_wifi_setup


class Font:
    """A fixed-width board font: cell width and baseline as in its BDF."""
    def __init__(self, name, width, baseline):
        self.name, self.width, self.baseline = name, width, baseline

    def CharacterWidth(self, code):
        return self.width


F4x6, F5x8, F6x13 = Font("4x6", 4, 5), Font("5x8", 5, 7), Font("6x13", 6, 11)
# display.display.fonts(), per board height
FONTS = {
    32: {"countdown_message": F5x8, "countdown_label": F4x6, "info": F4x6, "ride": F4x6},
    64: {"countdown_message": F6x13, "countdown_label": F5x8, "info": F4x6, "ride": F5x8},
}


class FakeCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.text = []


def render(name, height):
    canvas = FakeCanvas(64, height)
    wifi_setup.loaded_fonts.clear()
    wifi_setup.loaded_fonts.update(FONTS[height])
    render_wifi_setup(canvas, name)
    return canvas.text


@pytest.fixture(autouse=True)
def fake_drawing(monkeypatch):
    monkeypatch.setattr(wifi_setup, "loaded_fonts", {})
    monkeypatch.setattr(wifi_setup, "color_dict", {"gold": "gold", "white": "white", "wait": "blue"})

    def draw_text(canvas, font, x, y, color, text, space_px):
        canvas.text.append({"font": font.name, "x": x, "y": y, "color": color, "text": text,
                            "right": x + len(text) * font.width, "top": y - font.baseline})

    monkeypatch.setattr(countdown, "draw_text", draw_text)


@pytest.mark.parametrize("height", [32, 64])
def test_it_says_wifi_setup_and_the_hotspot_to_join_all_on_the_board(height):
    rows = render("Disneypi-setup", height)
    assert [(r["text"], r["color"]) for r in rows] == [
        ("Wi-Fi setup", "gold"), ("Join", "white"), ("Disneypi-setup", "blue")]
    for row in rows:
        assert 0 <= row["x"] and row["right"] <= 64 and 0 <= row["top"] and row["y"] < height, row
    tops = [r["top"] for r in rows]
    assert tops == sorted(tops) and len(set(tops)) == 3, "stacked, not overlapping"


def test_the_biggest_font_that_fits_is_used():
    assert [r["font"] for r in render("Disneypi-setup", 32)] == ["5x8", "4x6", "4x6"]
    # 6x13 makes "Wi-Fi setup" 66 pixels wide; 5x8 "Disneypi-setup" 70
    assert [r["font"] for r in render("Disneypi-setup", 64)] == ["5x8", "4x6", "4x6"]
    assert [r["font"] for r in render("ZeroPi-setup", 64)][-1] == "5x8"


def test_a_name_too_long_for_one_line_breaks_after_its_hyphen():
    rows = render("MagicKingdom-setup", 32)
    assert [r["text"] for r in rows][2:] == ["MagicKingdom-", "setup"]


def test_the_longest_hotspot_name_still_fits_on_a_64x32_board():
    name = "LightningLaneLiveLEDBoard1-setup"  # 32 letters: Wi-Fi's limit
    rows = render(name, 32)
    assert "".join(r["text"] for r in rows[2:]) == name
    for row in rows:
        assert row["right"] <= 64 and row["top"] >= 0 and row["y"] < 32, row


@pytest.mark.parametrize("height", [32, 64])
def test_the_second_page_gives_the_settings_pages_address_all_on_the_board(height):
    canvas = FakeCanvas(64, height)
    wifi_setup.loaded_fonts.update(FONTS[height])
    wifi_setup.render_settings_address(canvas)
    rows = canvas.text
    assert [(r["text"], r["color"]) for r in rows] == [
        ("Settings", "gold"), ("Browse to", "white"), ("10.41.0.1:8080", "blue")]
    for row in rows:
        assert 0 <= row["x"] and row["right"] <= 64 and 0 <= row["top"] and row["y"] < height, row


def test_the_address_is_the_hotspots_and_the_servers_port():
    from settings_page.server import HOTSPOT_NETWORK, PORT
    from ipaddress import ip_address
    host, port = wifi_setup.SETTINGS_ADDRESS.split(":")
    assert ip_address(host) in HOTSPOT_NETWORK and int(port) == PORT
