"""CLAUDE.md loads in every Claude Code session, so it stays short and its pointers stay real."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
MAX_CHARS = 16_000  # about 4k tokens; feature detail belongs in docs/dev/<topic>.md


def test_claude_md_stays_short():
    size = len(CLAUDE_MD.read_text())
    assert size <= MAX_CHARS, (
        f"CLAUDE.md is {size} characters (limit {MAX_CHARS}): move feature detail into "
        "docs/dev/<topic>.md and leave a pointer line"
    )


def test_every_doc_claude_md_points_to_exists():
    paths = set(re.findall(r"`((?:docs|tests)/[\w./-]+\.(?:md|py))`", CLAUDE_MD.read_text()))
    assert paths, "expected pointers to docs/dev notes"
    assert sorted(p for p in paths if not (ROOT / p).is_file()) == []


def test_every_topic_note_is_listed_in_claude_md():
    listed = CLAUDE_MD.read_text()
    notes = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs" / "dev").glob("*.md"))
    assert notes and [n for n in notes if f"`{n}`" not in listed] == []
