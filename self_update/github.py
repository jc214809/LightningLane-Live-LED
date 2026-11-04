"""What GitHub says is available: the releases (vX.Y.Z tags that tools/check_release_tag.py let
through) and develop-beta's tip with its CI result. Unauthenticated (60 calls an hour per board),
which is plenty for updates started by hand: one check is two or three calls.
"""
import json
import re
import ssl
import urllib.error
import urllib.request

import certifi

API = "https://api.github.com"
REPO = "jc214809/LightningLane-Live-LED"
TIMEOUT_S = 15
# A check run that ended in one of these doesn't hold an update back.
PASSING = ("success", "neutral", "skipped")
# A check run's state, as ci_status gives it.
RUNNING, PASSED, FAILED = "running", "passed", "failed"


class GitHubError(Exception):
    """GitHub couldn't be asked, or answered something unusable; the text says which."""


def _get(path):
    request = urllib.request.Request(f"{API}/repos/{REPO}/{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "LightningLane-Live-LED updater"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S,
                                    context=ssl.create_default_context(cafile=certifi.where())) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raise GitHubError(f"GitHub answered HTTP {e.code} for {path}") from None
    except (OSError, ValueError) as e:  # no network, a timeout, or a reply that isn't JSON
        raise GitHubError(f"can't reach GitHub ({e})") from None


def releases():
    """The release tags, as GitHub lists them (newest first), leaving out drafts and pre-releases."""
    found = _get("releases?per_page=30")
    if not isinstance(found, list):
        raise GitHubError("GitHub's list of releases isn't a list")
    return [r["tag_name"] for r in found if isinstance(r, dict) and isinstance(r.get("tag_name"), str)
            and not r.get("draft") and not r.get("prerelease")]


def branch_tip(branch):
    """The commit at the tip of branch."""
    found = _get(f"commits/{branch}")
    sha = found.get("sha") if isinstance(found, dict) else None
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise GitHubError(f"GitHub didn't give {branch}'s commit")
    return sha


def ci_status(sha):
    """(why sha's CI doesn't let it be installed (no checks, still running, a failure), or None if it
    passed; its runs as (name, RUNNING/PASSED/FAILED), as GitHub lists them)."""
    found = _get(f"commits/{sha}/check-runs?per_page=100")
    runs = found.get("check_runs") if isinstance(found, dict) else None
    if not isinstance(runs, list):
        raise GitHubError(f"GitHub didn't give {sha[:7]}'s checks")
    runs = [r for r in runs if isinstance(r, dict)]
    states = [(str(r.get("name") or "?"), RUNNING if r.get("status") != "completed"
               else PASSED if r.get("conclusion") in PASSING else FAILED) for r in runs]
    if not runs:
        return f"{sha[:7]} has no CI results", states
    running = [name for name, state in states if state == RUNNING]
    if running:
        return f"{sha[:7]}'s CI is still running ({', '.join(running)})", states
    failed = [f"{r.get('name', '?')}: {r.get('conclusion')}" for r in runs if r.get("conclusion") not in PASSING]
    if failed:
        return f"{sha[:7]}'s CI didn't pass ({', '.join(failed)})", states
    return None, states

