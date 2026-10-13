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
    return started


ON = SoundSettings(True, None, OVERNIGHT)
EVENING = datetime(2026, 10, 10, 21, 0)


def test_plays_while_the_block_runs_and_stops_after(clips, popen):
    with sound.playing(["happily-ever-after", "fireworks"], ON, EVENING) as process:
        assert process is popen[0] and not process.stdin.closed
    assert popen[0].command[:2] == ["sh", "-c"], "under the guard that dies with the app"
    assert popen[0].command[-1] == str(clips / "fireworks.wav")
    assert popen[0].stdin.closed, "closing the pipe stops the player"


def test_stops_even_when_the_screen_fails(clips, popen):
    with pytest.raises(RuntimeError):
        with sound.playing(["fireworks"], ON, EVENING):
            raise RuntimeError("draw failed")
    assert popen[0].stdin.closed


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
    assert popen == []


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
