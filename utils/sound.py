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
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave
from contextlib import contextmanager
from datetime import datetime

from utils import debug
from utils.config import load_config, sound_settings

# Relative to the working directory, so run the app from the repo root.
SOUNDS_DIR = "sounds"
# ALSA's list of sound cards on a Pi: " 1 [Device         ]: USB-Audio - ...", one per card.
CARDS_FILE = "/proc/asound/cards"


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


# The mixer control a USB speaker's volume goes by, in the order to try; else the card's first one.
VOLUME_CONTROLS = ("PCM", "Speaker", "Master", "Headphone")
_CONTROL = re.compile(r"Simple mixer control '([^']+)'")


def saved_volume(fallback, load=load_config):
    """config.json's sound.volume as it is now: the settings page changes it without restarting
    the app. fallback (the start-up one) if the file can't be read."""
    try:
        return sound_settings(load()).volume
    except (OSError, ValueError, AttributeError) as e:
        debug.warning(f"Can't read the volume from config.json ({e}); using {fallback}.")
        return fallback


def set_volume(settings, platform=sys.platform, run=subprocess.run):
    """Set the speaker to settings.volume percent with amixer: before each clip, so a speaker
    plugged back in (at its own default, often full) is turned down again. True if it was set;
    a missing amixer or a card with no control is logged and never stops the clip."""
    if platform == "darwin" or shutil.which("amixer") is None:
        return False
    card = _card(settings.device)
    command = ["amixer"] + (["-c", card] if card else [])
    try:
        found = run(command + ["scontrols"], capture_output=True, text=True, timeout=5)
        controls = _CONTROL.findall(found.stdout or "")
        control = next((c for c in VOLUME_CONTROLS if c in controls), controls[0] if controls else None)
        if control is None:
            debug.warning(f"Can't set the volume: amixer lists no controls for {settings.device or 'the default card'}.")
            return False
        done = run(command + ["-q", "sset", control, f"{settings.volume}%"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as e:
        debug.warning(f"Can't set the volume with amixer: {e}")
        return False
    if done.returncode:
        debug.warning(f"Can't set the volume: amixer {control} said {done.stderr.strip() or done.returncode}")
        return False
    return True


# The settings page's Play test sound: this long, from the start of the fireworks music, else a chime.
TEST_SECONDS = 4
TEST_CLIP = "fireworks"


def chime_wav(path, rate=22050):
    """Write a short two-note chime to path (16-bit mono WAV), for a test with no music in sounds/."""
    frames = bytearray()
    for freq, length in ((660, 0.35), (880, 0.6)):
        count = int(rate * length)
        for i in range(count):
            fade = min(1.0, i / (rate * 0.01), (count - i) / (rate * 0.15))  # no clicks at either end
            frames += struct.pack("<h", int(12000 * fade * math.sin(2 * math.pi * freq * i / rate)))
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(bytes(frames))


def test_command(path, device=None, platform=sys.platform):
    """The player for TEST_SECONDS of path: afplay on a Mac, aplay on a Pi (on device if given)."""
    if platform == "darwin":
        return ["afplay", "-t", str(TEST_SECONDS), path]
    return ["aplay", "-q", "-d", str(TEST_SECONDS)] + (["-D", device] if device else []) + [path]


def play_test(settings, platform=sys.platform, run=subprocess.run, sounds_dir=None):
    """Set settings.volume and play a few seconds at it, for the settings page; waits until it's
    done. (True, what played) or (False, why not). Sound needn't be on: it's for setting it up."""
    if shutil.which(test_command("", platform=platform)[0]) is None:
        return False, f"{test_command('', platform=platform)[0]} isn't installed."
    volume_set = set_volume(settings, platform, run)
    clip = find_clip([TEST_CLIP], sounds_dir)
    with tempfile.TemporaryDirectory() as folder:
        if clip is None:
            clip = os.path.join(folder, "chime.wav")
            chime_wav(clip)
        command = test_command(clip, settings.device, platform)
        try:
            done = run(command, capture_output=True, text=True, timeout=TEST_SECONDS + 10)
        except (OSError, subprocess.TimeoutExpired) as e:
            debug.warning(f"Test sound: {command[0]} failed: {e}")
            return False, f"{command[0]} failed: {e}"
    if done.returncode:  # like "Device or resource busy" while a show is playing
        problem = (done.stderr or "").strip().splitlines()[-1:] or [f"exited {done.returncode}"]
        debug.warning(f"Test sound: {command[0]} said {problem[0]}")
        return False, f"{command[0]} said {problem[0]}"
    what = "the start of the fireworks music" if os.path.basename(clip) != "chime.wav" else "a chime"
    if not volume_set:
        return True, f"Played {what} at the speaker's own level: the volume couldn't be set."
    return True, f"Played {what} at {settings.volume}%."


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
            set_volume(settings._replace(volume=saved_volume(settings.volume)))
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


# ---- What's keeping the show silent, for the badges in display/sound_badges.py ----

NO_MUSIC = "no music"  # sound is on, but a show has no clip in sounds/
CANT_PLAY = "can't play"  # no player, or no sound card for the configured device
CHECK_EVERY_S = 60

_CARD_LINE = re.compile(r"^\s*(\d+)\s+\[\s*([^\]\s]+)\s*\]")


def show_clips(show):
    """The clips a show plays, in order of preference: its own, then the generic fireworks music."""
    return [clip_name(show), "fireworks"]


def card_present(device, cards_file=CARDS_FILE):
    """True if ALSA lists the card device names ("plughw:1,0", "hw:CARD=Device,DEV=0"), or any
    card for the default device (None, "default", or one naming no card)."""
    try:
        with open(cards_file) as f:
            cards = [m.groups() for m in map(_CARD_LINE.match, f) if m]
    except OSError:
        return False
    card = _card(device)
    if not card:
        return bool(cards)
    return any(card in (index, name) for index, name in cards)


def _card(device):
    """The card an ALSA device names, by index or name ("plughw:1,0" -> "1",
    "hw:CARD=Device,DEV=0" -> "Device"), or "" for the default."""
    card = device.partition(":")[2].split(",")[0] if device else ""
    return card[len("CARD="):] if card.startswith("CARD=") else card


def problem(settings, shows, sounds_dir=None, platform=sys.platform, cards_file=CARDS_FILE):
    """CANT_PLAY, NO_MUSIC or None, without playing anything. shows is a list of show_clips lists.
    Quiet hours don't count: the badge is there to get it fixed before the show."""
    if not settings.enabled:
        return None
    player = player_command("", settings.device, platform)[0]
    if shutil.which(player) is None or (platform != "darwin" and not card_present(settings.device, cards_file)):
        return CANT_PLAY
    if any(find_clip(names, sounds_dir) is None for names in shows):
        return NO_MUSIC
    return None


_watched = None  # (settings, shows), from watch()
_found = None
_checked_at = None


def watch(settings, shows):
    """Check settings and shows for current_problem() from now on; the app calls it once at start-up."""
    global _watched, _found, _checked_at
    _watched, _found, _checked_at = (settings, shows), None, None


def current_problem(clock=time.monotonic):
    """The watched problem, rechecked at most every CHECK_EVERY_S: it's asked every frame. Logged
    when it changes, so a fix (a clip copied in, the sound card plugged back) clears it."""
    global _found, _checked_at
    if _watched is None:
        return None
    now = clock()
    if _checked_at is None or now - _checked_at >= CHECK_EVERY_S:
        _checked_at = now
        settings, shows = _watched
        found = problem(settings, shows)
        if found != _found:
            if found == CANT_PLAY:
                debug.warning("Sound is on but can't play: no player installed or no sound card for "
                              f"{settings.device or 'the default device'}. Showing the speaker badge.")
            elif found == NO_MUSIC:
                missing = [names[0] for names in shows if find_clip(names) is None]
                debug.warning(f"Sound is on but {SOUNDS_DIR}/ has no music for {', '.join(missing)} "
                              f"(nor {shows[0][-1]}.wav). Showing the music badge.")
            else:
                debug.info("Sound problem fixed; badge off.")
            _found = found
    return _found
