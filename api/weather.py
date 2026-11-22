import random
import time
from typing import Any

import pyowm
import requests

from utils import debug
from utils.config import load_config, weather_api_key

# Retries within one fetch, for errors that usually clear in seconds (timeouts,
# dropped connections, 5xx). The 5-minute update cycle is the long retry.
RETRIES = 2
BACKOFF_S = 1.0
# After a fetch fails every attempt, or OpenWeatherMap says 429, the rest of the
# parks skip until this has passed, so an outage costs one park's retries a cycle.
PAUSE_S = 60
# A rejected key (401) is rechecked with one real call after this, doubling on
# every further 401 up to the cap. A different key in config.json skips the wait.
KEY_RECHECK_S = 300
KEY_RECHECK_MAX_S = 3600
# OpenWeatherMap's data changes every 10 minutes at most, so a fresher reading
# is reused; a failed fetch keeps showing the last good one for up to an hour.
CACHE_S = 600
STALE_S = 3600

_last_good: dict[tuple, tuple] = {}  # (lat, lon) -> (weather dict, monotonic time fetched)
_paused_until = 0.0
_rejected: dict[str, Any] | None = None  # {"key", "until", "wait"} while the key is being refused


def _reset():
    """Forget every reading and back-off; for tests."""
    global _paused_until, _rejected
    _last_good.clear()
    _paused_until = 0.0
    _rejected = None


def _redact(message, api_key):
    # pyowm puts the key in the request URL, so it turns up in every error.
    return message.replace(api_key, "***") if api_key else message


def _fallback(location, now):
    """The last good reading for this location, unless it's over STALE_S old."""
    cached = _last_good.get(location)
    if cached and now - cached[1] < STALE_S:
        return cached[0]
    return None


def _call_api(api_key, lat, lon):
    observation = pyowm.OWM(api_key).weather_manager().weather_at_coords(lat, lon)
    weather_data = observation.weather
    debug.log(f"Weather Data for {observation.location.name}: {weather_data}")
    return {
        "temperature": str(int(weather_data.temperature("fahrenheit")["temp"])) + "°",
        "description": weather_data.detailed_status,
        "short_description": "T-Storm" if "thunderstorm" in weather_data.status.lower() else weather_data.status,
        "city": observation.location.name,
        "icon": weather_data.weather_icon_name,  # Icon code
    }


def _key_rejected(api_key, now):
    global _rejected
    wait = KEY_RECHECK_S if _rejected is None else min(_rejected["wait"] * 2, KEY_RECHECK_MAX_S)
    if _rejected is None:
        debug.warning(
            f"[WEATHER] OpenWeatherMap rejected the API key (401); checking it again in {wait // 60} min. Check config.json."
        )
    else:
        debug.log(f"[WEATHER] API key still rejected; next check in {wait // 60} min.")
    _rejected = {"key": api_key, "until": now + wait, "wait": wait}


def _read_api_key():
    """The key from config.json, or None (logged) when it can't be read or isn't set."""
    try:
        api_key = weather_api_key(load_config())
    except (OSError, ValueError, AttributeError) as e:
        debug.warning(f"[WEATHER] Couldn't read the API key from config.json: {e}")
        return None
    if not api_key:
        debug.log("[WEATHER] No API key in config.json; skipping weather.")
        return None
    return api_key


def _backing_off(api_key, now):
    """True while a rejected key or a pause says not to call the API yet."""
    global _rejected
    if _rejected is not None:
        if api_key != _rejected["key"]:
            debug.info("[WEATHER] API key changed in config.json; trying it now.")
            _rejected = None
        elif now < _rejected["until"]:
            return True
    return now < _paused_until


def _pause():
    global _paused_until
    _paused_until = time.monotonic() + PAUSE_S


def _should_retry(error, api_key, attempt):
    """Log a failed attempt; True to try again (after the backoff sleep), False to give up."""
    reason = f"{type(error).__name__}: {_redact(str(error), api_key)}"
    if "429" in str(error):
        debug.warning(f"[WEATHER] Rate limited (429); pausing weather for {PAUSE_S}s.")
        _pause()
        return False
    if attempt < RETRIES:
        delay = BACKOFF_S * 2**attempt + random.uniform(0, BACKOFF_S)
        debug.log(f"[WEATHER] Fetch failed ({reason}); retrying in {delay:.1f}s.")
        time.sleep(delay)
        return True
    debug.warning(
        f"[WEATHER] Fetch failed after {RETRIES + 1} tries ({reason}); "
        f"keeping the last reading and pausing weather for {PAUSE_S}s."
    )
    _pause()
    return False


def _fetch_with_retries(api_key, lat, lon):
    """One reading from the API, retrying transient errors; None when it gives up (logged)."""
    global _rejected
    attempt = 0
    while True:
        try:
            weather = _call_api(api_key, lat, lon)
        except pyowm.commons.exceptions.UnauthorizedError:
            _key_rejected(api_key, time.monotonic())
            return None
        except pyowm.commons.exceptions.NotFoundError as e:
            debug.warning(f"[WEATHER] No weather for lat:{lat} lon:{lon} (404): {_redact(str(e), api_key)}")
            return None
        except (
            pyowm.commons.exceptions.PyOWMError,
            requests.RequestException,
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
        ) as e:
            if not _should_retry(e, api_key, attempt):
                return None
            attempt += 1
            continue
        if _rejected is not None:
            debug.info("[WEATHER] OpenWeatherMap accepted the API key again.")
            _rejected = None
        return weather


def fetch_weather_data(lat, lon):
    """Current weather at lat/lon, or the last good reading if this fetch fails.

    Never raises: every failure is logged and falls back, so one park's weather
    can't abort the live-data cycle that calls this. Returns None only when
    there's no reading under STALE_S old.
    """
    now = time.monotonic()
    location = (lat, lon)
    cached = _last_good.get(location)
    if cached and now - cached[1] < CACHE_S:
        return cached[0]

    api_key = _read_api_key()
    if api_key is None or _backing_off(api_key, now):
        return _fallback(location, now)

    weather = _fetch_with_retries(api_key, lat, lon)
    if weather is None:
        return _fallback(location, now)
    _last_good[location] = (weather, time.monotonic())
    return weather
