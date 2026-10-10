"""
The command line: the rgbmatrix library's --led-* flags plus our own (--emulated). Laid out as
mlb-led-scoreboard's cli.py: disney.py parses it once, then switches the driver to the emulator
if asked, so importing the driver never reads sys.argv. As upstream, config.json's "matrix"
section can hold the same settings ({"led_rows": 64, ...}), and boards.json holds each board's,
keyed by hostname. Precedence: command line, config.json's matrix, the board's preset, defaults.
"""
import argparse
import json
import os
import socket
import sys

import driver
from utils import debug

# Fonts and layouts exist for these board heights only (display/display.py's initialize_fonts).
SUPPORTED_ROWS = (32, 64)
# Every board's settings, keyed by hostname; next to this file, so it's found from any cwd.
BOARDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boards.json")


def board_preset(hostname=None, path=BOARDS_FILE):
    """(name, settings) for this machine from boards.json, matched on the hostname ignoring
    case, or (None, None) when it has no entry or there's no file. Exits on a broken file."""
    hostname = (hostname or socket.gethostname()).split(".")[0].lower()
    try:
        with open(path) as f:
            boards = json.load(f)
    except FileNotFoundError:
        return None, None
    except ValueError as e:
        sys.exit(f"{os.path.basename(path)} isn't valid JSON: {e}")
    if not isinstance(boards, dict):
        sys.exit(f'{os.path.basename(path)} should map hostnames to settings, like {{"Disneypi": {{"led_rows": 64}}}}')
    for name, settings in boards.items():
        if name.lower() == hostname:
            return name, settings
    return None, None


def arguments(argv=None, matrix=None, board=None, board_name=None):
    """Parsed flags: the board's preset from boards.json (`board`), then config.json's "matrix"
    section (`matrix`), then the command line (argv, default sys.argv[1:]); each overrides the one
    before. Exits with a usage message on an unknown flag or setting, or a value the boards can't
    use; under unittest, test runners' own flags on sys.argv are ignored instead."""
    parser = _make_parser()
    preset = _matrix_tokens(parser, board, f'boards.json "{board_name}"')
    from_config = _matrix_tokens(parser, matrix, 'config.json "matrix"')
    if argv is None and "unittest" in sys.modules:
        parsed, _ = parser.parse_known_args(preset + from_config + sys.argv[1:])
    else:
        parsed = parser.parse_args(preset + from_config + list(sys.argv[1:] if argv is None else argv))
    if parsed.led_rows not in SUPPORTED_ROWS:
        parser.error(f"--led-rows must be one of {SUPPORTED_ROWS}, not {parsed.led_rows}")
    if min(parsed.led_cols, parsed.led_chain, parsed.led_parallel) <= 0:
        parser.error("--led-cols, --led-chain and --led-parallel must be positive")
    return parsed


def describe(parsed, argv=None, matrix=None, board=None, board_name=None):
    """One line for the startup log: which preset applies, then each setting that isn't at its
    default and what set it (command line, config, or the board's preset), by the same
    precedence as arguments()."""
    parser = _make_parser()
    by_flag = parser._option_string_actions
    from_command_line = {by_flag[token.split("=", 1)[0]].dest
                         for token in (sys.argv[1:] if argv is None else argv) if token.split("=", 1)[0] in by_flag}

    def source(dest):
        if dest in from_command_line:
            return "command line"
        if (matrix or {}).get(dest) is not None:
            return "config"
        return f"board {board_name}" if (board or {}).get(dest) is not None else "default"

    changed = [f"{action.dest}={getattr(parsed, action.dest)} ({source(action.dest)})"
               for action in parser._actions
               if action.option_strings and action.dest != "help"
               and getattr(parsed, action.dest, action.default) != action.default]
    preset = f"boards.json preset {board_name}" if board_name else "no boards.json preset for this hostname"
    return f"Board settings ({preset}): " + (", ".join(changed) + "; the rest default" if changed else "all default")


def _matrix_tokens(parser, matrix, where):
    """A settings object (config.json's "matrix", a boards.json preset; `where` names it in
    errors) as flags, checked by the same parser as the command line (types, choices) and put
    before it, so later ones override it. Keys are the flags' names with underscores, as in
    mlb-led-scoreboard: "led_gpio_mapping" for --led-gpio-mapping."""
    if not matrix:
        return []
    if not isinstance(matrix, dict):
        parser.error(f'{where} should be an object, like {{"led_rows": 64}}')
    flags = {action.dest: action for action in parser._actions if action.option_strings and action.dest != "help"}
    tokens = []
    for key, value in matrix.items():
        action = flags.get(key)
        if action is None:
            parser.error(f'{where} has no setting "{key}" '
                         '(use a flag\'s name with underscores, like "led_rows")')
        if value is None:  # null: not set, as if the flag weren't given
            continue
        if action.nargs == 0:  # a switch like --led-show-refresh: present or not
            if not isinstance(value, bool):
                parser.error(f'{where}: "{key}" should be true or false, not {value!r}')
            if value:
                tokens.append(action.option_strings[0])
        else:
            tokens += [action.option_strings[0], str(value)]
    return tokens


def _make_parser():
    parser = argparse.ArgumentParser()

    # Options for the rpi-rgb-led-matrix library
    parser.add_argument(
        "--led-rows",
        action="store",
        help="Display rows: 32 or 64. (Default: 32)",
        default=32,
        type=int,
    )
    parser.add_argument(
        "--led-cols", action="store", help="Panel columns. Typically 32 or 64. (Default: 32)", default=32, type=int
    )
    parser.add_argument("--led-chain", action="store", help="Daisy-chained boards. (Default: 1)", default=1, type=int)
    parser.add_argument(
        "--led-parallel",
        action="store",
        help="For Plus-models or RPi2: parallel chains. 1..3. (Default: 1)",
        default=1,
        type=int,
    )
    parser.add_argument(
        "--led-pwm-bits", action="store", help="Bits used for PWM. Range 1..11. (Default: 11)", default=11, type=int
    )
    parser.add_argument(
        "--led-brightness",
        action="store",
        help="Sets brightness level. Range: 1..100. (Default: 100)",
        default=100,
        type=int,
    )
    parser.add_argument(
        "--led-gpio-mapping",
        help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm",
        choices=["regular", "adafruit-hat", "adafruit-hat-pwm"],
        type=str,
    )
    parser.add_argument(
        "--led-scan-mode",
        action="store",
        help="Progressive or interlaced scan. 0 = Progressive, 1 = Interlaced. (Default: 1)",
        default=1,
        choices=range(2),
        type=int,
    )
    parser.add_argument(
        "--led-pwm-lsb-nanoseconds",
        action="store",
        help="Base time-unit for the on-time in the lowest significant bit in nanoseconds. (Default: 130)",
        default=130,
        type=int,
    )
    parser.add_argument(
        "--led-show-refresh", action="store_true", help="Shows the current refresh rate of the LED panel."
    )
    parser.add_argument(
        "--led-slowdown-gpio",
        action="store",
        help="Slow down writing to GPIO. Range: 0..4. (Default: 1)",
        choices=range(5),
        type=int,
    )
    parser.add_argument("--led-no-hardware-pulse", action="store", help="Don't use hardware pin-pulse generation.")
    parser.add_argument(
        "--led-rgb-sequence",
        action="store",
        help="Switch if your matrix has led colors swapped. (Default: RGB)",
        default="RGB",
        type=str,
    )
    parser.add_argument(
        "--led-panel-type",
        action="store",
        help="Chipset initialization for panels that need it. (Default: none)",
        default="",
        choices=["", "FM6126A", "FM6127"],
        type=str,
    )
    parser.add_argument(
        "--led-pixel-mapper", action="store", help='Apply pixel mappers. e.g "Rotate:90"', default="", type=str
    )
    parser.add_argument(
        "--led-row-addr-type",
        action="store",
        help="0 = default; 1 = AB-addressed panels; 2 = direct row select; 3 = ABC-addressed panels. (Default: 0)",
        default=0,
        type=int,
        choices=[0, 1, 2, 3],
    )
    parser.add_argument(
        "--led-multiplexing",
        action="store",
        help="Multiplexing type: 0 = direct; 1 = strip; 2 = checker; 3 = spiral; 4 = Z-strip; 5 = ZnMirrorZStripe;"
        "6 = coreman; 7 = Kaler2Scan; 8 = ZStripeUneven. (Default: 0)",
        default=0,
        type=int,
    )
    parser.add_argument(
        "--led-limit-refresh",
        action="store",
        help="Limit refresh rate to this frequency in Hz. Useful to keep a constant refresh rate on loaded system. "
        "0=no limit. Default: 0",
        default=0,
        type=int,
    )
    parser.add_argument(
        "--led-pwm-dither-bits", action="store", help="Time dithering of lower bits (Default: 0)", default=0, type=int,
    )
    parser.add_argument(
        "--emulated",
        action="store_const",
        help="Force using emulator mode over default matrix display.",
        const=True
    )
    parser.add_argument(
        "--drop-privileges", action="store_true", help="Force the matrix driver to drop root privileges after setup."
    )
    return parser


def led_matrix_options(args):
    """The driver's RGBMatrixOptions from parsed flags. Call after any driver.set_mode, so the
    options are the class of the driver in use."""
    options = driver.RGBMatrixOptions()

    if args.led_gpio_mapping is not None:
        options.hardware_mapping = args.led_gpio_mapping

    options.rows = args.led_rows
    options.cols = args.led_cols
    options.chain_length = args.led_chain
    options.parallel = args.led_parallel
    options.row_address_type = args.led_row_addr_type
    options.multiplexing = args.led_multiplexing
    options.pwm_bits = args.led_pwm_bits
    options.brightness = args.led_brightness
    options.scan_mode = args.led_scan_mode
    options.pwm_lsb_nanoseconds = args.led_pwm_lsb_nanoseconds
    options.led_rgb_sequence = args.led_rgb_sequence
    options.drop_privileges = args.drop_privileges

    try:
        options.pixel_mapper_config = args.led_pixel_mapper
    except AttributeError:
        debug.warning("Your compiled RGB Matrix Library is out of date.")
        debug.warning("The --led-pixel-mapper argument will not work until it is updated.")

    # Unset leaves the library's default (no chipset init); getattr keeps callers
    # that build their own Namespace without the flag working.
    panel_type = getattr(args, "led_panel_type", "")
    if panel_type:
        try:
            options.panel_type = panel_type
        except AttributeError:
            debug.warning("Your compiled RGB Matrix Library is out of date.")
            debug.warning("The --led-panel-type argument will not work until it is updated.")

    try:
        options.pwm_dither_bits = args.led_pwm_dither_bits
    except AttributeError:
        debug.warning("Your compiled RGB Matrix Library is out of date.")
        debug.warning("The --led-pwm-dither-bits argument will not work until it is updated.")

    try:
        options.limit_refresh_rate_hz = args.led_limit_refresh
    except AttributeError:
        debug.warning("Your compiled RGB Matrix Library is out of date.")
        debug.warning("The --led-limit-refresh argument will not work until it is updated.")

    if args.led_show_refresh:
        options.show_refresh_rate = 1

    if args.led_slowdown_gpio is not None:
        options.gpio_slowdown = args.led_slowdown_gpio

    if args.led_no_hardware_pulse:
        options.disable_hardware_pulsing = True

    return options

