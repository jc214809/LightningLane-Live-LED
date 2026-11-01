import os
import subprocess
import sys
import textwrap
import time as _time
from datetime import datetime, time, timedelta, timezone

import pytest

from utils import sound
from utils.config import SoundSettings


@pytest.mark.parametrize("title, expected", [
    ("Happily Ever After", "happily-ever-after"),
    ("Disney's Not-So-Spooky Spectacular", "disneys-not-so-spooky-spectacular"),
    ("Disney’s Not-So-Spooky Spectacular", "disneys-not-so-spooky-spectacular"),  # the API's curly apostrophe
    ("  EPCOT Forever! ", "epcot-forever"),
])
def test_clip_name(title, expected):
    assert sound.clip_name(title) == expected


def test_find_clip_takes_the_first_wav_that_exists(tmp_path):
    (tmp_path / "fireworks.wav").write_bytes(b"")
    (tmp_path / "happily-ever-after.mp3").write_bytes(b"")  # aplay can't play it
    assert sound.find_clip(["happily-ever-after", "fireworks"], str(tmp_path)) == str(tmp_path / "fireworks.wav")
    (tmp_path / "happily-ever-after.wav").write_bytes(b"")
    assert sound.find_clip(["happily-ever-after", "fireworks"], str(tmp_path)).endswith("happily-ever-after.wav")
    assert sound.find_clip(["nothing"], str(tmp_path)) is None
    assert sound.find_clip(["fireworks"], str(tmp_path / "missing")) is None


OVERNIGHT = (time(22, 0), time(8, 0))


@pytest.mark.parametrize("clock, quiet_hours, expected", [
    (time(21, 59), OVERNIGHT, False),
    (time(22, 0), OVERNIGHT, True),
    (time(2, 30), OVERNIGHT, True),  # wraps midnight
    (time(7, 59), OVERNIGHT, True),
    (time(8, 0), OVERNIGHT, False),
    (time(13, 0), (time(12, 0), time(14, 0)), True),  # a span within the day
    (time(15, 0), (time(12, 0), time(14, 0)), False),
    (time(3, 0), None, False),
])
def test_in_quiet_hours(clock, quiet_hours, expected):
    assert sound.in_quiet_hours(quiet_hours, datetime.combine(datetime(2026, 10, 10), clock)) is expected


def test_quiet_hours_are_the_boards_local_time():
    local = datetime(2026, 10, 10, 23, 0).astimezone()  # 11pm here, whatever the zone
    assert sound.in_quiet_hours(OVERNIGHT, local.astimezone(timezone.utc)) is True


def test_player_command():
    assert sound.player_command("sounds/a.wav", platform="darwin") == ["afplay", "sounds/a.wav"]
    assert sound.player_command("sounds/a.wav", platform="linux") == ["aplay", "-q", "sounds/a.wav"]
    assert sound.player_command("sounds/a.wav", "plughw:1,0", platform="linux") == [
        "aplay", "-q", "-D", "plughw:1,0", "sounds/a.wav"]


class FakePipe:
    closed = False

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self, command, hangs=False):
        self.command, self.hangs = command, hangs
        self.stdin = FakePipe()
        self.killed = False

    def wait(self, timeout=None):
        if self.hangs:
            raise subprocess.TimeoutExpired(self.command, timeout)

    def kill(self):
        self.killed = True


@pytest.fixture
def clips(tmp_path, monkeypatch):
    (tmp_path / "fireworks.wav").write_bytes(b"")
    monkeypatch.setattr(sound, "SOUNDS_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def popen(monkeypatch):
    started = []

    def fake(command, **kwargs):
        started.append(FakeProcess(command))
        return started[-1]
    monkeypatch.setattr(sound.subprocess, "Popen", fake)
    monkeypatch.setattr(sound.shutil, "which", lambda name: f"/usr/bin/{name}")  # CI has no aplay
    monkeypatch.setattr(sound, "set_volume", lambda settings: started.append(("volume", settings.volume)))
    return started


ON = SoundSettings(True, None, OVERNIGHT)
EVENING = datetime(2026, 10, 10, 21, 0)


def test_plays_while_the_block_runs_and_stops_after(clips, popen):
    with sound.playing(["happily-ever-after", "fireworks"], ON, EVENING) as process:
        assert popen[0] == ("volume", 80), "the volume is set before the clip starts"
        assert process is popen[1] and not process.stdin.closed
    assert process.command[:2] == ["sh", "-c"], "under the guard that dies with the app"
    assert process.command[-1] == str(clips / "fireworks.wav")
    assert process.stdin.closed, "closing the pipe stops the player"


def test_stops_even_when_the_screen_fails(clips, popen):
    with pytest.raises(RuntimeError):
        with sound.playing(["fireworks"], ON, EVENING):
            raise RuntimeError("draw failed")
    assert popen[1].stdin.closed


def test_a_guard_that_hangs_is_killed(clips, monkeypatch):
    process = FakeProcess(["sh"], hangs=True)
    monkeypatch.setattr(sound.subprocess, "Popen", lambda command, **kwargs: process)
    monkeypatch.setattr(sound.shutil, "which", lambda name: f"/usr/bin/{name}")
    with sound.playing(["fireworks"], ON, EVENING):
        pass
    assert process.stdin.closed and process.killed


def test_a_missing_player_is_logged_not_started(clips, popen, monkeypatch):
    monkeypatch.setattr(sound.shutil, "which", lambda name: None)
    with sound.playing(["fireworks"], ON, EVENING) as process:
        assert process is None
    assert not any(isinstance(p, FakeProcess) for p in popen), "no player started"


@pytest.mark.parametrize("settings, now, names", [
    (SoundSettings(False, None, None), EVENING, ["fireworks"]),  # sound off
    (ON, EVENING + timedelta(hours=2), ["fireworks"]),  # 11pm: quiet hours
    (ON, EVENING, ["no-such-show"]),  # no clip
])
def test_silent(clips, popen, settings, now, names):
    with sound.playing(names, settings, now) as process:
        assert process is None
    assert popen == []


def test_no_player_or_sound_card_never_stops_the_screen(clips, monkeypatch):
    def missing(command, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", command[0])
    monkeypatch.setattr(sound.subprocess, "Popen", missing)
    ran = []
    with sound.playing(["fireworks"], ON, EVENING) as process:
        ran.append(process)
    assert ran == [None]


# ---- The real guard: the player never outlives the block or the app ----

def _player_pid(pid_file):
    """A stand-in for afplay/aplay that records its pid and plays for 30s."""
    return ["sh", "-c", f'echo $$ > "{pid_file}"; exec sleep 30']


def _wait_for(check, seconds=5.0):
    deadline = _time.monotonic() + seconds
    while _time.monotonic() < deadline:
        if check():
            return True
        _time.sleep(0.05)
    return False


def _gone(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def _started_pid(pid_file):
    assert _wait_for(lambda: pid_file.exists() and pid_file.read_text().strip()), "the player never started"
    return int(pid_file.read_text())


def test_the_real_player_stops_when_the_block_ends(clips, tmp_path, monkeypatch):
    pid_file = tmp_path / "player.pid"
    monkeypatch.setattr(sound, "player_command", lambda path, device=None: _player_pid(pid_file))
    with sound.playing(["fireworks"], ON, EVENING):
        pid = _started_pid(pid_file)
        assert not _gone(pid)
    assert _wait_for(lambda: _gone(pid)), "the player kept playing after the block"


def test_the_real_player_dies_with_the_app(clips, tmp_path):
    """kill -9 runs no cleanup in the app; the closed pipe still stops the player."""
    pid_file = tmp_path / "player.pid"
    app = textwrap.dedent(f"""
        import os, signal
        from datetime import datetime
        from utils import sound
        from utils.config import SoundSettings
        sound.SOUNDS_DIR = {str(clips)!r}
        sound.player_command = lambda path, device=None: {_player_pid(pid_file)!r}
        with sound.playing(["fireworks"], SoundSettings(True), datetime(2026, 10, 10, 21, 0)):
            while not os.path.exists({str(pid_file)!r}):
                pass
            os.kill(os.getpid(), signal.SIGKILL)
    """)
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    subprocess.run([sys.executable, "-c", app], cwd=repo, timeout=20)
    pid = _started_pid(pid_file)
    assert _wait_for(lambda: _gone(pid)), "the player outlived the app"


# ---- The badges' check: what keeps the show silent, found without playing ----

CARDS = textwrap.dedent("""\
     0 [vc4hdmi        ]: vc4-hdmi - vc4-hdmi
                          vc4-hdmi
     1 [Device         ]: USB-Audio - USB Audio Device
                          C-Media Electronics Inc. USB Audio Device at usb-3f980000.usb-1.4, full speed
""")


@pytest.fixture
def cards(tmp_path):
    path = tmp_path / "cards"
    path.write_text(CARDS)
    return str(path)


@pytest.mark.parametrize("device, expected", [
    (None, True),  # ALSA's default: any card will do
    ("default", True),
    ("plughw:1,0", True),
    ("hw:1", True),
    ("plughw:CARD=Device,DEV=0", True),
    ("hw:Device", True),
    ("plughw:2,0", False),  # unplugged
    ("hw:CARD=Headphones", False),
])
def test_card_present(cards, device, expected):
    assert sound.card_present(device, cards) is expected


def test_no_cards_at_all(tmp_path):
    path = tmp_path / "cards"
    path.write_text("--- no soundcards ---\n")
    assert sound.card_present(None, str(path)) is False
    assert sound.card_present(None, str(tmp_path / "missing")) is False, "no ALSA at all"


HEA = [sound.show_clips("Happily Ever After")]


@pytest.fixture
def players(monkeypatch):
    installed = {"aplay", "afplay"}
    monkeypatch.setattr(sound.shutil, "which", lambda name: f"/usr/bin/{name}" if name in installed else None)
    return installed


def test_problem_is_none_when_all_is_well(clips, cards, players):
    assert sound.problem(ON, HEA, str(clips), "linux", cards) is None


def test_problem_is_none_with_sound_off(tmp_path, players):
    assert sound.problem(SoundSettings(False), HEA, str(tmp_path), "linux", str(tmp_path / "missing")) is None


def test_no_music_when_a_show_has_no_clip(tmp_path, cards, players):
    assert sound.problem(ON, HEA, str(tmp_path), "linux", cards) == sound.NO_MUSIC
    (tmp_path / "happily-ever-after.wav").write_bytes(b"RIFF")
    assert sound.problem(ON, HEA, str(tmp_path), "linux", cards) is None
    party = HEA + [sound.show_clips("Boo-to-You Parade")]
    assert sound.problem(ON, party, str(tmp_path), "linux", cards) == sound.NO_MUSIC, "every show needs one"


def test_cant_play_without_aplay(clips, cards, players):
    players.discard("aplay")
    assert sound.problem(ON, HEA, str(clips), "linux", cards) == sound.CANT_PLAY


def test_cant_play_without_the_configured_card(tmp_path, cards, players):
    unplugged = SoundSettings(True, "plughw:2,0")
    assert sound.problem(unplugged, HEA, str(tmp_path), "linux", cards) == sound.CANT_PLAY, "wins over no music"


def test_a_mac_needs_only_afplay(clips, tmp_path, players):
    assert sound.problem(ON, HEA, str(clips), "darwin", str(tmp_path / "missing")) is None
    players.discard("afplay")
    assert sound.problem(ON, HEA, str(clips), "darwin") == sound.CANT_PLAY


def test_current_problem_is_none_until_watched():
    assert sound.current_problem() is None


def test_current_problem_rechecks_once_a_minute_and_logs_changes(monkeypatch):
    found = [sound.NO_MUSIC]
    monkeypatch.setattr(sound, "problem", lambda settings, shows: found[0])
    monkeypatch.setattr(sound, "find_clip", lambda names: None)
    logged = []
    monkeypatch.setattr(sound.debug, "warning", logged.append)
    monkeypatch.setattr(sound.debug, "info", logged.append)
    clock = [100.0]
    sound.watch(ON, HEA)

    assert sound.current_problem(lambda: clock[0]) == sound.NO_MUSIC
    assert len(logged) == 1 and "happily-ever-after" in logged[0]
    found[0] = None  # the clip was copied in
    clock[0] += 30
    assert sound.current_problem(lambda: clock[0]) == sound.NO_MUSIC, "not rechecked every frame"
    clock[0] += 30
    assert sound.current_problem(lambda: clock[0]) is None
    assert logged[-1] == "Sound problem fixed; badge off."
    clock[0] += 60
    sound.current_problem(lambda: clock[0])
    assert len(logged) == 2, "logged on a change, not every check"


# ---- Volume, set with amixer before each clip ----

class FakeRun:
    """subprocess.run for amixer: scontrols lists `controls`; sset exits with `code`."""
    def __init__(self, controls=("Headphone", "PCM"), code=0, raises=None):
        self.controls, self.code, self.raises, self.calls = controls, code, raises, []

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        if self.raises:
            raise self.raises
        if command[-1] == "scontrols":
            out = "".join(f"Simple mixer control '{c}',0\n" for c in self.controls)
            return subprocess.CompletedProcess(command, 0, out, "")
        return subprocess.CompletedProcess(command, self.code, "", "amixer: Invalid card" if self.code else "")


@pytest.fixture
def amixer(monkeypatch):
    monkeypatch.setattr(sound.shutil, "which", lambda name: f"/usr/bin/{name}")
    warnings = []
    monkeypatch.setattr(sound.debug, "warning", warnings.append)
    return warnings


@pytest.mark.parametrize("device, card", [
    (None, []), ("plughw:1,0", ["-c", "1"]), ("plughw:CARD=Device,DEV=0", ["-c", "Device"]),
])
def test_set_volume_sets_the_speakers_pcm_on_its_card(amixer, device, card):
    run = FakeRun()
    assert sound.set_volume(SoundSettings(True, device, None, 65), "linux", run)
    assert run.calls == [["amixer"] + card + ["scontrols"], ["amixer"] + card + ["-q", "sset", "PCM", "65%"]]
    assert amixer == []


def test_set_volume_falls_back_to_the_cards_first_control(amixer):
    run = FakeRun(controls=("Mic", "Auto Gain Control"))
    assert sound.set_volume(ON, "linux", run)
    assert run.calls[-1][-2:] == ["Mic", "80%"]


@pytest.mark.parametrize("run, warning", [
    (FakeRun(controls=()), "lists no controls"),
    (FakeRun(code=1), "amixer PCM said amixer: Invalid card"),
    (FakeRun(raises=subprocess.TimeoutExpired("amixer", 5)), "Can't set the volume with amixer"),
    (FakeRun(raises=OSError("no such file")), "no such file"),
])
def test_set_volume_logs_a_failure_and_carries_on(amixer, run, warning):
    assert sound.set_volume(ON, "linux", run) is False
    assert warning in amixer[0]


def test_set_volume_skips_a_mac_and_a_board_without_amixer(monkeypatch):
    run = FakeRun()
    assert sound.set_volume(ON, "darwin", run) is False
    monkeypatch.setattr(sound.shutil, "which", lambda name: None)
    assert sound.set_volume(ON, "linux", run) is False
    assert run.calls == []


def test_saved_volume_is_read_fresh_so_the_settings_page_needs_no_restart(monkeypatch):
    assert sound.saved_volume(80, lambda: {"sound": {"volume": 40}}) == 40
    assert sound.saved_volume(80, lambda: {}) == 80


def test_saved_volume_falls_back_when_config_json_cant_be_read(monkeypatch):
    warnings = []
    monkeypatch.setattr(sound.debug, "warning", warnings.append)

    def broken():
        raise ValueError("Expecting value")
    assert sound.saved_volume(65, broken) == 65
    assert "Expecting value" in warnings[0]


def test_playing_sets_the_volume_saved_now_not_the_start_up_one(clips, popen, monkeypatch):
    monkeypatch.setattr(sound, "saved_volume", lambda fallback: 30)
    with sound.playing(["fireworks"], ON, EVENING):
        pass
    assert popen[0] == ("volume", 30)


# ---- The settings page's test sound ----

def test_the_chime_is_a_short_wav(tmp_path):
    import wave
    path = str(tmp_path / "chime.wav")
    sound.chime_wav(path)
    with wave.open(path) as f:
        assert (f.getnchannels(), f.getsampwidth()) == (1, 2)
        assert 0.5 < f.getnframes() / f.getframerate() < 2


def test_the_test_plays_a_few_seconds():
    assert sound.test_command("a.wav", "plughw:1,0", "linux") == ["aplay", "-q", "-d", "4", "-D", "plughw:1,0", "a.wav"]
    assert sound.test_command("a.wav", None, "darwin") == ["afplay", "-t", "4", "a.wav"]


class FakePlayer(FakeRun):
    """FakeRun for amixer, and aplay exiting with `play_code` and `play_error`."""
    def __init__(self, play_code=0, play_error="", **kwargs):
        super().__init__(**kwargs)
        self.play_code, self.play_error, self.played = play_code, play_error, []

    def __call__(self, command, **kwargs):
        if command[0] != "aplay":
            return super().__call__(command, **kwargs)
        self.played.append((command, os.path.exists(command[-1])))
        return subprocess.CompletedProcess(command, self.play_code, "", self.play_error)


def test_a_test_plays_the_start_of_the_fireworks_music_at_the_volume(amixer, clips):
    run = FakePlayer()
    settings = SoundSettings(True, "plughw:1,0", None, 45)
    assert sound.play_test(settings, "linux", run, str(clips)) == \
        (True, "Played the start of the fireworks music at 45%.")
    assert run.calls[1][-2:] == ["PCM", "45%"], "the volume first"
    assert run.played == [(["aplay", "-q", "-d", "4", "-D", "plughw:1,0", str(clips / "fireworks.wav")], True)]


def test_with_no_music_a_test_plays_a_chime(amixer, tmp_path):
    run = FakePlayer()
    assert sound.play_test(ON, "linux", run, str(tmp_path)) == (True, "Played a chime at 80%.")
    assert run.played[0][0][-1].endswith("chime.wav") and run.played[0][1], "the chime existed while it played"


def test_a_test_says_why_it_didnt_play(amixer, clips):
    run = FakePlayer(play_code=1, play_error="aplay: main:831: audio open error: Device or resource busy\n")
    assert sound.play_test(ON, "linux", run, str(clips)) == \
        (False, "aplay said aplay: main:831: audio open error: Device or resource busy")
    assert "Device or resource busy" in amixer[-1]


def test_a_test_with_no_player_or_no_volume_says_so(amixer, clips, monkeypatch):
    run = FakePlayer(controls=())
    assert sound.play_test(ON, "linux", run, str(clips)) == \
        (True, "Played the start of the fireworks music at the speaker's own level: the volume couldn't be set.")
    monkeypatch.setattr(sound.shutil, "which", lambda name: None)
    assert sound.play_test(ON, "linux", FakePlayer(), str(clips)) == (False, "aplay isn't installed.")
