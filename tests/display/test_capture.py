# tests/display/test_capture.py
import os
import types

import pytest

from display import capture

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
FONTS = sorted({path for height in (32, 64) for path in __import__("display.display", fromlist=["fonts"]).fonts()[height].values()})
TEXT = "Space Mountain 45 Mins - it's a small world! 9AM-11PM $15 *"


class NativeCanvas:
    """What rgbmatrix's compiled drawing functions accept."""

    def __init__(self):
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        self.px[(x, y)] = (r, g, b)


def pi_graphics():
    """A graphics module that behaves like rgbmatrix's on the Pi: its own canvas or a TypeError."""
    def only_native(name):
        def fn(canvas, *args):
            if not isinstance(canvas, NativeCanvas):
                raise TypeError(f"Argument 'c' has incorrect type (expected rgbmatrix.core.Canvas, got {type(canvas).__name__})")
        fn.__name__ = name
        return fn
    return types.SimpleNamespace(DrawText=only_native("DrawText"), DrawLine=only_native("DrawLine"),
                                 Color=lambda r, g, b: types.SimpleNamespace(red=r, green=g, blue=b))


@pytest.fixture
def on_a_pi(monkeypatch):
    fake = pi_graphics()
    monkeypatch.setattr(capture, "graphics", fake)
    font = object()
    monkeypatch.setitem(capture.font_paths, id(font), os.path.join(REPO, "assets/fonts/patched/5x8.bdf"))
    return fake, font


def test_a_screen_with_text_and_lines_can_be_captured_on_a_pi(on_a_pi):
    # The crash on the board: WALL-E redrew the old ride screen onto a recording canvas, and
    # rgbmatrix's DrawText refused it (TypeError: expected rgbmatrix.core.Canvas, got _Capture).
    graphics, font = on_a_pi

    def ride_screen(canvas, t):
        graphics.DrawText(canvas, font, 2, 10, graphics.Color(255, 255, 255), "Space Mountain")
        graphics.DrawLine(canvas, 0, 31, 30, 31, graphics.Color(40, 200, 60))

    px = capture.capture_screen(ride_screen, 0.0, 64, 32)
    assert sum(1 for rgb in px.values() if rgb == (255, 255, 255)) > 40, "the ride name was captured"
    assert [x for (x, y), rgb in px.items() if rgb == (40, 200, 60)] == list(range(31)), "and the wait bar"


def test_the_board_gets_its_own_drawing_back_after_a_capture(on_a_pi):
    graphics, font = on_a_pi
    native = graphics.DrawText, graphics.DrawLine
    capture.capture_screen(lambda c, t: graphics.DrawText(c, font, 0, 8, graphics.Color(1, 1, 1), "A"), 0.0, 64, 32)
    assert (graphics.DrawText, graphics.DrawLine) == native
    graphics.DrawText(NativeCanvas(), font, 0, 8, graphics.Color(1, 1, 1), "A")  # still the board's own


def test_a_screen_that_still_fails_gives_what_it_drew_instead_of_crashing(on_a_pi, monkeypatch):
    graphics, font = on_a_pi
    logged = []
    monkeypatch.setattr(capture.debug, "exception", lambda msg: logged.append(msg))

    def broken(canvas, t):
        canvas.SetPixel(1, 1, 9, 9, 9)
        raise RuntimeError("something new the capture can't draw")

    assert capture.capture_screen(broken, 0.0, 64, 32) == {(1, 1): (9, 9, 9)}
    assert logged, "logged, not swallowed"
    assert graphics.DrawText.__name__ == "DrawText", "restored even after a failure"


def test_text_in_a_font_that_was_never_registered_is_reported(on_a_pi, monkeypatch):
    graphics, _ = on_a_pi
    logged = []
    monkeypatch.setattr(capture.debug, "exception", lambda msg: logged.append(msg))
    capture.capture_screen(lambda c, t: graphics.DrawText(c, object(), 0, 8, graphics.Color(1, 1, 1), "A"), 0.0, 64, 32)
    assert logged


def test_fonts_are_registered_as_they_load(monkeypatch, tmp_path):
    import display.display as display_mod
    loaded = []

    class Font:
        def LoadFont(self, path):
            loaded.append(path)
    monkeypatch.setattr(display_mod, "graphics", types.SimpleNamespace(Font=Font))
    monkeypatch.setattr(display_mod, "loaded_fonts", {})
    display_mod.initialize_fonts(32)
    for name, font in display_mod.loaded_fonts.items():
        assert capture.font_paths[id(font)].endswith(display_mod.fonts()[32][name]), name


@pytest.mark.parametrize("path", FONTS)
def test_captured_text_matches_the_emulators_pixel_for_pixel(path):
    emulator = pytest.importorskip("RGBMatrixEmulator.graphics")
    font = emulator.Font()
    font.LoadFont(os.path.join(REPO, path))
    capture.font_paths[id(font)] = os.path.join(REPO, path)
    try:
        theirs, ours = capture.Capture(400, 40), capture.Capture(400, 40)
        color = emulator.Color(200, 100, 50)
        w_theirs = emulator.DrawText(theirs, font, 3, 20, color, TEXT)
        w_ours = capture.draw_text(ours, font, 3, 20, color, TEXT)
    finally:
        capture.font_paths.pop(id(font), None)
    assert ours.px == theirs.px
    assert w_ours == w_theirs


@pytest.mark.parametrize("line", [(0, 31, 63, 31), (5, 0, 5, 20), (0, 0, 20, 7), (30, 20, 2, 3), (4, 4, 4, 4)])
def test_captured_lines_match_the_emulators(line):
    emulator = pytest.importorskip("RGBMatrixEmulator.graphics")
    theirs, ours = capture.Capture(64, 32), capture.Capture(64, 32)
    color = emulator.Color(10, 20, 30)
    emulator.DrawLine(theirs, *line, color)
    capture.draw_line(ours, *line, color)
    assert ours.px == theirs.px


def test_capture_takes_images_like_the_weather_icon():
    from PIL import Image
    img = Image.new("RGB", (3, 2), (0, 0, 0))
    img.putpixel((1, 0), (250, 200, 10))
    shot = capture.Capture(64, 32)
    shot.SetPixel(11, 5, 1, 2, 3)  # under the icon's black: covered
    shot.SetImage(img, 10, 5)
    assert shot.px == {(11, 5): (250, 200, 10)}
