"""Whether the board is in comitup's Wi-Fi setup hotspot, and the hotspot's name.

board-setup.sh installs comitup with a callback that writes "<STATE> <hotspot name>" to
STATE_FILE on each change of state: HOTSPOT (no known network in range, so the setup hotspot is
up), CONNECTING or CONNECTED. /run is cleared at boot, so the file never outlives comitup's run.
"""
from utils import debug

STATE_FILE = "/run/comitup-state"

_last_problem = None


def hotspot_name(path=STATE_FILE):
    """The setup hotspot's name while it's up, else None (also with no comitup, or a bad file)."""
    global _last_problem
    try:
        with open(path, encoding="utf-8") as f:
            state, _, name = f.read().strip().partition(" ")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as e:
        problem = f"Can't read {path}: {e}"
        if problem != _last_problem:  # polled every few seconds: say it once
            debug.warning(problem)
            _last_problem = problem
        return None
    _last_problem = None
    if state != "HOTSPOT":
        return None
    return name.strip() or None
