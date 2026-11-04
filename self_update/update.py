"""Deciding and doing an update, and undoing one.

Two channels: RELEASES, the newest GitHub release newer than what's installed (never a downgrade,
and never one older than MIN_RELEASE, the first with the updater), and BETA, develop-beta's tip
once its CI has passed. An update:

1. Pre-flight: no unfinished update, REQUIRED_FREE_BYTES free, no under-voltage or throttling now,
   no show playing, no changes in the checkout, and GitHub reachable.
2. Rollback point (state.py): the commit and branch, pip freeze, a copy of config.json.
3. git checkout --detach, then the new version's LLL-install.sh (pip only if requirements.txt
   changed), and restart the app and the settings page.
4. Health within HEALTH_WINDOW_S: the app has written a heartbeat since its restart
   (utils/heartbeat.py), systemd hasn't restarted it (Restart=always hides a crash loop), and the
   settings page answers. Pass: it joins the good commits. Fail, or any step erroring: roll back
   (the old commit, the freeze, config.json, restart) and say why by Pushover.
"""
import json
import os
import re
import shutil
import socket
import time
from dataclasses import dataclass

from settings_page import pushover
from self_update import github, state as states
from self_update.board import CommandFailed
from utils import debug, heartbeat
from utils.config import pushover_keys

RELEASES, BETA = "releases", "beta"
CHANNELS = (RELEASES, BETA)
BETA_BRANCH = "develop-beta"
# v2.0.0 and older don't have the updater: installing one would remove the way back.
MIN_RELEASE = (2, 1, 0)
# Present in every version the updater may install.
UPDATER_FILE = "self_update/__init__.py"
REQUIRED_FREE_BYTES = 300 * 1024 * 1024
# The firmware's "now" flags: under-voltage, frequency capped, throttled, soft temperature limit.
# (The since-boot flags, bits 16-19, would block every update until a reboot.)
THROTTLED_NOW = 0xF
APP_UNIT = "LightningLane-Live-LED.service"
SETTINGS_UNIT = "lll-settings.service"
SETTINGS_PORT = 8080
HEALTH_WINDOW_S = 5 * 60
HEALTH_POLL_S = 5

# Outcome results.
UPDATED, CURRENT, BLOCKED, WOULD_UPDATE = "updated", "current", "blocked", "would_update"
ROLLED_BACK, ROLLBACK_FAILED, NOTHING_TO_UNDO = "rolled_back", "rollback_failed", "nothing_to_undo"
SUCCESSES = (UPDATED, CURRENT, WOULD_UPDATE, ROLLED_BACK)


@dataclass
class Target:
    channel: str
    ref: str  # the release tag, or the beta branch
    sha: str = None  # known up front for beta; a release's comes from its tag after the fetch


@dataclass
class Outcome:
    result: str
    message: str
    ok: bool = None  # whether it did what was asked; by default, from the result

    def __post_init__(self):
        if self.ok is None:
            self.ok = self.result in SUCCESSES


def parse_version(text):
    """(major, minor, patch) from "v2.1.0" or "2.1.0", or None."""
    found = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(text).strip())
    return tuple(int(n) for n in found.groups()) if found else None


def newest_release(tags, installed):
    """The newest release tag at least MIN_RELEASE and newer than the installed version, or None."""
    current = parse_version(installed) or (0, 0, 0)
    found = [(v, tag) for tag in tags if (v := parse_version(tag)) and v >= MIN_RELEASE and v > current]
    return max(found)[1] if found else None


class Updater:
    def __init__(self, board, state=None, gh=github, installed_version=None, config_path=None,
                 heartbeat_path=None, notify=None, clock=time.time, sleep=time.sleep):
        from version import SCRIPT_VERSION
        self.board, self.state, self.gh = board, state or states.State(), gh
        self.installed_version = installed_version or SCRIPT_VERSION
        self.config_path = config_path or os.path.join(board.app_dir, "config.json")
        self.heartbeat_path, self.clock, self.sleep = heartbeat_path, clock, sleep
        self.notify = notify or self._pushover

    # deciding

    def preflight(self):
        """What stops an update now, as a list of reasons (empty: go)."""
        problems = []
        free = self.board.free_bytes()
        if free < REQUIRED_FREE_BYTES:
            problems.append(f"only {free // 2**20} MB free; an update needs {REQUIRED_FREE_BYTES // 2**20} MB")
        flags = self.board.throttled()
        if flags and flags & THROTTLED_NOW:
            problems.append(f"the Pi is under-voltage or throttled right now ({flags:#x}): fix its power or cooling first")
        show = heartbeat.show_playing(heartbeat.read(self.heartbeat_path), self.clock())
        if show:
            problems.append(f"{show} is playing")
        changes = self.board.changes()
        if changes:
            problems.append(f"the checkout has changes: {', '.join(c.strip() for c in changes[:3])}"
                            + (f" and {len(changes) - 3} more" if len(changes) > 3 else ""))
        return problems

    def plan(self, channel):
        """(Target, None), or (None, why there's nothing to install). Raises github.GitHubError."""
        if channel == RELEASES:
            tag = newest_release(self.gh.releases(), self.installed_version)
            if not tag:
                return None, f"no release newer than {self.installed_version}"
            return Target(RELEASES, tag), None
        sha = self.gh.branch_tip(BETA_BRANCH)
        if sha == self.board.head():
            return None, f"already on {BETA_BRANCH}'s tip ({sha[:7]})"
        problem = self.gh.ci_problem(sha)
        if problem:
            return None, problem
        return Target(BETA, BETA_BRANCH, sha), None

    def _resolve(self, target):
        """Fetch, and fill in target.sha. Returns the Outcome if it can't (or needn't) be installed, else None."""
        self.board.fetch()
        sha = self.board.commit_of(f"refs/tags/{target.ref}" if target.channel == RELEASES else target.sha)
        if not sha:
            return Outcome(BLOCKED, f"{target.ref} isn't in the fetched checkout")
        target.sha = sha
        if sha == self.board.head():
            return Outcome(CURRENT, f"already on {target.ref} ({sha[:7]})")
        if self.board.file_at(sha, UPDATER_FILE) is None:
            return Outcome(BLOCKED, f"{target.ref} ({sha[:7]}) predates the updater: it couldn't update or roll back again")
        return None

    # updating

    def update(self, channel, dry_run=False):
        """Update on channel, or (dry_run) only say what it would do, changing nothing but the fetch."""
        if channel not in CHANNELS:
            raise ValueError(f"channel must be one of {CHANNELS}")
        if dry_run:
            return self._update(channel, dry_run=True)
        try:
            with self.state.lock():
                return self._update(channel)
        except states.Busy as e:
            return Outcome(BLOCKED, str(e))

    def _update(self, channel, dry_run=False):
        record = self.state.load()
        if record["phase"] in states.UNFINISHED:
            return Outcome(BLOCKED, f"an earlier update didn't finish (it stopped at {record['phase']}): "
                                    "roll it back first (python3 -m self_update rollback)")
        problems = self.preflight()
        target = None
        try:
            target, why = self.plan(channel)
        except github.GitHubError as e:
            problems.append(str(e))
        if problems:
            return Outcome(BLOCKED, "; ".join(problems))
        if target is None:
            return Outcome(CURRENT, why)
        try:
            stop = self._resolve(target)
        except CommandFailed as e:
            return Outcome(BLOCKED, str(e))
        if stop:
            return stop
        if dry_run:
            return Outcome(WOULD_UPDATE, f"would update to {target.ref} ({target.sha[:7]})")
        try:
            record = self._take_rollback_point(record, target)
        except (CommandFailed, OSError) as e:
            return Outcome(BLOCKED, f"couldn't take a rollback point, so nothing changed: {e}")
        debug.info(f"Updating from {record['from']['sha'][:7]} to {target.ref} ({target.sha[:7]}).")
        try:
            self.board.checkout(target.sha)
            self.state.set_phase(record, states.SWITCHED)
            self.board.install(skip_requirements=not record["from"]["requirements_changed"])
            self.state.set_phase(record, states.INSTALLED)
            self.state.set_phase(record, states.CHECKING)
            problem = self._restart_and_check()
        except CommandFailed as e:
            problem = str(e)
        except Exception as e:  # anything at all: the board mustn't be left half-updated
            debug.exception("The update failed unexpectedly.")
            problem = f"the update failed unexpectedly: {e}"
        if problem is None:
            states.remember_good(record, target.sha)
            self.state.set_phase(record, states.UPDATED, reason=None)
            debug.info(f"Updated to {target.ref} ({target.sha[:7]}); it passed its health check.")
            return Outcome(UPDATED, f"updated to {target.ref} ({target.sha[:7]})")
        debug.error(f"The update to {target.ref} ({target.sha[:7]}) failed: {problem}. Rolling back.")
        undone = self._roll_back(record, problem)
        return Outcome(undone.result, undone.message, ok=False)  # back where it was, but not updated

    def _take_rollback_point(self, record, target):
        head = self.board.head()
        freeze = self.board.pip_freeze()
        os.makedirs(self.state.folder, mode=0o700, exist_ok=True)
        with open(self.state.freeze_path, "w", encoding="utf-8") as f:
            f.write("\n".join(freeze) + "\n")
        has_config = os.path.isfile(self.config_path)
        if has_config:
            shutil.copy2(self.config_path, self.state.config_path)
        record.update(
            {"from": {"sha": head, "branch": self.board.branch(), "version": self.installed_version,
                      "requirements_changed": self.board.changed(head, target.sha, "requirements.txt"),
                      "config_saved": has_config},
             "to": {"sha": target.sha, "ref": target.ref, "channel": target.channel},
             "started_at": self.clock(), "reason": None})
        return self.state.set_phase(record, states.READY)

    def _restart_and_check(self):
        """Restart the app and the settings page, then wait for health. Returns the problem, or None."""
        settings = self.board.unit_exists(SETTINGS_UNIT)
        since = self.clock()
        self.board.restart(APP_UNIT)
        if settings:
            self.board.restart(SETTINGS_UNIT)
        return self.wait_healthy(since, self.board.restarts(APP_UNIT), settings)

    def wait_healthy(self, since, restarts_before, settings):
        """None once the app is healthy, else the last problem when HEALTH_WINDOW_S runs out. A
        restart by systemd fails at once: a crash loop won't heal."""
        deadline = since + HEALTH_WINDOW_S
        while True:
            restarts = self.board.restarts(APP_UNIT) - restarts_before
            if restarts > 0:
                return f"the app crashed: systemd restarted it {restarts} time{'s' if restarts > 1 else ''}"
            problem = self._health_problem(since, settings)
            if problem is None or self.clock() >= deadline:
                return problem
            self.sleep(HEALTH_POLL_S)

    def _health_problem(self, since, settings):
        if not self.board.active(APP_UNIT):
            return "the app isn't running"
        beat = heartbeat.read(self.heartbeat_path)
        if not beat or beat["at"] < since:
            return "the app hasn't finished a screen since it restarted"
        if settings and not self.board.port_answers(SETTINGS_PORT):
            return f"the settings page doesn't answer on port {SETTINGS_PORT}"
        return None

    # undoing

    def rollback(self, reason="rolled back by hand"):
        """Undo the last update (finished or not), back to its rollback point."""
        try:
            with self.state.lock():
                record = self.state.load()
                if not record.get("from") or record["phase"] in (states.IDLE, states.ROLLED_BACK):
                    return Outcome(NOTHING_TO_UNDO, "there's no update to undo")
                return self._roll_back(record, reason)
        except states.Busy as e:
            return Outcome(BLOCKED, str(e))

    def recover(self):
        """At boot: roll back an update that stopped midway (a power cut, a crash), else do nothing.
        A failed rollback is left for a person: retrying it every boot could loop."""
        try:
            with self.state.lock():
                record = self.state.load()
                if record["phase"] not in states.UNFINISHED or not record.get("from"):
                    return Outcome(NOTHING_TO_UNDO, f"no unfinished update (last: {record['phase']})")
                debug.warning(f"An update stopped midway (at {record['phase']}): rolling it back.")
                return self._roll_back(record, f"the update stopped midway (at {record['phase']}), "
                                               "probably a power cut")
        except states.Busy as e:
            return Outcome(BLOCKED, str(e))

    def _roll_back(self, record, reason):
        self.state.set_phase(record, states.ROLLING_BACK, reason=reason)
        old = record["from"]
        try:
            branch = old.get("branch")
            if branch and self.board.commit_of(f"refs/heads/{branch}") == old["sha"]:
                self.board.checkout(branch, detach=False)
            else:
                self.board.checkout(old["sha"])
            self.board.install(skip_requirements=True)  # the old installer: the shebang and the rest
            if old.get("requirements_changed") or not self.board.installer_skips_requirements():
                self.board.pip_install(self.state.freeze_path)
            if old.get("config_saved") and os.path.isfile(self.state.config_path):
                shutil.copyfile(self.state.config_path, self.config_path)  # into the old file: keeps its owner
            problem = self._restart_and_check()
        except CommandFailed as e:
            problem = str(e)
        except Exception as e:
            debug.exception("The rollback failed unexpectedly.")
            problem = f"the rollback failed unexpectedly: {e}"
        bad = (record.get("to") or {}).get("sha")
        record["good"] = [sha for sha in record.get("good", []) if sha != bad]
        name = f"{old.get('version')} ({old['sha'][:7]})"
        if problem is None:
            self.state.set_phase(record, states.ROLLED_BACK)
            debug.warning(f"Rolled back to {name}: {reason}.")
            self.notify("Update rolled back", f"Back on {name}. Why: {reason}.")
            return Outcome(ROLLED_BACK, f"rolled back to {name}: {reason}")
        self.state.set_phase(record, states.ROLLBACK_FAILED, rollback_problem=problem)
        debug.error(f"Rolling back to {name} failed: {problem}.")
        self.notify("Update rollback FAILED",
                    f"Couldn't get back to {name}: {problem}. The update had failed because: {reason}. "
                    "Over SSH: sudo venv/bin/python3 -m self_update rollback")
        return Outcome(ROLLBACK_FAILED, f"rolling back to {name} failed: {problem} (the update failed: {reason})")

    def _pushover(self, title, message):
        """Pushover the news if config.json has the keys; a failure is logged, never raised."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                keys = pushover_keys(json.load(f))
        except (OSError, ValueError, AttributeError):
            keys = None
        if not keys:
            return
        board = socket.gethostname().split(".")[0]
        try:
            pushover.send(keys, f"{board}: {title}", message)
        except (OSError, ValueError, pushover.PushoverError) as e:
            debug.warning(f"Couldn't Pushover \"{title}\": {e}")
