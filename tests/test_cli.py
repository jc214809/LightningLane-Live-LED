import sys
from argparse import Namespace
import pytest
from cli import arguments, led_matrix_options
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
        led_panel_type="FM6127",
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
    assert options.panel_type == "FM6127"
    assert options.pwm_dither_bits == 0
    assert options.limit_refresh_rate_hz == 0
    assert options.show_refresh_rate == 1
    assert options.gpio_slowdown == 1
    assert options.disable_hardware_pulsing is True

def test_unset_panel_type_leaves_the_library_default():
    base = dict(
        led_gpio_mapping="regular", led_rows=32, led_cols=64, led_chain=1, led_parallel=1,
        led_row_addr_type=0, led_multiplexing=0, led_pwm_bits=11, led_brightness=100,
        led_scan_mode=1, led_pwm_lsb_nanoseconds=130, led_rgb_sequence="RGB",
        drop_privileges=False, led_pixel_mapper="", led_pwm_dither_bits=0,
        led_limit_refresh=0, led_show_refresh=False, led_slowdown_gpio=1,
        led_no_hardware_pulse=False,
    )
    for extra in ({}, {"led_panel_type": ""}):
        options = led_matrix_options(Namespace(**base, **extra))
        assert not hasattr(options, "panel_type"), "never set, so the binding's default stands"


def test_panel_type_on_an_old_library_warns_instead_of_crashing(monkeypatch):
    warnings = []
    monkeypatch.setattr(debug, "warning", lambda msg: warnings.append(msg))

    class OldOptions(DummyRGBMatrixOptions):
        __slots__ = ()

        def __setattr__(self, name, value):
            if name == "panel_type":
                raise AttributeError(name)
            super().__setattr__(name, value)

    monkeypatch.setattr(driver, "RGBMatrixOptions", OldOptions)
    args_obj = Namespace(
        led_gpio_mapping="regular", led_rows=32, led_cols=64, led_chain=1, led_parallel=1,
        led_row_addr_type=0, led_multiplexing=0, led_pwm_bits=11, led_brightness=100,
        led_scan_mode=1, led_pwm_lsb_nanoseconds=130, led_rgb_sequence="RGB",
        drop_privileges=False, led_pixel_mapper="", led_panel_type="FM6126A",
        led_pwm_dither_bits=0, led_limit_refresh=0, led_show_refresh=False,
        led_slowdown_gpio=1, led_no_hardware_pulse=False,
    )
    led_matrix_options(args_obj)
    assert "The --led-panel-type argument will not work until it is updated." in warnings


def test_panel_type_rejects_unknown_chipsets():
    with pytest.raises(SystemExit):
        arguments(["--led-panel-type", "FM9999"])

# -----------------------------------------------------------------------------
# Tests for arguments()
# -----------------------------------------------------------------------------
def test_args_defaults():
    original_argv = sys.argv.copy()
    try:
        sys.argv = ["program"]
        parsed = arguments()
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
        assert parsed.led_panel_type == ""
        assert parsed.led_row_addr_type == 0
        assert parsed.led_multiplexing == 0
        assert parsed.led_limit_refresh == 0
        assert parsed.led_pwm_dither_bits == 0
        # Store_true flags default to False.
        assert parsed.led_show_refresh is False
        assert parsed.drop_privileges is False
    finally:
        sys.argv = original_argv

def test_args_custom():
    parsed = arguments([
        "--led-rows", "64", "--led-cols", "64", "--led-chain", "2", "--led-parallel", "3",
        "--led-pwm-bits", "8", "--led-brightness", "50", "--led-gpio-mapping", "adafruit-hat",
        "--led-scan-mode", "0", "--led-pwm-lsb-nanoseconds", "150", "--led-show-refresh",
        "--led-slowdown-gpio", "2", "--led-no-hardware-pulse", "dummy", "--led-rgb-sequence", "BGR",
        "--led-pixel-mapper", "Rotate:180", "--led-panel-type", "FM6126A", "--led-row-addr-type", "2",
        "--led-multiplexing", "3", "--led-limit-refresh", "60", "--led-pwm-dither-bits", "2",
        "--emulated", "--drop-privileges",
    ])
    assert parsed.led_rows == 64
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
    assert parsed.led_panel_type == "FM6126A"
    assert parsed.led_row_addr_type == 2
    assert parsed.led_multiplexing == 3
    assert parsed.led_limit_refresh == 60
    assert parsed.led_pwm_dither_bits == 2
    assert parsed.emulated is True
    assert parsed.drop_privileges is True


@pytest.mark.parametrize("argv", [
    ["--led-rows", "16"],   # no fonts or layouts for it
    ["--led-rows", "128"],
    ["--led-cols", "0"],
    ["--led-chain", "0"],
    ["--led-parallel", "-1"],
    ["--led-row", "64"],    # a typo'd flag
    ["--config", "x"],      # removed: config.json is always read
])
def test_bad_flags_exit_with_a_usage_message(argv):
    with pytest.raises(SystemExit):
        arguments(argv)


@pytest.mark.parametrize("rows", ["32", "64"])
def test_both_board_heights_are_accepted(rows):
    assert arguments(["--led-rows", rows]).led_rows == int(rows)


def test_test_runner_flags_on_the_command_line_are_ignored_under_unittest(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pytest", "-q", "--led-rows", "64", "-k", "something"])
    assert arguments().led_rows == 64
