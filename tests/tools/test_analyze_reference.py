import importlib.util
import os
import shutil

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("analyze_reference", os.path.join(ROOT, "tools", "analyze_reference.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="the grid detection is the editor's JS core")
REFS = tool.REFERENCES


def test_every_reference_image_has_a_readme_row():
    missing = tool.missing_rows()
    assert missing == [], ("add a row to docs/references/README.md for each (measure with "
                           f"python3 tools/analyze_reference.py <image>): {missing}")


def test_every_readme_row_links_an_image_that_exists():
    with open(tool.README, encoding="utf-8") as f:
        linked = tool.readme_links(f.read())
    assert sorted(f for f in linked if not os.path.exists(os.path.join(REFS, f))) == []


def test_links_are_read_bare_in_angle_brackets_and_percent_encoded():
    text = ("| Reference | Character |\n|---|---|\n"
            "| [a.jpg](a.jpg) | A |\n| [b c.png](<b c.png>) | B |\n| [d e.jpg](d%20e.jpg) | D |\n"
            "Not a row: [x.png](x.png)\n")
    assert tool.readme_links(text) == {"a.jpg", "b c.png", "d e.jpg"}


@pytest.fixture
def refs(tmp_path):
    (tmp_path / "README.md").write_text("| [a.jpg](a.jpg) | A |\n")
    for name in ("a.jpg", "New One.PNG", "notes.txt"):
        (tmp_path / name).write_bytes(b"")
    return tmp_path


def test_missing_rows_names_only_images_without_a_row(refs):
    assert tool.missing_rows(str(refs)) == ["New One.PNG"], "a.jpg has a row, notes.txt isn't an image"


def test_missing_report_is_empty_when_every_image_has_a_row():
    assert tool.missing_report([]) == ""
    report = tool.missing_report(["New One.PNG"])
    assert "docs/references/New One.PNG" in report and "analyze_reference.py" in report


def test_the_hook_prints_the_missing_images_or_nothing(refs, monkeypatch, capsys):
    monkeypatch.setattr(tool, "REFERENCES", str(refs))
    assert tool.main(["--missing"]) == 0
    assert "New One.PNG" in capsys.readouterr().out
    (refs / "README.md").write_text("| [a.jpg](a.jpg) | A |\n| [New One.PNG](<New One.PNG>) | N |\n")
    assert tool.main(["--missing"]) == 0
    assert capsys.readouterr().out == ""


def test_the_hook_never_fails_the_session_over_a_missing_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(tool, "REFERENCES", str(tmp_path / "gone"))
    assert tool.main(["--missing"]) == 0


# What the README's table says today, for characters measured by hand.
@pytest.mark.parametrize("w, h, on_32, on_64", [
    (23, 28, "Yes", "Yes (2x too)"),               # Forky
    (26, 31, "Tight", "Yes (2x too)"),             # Tink
    (35, 30, "Tight", "Yes"),                      # Mike
    (26, 33, "No (1 row over)", "Yes"),            # Sulley
    (25, 34, "No (2 rows over)", "Yes"),           # Ralph
    (20, 64, "No (32 rows over)", "Tight"),        # Pooh and his balloon
    (67, 60, "No (3 columns too wide)", "No (3 columns too wide)"),  # Tigger and Pooh
    (74, 86, "No (10 columns too wide)", "No (10 columns too wide, 22 rows too tall)"),  # Tiana
])
def test_fits_match_the_readme(w, h, on_32, on_64):
    assert (tool.fits_64x32(w, h), tool.fits_64x64(w, h)) == (on_32, on_64)


def test_pieces_finds_each_character_and_ignores_stray_cells():
    block = ["AAAAAAA"] * 7
    rows = [b + "....." + b + "..B" for b in block] + ["." * 22]
    assert tool.pieces(rows) == [(7, 7), (7, 7)], "two 49-cell characters; the 7-cell strip is backdrop"
    assert tool.pieces(["..."]) == []


def _grid(period=13.0, score=.9):
    return {"period": period, "offset": 0, "score": score}


def _reading(rows, **kw):
    reading = {"turn": 0, "fx": _grid(), "fy": _grid(), "rows": rows, "colors": {"R": [220, 30, 40]},
               "extraColors": 0, "box": None, "lines": False}
    reading.update(kw)
    return reading


def test_draft_row_measures_the_character_and_lists_its_colours():
    row, notes = tool.draft_row("Forky.jpg", _reading(["R" * 23] * 28))
    assert row == "| [Forky.jpg](Forky.jpg) | TODO: who it shows | 23 x 28 | Yes | Yes (2x too) | Pattern mode reads it |"
    assert "13.0 x 13.0 px cells" in notes[0] and notes[-1] == "Colours: R #dc1e28"


def test_draft_row_says_how_the_editor_reads_it():
    row, notes = tool.draft_row("bead photo.jpg", _reading(["RR"] * 4, turn=8.5))
    assert row.startswith("| [bead photo.jpg](<bead photo.jpg>) |"), "a name with spaces goes in angle brackets"
    assert "Detect grid straightens it" in row and any("Turned 8.5 degrees" in n for n in notes)
    row, _ = tool.draft_row("sheet.png", _reading(["RR"] * 4, box=[0, 0, 9, 9], lines=True))
    assert row.endswith("| Pattern mode: drag a box round it, tick Grid lines only |")


def test_draft_row_flags_a_sheet_for_one_row_per_character():
    block = ["R" * 8] * 8
    _, notes = tool.draft_row("sheet.png", _reading([b + "...." + b for b in block]))
    assert any("2 separate pieces (8 x 8, 8 x 8)" in n and "--box" in n for n in notes)


@pytest.mark.parametrize("reading", [
    {"fx": None, "fy": _grid()},                          # nothing repeats across
    {"fx": _grid(score=.05), "fy": _grid()},              # barely repeats: noise, not a grid
    {"fx": _grid(14.4), "fy": _grid(44.6, score=.35)},    # RC's enamel pin: cells three times taller than wide
])
def test_draft_row_falls_back_to_tracing_without_a_believable_grid(reading):
    row, notes = tool.draft_row("RC.webp", _reading(["RR"] * 4, **reading))
    assert "| | Needs tracing | Needs tracing |" in row and "Calibrate" in row
    assert "--box" in notes[0], "a sheet may still read character by character"


def test_draft_row_with_a_grid_but_nothing_on_it():
    row, notes = tool.draft_row("blank.png", _reading([]))
    assert row == "| [blank.png](blank.png) | TODO: who it shows | | | | |" and "nothing on it" in notes[0]


def test_a_missing_image_is_an_error_not_a_traceback(tmp_path, caplog):
    assert tool.main([str(tmp_path / "nope.png")]) == 1
    assert "nope.png" in caplog.text


def test_box_takes_four_numbers():
    assert tool._box("1,2,3.5,4") == [1, 2, 3.5, 4]
    with pytest.raises(Exception):
        tool._box("1,2,3")


@needs_node
def test_forky_is_measured_like_the_readme_by_hand(capsys):
    """Forky.jpg was measured by hand at 13 px cells, 23 x 28."""
    assert tool.main([os.path.join(REFS, "Forky.jpg"), "--art", "--name", "FORKY_ART", "--palette", "FORKY_COLORS"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("| [Forky.jpg](Forky.jpg) | TODO: who it shows | 23 x 28 | Yes | Yes (2x too) |")
    assert "13.0 x 13.0 px cells" in out
    assert '\nFORKY_ART = [\n    "' in out and "\nFORKY_COLORS = {\n" in out, "--art prints a sprite to paste"
    art = out.split("FORKY_ART = [\n")[1].split("]")[0].splitlines()
    assert len(art) == 28 and all(len(line.strip().strip('",')) == 23 for line in art)


@needs_node
def test_one_character_is_measured_from_a_box_on_a_sheet():
    reading = tool.read_image(os.path.join(REFS, "toy_story_4_sheet.png"), box=(435, 275, 665, 590), lines=True)
    rows = reading["rows"]
    assert abs(len(rows[0]) - 19) <= 1 and abs(len(rows) - 27) <= 1, "Woody, as the editor's test reads him"
    assert tool.grid_found(reading)


@needs_node
def test_a_whole_sheet_on_many_grids_is_not_measured_as_one():
    reading = tool.read_image(os.path.join(REFS, "Bullseye.jpg"))
    assert not tool.grid_found(reading), "each character needs its own --box"
