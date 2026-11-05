"""The board's side of an update: git, pip, the installer, systemd and the Pi's own state. Every
command goes through one run function (subprocess.run by default), so tests swap it for a fake.

The updater runs as root, but the checkout belongs to the user who cloned it (and pulls it by hand
over SSH), so git runs as that user: files git writes stay theirs.
"""
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys

from self_update.release_notes import first_line, release_notes
from utils.system_stats import THROTTLED_PATH

GIT_TIMEOUT_S = 120
PIP_TIMEOUT_S = 3 * 60 * 60  # a Pi Zero building a wheel takes ages
INSTALL_TIMEOUT_S = 3 * 60 * 60
SYSTEMCTL_TIMEOUT_S = 60
# The installer's flag for skipping pip; an installer older than the updater doesn't have it.
SKIP_REQUIREMENTS = "--skip-requirements"
# A pull request's merge commit, as GitHub titles it: "<PR title> (#N)" with the PR's description
# (and its release notes) as the body, since 2026-11-04; before, "Merge pull request #N from
# owner/branch" with the PR's title as the body.
PR_TITLED = re.compile(r"(.+) \(#(\d+)\)$")
PR_MERGE = re.compile(r"Merge pull request #(\d+) from \S+?/(\S+)")
# Merges of these branches carry other PRs (a release is develop-beta into main): those are listed
# instead. A PR-titled merge names no branch, so one is a release when it brings in other PRs' merges.
RELEASE_BRANCHES = ("develop-beta", "main")


class CommandFailed(Exception):
    """A command the update needed failed; the text says which and how (the end of its output)."""


class Board:
    def __init__(self, app_dir, run=subprocess.run, python=sys.executable, euid=os.geteuid):
        self.app_dir, self._run, self.python, self._euid = app_dir, run, python, euid

    def _command(self, args, timeout, check=True, **kwargs):
        try:
            done = self._run(args, cwd=self.app_dir, capture_output=True, text=True, timeout=timeout, **kwargs)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CommandFailed(f"{' '.join(args[:3])} failed: {e}") from None
        if check and done.returncode:
            tail = (done.stderr or done.stdout or "").strip().splitlines()[-5:]
            raise CommandFailed(f"{' '.join(args[:3])} exited {done.returncode}" + (f": {' / '.join(tail)}" if tail else ""))
        return done

    # git

    def _as_owner(self):
        """subprocess.run's user/group/env to run as the checkout's owner, when root and it isn't root's."""
        owner = os.stat(os.path.join(self.app_dir, ".git"))
        if self._euid() != 0 or owner.st_uid == 0:
            return {}
        home = pwd.getpwuid(owner.st_uid).pw_dir
        return {"user": owner.st_uid, "group": owner.st_gid, "env": {**os.environ, "HOME": home}}

    def git(self, *args, check=True, timeout=GIT_TIMEOUT_S):
        return self._command(["git", *args], timeout, check=check, **self._as_owner())

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def branch(self):
        """The checked-out branch, or None when HEAD is detached (as after an update)."""
        done = self.git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
        return done.stdout.strip() if done.returncode == 0 else None

    def changes(self):
        """Tracked files changed in the checkout, as git status lists them (untracked files don't count:
        config.json, venv and the logs live there)."""
        return self.git("status", "--porcelain", "--untracked-files=no").stdout.splitlines()

    def fetch(self):
        self.git("fetch", "--force", "--tags", "origin")

    def commit_of(self, ref):
        """The commit ref names, or None."""
        done = self.git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
        return done.stdout.strip() if done.returncode == 0 else None

    def tags_at(self, sha):
        """The tags on commit sha."""
        return self.git("tag", "--points-at", sha).stdout.split()

    def describe(self, sha):
        """sha's version from its tags, as version.py gives it ("2.2.0", "2.1.5-beta"), or None."""
        done = self.git("describe", "--tags", "--match", "v[0-9]*", sha, check=False)
        return done.stdout.strip().removeprefix("v") or None if done.returncode == 0 else None

    def file_at(self, sha, path):
        """path's text at commit sha, or None if it isn't there."""
        done = self.git("show", f"{sha}:{path}", check=False)
        return done.stdout if done.returncode == 0 else None

    def changed(self, old, new, path):
        """Whether path differs between commits old and new."""
        return self.git("diff", "--quiet", old, new, "--", path, check=False).returncode != 0

    def what_changed(self, old, new):
        """What's in commit new that isn't in old, newest first: [(PR number, title, notes)] for each
        pull request merged, or [(None, subject, None)] per commit when there are none (commits made
        straight on the branch). notes: release_notes() of the merge's body (None without any, as in
        merges from before them; [] for "None")."""
        merges = self.git("log", "--merges", "--format=%P%x1f%s%x1f%b%x1e", f"{old}..{new}").stdout
        found = []
        for entry in merges.split("\x1e"):
            parents, _, rest = entry.strip().partition("\x1f")
            subject, _, body = rest.partition("\x1f")
            merge, titled = PR_MERGE.match(subject), PR_TITLED.match(subject)
            if merge and merge.group(2) not in RELEASE_BRANCHES:
                found.append((int(merge.group(1)), first_line(body) or merge.group(2), release_notes(body)))
            elif titled and not merge and not self._carries_pull_requests(parents.split()):
                found.append((int(titled.group(2)), titled.group(1).strip(), release_notes(body)))
        if found:
            return found
        commits = self.git("log", "--no-merges", "--format=%s", f"{old}..{new}").stdout
        return [(None, line.strip(), None) for line in commits.splitlines() if line.strip()]

    def _carries_pull_requests(self, parents):
        """Whether a merge brings in other pull requests' merges: a release, not a pull request of its own."""
        if len(parents) < 2:
            return False
        merged = self.git("log", "--merges", "--format=%s", f"{parents[0]}..{parents[1]}").stdout.splitlines()
        return any(PR_MERGE.match(line) or PR_TITLED.match(line) for line in merged)

    def checkout(self, ref, detach=True):
        self.git("checkout", *(["--detach"] if detach else []), ref)

    # pip and the installer (as root, like the app)

    def pip_freeze(self):
        """pip freeze's pinned lines, without what pip can't reinstall from an index: the rgbmatrix
        driver (built from source by the installer) and anything installed from a path or URL."""
        lines = self._command([self.python, "-m", "pip", "freeze"], PIP_TIMEOUT_S).stdout.splitlines()
        return [line for line in lines if "==" in line and " @ " not in line and not line.startswith("-e")
                and not line.lower().startswith("rgbmatrix")]

    def pip_install(self, requirements_path):
        self._command([self.python, "-m", "pip", "install", "--prefer-binary", "-r", requirements_path], PIP_TIMEOUT_S)

    def install(self, skip_requirements):
        """The checked-out version's LLL-install.sh, as for a routine update by hand (-p -m), without the
        Wi-Fi setup step (-w); skip_requirements also skips pip, when the installer has the flag."""
        args = ["bash", "LLL-install.sh", "-p", "-m", "-w"]
        if skip_requirements and self.installer_skips_requirements():
            args.append(SKIP_REQUIREMENTS)
        self._command(args, INSTALL_TIMEOUT_S)

    def installer_skips_requirements(self):
        try:
            with open(os.path.join(self.app_dir, "LLL-install.sh"), encoding="utf-8") as f:
                return SKIP_REQUIREMENTS in f.read()
        except OSError:
            return False

    # systemd

    def systemctl_show(self, unit, prop):
        """A unit's property (NRestarts, ActiveState, LoadState), as text."""
        return self._command(["systemctl", "show", "--property", prop, "--value", unit],
                             SYSTEMCTL_TIMEOUT_S).stdout.strip()

    def unit_exists(self, unit):
        return self.systemctl_show(unit, "LoadState") == "loaded"

    def restart(self, unit):
        self._command(["systemctl", "restart", unit], SYSTEMCTL_TIMEOUT_S)

    def restarts(self, unit):
        """systemd's count of the unit's automatic restarts (a crash loop), or 0 if it can't say."""
        try:
            return int(self.systemctl_show(unit, "NRestarts") or 0)
        except ValueError:
            return 0

    def active(self, unit):
        return self.systemctl_show(unit, "ActiveState") == "active"

    # the Pi

    def free_bytes(self):
        return shutil.disk_usage(self.app_dir).free

    def throttled(self, path=THROTTLED_PATH):
        """The firmware's throttle flags, or None off a Pi (see utils.system_stats.describe)."""
        try:
            with open(path, encoding="utf-8") as f:
                return int(f.read().strip(), 16)
        except (OSError, ValueError):
            return None

    def port_answers(self, port, host="127.0.0.1", timeout=3):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False
