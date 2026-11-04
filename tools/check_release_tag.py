"""Checks a release tag against version.py: `python3 tools/check_release_tag.py v2.0.0`.

Run by .github/workflows/release.yml on every pushed v* tag, which makes the GitHub release only
when this passes. The settings page's updater (ROADMAP #17) lists releases, so a tag that doesn't
match the code it points at never becomes an installable version.
"""
import logging
import os
import re
import sys

VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "version.py")


def script_version(path=VERSION_FILE):
    """SCRIPT_VERSION from version.py, read as text (the tag's checkout, not whatever is importable)."""
    with open(path, encoding="utf-8") as f:
        found = re.search(r'^SCRIPT_VERSION\s*=\s*["\']([^"\']+)["\']', f.read(), re.MULTILINE)
    if not found:
        raise ValueError(f"no SCRIPT_VERSION in {path}")
    return found.group(1)


def tag_problem(tag, version):
    """Why the tag can't be a release of this version, or None."""
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        return f"{tag!r} isn't a release tag (vMAJOR.MINOR.PATCH)"
    if tag != f"v{version}":
        return f"{tag} doesn't match version.py's {version}: bump SCRIPT_VERSION or tag v{version}"
    return None


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        logging.error("usage: check_release_tag.py vX.Y.Z")
        return 2
    problem = tag_problem(args[0], script_version())
    if problem:
        logging.error(problem)
        return 1
    logging.info("%s matches version.py", args[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
