"""The Updates card's logic, with a fake updater and board (no git, systemd or GitHub)."""
import subprocess

import pytest

from self_update.board import CommandFailed
from self_update.state import State
from self_update.update import Outcome, Target
from settings_page import updates as upd
from settings_page.updates import Updates


class FakeBoard:
    def __init__(self):
        self.running, self.asked = False, []
        self.on_branch, self.tags = "develop-beta", []
        self.log = [(201, "Show what an update brings", None), (200, "Roll back at boot", ["Rolls back at boot."])]

    def what_changed(self, old, new):
        if isinstance(self.log, Exception):
            raise self.log
        return self.log

    def describe(self, sha):
        return "2.2.0"

    def changed(self, old, new, path):
        return path == "requirements.txt"

    def active(self, unit):
        self.asked.append(unit)
        if self.running is None:
            raise CommandFailed("systemctl show failed: [Errno 2] No such file")
        return self.running

    def head(self):
        return "a" * 40

    def branch(self):
        return self.on_branch

    def tags_at(self, sha):
        if isinstance(self.tags, Exception):
            raise self.tags
        return self.tags


class FakeUpdater:
    def __init__(self, tmp_path, outcome=Outcome("would_update", "would update to v2.2.0 (2222222)",
                                                 target=Target("releases", "v2.2.0", "2" * 40))):
        self.board, self.state, self.outcome, self.asked = FakeBoard(), State(str(tmp_path / "s")), outcome, []
        self.installed_version = "2.1.0"

    def update(self, channel, dry_run=False):
        self.asked.append((channel, dry_run))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class Clock:
    now = 1000.0

    def __call__(self):
        return self.now


def make(tmp_path, run=None, **kwargs):
    updater, clock = FakeUpdater(tmp_path, **kwargs), Clock()
    calls = []

    def fake_run(args, **_):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")
    updates = Updates("/app", updater, run=run or fake_run, python="/app/venv/bin/python3", clock=clock)
    return updates, updater, clock, calls


def test_a_board_that_never_updated_shows_what_is_installed_and_asks_for_a_check(tmp_path):
    updates, *_ = make(tmp_path)
    view = updates.view()
    assert (view["version"], view["sha"], view["branch"], view["running"]) == ("2.1.0", "a" * 40, "develop-beta", False)
    assert view["phase"] == "idle" and view["outcome"] is None and view["check"] is None
    assert view["channel"] == view["installed_channel"] == "beta" and view["from"] is None
    assert view["auto_check"] is True


def test_the_channel_is_the_installed_ones_until_a_check_picks_another(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    assert updates.view()["channel"] == "beta", "on develop-beta"
    updater.board.on_branch = "main"
    assert updates.view()["channel"] == "releases"
    updater.board.on_branch = None  # detached, as an update leaves it
    assert updates.view()["channel"] == "beta", "a commit that isn't a release"
    updater.state.save({"phase": "updated", "to": {"channel": "releases", "sha": "a" * 40}, "good": []})
    assert updates.view()["channel"] == "releases", "what the last update installed"
    updater.state.save({"phase": "updated", "to": {"channel": "releases", "sha": "b" * 40}, "good": []})
    assert updates.view()["channel"] == "beta", "the last update installed something else: rolled back"
    updater.board.tags = ["v2.1.0-rc1", "v2.1.0"]
    assert updates.view()["channel"] == "releases", "on a release tag"
    updater.board.tags = ["nightly"]
    assert updates.view()["channel"] == "beta"
    updates.check("releases")
    view = updates.view()
    assert view["channel"] == "releases" and view["installed_channel"] == "beta" and view["auto_check"] is False


def test_unreadable_tags_or_commit_still_give_a_channel(tmp_path, monkeypatch):
    warnings = []
    monkeypatch.setattr(upd.debug, "warning", warnings.append)
    updates, updater, _, _ = make(tmp_path)
    updater.board.tags = CommandFailed("git tag exited 128")
    assert updates.view()["channel"] == "beta" and "tags" in warnings[0]
    assert updates.installed_channel(None, None, {}) == "releases"
    assert updates.installed_channel(None, None, {"to": {"channel": "beta"}}) == "beta"


def test_the_pages_own_check_reuses_a_fresh_one(tmp_path):
    updates, updater, clock, _ = make(tmp_path)
    updates.auto_check("beta")
    updates.auto_check("beta")
    assert updater.asked == [("beta", True)], "one check: the second page load reuses it"
    updates.auto_check("releases")
    assert updater.asked[-1] == ("releases", True), "another channel checks"
    clock.now += upd.CHECK_FRESH_S + 1
    updates.auto_check("releases")
    assert len(updater.asked) == 3, "too old: checks again"
    updates.check("releases")
    assert len(updater.asked) == 4, "the Check button always checks"


def test_a_check_is_a_dry_run_kept_for_ten_minutes(tmp_path):
    updates, updater, clock, calls = make(tmp_path)
    updates.check("beta")
    assert updater.asked == [("beta", True)] and calls == [], "a dry run: nothing started"
    assert updates.view()["check"] == {
        "channel": "beta", "result": "would_update", "message": "would update to v2.2.0 (2222222)", "ok": True,
        "at": 1000.0, "ref": "v2.2.0", "sha": "2" * 40, "version": "2.2.0", "packages": True,
        "changes": [[201, "Show what an update brings", None], [200, "Roll back at boot", ["Rolls back at boot."]]]}
    clock.now += upd.CHECK_FRESH_S + 1
    assert updates.view()["check"] is None


def test_a_check_waiting_on_ci_keeps_its_runs(tmp_path):
    updates, _, _, _ = make(tmp_path, outcome=Outcome("waiting", "3333333's CI is still running (test (3.11))",
                                                      runs=[("test (3.11)", "running"), ("test (3.13)", "passed")]))
    updates.check("beta")
    check = updates.view()["check"]
    assert check["result"] == "waiting" and check["runs"] == [["test (3.11)", "running"], ["test (3.13)", "passed"]]


def test_a_check_with_a_bad_channel_does_nothing(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    updates.check("nightly")
    assert updater.asked == [] and updates.last_check is None


def test_a_check_that_fails_or_runs_during_an_update_says_why(tmp_path):
    updates, updater, _, _ = make(tmp_path, outcome=CommandFailed("git status exited 128: not a git repository"))
    updates.check("releases")
    assert updates.last_check["result"] == "blocked" and "not a git repository" in updates.last_check["message"]
    updater.board.running = True
    updater.asked.clear()
    updates.check("releases")
    assert updater.asked == [] and updates.last_check["message"] == "an update or rollback is running"


def test_an_update_starts_as_its_own_unit_and_drops_the_check(tmp_path):
    updates, _, _, calls = make(tmp_path)
    updates.check("beta")
    assert updates.start("update", "beta") == upd.STARTED
    assert calls == [["systemd-run", "--unit=lll-update", "--collect", "--working-directory=/app",
                      "--description=LightningLane-Live-LED update", "/app/venv/bin/python3", "-m", "self_update",
                      "update", "--channel", "beta"]]
    assert updates.last_check is None
    assert updates.start("rollback") == upd.STARTED and calls[1][-1] == "rollback"


def test_an_update_with_a_bad_channel_doesnt_start(tmp_path):
    updates, _, _, calls = make(tmp_path)
    assert updates.start("update", "nightly") == upd.START_FAILED and calls == []


def test_one_already_running_is_busy(tmp_path):
    updates, updater, _, calls = make(tmp_path)
    updater.board.running = True
    assert updates.start("rollback") == upd.BUSY and calls == []
    updater.board.running = False
    updates.run = lambda args, **_: subprocess.CompletedProcess(
        args, 1, "", "Failed to start transient service unit: Unit lll-update.service was already loaded")
    assert updates.start("rollback") == upd.BUSY, "systemd refused a second"


@pytest.mark.parametrize("run", [
    lambda args, **_: subprocess.CompletedProcess(args, 1, "", "Failed to connect to bus"),
    lambda args, **_: (_ for _ in ()).throw(FileNotFoundError("systemd-run")),
    lambda args, **_: (_ for _ in ()).throw(subprocess.TimeoutExpired(args, 30)),
])
def test_a_start_that_fails_is_logged(tmp_path, monkeypatch, run):
    errors = []
    monkeypatch.setattr(upd.debug, "error", errors.append)
    updates, *_ = make(tmp_path, run=run)
    assert updates.start("update", "releases") == upd.START_FAILED
    assert errors and "can't start the update" in errors[0]


def test_status_says_what_a_running_update_is_doing(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    assert updates.status() == {"running": False, "phase": None, "step": None}
    updater.board.running = True
    assert updates.status() == {"running": True, "phase": "Checking it can update", "step": 0}, \
        "before its rollback point"
    for phase, step in (("ready", 1), ("switched", 2), ("installed", 3), ("checking", 3)):
        updater.state.save({"phase": phase, "good": []})
        assert updates.status()["step"] == step and updates.view()["step"] == step
    assert updates.status()["phase"] == "Checking the new version works" == updates.view()["status"]
    assert updater.board.asked[-1] == "lll-update.service"
    updater.state.save({"phase": "rolling_back", "good": []})
    assert updates.status() == {"running": True, "phase": "Rolling back", "step": None}


def test_a_rollback_started_here_has_no_steps_before_its_phase_is_saved(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    updater.state.save({"phase": "updated", "good": []})
    updates.start("rollback")
    updater.board.running = True
    assert updates.status() == {"running": True, "phase": "Rolling back", "step": None}
    updates.start("update", "beta")
    assert updates.status()["step"] is None, "busy: the rollback still runs"


def test_without_systemctl_nothing_is_running(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    updater.board.running = None
    assert updates.running() is False


def test_a_check_that_cant_list_the_changes_still_offers_the_update(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    updater.board.log = CommandFailed("git log exited 128")
    updates.check("releases")
    assert updates.last_check["result"] == "would_update" and updates.last_check["ref"] == "v2.2.0"
    assert "changes" not in updates.last_check


def test_while_it_runs_the_card_knows_what_is_being_installed(tmp_path):
    updates, updater, _, _ = make(tmp_path)
    updates.check("releases")
    updates.start("update", "releases")
    updater.board.running = True
    to = updates.view()["to"]
    assert to["ref"] == "v2.2.0" and to["changes"][0] == [201, "Show what an update brings", None], "before its rollback point"
    updates.starting = None  # the settings page restarted mid-update: state.json still says
    updater.state.save({"phase": "checking", "to": {"ref": "v2.2.0", "sha": "2" * 40}, "good": []})
    assert updates.view()["to"] == {"ref": "v2.2.0", "sha": "2" * 40}
    updater.board.running = False
    assert updates.view()["to"] is None


def test_starting_a_rollback_or_another_channel_carries_no_list(tmp_path):
    updates, _, _, _ = make(tmp_path)
    updates.check("releases")
    updates.start("update", "beta")
    assert updates.starting is None
