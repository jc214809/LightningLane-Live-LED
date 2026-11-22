"""Source files stay small enough to hold in your head (docs/dev/CODE-QUALITY.md).

Every tracked .py file outside tests/ is at most MAX_LINES long, except the files below, which were
already longer when the rule began. Each may shrink but not grow; when one shrinks, lower its cap
(this test says so), and when a split brings it under MAX_LINES, delete its entry.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 600

# path: the most lines it may have. Baseline measured 2026-11-22.
ALLOWED_LONG = {}


def _line_counts():
    """{path: line count} for every tracked source file outside tests/ (from `git ls-files`, any cwd)."""
    listed = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True)
    paths = [p for p in listed.stdout.splitlines() if not p.startswith("tests/")]
    return {p: len((ROOT / p).read_text().splitlines()) for p in paths if (ROOT / p).is_file()}


def test_source_files_stay_under_the_length_cap():
    counts = _line_counts()
    assert counts, "expected tracked source files"
    too_long = sorted(f"{p}: {n} lines (cap {ALLOWED_LONG.get(p, MAX_LINES)})"
                      for p, n in counts.items() if n > ALLOWED_LONG.get(p, MAX_LINES))
    assert too_long == [], "split these by feature (docs/dev/CODE-QUALITY.md), don't raise a cap"


def test_allowlisted_files_are_still_over_the_cap_and_their_caps_are_tight():
    counts = _line_counts()
    missing = sorted(p for p in ALLOWED_LONG if p not in counts)
    assert missing == [], f"allowlisted but no longer tracked: remove from ALLOWED_LONG: {missing}"
    loose = sorted(f"{p}: now {counts[p]} lines, cap {cap}: lower it to {counts[p]}"
                   if counts[p] > MAX_LINES else f"{p}: now {counts[p]} lines: delete its entry"
                   for p, cap in ALLOWED_LONG.items() if counts[p] < cap)
    assert loose == []
