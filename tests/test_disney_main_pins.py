"""
Pins for disney.main, call by call: the start-up sequence (settings, driver, matrix, fonts, Wi-Fi setup,
parks, the updater threads, trips) and the display loop's calls, in order, with everything heavy
replaced by a recorder. They exist so main can be split into named steps with no change in behaviour;
each case here passed on the code before the split.
"""
from datetime import time as clock_time
from types import SimpleNamespace

import pytest

import disney


class _Stop(Exception):
    pass


class _Matrix:
    height = 32
    width = 64

    def __init__(self, log):
        self.log = log

    def Clear(self):
        self.log.append("clear")


class _DebugRecorder:
    def __init__(self, log):
        self._log = log

    def info(self, msg, *args):
        self._log.append(("info", msg))

    def error(self, msg, *args):
        self._log.append(("error", msg))

    def log(self, msg, *args):
        self._log.append(("log", msg % args if args else msg))


PARKS = [{"name": "Magic Kingdom", "operating": True}, {"name": "EPCOT", "operating": False},
         {"name": "Hollywood Studios", "operating": True}]
SCHEDULE = SimpleNamespace(day="day", night="night", day_start=clock_time(7, 0), night_start=clock_time(19, 0))


class _Boot:
    """Stands in for everything main() calls. Each method below is installed over the disney function of
    the same name and records what it was given into self.log. opts: config, emulated, hardware_failed,
    surprises, schedule, parks (what resolve returns), parks_data (what start_live_updaters fills in),
    stop_at (the render_logo call that raises _Stop), version_info, stop_in (the name of a call that raises
    _Stop after recording itself)."""

    FAKES = ("load_config", "model_defaults", "arguments", "describe", "set_forced_surprise", "load_surprises",
             "surprise_settings", "brightness_schedule", "forced_show_name", "set_forced_show", "sound_settings",
             "watch_sound", "led_matrix_options", "initialize_fonts", "show_wifi_setup_while_needed",
             "resolve_parks_from_config", "start_live_updaters", "log_configured_trips", "play_forced_show",
             "play_fireworks_show_if_due", "play_trip_countdown", "initialize_park_information_screen",
             "loop_through_attractions", "render_logo")

    def __init__(self, opts):
        self.opts, self.log = opts, []
        self.matrix = _Matrix(self.log)
        self.args = SimpleNamespace(emulated=opts.get("emulated", True))
        self.config = opts.get("config", {})
        self.logos, self.trips = 0, ["trip-a", "trip-b", "trip-c"]

    def load_config(self):
        self.log.append("load_config")
        return self.config

    def model_defaults(self, choice):
        self.log.append(("model_defaults", choice))
        return "pi4", {"d": 1}, "why"

    def arguments(self, **kwargs):
        self.log.append(("arguments", kwargs))
        return self.args

    def describe(self, args, **kwargs):
        self.log.append(("describe", args is self.args, kwargs))
        return "described"

    def set_forced_surprise(self, value):
        self.log.append(("set_forced_surprise", value))

    def load_surprises(self):
        self.log.append("load_surprises")
        return "raw-surprises"

    def surprise_settings(self, raw):
        return self.opts.get("surprises", disney.SurpriseSettings())

    def brightness_schedule(self, config):
        self.log.append("brightness_schedule")
        return self.opts.get("schedule")

    def forced_show_name(self, config):
        self.log.append("forced_show_name")
        return "forced"

    def set_forced_show(self, value):
        self.log.append(("set_forced_show", value))

    def sound_settings(self, config):
        self.log.append("sound_settings")
        return disney.SoundSettings()

    def watch_sound(self, settings, clips):
        self.log.append(("watch_sound", settings, clips))

    def led_matrix_options(self, args):
        self.log.append(("led_matrix_options", args is self.args))
        return "options"

    def initialize_fonts(self, height):
        self.log.append(("initialize_fonts", height))

    def show_wifi_setup_while_needed(self, matrix):
        self.log.append(("wifi_setup", matrix is self.matrix))

    def resolve_parks_from_config(self, names):
        self.log.append(("resolve_parks", names))
        return self.opts.get("parks", PARKS)

    def start_live_updaters(self, config, parks, interval, parks_data):
        self.log.append(("start_live_updaters", config is self.config, parks, interval))
        parks_data.extend(self.opts.get("parks_data", []))

    def log_configured_trips(self, config):
        self.log.append(("log_configured_trips", config is self.config))

    def play_forced_show(self, matrix):
        self.log.append(("play_forced_show", matrix is self.matrix))

    def play_fireworks_show_if_due(self, matrix, parks):
        self.log.append(("fireworks_if_due", len(parks)))

    def play_trip_countdown(self, matrix, config, last):
        self.log.append(("play_trip_countdown", config is self.config, last))
        return self.trips.pop(0)

    def initialize_park_information_screen(self, matrix, park):
        self.log.append(("park_screen", park["name"]))

    def loop_through_attractions(self, matrix, park, parks):
        self.log.append(("attractions", park["name"]))

    def render_logo(self, matrix):
        self.logos += 1
        self.log.append(("render_logo", matrix is self.matrix))
        if self.logos >= self.opts.get("stop_at", 99):
            raise _Stop

    def stoppable(self, name):
        method = getattr(self, name)

        def wrapper(*args, **kwargs):
            result = method(*args, **kwargs)
            if name == self.opts.get("stop_in"):
                raise _Stop
            return result
        return wrapper

    def install(self, monkeypatch):
        for name in self.FAKES:
            monkeypatch.setattr(disney, name, self.stoppable(name))
        log, matrix = self.log, self.matrix
        monkeypatch.setattr(disney, "debug", _DebugRecorder(log))
        monkeypatch.setattr(disney, "time", SimpleNamespace(sleep=lambda s: log.append(("sleep", s))))
        monkeypatch.setattr(disney, "logging", SimpleNamespace(info=lambda msg: log.append(("logging.info", msg))))
        monkeypatch.setattr(disney.brightness, "use", lambda s: log.append(("brightness.use", s)))
        monkeypatch.setattr(disney.heartbeat, "beat", lambda: log.append("beat"))
        monkeypatch.setattr(disney.driver, "set_mode", lambda mode: log.append(("set_mode", mode)), raising=False)
        monkeypatch.setattr(disney.driver, "DriverMode", SimpleNamespace(SOFTWARE_EMULATION="EMU"), raising=False)
        monkeypatch.setattr(disney.driver, "is_emulated", lambda: self.opts.get("emulated", True), raising=False)
        monkeypatch.setattr(disney.driver, "hardware_load_failed", self.opts.get("hardware_failed", False),
                            raising=False)
        monkeypatch.setattr(disney.driver, "__version__", "9.9", raising=False)
        monkeypatch.setattr(disney.driver, "RGBMatrix", lambda options: log.append(("RGBMatrix", options)) or matrix)
        # main assigns these module globals; setting them here makes monkeypatch put them back.
        for name in ("surprises", "sound", "show_settings_by_clip"):
            monkeypatch.setattr(disney, name, getattr(disney, name))
        if "version_info" in self.opts:
            monkeypatch.setattr(disney.sys, "version_info", self.opts["version_info"])


@pytest.fixture
def boot(monkeypatch):
    """boot(**opts) runs main() against _Boot's recorders; returns (log, matrix, raised, result)."""
    def go(**opts):
        harness = _Boot(opts)
        harness.install(monkeypatch)
        raised = result = None
        try:
            result = disney.main()
        except BaseException as e:  # SystemExit from the version check is one of them
            raised = e
        return harness.log, harness.matrix, raised, result
    return go
STARTUP = [
    "load_config",
    ("model_defaults", "pi4"),
    ("arguments", {"matrix": {"m": 1}, "defaults": {"d": 1}, "model": "pi4"}),
    ("describe", True, {"matrix": {"m": 1}, "defaults": {"d": 1}, "model": "pi4", "why": "why"}),
    ("info", "described"),
    ("set_mode", "EMU"),
    ("set_forced_surprise", None),
    "load_surprises",
    "brightness_schedule",
    ("brightness.use", None),
    "forced_show_name",
    ("set_forced_show", "forced"),
    "sound_settings",
    ("watch_sound", disney.SoundSettings(), []),
    ("log", "Using RGBMatrixEmulator version 9.9"),
    ("led_matrix_options", True),
    ("RGBMatrix", "options"),
    ("initialize_fonts", 32),
    ("wifi_setup", True),
    ("resolve_parks", ["MK"]),
    ("start_live_updaters", True, PARKS, 300),
    ("log_configured_trips", True),
]
CONFIG = {"pi_model": "pi4", "parks": ["MK"], "matrix": {"m": 1}}


def _ends_in_the_error_handler(log, matrix, message):
    """The loop's except and finally: Clear, two errors (the message, the traceback), Clear."""
    assert log[-4] == "clear"
    assert log[-3] == ("error", message)
    assert log[-2][0] == "error" and log[-2][1].startswith("Traceback")
    assert log[-1] == "clear"


def test_pin_startup_runs_settings_driver_matrix_fonts_wifi_parks_updaters_trips_in_order(boot):
    log, matrix, raised, result = boot(config=CONFIG, stop_in="play_forced_show")
    assert raised is None and result is None  # the loop's except swallowed the stop
    assert log[:len(STARTUP)] == STARTUP
    assert log[len(STARTUP):len(STARTUP) + 1] == [("play_forced_show", True)]
    _ends_in_the_error_handler(log, matrix, "An error occurred: ")
    assert len(log) == len(STARTUP) + 1 + 4


def test_pin_a_real_board_skips_the_emulator_switch_and_names_the_rgbmatrix_version(boot):
    log, *_ = boot(config=CONFIG, emulated=False, stop_in="play_forced_show")
    assert "set_mode" not in [e[0] for e in log if isinstance(e, tuple)]
    assert ("log", "Using rgbmatrix version 9.9") in log and ("log", "Using RGBMatrixEmulator version 9.9") not in log


def test_pin_a_failed_hardware_load_says_it_fell_back_to_the_emulator(boot):
    log, *_ = boot(config=CONFIG, hardware_failed=True, stop_in="play_forced_show")
    i = log.index(("log", "rgbmatrix not installed, falling back to emulator!"))
    assert log[i + 1] == ("log", "Using RGBMatrixEmulator version 9.9")


@pytest.mark.parametrize("settings, line", [
    (disney.SurpriseSettings(enabled=False), "Surprise characters: all off."),
    (disney.SurpriseSettings(off={"b", "a"}), "Surprise characters: off for a, b."),
])
def test_pin_surprise_settings_are_logged_when_anything_is_off(boot, settings, line):
    log, *_ = boot(config=CONFIG, surprises=settings, stop_in="play_forced_show")
    assert log[log.index("load_surprises") + 1] == ("info", line)
    assert disney.surprises is settings


def test_pin_nothing_is_logged_for_surprises_when_all_are_on(boot):
    log, *_ = boot(config=CONFIG, stop_in="play_forced_show")
    assert not any(e[0] == "info" and "Surprise" in e[1] for e in log if isinstance(e, tuple))


def test_pin_a_brightness_schedule_is_used_then_logged(boot):
    log, *_ = boot(config=CONFIG, schedule=SCHEDULE, stop_in="play_forced_show")
    i = log.index("brightness_schedule")
    assert log[i + 1:i + 3] == [("brightness.use", SCHEDULE),
                                ("info", "Brightness schedule: day from 07:00, night from 19:00.")]


def test_pin_an_old_python_exits_before_the_driver_and_matrix(boot):
    log, matrix, raised, _ = boot(config=CONFIG, version_info=(3, 4))
    assert isinstance(raised, SystemExit) and raised.code == 1
    assert log[-2:] == [("watch_sound", disney.SoundSettings(), []), ("error", "Please run with python3")]
    assert "clear" not in log and not any(e[0] == "RGBMatrix" for e in log if isinstance(e, tuple))


def test_pin_no_parks_ends_main_before_any_thread_starts(boot):
    log, matrix, raised, result = boot(config=CONFIG, parks=[])
    assert raised is None and result is None
    assert log[-2:] == [("resolve_parks", ["MK"]), ("error", "No parks found. Exiting.")]


def test_pin_no_configured_parks_asks_for_an_empty_list(boot):
    log, *_ = boot(config={}, parks=[])
    assert ("resolve_parks", []) in log


def test_pin_the_loop_plays_each_operating_park_and_skips_the_closed_one(boot):
    log, matrix, raised, _ = boot(config=CONFIG, parks_data=PARKS, stop_at=3)
    loop = log[len(STARTUP):]
    assert loop == [
        ("play_forced_show", True),
        # cycle 1
        ("wifi_setup", True), ("fireworks_if_due", 3), ("render_logo", True), "beat", ("play_trip_countdown", True, None),
        ("fireworks_if_due", 3), ("park_screen", "Magic Kingdom"), ("attractions", "Magic Kingdom"),
        ("logging.info", "Skipping EPCOT because no attractions are operating."),
        ("fireworks_if_due", 3), ("park_screen", "Hollywood Studios"), ("attractions", "Hollywood Studios"),
        "clear",
        # cycle 2: the trip shown last comes back in
        ("wifi_setup", True), ("fireworks_if_due", 3), ("render_logo", True), "beat",
        ("play_trip_countdown", True, "trip-a"),
        ("fireworks_if_due", 3), ("park_screen", "Magic Kingdom"), ("attractions", "Magic Kingdom"),
        ("logging.info", "Skipping EPCOT because no attractions are operating."),
        ("fireworks_if_due", 3), ("park_screen", "Hollywood Studios"), ("attractions", "Hollywood Studios"),
        "clear",
        # cycle 3 stops at the intro
        ("wifi_setup", True), ("fireworks_if_due", 3), ("render_logo", True),
        "clear", ("error", "An error occurred: "), loop[-2], "clear",
    ]
    assert loop[-2][0] == "error" and loop[-2][1].startswith("Traceback")


def test_pin_with_no_park_data_yet_it_waits_five_seconds_and_goes_round_again(boot):
    log, *_ = boot(config=CONFIG, parks_data=[], stop_at=2)
    loop = log[len(STARTUP):]
    assert loop[:9] == [
        ("play_forced_show", True),
        ("wifi_setup", True), ("fireworks_if_due", 0), ("render_logo", True), "beat", ("play_trip_countdown", True, None),
        ("info", "No parks data yet, waiting..."), ("sleep", 5), "clear",
    ]
    assert loop[9:12] == [("wifi_setup", True), ("fireworks_if_due", 0), ("render_logo", True)]


@pytest.mark.parametrize("stop_in", ["loop_through_attractions", "initialize_park_information_screen",
                                     "play_trip_countdown"])
def test_pin_an_error_anywhere_after_the_matrix_exists_clears_it_logs_and_ends(boot, stop_in):
    log, matrix, raised, result = boot(config=CONFIG, parks_data=PARKS, stop_in=stop_in)
    assert raised is None and result is None
    _ends_in_the_error_handler(log, matrix, "An error occurred: ")


@pytest.mark.parametrize("stop_in", ["initialize_fonts", "led_matrix_options", "start_live_updaters", "log_configured_trips"])
def test_pin_an_error_before_the_loop_is_not_caught_by_it(boot, stop_in):
    log, matrix, raised, result = boot(config=CONFIG, stop_in=stop_in)
    assert isinstance(raised, _Stop) and "clear" not in log
