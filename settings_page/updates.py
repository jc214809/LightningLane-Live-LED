"""The Updates card's side of the settings page (ROADMAP #17): what's installed and how the last
update went (self_update's state.json and outcome.json), a check for a newer version (a dry run,
in this process: it changes nothing but a git fetch) with what's in it (the pull requests merged
since what's installed), and starting an update or a rollback. The page checks the channel of
what's installed by itself when it loads (auto_check), at most once per CHECK_FRESH_S: GitHub allows
60 calls an hour, and a check is two or three.

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
from self_update.update import BETA, BLOCKED, CHANNELS, RELEASES, WAITING, WOULD_UPDATE, Updater, parse_version
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
ROLLING_BACK_TEXT = "Rolling back"
# An update's steps, as the card lists them while one runs, and the step each phase is on.
STEPS = (CHECKING_TEXT, "Saving a rollback point", "Installing the new version", "Restarting and checking it works")
PHASE_STEP = {states.READY: 1, states.SWITCHED: 2, states.INSTALLED: 3, states.CHECKING: 3}
RELEASE_BRANCH = "main"
# start()'s outcomes, which the page says after the redirect.
STARTED, BUSY, START_FAILED = "started", "busy", "failed"
STARTS = (STARTED, BUSY, START_FAILED)


class Updates:
    def __init__(self, app_dir=APP_DIR, updater=None, run=subprocess.run, python=sys.executable, clock=time.time):
        self.app_dir, self._updater, self.run, self.python, self.clock = app_dir, updater, run, python, clock
        # {"channel", "result", "message", "ok", "at"}, and when it found one, details()'s keys; when
        # it's waiting on CI, "runs": [[name, github.RUNNING/PASSED/FAILED], ...]
        self.last_check = None
        self.starting = None  # the check whose update was started, for what the card says while it runs
        self.started = None  # what was started last, "update" or "rollback"
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
        """For the page's script while one runs: {"running", "phase" (what it's doing, in words),
        "step" (its index in STEPS, or None for a rollback, which has no steps)}."""
        running = self.running()
        phase = self.updater.state.load()["phase"]
        text, step = self._progress(phase) if running else (None, None)
        return {"running": running, "phase": text, "step": step}

    def _progress(self, phase):
        """(what a running update or rollback is doing, its step) from state.json's phase."""
        if phase == states.ROLLING_BACK or (phase not in states.UNFINISHED and self.started == "rollback"):
            return ROLLING_BACK_TEXT, None
        return PHASE_TEXT.get(phase, CHECKING_TEXT), PHASE_STEP.get(phase, 0)

    def installed_channel(self, sha, branch, record):
        """The channel what's installed came from: RELEASES on a release tag or the release branch,
        the channel of the update that installed it, else BETA (develop-beta, or a commit off it)."""
        to = record.get("to") if isinstance(record.get("to"), dict) else {}
        if not sha:
            return to.get("channel") if to.get("channel") in CHANNELS else RELEASES
        try:
            tagged = any(parse_version(tag) for tag in self.updater.board.tags_at(sha))
        except CommandFailed as e:
            debug.warning(f"Settings page: can't read the checkout's tags: {e}")
            tagged = False
        if tagged or branch == RELEASE_BRANCH:
            return RELEASES
        if to.get("sha") == sha and to.get("channel") in CHANNELS:
            return to["channel"]
        return BETA

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
        installed = self.installed_channel(sha, branch, record)
        status, step = self._progress(record["phase"]) if running else (None, None)
        return {"version": updater.installed_version, "sha": sha, "branch": branch, "running": running,
                "to": to if running else None, "phase": record["phase"], "status": status, "step": step,
                "from": record.get("from") if isinstance(record.get("from"), dict) else None,
                "outcome": updater.state.load_outcome(), "check": check, "installed_channel": installed,
                "channel": (check or {}).get("channel") or installed,
                # No check yet: the page's script asks for one (auto_check) once it's loaded.
                "auto_check": not check and not running}

    def auto_check(self, channel):
        """The page's own check when it loads: check(channel), unless one from the last CHECK_FRESH_S
        is kept (also one that finished while this waited for it)."""
        self.check(channel, reuse=True)

    def check(self, channel, reuse=False):
        """The Check button: what an update on channel would do, kept in last_check. Changes nothing.
        reuse: keep a fresh check of channel instead."""
        if channel not in CHANNELS:
            return
        if self.running():
            result, message, ok, found = BLOCKED, "an update or rollback is running", False, {}
        else:
            with self._check_lock:  # two at once would fetch at once
                last = self.last_check
                if reuse and last and last["channel"] == channel and self.clock() - last["at"] <= CHECK_FRESH_S:
                    return
                try:
                    outcome = self.updater.update(channel, dry_run=True)
                    result, message, ok = outcome.result, outcome.message, outcome.ok
                    found = self.details(outcome.target) if result == WOULD_UPDATE and outcome.target else {}
                    if result == WAITING and outcome.runs is not None:
                        found = {"runs": [list(run) for run in outcome.runs]}
                except (CommandFailed, OSError) as e:
                    result, message, ok, found = BLOCKED, str(e), False, {}
        debug.info(f"Settings page: checked for updates on {channel}: {result}: {message}")
        self.last_check = {"channel": channel, "result": result, "message": message, "ok": ok, "at": self.clock(),
                           **found}

    def details(self, target):
        """What an update to target brings: {"ref", "sha", "version" (its version.py's, or None),
        "changes" ([PR number or None, title, release notes], newest first: Board.what_changed), "packages" (whether requirements.txt
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
        self.started = command
        self.starting = self.last_check if command == "update" and self.last_check \
            and self.last_check.get("channel") == channel and self.last_check.get("sha") else None
        debug.info(f"Settings page: started the {command}" + (f" on {channel}" if channel else "")
                   + f" ({UPDATE_UNIT}.service; journalctl -u {UPDATE_UNIT} has how it goes).")
        self.last_check = None
        return STARTED
