import subprocess

from version import SCRIPT_VERSION, version


def _run(code=0, out="", error=None):
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        if error:
            raise error
        return subprocess.CompletedProcess(args, code, out, "")
    run.calls = calls
    return run


def test_the_version_is_git_describe_without_the_v():
    run = _run(out="v2.1.5-beta\n")
    assert version("/app", run) == "2.1.5-beta"
    args, kwargs = run.calls[0]
    assert args == ["git", "-c", "safe.directory=/app", "describe", "--tags", "--match", "v[0-9]*"]
    assert kwargs["cwd"] == "/app", "the checkout, wherever it's run from"
    assert version("/app2", _run(out="v2.1.5-beta-3-g1a2b3c4\n")) == "2.1.5-beta-3-g1a2b3c4"


def test_without_git_or_a_tag_it_falls_back_to_the_typed_number():
    assert version("/no-tags", _run(code=128)) == SCRIPT_VERSION
    assert version("/no-git", _run(error=FileNotFoundError("git"))) == SCRIPT_VERSION
    assert version("/slow", _run(error=subprocess.TimeoutExpired("git", 10))) == SCRIPT_VERSION


def test_it_asks_git_once_per_checkout():
    run = _run(out="v2.2.0\n")
    assert version("/once", run) == version("/once", run) == "2.2.0"
    assert len(run.calls) == 1

