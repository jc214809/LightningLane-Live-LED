import utils.settings_pin as settings_pin
from utils.settings_pin import CHECK_EVERY_S, shown_pin


class Clocks:
    def __init__(self):
        self.wall, self.mono = 1_000_000.0, 50.0

    def ask(self, path):
        return shown_pin(path, clock=lambda: self.wall, monotonic=lambda: self.mono)


def test_the_pin_shows_until_its_expiry(tmp_path):
    path = tmp_path / "pin"
    clocks = Clocks()
    path.write_text(f"0427 {clocks.wall + 120:.0f}\n")
    assert clocks.ask(str(path)) == "0427"
    clocks.wall += 120
    assert clocks.ask(str(path)) is None


def test_the_file_is_read_at_most_once_a_second(tmp_path):
    path = tmp_path / "pin"
    clocks = Clocks()
    assert clocks.ask(str(path)) is None
    path.write_text(f"1234 {clocks.wall + 120:.0f}\n")
    clocks.mono += CHECK_EVERY_S / 2
    assert clocks.ask(str(path)) is None, "still the cached read"
    clocks.mono += CHECK_EVERY_S / 2
    assert clocks.ask(str(path)) == "1234"
    path.unlink()  # signed in: the server removes it
    clocks.mono += CHECK_EVERY_S
    assert clocks.ask(str(path)) is None


def test_a_bad_file_shows_nothing_and_is_warned_about_once(tmp_path, monkeypatch):
    warnings = []
    monkeypatch.setattr(settings_pin.debug, "warning", warnings.append)
    monkeypatch.setattr(settings_pin, "_last_problem", None)
    path = tmp_path / "pin"
    path.write_text("not a pin file at all\n")
    clocks = Clocks()
    for _ in range(3):
        assert clocks.ask(str(path)) is None
        clocks.mono += CHECK_EVERY_S
    assert len(warnings) == 1


def test_letters_in_place_of_digits_show_nothing(tmp_path):
    path = tmp_path / "pin"
    clocks = Clocks()
    path.write_text(f"12a4 {clocks.wall + 120:.0f}\n")
    assert clocks.ask(str(path)) is None
