"""
Pins for Updater._update, call by call: every outcome path with its collaborators (preflight, plan,
resolve, rollback point, board, state, restart and health check, rollback) in order, and the log lines
and Outcome each one ends in. They exist so _update can be split into named steps with no change in
behaviour; each case here passed on the code before the split.
"""
import pytest

from self_update import github
from self_update import state as states
from self_update import update as update_module
from self_update.board import CommandFailed
from self_update.update import (
    BLOCKED,
    CURRENT,
    ROLLBACK_FAILED,
    ROLLED_BACK,
    UPDATED,
    WAITING,
    WOULD_UPDATE,
    Outcome,
    Target,
    Updater,
)


class _Board:
    app_dir = "/nowhere"

    def __init__(self, log, fail_on=None, error=None):
        self.log, self.fail_on, self.error = log, fail_on, error

    def checkout(self, sha, detach=True):
        self.log.append(("checkout", sha) if detach else ("checkout", sha, detach))
        self._maybe_fail("checkout")

    def install(self, skip_requirements):
        self.log.append(("install", skip_requirements))
        self._maybe_fail("install")

    def _maybe_fail(self, name):
        if self.fail_on == name:
            raise self.error


class _State:
    def __init__(self, log, phase="idle"):
        self.log, self.record = log, {"phase": phase}

    def load(self):
        self.log.append("load")
        return self.record

    def set_phase(self, record, phase, **changes):
        self.log.append(("set_phase", phase, changes))
        record.update(phase=phase, **changes)
        return record


class _Debug:
    def __init__(self, log):
        self.log = log

    def info(self, msg):
        self.log.append(("info", msg))

    def error(self, msg):
        self.log.append(("error", msg))

    def exception(self, msg):
        self.log.append(("exception", msg))

    def warning(self, msg):
        self.log.append(("warning", msg))


def _maybe_raise(value):
    """Raise value if it's an exception, else hand it back."""
    if isinstance(value, BaseException):
        raise value
    return value


@pytest.fixture
def run(monkeypatch):
    """run(**opts) -> (outcome, log, target). Every collaborator is a recording stand-in; opts choose what
    they do: phase, problems, plan, plan_error, resolve, resolve_error, point_error, board_fail,
    board_error, restart (a problem string, an exception to raise, or None), dry_run, undone,
    requirements_changed."""
    def go(**opts):
        log = []
        target = Target("beta", "develop-beta", "b" * 40)
        record_from = {"sha": "a" * 40, "requirements_changed": opts.get("requirements_changed", True)}
        board = _Board(log, opts.get("board_fail"), opts.get("board_error"))
        updater = Updater(board, state=_State(log, opts.get("phase", "idle")), gh=None,
                          installed_version="2.0.0", config_path="/nowhere/config.json", notify=lambda *a: None)

        def preflight():
            log.append("preflight")
            return list(opts.get("problems", ()))

        def plan_(channel):
            log.append(("plan", channel))
            _maybe_raise(opts.get("plan_error"))
            return opts.get("plan", (target, None))

        def resolve_(t):
            log.append(("resolve", t))
            _maybe_raise(opts.get("resolve_error"))
            return opts.get("resolve")

        def point(record, t):
            log.append(("rollback point", t))
            _maybe_raise(opts.get("point_error"))
            record["from"] = record_from
            return record

        def restart_():
            log.append("restart and check")
            return _maybe_raise(opts.get("restart"))

        def roll_back(record, problem):
            log.append(("roll back", problem))
            return opts.get("undone", Outcome(ROLLED_BACK, f"rolled back to x: {problem}"))

        updater.preflight, updater.plan, updater._resolve = preflight, plan_, resolve_
        updater._take_rollback_point, updater._restart_and_check, updater._roll_back = point, restart_, roll_back
        monkeypatch.setattr(update_module, "debug", _Debug(log))
        monkeypatch.setattr(states, "remember_good", lambda record, sha: log.append(("remember_good", sha)))
        outcome = updater._update("beta", dry_run=opts.get("dry_run", False))
        return outcome, log, target
    return go


def test_pin_an_unfinished_update_blocks_before_anything_else(run):
    outcome, log, _ = run(phase="switched")
    assert log == ["load"]
    assert outcome == Outcome(BLOCKED, "an earlier update didn't finish (it stopped at switched): "
                                       "roll it back first (python3 -m self_update rollback)")


def test_pin_preflight_problems_still_ask_the_plan_and_are_all_reported(run):
    outcome, log, _ = run(problems=["low disk", "a show is playing"], plan_error=github.GitHubError("offline"))
    assert log == ["load", "preflight", ("plan", "beta")]
    assert outcome == Outcome(BLOCKED, "low disk; a show is playing; offline")


def test_pin_preflight_problems_block_even_when_the_plan_is_fine(run):
    outcome, log, _ = run(problems=["low disk"])
    assert log == ["load", "preflight", ("plan", "beta")]
    assert outcome == Outcome(BLOCKED, "low disk")


def test_pin_a_github_error_alone_blocks(run):
    outcome, log, _ = run(plan_error=github.GitHubError("rate limited"))
    assert log == ["load", "preflight", ("plan", "beta")] and outcome == Outcome(BLOCKED, "rate limited")


def test_pin_nothing_to_install_returns_the_plans_outcome_untouched(run):
    waiting = Outcome(WAITING, "CI not done", runs=[1])
    outcome, log, _ = run(plan=(None, waiting))
    assert log == ["load", "preflight", ("plan", "beta")] and outcome is waiting


def test_pin_a_failed_resolve_blocks_with_the_commands_message(run):
    outcome, log, target = run(resolve_error=CommandFailed("fetch failed"))
    assert log == ["load", "preflight", ("plan", "beta"), ("resolve", target)]
    assert outcome == Outcome(BLOCKED, "fetch failed")


def test_pin_a_resolve_that_stops_returns_its_outcome(run):
    stop = Outcome(CURRENT, "already there")
    outcome, log, target = run(resolve=stop)
    assert log == ["load", "preflight", ("plan", "beta"), ("resolve", target)] and outcome is stop


def test_pin_a_dry_run_says_what_it_would_do_and_takes_no_rollback_point(run):
    outcome, log, target = run(dry_run=True)
    assert log == ["load", "preflight", ("plan", "beta"), ("resolve", target)]
    assert outcome == Outcome(WOULD_UPDATE, f"would update to develop-beta ({'b' * 7})", target=target)


@pytest.mark.parametrize("error", [CommandFailed("git broke"), OSError("disk full")])
def test_pin_a_failed_rollback_point_blocks_and_changes_nothing(run, error):
    outcome, log, target = run(point_error=error)
    assert log == ["load", "preflight", ("plan", "beta"), ("resolve", target), ("rollback point", target)]
    assert outcome == Outcome(BLOCKED, f"couldn't take a rollback point, so nothing changed: {error}")


def test_pin_a_healthy_update_walks_every_phase_and_remembers_the_commit(run):
    outcome, log, target = run(restart=None)
    sha = "b" * 40
    assert log == [
        "load", "preflight", ("plan", "beta"), ("resolve", target), ("rollback point", target),
        ("info", f"Updating from {'a' * 7} to develop-beta ({'b' * 7})."),
        ("checkout", sha),
        ("set_phase", "switched", {}),
        ("install", False),  # requirements changed: not skipped
        ("set_phase", "installed", {}),
        ("set_phase", "checking", {}),
        "restart and check",
        ("remember_good", sha),
        ("set_phase", "updated", {"reason": None}),
        ("info", f"Updated to develop-beta ({'b' * 7}); it passed its health check."),
    ]
    assert outcome == Outcome(UPDATED, f"updated to develop-beta ({'b' * 7})")


def test_pin_pip_is_skipped_when_requirements_did_not_change(run):
    _, log, _ = run(requirements_changed=False)
    assert ("install", True) in log and ("install", False) not in log


@pytest.mark.parametrize("fail_on, upto", [("checkout", ["checkout"]), ("install", ["checkout", "switched", "install"])])
def test_pin_a_failed_step_rolls_back_with_the_commands_message(run, fail_on, upto):
    outcome, log, target = run(board_fail=fail_on, board_error=CommandFailed(f"{fail_on} failed"))
    steps = [e[1] if e[0] == "set_phase" else e[0] for e in log[6:] if isinstance(e, tuple)]
    assert steps[:len(upto)] == upto
    assert log[-2:] == [
        ("error", f"The update to develop-beta ({'b' * 7}) failed: {fail_on} failed. Rolling back."),
        ("roll back", f"{fail_on} failed"),
    ]
    assert "restart and check" not in log and ("remember_good", "b" * 40) not in log
    assert outcome == Outcome(ROLLED_BACK, f"rolled back to x: {fail_on} failed", ok=False)


def test_pin_an_unhealthy_restart_rolls_back_with_the_health_problem(run):
    outcome, log, _ = run(restart="the app crashed")
    assert log[-2:] == [("error", f"The update to develop-beta ({'b' * 7}) failed: the app crashed. Rolling back."),
                          ("roll back", "the app crashed")]
    assert not any(e[0] == "set_phase" and e[1] == "updated" for e in log if isinstance(e, tuple))
    assert outcome.ok is False


def test_pin_a_command_failure_from_the_restart_is_its_message(run):
    outcome, log, _ = run(restart=CommandFailed("systemctl failed"))
    assert ("roll back", "systemctl failed") in log
    assert not any(e[0] == "exception" for e in log if isinstance(e, tuple))


def test_pin_any_other_error_is_logged_with_its_traceback_and_rolled_back(run):
    outcome, log, _ = run(restart=RuntimeError("weird"))
    assert ("exception", "The update failed unexpectedly.") in log
    assert ("roll back", "the update failed unexpectedly: weird") in log
    assert log.index(("exception", "The update failed unexpectedly.")) < log.index(
        ("roll back", "the update failed unexpectedly: weird"))


def test_pin_the_outcome_of_a_failed_rollback_is_carried_with_ok_false(run):
    failed = Outcome(ROLLBACK_FAILED, "rolling back failed")
    outcome, _, _ = run(restart="bad", undone=failed)
    assert outcome == Outcome(ROLLBACK_FAILED, "rolling back failed", ok=False)
