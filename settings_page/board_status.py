"""The settings page's "On the board now" card: what the app's heartbeat (utils/heartbeat.py, /run/lll-health)
says. The app writes it after the intro and each screen (every park closed included) and while a show plays, so
its age says whether the app is up, without the settings page loading any of the app's own code.
"""
import time
from dataclasses import dataclass
from typing import Optional

from utils import heartbeat

# The updater's health window (self_update/update.py HEALTH_WINDOW_S): longer than this without a screen and
# the app has stopped or is stuck.
QUIET_S = 5 * 60

RUNNING, SHOW, QUIET, NONE = "running", "show", "quiet", "none"


@dataclass(frozen=True)
class BoardNow:
    state: str  # RUNNING, SHOW (a fireworks show is playing), QUIET (no screen for QUIET_S) or NONE (no heartbeat)
    age_s: Optional[float] = None  # since the last screen
    version: Optional[str] = None
    show: Optional[str] = None


def board_now(path=None, now=None):
    """The heartbeat as a BoardNow. Never raises: an unreadable or missing file is NONE."""
    now = time.time() if now is None else now
    beat = heartbeat.read(path)
    if beat is None:
        return BoardNow(NONE)
    age = max(0.0, now - beat["at"])
    version = beat.get("version") if isinstance(beat.get("version"), str) else None
    show = heartbeat.show_playing(beat, now)
    if show:
        return BoardNow(SHOW, age, version, str(show))
    return BoardNow(RUNNING if age <= QUIET_S else QUIET, age, version)


def ago(seconds):
    """'12 seconds ago', '1 minute ago', '3 hours ago'."""
    seconds = int(seconds)
    for size, unit in ((86400, "day"), (3600, "hour"), (60, "minute"), (1, "second")):
        if seconds >= size or size == 1:
            n = seconds // size
            return f"{n} {unit}{'' if n == 1 else 's'} ago"
