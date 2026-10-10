"""
config.json: one loader, and the settings with defaults or fallbacks worth keeping in one
place. Read on demand, not cached: weather re-reads it each fetch so a new key takes effect
without a restart. Feature-specific sections (trip_countdown, force_surprise) are read by
the code that validates them (utils/trips.py, disney.py).
"""
import json

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
