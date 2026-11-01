import pytest

import settings_page.pins as pins
from settings_page.pins import PIN_SHOWN_S, SESSION_S, TRIES_PER_PIN, PinGate


class Clock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def gate(tmp_path, clock):
    return PinGate(str(tmp_path / "pin"), clock)


def board_pin(gate):
    """The PIN and expiry the board would draw, from the file."""
    with open(gate.pin_file) as f:
        pin, expires = f.read().split()
    return pin, float(expires)


def test_asking_puts_a_4_digit_pin_on_the_board_until_it_runs_out(gate, clock):
    assert gate.show_pin() == PIN_SHOWN_S
    pin, expires = board_pin(gate)
    assert len(pin) == 4 and pin.isdigit()
    assert expires == clock.now + PIN_SHOWN_S


def test_asking_again_keeps_the_pin_that_is_up(gate, clock):
    gate.show_pin()
    first = board_pin(gate)
    clock.now += 30
    assert gate.show_pin() == PIN_SHOWN_S - 30
    assert board_pin(gate) == first


def test_the_right_pin_signs_in_for_an_hour_and_comes_off_the_board(gate, clock):
    gate.show_pin()
    token = gate.try_pin(board_pin(gate)[0])
    assert token and gate.signed_in(token)
    with pytest.raises(FileNotFoundError):
        board_pin(gate)
    assert gate.try_pin("0000") is None, "used up"
    clock.now += SESSION_S - 1
    assert gate.signed_in(token)
    clock.now += 1
    assert not gate.signed_in(token)


def test_a_pin_runs_out(gate, clock):
    gate.show_pin()
    pin = board_pin(gate)[0]
    clock.now += PIN_SHOWN_S
    assert gate.try_pin(pin) is None


def test_wrong_guesses_use_the_pin_up_and_no_new_one_comes_until_it_would_have_run_out(gate, clock, monkeypatch):
    warnings = []
    monkeypatch.setattr(pins.debug, "warning", warnings.append)
    gate.show_pin()
    pin = board_pin(gate)[0]
    wrong = "1111" if pin != "1111" else "2222"
    for _ in range(TRIES_PER_PIN):
        assert gate.try_pin(wrong) is None
    assert len(warnings) == TRIES_PER_PIN
    assert gate.try_pin(pin) is None, "locked once its tries are used"
    with pytest.raises(FileNotFoundError):
        board_pin(gate)
    clock.now += 60
    gate.show_pin()
    with pytest.raises(FileNotFoundError):
        board_pin(gate)
    clock.now += PIN_SHOWN_S - 60
    gate.show_pin()
    new_pin = board_pin(gate)[0]
    assert gate.try_pin(new_pin)


def test_no_pin_asked_for_means_no_way_in(gate):
    assert gate.try_pin("") is None and gate.try_pin("1234") is None
    assert not gate.signed_in(None) and not gate.signed_in("made-up")


def test_sessions_are_capped_dropping_the_oldest(gate, clock, monkeypatch):
    monkeypatch.setattr(pins, "MAX_SESSIONS", 2)
    tokens = []
    for _ in range(3):
        gate.show_pin()
        tokens.append(gate.try_pin(board_pin(gate)[0]))
        clock.now += PIN_SHOWN_S
    assert [gate.signed_in(t) for t in tokens] == [False, True, True]


def test_a_pin_file_that_cant_be_written_is_logged_not_raised(tmp_path, clock, monkeypatch):
    errors = []
    monkeypatch.setattr(pins.debug, "error", errors.append)
    gate = PinGate(str(tmp_path / "missing-folder" / "pin"), clock)
    gate.show_pin()
    assert len(errors) == 1 and "can't put the PIN on the board" in errors[0]
