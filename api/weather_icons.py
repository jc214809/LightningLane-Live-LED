"""OpenWeatherMap weather icons, downloaded by the REST thread and shown by the park screen.

The display never fetches (see the import-linter contract): the REST thread calls
`fetch_icon` after each weather reading and publishes the image in
`updater.shared.weather_icons`, which the park screen reads.
"""

import time
from io import BytesIO

import requests
from PIL import Image

from utils import debug

ICON_TIMEOUT_S = 5
ICON_RETRY_S = 300
ICON_SIZE = (15, 15)

_cache = {}  # icon code -> resized PIL image
_failures = {}  # icon code -> monotonic time of its last failed download


def _reset():
    """Forget every icon and back-off; for tests."""
    _cache.clear()
    _failures.clear()


def fetch_icon(icon_code):
    """The 15x15 image for an OpenWeatherMap icon code, or None if it can't be had.

    A cache hit makes no request. A failed download is logged and not retried for
    ICON_RETRY_S, so a bad code costs one request per window, not one per cycle.
    """
    if icon_code in _cache:
        return _cache[icon_code]
    failed_at = _failures.get(icon_code)
    if failed_at is not None and time.monotonic() - failed_at < ICON_RETRY_S:
        return None

    icon_url = f"https://openweathermap.org/img/wn/{icon_code}.png"
    try:
        response = requests.get(icon_url, timeout=ICON_TIMEOUT_S)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img = img.resize(ICON_SIZE)  # small enough for the matrix
        _cache[icon_code] = img
        _failures.pop(icon_code, None)
        debug.log(f"Downloaded weather icon {icon_code}")
        return img
    except requests.RequestException as e:
        debug.error(f"Failed to fetch icon from URL: {icon_url} - {e}")
    except Exception as e:
        debug.error(f"Failed to load icon: {e}")
    _failures[icon_code] = time.monotonic()
    return None
