import io
import json
import urllib.error

import pytest

import self_update.github as github
from self_update.github import GitHubError

SHA = "a" * 40


class Urlopen:
    """A fake urllib.request.urlopen: answers each URL from replies (an object, bytes or an exception)."""
    def __init__(self, replies):
        self.replies, self.urls = replies, []

    def __call__(self, request, timeout=None, context=None):
        self.urls.append(request.full_url)
        reply = next(v for k, v in self.replies.items() if request.full_url.endswith(k))
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(reply if isinstance(reply, bytes) else json.dumps(reply).encode())


def _replies(monkeypatch, replies):
    fake = Urlopen(replies)
    monkeypatch.setattr(github.urllib.request, "urlopen", fake)
    return fake


def test_releases_leave_out_drafts_and_pre_releases(monkeypatch):
    fake = _replies(monkeypatch, {"releases?per_page=30": [
        {"tag_name": "v2.2.0", "draft": True}, {"tag_name": "v2.1.0"}, {"tag_name": "v2.1.0-rc1", "prerelease": True},
        {"tag_name": "v2.0.0", "draft": False, "prerelease": False}, {"name": "no tag"}, "junk"]})
    assert github.releases() == ["v2.1.0", "v2.0.0"]
    assert fake.urls == [f"{github.API}/repos/{github.REPO}/releases?per_page=30"]


def test_a_branch_tip_is_its_commit(monkeypatch):
    _replies(monkeypatch, {"commits/develop-beta": {"sha": SHA}})
    assert github.branch_tip("develop-beta") == SHA


@pytest.mark.parametrize("reply", [{"sha": "nothex"}, {}, [], {"sha": None}])
def test_a_branch_tip_that_isnt_a_commit_is_an_error(monkeypatch, reply):
    _replies(monkeypatch, {"commits/develop-beta": reply})
    with pytest.raises(GitHubError, match="develop-beta's commit"):
        github.branch_tip("develop-beta")


def _runs(*runs):
    return {f"commits/{SHA}/check-runs?per_page=100": {"check_runs": list(runs)}}


def test_ci_passes_when_every_check_ended_well(monkeypatch):
    _replies(monkeypatch, _runs(
        {"name": "test (3.11)", "status": "completed", "conclusion": "success"},
        {"name": "test (3.13)", "status": "completed", "conclusion": "success"},
        {"name": "optional", "status": "completed", "conclusion": "skipped"}))
    assert github.ci_status(SHA) == (None, [("test (3.11)", "passed"), ("test (3.13)", "passed"), ("optional", "passed")])


@pytest.mark.parametrize("runs, why, states", [
    ((), "has no CI results", []),
    (({"name": "test (3.11)", "status": "in_progress", "conclusion": None},
      {"name": "test (3.13)", "status": "completed", "conclusion": "success"}), "still running (test (3.11))",
     [("test (3.11)", "running"), ("test (3.13)", "passed")]),
    (({"name": "test (3.11)", "status": "completed", "conclusion": "success"},
      {"name": "test (3.13)", "status": "completed", "conclusion": "failure"}), "didn't pass (test (3.13): failure)",
     [("test (3.11)", "passed"), ("test (3.13)", "failed")]),
    (({"status": "queued"},), "still running (?)", [("?", "running")]),
])
def test_ci_that_hasnt_passed_says_why_and_how_each_run_stands(monkeypatch, runs, why, states):
    _replies(monkeypatch, _runs(*runs))
    problem, found = github.ci_status(SHA)
    assert why in problem and found == states


@pytest.mark.parametrize("reply, why", [
    (urllib.error.HTTPError("u", 403, "rate limited", {}, io.BytesIO(b"")), "HTTP 403"),
    (urllib.error.URLError("no route to host"), "can't reach GitHub"),
    (TimeoutError("timed out"), "can't reach GitHub"),
    (b"<html>", "can't reach GitHub"),
])
def test_github_failures_are_github_errors(monkeypatch, reply, why):
    _replies(monkeypatch, {"releases?per_page=30": reply})
    with pytest.raises(GitHubError, match=why):
        github.releases()


def test_a_list_of_releases_that_isnt_a_list_is_an_error(monkeypatch):
    _replies(monkeypatch, {"releases?per_page=30": {"message": "Not Found"}})
    with pytest.raises(GitHubError, match="isn't a list"):
        github.releases()


def test_checks_that_arent_a_list_are_an_error(monkeypatch):
    _replies(monkeypatch, {f"commits/{SHA}/check-runs?per_page=100": {"message": "Not Found"}})
    with pytest.raises(GitHubError, match="checks"):
        github.ci_status(SHA)
