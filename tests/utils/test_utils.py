import sys
from argparse import Namespace
import pytest
from utils.utils import (
    led_matrix_options,
    center_text_position,
    split_string,
    deep_update,
    get_eastern,
    args,
    pretty_print_json,
)
from utils import debug

# -----------------------------------------------------------------------------
# Helper: Dummy RGBMatrixOptions
# -----------------------------------------------------------------------------
class DummyRGBMatrixOptions:
    def __init__(self):
        self.hardware_mapping = None
        self.rows = None
        self.cols = None
        self.chain_length = None
        self.parallel = None
        self.row_address_type = None
        self.multiplexing = None
        self.pwm_bits = None
        self.brightness = None
        self.scan_mode = None
        self.pwm_lsb_nanoseconds = None
        self.led_rgb_sequence = None
        self.drop_privileges = None
        self.pixel_mapper_config = None
        self.pwm_dither_bits = None
        self.limit_refresh_rate_hz = None
        self.show_refresh_rate = None
        self.gpio_slowdown = None
        self.disable_hardware_pulsing = None

# Ensure driver.RGBMatrixOptions is available.
import driver
if not hasattr(driver, "RGBMatrixOptions"):
    driver.RGBMatrixOptions = DummyRGBMatrixOptions

# -----------------------------------------------------------------------------
# Tests for led_matrix_options (arguments handling and exception warnings)
# -----------------------------------------------------------------------------
def test_led_matrix_options_attribute_errors(monkeypatch):
    # Capture warnings
    warnings = []
    monkeypatch.setattr(debug, "warning", lambda msg: warnings.append(msg))

    # Create a Namespace with required arguments but omit certain attributes
    args_obj = Namespace(
        led_gpio_mapping="regular",
        led_rows=32,
        led_cols=32,
        led_chain=1,
        led_parallel=1,
        led_row_addr_type=0,
        led_multiplexing=0,
        led_pwm_bits=11,
        led_brightness=100,
        led_scan_mode=1,
        led_pwm_lsb_nanoseconds=130,
        led_rgb_sequence="RGB",
        drop_privileges=False,
        # Omit: led_pixel_mapper, led_pwm_dither_bits, led_limit_refresh
        led_show_refresh=False,
        led_slowdown_gpio=1,
        led_no_hardware_pulse=True,
    )
    for attr in ["led_pixel_mapper", "led_pwm_dither_bits", "led_limit_refresh"]:
        if hasattr(args_obj, attr):
            delattr(args_obj, attr)

    # Call led_matrix_options (this will trigger exception branches)
    options = led_matrix_options(args_obj)

    # Expect 3 try/except blocks; each should warn twice = 6 warnings.
    assert len(warnings) == 6, f"Expected 6 warnings, got {len(warnings)}: {warnings}"
    generic = "Your compiled RGB Matrix Library is out of date."
    pwm_warning = "The --led-pwm-dither-bits argument will not work until it is updated."
    mapper_warning = "The --led-pixel-mapper argument will not work until it is updated."
    limit_warning = "The --led-limit-refresh argument will not work until it is updated."
    generic_count = sum(1 for msg in warnings if generic in msg)
    assert generic_count == 3, f"Expected generic warning 3 times, got {generic_count}: {warnings}"
    assert mapper_warning in warnings, f"Expected pixel mapper warning not found: {warnings}"
    assert pwm_warning in warnings, f"Expected PWM dither warning not found: {warnings}"
    assert limit_warning in warnings, f"Expected limit refresh warning not found: {warnings}"

def test_led_matrix_options():
    # Test normal parsing of arguments into options.
    args_obj = Namespace(
        led_gpio_mapping="regular",
        led_rows=16,
        led_cols=32,
        led_chain=1,
        led_parallel=1,
        led_row_addr_type=0,
        led_multiplexing=0,
        led_pwm_bits=11,
        led_brightness=100,
        led_scan_mode=1,
        led_pwm_lsb_nanoseconds=130,
        led_rgb_sequence="RGB",
        drop_privileges=False,
        led_pixel_mapper="Rotate:90",
        led_pwm_dither_bits=0,
        led_limit_refresh=0,
        led_show_refresh=True,
        led_slowdown_gpio=1,
        led_no_hardware_pulse=True,
    )
    options = led_matrix_options(args_obj)
    assert options.hardware_mapping == "regular"
    assert options.rows == 16
    assert options.cols == 32
    assert options.chain_length == 1
    assert options.parallel == 1
    assert options.row_address_type == 0
    assert options.multiplexing == 0
    assert options.pwm_bits == 11
    assert options.brightness == 100
    assert options.scan_mode == 1
    assert options.pwm_lsb_nanoseconds == 130
    assert options.led_rgb_sequence == "RGB"
    assert options.drop_privileges is False
    assert options.pixel_mapper_config == "Rotate:90"
    assert options.pwm_dither_bits == 0
    assert options.limit_refresh_rate_hz == 0
    assert options.show_refresh_rate == 1
    assert options.gpio_slowdown == 1
    assert options.disable_hardware_pulsing is True

# -----------------------------------------------------------------------------
# Tests for utility functions
# -----------------------------------------------------------------------------
def test_center_text_position():
    # "abc" length=3, each char width=5 gives total width=15.
    # Center position 50, so expected = abs(50 - (15//2)) = abs(50 - 7) = 43.
    assert center_text_position("abc", 50, 5) == 43

def test_split_string():
    assert split_string("abcdef", 2) == ["ab", "cd", "ef"]

def test_deep_update():
    source = {"a": {"b": 1}}
    overrides = {"a": {"c": 2}, "d": 3}
    result = deep_update(source, overrides)
    assert result == {"a": {"b": 1, "c": 2}, "d": 3}
    assert source is result

def test_get_eastern():
    eastern_time = get_eastern("2024-01-01T12:00:00Z")
    # Check that the result ends with either "AM" or "PM".
    assert eastern_time.endswith("AM") or eastern_time.endswith("PM")

def test_pretty_print_json_exception():
    # Test that pretty_print_json raises a TypeError for non-serializable objects.
    class NotSerializable:
        pass
    with pytest.raises(TypeError):
        pretty_print_json(NotSerializable())

# -----------------------------------------------------------------------------
# Tests for argparse-based args() function
# -----------------------------------------------------------------------------
def test_args_defaults():
    original_argv = sys.argv.copy()
    try:
        sys.argv = ["program"]
        parsed = args()
        assert parsed.led_rows == 32
        assert parsed.led_cols == 32
        assert parsed.led_chain == 1
        assert parsed.led_parallel == 1
        assert parsed.led_pwm_bits == 11
        assert parsed.led_brightness == 100
        assert parsed.led_scan_mode == 1
        assert parsed.led_pwm_lsb_nanoseconds == 130
        assert parsed.led_rgb_sequence == "RGB"
        assert parsed.led_pixel_mapper == ""
        assert parsed.led_row_addr_type == 0
        assert parsed.led_multiplexing == 0
        assert parsed.led_limit_refresh == 0
        assert parsed.led_pwm_dither_bits == 0
        assert parsed.config == "config"
        # Store_true flags default to False.
        assert parsed.led_show_refresh is False
        assert parsed.drop_privileges is False
    finally:
        sys.argv = original_argv

def test_args_custom():
    original_argv = sys.argv.copy()
    try:
        custom = [
            "program",
            "--led-rows", "16",
            "--led-cols", "64",
            "--led-chain", "2",
            "--led-parallel", "3",
            "--led-pwm-bits", "8",
            "--led-brightness", "50",
            "--led-gpio-mapping", "adafruit-hat",
            "--led-scan-mode", "0",
            "--led-pwm-lsb-nanoseconds", "150",
            "--led-show-refresh",
            "--led-slowdown-gpio", "2",
            "--led-no-hardware-pulse", "dummy",
            "--led-rgb-sequence", "BGR",
            "--led-pixel-mapper", "Rotate:180",
            "--led-row-addr-type", "2",
            "--led-multiplexing", "3",
            "--led-limit-refresh", "60",
            "--led-pwm-dither-bits", "2",
            "--config", "custom_config",
            "--emulated",
            "--drop-privileges"
        ]
        sys.argv = custom
        parsed = args()
        assert parsed.led_rows == 16
        assert parsed.led_cols == 64
        assert parsed.led_chain == 2
        assert parsed.led_parallel == 3
        assert parsed.led_pwm_bits == 8
        assert parsed.led_brightness == 50
        assert parsed.led_gpio_mapping == "adafruit-hat"
        assert parsed.led_scan_mode == 0
        assert parsed.led_pwm_lsb_nanoseconds == 150
        assert parsed.led_show_refresh is True
        assert parsed.led_slowdown_gpio == 2
        assert parsed.led_no_hardware_pulse == "dummy"
        assert parsed.led_rgb_sequence == "BGR"
        assert parsed.led_pixel_mapper == "Rotate:180"
        assert parsed.led_row_addr_type == 2
        assert parsed.led_multiplexing == 3
        assert parsed.led_limit_refresh == 60
        assert parsed.led_pwm_dither_bits == 2
        assert parsed.config == "custom_config"
        assert parsed.emulated is True
        assert parsed.drop_privileges is True
    finally:
        sys.argv = original_argv