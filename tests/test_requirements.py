import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _requirements_txt():
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def _pyproject_dependencies():
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["dependencies"]


def test_requirements_txt_matches_pyproject_dependencies():
    assert sorted(_requirements_txt()) == sorted(_pyproject_dependencies())


def test_pillow_stays_below_12_for_rgbmatrix():
    # rgbmatrix's SetImage reads ImagingCore.unsafe_ptrs, which Pillow 12 removed; on a board
    # the first SetImage (the weather icon) crashed the service into a restart loop.
    for spec in (_requirements_txt(), _pyproject_dependencies()):
        pillow = next(req for req in spec if req.lower().startswith("pillow"))
        cap = re.search(r"<\s*(\d+)", pillow)
        assert cap and int(cap.group(1)) <= 12, pillow
