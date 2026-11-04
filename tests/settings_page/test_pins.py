import pytest

import settings_page.pins as pins
from settings_page.pins import PIN_SHOWN_S, SEND_EVERY_S, SESSION_S, TRIES_PER_PIN, PinGate


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


def test_signing_out_ends_only_that_session(gate, clock):
    gate.show_pin()
    first = gate.try_pin(board_pin(gate)[0])
    gate.show_pin()
    second = gate.try_pin(board_pin(gate)[0])
    gate.sign_out(first)
    assert not gate.signed_in(first) and gate.signed_in(second)
    gate.sign_out(first)
    gate.sign_out(None)  # no cookie, or one already gone: nothing to do


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


class Sends:
    """A fake pushover.send_pin with the keys bound: records (pin, seconds left), or raises."""
    def __init__(self, error=None):
        self.sent, self.error = [], error

    def __call__(self, pin, left):
        if self.error:
            raise self.error
        self.sent.append((pin, left))


def test_sending_puts_the_pin_on_the_board_and_sends_the_same_one(gate, clock):
    send = Sends()
    assert gate.send_pin(send) == "sent"
    assert send.sent == [(board_pin(gate)[0], PIN_SHOWN_S)]


def test_one_send_a_minute_whoever_presses_it(gate, clock):
    send = Sends()
    gate.send_pin(send)
    clock.now += SEND_EVERY_S - 1
    assert gate.send_pin(send) == "wait" and len(send.sent) == 1
    clock.now += 1
    assert gate.send_pin(send) == "sent"
    assert send.sent[1] == (send.sent[0][0], PIN_SHOWN_S - SEND_EVERY_S), "the PIN that's up, with its time left"


def test_a_failed_send_is_logged_without_the_pin_counts_toward_the_limit_and_leaves_it_on_the_board(
        gate, clock, monkeypatch):
    errors = []
    monkeypatch.setattr(pins.debug, "error", errors.append)
    assert gate.send_pin(Sends(OSError("no route to host"))) == "failed"
    pin = board_pin(gate)[0]
    assert len(errors) == 1 and "no route to host" in errors[0] and pin not in errors[0]
    assert gate.send_pin(Sends()) == "wait"


def test_a_pin_out_of_tries_isnt_sent(gate, clock):
    gate.show_pin()
    pin = board_pin(gate)[0]
    for _ in range(TRIES_PER_PIN):
        gate.try_pin("1111" if pin != "1111" else "2222")
    send = Sends()
    assert gate.send_pin(send) == "used" and send.sent == []


def test_after_someone_signs_in_the_next_ask_gets_a_new_pin(gate, clock):
    """Not the used one, which isn't on the board any more."""
    gate.show_pin()
    gate.try_pin(board_pin(gate)[0])
    clock.now += 10
    assert gate.show_pin() == PIN_SHOWN_S
    pin = board_pin(gate)[0]
    assert gate.try_pin(pin)
