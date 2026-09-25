# tests/display/fireworks/test_fireworks.py
import math
import random

import pytest

import display.fireworks.fireworks as fireworks
from display.fireworks.fireworks import FireworksShow, castle_sprite, render_castle_fireworks


def _run(show, frames):
    for _ in range(frames):
        show.step()


@pytest.mark.parametrize("board_height, expected", [(32, (23, 20)), (64, (46, 40))])
def test_castle_sprite_scales_with_board_height(board_height, expected):
    pixels, w, h = castle_sprite(board_height)
    assert (w, h) == expected
    assert all(0 <= dx < w and 0 <= dy < h for dx, dy, _ in pixels)


def _sprite_rows(board_height):
    pixels, w, h = castle_sprite(board_height)
    kinds = {(x, y): k for x, y, k in pixels}
    return [''.join(kinds.get((x, y), '.') for x in range(w)) for y in range(h)]


def test_small_castle_matches_the_art_exactly():
    assert _sprite_rows(32) == fireworks._CASTLE_ART


def test_big_castle_door_is_two_leds_taller_with_windows_raised_to_match():
    rows = _sprite_rows(64)
    door_rows = [y for y, r in enumerate(rows) if 'D' in r]
    assert door_rows == list(range(32, 40)), "8 LEDs tall: plain 2x would be 6"
    # Narrow top, wider body, same shape as the small castle's door.
    assert rows[32].count('D') == rows[33].count('D') == 6
    assert all(rows[y].count('D') == 10 for y in range(34, 40))
    main_wall = slice(10, 36)
    window_rows = [y for y in range(26, 40) if '.' in rows[y][main_wall]]
    assert window_rows == [28, 29]
    assert all('.' not in rows[y][main_wall] and 'D' not in rows[y] for y in (30, 31)), "wall gap above door"


@pytest.mark.parametrize("width, height", [(64, 32), (64, 64), (32, 32)])
def test_castle_sits_on_bottom_and_is_centered(width, height):
    show = FireworksShow(width, height, random.Random(1))
    assert show.castle_y + show.castle_h == height
    assert abs(show.castle_x - (width - show.castle_x - show.castle_w)) <= 1


@pytest.mark.parametrize("width, height", [(64, 32), (64, 64)])
def test_frames_stay_in_bounds_with_valid_colors(width, height):
    show = FireworksShow(width, height, random.Random(3))
    for _ in range(300):
        show.step()
        for (x, y), rgb in show.frame_pixels().items():
            assert 0 <= x < width and 0 <= y < height
            assert len(rgb) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)


def test_rockets_launch_and_burst_into_sparks():
    show = FireworksShow(64, 32, random.Random(5))
    show.step()
    assert show.rockets, "first step should launch a rocket"
    _run(show, 60)
    assert show.sparks, "rockets should have burst by now"


def test_sparks_expire_and_particle_count_stays_bounded():
    show = FireworksShow(64, 64, random.Random(9))
    peak = 0
    for _ in range(1000):
        show.step()
        peak = max(peak, len(show.sparks) + len(show.rockets))
    assert peak < 600
    show.frames_to_next_launch = 10 ** 6
    _run(show, 120)
    assert not show.sparks and not show.rockets


def test_castle_occludes_fireworks_behind_it():
    show = FireworksShow(64, 32, random.Random(2))
    show.rockets = []
    show.frames_to_next_launch = 10 ** 6
    dx, dy, kind = next(p for p in show.castle_pixels if p[2] == "Y")
    x, y = show.castle_x + dx, show.castle_y + dy
    show.sparks = [fireworks._Spark(x, y, 0, 0, 40, (255, 0, 0))]
    assert show.frame_pixels()[(x, y)] == fireworks._CASTLE_COLORS["Y"]


def test_burst_flash_tints_walls_then_fades():
    show = FireworksShow(64, 32, random.Random(4))
    show.frames_to_next_launch = 10 ** 6
    dx, dy, _ = next(p for p in show.castle_pixels if p[2] == "W")
    pos = (show.castle_x + dx, show.castle_y + dy)
    dark = show.frame_pixels()[pos]
    show._explode(fireworks._Rocket(10, 5, 0, -1, 5, (255, 0, 0)))
    lit = show.frame_pixels()[pos]
    assert lit[0] > dark[0]
    _run(show, 60)
    assert show.frame_pixels()[pos][0] < lit[0]


def _force_mickey(show, monkeypatch):
    monkeypatch.setattr(fireworks, "MICKEY_CHANCE", 1.0)
    show.rockets = []
    show.launch()
    show.frames_to_next_launch = 10 ** 6
    return show.rockets[0]


@pytest.mark.parametrize("width, height", [(64, 32), (64, 64)])
def test_mickey_rockets_leave_room_for_the_whole_shape(width, height, monkeypatch):
    for seed in range(50):
        show = FireworksShow(width, height, random.Random(seed))
        rocket = _force_mickey(show, monkeypatch)
        assert rocket.mickey
        reach = fireworks._MICKEY_HALF_WIDTH * show.mickey_radius
        assert reach <= rocket.x <= width - reach
        assert rocket.burst_y - fireworks._MICKEY_TOP * show.mickey_radius >= 0


@pytest.mark.parametrize("width, height", [(64, 32), (64, 64)])
def test_mickey_burst_forms_head_and_two_ears(width, height, monkeypatch):
    show = FireworksShow(width, height, random.Random(0))
    rocket = _force_mickey(show, monkeypatch)
    show._explode(rocket)
    assert show.sparks
    assert len({s.life for s in show.sparks}) == 1, "all sparks fade together so the shape holds"
    # Direction of travel is the shape: two ear lobes up-left and up-right, head below.
    upper_left = [s for s in show.sparks if s.vx < 0 and s.vy < -abs(s.vx) * 0.3]
    upper_right = [s for s in show.sparks if s.vx > 0 and s.vy < -abs(s.vx) * 0.3]
    below = [s for s in show.sparks if s.vy > 0]
    assert upper_left and upper_right and below
    assert abs(len(upper_left) - len(upper_right)) <= 1
    # Outline only: no spark's direction lands strictly inside another circle of the shape.
    travel = (1 - fireworks.DRAG ** (fireworks.MICKEY_LIFE * 0.6)) / (1 - fireworks.DRAG)
    speed = show.mickey_radius / travel
    for s in show.sparks:
        px, py = s.vx / speed, s.vy / speed
        inside = [c for c in fireworks._MICKEY_CIRCLES
                  if (px - c[0]) ** 2 + (py - c[1]) ** 2 < (c[2] - 0.1) ** 2]
        assert not inside


def test_mickey_bursts_expire_like_other_sparks(monkeypatch):
    show = FireworksShow(64, 64, random.Random(3))
    rocket = _force_mickey(show, monkeypatch)
    show._explode(rocket)
    show.rockets = []
    _run(show, fireworks.MICKEY_LIFE + 1)
    assert not show.sparks


def test_regular_rockets_still_launch_when_mickey_is_rare(monkeypatch):
    monkeypatch.setattr(fireworks, "MICKEY_CHANCE", 0.0)
    show = FireworksShow(64, 32, random.Random(1))
    for _ in range(20):
        show.launch()
    assert not any(r.mickey for r in show.rockets)


class FakeCanvas:
    def __init__(self):
        self.pixels = {}

    def Clear(self):
        self.pixels = {}

    def SetPixel(self, x, y, r, g, b):
        self.pixels[(x, y)] = (r, g, b)


class FakeMatrix:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.swaps = 0
        self.cleared = False
        self.last_frame = None

    def CreateFrameCanvas(self):
        return FakeCanvas()

    def SwapOnVSync(self, canvas):
        self.swaps += 1
        self.last_frame = dict(canvas.pixels)
        return FakeCanvas()

    def Clear(self):
        self.cleared = True


class FakeFont:
    def __init__(self, char_width, height, baseline):
        self.char_width, self.height, self.baseline = char_width, height, baseline

    def CharacterWidth(self, code):
        return self.char_width


class FakeColor:
    def __init__(self, r, g, b):
        self.rgb = (r, g, b)


def test_render_castle_fireworks_draws_every_frame(monkeypatch):
    monkeypatch.setattr(fireworks.time, "sleep", lambda s: None)
    monkeypatch.setattr(fireworks, "loaded_fonts", {})
    matrix = FakeMatrix(64, 32)
    render_castle_fireworks(matrix, duration=1.0, fps=30, rng=random.Random(8))
    assert matrix.swaps == 30
    assert matrix.last_frame, "frames should contain pixels"
    assert matrix.cleared


def test_title_alpha_waits_then_fades_in_and_holds():
    assert fireworks.title_alpha(0) == 0
    assert fireworks.title_alpha(fireworks.TITLE_DELAY_S) == 0
    mid = fireworks.title_alpha(fireworks.TITLE_DELAY_S + fireworks.TITLE_FADE_S / 2)
    assert mid == pytest.approx(0.5)
    samples = [fireworks.title_alpha(t / 10) for t in range(40)]
    assert samples == sorted(samples)
    assert fireworks.title_alpha(fireworks.TITLE_DELAY_S + fireworks.TITLE_FADE_S) == 1
    assert fireworks.title_alpha(60) == 1


@pytest.mark.parametrize("font, height", [(FakeFont(4, 6, 5), 32), (FakeFont(4, 6, 5), 64)])
def test_title_is_centered_above_the_castle(font, height):
    layout = fireworks.title_layout(font, 64, height)
    assert [text for _, _, text in layout] == list(fireworks.TITLE_LINES)
    for x, _, text in layout:
        w = len(text) * font.char_width
        assert x >= 0 and x + w <= 64
        assert abs(x - (64 - x - w)) <= 1
    castle_top = FireworksShow(64, height, random.Random(0)).castle_y
    last_baseline = layout[-1][1]
    assert last_baseline - font.baseline + font.height <= castle_top


def test_render_fades_title_in_over_the_scene(monkeypatch):
    drawn = []
    monkeypatch.setattr(fireworks.time, "sleep", lambda s: None)
    monkeypatch.setattr(fireworks, "loaded_fonts", {"title": FakeFont(4, 6, 5)})
    monkeypatch.setattr(fireworks, "graphics", type("G", (), {
        "Color": FakeColor,
        "DrawText": staticmethod(lambda canvas, font, x, y, color, text: drawn.append((color.rgb, text))),
    }))
    render_castle_fireworks(FakeMatrix(64, 32), duration=3.0, fps=10, rng=random.Random(1))
    assert drawn, "title should be drawn once the fade starts"
    text_draws = [(rgb, text) for rgb, text in drawn if rgb != (0, 0, 0)]
    outline_draws = [d for d in drawn if d[0] == (0, 0, 0)]
    assert len(outline_draws) == 8 * len(text_draws)
    reds = [rgb[0] for rgb, _ in text_draws]
    assert reds == sorted(reds)
    assert text_draws[-1][0] == fireworks.TITLE_RGB
    assert {text for _, text in text_draws} == set(fireworks.TITLE_LINES)


def test_title_outline_is_drawn_before_the_text(monkeypatch):
    calls = []
    monkeypatch.setattr(fireworks, "graphics", type("G", (), {
        "Color": FakeColor,
        "DrawText": staticmethod(lambda canvas, font, x, y, color, text: calls.append((x, y, color.rgb))),
    }))
    fireworks.draw_title(None, FakeFont(4, 6, 5), [(10, 5, "Hi")], 1.0)
    assert calls[-1] == (10, 5, fireworks.TITLE_RGB)
    assert {(x, y) for x, y, rgb in calls[:-1]} == {(10 + dx, 5 + dy) for dx, dy in fireworks._OUTLINE_OFFSETS}
    assert all(rgb == (0, 0, 0) for _, _, rgb in calls[:-1])

    calls.clear()
    fireworks.draw_title(None, FakeFont(4, 6, 5), [(10, 5, "Hi")], 0)
    assert calls == [], "nothing is drawn before the fade starts"
