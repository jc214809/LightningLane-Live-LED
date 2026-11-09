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
@pytest.mark.parametrize("theme", [None, "halloween", "christmas"])
def test_frames_stay_in_bounds_with_valid_colors(width, height, theme):
    show = FireworksShow(width, height, random.Random(3), theme)
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


def test_render_can_leave_the_title_off(monkeypatch):
    drawn = []
    monkeypatch.setattr(fireworks.time, "sleep", lambda s: None)
    monkeypatch.setattr(fireworks, "loaded_fonts", {"title": FakeFont(4, 6, 5)})
    monkeypatch.setattr(fireworks, "graphics", type("G", (), {
        "Color": FakeColor,
        "DrawText": staticmethod(lambda canvas, font, x, y, color, text: drawn.append(text)),
    }))
    matrix = FakeMatrix(64, 32)
    render_castle_fireworks(matrix, duration=3.0, fps=10, rng=random.Random(1), title=False)
    assert drawn == [], "no title text at all"
    assert matrix.swaps == 30 and matrix.last_frame, "the castle and fireworks still play"


def test_halloween_show_has_a_purple_sky_flickering_orange_windows_and_party_bursts():
    show = FireworksShow(64, 64, random.Random(8), "halloween")
    theme = fireworks.THEMES["halloween"]
    frame = show.frame_pixels()
    r, g, b = frame[(40, 2)]
    assert b > r > g, "purple sky"
    windows = [(show.castle_x + dx, show.castle_y + dy) for dx, dy, kind in show.castle_pixels if kind == "Y"]
    assert windows and all(frame[p][0] > 150 and frame[p][0] > frame[p][1] > frame[p][2] for p in windows), "orange"
    later = FireworksShow(64, 64, random.Random(8), "halloween")
    _run(later, 3)
    assert any(later.frame_pixels()[p] != frame[p] for p in windows), "they flicker"
    _run(show, 400)
    allowed = set(theme["palette"]) | {fireworks.PUMPKIN_RGB, fireworks.PUMPKIN_FILL_RGB,
                                        fireworks.STEM_RGB, fireworks.FACE_RGB}
    assert {s.color for s in show.sparks} <= allowed, "bursts use only the party's colours"


@pytest.mark.parametrize("height", [32, 64])
def test_halloween_moon_sits_clear_of_the_castle(height):
    show = FireworksShow(64, height, random.Random(9), "halloween")
    castle = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, _ in show.castle_pixels}
    assert show.moon and not set(show.moon) & castle
    assert all(0 <= x < 64 and 0 <= y < height for x, y in show.moon)


def test_a_bat_flaps_across_the_sky():
    show = FireworksShow(64, 64, random.Random(10), "halloween")
    assert show.bats, "one bat starts on its way across the moon"
    xs, poses = [], set()
    for _ in range(40):
        show.step()
        bat = show.bats[0]
        xs.append(bat[0])
        pixels = show._bat_pixels(bat)
        poses.add(tuple((x - pixels[0][0], y - pixels[0][1]) for x, y in pixels))
        assert all(show.frame_pixels().get(p) == fireworks.BAT_RGB for p in pixels if 0 <= p[0] < 64 and 0 <= p[1] < 64)
    assert xs == sorted(xs) and xs[-1] > xs[0] + 10, "it flies across"
    assert len(poses) >= 2, "its wings flap"


@pytest.mark.parametrize("height", [32, 64])
def test_mickey_pumpkin_bursts_have_an_orange_outline_green_stem_and_a_face(height, monkeypatch):
    shape = "mickey_pumpkin"
    show = FireworksShow(64, height, random.Random(11), "halloween")
    monkeypatch.setattr(show, "_pick_shape", lambda: shape)
    show.rockets = []
    show.launch()
    rocket = show.rockets[0]
    assert rocket.shape == shape and not rocket.mickey
    reach = fireworks._MICKEY_HALF_WIDTH * show.shape_radius
    assert reach <= rocket.x <= 64 - reach and rocket.burst_y - fireworks._MICKEY_TOP * show.shape_radius >= 0
    assert rocket.burst_y + show.shape_radius <= show.castle_y + 3, "the face clears the castle"
    show.sparks = []
    show._explode(rocket)
    colors = [s.color for s in show.sparks]
    assert colors.count(fireworks.PUMPKIN_RGB) > colors.count(fireworks.FACE_RGB) > colors.count(fireworks.STEM_RGB) > 0
    assert colors.count(fireworks.PUMPKIN_FILL_RGB) > 0, "filled in"
    assert len({s.life for s in show.sparks}) == 1, "the shape holds together"
    stem = [s for s in show.sparks if s.color == fireworks.STEM_RGB]
    face = [s for s in show.sparks if s.color == fireworks.FACE_RGB]
    assert max(s.vy for s in stem) < min(s.vy for s in face), "stem on top, face below it"


@pytest.mark.parametrize("radius", [5, 9])  # the pumpkin's size on 64x32 and on 64x64
def test_mickey_pumpkin_head_is_filled_in_around_its_face_on_both_boards(radius):
    # The dark gap round the carved face once joined up on the small pumpkin and left its head
    # an outline and a face (8% filled); the old "any fill at all" check passed on the ears alone.
    points = fireworks._mickey_pumpkin_points(radius)
    led = lambda x, y: (round(x * radius), round(y * radius))
    fill = {led(x, y) for x, y, c in points if c == fireworks.PUMPKIN_FILL_RGB}
    face = {led(x, y) for x, y, c in points if c == fireworks.FACE_RGB}
    head = [(x, y) for x in range(-radius, radius + 1) for y in range(-radius, radius + 1)
            if x * x + y * y <= (radius - 1.5) ** 2 and (x, y) not in face]
    filled = sum(1 for p in head if p in fill) / len(head)
    assert filled > 0.45, f"only {filled:.0%} of the head round the face is filled"


def test_halloween_bursts_are_mickey_pumpkins_among_regular_fireworks():
    show = FireworksShow(64, 64, random.Random(12), "halloween")
    shapes = [show._pick_shape() for _ in range(2000)]
    assert set(shapes) == {"mickey_pumpkin", None}, "no plain pumpkins or plain Mickeys"
    assert 200 < shapes.count("mickey_pumpkin") < 400, "about as often as the everyday show's Mickeys"


def _burst(height, shape, seed=11):
    """A Christmas show's rocket of the given shape, launched and exploded at once: (show, rocket, sparks)."""
    show = FireworksShow(64, height, random.Random(seed), "christmas")
    show._pick_shape = lambda: shape
    show.rockets = []
    show.launch()
    rocket = show.rockets[0]
    show.sparks = []
    show._explode(rocket)
    return show, rocket, show.sparks


def test_halloween_frames_are_unchanged_by_the_shape_tables():
    # Hashes of 400 seeded frames, captured before the shape bursts were routed through _SHAPE_POINTS.
    import hashlib
    expected = {32: "c0360c55d0579a6c6d07a2015bd80423", 64: "b975ae621016f973207e068fdfa137dd"}
    for height, digest in expected.items():
        show = FireworksShow(64, height, random.Random(5), "halloween")
        h = hashlib.md5()
        for _ in range(400):
            show.step()
            h.update(repr(sorted(show.frame_pixels().items())).encode())
        assert h.hexdigest() == digest, height


@pytest.mark.parametrize("height", [32, 64])
def test_christmas_show_has_a_midnight_sky_red_roofs_and_steady_green_windows(height):
    show = FireworksShow(64, height, random.Random(8), "christmas")
    theme = fireworks.THEMES["christmas"]
    frame = show.frame_pixels()
    r, g, b = frame[(40, 2)] if height == 64 else frame[(40, 1)]
    assert b > g > r and b < 80, "midnight blue"
    colors = {kind: [(show.castle_x + dx, show.castle_y + dy) for dx, dy, k in show.castle_pixels if k == kind]
              for kind in "RYGW"}
    assert all(frame[p][0] > 140 and frame[p][1] < 60 for p in colors["R"]), "red roofs"
    assert all(frame[p] == theme["castle"]["Y"] for p in colors["Y"]) and theme["castle"]["Y"][1] > 200, "green windows"
    assert all(frame[p] == theme["castle"]["G"] for p in colors["G"]), "gold finials"
    windows = colors["Y"] + colors["G"]
    _run(show, 5)
    later = show.frame_pixels()
    assert all(later[p] == frame[p] for p in windows), "no flicker"
    assert not show.moon and not show.bats and not show.bats_on
    _run(show, 400)
    allowed = set(theme["palette"]) | {fireworks.ORNAMENT_RGB, fireworks.ORNAMENT_FILL_RGB, fireworks.CAP_RGB,
                                        fireworks.SHINE_RGB, fireworks.CANE_RED, fireworks.CANE_WHITE}
    assert {s.color for s in show.sparks} <= allowed, "bursts use only the party's colours"


def test_christmas_bursts_are_ornaments_and_candy_canes_among_regular_fireworks():
    show = FireworksShow(64, 64, random.Random(12), "christmas")
    shapes = [show._pick_shape() for _ in range(4000)]
    assert set(shapes) == {"mickey_ornament", "candy_cane", None}
    assert 240 < shapes.count("mickey_ornament") < 400, "about 8%"
    assert 200 < shapes.count("candy_cane") < 360, "about 7%"


@pytest.mark.parametrize("radius", [5, 9])  # the ornament's size on 64x32 and on 64x64
def test_mickey_ornament_has_a_red_outline_a_filled_head_a_gold_cap_and_a_shine(radius):
    points = fireworks._mickey_ornament_points(radius)
    count = lambda rgb: sum(1 for p in points if p[2] == rgb)
    assert count(fireworks.ORNAMENT_RGB) > count(fireworks.CAP_RGB) > 0
    assert count(fireworks.ORNAMENT_FILL_RGB) > count(fireworks.CAP_RGB), "filled in"
    assert 2 <= count(fireworks.SHINE_RGB) <= 4
    led = lambda x, y: (round(x * radius), round(y * radius))
    shine = {led(x, y) for x, y, c in points if c == fireworks.SHINE_RGB}
    assert all(x < 0 and y < 0 for x, y in shine), "upper left"
    fill = {led(x, y) for x, y, c in points if c == fireworks.ORNAMENT_FILL_RGB}
    assert not fill & shine, "a dark gap round the shine"
    cap = [(x, y) for x, y, c in points if c == fireworks.CAP_RGB]
    assert all(abs(x) < 0.3 and y < -0.95 for x, y in cap), "on top of the head, between the ears"
    head = [(x, y) for x in range(-radius, radius + 1) for y in range(-radius, radius + 1)
            if x * x + y * y <= (radius - 1.5) ** 2 and (x, y) not in shine]
    assert sum(1 for p in head if p in fill) / len(head) > 0.45


@pytest.mark.parametrize("height", [32, 64])
def test_ornament_burst_stays_on_the_board_and_clear_of_the_castle(height):
    show, rocket, sparks = _burst(height, "mickey_ornament")
    assert rocket.shape == "mickey_ornament" and rocket.color == fireworks.ORNAMENT_RGB
    reach = fireworks._MICKEY_HALF_WIDTH * show.shape_radius
    assert reach <= rocket.x <= 64 - reach and rocket.burst_y - fireworks._MICKEY_TOP * show.shape_radius >= 0
    assert rocket.burst_y + show.shape_radius <= show.castle_y + 3
    assert len({s.life for s in sparks}) == 1


@pytest.mark.parametrize("radius", [5, 9])
def test_candy_cane_is_striped_red_and_white_with_a_hook_over_the_top(radius):
    points = fireworks._candy_cane_points(radius)
    red = sum(1 for p in points if p[2] == fireworks.CANE_RED)
    white = sum(1 for p in points if p[2] == fireworks.CANE_WHITE)
    assert red + white == len(points) and min(red, white) / max(red, white) > 0.7, "near-equal stripes"
    stick_x = fireworks._CANE_X
    stick = [p for p in points if p[1] >= -1.0 and p[0] < stick_x + 0.3]
    assert max(p[1] for p in stick) - min(p[1] for p in stick) >= 1.8, "two head-radii tall"
    width = len({round(p[0] * radius) for p in stick})
    assert width == (3 if radius >= 6 else 2)
    hook = [p for p in points if p[1] < -1.0 - 0.5 / radius]
    assert hook and all(p[0] > stick_x - 0.3 for p in hook)
    assert max(p[0] for p in hook) > stick_x + 0.6, "curls over to the right"
    assert any(p[1] > -1.0 and p[0] > stick_x + 0.6 for p in points), "and a little way down"
    assert len({round(p[1] * radius) for p in stick if p[2] == fireworks.CANE_RED}) > 3, "bands, not a solid colour"


@pytest.mark.parametrize("height", [32, 64])
@pytest.mark.parametrize("seed", range(12))
def test_candy_cane_burst_stays_on_the_board_and_clear_of_the_castle(height, seed):
    show, rocket, sparks = _burst(height, "candy_cane", seed)
    assert rocket.shape == "candy_cane" and not rocket.mickey
    radius = show.shape_radius
    cx, cy = rocket.x, rocket.burst_y
    points = fireworks._shape_points("candy_cane", radius, rocket.tilt)
    xs = [cx + px * radius for px, _, _ in points]
    ys = [cy + py * radius for _, py, _ in points]
    assert min(xs) >= 0 and max(xs) <= 63 and min(ys) >= 0
    assert max(ys) <= show.castle_y + 3, "the foot clears the castle spire"


def test_candy_canes_burst_at_a_random_tilt_either_way_or_sideways_never_upside_down():
    tilts = {_burst(64, "candy_cane", seed)[1].tilt for seed in range(60)}
    assert tilts == set(fireworks._SHAPE_TILTS["candy_cane"])
    assert any(t < 0 for t in tilts) and any(0 < t < 90 for t in tilts) and 90 in tilts
    assert all(abs(t) <= 90 for t in tilts), "never upside down"
    # The sparks fly out along the tilted shape: a sideways cane is wider than it is tall.
    show, rocket, sparks = _burst(64, "candy_cane", 0)
    rocket.tilt = 90
    show.sparks = []
    show._explode(rocket)
    xs, ys = [s.vx for s in show.sparks], [s.vy for s in show.sparks]
    assert max(xs) - min(xs) > 1.5 * (max(ys) - min(ys))


def test_other_shapes_never_tilt():
    for shape in ("mickey_ornament", "mickey_pumpkin"):
        assert _burst(64, shape)[1].tilt == 0


@pytest.mark.parametrize("height", [32, 64])
def test_snow_stays_on_the_board_falls_and_wraps_to_the_top(height):
    show = FireworksShow(64, height, random.Random(3), "christmas")
    assert len(show.snow) == (64 // 4 if height == 64 else 64 // 6)
    ys = [f[1] for f in show.snow]
    show.step()
    assert all(f[1] > y for f, y in zip(show.snow, ys) if y + f[2] < height), "it falls"
    wrapped = False
    for _ in range(600):
        before = [f[1] for f in show.snow]
        show.step()
        wrapped = wrapped or any(f[1] < y for f, y in zip(show.snow, before))
        assert all(0 <= f[0] <= 64 and 0 <= f[1] < height for f in show.snow)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in show.frame_pixels())
    assert wrapped, "a flake that passes the bottom starts again at the top"
    assert any(show.frame_pixels().get((round(f[0] + math.sin(show.frame * 0.05 + f[3])), round(f[1])))
               == fireworks.SNOW_RGB for f in show.snow if show.castle_y > f[1]), "flakes are drawn"


def test_other_themes_have_no_snow_or_sleigh():
    for theme in (None, "halloween"):
        show = FireworksShow(64, 64, random.Random(1), theme)
        _run(show, 50)
        assert not show.snow and not show.sleighs


@pytest.mark.parametrize("height", [32, 64])
def test_a_sleigh_crosses_the_sky_and_another_comes_later_never_two_at_once(height):
    show = FireworksShow(64, height, random.Random(10), "christmas")
    assert len(show.sleighs) == 1, "one starts on its way across soon after the show starts"
    x0 = show.sleighs[0][0]
    seen_at = []
    for i in range(3000):
        show.step()
        assert len(show.sleighs) <= 1
        if show.sleighs:
            seen_at.append(i)
            sleigh = show.sleighs[0]
            assert sleigh[1] + len(show.sleigh_art) < show.castle_y, "clear of the castle"
    gaps = [i for i, j in zip(seen_at[1:], seen_at) if i - j > 1]
    assert gaps, "the first leaves the sky and a new one comes along later"
    assert x0 < 0, "entering from the left"


def test_the_sleigh_flies_and_is_drawn_over_the_sky_facing_the_way_it_goes():
    show = FireworksShow(64, 64, random.Random(10), "christmas")
    xs = []
    for _ in range(80):
        show.step()
        xs.append(show.sleighs[0][0])
    assert xs == sorted(xs) and xs[-1] > xs[0] + 20, "flies across"
    frame = show.frame_pixels()
    right = show._sleigh_pixels(show.sleighs[0])
    assert right and all(frame.get((x, y)) == rgb for x, y, rgb in right
                         if 0 <= x < 64 and 0 <= y < 64)
    left_sleigh = [show.sleighs[0][0], show.sleighs[0][1], -0.45]
    left = show._sleigh_pixels(left_sleigh)
    base = int(round(left_sleigh[0]))
    width = len(show.sleigh_art[0])
    rudolph = lambda pixels, x0: {x - x0 for x, y, c in pixels if c in (fireworks._NOSE_BRIGHT, fireworks._NOSE_DIM)}
    assert rudolph(right, base) and min(rudolph(right, base)) > width * 0.9, "Rudolph leads"
    assert rudolph(left, base) == {width - 1 - x for x in rudolph(right, base)}, "mirrored"
    assert {(x - base, y) for x, y, _ in left} == {(width - 1 - x + base, y) for x, y, _ in right}


def test_rudolphs_nose_blinks_slowly():
    show = FireworksShow(64, 64, random.Random(10), "christmas")
    noses = set()
    for _ in range(60):
        show.step()
        noses |= {c for _, _, c in show._sleigh_pixels(show.sleighs[0] if show.sleighs else [0, 0, 1])
                  if c in (fireworks._NOSE_BRIGHT, fireworks._NOSE_DIM)}
    assert noses == {fireworks._NOSE_BRIGHT, fireworks._NOSE_DIM}


def test_sleigh_art_rows_are_all_one_width_and_use_known_colours():
    for art in (fireworks._SLEIGH_ART_SMALL, fireworks._SLEIGH_ART_BIG):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) <= set(".N") | set(fireworks._SLEIGH_COLORS)


def test_sleigh_team_sizes_the_user_picked():
    # 64x32: Santa and two reindeer at 1x, big enough to read; 64x64: Santa and Rudolph doubled.
    small, big = fireworks._SLEIGH_ART_SMALL, fireworks._SLEIGH_ART_BIG
    assert len(small) == 8 and len(small[0]) > 32
    assert "".join(small).count("N") == 1 and "".join(small).count("n") == 1, "Rudolph red, the other black"
    assert big == ["".join(c * 2 for c in row) for row in fireworks._sleigh_team(1) for _ in range(2)]
    assert "n" not in "".join(big) and len(big[0]) <= 64
    # Every reindeer's nose sits at the end of its muzzle, in front of its head.
    for row in small:
        for nose in "Nn":
            if nose in row:
                i = row.index(nose)
                assert row[i - 2:i] == "BB" and row[i + 1:i + 2] in ("", ".")
    # Santa faces the way the sleigh flies: his face is in front of the hair at the back of his head.
    face_row = fireworks._SANTA_SLEIGH[3]
    assert face_row.index("W") < face_row.index("F")


@pytest.mark.parametrize("height", [32, 64])
def test_every_sleigh_clears_the_castle_spire(height):
    show = FireworksShow(64, height, random.Random(4), "christmas")
    for _ in range(4000):
        show.step()
        for sleigh in show.sleighs:
            assert 0 <= sleigh[1] and sleigh[1] + len(show.sleigh_art) < show.castle_y


def test_everyday_show_is_unchanged_on_black():
    show = FireworksShow(64, 32, random.Random(8))
    assert show.palette is fireworks._PALETTE and show.castle_colors == fireworks._CASTLE_COLORS
    assert len(show.frame_pixels()) < 64 * 32, "no sky fill"
