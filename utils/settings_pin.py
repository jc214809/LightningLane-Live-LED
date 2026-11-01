"""The settings page's PIN, while it's on the board: the settings server (settings_page/pins.py)
writes "<PIN> <expiry, epoch seconds>" to PIN_FILE when someone on the home network asks for one,
and removes it once it's used. Asked every frame, so the file is read at most every CHECK_EVERY_S.
"""
import time

from settings_page.pins import PIN_FILE
from utils import debug

CHECK_EVERY_S = 1.0

_cache = {"at": None, "pin": None, "expires": 0.0}
_last_problem = None


def shown_pin(path=None, clock=time.time, monotonic=time.monotonic):
    """The PIN to show now, or None."""
    now = monotonic()
    if _cache["at"] is None or now - _cache["at"] >= CHECK_EVERY_S:
        _cache.update(at=now, **_read(path or PIN_FILE))
    return _cache["pin"] if _cache["pin"] and clock() < _cache["expires"] else None


def _read(path):
    global _last_problem
    try:
        with open(path, encoding="utf-8") as f:
            pin, expires = f.read().split()
        found = {"pin": pin if pin.isdigit() else None, "expires": float(expires)}
    except FileNotFoundError:
        found = {"pin": None, "expires": 0.0}
    except (OSError, ValueError, UnicodeDecodeError) as e:
        problem = f"Can't read the settings PIN from {path}: {e}"
        if problem != _last_problem:  # asked every frame: say it once
            debug.warning(problem)
        _last_problem = problem
        return {"pin": None, "expires": 0.0}
    _last_problem = None
    return found
