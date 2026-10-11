"""
Sound through the board's speaker. On a Pi that's a USB sound card: the onboard audio shares the
PWM hardware rgbmatrix times the LEDs with (LLL-install.sh blacklists it), and an I2S amp would
need GPIO 21, the Bonnet's latch pin. On a Mac (an emulator run) it's the Mac's own speakers.

Clips are WAV files in sounds/, which is gitignored: Disney's audio isn't ours to publish. Each
plays in its own process, so drawing never waits on it.

The player runs under a shell that holds a pipe from the app and kills the player when it closes:
when the block ends, or when the app dies any way at all (a crash, the debugger's Stop, kill -9),
since the OS closes the pipe then too. Otherwise a 19-minute soundtrack outlives the app.
"""
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime

from utils import debug

# Relative to the working directory, so run the app from the repo root.
SOUNDS_DIR = "sounds"


def clip_name(title):
    """A show's file name: "Disney's Not-So-Spooky Spectacular" -> "disneys-not-so-spooky-spectacular"."""
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"['’]", "", title.lower())).strip("-")


def find_clip(names, sounds_dir=None):
    """The first of sounds/<name>.wav that exists, or None. aplay plays WAV only."""
    sounds_dir = sounds_dir or SOUNDS_DIR
    for name in names:
        path = os.path.join(sounds_dir, f"{name}.wav")
        if os.path.isfile(path):
            return path
    return None


def in_quiet_hours(quiet_hours, now):
    """True if now's local time is within (start, end); a span like 22:00-08:00 wraps midnight."""
    if not quiet_hours:
        return False
    start, end = quiet_hours
    clock = now.astimezone().time() if now.tzinfo else now.time()
    if start <= end:
        return start <= clock < end
    return clock >= start or clock < end


def player_command(path, device=None, platform=sys.platform):
    """afplay on a Mac; aplay (ALSA) on a Pi, on device if given."""
    if platform == "darwin":
        return ["afplay", path]
    return ["aplay", "-q"] + (["-D", device] if device else []) + [path]


# Runs the player in the background and waits for the app's pipe to close (read hits EOF), then
# kills it; a clip that already ended makes the kill a no-op.
_GUARD = '"$@" & player=$!; read _; kill "$player" 2>/dev/null'


def _start(command):
    """The player under _GUARD, or None if it isn't installed (the shell alone wouldn't say)."""
    if shutil.which(command[0]) is None:
        debug.warning(f"Can't play sound: {command[0]} isn't installed.")
        return None
    return subprocess.Popen(["sh", "-c", _GUARD, "sh"] + command, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _stop(process):
    """Close the pipe, so the guard kills the player and exits; kill the guard if it hangs."""
    process.stdin.close()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


@contextmanager
def playing(names, settings, now=None):
    """Play the first clip of names that's in sounds/ while the with block runs, and stop it when the
    block ends or the app dies. Silent when sound is off, in quiet hours, or with no clip; a missing
    player or sound card is logged and never stops the screen."""
    now = now or datetime.now().astimezone()
    process = None
    if not settings.enabled:
        pass
    elif in_quiet_hours(settings.quiet_hours, now):
        debug.info(f"Quiet hours: not playing {names[0]}.")
    else:
        path = find_clip(names)
        if path is None:
            debug.info(f"No sound for {names[0]}: add one of {', '.join(n + '.wav' for n in names)} to {SOUNDS_DIR}/.")
        else:
            command = player_command(path, settings.device)
            try:
                process = _start(command)
                if process is not None:
                    debug.info(f"Playing {path}.")
            except OSError as e:
                debug.warning(f"Couldn't play {path} with {command[0]}: {e}")
    try:
        yield process
    finally:
        if process is not None:
            _stop(process)
