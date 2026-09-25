# tests/display/test_animation.py
import random

import pytest

import display.animation as animation


class FakeColor:
    def __init__(self, r, g, b):
        self.rgb = (r, g, b)


class FakeCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.px = {}

    def Clear(self):
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        self.px[(x, y)] = (r, g, b)


class FakeMatrix:
    def __init__(self, width=64, height=32):
        self.width, self.height = width, height
        self.canvases_created = 0
        self.frames = []

    def CreateFrameCanvas(self):
        self.canvases_created += 1
        return FakeCanvas(self.width, self.height)

    def SwapOnVSync(self, canvas):
        self.frames.append(dict(canvas.px))
        return FakeCanvas(self.width, self.height)


def _draw_line(canvas, x0, y0, x1, y1, color):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            canvas.SetPixel(x, y, *color.rgb)


@pytest.fixture(autouse=True)
def fake_graphics(monkeypatch):
    monkeypatch.setattr(animation, "graphics", type("G", (), {"Color": FakeColor, "DrawLine": staticmethod(_draw_line)}))
    monkeypatch.setattr(animation.time, "sleep", lambda s: None)
    animation._canvases.clear()
    animation._last_screen.clear()


def fill(rgb):
    def draw(canvas, t):
        for x in range(canvas.width):
            for y in range(canvas.height):
                canvas.SetPixel(x, y, *rgb)
        return False
    return draw


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, s):
        self.now += s


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(animation.time, "monotonic", c.monotonic)
    monkeypatch.setattr(animation.time, "sleep", c.sleep)
    return c


def test_run_frames_stops_redrawing_once_static_and_sleeps_out_the_rest(clock):
    matrix = FakeMatrix()
    calls = []
    animation.run_frames(matrix, lambda canvas, t: calls.append(t) or len(calls) < 5, duration_s=8)
    assert len(calls) == 5 == len(matrix.frames)
    assert clock.now == pytest.approx(8)


def test_slow_frames_do_not_stretch_the_screen(clock):
    matrix = FakeMatrix()

    def slow(canvas, t):
        clock.now += 0.1  # each frame takes 3x its budget
        return True

    animation.run_frames(matrix, slow, duration_s=8)
    assert clock.now == pytest.approx(8, abs=0.11)


def test_canvas_is_created_once_and_reused_across_screens():
    matrix = FakeMatrix()
    for _ in range(3):
        animation.show_screen(matrix, fill((255, 0, 0)), 1)
    assert matrix.canvases_created == 1


def test_first_screen_wipes_in_from_black():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((255, 0, 0)), 2)
    first = matrix.frames[0]
    assert all(first.get((x, 5)) in (None, (0, 0, 0)) for x in range(10, 64)), "right side still dark"
    assert matrix.frames[-1][(63, 5)] == (255, 0, 0)
    assert all(rgb != animation.EDGE_RGB for rgb in matrix.frames[-1].values()), "edge gone once revealed"


def test_next_screen_first_sweeps_the_previous_one_away():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((255, 0, 0)), 1)
    matrix.frames.clear()
    animation.show_screen(matrix, fill((0, 0, 255)), 2)
    first = matrix.frames[0]
    assert first[(60, 5)] == (255, 0, 0), "old screen still visible ahead of the sweep"
    assert matrix.frames[-1][(60, 5)] == (0, 0, 255)


def test_previous_screen_is_swept_away_as_it_was_last_shown():
    matrix = FakeMatrix()
    drawn_at = []

    def pulsing(canvas, t):
        drawn_at.append(t)
        return True

    animation.show_screen(matrix, pulsing, 1)
    last_shown = drawn_at[-1]
    drawn_at.clear()
    animation.show_screen(matrix, fill((0, 0, 255)), 1)
    assert drawn_at and set(drawn_at) == {last_shown}, "redrawn at a real, finite time"


def test_forget_screen_skips_the_sweep():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((255, 0, 0)), 1)
    animation.forget_screen(matrix)
    matrix.frames.clear()
    animation.show_screen(matrix, fill((0, 0, 255)), 2)
    assert (255, 0, 0) not in matrix.frames[0].values()


def test_screen_time_starts_after_the_reveal():
    matrix = FakeMatrix()
    seen = []
    animation.show_screen(matrix, lambda canvas, t: seen.append(t) or t < 0.5, 2)
    reveal_frames = int(animation.WIPE_S * animation.FPS)
    assert seen[:reveal_frames] == [0.0] * reveal_frames
    assert seen[reveal_frames + 3] > 0


FLYBYS = [animation.TinkReveal, animation.BuzzReveal]


@pytest.mark.parametrize("reveal_cls", FLYBYS)
@pytest.mark.parametrize("height", [32, 64])
def test_flyby_finishes_and_its_trail_settles(reveal_cls, height):
    reveal = reveal_cls(64, height, random.Random(1))
    canvas = FakeCanvas(64, height)
    frame = 0
    while reveal.overlay(canvas, frame / animation.FPS):
        frame += 1
        assert frame < 5 * animation.FPS, "reveal never ended"
    assert frame >= reveal.duration * animation.FPS
    assert not reveal.particles


@pytest.mark.parametrize("reveal_cls", FLYBYS)
def test_flyby_reveals_what_is_behind_the_character(reveal_cls):
    reveal = reveal_cls(64, 64, random.Random(2))
    canvas = FakeCanvas(64, 64)
    mid = reveal.duration / 2
    for f in range(int(mid * animation.FPS)):
        canvas.Clear()
        reveal.overlay(canvas, f / animation.FPS)
    canvas.Clear()
    fill((9, 9, 9))(canvas, 0)
    reveal.overlay(canvas, mid)
    assert canvas.px[(0, 0)] == (9, 9, 9), "left of the character is revealed"
    assert canvas.px[(63, 63)] == (0, 0, 0), "right of the character is still dark"


@pytest.mark.parametrize("reveal_cls", FLYBYS)
@pytest.mark.parametrize("height", [32, 64])
def test_flyby_crosses_the_whole_board_and_stays_vertically_on_it(reveal_cls, height):
    reveal = reveal_cls(64, height, random.Random(3))
    start_x, _ = reveal.position(0)
    end_x, _ = reveal.position(reveal.duration)
    assert start_x + reveal.sprite_w <= 0 and end_x >= 64, "enters and leaves off screen"
    for f in range(int(reveal.duration * animation.FPS)):
        _, y = reveal.position(f / animation.FPS)
        assert 0 <= y and y + reveal.sprite_h <= height


def test_buzz_climbs_and_trails_rocket_flame_behind_him():
    buzz = animation.BuzzReveal(64, 64, random.Random(4))
    _, y_start = buzz.position(0)
    _, y_end = buzz.position(buzz.duration)
    assert y_end < y_start, "to infinity: he climbs"
    x, y = buzz.position(0.5)
    flame = buzz.spawn(x, y)
    assert flame and all(p[0] < x and p[2] < 0 for p in flame), "flame starts behind him and streams backward"
    assert all(p[5] in buzz.flame_colors for p in flame)


def test_sprite_art_rows_are_even_and_use_defined_colors():
    for cls in FLYBYS:
        assert len({len(row) for row in cls.art}) == 1
        assert {ch for row in cls.art for ch in row} - {"."} <= set(cls.colors)


def test_ease_out_is_clamped_and_monotonic():
    samples = [animation.ease_out(p / 10) for p in range(-2, 13)]
    assert samples[0] == 0 and samples[-1] == 1
    assert samples == sorted(samples)
