import subprocess
from types import SimpleNamespace

import pytest

import self_update.board as board_module
from self_update.board import Board, CommandFailed


class Run:
    """A fake subprocess.run: answers by the command's start, records every call."""
    def __init__(self, answers=None):
        self.answers, self.calls = answers or {}, []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        for start, answer in self.answers.items():
            if tuple(args[:len(start)]) == start:
                if isinstance(answer, Exception):
                    raise answer
                code, out = answer if isinstance(answer, tuple) else (0, answer)
                return subprocess.CompletedProcess(args, code, out, "boom" if code else "")
        return subprocess.CompletedProcess(args, 0, "", "")

    def args(self):
        return [args for args, _ in self.calls]


@pytest.fixture
def checkout(tmp_path):
    (tmp_path / ".git").mkdir()
    return tmp_path


def _board(checkout, answers=None, euid=1000):
    run = Run(answers)
    return Board(str(checkout), run=run, python="/app/venv/bin/python3", euid=lambda: euid), run


def test_git_runs_in_the_checkout_as_its_user_when_not_root(checkout):
    board, run = _board(checkout, {("git", "rev-parse", "HEAD"): "abc\n"})
    assert board.head() == "abc"
    args, kwargs = run.calls[0]
    assert kwargs["cwd"] == str(checkout) and "user" not in kwargs and kwargs["timeout"]


def test_git_as_root_runs_as_the_checkouts_owner(checkout, monkeypatch):
    monkeypatch.setattr(board_module.os, "stat", lambda path: SimpleNamespace(st_uid=1000, st_gid=1000))
    home = str(checkout.parent / "owner-home")
    monkeypatch.setattr(board_module.pwd, "getpwuid", lambda uid: SimpleNamespace(pw_dir=home))
    board, run = _board(checkout, euid=0)
    board.fetch()
    args, kwargs = run.calls[0]
    assert args == ["git", "fetch", "--force", "--tags", "origin"]
    assert kwargs["user"] == 1000 and kwargs["group"] == 1000 and kwargs["env"]["HOME"] == home


def test_a_root_owned_checkout_runs_git_as_root(checkout, monkeypatch):
    monkeypatch.setattr(board_module.os, "stat", lambda path: SimpleNamespace(st_uid=0, st_gid=0))
    board, run = _board(checkout, euid=0)
    board.git("status")
    assert "user" not in run.calls[0][1]


def test_branch_is_none_when_detached(checkout):
    board, _ = _board(checkout, {("git", "symbolic-ref"): (1, "")})
    assert board.branch() is None
    board, _ = _board(checkout, {("git", "symbolic-ref"): "develop-beta\n"})
    assert board.branch() == "develop-beta"


def test_tags_at_lists_a_commits_tags(checkout):
    board, run = _board(checkout, {("git", "tag"): "v2.1.0\nv2.1.0-rc\n"})
    assert board.tags_at("abc") == ["v2.1.0", "v2.1.0-rc"]
    assert run.args() == [["git", "tag", "--points-at", "abc"]]
    board, _ = _board(checkout, {("git", "tag"): ""})
    assert board.tags_at("abc") == []


def test_changes_list_tracked_files_only(checkout):
    board, run = _board(checkout, {("git", "status"): " M disney.py\n"})
    assert board.changes() == [" M disney.py"]
    assert "--untracked-files=no" in run.calls[0][0]


def test_commit_of_and_file_at_give_none_when_missing(checkout):
    board, _ = _board(checkout, {("git", "rev-parse"): (1, ""), ("git", "show"): (128, "")})
    assert board.commit_of("refs/tags/v9.9.9") is None
    assert board.file_at("abc", "self_update/__init__.py") is None
    board, run = _board(checkout, {("git", "rev-parse"): "def\n", ("git", "show"): "text"})
    assert board.commit_of("refs/tags/v2.1.0") == "def" and run.calls[0][0][-1] == "refs/tags/v2.1.0^{commit}"
    assert board.file_at("def", "version.py") == "text"


def test_changed_compares_one_file_between_commits(checkout):
    board, run = _board(checkout, {("git", "diff"): (1, "")})
    assert board.changed("a", "b", "requirements.txt") is True
    assert run.calls[0][0] == ["git", "diff", "--quiet", "a", "b", "--", "requirements.txt"]
    board, _ = _board(checkout)
    assert board.changed("a", "b", "requirements.txt") is False


def test_what_changed_lists_the_pull_requests_merged_but_not_release_merges(checkout):
    log = ("Merge pull request #201 from jc214809/feature/updates-card\x1fShow what an update brings\n\x1e\n"
           "Merge branch 'feature/updater' into feature/update-recovery\x1f\x1e\n"
           "Merge pull request #197 from jc214809/develop-beta\x1fRelease v2.0.0\x1e\n"
           "Merge pull request #200 from jc214809/feature/update-recovery\x1f\nRoll back at boot\n\nMore words\x1e\n")
    board, run = _board(checkout, {("git", "log", "--merges"): log})
    assert board.what_changed("a", "b") == [(201, "Show what an update brings"), (200, "Roll back at boot")]
    assert run.calls[0][0] == ["git", "log", "--merges", "--format=%s%x1f%b%x1e", "a..b"]


def test_with_no_pull_requests_what_changed_lists_the_commits(checkout):
    board, _ = _board(checkout, {("git", "log", "--merges"): "", ("git", "log", "--no-merges"): "Fix a typo\nBump it\n"})
    assert board.what_changed("a", "b") == [(None, "Fix a typo"), (None, "Bump it")]


def test_checkout_detaches_unless_going_back_to_a_branch(checkout):
    board, run = _board(checkout)
    board.checkout("abc")
    board.checkout("develop-beta", detach=False)
    assert run.args() == [["git", "checkout", "--detach", "abc"], ["git", "checkout", "develop-beta"]]


def test_a_failed_command_says_which_and_how(checkout):
    board, _ = _board(checkout, {("git", "checkout"): (1, "")})
    with pytest.raises(CommandFailed, match="git checkout --detach exited 1: boom"):
        board.checkout("abc")


@pytest.mark.parametrize("error", [OSError("no git"), subprocess.TimeoutExpired("git", 120)])
def test_a_command_that_cant_run_is_a_failure(checkout, error):
    board, _ = _board(checkout, {("git",): error})
    with pytest.raises(CommandFailed):
        board.fetch()


def test_the_freeze_leaves_out_what_pip_cant_reinstall(checkout):
    freeze = "aiohttp==3.11.13\nrgbmatrix==0.0.1\nfoo @ file:///tmp/foo\n-e git+https://x#egg=bar\nPillow==11.0.0\n"
    board, run = _board(checkout, {("/app/venv/bin/python3", "-m", "pip", "freeze"): freeze})
    assert board.pip_freeze() == ["aiohttp==3.11.13", "Pillow==11.0.0"]


def test_pip_install_uses_the_apps_python(checkout):
    board, run = _board(checkout)
    board.pip_install("/var/lib/lll-update/pip-freeze.txt")
    assert run.args() == [["/app/venv/bin/python3", "-m", "pip", "install", "--prefer-binary",
                           "-r", "/var/lib/lll-update/pip-freeze.txt"]]


def test_the_installer_skips_pip_only_when_it_has_the_flag(checkout):
    board, run = _board(checkout)
    (checkout / "LLL-install.sh").write_text("old installer, no such flag")
    board.install(skip_requirements=True)
    (checkout / "LLL-install.sh").write_text("-r | --skip-requirements)")
    board.install(skip_requirements=True)
    board.install(skip_requirements=False)
    assert run.args() == [["bash", "LLL-install.sh", "-p", "-m", "-w"],
                          ["bash", "LLL-install.sh", "-p", "-m", "-w", "--skip-requirements"],
                          ["bash", "LLL-install.sh", "-p", "-m", "-w"]]


def test_the_real_installer_has_the_flag():
    with open("LLL-install.sh") as f:
        assert board_module.SKIP_REQUIREMENTS in f.read()


def test_systemd_states(checkout):
    unit = "LightningLane-Live-LED.service"
    board, run = _board(checkout, {("systemctl", "show", "--property", "NRestarts"): "2\n",
                                   ("systemctl", "show", "--property", "ActiveState"): "active\n",
                                   ("systemctl", "show", "--property", "LoadState"): "not-found\n"})
    assert board.restarts(unit) == 2 and board.active(unit) is True and board.unit_exists("lll-settings.service") is False
    board.restart(unit)
    assert run.args()[-1] == ["systemctl", "restart", unit]
    board, _ = _board(checkout, {("systemctl", "show"): "[not set]\n"})
    assert board.restarts(unit) == 0


def test_throttle_flags_from_the_firmware(checkout, tmp_path):
    board, _ = _board(checkout)
    path = tmp_path / "get_throttled"
    assert board.throttled(str(path)) is None, "off a Pi"
    path.write_text("0x50005\n")
    assert board.throttled(str(path)) == 0x50005
    path.write_text("junk")
    assert board.throttled(str(path)) is None


def test_free_bytes_and_ports(checkout):
    board, _ = _board(checkout)
    assert board.free_bytes() > 0
    assert board.port_answers(1, timeout=0.2) is False
