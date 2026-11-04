"""A pull request's "## Release notes": what changes on the board, in words for the person who owns
it. The Updates card shows them for each pull request an update brings, read from the merge
commit's body (the repo merges with the PR's description as the commit message), so the board
needs no GitHub call to say what's new. CI refuses a pull request without them:

    PR_BODY="$(gh pr view 204 --json body -q .body)" python3 -m self_update.release_notes

Plain text, no imports beyond the standard library: CI runs it without the app's requirements.
"""
import logging
import os
import re
import sys

HEADING = re.compile(r"^#{1,6}\s+release notes\s*:?\s*$", re.IGNORECASE)
ANY_HEADING = re.compile(r"^#{1,6}\s")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
BULLET = re.compile(r"^(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?")
# What a pull request with nothing the owner would notice (CI, docs, tests) says instead.
NONE = re.compile(r"^(?:none|n/?a|nothing)\W*$", re.IGNORECASE)


def _lines(text):
    return COMMENT.sub("", text or "").replace("\r\n", "\n").split("\n")


def release_notes(body):
    """The notes in a PR description or merge commit body: None with no "## Release notes" section,
    [] when it says None (nothing the owner would notice), else its lines, bullets dropped. A
    section with nothing in it (the template's comment left alone) is None too."""
    lines, notes, inside = _lines(body), [], False
    for line in lines:
        text = line.strip()
        if HEADING.match(text):
            inside, notes = True, []
            continue
        if inside and ANY_HEADING.match(text):
            break
        if inside and text:
            notes.append(BULLET.sub("", text))
    if not notes:
        return None
    if len(notes) == 1 and NONE.match(notes[0]):
        return []
    return notes


def first_line(body):
    """The body's first plain line outside its release notes (not a heading, comment or blank),
    bullet dropped, or None: what to show for a merge without notes. A merge from before the notes
    has the PR's title there."""
    in_notes = False
    for line in _lines(body):
        text = line.strip()
        if ANY_HEADING.match(text):
            in_notes = bool(HEADING.match(text))
        elif text and not in_notes:
            return BULLET.sub("", text)
    return None


def problem(body, head_branch=None):
    """Why a pull request can't merge without saying what it changes, or None. A release (a merge of
    develop-beta, which carries pull requests that each have their own) needs none."""
    if head_branch == "develop-beta":
        return None
    if release_notes(body) is None:
        return ('add a "## Release notes" section to the description: what changes on the board, in a '
                'sentence for the person who owns it, or "None" if nothing they\'d notice')
    return None


def main(environ=os.environ):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    found = problem(environ.get("PR_BODY", ""), environ.get("PR_HEAD", ""))
    if found:
        logging.error("Release notes: %s", found)
        return 1
    logging.info("Release notes: present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
