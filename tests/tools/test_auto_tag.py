import subprocess

import pytest

from tools import auto_tag
from tools.auto_tag import Tagger, main, newest_release, next_tag, release_notes, tag_for

TAGS = ["v1.1.0", "v2.0.0", "v2.0.1-beta", "v2.0.2-beta", "v1.1.7-beta", "nightly"]


def test_a_beta_counts_up_from_the_newest_release():
    assert next_tag("beta", TAGS) == "v2.0.3-beta"
    assert next_tag("beta", TAGS + ["v2.1.0"]) == "v2.1.1-beta", "a release starts its Betas again from 1"
    assert next_tag("beta", ["v2.0.0", "v2.0.9-beta", "v2.0.10-beta"]) == "v2.0.11-beta", "by number, not text"
    assert next_tag("beta", []) == "v0.0.1-beta"


def test_a_release_bumps_the_minor_version():
    assert next_tag("release", TAGS) == "v2.1.0", "the first: MIN_RELEASE, the first with the updater"
    assert next_tag("release", TAGS + ["v2.1.0", "v2.1.4-beta"]) == "v2.2.0"
    assert newest_release(["v2.10.0", "v2.9.0", "v3.0.0-beta"]) == "v2.10.0" and newest_release(["x"]) is None


def test_a_commit_that_has_its_tag_keeps_it():
    assert tag_for("beta", TAGS, ["v2.0.2-beta"]) == "v2.0.2-beta"
    assert tag_for("release", TAGS, ["v2.0.2-beta"]) == "v2.1.0", "a Beta tag isn't a release's"
    assert tag_for("release", TAGS + ["v2.1.0"], ["v2.1.0"]) == "v2.1.0"


def test_release_notes_list_each_pull_request_with_its_notes():
    changes = [(205, "Sparkle the castle", ["The castle sparkles.", "So do the rides."]),
               (204, "Faster CI", []), (203, "Old one", None), (None, "A straight commit", None), (202, "Docs", [])]
    assert release_notes(changes) == (
        "- Sparkle the castle (#205)\n  - The castle sparkles.\n  - So do the rides.\n"
        "- Old one (#203)\n- A straight commit\n\nBehind the scenes, nothing you'd notice: #204, #202\n")
    assert release_notes([]) == "No changes.\n"


class Git:
    """A fake subprocess.run for git: a remote whose tags another run can take first."""
    def __init__(self, tags, remote_taken=(), points_at=""):
        self.tags, self.remote_taken, self.points_at, self.calls = list(tags), set(remote_taken), points_at, []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        out, code = "", 0
        if args[1:3] == ["tag", "--list"]:
            out = "\n".join(self.tags)
        elif args[1:3] == ["tag", "--points-at"]:
            out = self.points_at
        elif args[1] == "fetch":
            self.tags += [t for t in self.remote_taken if t not in self.tags]
        elif args[1] == "push":
            tag = args[-1].removeprefix("refs/tags/")
            code = 1 if tag in self.remote_taken else 0
            self.remote_taken.add(tag)  # someone else's push shows up at the next fetch
        elif args[1] == "rev-parse":
            out = "parent\n"
        return subprocess.CompletedProcess(args, code, out, "rejected" if code else "")


def test_tagging_pushes_the_next_tag(tmp_path):
    git = Git(TAGS)
    assert Tagger(str(tmp_path), git).tag("beta", "abc1234") == "v2.0.3-beta"
    assert ["git", "fetch", "--force", "--tags", "origin"] in git.calls
    assert ["git", "tag", "--force", "v2.0.3-beta", "abc1234"] in git.calls
    assert git.calls[-1] == ["git", "push", "origin", "refs/tags/v2.0.3-beta"]


def test_a_number_another_merge_took_is_retried_with_the_next(tmp_path):
    git = Git(TAGS)
    git.remote_taken = set()
    original = git.__call__

    def taken_once(args, **kwargs):  # another run pushes v2.0.3-beta between our fetch and push
        if args[1] == "push" and not git.remote_taken:
            git.remote_taken.add("v2.0.3-beta")
        return original(args, **kwargs)
    tagger = Tagger(str(tmp_path), taken_once)
    assert tagger.tag("beta", "abc1234") == "v2.0.4-beta"
    assert ["git", "tag", "--delete", "v2.0.3-beta"] in git.calls


def test_a_rerun_pushes_the_tag_the_commit_has(tmp_path):
    git = Git(TAGS, points_at="v2.0.2-beta\n")
    assert Tagger(str(tmp_path), git).tag("beta", "abc1234") == "v2.0.2-beta"


def test_it_gives_up_after_a_few_tries(tmp_path):
    def always_taken(args, **kwargs):
        code = 1 if args[1] == "push" else 0
        return subprocess.CompletedProcess(args, code, "", "")
    with pytest.raises(RuntimeError, match="couldn't push"):
        Tagger(str(tmp_path), always_taken).tag("beta", "abc1234")


def test_a_failing_git_command_is_an_error(tmp_path):
    def broken(args, **kwargs):
        return subprocess.CompletedProcess(args, 128, "", "not a git repository")
    with pytest.raises(RuntimeError, match="not a git repository"):
        Tagger(str(tmp_path), broken).tag("beta", "abc1234")


def test_release_notes_cover_the_pull_requests_since_the_last_release(tmp_path, monkeypatch):
    seen = []

    class FakeBoard:
        def __init__(self, app_dir, run):
            pass

        def what_changed(self, old, new):
            seen.append((old, new))
            return [(210, "Auto tags", ["Versions come from tags."])]
    monkeypatch.setattr(auto_tag, "Board", FakeBoard)
    tagger = Tagger(str(tmp_path), Git(TAGS + ["v2.1.0"]))
    assert tagger.notes("v2.1.0", "m") == "- Auto tags (#210)\n  - Versions come from tags.\n"
    assert seen == [("v2.0.0", "m")], "since the release before, not the new one"
    Tagger(str(tmp_path), Git(["v2.1.0"])).notes("v2.1.0", "m")
    assert seen[-1] == ("parent", "m"), "the first release: since main's own parent"


class FakeTagger:
    def __init__(self, error=None):
        self.error = error

    def tag(self, kind, sha):
        if self.error:
            raise self.error
        return "v2.1.0" if kind == "release" else "v2.0.3-beta"

    def notes(self, tag, sha):
        return f"notes for {tag}\n"


def test_main_prints_the_tag_and_writes_a_releases_notes(tmp_path, capsys):
    notes = tmp_path / "notes.md"
    assert main(["release", "abc", "--notes", str(notes)], FakeTagger()) == 0
    assert capsys.readouterr().out == "v2.1.0\n" and notes.read_text() == "notes for v2.1.0\n"
    other = tmp_path / "beta.md"
    assert main(["beta", "abc", "--notes", str(other)], FakeTagger()) == 0
    assert capsys.readouterr().out == "v2.0.3-beta\n" and not other.exists(), "a Beta has no release"


def test_main_fails_without_a_tag(capsys):
    assert main(["beta", "abc"], FakeTagger(RuntimeError("couldn't push"))) == 1
    assert capsys.readouterr().out == ""


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def test_with_real_git_merges_get_betas_then_a_release_and_describe_reads_them(tmp_path):
    from version import version
    remote, work = tmp_path / "remote.git", tmp_path / "work"
    _git(tmp_path, "init", "--quiet", "--bare", str(remote))
    _git(tmp_path, "init", "--quiet", "-b", "develop-beta", str(work))
    for key, value in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
        _git(work, "config", key, value)
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "commit", "--quiet", "--allow-empty", "-m", "start")
    _git(work, "tag", "v2.0.0")

    def merge_pr(number, title, notes):
        _git(work, "checkout", "--quiet", "-b", f"f{number}")
        _git(work, "commit", "--quiet", "--allow-empty", "-m", "work")
        _git(work, "checkout", "--quiet", "develop-beta")
        _git(work, "merge", "--quiet", "--no-ff", f"f{number}", "-m", f"{title} (#{number})\n\n## Release notes\n{notes}")
        _git(work, "push", "--quiet", "origin", "develop-beta", "v2.0.0")
        return _git(work, "rev-parse", "HEAD")

    tagger = Tagger(str(work))
    first = merge_pr(1, "Sparkles", "- The castle sparkles.")
    assert tagger.tag("beta", first) == "v2.0.1-beta"
    assert tagger.tag("beta", first) == "v2.0.1-beta", "a rerun keeps it"
    assert tagger.tag("beta", merge_pr(2, "Faster CI", "None")) == "v2.0.2-beta"
    assert _git(remote, "tag", "--list") == "v2.0.0\nv2.0.1-beta\nv2.0.2-beta"
    version.cache_clear()
    assert version(str(work)) == "2.0.2-beta"

    _git(work, "checkout", "--quiet", "-b", "main", "v2.0.0")
    _git(work, "merge", "--quiet", "--no-ff", "develop-beta", "-m", "Release (#3)")
    release = _git(work, "rev-parse", "HEAD")
    assert tagger.tag("release", release) == "v2.1.0"
    assert tagger.notes("v2.1.0", release) == ("- Sparkles (#1)\n  - The castle sparkles.\n\n"
                                               "Behind the scenes, nothing you'd notice: #2\n")
    version.cache_clear()
    assert version(str(work)) == "2.1.0"
    _git(work, "checkout", "--quiet", "develop-beta")
    assert tagger.tag("beta", merge_pr(4, "Next", "None")) == "v2.1.1-beta"
