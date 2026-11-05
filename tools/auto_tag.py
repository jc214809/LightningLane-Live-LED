"""Tags a merge with the next version, for .github/workflows/auto-tag.yml. Tags only: no workflow
commits, since a GITHUB_TOKEN push gets no CI run and the Beta channel installs only a tip whose
CI passed.

    python3 tools/auto_tag.py beta SHA                    # a pull request merged into develop-beta
    python3 tools/auto_tag.py release SHA --notes FILE    # develop-beta merged into main

beta tags vX.Y.(N+1)-beta: X.Y from the newest release, N the highest Beta for X.Y so far (after
v2.2.0 the first is v2.2.1-beta). release tags vX.(Y+1).0 and writes its release notes to FILE: the
pull requests since the last release with their "## Release notes" (self_update/release_notes.py),
as each board's Updates card shows them. A commit that already has its tag keeps it (a rerun), and
a tag someone else pushed first (two quick merges) is retried with the next number. Prints the tag.

Runs in CI without the app's requirements: the standard library and self_update.board only.
"""
import argparse
import logging
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from self_update.board import Board  # noqa: E402

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BETA, RELEASE = "beta", "release"
RELEASE_TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
BETA_TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)-beta")
PUSH_ATTEMPTS = 5
GIT_TIMEOUT_S = 120


def _releases(tags):
    return sorted(tuple(int(n) for n in found.groups()) for tag in tags if (found := RELEASE_TAG.fullmatch(tag)))


def newest_release(tags):
    """The newest vX.Y.Z tag, or None."""
    found = _releases(tags)
    return "v{}.{}.{}".format(*found[-1]) if found else None


def next_tag(kind, tags):
    """The next beta or release tag after tags (all the repo's)."""
    releases = _releases(tags)
    major, minor, _ = releases[-1] if releases else (0, 0, 0)
    if kind == RELEASE:
        return f"v{major}.{minor + 1}.0"
    betas = [int(found.group(3)) for tag in tags
             if (found := BETA_TAG.fullmatch(tag)) and (int(found.group(1)), int(found.group(2))) == (major, minor)]
    return f"v{major}.{minor}.{max(betas, default=0) + 1}-beta"


def tag_for(kind, tags, on_commit):
    """The commit's own tag of this kind if it has one (a rerun), else the next one."""
    pattern = BETA_TAG if kind == BETA else RELEASE_TAG
    mine = sorted(tag for tag in on_commit if pattern.fullmatch(tag))
    return mine[-1] if mine else next_tag(kind, tags)


def release_notes(changes):
    """A GitHub release's text from Board.what_changed's [(PR number, title, notes)]: each pull
    request with its notes, those whose notes say None in one closing line."""
    lines, hidden = [], []
    for number, title, notes in changes:
        if notes == [] and number:
            hidden.append(f"#{number}")
            continue
        lines.append(f"- {title}" + (f" (#{number})" if number else ""))
        lines += [f"  - {note}" for note in notes or ()]
    if hidden:
        lines += ["", f"Behind the scenes, nothing you'd notice: {', '.join(hidden)}"]
    return "\n".join(lines) + "\n" if lines else "No changes.\n"


class Tagger:
    def __init__(self, app_dir=APP_DIR, run=subprocess.run):
        self.app_dir, self._run = app_dir, run

    def git(self, *args, check=True):
        done = self._run(["git", *args], cwd=self.app_dir, capture_output=True, text=True, timeout=GIT_TIMEOUT_S)
        if check and done.returncode:
            raise RuntimeError(f"git {' '.join(args)} exited {done.returncode}: {(done.stderr or '').strip()}")
        return done

    def tags(self):
        return self.git("tag", "--list", "v*").stdout.split()

    def tag(self, kind, sha):
        """Tag sha and push the tag, retrying with the next number when another run took this one."""
        for _ in range(PUSH_ATTEMPTS):
            self.git("fetch", "--force", "--tags", "origin")
            tag = tag_for(kind, self.tags(), self.git("tag", "--points-at", sha).stdout.split())
            self.git("tag", "--force", tag, sha)
            if self.git("push", "origin", f"refs/tags/{tag}", check=False).returncode == 0:
                logging.info("Tagged %s %s", sha[:7], tag)
                return tag
            logging.warning("Couldn't push %s (another merge took it?): trying again", tag)
            self.git("tag", "--delete", tag)
        raise RuntimeError(f"couldn't push a {kind} tag for {sha[:7]} in {PUSH_ATTEMPTS} tries")

    def notes(self, tag, sha):
        """The release notes for tag on sha: what came in since the release before it, else since
        sha's first parent."""
        earlier = newest_release([t for t in self.tags() if t != tag])
        since = earlier or self.git("rev-parse", f"{sha}^").stdout.strip()
        return release_notes(Board(self.app_dir, run=self._run).what_changed(since, sha))


def main(argv=None, tagger=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    parser = argparse.ArgumentParser(description="Tag a merge with the next version.")
    parser.add_argument("kind", choices=(BETA, RELEASE))
    parser.add_argument("sha")
    parser.add_argument("--notes", help="release: write its release notes here")
    args = parser.parse_args(argv)
    tagger = tagger or Tagger()
    try:
        tag = tagger.tag(args.kind, args.sha)
        if args.kind == RELEASE and args.notes:
            with open(args.notes, "w", encoding="utf-8") as f:
                f.write(tagger.notes(tag, args.sha))
    except RuntimeError as e:
        logging.error("%s", e)
        return 1
    print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
