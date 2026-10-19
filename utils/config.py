"""
config.json: one loader, and the settings with defaults or fallbacks worth keeping in one
place. Read on demand, not cached: weather re-reads it each fetch so a new key takes effect
without a restart. Feature-specific sections (trip_countdown, force_surprise) are read by
the code that validates them (utils/trips.py, disney.py).
"""
import json
from datetime import time
from typing import NamedTuple, Optional, Tuple

from utils import debug

# Relative to the working directory, so run the app from the repo root.
CONFIG_FILE = "config.json"


def load_config(file_path=CONFIG_FILE):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)


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


def show_settings(config):
    """config.json's "shows": a list of {"name", "enabled", "version"}, one per fireworks show (all but
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
        shows[name] = ShowSettings(enabled, version)
    return shows


class SoundSettings(NamedTuple):
    enabled: bool = False
    device: Optional[str] = None  # aplay -D on a Pi; None is ALSA's default card
    quiet_hours: Optional[Tuple[time, time]] = None  # (start, end) in the board's local time


def sound_settings(config):
    """config.json's "sound" section: {"enabled": true, "device": null,
    "quiet_hours": {"start": "22:00", "end": "08:00"}}. Without the section the board stays silent.
    A bad quiet_hours turns sound off rather than risk playing in the night."""
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

    quiet = section.get("quiet_hours")
    quiet_hours = None
    if quiet is not None:
        try:
            quiet_hours = (time.fromisoformat(quiet["start"]), time.fromisoformat(quiet["end"]))
        except (TypeError, KeyError, ValueError):
            debug.warning(f'config.json "sound.quiet_hours" should be {{"start": "22:00", "end": "08:00"}}, '
                          f'not {quiet!r}; sound is off.')
            return SoundSettings()
    return SoundSettings(enabled, device, quiet_hours)
