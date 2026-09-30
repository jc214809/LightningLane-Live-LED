"""landmark_for, landmark_screen and the landmark title font."""

import random

import pytest

import display.landmarks as landmarks

from tests.display.landmarks.support import TITLE_CHAR_W, _pinned


@pytest.mark.parametrize("name, cls", [
    ("Magic Kingdom", landmarks.CastleLandmark),
    ("EPCOT", landmarks.SpaceshipEarthLandmark),
    ("Epcot", landmarks.SpaceshipEarthLandmark),
    ("Hollywood Studios", landmarks.TowerOfTerrorLandmark),
    ("Disney's Hollywood Studios", landmarks.TowerOfTerrorLandmark),
    ("Animal Kingdom", landmarks.TreeOfLifeLandmark),
    ("Cedar Point", None),
    ("", None),
    (None, None),
])
def test_landmark_for_matches_park_names_loosely(name, cls):
    assert landmarks.landmark_for(name) is cls


def test_a_party_swaps_in_its_own_landmark():
    assert landmarks.landmark_for("Magic Kingdom", "halloween") is landmarks.FriendlyJackOLanternLandmark
    assert landmarks.landmark_for("Magic Kingdom", None) is landmarks.CastleLandmark
    assert landmarks.landmark_for("Magic Kingdom", "not-a-party") is landmarks.CastleLandmark


def test_every_special_events_landmark_exists():
    for key, event in landmarks.SPECIAL_EVENTS.items():
        if not event.get("landmark"):
            continue
        cls = landmarks.landmark_for("Anywhere", key)
        assert isinstance(cls, type) and issubclass(cls, landmarks.Landmark), key


def test_an_event_without_a_landmark_keeps_the_parks_own():
    assert landmarks.landmark_for("Magic Kingdom", "christmas") is landmarks.CastleLandmark
    assert landmarks.landmark_for("EPCOT", "extended_evening") is landmarks.SpaceshipEarthLandmark


def _bdf_glyphs(path):
    """{char: (DWIDTH, BBX, bitmap rows)} from a BDF font."""
    glyphs, cur = {}, None
    for line in open(path):
        key, _, rest = line.strip().partition(" ")
        if key == "ENCODING":
            cur = {"code": int(rest), "rows": []}
        elif cur is not None and key == "DWIDTH":
            cur["dwidth"] = rest
        elif cur is not None and key == "BBX":
            cur["bbx"] = rest
        elif cur is not None and key == "ENDCHAR":
            glyphs[chr(cur["code"])] = (cur["dwidth"], cur["bbx"], tuple(cur["rows"]))
            cur = None
        elif cur is not None and key not in ("SWIDTH", "BITMAP", "STARTCHAR") and line.strip():
            cur["rows"].append(line.strip())
    return glyphs


def test_landmark_font_is_the_title_font_with_a_readable_n():
    import display.display as display
    for height in (32, 64):
        assert display.fonts()[height]["landmark_title"].endswith("4x6-landmark.bdf")
    legacy = _bdf_glyphs("assets/fonts/patched/4x6-legacy.bdf")
    landmark = _bdf_glyphs("assets/fonts/patched/4x6-landmark.bdf")
    assert {ch for ch in legacy if legacy[ch] != landmark[ch]} == {"N"}, "only N changes"
    dwidth, bbx, rows = landmark["N"]
    assert dwidth.split()[0] == "5" and bbx.split()[0] == "4", "4 pixels wide, with a gap after it"
    bits = [format(int(r, 16) >> 4, "04b") for r in rows]
    assert bits[1] == "1101" and bits[2] == "1011", "a diagonal from top left to bottom right"


def test_landmark_screen_draws_the_title_with_a_shadow(monkeypatch):
    class Font:
        baseline = 5

        def CharacterWidth(self, ch):
            return TITLE_CHAR_W

    class Canvas:
        def SetPixel(self, *a):
            pass

    calls = []
    monkeypatch.setitem(landmarks.loaded_fonts, "landmark_title", Font())
    monkeypatch.setattr(landmarks.graphics, "Color", lambda *rgb: rgb, raising=False)
    monkeypatch.setattr(landmarks.graphics, "DrawText",
                        lambda canvas, font, x, y, color, text: calls.append((x, y, color, text)), raising=False)
    pumpkin = _pinned("wink")(64, 64, random.Random(15))
    landmarks.landmark_screen(pumpkin)(Canvas(), 2.0)
    drawn = [c for c in calls if c[2] != landmarks.TITLE_SHADOW_RGB]
    shadows = [c for c in calls if c[2] == landmarks.TITLE_SHADOW_RGB]
    assert [c[3] for c in drawn] == [text for text, *_ in pumpkin.title(2.0)]
    assert [(x - 1, y - 1, text) for x, y, _, text in shadows] == [(x, y, text) for x, y, _, text in drawn]


def test_landmark_screen_draws_every_pixel_and_keeps_animating():
    class Canvas:
        def __init__(self):
            self.px = {}

        def SetPixel(self, x, y, r, g, b):
            self.px[(x, y)] = (r, g, b)

    scene = landmarks.TreeOfLifeLandmark(64, 32, random.Random(4))
    canvas = Canvas()
    assert landmarks.landmark_screen(scene)(canvas, 1.0) is True
    assert canvas.px == scene.frame(1.0)
