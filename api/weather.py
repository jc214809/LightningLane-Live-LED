import random
import time

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

_last_good = {}  # (lat, lon) -> (weather dict, monotonic time fetched)
_paused_until = 0.0
_rejected = None  # {"key", "until", "wait"} while the key is being refused


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
        "temperature": str(int(weather_data.temperature('fahrenheit')["temp"])) + "°",
        "description": weather_data.detailed_status,
        "short_description": "T-Storm" if "thunderstorm" in weather_data.status.lower() else weather_data.status,
        "city": observation.location.name,
        "icon": weather_data.weather_icon_name  # Icon code
    }


def _key_rejected(api_key, now):
    global _rejected
    wait = KEY_RECHECK_S if _rejected is None else min(_rejected["wait"] * 2, KEY_RECHECK_MAX_S)
    if _rejected is None:
        debug.warning(f"[WEATHER] OpenWeatherMap rejected the API key (401); checking it again in {wait // 60} min. Check config.json.")
    else:
        debug.log(f"[WEATHER] API key still rejected; next check in {wait // 60} min.")
    _rejected = {"key": api_key, "until": now + wait, "wait": wait}


def fetch_weather_data(lat, lon):
    """Current weather at lat/lon, or the last good reading if this fetch fails.

    Never raises: every failure is logged and falls back, so one park's weather
    can't abort the live-data cycle that calls this. Returns None only when
    there's no reading under STALE_S old.
    """
    global _paused_until, _rejected
    now = time.monotonic()
    location = (lat, lon)
    cached = _last_good.get(location)
    if cached and now - cached[1] < CACHE_S:
        return cached[0]

    try:
        api_key = weather_api_key(load_config())
    except (OSError, ValueError, AttributeError) as e:
        debug.warning(f"[WEATHER] Couldn't read the API key from config.json: {e}")
        return _fallback(location, now)
    if not api_key:
        debug.log("[WEATHER] No API key in config.json; skipping weather.")
        return _fallback(location, now)

    if _rejected is not None:
        if api_key != _rejected["key"]:
            debug.info("[WEATHER] API key changed in config.json; trying it now.")
            _rejected = None
        elif now < _rejected["until"]:
            return _fallback(location, now)
    if now < _paused_until:
        return _fallback(location, now)

    for attempt in range(RETRIES + 1):
        try:
            weather = _call_api(api_key, lat, lon)
        except pyowm.commons.exceptions.UnauthorizedError:
            _key_rejected(api_key, time.monotonic())
            return _fallback(location, now)
        except pyowm.commons.exceptions.NotFoundError as e:
            debug.warning(f"[WEATHER] No weather for lat:{lat} lon:{lon} (404): {_redact(str(e), api_key)}")
            return _fallback(location, now)
        except (pyowm.commons.exceptions.PyOWMError, requests.RequestException, KeyError, TypeError, ValueError, AttributeError) as e:
            reason = f"{type(e).__name__}: {_redact(str(e), api_key)}"
            if "429" in str(e):
                debug.warning(f"[WEATHER] Rate limited (429); pausing weather for {PAUSE_S}s.")
                _paused_until = time.monotonic() + PAUSE_S
                return _fallback(location, now)
            if attempt < RETRIES:
                delay = BACKOFF_S * 2 ** attempt + random.uniform(0, BACKOFF_S)
                debug.log(f"[WEATHER] Fetch failed ({reason}); retrying in {delay:.1f}s.")
                time.sleep(delay)
                continue
            debug.warning(f"[WEATHER] Fetch failed after {RETRIES + 1} tries ({reason}); "
                          f"keeping the last reading and pausing weather for {PAUSE_S}s.")
            _paused_until = time.monotonic() + PAUSE_S
            return _fallback(location, now)
        if _rejected is not None:
            debug.info("[WEATHER] OpenWeatherMap accepted the API key again.")
            _rejected = None
        _last_good[location] = (weather, time.monotonic())
        return weather
