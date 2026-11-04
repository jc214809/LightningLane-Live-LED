"""The app's heartbeat, for the updater (self_update): HEARTBEAT_FILE holds JSON with when the app
last finished a screen ("at", epoch seconds), its pid and version, and, while a fireworks show is
playing, the show and when it ends ("show", "show_until").

systemd's Restart=always hides a crash loop, so an update counts as healthy only once the new app
has written a heartbeat since it was restarted. The updater also won't start while a show plays.
/run is cleared at boot, so a heartbeat never outlives the app's run. Written atomically (a temp
file renamed over it) and never raises: a board that can't write it only fails its health check.
"""
import json
import os
import time

from utils import debug
from version import SCRIPT_VERSION

HEARTBEAT_FILE = "/run/lll-health"

_last_problem = None


def beat(show=None, show_s=0, path=None, clock=time.time):
    """Say the app is alive now; with show, that it's playing that show for the next show_s seconds."""
    global _last_problem
    path = path or HEARTBEAT_FILE
    now = clock()
    beat_data = {"at": now, "pid": os.getpid(), "version": SCRIPT_VERSION}
    if show:
        beat_data.update(show=show, show_until=now + max(0, show_s))
    temp = f"{path}.{os.getpid()}.new"
    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(beat_data, f)
        os.replace(temp, path)
    except OSError as e:
        problem = f"Can't write the heartbeat {path}: {e}"
        if problem != _last_problem:  # written every screen: say it once
            debug.warning(problem)
        _last_problem = problem
        return False
    _last_problem = None
    return True


def read(path=None):
    """The last heartbeat as a dict, or None (none yet, or unreadable)."""
    try:
        with open(path or HEARTBEAT_FILE, encoding="utf-8") as f:
            found = json.load(f)
    except (OSError, ValueError):
        return None
    return found if isinstance(found, dict) and isinstance(found.get("at"), (int, float)) else None


def show_playing(heartbeat, now):
    """The show the heartbeat says is playing now, or None. A show's end is written when it starts,
    so an app that died mid-show doesn't block updates past it."""
    if not heartbeat or not heartbeat.get("show"):
        return None
    until = heartbeat.get("show_until")
    return heartbeat["show"] if isinstance(until, (int, float)) and now < until else None
