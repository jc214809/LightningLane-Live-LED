"""The updater's state in STATE_DIR (root's, kept across reboots): state.json, the rollback point's
pip freeze and config.json copy, and a lock so two updates never run at once.

state.json: "phase" (below), "from" (the rollback point: "sha", "branch" (None when detached),
"version", "requirements_changed"), "to" (the update's "sha", "ref", "channel"), "reason" (why the
last one rolled back) and "good" (the last KEEP_GOOD commits that passed their health check,
newest first). A phase in UNFINISHED means an update stopped midway: a power cut, or a crash.
"""
import fcntl
import json
import os
from contextlib import contextmanager

STATE_DIR = "/var/lib/lll-update"
KEEP_GOOD = 3

IDLE, READY, SWITCHED, INSTALLED, CHECKING, ROLLING_BACK = \
    "idle", "ready", "switched", "installed", "checking", "rolling_back"
UPDATED, ROLLED_BACK, ROLLBACK_FAILED = "updated", "rolled_back", "rollback_failed"
UNFINISHED = (READY, SWITCHED, INSTALLED, CHECKING, ROLLING_BACK)


class Busy(Exception):
    """Another update or rollback holds the lock."""


class State:
    def __init__(self, folder=STATE_DIR):
        self.folder = folder
        self.path = os.path.join(folder, "state.json")
        self.freeze_path = os.path.join(folder, "pip-freeze.txt")
        self.config_path = os.path.join(folder, "config.json.before-update")

    def load(self):
        """state.json, or a fresh state when there isn't one (or it's unreadable: logged by the caller's
        outcome, since an unknown phase can't be rolled back anyway)."""
        try:
            with open(self.path, encoding="utf-8") as f:
                found = json.load(f)
        except (OSError, ValueError):
            found = None
        if not isinstance(found, dict):
            found = {}
        found.setdefault("phase", IDLE)
        if not isinstance(found.get("good"), list):
            found["good"] = []
        return found

    def save(self, state):
        """Write state.json whole or not at all, flushed to disk: it's what a power cut leaves."""
        os.makedirs(self.folder, mode=0o700, exist_ok=True)
        temp = self.path + ".new"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, self.path)

    def set_phase(self, state, phase, **changes):
        state.update(phase=phase, **changes)
        self.save(state)
        return state

    @contextmanager
    def lock(self):
        """Hold the update lock, or raise Busy. The kernel drops it if the process dies."""
        os.makedirs(self.folder, mode=0o700, exist_ok=True)
        with open(os.path.join(self.folder, "lock"), "w") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy("an update or rollback is already running") from None
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


def remember_good(state, sha):
    """Put sha first in the good commits, keeping KEEP_GOOD."""
    state["good"] = ([sha] + [s for s in state.get("good", []) if s != sha])[:KEEP_GOOD]
