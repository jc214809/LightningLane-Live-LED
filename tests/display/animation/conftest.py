import pytest

# display.animation and the fakes are imported inside the fixtures, not up here: pytest loads a
# conftest before tests/stubs has swapped in its fake driver, and importing display.animation
# this early would pull in the real one (the LED emulator's web server).


@pytest.fixture(autouse=True)
def fake_graphics(monkeypatch):
    import display.animation as animation
    from tests.display.animation.support import FakeColor, _draw_line

    monkeypatch.setattr(animation.drawing, "graphics", type("G", (), {"Color": FakeColor, "DrawLine": staticmethod(_draw_line)}))
    monkeypatch.setattr(animation.time, "sleep", lambda s: None)
    animation._canvases.clear()
    animation._last_screen.clear()


@pytest.fixture
def clock(monkeypatch):
    import display.animation as animation
    from tests.display.animation.support import FakeClock

    c = FakeClock()
    monkeypatch.setattr(animation.time, "monotonic", c.monotonic)
    monkeypatch.setattr(animation.time, "sleep", c.sleep)
    return c
