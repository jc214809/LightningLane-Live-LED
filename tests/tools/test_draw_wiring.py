import importlib.util
import os
import xml.etree.ElementTree as ET

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("draw_wiring", os.path.join(ROOT, "tools", "draw_wiring.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

# rpi-rgb-led-matrix's lib/hardware-mapping.c, "adafruit-hat": the GPIO behind each Bonnet signal
ADAFRUIT_HAT = {"OE": 4, "CLK": 17, "LAT": 21, "A": 22, "B": 26, "C": 27, "D": 20, "E": 24,
                "R1": 5, "G1": 13, "B1": 6, "R2": 12, "G2": 16, "B2": 23}


@pytest.mark.parametrize("name, zero", tool.FILES.items())
def test_the_committed_diagram_is_what_the_tool_draws(name, zero):
    with open(os.path.join(tool.DOCS, name), encoding="utf-8") as f:
        committed = f.read()
    assert committed == tool.build(zero), f"run python3 tools/draw_wiring.py to redraw {name}"


@pytest.mark.parametrize("zero", [False, True])
def test_the_diagram_is_well_formed_svg(zero):
    root = ET.fromstring(tool.build(zero))
    assert root.tag == "{http://www.w3.org/2000/svg}svg"


def test_the_breakout_row_is_the_bonnets_in_order():
    """As printed on the Bonnet, left to right (Adafruit's product photo)."""
    assert [label for label, _, _ in tool.BREAKOUT] == [
        "SDA", "SCL", "TX", "RX", "4", "17", "18", "27", "22", "23", "24", "25", "MO", "MI", "CLK", "CE0",
        "CE1", "5", "6", "12", "13", "16", "19", "20", "21"]
    assert tool.POWER_PADS == ["5V", "", "GND"]


def test_each_signal_under_a_pad_is_the_one_the_driver_puts_on_that_gpio():
    signals = {signal: gpio for _, gpio, signal in tool.BREAKOUT if signal}
    assert signals == {s: g for s, g in ADAFRUIT_HAT.items() if s != "B"}  # B (GPIO 26) isn't on the row


def test_numbered_pads_are_their_gpio_and_named_ones_the_pis_usual_names():
    for label, gpio, _ in tool.BREAKOUT:
        if label.isdigit():
            assert int(label) == gpio
    named = {label: gpio for label, gpio, _ in tool.BREAKOUT if not label.isdigit()}
    assert named == {"SDA": 2, "SCL": 3, "TX": 14, "RX": 15, "MO": 10, "MI": 9, "CLK": 11, "CE0": 8, "CE1": 7}


def test_the_button_uses_free_pads_scl_25_and_gnd():
    pads = {label: (gpio, signal) for label, gpio, signal in tool.BREAKOUT}
    assert pads["SCL"] == (3, None)  # GPIO 3: the only pin that wakes a shut-down Pi
    assert pads["25"] == (25, None)
    svg = tool.build(False)
    for label in ("SCL = GPIO 3, the switch", "25 = GPIO 25: LED +", "GND, both ground wires"):
        assert label in svg


def test_the_wiring_matches_power_md():
    with open(os.path.join(tool.DOCS, "POWER.md"), encoding="utf-8") as f:
        power = f.read()
    assert "SCL pad  (GPIO 3)" in power and "25 pad   (GPIO 25)" in power and "GND pad" in power
    for label, _, _ in tool.BREAKOUT:
        assert f" {label} " in power or f" {label}\n" in power, label


@pytest.mark.parametrize("zero", [False, True])
def test_the_diagram_shows_the_case_jack_the_jumper_and_what_the_pads_do(zero):
    svg = tool.build(zero)
    assert "case jack (Adafruit 610)" in svg
    assert "big tab with the centre pin" in svg and "sleeve" in svg and "stays empty" in svg
    assert "4–18 jumper" in svg and "needs adafruit-hat-pwm" in svg
    assert "What the pads do" in svg and "shutdown and wake" in svg
