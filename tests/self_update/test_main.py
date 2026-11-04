import pytest

import self_update.__main__ as cli
from self_update.update import Outcome
from utils import heartbeat


class FakeUpdater:
    def __init__(self, tmp_path, outcome=Outcome("updated", "updated to v2.2.0 (2222222)")):
        from self_update.state import State
        self.state, self.outcome, self.asked = State(str(tmp_path / "lll-update")), outcome, []
        self.installed_version, self.heartbeat_path, self.clock = "2.1.0", str(tmp_path / "health"), lambda: 1030.0
        self.board = type("B", (), {"head": lambda s: "a" * 40, "branch": lambda s: None})()

    def update(self, channel, dry_run=False):
        self.asked.append(("update", channel, dry_run))
        return self.outcome

    def rollback(self):
        self.asked.append(("rollback",))
        return self.outcome

    def recover(self):
        self.asked.append(("recover",))
        return self.outcome


@pytest.fixture(autouse=True)
def journal_only(monkeypatch):
    # main() takes the file handler off the app's logger; keep that to the test.
    monkeypatch.setattr(cli.debug, "file_handler", None)


ROOT, USER = (lambda: 0), (lambda: 1000)


@pytest.mark.parametrize("argv, asked", [
    (["update"], ("update", "releases", False)),
    (["update", "--channel", "beta"], ("update", "beta", False)),
    (["check", "--channel", "beta"], ("update", "beta", True)),
    (["rollback"], ("rollback",)),
    (["recover"], ("recover",)),
])
def test_commands(tmp_path, capsys, argv, asked):
    updater = FakeUpdater(tmp_path)
    assert cli.main(argv, updater=updater, euid=ROOT) == 0
    assert updater.asked == [asked]
    assert capsys.readouterr().out == "updated: updated to v2.2.0 (2222222)\n"


def test_update_rollback_and_recovery_keep_their_outcome_for_the_settings_page(tmp_path, capsys):
    updater = FakeUpdater(tmp_path, Outcome("rolled_back", "rolled back to 2.1.0: it crashed", ok=False))
    cli.main(["update", "--channel", "beta"], updater=updater, euid=ROOT)
    assert updater.state.load_outcome() == {"command": "update", "channel": "beta", "result": "rolled_back",
                                            "message": "rolled back to 2.1.0: it crashed", "ok": False, "at": 1030.0}
    updater.outcome = Outcome("blocked", "an update or rollback is already running")
    cli.main(["rollback"], updater=updater, euid=ROOT)
    assert updater.state.load_outcome()["command"] == "rollback" and updater.state.load_outcome()["channel"] is None


def test_a_check_or_a_boot_with_nothing_to_recover_leaves_the_last_outcome(tmp_path, capsys):
    updater = FakeUpdater(tmp_path, Outcome("would_update", "would update to v2.2.0 (2222222)"))
    cli.main(["check"], updater=updater, euid=ROOT)
    assert updater.state.load_outcome() is None
    updater.outcome = Outcome("nothing_to_undo", "no unfinished update (last: updated)")
    cli.main(["recover"], updater=updater, euid=ROOT)
    assert updater.state.load_outcome() is None
    cli.main(["rollback"], updater=updater, euid=ROOT)
    assert updater.state.load_outcome()["result"] == "nothing_to_undo", "asked by hand: it says so"


def test_a_failure_exits_1(tmp_path, capsys):
    updater = FakeUpdater(tmp_path, Outcome("rolled_back", "rolled back to 2.1.0: it crashed", ok=False))
    assert cli.main(["update"], updater=updater, euid=ROOT) == 1


def test_nothing_to_recover_is_the_usual_boot(tmp_path, capsys):
    updater = FakeUpdater(tmp_path, Outcome("nothing_to_undo", "no unfinished update (last: updated)"))
    assert cli.main(["recover"], updater=updater, euid=ROOT) == 0
    assert cli.main(["rollback"], updater=updater, euid=ROOT) == 1, "by hand, there was nothing to undo"


def test_update_and_rollback_need_root_but_check_doesnt(tmp_path, capsys):
    updater = FakeUpdater(tmp_path)
    assert cli.main(["update"], updater=updater, euid=USER) == 1
    assert cli.main(["rollback"], updater=updater, euid=USER) == 1
    assert cli.main(["recover"], updater=updater, euid=USER) == 1
    assert "needs root" in capsys.readouterr().err and updater.asked == []
    assert cli.main(["check"], updater=updater, euid=USER) == 0


def test_status(tmp_path, capsys):
    updater = FakeUpdater(tmp_path)
    record = updater.state.load()
    record.update(phase="rolled_back", reason="the app crashed", good=["b" * 40],
                  to={"ref": "v2.2.0", "sha": "c" * 40}, **{"from": {"version": "2.1.0", "sha": "a" * 40}})
    updater.state.save(record)
    heartbeat.beat(path=updater.heartbeat_path, clock=lambda: 1000.0)
    assert cli.main(["status"], updater=updater, euid=USER) == 0
    out = capsys.readouterr().out
    for text in ("Installed: 2.1.0 at aaaaaaa (detached)", "Last update: rolled_back", "to v2.2.0 (ccccccc), from 2.1.0",
                 "rolled back because: the app crashed", "Good commits: bbbbbbb", "Heartbeat: 30s ago"):
        assert text in out


def test_a_bad_channel_or_command_is_a_usage_error(tmp_path):
    for argv in (["update", "--channel", "nightly"], ["upgrade"], []):
        with pytest.raises(SystemExit) as exit_:
            cli.main(argv, updater=FakeUpdater(tmp_path), euid=ROOT)
        assert exit_.value.code == 2
