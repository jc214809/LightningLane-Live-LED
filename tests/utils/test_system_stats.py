import pytest

from utils import system_stats


@pytest.fixture
def board(tmp_path, monkeypatch):
    """Point the module at fake sysfs files; each test writes the ones its board has."""
    paths = {"THERMAL_PATH": tmp_path / "temp", "CPU_FREQ_PATH": tmp_path / "freq",
             "THROTTLED_PATH": tmp_path / "throttled"}
    for name, path in paths.items():
        monkeypatch.setattr(system_stats, name, str(path))
    monkeypatch.setattr(system_stats.os, "getloadavg", lambda: (1.44, 1.0, 1.0))
    return paths


def test_a_pi_reports_load_temperature_clock_and_throttle_flags(board):
    board["THERMAL_PATH"].write_text("61234\n")
    board["CPU_FREQ_PATH"].write_text("1500000\n")
    board["THROTTLED_PATH"].write_text("50005\n")
    assert system_stats.describe() == "load 1.4, 61°C, 1500 MHz, throttled 0x50005"


def test_what_the_machine_lacks_is_left_out(board):
    assert system_stats.describe() == "load 1.4"


def test_unreadable_values_are_left_out_not_raised(board):
    board["THERMAL_PATH"].write_text("n/a")
    board["CPU_FREQ_PATH"].write_text("")
    board["THROTTLED_PATH"].write_text("zzz")
    assert system_stats.describe() == "load 1.4"


def test_without_a_load_average_the_rest_still_shows(board, monkeypatch):
    def no_load():
        raise OSError("no loadavg")
    monkeypatch.setattr(system_stats.os, "getloadavg", no_load)
    board["THERMAL_PATH"].write_text("40000")
    assert system_stats.describe() == "40°C"
