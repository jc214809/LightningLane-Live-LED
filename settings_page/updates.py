"""The Updates card's side of the settings page (ROADMAP #17): what's installed and how the last
update went (self_update's state.json and outcome.json), a check for a newer version (a dry run,
in this process: it changes nothing but a git fetch) with what's in it (the pull requests merged
since what's installed), and starting an update or a rollback.

An update restarts this service, so it runs as its own transient unit (systemd-run
--unit=lll-update), which also means only one runs at a time: systemd refuses a second.
"""
import os
import re
import subprocess
import sys
import threading
import time

from self_update import state as states
from self_update.board import Board, CommandFailed
from self_update.update import BLOCKED, CHANNELS, RELEASES, WOULD_UPDATE, Updater
from utils import debug

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPDATE_UNIT = "lll-update"
START_TIMEOUT_S = 30
# A check older than this is dropped: what's newest may have moved on.
CHECK_FRESH_S = 10 * 60
# What a running update is doing, by state.json's phase (before its rollback point, it's checking).
PHASE_TEXT = {states.READY: "Saving a rollback point", states.SWITCHED: "Installing the new version",
              states.INSTALLED: "Restarting the board", states.CHECKING: "Checking the new version works",
              states.ROLLING_BACK: "Rolling back"}
CHECKING_TEXT = "Checking it can update"
# start()'s outcomes, which the page says after the redirect.
STARTED, BUSY, START_FAILED = "started", "busy", "failed"
STARTS = (STARTED, BUSY, START_FAILED)


class Updates:
    def __init__(self, app_dir=APP_DIR, updater=None, run=subprocess.run, python=sys.executable, clock=time.time):
        self.app_dir, self._updater, self.run, self.python, self.clock = app_dir, updater, run, python, clock
        # {"channel", "result", "message", "ok", "at"}, and when it found one, details()'s keys
        self.last_check = None
        self.starting = None  # the check whose update was started, for what the card says while it runs
        self._check_lock = threading.Lock()

    @property
    def updater(self):
        if self._updater is None:  # built on first use: it reads version.py and the checkout
            self._updater = Updater(Board(self.app_dir))
        return self._updater

    def running(self):
        """Whether an update or rollback is running now (its unit is active)."""
        try:
            return self.updater.board.active(f"{UPDATE_UNIT}.service")
        except CommandFailed:  # no systemctl: nothing can be running
            return False

    def status(self):
        """For the page's script while one runs: {"running", "phase"} (what it's doing, in words)."""
        running = self.running()
        phase = self.updater.state.load()["phase"]
        return {"running": running, "phase": PHASE_TEXT.get(phase, CHECKING_TEXT) if running else None}

    def view(self):
        """What the card shows (page.updates_card)."""
        updater = self.updater
        try:
            sha, branch = updater.board.head(), updater.board.branch()
        except CommandFailed as e:
            debug.warning(f"Settings page: can't read the checkout's commit: {e}")
            sha, branch = None, None
        record = updater.state.load()
        check = self.last_check
        if check and self.clock() - check["at"] > CHECK_FRESH_S:
            check = self.last_check = None
        running = self.running()
        # What's being installed: state.json's once the update has its rollback point (it survives
        # this page's restart), else what was started.
        to = record.get("to") if record["phase"] in states.UNFINISHED and isinstance(record.get("to"), dict) \
            else self.starting
        if running and to and self.starting and self.starting.get("sha") == to.get("sha"):
            to = {**self.starting, **to}
        return {"version": updater.installed_version, "sha": sha, "branch": branch, "running": running,
                "to": to if running else None,
                "phase": record["phase"], "status": PHASE_TEXT.get(record["phase"], CHECKING_TEXT) if running else None,
                "from": record.get("from") if isinstance(record.get("from"), dict) else None,
                "outcome": updater.state.load_outcome(), "check": check,
                "channel": (check or {}).get("channel") or (record.get("to") or {}).get("channel") or RELEASES}

    def check(self, channel):
        """The Check button: what an update on channel would do, kept in last_check. Changes nothing."""
        if channel not in CHANNELS:
            return
        if self.running():
            result, message, ok, found = BLOCKED, "an update or rollback is running", False, {}
        else:
            with self._check_lock:  # two at once would fetch at once
                try:
                    outcome = self.updater.update(channel, dry_run=True)
                    result, message, ok = outcome.result, outcome.message, outcome.ok
                    found = self.details(outcome.target) if result == WOULD_UPDATE and outcome.target else {}
                except (CommandFailed, OSError) as e:
                    result, message, ok, found = BLOCKED, str(e), False, {}
        debug.info(f"Settings page: checked for updates on {channel}: {result}: {message}")
        self.last_check = {"channel": channel, "result": result, "message": message, "ok": ok, "at": self.clock(),
                           **found}

    def details(self, target):
        """What an update to target brings: {"ref", "sha", "version" (its version.py's, or None),
        "changes" ([PR number or None, title], newest first), "packages" (whether requirements.txt
        changes: pip runs, which takes ages on a Pi Zero)}. Only ref and sha if git can't say."""
        found = {"ref": target.ref, "sha": target.sha}
        board = self.updater.board
        try:
            head = board.head()
            version = re.search(r'SCRIPT_VERSION\s*=\s*"([^"]+)"', board.file_at(target.sha, "version.py") or "")
            found.update(version=version.group(1) if version else None,
                         changes=[list(change) for change in board.what_changed(head, target.sha)],
                         packages=board.changed(head, target.sha, "requirements.txt"))
        except CommandFailed as e:
            debug.warning(f"Settings page: can't list what's in {target.ref}: {e}")
        return found

    def start(self, command, channel=None):
        """Start python3 -m self_update update --channel channel, or rollback, as its own unit.
        STARTED, BUSY (one is running already) or START_FAILED (logged)."""
        args = ["systemd-run", f"--unit={UPDATE_UNIT}", "--collect", f"--working-directory={self.app_dir}",
                "--description=LightningLane-Live-LED update", self.python, "-m", "self_update", command]
        if command == "update":
            if channel not in CHANNELS:
                return START_FAILED
            args += ["--channel", channel]
        if self.running():
            return BUSY
        try:
            done = self.run(args, capture_output=True, text=True, timeout=START_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as e:
            debug.error(f"Settings page: can't start the {command}: {e}")
            return START_FAILED
        if done.returncode:
            problem = (done.stderr or "").strip() or f"systemd-run exited {done.returncode}"
            if "already" in problem:  # "Unit lll-update.service was already loaded" / "already exists"
                return BUSY
            debug.error(f"Settings page: can't start the {command}: {problem}")
            return START_FAILED
        self.starting = self.last_check if command == "update" and self.last_check \
            and self.last_check.get("channel") == channel and self.last_check.get("sha") else None
        debug.info(f"Settings page: started the {command}" + (f" on {channel}" if channel else "")
                   + f" ({UPDATE_UNIT}.service; journalctl -u {UPDATE_UNIT} has how it goes).")
        self.last_check = None
        return STARTED
