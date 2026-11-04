import pytest

import utils.wifi_setup as wifi_setup
from utils.wifi_setup import hotspot_name


@pytest.fixture
def state(tmp_path):
    path = tmp_path / "comitup-state"

    def write(text):
        path.write_text(text)
        return str(path)
    return write


def test_the_hotspot_name_while_comitup_is_in_its_setup_hotspot(state):
    assert hotspot_name(state("HOTSPOT Disneypi-setup\n")) == "Disneypi-setup"


@pytest.mark.parametrize("text", ["CONNECTING Disneypi-setup\n", "CONNECTED Disneypi-setup\n", "HOTSPOT\n", "", "\n"])
def test_no_name_once_it_joins_a_network_or_with_no_name_to_show(state, text):
    assert hotspot_name(state(text)) is None


def test_no_comitup_means_no_setup_screen(tmp_path):
    assert hotspot_name(str(tmp_path / "missing")) is None


def test_an_unreadable_file_is_warned_about_once_and_shows_nothing(tmp_path, monkeypatch):
    warnings = []
    monkeypatch.setattr(wifi_setup.debug, "warning", warnings.append)
    monkeypatch.setattr(wifi_setup, "_last_problem", None)
    folder = str(tmp_path)  # reading a folder raises IsADirectoryError, an OSError
    assert hotspot_name(folder) is None
    assert hotspot_name(folder) is None
    assert len(warnings) == 1 and folder in warnings[0]


def test_bytes_that_arent_text_show_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(wifi_setup.debug, "warning", lambda message: None)
    path = tmp_path / "comitup-state"
    path.write_bytes(b"HOTSPOT \xff\xfe\n")
    assert hotspot_name(str(path)) is None
