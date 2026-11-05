import json
import os

import pytest

from self_update import state as states
from self_update import update as update_module
from self_update.board import CommandFailed
from self_update.github import GitHubError
from self_update.update import (BETA, RELEASES, Updater, beta_number, channel_of, installed_number, name_of,
                                newest_release, parse_version, release_of)
from utils import heartbeat

OLD, NEW, BETA_TIP = "1" * 40, "2" * 40, "3" * 40
APP, SETTINGS = update_module.APP_UNIT, update_module.SETTINGS_UNIT


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeBoard:
    """The board, in memory. healthy: whether the app it restarts writes a heartbeat; crashes: how many
    times systemd restarts it after that."""
    def __init__(self, app_dir, clock, heartbeat_path):
        self.app_dir, self.clock, self.heartbeat_path = str(app_dir), clock, heartbeat_path
        self.head_sha, self.branch_name, self.dirty = OLD, "develop-beta", []
        self.refs = {"refs/tags/v2.1.0": NEW, "refs/tags/v2.2.0": NEW, BETA_TIP: BETA_TIP, NEW: NEW,
                     "refs/heads/develop-beta": OLD}
        self.without_updater, self.tags = set(), {}
        self.requirements_changed, self.free, self.flags = False, 10 * 2**30, 0
        self.healthy, self.crashes, self.settings, self.port = True, 0, True, True
        self.n_restarts, self.skips_flag, self.fail = 0, True, {}
        self.calls = []

    def _call(self, name, *args):
        self.calls.append((name, *args))
        if name in self.fail and self.fail[name](self, *args):
            raise CommandFailed(f"{name} failed")

    def head(self):
        return self.head_sha

    def branch(self):
        return self.branch_name

    def changes(self):
        return self.dirty

    def fetch(self):
        self._call("fetch")

    def commit_of(self, ref):
        return self.refs.get(ref)

    def file_at(self, sha, path):
        return None if sha in self.without_updater else "text"

    def tags_at(self, sha):
        self._call("tags_at", sha)
        return self.tags.get(sha, [])

    def changed(self, old, new, path):
        return self.requirements_changed

    def checkout(self, ref, detach=True):
        self._call("checkout", ref, detach)
        self.head_sha = self.refs.get(f"refs/heads/{ref}", ref)
        self.branch_name = None if detach else ref

    def pip_freeze(self):
        self._call("pip_freeze")
        return ["aiohttp==3.11.13"]

    def pip_install(self, path):
        self._call("pip_install", path)

    def install(self, skip_requirements):
        self._call("install", self.head_sha, skip_requirements)

    def installer_skips_requirements(self):
        return self.skips_flag

    def unit_exists(self, unit):
        return self.settings if unit == SETTINGS else True

    def restart(self, unit):
        self._call("restart", unit)
        if unit == APP:
            healthy = self.healthy if self.head_sha != OLD else True  # the old version always worked
            if healthy:
                heartbeat.beat(path=self.heartbeat_path, clock=self.clock)

    def restarts(self, unit):
        n, self.n_restarts = self.n_restarts, self.n_restarts + (self.crashes if self.head_sha != OLD else 0)
        return n

    def active(self, unit):
        return True

    def free_bytes(self):
        return self.free

    def throttled(self):
        return self.flags

    def port_answers(self, port):
        return self.port


class FakeGitHub:
    def __init__(self):
        self.tags, self.tip, self.ci, self.error = ["v2.2.0", "v2.1.0", "v2.0.0"], BETA_TIP, None, None
        self.runs = []

    def _maybe_fail(self):
        if self.error:
            raise GitHubError(self.error)

    def releases(self):
        self._maybe_fail()
        return self.tags

    def branch_tip(self, branch):
        self._maybe_fail()
        return self.tip

    def ci_status(self, sha):
        return self.ci, self.runs


@pytest.fixture
def env(tmp_path):
    clock = Clock()
    app = tmp_path / "app"
    app.mkdir()
    (app / "board-config.json").write_text(json.dumps({"parks": ["Magic Kingdom"]}))
    hb = str(tmp_path / "lll-health")
    board, gh = FakeBoard(app, clock, hb), FakeGitHub()
    notes = []
    updater = Updater(board, state=states.State(str(tmp_path / "lll-update")), gh=gh, installed_version="2.0.0",
                      config_path=str(app / "board-config.json"), heartbeat_path=hb,
                      notify=lambda title, message: notes.append((title, message)), clock=clock, sleep=clock.sleep)
    return type("Env", (), {"board": board, "gh": gh, "updater": updater, "notes": notes, "clock": clock,
                            "config": app / "board-config.json", "state": updater.state})


def test_versions():
    assert parse_version("v2.1.0") == (2, 1, 0) == parse_version("2.1.0")
    assert parse_version("v2.1") is None and parse_version("latest") is None
    assert parse_version("v2.1.5-beta") is None, "a Beta tag is never a release"


def test_installed_versions_as_git_describe_gives_them():
    assert installed_number("2.1.0") == installed_number("2.1.0-3-g1a2b3c4") == (2, 1, 0)
    assert installed_number("2.1.5-beta") == installed_number("v2.1.5-beta-3-g1a2b3c4") == (2, 1, 5)
    assert installed_number("latest") is None and installed_number("2.1.5-rc") is None
    assert beta_number("2.1.5-beta") == "2.1.5"
    assert beta_number("2.1.5-beta-3-g1a2b3c4") is None, "a commit past a Beta isn't that Beta"
    assert beta_number("2.1.0") is None and beta_number(None) is None
    assert release_of("2.1.5-beta") == release_of("2.1.5-beta-2-gabcdef0") == "2.1.0"
    assert release_of("2.1.0-2-gabcdef0") == "2.1.0" and release_of("unknown") == "unknown"


@pytest.mark.parametrize("tags, installed, expected", [
    (["v2.2.0", "v2.1.0", "v2.0.0"], "2.0.0", "v2.2.0"),
    (["v2.1.0", "v2.3.0", "v2.2.0"], "2.1.0", "v2.3.0"),  # newest by version, not list order
    (["v2.1.0"], "2.1.0", None),  # nothing newer
    (["v2.1.0"], "2.5.0", None),  # beta ahead of every release: no downgrade
    (["v2.0.0", "v1.1.0"], "1.0.0", None),  # older than the updater: never offered
    (["v2.1.0", "junk"], "not a version", "v2.1.0"),
    (["v2.2.0", "v2.1.0"], "2.1.5-beta", "v2.2.0"),  # a Beta counts as its number
    (["v2.1.0"], "2.1.5-beta-3-g1a2b3c4", None),  # older than it: no downgrade
    (["v2.2.0", "v2.1.5-beta"], "2.1.0", "v2.2.0"),
])
def test_newest_release(tags, installed, expected):
    assert newest_release(tags, installed) == expected


def test_a_release_update_switches_installs_and_checks_health(env):
    outcome = env.updater.update(RELEASES)
    assert outcome.ok and outcome.result == "updated" and "v2.2.0" in outcome.message
    assert env.board.calls == [("fetch",), ("pip_freeze",), ("tags_at", OLD), ("checkout", NEW, True),
                               ("install", NEW, True), ("restart", APP), ("restart", SETTINGS)]
    record = env.state.load()
    assert record["phase"] == "updated" and record["good"] == [NEW]
    assert record["from"] == {"sha": OLD, "branch": "develop-beta", "version": "2.0.0", "channel": "beta",
                              "requirements_changed": False, "config_saved": True}
    assert record["to"] == {"sha": NEW, "ref": "v2.2.0", "channel": "releases"}
    assert open(env.state.freeze_path).read() == "aiohttp==3.11.13\n"
    assert json.load(open(env.state.config_path)) == {"parks": ["Magic Kingdom"]}
    assert env.notes == []


def test_pip_runs_only_when_requirements_changed(env):
    env.board.requirements_changed = True
    assert env.updater.update(RELEASES).ok
    assert ("install", NEW, False) in env.board.calls


def test_beta_installs_the_tip_once_ci_passed(env):
    outcome = env.updater.update(BETA)
    assert outcome.result == "updated"
    assert ("checkout", BETA_TIP, True) in env.board.calls
    assert env.state.load()["to"]["channel"] == "beta"


def test_beta_waits_for_ci(env):
    env.gh.ci = "3333333's CI is still running (test (3.11))"
    env.gh.runs = [("test (3.11)", "running"), ("test (3.13)", "passed")]
    outcome = env.updater.update(BETA)
    assert outcome.result == "waiting" and outcome.ok and "still running" in outcome.message
    assert outcome.runs == env.gh.runs, "for the card to list"
    assert env.board.calls == [], "nothing fetched or changed"


def test_beta_already_on_the_tip_is_current(env):
    env.gh.tip = OLD
    assert env.updater.update(BETA).result == "current"


def test_no_newer_release_is_current(env):
    env.updater.installed_version = "2.2.0"
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "current" and outcome.ok and env.board.calls == []


def test_a_release_already_checked_out_is_current(env):
    env.board.head_sha = NEW
    assert env.updater.update(RELEASES).result == "current"
    assert env.board.calls == [("fetch",)]


def test_a_target_without_the_updater_is_refused(env):
    env.board.without_updater.add(NEW)
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "blocked" and "predates the updater" in outcome.message
    assert env.board.calls == [("fetch",)]


def test_a_tag_missing_after_the_fetch_is_refused(env):
    del env.board.refs["refs/tags/v2.2.0"]
    assert "isn't in the fetched checkout" in env.updater.update(RELEASES).message


def test_a_failed_fetch_changes_nothing(env):
    env.board.fail = {"fetch": lambda board: True}
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "blocked" and "fetch failed" in outcome.message
    assert env.state.load()["phase"] == "idle"


@pytest.mark.parametrize("setup, why", [
    (lambda e: setattr(e.board, "free", 100 * 2**20), "only 100 MB free"),
    (lambda e: setattr(e.board, "flags", 0x50005), "under-voltage or throttled"),
    (lambda e: heartbeat.beat(show="Happily Ever After", show_s=600, path=e.updater.heartbeat_path, clock=e.clock),
     "Happily Ever After is playing"),
    (lambda e: setattr(e.board, "dirty", [" M disney.py", " M a", " M b", " M c"]), "changes: M disney.py, M a, M b and 1 more"),
    (lambda e: setattr(e.gh, "error", "can't reach GitHub (timed out)"), "can't reach GitHub"),
])
def test_preflight_blocks_an_update(env, setup, why):
    setup(env)
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "blocked" and not outcome.ok and why in outcome.message
    assert env.board.calls == []


def test_only_flags_set_now_block(env):
    env.board.flags = 0x50000  # under-voltage since boot, fine now
    assert env.updater.update(RELEASES).ok


def test_a_check_says_what_it_would_do_and_changes_nothing(env):
    outcome = env.updater.update(RELEASES, dry_run=True)
    assert outcome.result == "would_update" and outcome.ok and "v2.2.0" in outcome.message
    assert outcome.target.ref == "v2.2.0" and outcome.target.sha, "what it found, for the settings page"
    assert env.board.calls == [("fetch",)]
    assert not os.path.exists(env.state.path)


def test_an_unfinished_update_blocks_the_next(env):
    env.state.set_phase(env.state.load(), states.SWITCHED, **{"from": {"sha": OLD}})
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "blocked" and "stopped at switched" in outcome.message


def test_a_running_update_blocks_another(env):
    with env.state.lock():
        outcome = env.updater.update(RELEASES)
    assert outcome.result == "blocked" and "already running" in outcome.message


def test_an_unknown_channel_is_a_mistake(env):
    with pytest.raises(ValueError):
        env.updater.update("nightly")


def test_an_app_that_never_draws_is_rolled_back_after_the_window(env):
    env.board.healthy = False
    env.board.requirements_changed = True
    # A save on the settings page mid-update (the hook never fails the install).
    env.board.fail = {"install": lambda board, sha, skip: env.config.write_text('{"parks": ["EPCOT"]}') and False}
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "rolled_back" and not outcome.ok
    assert "hasn't finished a screen" in outcome.message
    assert env.clock.now >= 1000 + update_module.HEALTH_WINDOW_S
    rollback = env.board.calls[env.board.calls.index(("restart", SETTINGS)) + 1:]
    assert rollback == [("checkout", "develop-beta", False), ("install", OLD, True),
                        ("pip_install", env.state.freeze_path), ("restart", APP), ("restart", SETTINGS)]
    assert env.board.branch_name == "develop-beta", "back on the branch it was on"
    assert json.loads(env.config.read_text()) == {"parks": ["Magic Kingdom"]}, "config.json as before the update"
    record = env.state.load()
    assert record["phase"] == "rolled_back" and "hasn't finished a screen" in record["reason"] and NEW not in record["good"]
    assert env.notes == [("Update rolled back", "Back on Beta 1111111. Why: " + record["reason"] + ".")]


def test_a_rollback_names_a_beta_by_its_commit_and_a_release_by_its_version(env):
    # A Beta an earlier update installed: detached, its version.py still says the release it grew from.
    env.board.branch_name = None
    env.state.save({"phase": "updated", "good": [OLD], "to": {"sha": OLD, "ref": "develop-beta", "channel": "beta"}})
    env.board.crashes = 1
    assert "rolled back to Beta 1111111: the app crashed" in env.updater.update(RELEASES).message
    env.board.head_sha, env.board.tags = OLD, {OLD: ["v2.0.0"]}
    env.state.save({"phase": "updated", "good": [OLD]})
    assert "rolled back to 2.0.0 (1111111): the app crashed" in env.updater.update(RELEASES).message


def test_a_commits_channel(env, monkeypatch):
    board, beta_update = env.board, {"to": {"sha": OLD, "channel": "beta"}}
    board.tags = {OLD: ["v2.1.0"]}
    assert channel_of(board, OLD, None, beta_update) == RELEASES, "a release tag wins"
    board.tags = {OLD: ["nightly"]}
    assert channel_of(board, OLD, "main", beta_update) == RELEASES, "so does the release branch"
    assert channel_of(board, OLD, None, {"to": {"sha": OLD, "channel": "releases"}}) == RELEASES, "as installed"
    assert channel_of(board, OLD, None, {}) == BETA, "anything else: a Beta"
    assert channel_of(board, None, None, {}) == RELEASES and channel_of(board, None, None, beta_update) == BETA
    warnings = []
    monkeypatch.setattr(update_module.debug, "warning", warnings.append)
    board.fail = {"tags_at": lambda board, sha: True}
    assert channel_of(board, OLD, None, {}) == BETA and "tags" in warnings[0]


def test_a_rollback_point_from_before_channels_is_named_by_its_version():
    assert name_of({"sha": OLD, "version": "2.0.0"}) == "2.0.0 (1111111)"
    assert name_of({"sha": OLD, "version": "2.0.0", "channel": "beta"}) == "Beta 1111111"


def test_a_beta_rollback_point_is_named_by_its_number_when_it_was_exactly_one():
    assert name_of({"sha": OLD, "version": "2.1.5-beta", "channel": "beta"}) == "Beta 2.1.5"
    assert name_of({"sha": OLD, "version": "2.1.5-beta-2-g1111111", "channel": "beta"}) == "Beta 1111111"


def test_a_crash_loop_rolls_back_without_waiting_out_the_window(env):
    env.board.crashes = 1
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "rolled_back" and "systemd restarted it" in outcome.message
    assert env.clock.now < 1000 + update_module.HEALTH_WINDOW_S


def test_a_settings_page_that_doesnt_answer_fails_the_update(env):
    env.board.port = False
    outcome = env.updater.update(RELEASES)
    assert "port 8080" in outcome.message
    assert env.state.load()["phase"] == "rollback_failed", "the old version's page didn't answer either"
    assert env.notes[0][0] == "Update rollback FAILED"


def test_no_settings_service_skips_its_check(env):
    env.board.settings = False
    env.board.port = False
    assert env.updater.update(RELEASES).result == "updated"
    assert ("restart", SETTINGS) not in env.board.calls


def test_a_failed_install_rolls_back_from_a_detached_head(env):
    env.board.branch_name = None
    env.board.fail = {"install": lambda board, sha, skip: sha == NEW}
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "rolled_back" and "install failed" in outcome.message
    assert ("checkout", OLD, True) in env.board.calls


def test_a_branch_that_moved_on_rolls_back_to_the_commit(env):
    env.board.refs["refs/heads/develop-beta"] = "9" * 40
    env.board.healthy = False
    env.updater.update(RELEASES)
    assert ("checkout", OLD, True) in env.board.calls


def test_an_old_installer_without_the_flag_gets_the_freeze_back(env):
    env.board.healthy = False
    env.board.skips_flag = False
    env.updater.update(RELEASES)
    assert ("pip_install", env.state.freeze_path) in env.board.calls


def test_an_unexpected_error_still_rolls_back(env, monkeypatch):
    monkeypatch.setattr(env.board, "install", lambda skip_requirements: 1 / 0)
    outcome = env.updater.update(RELEASES)
    assert outcome.result in ("rolled_back", "rollback_failed") and "unexpectedly" in outcome.message


def test_a_failed_rollback_point_changes_nothing(env):
    env.board.fail = {"pip_freeze": lambda board: True}
    outcome = env.updater.update(RELEASES)
    assert outcome.result == "blocked" and "nothing changed" in outcome.message
    assert not any(call[0] == "checkout" for call in env.board.calls)


def test_a_rollback_by_hand_undoes_the_last_update(env):
    assert env.updater.update(RELEASES).ok
    outcome = env.updater.rollback()
    assert outcome.result == "rolled_back" and outcome.ok and "by hand" in outcome.message
    assert env.board.head_sha == OLD and env.state.load()["good"] == []
    assert env.updater.rollback().result == "nothing_to_undo"


def test_a_rollback_with_no_update_has_nothing_to_undo(env):
    assert env.updater.rollback().result == "nothing_to_undo"


def test_a_rollback_while_an_update_runs_is_blocked(env):
    assert env.updater.update(RELEASES).ok
    with env.state.lock():
        assert env.updater.rollback().result == "blocked"


def test_pushover_goes_out_only_with_keys(env, monkeypatch):
    sent = []
    monkeypatch.setattr(update_module.pushover, "send", lambda keys, title, message: sent.append((keys, title)))
    updater = Updater(env.board, state=env.state, gh=env.gh, config_path=str(env.config))
    updater._pushover("Update rolled back", "why")
    assert sent == []
    env.config.write_text(json.dumps({"pushover": {"user_key": "u-real", "app_token": "t-real"}}))
    updater._pushover("Update rolled back", "why")
    assert sent and sent[0][0] == ("u-real", "t-real") and sent[0][1].endswith(": Update rolled back")


def test_a_pushover_failure_is_logged_not_raised(env, monkeypatch):
    warnings = []
    monkeypatch.setattr(update_module.debug, "warning", warnings.append)

    def refuse(keys, title, message):
        raise update_module.pushover.PushoverError("application token is invalid")

    monkeypatch.setattr(update_module.pushover, "send", refuse)
    env.config.write_text(json.dumps({"pushover": {"user_key": "u-real", "app_token": "t-real"}}))
    Updater(env.board, state=env.state, gh=env.gh, config_path=str(env.config))._pushover("T", "m")
    assert warnings and "token is invalid" in warnings[0]


@pytest.mark.parametrize("phase", states.UNFINISHED)
def test_recovery_at_boot_rolls_back_an_update_a_power_cut_stopped(env, phase):
    env.board.head_sha, env.board.branch_name = NEW, None  # where the power cut left it
    env.state.set_phase(env.state.load(), phase, **{"from": {"sha": OLD, "branch": "develop-beta", "version": "2.0.0",
                                                             "requirements_changed": False, "config_saved": False}},
                        to={"sha": NEW, "ref": "v2.2.0", "channel": "releases"})
    outcome = env.updater.recover()
    assert outcome.result == "rolled_back" and f"stopped midway (at {phase})" in outcome.message
    assert env.board.head_sha == OLD and env.board.branch_name == "develop-beta"
    assert env.notes and env.notes[0][0] == "Update rolled back"


@pytest.mark.parametrize("phase", ["idle", "updated", "rolled_back", "rollback_failed"])
def test_recovery_leaves_a_finished_update_alone(env, phase):
    env.state.set_phase(env.state.load(), phase, **{"from": {"sha": OLD}})
    outcome = env.updater.recover()
    assert outcome.result == "nothing_to_undo" and phase in outcome.message
    assert env.board.calls == [] and env.notes == []


def test_recovery_waits_for_a_running_update(env):
    with env.state.lock():
        assert env.updater.recover().result == "blocked"
