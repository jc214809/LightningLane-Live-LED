"""
config.json: one loader, and the settings with defaults or fallbacks worth keeping in one
place. Read on demand, not cached: weather re-reads it each fetch so a new key takes effect
without a restart. Feature-specific sections (trip_countdown, force_surprise) are read by
the code that validates them (utils/trips.py, disney.py).
"""
import json
import os
import shutil
from datetime import time
from typing import NamedTuple, Optional, Tuple

from utils import debug

# Relative to the working directory, so run the app from the repo root.
CONFIG_FILE = "config.json"


def load_config(file_path=CONFIG_FILE):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def save_config(config, path=CONFIG_FILE):
    """Write config.json whole or not at all, keeping the last one as config.json.bak, with the
    old file's owner and mode (the user's, 600, as board-setup.sh made it), even when run as root."""
    temp = path + ".new"
    try:
        old = os.stat(path)
    except FileNotFoundError:
        old = None
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, old.st_mode & 0o777 if old else 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    if old:
        try:
            os.chown(temp, old.st_uid, old.st_gid)
        except PermissionError:  # not root (a dev machine): it's ours already
            pass
        shutil.copy2(path, path + ".bak")
    os.replace(temp, path)


def debug_enabled(config):
    """config.json's "debug": true logs at DEBUG level; missing means INFO."""
    return bool(config.get("debug"))


def weather_api_key(config):
    """config.json's "weather": {"apikey": ...}, or None."""
    section = config.get("weather")
    return section.get("apikey") if isinstance(section, dict) else None


def has_api_key(api_key):
    """True for a real ThemeParks key. The WebSocket needs one: without it the
    server accepts the handshake, then closes with 3000 "Authentication timeout"."""
    return isinstance(api_key, str) and bool(api_key.strip()) and not api_key.startswith("<")


def websocket_settings(config):
    """(use_websocket, api_key) from config.json's "websocket" section:
    {"enabled": true, "api_key": "..."}. Runs only when enabled with a real key.
    A config without the section falls back to the old top-level themeparks_api_key."""
    section = config.get("websocket")
    if section is None:
        api_key = config.get("themeparks_api_key")
        if has_api_key(api_key):
            debug.info('Using the top-level "themeparks_api_key"; move it to "websocket": {"api_key": ...} in config.json.')
        return has_api_key(api_key), api_key
    if not isinstance(section, dict):
        debug.warning('config.json "websocket" should be {"enabled": true, "api_key": "..."}; using REST polling only.')
        return False, None

    enabled = section.get("enabled", True)
    api_key = section.get("api_key")
    if not isinstance(enabled, bool):
        debug.warning(f'config.json "websocket.enabled" should be true or false, not {enabled!r}; using REST polling only.')
        return False, api_key
    if not enabled:
        return False, api_key
    if not has_api_key(api_key):
        debug.warning('config.json "websocket.enabled" is true but "websocket.api_key" is not set; using REST polling only.')
        return False, api_key
    return True, api_key


WS_PROTOCOLS = ("legacy", "preview")


def websocket_protocol(config):
    """config.json's "websocket.protocol": "legacy" (the default) or "preview"."""
    section = config.get("websocket")
    protocol = section.get("protocol", "legacy") if isinstance(section, dict) else "legacy"
    if protocol not in WS_PROTOCOLS:
        debug.warning(f'config.json "websocket.protocol" should be "legacy" or "preview", not {protocol!r}; using "legacy".')
        return "legacy"
    return protocol


SHOW_VERSIONS = ("default", "v1", "v2")


class ShowSettings(NamedTuple):
    enabled: bool = True
    # "default": the castle fireworks for five minutes; "v1" or "v2": a scored show's whole synced version
    version: str = "default"
    force: bool = False  # play it once at start-up whatever the schedule, for checking it on a board


def show_settings(config):
    """config.json's "shows": a list of {"name", "enabled", "version", "force"}, one per fireworks show (all but
    name optional), as {name: ShowSettings}. A show not listed is enabled and "default". A bad field is
    warned about and takes its default."""
    section = config.get("shows")
    if section is None:
        return {}
    if not isinstance(section, list):
        debug.warning('config.json "shows" should be a list of {"name": ..., "enabled": ..., "version": ...}; '
                      'ignoring it.')
        return {}
    shows = {}
    for entry in section:
        name = entry.get("name") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not name.strip():
            debug.warning(f'config.json "shows": skipping {entry!r}, which has no "name".')
            continue
        enabled = entry.get("enabled", True)
        if not isinstance(enabled, bool):
            debug.warning(f'config.json "shows": {name!r} "enabled" should be true or false, not {enabled!r}; using true.')
            enabled = True
        version = entry.get("version", "default")
        if version not in SHOW_VERSIONS:
            debug.warning(f'config.json "shows": {name!r} "version" should be "default", "v1" or "v2", '
                          f'not {version!r}; using "default".')
            version = "default"
        force = entry.get("force", False)
        if not isinstance(force, bool):
            debug.warning(f'config.json "shows": {name!r} "force" should be true or false, not {force!r}; using false.')
            force = False
        shows[name] = ShowSettings(enabled, version, force)
    return shows


def forced_show_name(config):
    """The show to play once at start-up, for checking it on a board: the first "shows" entry with
    "force": true, else the old top-level "force_show" (still read, with a warning), else None."""
    forced = [name for name, show in show_settings(config).items() if show.force]
    if len(forced) > 1:
        debug.warning(f'config.json "shows": more than one show has "force": true; playing {forced[0]!r} only.')
    if forced:
        return forced[0]
    legacy = config.get("force_show")
    if legacy:
        debug.warning(f'config.json "force_show" has moved: set "force": true on its entry in "shows" '
                      f'(like {{"name": {legacy!r}, "force": true}}). Playing {legacy!r} for now.')
        return legacy
    return None


# A USB speaker draws on the Pi's 5V rail; near full volume it under-volted Disneypi (a Pi 4), 80% didn't.
DEFAULT_VOLUME = 80


class SoundSettings(NamedTuple):
    enabled: bool = False
    device: Optional[str] = None  # aplay -D on a Pi; None is ALSA's default card
    quiet_hours: Optional[Tuple[time, time]] = None  # (start, end) in the board's local time
    volume: int = DEFAULT_VOLUME  # percent, set with amixer before each clip


def sound_settings(config):
    """config.json's "sound" section: {"enabled": true, "device": null, "volume": 80,
    "quiet_hours": {"start": "22:00", "end": "08:00"}}. Without the section the board stays silent.
    A bad quiet_hours turns sound off rather than risk playing in the night; a bad volume is 80."""
    section = config.get("sound")
    if section is None:
        return SoundSettings()
    if not isinstance(section, dict):
        debug.warning('config.json "sound" should be {"enabled": true, ...}; sound is off.')
        return SoundSettings()

    enabled = section.get("enabled", True)
    if not isinstance(enabled, bool):
        debug.warning(f'config.json "sound.enabled" should be true or false, not {enabled!r}; sound is off.')
        return SoundSettings()
    device = section.get("device")
    if device is not None and not (isinstance(device, str) and device.strip()):
        debug.warning(f'config.json "sound.device" should be an ALSA device like "plughw:1,0", not {device!r}; '
                      'using the default.')
        device = None

    volume = section.get("volume")
    if volume is None:
        volume = DEFAULT_VOLUME
    elif isinstance(volume, bool) or not isinstance(volume, int) or not 0 <= volume <= 100:
        debug.warning(f'config.json "sound.volume" should be 0 to 100, not {volume!r}; using {DEFAULT_VOLUME}.')
        volume = DEFAULT_VOLUME

    quiet = section.get("quiet_hours")
    quiet_hours = None
    if quiet is not None:
        try:
            quiet_hours = (time.fromisoformat(quiet["start"]), time.fromisoformat(quiet["end"]))
        except (TypeError, KeyError, ValueError):
            debug.warning(f'config.json "sound.quiet_hours" should be {{"start": "22:00", "end": "08:00"}}, '
                          f'not {quiet!r}; sound is off.')
            return SoundSettings()
    return SoundSettings(enabled, device, quiet_hours, volume)


class BrightnessSchedule(NamedTuple):
    day: int  # 1 to 100, as --led-brightness
    night: int
    day_start: time  # the board's local time
    night_start: time


BRIGHTNESS_SCHEDULE_KEYS = {"day", "night", "day_start", "night_start"}


def parse_brightness_schedule(section):
    """(BrightnessSchedule or None, what's wrong or None) for config.json's "brightness_schedule", shaped
    as Peloton-LED's: null for one brightness all day, else
    {"day": 80, "night": 15, "day_start": "07:00", "night_start": "22:00"}."""
    if section is None:
        return None, None
    if not isinstance(section, dict) or set(section) != BRIGHTNESS_SCHEDULE_KEYS:
        return None, "needs day, night, day_start and night_start"
    for key in ("day", "night"):
        value = section[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            return None, f'"{key}" should be 1 to 100, not {value!r}'
    starts = []
    for key in ("day_start", "night_start"):
        try:
            starts.append(time.fromisoformat(section[key]))
        except (TypeError, ValueError):
            return None, f'"{key}" should be a time like "07:00", not {section[key]!r}'
    return BrightnessSchedule(section["day"], section["night"], *starts), None


def brightness_schedule(config):
    """config.json's "brightness_schedule" (see parse_brightness_schedule), or None. A bad one is warned
    about and leaves the board at one brightness all day."""
    schedule, problem = parse_brightness_schedule(config.get("brightness_schedule"))
    if problem:
        debug.warning(f'config.json "brightness_schedule" {problem}; keeping one brightness all day.')
    return schedule
