# tests/display/test_capture_glyphs.py
"""Pins what capture._glyphs makes of a BDF file, line kind by line kind and for every shipped font."""

import hashlib
import os

import pytest

from display import capture

REPO = os.path.join(os.path.dirname(__file__), "..", "..")

SYNTHETIC_BDF = """STARTFONT 2.1
FONT -test
ENCODING 99
CHARS 5
STARTCHAR before-any-glyph
ENCODING 65
DWIDTH 6 0
BBX 5 3 1 -1
BITMAP
A8
50
F8
ENDCHAR
STARTCHAR no-dwidth-or-bbx
ENCODING 66
BITMAP
ff
ENDCHAR
STARTCHAR unencoded
ENCODING -1 66
DWIDTH 4 0
BBX 1 1 0 0
BITMAP
80
ENDCHAR
STARTCHAR no-bitmap
ENCODING 67
DWIDTH 4 0
ENDCHAR
STARTCHAR wide-rows
ENCODING 68 3
DWIDTH 9 0
BBX 9 2 0 0
BITMAP
FF80

0000
ENDCHAR
ENDCHAR
"""

SYNTHETIC_GLYPHS = {
    65: (6, 3, 1, -1, ["10101000", "01010000", "11111000"], 5),
    66: (0, 0, 0, 0, [], 0),
    68: (9, 2, 0, 0, ["1111111110000000", "0000000000000000"], 9),
}

# sha256 prefixes of every shipped font's parsed glyph table, taken before _glyphs was split into steps
FONT_GLYPH_HASHES = {
    "10x20": "e7d3d5d3e78016b9",
    "4x6-landmark": "5b3915c561121212",
    "4x6-legacy": "dc7d1d557dc742bb",
    "4x6": "e3ae8d2652bbc70f",
    "5x7": "0b4a7fd4c8df4432",
    "5x8": "cdeb1b1a8df0a9a3",
    "6x10": "db9c9425deacc20b",
    "6x12": "86959efb0587a329",
    "6x13": "24bb2bfed4ce9912",
    "6x13B": "79f4b837bb7a3821",
    "6x13O": "5fc74c77095de04c",
    "6x9": "e134bcecc503affb",
    "7x13": "3b56785b2b56b943",
    "7x13B": "cfaae72179b1fb9d",
    "7x13O": "5c1896ef38b115dc",
    "7x14": "982e72ec6b13996c",
    "7x14B": "c05a16400849b7e9",
    "8x13": "74e447a80428581d",
    "8x13B": "4bc541df6de577a9",
    "8x13O": "860fd59378ffc5f0",
    "9x15": "eceb818e9d33a05c",
    "9x15B": "6cda338399cd161c",
    "9x18": "f88c587ae6b97ee0",
    "9x18B": "bd92fbda70b00521",
    "clR6x12": "f4bd63fdc0e0ef35",
    "helvR12": "b02aa3e949dfc869",
    "tom-thumb": "100eb6af72265f32",
}


def test_glyph_parsing_handles_every_kind_of_bdf_line(tmp_path):
    path = tmp_path / "odd.bdf"
    path.write_text(SYNTHETIC_BDF, encoding="latin-1")
    assert capture._glyphs(str(path)) == SYNTHETIC_GLYPHS
    assert capture._glyphs(str(path)) is capture._glyphs(str(path)), "parsed once, then cached"


@pytest.mark.parametrize("name", sorted(FONT_GLYPH_HASHES))
def test_every_shipped_font_parses_to_the_same_glyph_table(name):
    glyphs = capture._glyphs(os.path.join(REPO, "assets/fonts/patched", f"{name}.bdf"))
    digest = hashlib.sha256(repr(sorted(glyphs.items())).encode()).hexdigest()
    assert digest[:16] == FONT_GLYPH_HASHES[name]
