import math
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


def test_run_frames_reports_frames_drawn_and_time_spent_animating(clock):
    calls = []
    drawn, spent = animation.run_frames(FakeMatrix(), lambda canvas, t: calls.append(t) or len(calls) < 30, duration_s=8)
    assert drawn == 30 and drawn / spent == pytest.approx(animation.FPS), "a board that keeps up reports 30 fps"

    def slow(canvas, t):
        clock.now += 0.1
        return True

    drawn, spent = animation.run_frames(FakeMatrix(), slow, duration_s=2)
    assert drawn / spent == pytest.approx(10, rel=0.1), "a board three times too slow reports ~10 fps"


def test_character_transitions_log_their_frame_rate(clock, monkeypatch):
    logged = []
    monkeypatch.setattr(animation.debug, "info", logged.append)
    animation.show_screen(FakeMatrix(), fill((1, 2, 3)), 1.0, transition="baymax", rng=random.Random(0))
    animation.show_screen(FakeMatrix(), fill((1, 2, 3)), 1.0, transition="wipe")
    assert len(logged) == 1 and logged[0].startswith("baymax: 30 fps"), "only characters log, not every wipe"


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


def test_network_badge_is_drawn_over_every_frame_while_offline():
    from updater.shared import note_network_result
    note_network_result(False)
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((0, 0, 255)), 1)
    assert all(frame[(63, 31)] == (255, 0, 0) for frame in matrix.frames), "badge over the wipe and the screen"
    assert matrix.frames[-1][(56, 31)] == (0, 0, 255), "screen untouched outside the badge"


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


FLYBYS = [animation.TinkReveal, animation.FigmentReveal, animation.DumboReveal]


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


def test_tink_is_a_fairy_not_a_glyph_and_doubles_on_64x64():
    art = animation.TinkReveal.art
    assert (len(art[0]), len(art)) == (9, 8)
    cells = "".join(art)
    assert {"W", "Y", "S", "G"} <= set(cells), "wings, her bun, a face and the green dress"
    assert art[0].strip(".") == "Y", "her bun on top"
    for height, size in ((32, (9, 8)), (64, (18, 16))):
        tink = animation.TinkReveal(64, height, random.Random(1))
        assert (tink.sprite_w, tink.sprite_h) == size


def test_buzz_launches_from_below_hovers_then_blasts_off_the_top():
    for height in (32, 64):
        buzz = animation.BuzzReveal(64, height, random.Random(4))
        assert buzz.position(0)[1] >= height, "starts below the board"
        hover = buzz.position(buzz.RISE_S + buzz.HOVER_S / 2)[1]
        assert 0 <= hover and hover + buzz.sprite_h <= height, "hovers on the board"
        assert buzz.position(buzz.duration)[1] + buzz.sprite_h <= 0, "gone off the top"
        xs = {buzz.position(f / animation.FPS)[0] for f in range(int(buzz.duration * animation.FPS))}
        assert xs == {(64 - buzz.sprite_w) / 2}, "straight up the middle"
        ys = [buzz.position(buzz.RISE_S + buzz.HOVER_S + f / animation.FPS)[1] for f in range(int(buzz.BLAST_S * animation.FPS))]
        steps = [a - b for a, b in zip(ys, ys[1:])]
        assert steps == sorted(steps), "accelerating as he blasts off"


def test_buzz_uncovers_the_screen_from_the_bottom_up_behind_him():
    buzz = animation.BuzzReveal(64, 64, random.Random(2))
    canvas = FakeCanvas(64, 64)
    t = buzz.RISE_S + buzz.HOVER_S / 2
    fill((9, 9, 9))(canvas, 0)
    buzz.overlay(canvas, t)
    _, y = buzz.position(t)
    feet = int(y + buzz.sprite_h)
    assert canvas.px[(0, 63)] == (9, 9, 9), "below him is revealed"
    assert canvas.px[(0, 0)] == (0, 0, 0), "above him is still dark"
    assert feet < 63


@pytest.mark.parametrize("height", [32, 64])
def test_buzz_finishes_and_his_flame_settles(height):
    buzz = animation.BuzzReveal(64, height, random.Random(1))
    canvas = FakeCanvas(64, height)
    frame = 0
    while buzz.overlay(canvas, frame / animation.FPS):
        frame += 1
        assert frame < 5 * animation.FPS, "reveal never ended"
    assert frame >= buzz.duration * animation.FPS and not buzz.particles


def test_buzz_wings_snap_open_with_a_flash_as_he_hovers():
    buzz = animation.BuzzReveal(64, 32, random.Random(3))

    def drawn(t):
        canvas = FakeCanvas(64, 32)
        buzz._draw_sprite(canvas, t)
        return canvas.px

    before, after = drawn(buzz.RISE_S - 0.05), drawn(buzz.RISE_S + buzz.FLASH_S + 0.05)
    width = lambda px: max(x for x, _ in px) - min(x for x, _ in px)
    assert width(after) > width(before) + 6, "folded, then spread"
    assert buzz.FLASH_RGB in drawn(buzz.RISE_S + 0.02).values(), "a flash at the wing tips as they open"
    assert buzz.FLASH_RGB not in after.values()


def test_buzz_flame_streams_down_from_under_his_feet():
    buzz = animation.BuzzReveal(64, 64, random.Random(4))
    x, y = buzz.position(buzz.RISE_S + buzz.HOVER_S)
    flame = buzz.spawn(x, y)
    assert flame and all(p[1] >= y + buzz.sprite_h - 0.01 and p[3] > 0 for p in flame), "under his feet, falling away"
    assert all(x <= p[0] <= x + buzz.sprite_w for p in flame)
    assert all(p[5] in buzz.flame_colors for p in flame)


def test_buzz_is_big_on_64x32_and_the_small_one_doubled_on_64x64():
    assert (animation.BuzzReveal(64, 32).sprite_w, animation.BuzzReveal(64, 32).sprite_h) == (15, 13)
    assert (animation.BuzzReveal(64, 64).sprite_w, animation.BuzzReveal(64, 64).sprite_h) == (22, 18)


def test_buzz_art_rows_are_even_and_use_defined_colors():
    for art in animation.BuzzReveal.SIZES.values():
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(animation.BuzzReveal.colors)


def test_sprite_art_rows_are_even_and_use_defined_colors():
    for cls in FLYBYS:
        assert len({len(row) for row in cls.art}) == 1
        assert {ch for row in cls.art for ch in row} - {"."} <= set(cls.colors)


def test_ease_out_is_clamped_and_monotonic():
    samples = [animation.ease_out(p / 10) for p in range(-2, 13)]
    assert samples[0] == 0 and samples[-1] == 1
    assert samples == sorted(samples)


def test_stitch_starts_and_ends_fully_hidden_below_the_board():
    stitch = animation.StitchReveal(64, 32, random.Random(1))
    canvas = FakeCanvas(64, 32)
    stitch.overlay(canvas, 0.0)
    assert not canvas.px, "nothing drawn at rise=0"
    canvas.Clear()
    stitch.overlay(canvas, stitch.duration - 0.001)
    ys_near_end = set(y for _, y in canvas.px)
    canvas.Clear()
    stitch.overlay(canvas, stitch.UP_S + stitch.HOLD_S)
    ys_at_peak = set(y for _, y in canvas.px)
    assert ys_at_peak, "something visible at the peak of the rise"
    assert max(ys_near_end, default=32) >= max(ys_at_peak) if ys_near_end else True


def test_stitch_rises_then_holds_then_descends():
    stitch = animation.StitchReveal(64, 64, random.Random(2))
    rises = [stitch.rise(t / 100) for t in range(int(stitch.duration * 100))]
    peak = max(rises)
    assert peak == pytest.approx(1.0, abs=0.01)
    up_phase = rises[: int(stitch.UP_S * 100)]
    assert up_phase == sorted(up_phase), "rises monotonically at first"
    down_phase = rises[-int(stitch.UP_S * 100):]
    assert down_phase == sorted(down_phase, reverse=True), "descends monotonically at the end"
    assert rises[0] == pytest.approx(0.0, abs=0.01)
    assert rises[-1] < 0.05, "back down by the end"


def test_stitch_never_draws_outside_the_board():
    for height in (32, 64):
        stitch = animation.StitchReveal(64, height, random.Random(3))
        for f in range(int(stitch.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            stitch.overlay(canvas, f / animation.FPS)
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height


def test_stitch_looks_left_then_right_while_settled():
    stitch = animation.StitchReveal(64, 64, random.Random(4))
    frames = [stitch.look_frame(stitch.UP_S + i * 0.1) for i in range(int(stitch.LOOK_S * 2 / 0.1) + 2)]
    assert 0 in frames and 1 in frames, "alternates between both poses"
    assert stitch.look_frame(0.0) == 0, "still looking forward/left while rising"


def test_stitch_finishes_and_is_excluded_from_flyby_tests():
    stitch = animation.StitchReveal(64, 32, random.Random(5))
    canvas = FakeCanvas(64, 32)
    assert stitch.overlay(canvas, stitch.duration) is False
    assert "stitch" in animation.TRANSITIONS
    assert animation.StitchReveal not in FLYBYS, "peek reveals aren't fly-bys"


def _striped_screen(canvas, t):
    for y in range(canvas.height):
        for x in range(canvas.width):
            canvas.SetPixel(x, y, 200, 100, 50)
    return False


def test_ralph_shatters_the_previous_screen_into_falling_debris():
    ralph = animation.RalphReveal(64, 32, random.Random(1))
    ralph.capture_prev(_striped_screen, 0.0)
    assert len(ralph.prev_px) == 64 * 32, "captured every pixel of the old screen"
    canvas = FakeCanvas(64, 32)
    before = ralph.RISE_S + ralph.WIND_S - 0.01
    ralph.overlay(canvas, before)
    assert not ralph.shattered, "screen is still whole until the fists land"
    ralph.overlay(FakeCanvas(64, 32), before + 0.02)
    assert ralph.shattered and ralph.debris


def test_ralph_debris_falls_and_clears_the_board():
    ralph = animation.RalphReveal(64, 32, random.Random(2))
    ralph.capture_prev(_striped_screen, 0.0)
    impact = ralph.RISE_S + ralph.WIND_S
    ralph.overlay(FakeCanvas(64, 32), impact + 0.01)
    early = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    ralph.overlay(FakeCanvas(64, 32), impact + 0.35)
    mid = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    ralph.overlay(FakeCanvas(64, 32), impact + 0.9)
    late = sum(d[1] for d in ralph.debris) / len(ralph.debris)
    assert mid < early, "the blast throws it upward and outward first"
    assert late > mid, "then gravity pulls it back down"
    canvas = FakeCanvas(64, 32)
    ralph.overlay(canvas, ralph.duration - 0.01)
    leftover = [p for p, rgb in canvas.px.items() if rgb == (200, 100, 50)]
    assert len(leftover) < 64 * 32 * 0.25, "most of the old screen has fallen away"


def test_ralph_finishes_and_never_draws_off_board():
    for height in (32, 64):
        ralph = animation.RalphReveal(64, height, random.Random(3))
        ralph.capture_prev(_striped_screen, 0.0)
        for f in range(int(ralph.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            assert ralph.overlay(canvas, f / animation.FPS) is True
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height
        assert ralph.overlay(FakeCanvas(64, height), ralph.duration) is False


def test_ralph_rises_into_frame_then_drops_away():
    ralph = animation.RalphReveal(64, 64, random.Random(4))
    assert ralph.ralph_y(0.0) >= ralph.height - 1, "starts below the board"
    peak = ralph.ralph_y(ralph.RISE_S + ralph.WIND_S / 2)
    assert peak == pytest.approx(ralph.height - ralph.sprite_h)
    assert ralph.ralph_y(ralph.duration - 0.01) > peak, "drops back down at the end"


def test_ralph_opts_into_receiving_the_previous_screen():
    assert animation.RalphReveal.wants_prev is True
    assert not getattr(animation.Wipe, "wants_prev", False)
    assert "ralph" in animation.TRANSITIONS


def test_mickey_materializes_the_new_screen_out_of_magic_dust():
    mickey = animation.MickeyReveal(64, 32, random.Random(1))
    mickey.capture_new(_striped_screen, 0.0)
    assert len(mickey.new_px) == 64 * 32, "captured every pixel of the incoming screen"
    assert len(mickey.motes) == len(mickey.new_px), "one mote per pixel to summon"
    landed = []
    for t in (mickey.RISE_S, mickey.RISE_S + mickey.CAST_S / 2, mickey.duration - 0.01):
        canvas = FakeCanvas(64, 32)
        mickey.overlay(canvas, t)
        landed.append(sum(1 for rgb in canvas.px.values() if rgb == (200, 100, 50)))
    assert landed == sorted(landed), "more of the screen has settled as the cast goes on"
    assert landed[0] < landed[-1] * 0.2, "almost nothing is there when he starts"
    assert landed[-1] > 64 * 32 * 0.4, "most of the screen has arrived by the end"


def test_mickey_summons_left_to_right_in_the_wake_of_the_wand():
    mickey = animation.MickeyReveal(64, 32, random.Random(2))
    mickey.capture_new(_striped_screen, 0.0)
    left = [m for m in mickey.motes if m[0] < 20]
    right = [m for m in mickey.motes if m[0] > 55]
    assert max(m[4] for m in left) <= min(m[4] for m in right), "the sweep reaches the left first"
    assert mickey._sweep_t(0) == 0.0 and mickey._sweep_t(63) == pytest.approx(1.0, abs=0.05)


def test_mickey_wand_tip_sweeps_across_the_board():
    mickey = animation.MickeyReveal(64, 64, random.Random(3))
    start_x, _ = mickey.wand_tip(mickey.RISE_S)
    end_x, _ = mickey.wand_tip(mickey.RISE_S + mickey.CAST_S)
    assert end_x > start_x >= 0, "the tip travels rightward across the board"
    xs = [mickey.wand_tip(mickey.RISE_S + i / animation.FPS)[0]
          for i in range(int(mickey.CAST_S * animation.FPS))]
    assert xs == sorted(xs), "and never doubles back"
    for f in range(int(mickey.duration * animation.FPS)):
        _, y = mickey.wand_tip(f / animation.FPS)
        assert 0 <= y < mickey.height


def test_mickey_finishes_and_never_draws_off_board():
    for height in (32, 64):
        mickey = animation.MickeyReveal(64, height, random.Random(4))
        mickey.capture_new(_striped_screen, 0.0)
        assert mickey.sprite_h <= height and mickey.sprite_w <= 64, "he fits the board"
        for f in range(int(mickey.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            assert mickey.overlay(canvas, f / animation.FPS) is True
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height
        assert mickey.overlay(FakeCanvas(64, height), mickey.duration) is False


def test_mickey_rises_into_frame_and_then_holds():
    mickey = animation.MickeyReveal(64, 64, random.Random(5))
    assert mickey.mickey_y(0.0) >= mickey.height - 1, "starts below the board"
    settled = mickey.height - mickey.sprite_h
    assert mickey.mickey_y(mickey.RISE_S) == pytest.approx(settled)
    assert mickey.mickey_y(mickey.duration - 0.01) == pytest.approx(settled), "stays for the cast"


def test_mickey_art_rows_are_even_and_use_defined_colors():
    art = animation.MickeyReveal.ART
    assert len({len(row) for row in art}) == 1
    assert {ch for row in art for ch in row} - {"."} == set(animation.MickeyReveal.COLORS)


def test_mickey_opts_into_receiving_the_new_screen():
    assert animation.MickeyReveal.wants_new is True
    assert not getattr(animation.RalphReveal, "wants_new", False)
    assert "mickey" in animation.TRANSITIONS


def test_show_screen_hands_mickey_the_new_screens_pixels():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((120, 30, 200)), animation.MickeyReveal.duration + 0.5,
                          transition="mickey", rng=random.Random(6))
    assert matrix.frames[0].get((63, 5)) in (None, (0, 0, 0)), "far side still unformed at the start"
    assert matrix.frames[-1][(63, 5)] == (120, 30, 200), "screen fully materialized by the end"


def test_slinky_plays_as_a_screen_transition():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((10, 200, 90)), animation.SlinkyReveal.duration + 0.5,
                          transition="slinky", rng=random.Random(7))
    assert matrix.frames[0].get((63, 5)) in (None, (0, 0, 0)), "far side still dark at the start"
    assert matrix.frames[-1][(63, 5)] == (10, 200, 90), "screen fully revealed by the end"


def _baymax_span(reveal, height, t):
    """Width and height in pixels of everything Baymax draws at time t."""
    canvas = FakeCanvas(64, height)
    reveal.overlay(canvas, t)
    if not canvas.px:
        return 0, 0
    xs = [x for x, _ in canvas.px]
    ys = [y for _, y in canvas.px]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_finishes_within_his_duration(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(1))
    canvas = FakeCanvas(64, height)
    assert baymax.overlay(canvas, baymax.duration - 0.01) is True
    assert baymax.overlay(FakeCanvas(64, height), baymax.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_never_draws_outside_the_board(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(2))
    for f in range(int(baymax.duration * animation.FPS) + 1):
        canvas = FakeCanvas(64, height)
        baymax.overlay(canvas, f / animation.FPS)
        for x, y in canvas.px:
            assert 0 <= x < 64 and 0 <= y < height


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_inflates_then_deflates_away(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(3))
    sizes = [_baymax_span(baymax, height, t) for t in (0.05, 0.3, 0.6, baymax.INFLATE_S)]
    heights = [h for _, h in sizes]
    assert heights == sorted(heights), "grows steadily while inflating"
    assert heights[0] * 3 < heights[-1], "starts as a flat puddle, ends full size"
    assert sizes[0][0] > sizes[0][1], "a deflated Baymax is wider than he is tall"
    full_w, full_h = sizes[-1]
    late_w, late_h = _baymax_span(baymax, height, baymax.duration - 0.3)
    assert late_h < full_h and late_w < full_w, "shrinks again as the air goes out"
    assert _baymax_span(baymax, height, baymax.duration - 0.01) == (0, 0), "gone by the end"


def test_baymax_inflation_curve_peaks_at_full_size_and_returns_to_nothing():
    baymax = animation.BaymaxReveal(64, 64, random.Random(4))
    inflations = [baymax.inflation(t / 100) for t in range(int(baymax.duration * 100))]
    assert inflations[0] < 0.15, "starts deflated"
    assert max(inflations) == pytest.approx(1.0, abs=0.12), "settles at full size, give or take the wobble"
    assert inflations[-1] < 0.05, "back to nothing by the end"
    rising = inflations[: int(baymax.INFLATE_S * 100)]
    assert rising == sorted(rising), "fills monotonically"
    falling = inflations[-int(baymax.DEFLATE_S * 100):]
    assert falling == sorted(falling, reverse=True), "empties monotonically"


def test_baymax_wobbles_as_he_settles():
    baymax = animation.BaymaxReveal(64, 64, random.Random(5))
    settling = [baymax.inflation(baymax.INFLATE_S + i / 100) for i in range(60)]
    assert max(settling) > 1.0 and min(settling) < 1.0, "overshoots and springs back"


@pytest.mark.parametrize("height", [32, 64])
def test_baymax_has_two_eyes_joined_by_a_line_once_inflated(height):
    baymax = animation.BaymaxReveal(64, height, random.Random(6))
    canvas = FakeCanvas(64, height)
    baymax.overlay(canvas, baymax.INFLATE_S + 0.05)
    dark = {(x, y) for (x, y), rgb in canvas.px.items() if rgb == baymax.DARK}
    assert dark, "the face is drawn"
    rows = {y for _, y in dark}
    line_y = max(rows, key=lambda y: len([1 for x, yy in dark if yy == y]))
    line = sorted(x for x, y in dark if y == line_y)
    assert line == list(range(line[0], line[-1] + 1)), "the eyes are joined by a solid line"
    # Above the line the dark pixels fall into exactly two separate eyes.
    above = sorted(x for x, y in dark if y == line_y - 1)
    groups = []
    for x in above:
        if groups and x - groups[-1][-1] == 1:
            groups[-1].append(x)
        else:
            groups.append([x])
    assert len(groups) == 2, "two eyes, with white between them"
    assert abs((groups[0][0] + groups[0][-1]) / 2 + (groups[1][0] + groups[1][-1]) / 2 - 2 * baymax.cx) <= 1.5, \
        "the eyes sit symmetrically about his centre"


def test_baymax_blinks_and_waves_while_he_holds():
    baymax = animation.BaymaxReveal(64, 64, random.Random(7))
    opens = [baymax.eye_open(baymax.INFLATE_S + i / 100) for i in range(int(baymax.HOLD_S * 100))]
    assert min(opens) < 0.15 and max(opens) == pytest.approx(1.0), "eyes close and reopen"
    assert baymax.eye_open(0.0) == 1.0, "no blink while he is still filling"
    waves = [baymax.wave(baymax.INFLATE_S + i / 100) for i in range(int(baymax.HOLD_S * 100))]
    assert max(waves) > 0.5 and min(waves) < -0.5, "the arm swings both ways"
    assert baymax.wave(baymax.duration - 0.01) == 0.0, "arm is back down before he deflates"


def test_baymax_is_big_on_both_boards():
    for height in (32, 64):
        baymax = animation.BaymaxReveal(64, height, random.Random(8))
        w, h = _baymax_span(baymax, height, baymax.INFLATE_S)
        assert h >= height * 0.75, "he fills most of the board's height"
        assert w >= 18, "and is genuinely wide"


def test_baymax_leaves_the_rest_of_the_new_screen_visible():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((0, 140, 200)), animation.BaymaxReveal.duration + 0.5,
                          transition="baymax", rng=random.Random(9))
    assert matrix.frames[0][(0, 0)] == (0, 140, 200), "no blackout: he pops up over the new screen"
    assert matrix.frames[-1][(32, 31)] == (0, 140, 200), "and he is gone by the end"


def test_baymax_is_registered_and_is_not_a_flyby():
    assert animation.TRANSITIONS["baymax"] is animation.BaymaxReveal
    assert animation.BaymaxReveal not in FLYBYS
    assert not getattr(animation.BaymaxReveal, "wants_prev", False)


def test_tron_is_a_registered_flyby():
    assert animation.TRANSITIONS["tron"] is animation.TronReveal
    assert issubclass(animation.TronReveal, animation.FlyByReveal)


def _tron_frame(tron, height, t, new=(0, 140, 0)):
    canvas = FakeCanvas(64, height)
    for x in range(64):
        for y in range(height):
            canvas.SetPixel(x, y, *new)
    more = tron.overlay(canvas, t)
    return canvas.px, more


@pytest.mark.parametrize("height", [32, 64])
def test_tron_races_blue_on_top_and_red_along_the_bottom(height):
    tron = animation.TronReveal(64, height, random.Random(1))
    (blue, bx, by), (red, rx, ry) = tron.bikes(tron.CROSS_S / 2)
    assert (blue, red) == ("blue", "red")
    assert by == 0 and ry == height - tron.sprite_h, "blue across the top, red along the bottom"
    assert rx < bx, "red is behind mid-race"
    assert tron.bikes(0)[0][1] - tron.bikes(0)[1][1] == tron.RED_LAG
    assert tron.bikes(tron.CROSS_S)[1][1] == tron.bikes(tron.CROSS_S)[0][1] >= 64, "level and gone by the end"
    px, _ = _tron_frame(tron, height, tron.CROSS_S / 2)
    colors = set(px.values())
    assert tron.BLUE["C"] in colors and tron.RED["C"] in colors, "both bikes drawn"
    assert tron.TRAILS["blue"][0] in colors and tron.TRAILS["red"][0] in colors, "and both trails"


@pytest.mark.parametrize("height", [32, 64])
def test_tron_uncovers_the_new_screen_behind_the_bikes_and_the_trails_derez(height):
    tron = animation.TronReveal(64, height, random.Random(1))
    new = (0, 140, 0)
    trails = {rgb for pair in tron.TRAILS.values() for rgb in pair}
    px, _ = _tron_frame(tron, height, tron.CROSS_S / 2)
    assert px[(0, height // 2)] == new, "behind the bikes, the new ride"
    assert px[(63, height // 2)] == (0, 0, 0), "ahead of them, not yet"

    px, _ = _tron_frame(tron, height, tron.CROSS_S + tron.HOLD_S / 2)
    held = [rgb for rgb in px.values() if rgb != new]
    assert held and set(held) <= trails, "the bikes are gone, the trails hold"
    px, _ = _tron_frame(tron, height, tron.CROSS_S + tron.HOLD_S + tron.FADE_S / 2)
    left = [rgb for rgb in px.values() if rgb != new]
    assert 0 < len(left) < len(held), "the trails drop out pixel by pixel"
    assert set(left) <= trails, "whole pixels, never dimmed over the screen"
    px, more = _tron_frame(tron, height, tron.duration)
    assert not more and set(px.values()) == {new}, "all gone at the end"


def test_mike_is_a_registered_peek_over_the_finished_screen():
    cls = animation.TRANSITIONS["mike"]
    assert cls is animation.MikeReveal and cls.over_screen
    assert not getattr(cls, "wants_prev", False) and not getattr(cls, "wants_new", False)


@pytest.mark.parametrize("height", [32, 64])
def test_mike_stays_on_the_board_and_is_gone_by_the_end(height):
    mike = animation.MikeReveal(64, height, random.Random(1))
    for f in range(int(mike.duration * animation.FPS) + 1):
        canvas = FakeCanvas(64, height)
        assert mike.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert mike.pixels(mike.duration - 0.01) == {}, "ducked out of sight"
    assert mike.overlay(FakeCanvas(64, height), mike.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_mike_shows_his_whole_round_body_once_up(height):
    mike = animation.MikeReveal(64, height, random.Random(2))
    px = mike.pixels(mike.UP_S + 0.05)
    body = [(x, y) for (x, y), rgb in px.items() if rgb in (mike.GREEN, mike.LIGHT, mike.EDGE)]
    assert max(y for _, y in body) < height - 1, "his body clears the bottom edge"
    assert max(x for x, _ in body) - min(x for x, _ in body) >= 2 * mike.r - 3


def _eye_whites(mike, t):
    return sum(1 for rgb in mike.pixels(t).values() if rgb == mike.WHITE)


def test_mike_blinks_looks_around_then_scares():
    mike = animation.MikeReveal(64, 64, random.Random(3))
    open_eye = _eye_whites(mike, mike.BLINK[0] - 0.05)
    mid_blink = (mike.BLINK[0] + mike.BLINK[1]) / 2
    assert mike.lid(mid_blink) == 1.0 and _eye_whites(mike, mid_blink) < open_eye / 2, "the lid covers the eye"
    looks = [mike.look(mike.LOOK[0] + i / 100) for i in range(int((mike.LOOK[1] - mike.LOOK[0]) * 100))]
    assert min(looks) == -1.0 and max(looks) == 1.0
    assert looks.index(-1.0) < looks.index(1.0), "left first, then right"
    assert mike.grin(mike.SCARE[0]) == 1.0 and mike.grin(0) == 0.0

    def top(t, rgb=None):
        return min(y for (_, y), c in mike.pixels(t).items() if rgb is None or c == rgb)

    before, scaring = mike.SCARE[0] - 0.05, mike.SCARE[0] + 0.2
    assert top(scaring) <= top(before) - 2, "he jumps at the scare"

    def hands_up(t):
        # Arm pixels out past his sides, above his eye.
        px = mike.pixels(t)
        cx = sum(x for x, _ in px) / len(px)
        return any(rgb == mike.DARK and abs(x - cx) > mike.r + 1 and y < top(t, mike.IRIS)
                   for (x, y), rgb in px.items())

    assert hands_up(scaring) and not hands_up(before), "arms thrown up only for the scare"


@pytest.mark.parametrize("height", [32, 64])
def test_mikes_hands_are_three_spread_fingers_and_a_thumb(height):
    mike = animation.MikeReveal(64, height, random.Random(5))
    body = mike._body(scare=True, look=0.0, lid=0.0, grin=0.0)
    green = {p for p, rgb in body.items() if rgb == mike.DARK}
    top = min(y for _, y in green)
    tips = sorted(x for x, y in green if y == top)
    assert len(tips) == 6, "three fingertips on each raised hand"
    for side in (-1, 1):
        xs = [x for x in tips if x * side > 0]
        assert all(b - a >= 2 for a, b in zip(xs, xs[1:])), "gaps between them, not one blob"
    assert not any(rgb == (120, 115, 130) for rgb in body.values()), "no grey claws"


@pytest.mark.parametrize("r", [8, 12, 16])
def test_mikes_scare_mouth_has_sharp_teeth_top_and_fangs_below(r):
    mike = animation.MikeReveal(64, 64, random.Random(4))
    mike.r, mike.ry = r, r * 1.08
    body = mike._body(scare=True, look=0.0, lid=0.0, grin=1.0)
    mouth = {p: rgb for p, rgb in body.items() if p[1] > 0 and rgb in (mike.MOUTH, mike.WHITE)}

    def column(x):
        return [mouth[(x, y)] for y in sorted(y for (bx, y) in mouth if bx == x)]

    def tooth(x):
        c = column(x)
        return next(i for i, rgb in enumerate(c) if rgb != mike.WHITE)

    assert tooth(0) > tooth(1), "pointed: the middle tooth hangs lower than its neighbour"
    assert all(column(x)[0] == mike.WHITE for x in (-1, 0, 1)), "teeth along the whole top"
    assert column(2)[-1] == mike.WHITE and column(0)[-1] == mike.MOUTH, "fangs below, apart"
    assert all(mike.MOUTH in column(x) for x in (-2, -1, 0, 1, 2)), "still an open mouth"


def test_dumbo_ears_alternate_between_the_two_flap_poses():
    dumbo = animation.DumboReveal(64, 32, random.Random(1))
    frames = [dumbo.flap_frame(i * dumbo.FLAP_S / 2) for i in range(8)]
    assert set(frames) == {0, 1}, "both ear poses are used"
    assert dumbo.flap_frame(0.0) == 0, "starts on the upstroke"
    assert dumbo.flap_frame(dumbo.FLAP_S * 1.5) == 1, "ears are down half a cycle later"
    assert dumbo.EARS_UP != dumbo.EARS_DOWN, "the poses actually differ"


def test_dumbo_draws_a_different_sprite_when_his_ears_are_down():
    dumbo = animation.DumboReveal(64, 32, random.Random(2))
    up, down = FakeCanvas(64, 32), FakeCanvas(64, 32)
    # Same horizontal position for both, so only the pose differs.
    t_up = dumbo.duration / 2
    t_down = t_up + dumbo.FLAP_S
    dumbo._draw_sprite(up, t_up)
    dumbo._draw_sprite(down, t_down)
    assert up.px and down.px
    assert up.px != down.px, "the ears visibly flap between frames"


def test_dumbo_bobs_with_the_flap_and_stays_on_both_boards():
    for height in (32, 64):
        dumbo = animation.DumboReveal(64, height, random.Random(3))
        ys = [dumbo.position(f / animation.FPS)[1] for f in range(int(dumbo.duration * animation.FPS))]
        assert max(ys) - min(ys) > 0.5, "he bobs rather than flying flat"
        assert min(ys) >= 0 and max(ys) + dumbo.sprite_h <= height


def test_dumbo_art_rows_are_uniform_and_every_colour_is_defined():
    for pose in animation.DumboReveal.poses:
        assert len({len(row) for row in pose}) == 1, "all rows the same width"
        assert {ch for row in pose for ch in row} - {"."} <= set(animation.DumboReveal.colors)
    assert len(animation.DumboReveal.poses[0]) == len(animation.DumboReveal.poses[1])
    assert len(animation.DumboReveal.poses[0][0]) == len(animation.DumboReveal.poses[1][0])


def test_dumbo_trails_feather_puffs_behind_him():
    dumbo = animation.DumboReveal(64, 64, random.Random(4))
    x, y = dumbo.position(dumbo.duration / 2)
    puffs = dumbo.spawn(x, y)
    assert puffs, "sheds a trail"
    assert all(p[2] < 0 for p in puffs), "puffs drift back behind him"
    assert all(p[5] in dumbo.feather_colors for p in puffs)


def test_dumbo_is_registered_as_a_transition():
    assert animation.TRANSITIONS["dumbo"] is animation.DumboReveal
    assert issubclass(animation.DumboReveal, animation.FlyByReveal)


def test_genie_is_registered_and_is_not_a_flyby():
    assert animation.TRANSITIONS["genie"] is animation.GenieReveal
    assert not issubclass(animation.GenieReveal, animation.FlyByReveal), \
        "the lamp emerge needs its own timeline, so it isn't a fly-by"
    assert animation.GenieReveal not in FLYBYS


def test_genie_art_rows_are_even_and_use_defined_colors():
    for art in (animation.GenieReveal.ART, animation.GenieReveal.LAMP_ART):
        assert len({len(row) for row in art}) == 1, "every row is the same width"
        assert {ch for row in art for ch in row} - {"."} <= set(animation.GenieReveal.COLORS)


def test_genie_lamp_is_big_with_its_spout_tip_up_and_right():
    lamp, (sc, sr) = animation.GenieReveal.LAMP_ART, animation.GenieReveal.LAMP_SPOUT
    for height in (32, 64):
        genie = animation.GenieReveal(64, height, random.Random(0))
        assert genie.lamp_w >= 64 * 0.35, "big enough to read as a lamp, not a blob"
        assert genie.lamp_x + genie.lamp_w <= 64 and genie.lamp_y >= 0, "and wholly on the board"
        assert (genie.lamp_w, genie.lamp_h) == (len(lamp[0]), len(lamp)), \
            "1x on both boards: doubled, it swamps the 64x64 board"
    width = len(lamp[0])
    tip = [c for c, ch in enumerate(lamp[int(sr)]) if ch != "."]
    assert max(tip) >= width - 3, "the spout reaches out to the lamp's right end"
    assert int(sc) in tip and sr < len(lamp) / 2, "smoke leaves from the upturned tip, not the body"


def test_genie_lamp_does_not_share_colors_with_genie():
    """A shared outline key once turned Genie's blue outline bronze."""
    lamp = {ch for row in animation.GenieReveal.LAMP_ART for ch in row} - {"."}
    genie = {ch for row in animation.GenieReveal.ART for ch in row} - {"."}
    assert not lamp & genie
    outline = animation.GenieReveal.COLORS["A"]
    assert sum(outline) > 150, "the lamp's outline still shows on the black board"


def test_genie_is_drawn_solid_just_before_full_size():
    """Near full size every cell landed on x.5 and rounding dropped every other column."""
    for height in (32, 64):
        genie = animation.GenieReveal(64, height, random.Random(0))
        full, almost = FakeCanvas(64, height), FakeCanvas(64, height)
        genie._draw_genie(full, genie.EMERGE_S)
        t = genie.EMERGE_S - 0.001
        assert 0.99 < genie.grow(t) < 1
        genie._draw_genie(almost, t)
        assert len(almost.px) >= len(full.px) * 0.97


def test_genie_lamp_stays_on_the_dark_side_while_he_flies():
    gold = {animation.GenieReveal.COLORS[k] for k in "AYLO"}
    genie = animation.GenieReveal(64, 64, random.Random(0))
    for f in range(int(genie.EMERGE_S * animation.FPS), int(genie.duration * animation.FPS)):
        t = f / animation.FPS
        genie.puffs = []
        canvas = FakeCanvas(64, 64)
        genie.overlay(canvas, t)
        front = genie.reveal_x(t)
        lamp = [x for (x, _), rgb in canvas.px.items() if rgb in gold and x < genie.lamp_x + genie.lamp_w]
        assert all(x >= front for x in lamp), "never drawn over the revealed screen"
        if f == int(genie.EMERGE_S * animation.FPS):
            assert lamp, "and doesn't vanish the moment he takes off"


def test_genie_finishes_within_its_duration_and_its_smoke_settles():
    for height in (32, 64):
        genie = animation.GenieReveal(64, height, random.Random(1))
        canvas = FakeCanvas(64, height)
        frame = 0
        while genie.overlay(canvas, frame / animation.FPS):
            frame += 1
            assert frame < 8 * animation.FPS, "reveal never ended"
        assert frame >= genie.duration * animation.FPS
        assert not genie.puffs, "every puff has expired"


def test_genie_never_draws_outside_the_board_on_either_size():
    for height in (32, 64):
        genie = animation.GenieReveal(64, height, random.Random(2))
        for f in range(int(genie.duration * animation.FPS) + 1):
            canvas = FakeCanvas(64, height)
            genie.overlay(canvas, f / animation.FPS)
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height


def test_genie_emerges_from_the_lamp_before_he_flies():
    genie = animation.GenieReveal(64, 64, random.Random(3))
    assert genie.grow(0.0) == 0, "only smoke at first, no Genie yet"
    assert 0 < genie.grow(genie.EMERGE_S * 0.8) < 1, "part-formed partway through the emerge"
    assert genie.grow(genie.EMERGE_S) == 1, "fully formed by the time he takes off"
    # He is parked over the lamp for the whole emerge, then crosses to the right.
    parked = genie.position(genie.EMERGE_S - 0.01)[0]
    assert genie.position(0.0)[0] == parked
    assert genie.position(genie.duration)[0] >= 64, "leaves the board to the right"


def test_genie_smoke_pours_from_the_lamp_then_trails_behind_him():
    genie = animation.GenieReveal(64, 64, random.Random(4))
    sx, sy = genie.spout()
    plume = genie.spawn(0.0)
    assert plume, "the lamp is already smoking at t=0"
    assert all(abs(p[0] - sx) <= 2 * genie.scale and p[1] == sy for p in plume), "starts at the spout"
    assert all(p[3] < 0 for p in plume), "pours upward out of the lamp"

    fly_t = genie.EMERGE_S + genie.FLY_S / 2
    x, _ = genie.position(fly_t)
    wake = genie.spawn(fly_t)
    assert wake and all(p[0] > x for p in wake), "the wake leaves from his body"
    assert all(p[2] < 0 for p in wake), "and streams backward as he flies right"
    assert all(p[5] in animation.GenieReveal.SMOKE_COLORS for p in plume + wake)


def test_genie_smoke_puffs_expand_and_decay():
    genie = animation.GenieReveal(64, 64, random.Random(5))
    genie.overlay(FakeCanvas(64, 64), 0.0)
    assert genie.puffs, "smoke spawned on the first frame"
    first = genie.puffs[0]
    life, radius = first[4], first[6]
    genie.overlay(FakeCanvas(64, 64), 0.4)
    assert first[6] > radius, "a puff swells as it disperses"
    assert first[4] < life, "and burns down its remaining life"


def test_genie_reveals_the_new_screen_behind_him_but_not_while_forming():
    genie = animation.GenieReveal(64, 64, random.Random(6))
    canvas = FakeCanvas(64, 64)
    fill((9, 9, 9))(canvas, 0)
    genie.overlay(canvas, genie.EMERGE_S / 2)
    assert canvas.px[(0, 0)] == (0, 0, 0), "nothing is revealed while he forms in the lamp"

    mid = genie.EMERGE_S + genie.FLY_S / 2
    for f in range(int(genie.EMERGE_S * animation.FPS), int(mid * animation.FPS)):
        canvas.Clear()
        genie.overlay(canvas, f / animation.FPS)
    canvas.Clear()
    fill((9, 9, 9))(canvas, 0)
    genie.puffs = []  # drifting emerge smoke would tint the dark corner checked below
    genie.overlay(canvas, mid)
    assert canvas.px[(0, 0)] == (9, 9, 9), "revealed in his wake"
    assert canvas.px[(63, 63)] == (0, 0, 0), "still dark ahead of him"


def test_genie_is_drawn_big_on_both_board_sizes():
    for height in (32, 64):
        genie = animation.GenieReveal(64, height, random.Random(7))
        assert genie.sprite_h <= height, "he fits the board"
        assert genie.sprite_h >= height * 0.75, "and fills most of it"
        canvas = FakeCanvas(64, height)
        genie.overlay(canvas, genie.EMERGE_S)
        lit = [p for p, rgb in canvas.px.items() if rgb != (0, 0, 0)]
        assert lit, "he is on the board once fully formed"
        xs, ys = [x for x, _ in lit], [y for _, y in lit]
        # He is proportioned to the board's height, so on the wide 64x32 board he is tall
        # rather than wide; what matters is that he is drawn whole and fills that height.
        assert min(xs) >= 0 and max(xs) < 64, "drawn entirely on the board, not half off it"
        assert max(xs) - min(xs) >= genie.sprite_w * 0.8, "nearly his full width is on screen"
        assert max(ys) - min(ys) >= height * 0.7, "and he fills most of the board's height"


def test_slinky_is_registered_with_well_formed_art():
    cls = animation.SlinkyReveal
    assert animation.TRANSITIONS["slinky"] is cls
    for art in (cls.FRONT_ART, cls.REAR_ART):
        assert len({len(row) for row in art}) == 1, "every row is the same width"
        assert {ch for row in art for ch in row} - {"."} <= set(cls.COLORS)


def test_slinky_holds_with_his_rear_on_one_side_and_head_on_the_other():
    for height in (32, 64):
        dog = animation.SlinkyReveal(64, height)
        hold = dog.STRETCH_S + dog.HOLD_S / 2
        assert dog.rear_x(hold) == 0, "his rear sits on the left edge"
        assert dog.front_x(hold) + dog.front_w == 64, "and his nose reaches the right edge"
        assert dog.front_h <= height and dog.rear_h <= height


def test_slinky_walks_out_then_the_rear_catches_up_and_both_leave():
    dog = animation.SlinkyReveal(64, 32)
    walk = [dog.front_x(f / animation.FPS) for f in range(int(dog.STRETCH_S * animation.FPS))]
    assert walk == sorted(walk) and walk[-1] > walk[0] + 20, "the front half walks steadily right"
    gap = lambda t: dog.front_x(t) - dog.rear_x(t)
    snap_end = dog.STRETCH_S + dog.HOLD_S + dog.SNAP_S
    assert gap(0.0) < gap(dog.STRETCH_S) > gap(snap_end), "stretches out, then snaps back together"
    assert dog.rear_x(dog.duration) >= 64, "and the whole dog has left the board"


def test_slinky_tail_is_a_spring():
    art, colors = animation.SlinkyReveal.REAR_ART, animation.SlinkyReveal.COLORS
    body_top = next(i for i, row in enumerate(art) if "B" in row)
    tail = [(r, c) for r, row in enumerate(art) for c, ch in enumerate(row) if ch in "SW"]
    assert tail and all(r < body_top for r, _ in tail), "the tail rises above his rump"
    assert {art[r][c] for r, c in tail} == {"S", "W"}, "banded bright and dark like a coil"
    assert sum(abs(a - b) for a, b in zip(colors["S"], colors["W"])) > 150


def test_slinky_spring_spreads_as_he_stretches():
    coil = {animation.SlinkyReveal.COIL_FRONT, animation.SlinkyReveal.COIL_BACK}

    def spring_span(t):
        canvas = FakeCanvas(64, 32)
        animation.SlinkyReveal(64, 32).overlay(canvas, t)
        xs = [x for (x, _), rgb in canvas.px.items() if rgb in coil]
        return max(xs) - min(xs)

    dog = animation.SlinkyReveal
    assert spring_span(dog.STRETCH_S + 0.1) > spring_span(0.0) + 20


def test_slinky_reveals_behind_him_and_stays_on_the_board():
    for height in (32, 64):
        dog = animation.SlinkyReveal(64, height)
        mid = dog.STRETCH_S / 2
        canvas = FakeCanvas(64, height)
        fill((9, 9, 9))(canvas, 0)
        dog.overlay(canvas, mid)
        assert canvas.px[(0, 0)] == (9, 9, 9), "revealed behind his front half"
        assert canvas.px[(63, 0)] == (0, 0, 0), "still dark ahead of him"
        frames = 0
        while dog.overlay(FakeCanvas(64, height), frames / animation.FPS):
            frames += 1
            assert frames < 10 * animation.FPS, "reveal never ended"
        for f in range(frames + 1):
            canvas = FakeCanvas(64, height)
            dog.overlay(canvas, f / animation.FPS)
            assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)


def _wrap(height=32, seed=0):
    return animation.SlinkyWrapReveal(64, height, random.Random(seed))


def _at(dog, name, frac):
    """A time `frac` of the way through the named phase."""
    names = ["walk_in", "walk_off", "pause", "peek", "look", "cross", "follow", "exit"]
    i = names.index(name)
    start = dog.beats[i - 1] if i else 0.0
    return start + (dog.beats[i] - start) * frac


def test_slinky_wrap_is_a_registered_surprise_with_well_formed_art():
    cls = animation.SlinkyWrapReveal
    assert animation.TRANSITIONS["slinky_wrap"] is cls and cls.over_screen
    arts = (cls.FRONT_ART, cls.FRONT_LOOK_ART, cls.REAR_ART, cls.REAR_WAG_ART)
    for art in arts:
        assert len({len(row) for row in art}) == 1
        assert {ch for row in art for ch in row} - {"."} <= set(cls.COLORS)
    changed = {r for r, (a, b) in enumerate(zip(cls.FRONT_ART, cls.FRONT_LOOK_ART)) if a != b}
    assert changed and changed <= {3, 4, 5}, "the look-down head only moves his pupils"
    body_top = next(i for i, row in enumerate(cls.REAR_ART) if "B" in row)
    changed = {r for r, (a, b) in enumerate(zip(cls.REAR_ART, cls.REAR_WAG_ART)) if a != b}
    assert changed and max(changed) < body_top, "the wag only moves his tail"


def test_slinky_wrap_pause_is_random_and_the_visit_fits_a_ride_screen():
    pauses = set()
    for seed in range(40):
        dog = _wrap(seed=seed)
        assert 1.0 <= dog.pause <= 3.0
        assert animation.COVER_S + dog.duration <= 8 - 1 / animation.FPS, "done before the screen changes"
        pauses.add(round(dog.pause, 2))
    assert len(pauses) > 20


def test_slinky_wrap_rear_holds_the_bottom_right_while_his_front_goes_round():
    for height in (32, 64):
        dog = _wrap(height)
        for name in ("walk_off", "pause", "peek", "look", "cross"):
            for frac in (0.1, 0.5, 0.9):
                rx, ground = dog.pose(_at(dog, name, frac))["rear"]
                assert (rx, ground) == (dog.rear_home, height), f"rear stays put during {name}"
        assert dog.rear_home > 64 / 2 and dog.rear_home + dog.rear_w < 64
        assert dog.pose(_at(dog, "walk_off", 0.999))["front"][0] > 64 - 2, "front walks off the right edge"
        assert dog.pose(_at(dog, "pause", 0.5))["front"] is None
        fx, fg = dog.pose(_at(dog, "look", 0.5))["front"]
        assert fx < 64 / 4 and fg == dog.front_h, "and peeks back in at the top-left"


def test_slinky_wrap_spring_goes_round_the_back_of_the_board():
    dog = _wrap(32)
    coil = {dog.COIL_FRONT, dog.COIL_BACK}
    t = _at(dog, "look", 0.5)
    canvas = FakeCanvas(64, 32)
    dog.overlay(canvas, t)
    fx, _ = dog.pose(t)["front"]
    xs = [x for (x, _), rgb in canvas.px.items() if rgb in coil]
    assert min(xs) == 0 and max(xs) == 63, "stubs run off the left edge and the right edge"
    assert not [x for x in xs if fx + dog.front_w <= x < dog.rear_home], "nothing across the middle"


def test_slinky_wrap_looks_down_at_his_rear_and_wags():
    dog = _wrap(32)
    t = _at(dog, "look", 0.5)
    canvas = FakeCanvas(64, 32)
    dog.overlay(canvas, t)
    fx, fg = dog.pose(t)["front"]
    pupil = dog.COLORS["P"]
    for r, (normal, looking) in enumerate(zip(dog.FRONT_ART, dog.FRONT_LOOK_ART)):
        for c, (a, b) in enumerate(zip(normal, looking)):
            px = canvas.px.get((int(fx) + c, fg - dog.front_h + r))
            if b == "P":
                assert px == pupil, "pupils drop to look down"
            elif a == "P":
                assert px != pupil
    tails = set()
    rx, rg = dog.pose(t)["rear"]
    for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
        c = FakeCanvas(64, 32)
        dog.overlay(c, _at(dog, "look", frac))
        tails.add(frozenset(p for p, rgb in c.px.items() if rgb in (dog.COLORS["S"], dog.COLORS["W"])
                            and p[1] < rg - dog.rear_h + 3 and p[0] < rx + dog.rear_w))
    assert len(tails) >= 2, "the tail swings between poses"


def test_slinky_wrap_rear_follows_his_path_round_then_both_leave():
    for height in (32, 64):
        dog = _wrap(height)
        out = [dog.pose(_at(dog, "follow", f * dog.FOLLOW_OUT))["rear"] for f in (0.1, 0.5, 0.99)]
        assert all(g == height for _, g in out), "leaves along the bottom, the way his front went"
        assert out[0][0] < out[1][0] < out[2][0] and out[2][0] > 64 - 3, "off the right edge"
        back = [dog.pose(_at(dog, "follow", dog.FOLLOW_OUT + f * (1 - dog.FOLLOW_OUT)))["rear"]
                for f in (0.01, 0.5, 0.999)]
        assert all(g == dog.front_h for _, g in back), "and comes back along the top"
        assert back[0][0] < 0, "in from the left edge"
        fx, _ = dog.pose(_at(dog, "follow", 0.999))["front"]
        assert back[2][0] + dog.rear_w <= fx and back[2][0] > back[1][0], "catching up behind him"
        assert dog.pose(dog.duration - 1e-6)["rear"][0] > 64 - dog.rear_w, "then the whole dog walks off right"
        assert dog.overlay(FakeCanvas(64, height), dog.duration) is False


def test_slinky_wrap_draws_over_the_screen_and_stays_on_the_board():
    for height in (32, 64):
        dog = _wrap(height)
        canvas = FakeCanvas(64, height)
        fill((9, 9, 9))(canvas, 0)
        dog.overlay(canvas, _at(dog, "look", 0.5))
        assert canvas.px[(32, height // 2 + 4)] == (9, 9, 9), "no blackout: the ride screen shows through"
        for f in range(int(dog.duration * animation.FPS) + 1):
            c = FakeCanvas(64, height)
            dog.overlay(c, f / animation.FPS)
            assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)


def test_surprises_let_the_screen_underneath_keep_animating():
    def times(transition):
        seen = []
        matrix = FakeMatrix()
        # A new matrix can reuse a collected one's id() and inherit its last screen.
        animation.forget_screen(matrix)
        animation.show_screen(matrix, lambda canvas, t: seen.append(t) or True, 0.5,
                              transition=transition, rng=random.Random(0))
        return seen
    assert max(times("baymax")) > 0.3, "under a surprise the ride screen plays on"
    assert max(times("wipe")) == 0, "a reveal still holds it at its first frame"


def test_genie_smoke_sets_each_pixel_once_however_many_puffs_overlap():
    """Drawing puff by puff was thousands of SetPixel calls a frame: too slow on a Pi."""
    genie = animation.GenieReveal(64, 64, random.Random(0))
    rgb = animation.GenieReveal.SMOKE_COLORS[0]
    genie.puffs = [[30.0, 30.0, 0, 0, 18, rgb, 1.5] for _ in range(50)]

    class Counting(FakeCanvas):
        def __init__(self):
            super().__init__(64, 64)
            self.writes = {}

        def SetPixel(self, x, y, r, g, b):
            self.writes[(x, y)] = self.writes.get((x, y), 0) + 1
            super().SetPixel(x, y, r, g, b)

    canvas = Counting()
    genie._draw_puffs(canvas)
    assert canvas.writes and max(canvas.writes.values()) == 1
    lone = Counting()
    genie.puffs = genie.puffs[:1]
    genie._draw_puffs(lone)
    assert canvas.px == lone.px, "stacked identical puffs look like one, not a white blob"
    centre, edge = lone.px[(30, 30)], lone.px[(31, 30)]
    assert sum(centre) > sum(edge) > 0, "brightest at the centre, fading out"


def test_genie_full_size_fast_path_draws_exactly_his_art():
    for height in (32, 64):
        genie = animation.GenieReveal(64, height, random.Random(0))
        t = genie.EMERGE_S + 0.3
        canvas = FakeCanvas(64, height)
        genie._draw_genie(canvas, t)
        x0, y0 = (math.floor(v + 0.5) for v in genie.position(t))
        s = genie.scale
        expected = {(x0 + c * s + sx, y0 + r * s + sy): genie.COLORS[k]
                    for r, line in enumerate(genie.ART) for c, k in enumerate(line) if k != "."
                    for sy in range(s) for sx in range(s)}
        expected = {p: rgb for p, rgb in expected.items() if 0 <= p[0] < 64 and 0 <= p[1] < height}
        assert canvas.px == expected


# ---- WALL-E ----

def _walle(height=32, seed=1, screen=_striped_screen):
    walle = animation.WallEReveal(64, height, random.Random(seed))
    walle.capture_prev(screen, 0.0)
    return walle


def _walle_colour_distance(a, b):
    colors = animation.WallEReveal.COLORS
    return sum(abs(x - y) for x, y in zip(colors.get(a, a), colors.get(b, b)))


def test_walle_opts_into_receiving_the_previous_screen():
    assert animation.WallEReveal.wants_prev is True
    assert animation.TRANSITIONS["walle"] is animation.WallEReveal


@pytest.mark.parametrize("height", [32, 64])
def test_walle_finishes_and_never_draws_off_board(height):
    walle = _walle(height)
    for f in range(int(walle.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert walle.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert walle.overlay(FakeCanvas(64, height), walle.duration) is False


def test_walle_rolls_in_stops_then_drives_off_the_right():
    walle = _walle()
    assert walle.walle_x(0) <= -walle.sprite_w + 1, "starts off the left edge"
    stopped = [walle.walle_x(t) for t in (walle.ENTER_S, walle.ENTER_S + walle.LOOK_S + walle.COMPACT_S)]
    assert stopped == [walle.STOP_X, walle.STOP_X], "parked while he looks and compacts"
    assert walle.walle_x(walle.duration - 0.01) > 60, "gone off the right edge by the end"


@pytest.mark.parametrize("height", [32, 64])
def test_walle_stays_the_same_size_on_both_boards(height):
    walle = _walle(height)
    assert walle.SCALE == 1 and walle.sprite_h == len(walle.ART) <= 20
    assert walle.y0 + walle.sprite_h == height, "on the bottom edge"


def test_the_old_screen_hides_the_new_one_until_he_starts_compacting():
    walle = _walle()
    canvas = FakeCanvas(64, 32)
    fill((1, 2, 3))(canvas, 0)
    walle.overlay(canvas, walle.ENTER_S + walle.LOOK_S - 0.05)
    assert (1, 2, 3) not in canvas.px.values(), "no new screen peeking through yet"
    assert list(canvas.px.values()).count((200, 100, 50)) > 64 * 32 * 0.6, "the old screen is still up"


def test_walle_vacuums_the_whole_old_screen_nearest_first():
    walle = _walle()
    start = walle.ENTER_S + walle.LOOK_S
    ix, iy = walle.intake()
    mid = FakeCanvas(64, 32)
    walle.overlay(mid, start + walle.SWEEP_S / 2)
    left = [(x, y) for (x, y), rgb in mid.px.items() if rgb == (200, 100, 50)]
    assert left and min(math.hypot(x - ix, y - iy) for x, y in left) > 5, "the pixels nearest him go first"
    done = FakeCanvas(64, 32)
    walle.overlay(done, start + walle.COMPACT_S + 0.01)
    assert (200, 100, 50) not in done.px.values(), "every pixel of the old screen is in the cube"


def test_the_cube_is_made_of_what_he_ate_and_carries_a_sprout():
    walle = _walle()
    assert set(walle.cube) == {(160, 80, 40)}, "the old screen's colour, dimmed by the squash"
    canvas = FakeCanvas(64, 32)
    walle.overlay(canvas, walle.duration - walle.LEAVE_S + 0.05)
    assert (160, 80, 40) in canvas.px.values()
    assert walle.PLANT_RGB["leaf"] in canvas.px.values()


def test_walle_blinks_during_his_look():
    walle = _walle()
    def lenses(t):
        canvas = FakeCanvas(64, 32)
        walle.overlay(canvas, t)
        return list(canvas.px.values()).count(walle.COLORS["L"])
    look = walle.ENTER_S
    assert lenses(look + walle.BLINK_AT + walle.BLINK_S / 2) == 0, "eyes shut"
    assert lenses(look + walle.BLINK_AT - 0.05) > 0 and lenses(look + walle.BLINK_AT + walle.BLINK_S + 0.05) > 0


def test_walle_tilts_his_head_before_the_blink():
    walle = _walle()
    def eye_tops(t):
        canvas = FakeCanvas(64, 32)
        walle.overlay(canvas, t)
        housing = [(x, y) for (x, y), rgb in canvas.px.items() if rgb == walle.COLORS["E"]]
        return min(y for x, y in housing if x < walle.STOP_X + 10), min(y for x, y in housing if x >= walle.STOP_X + 10)
    left, right = eye_tops(walle.ENTER_S + walle.TILT_S / 2)
    assert left < right, "one eye lifted: a curious tilt"
    left, right = eye_tops(walle.ENTER_S + walle.BLINK_AT - 0.05)
    assert left == right, "level again"


def test_walle_kicks_up_dust_when_he_stops():
    walle = _walle()
    walle.overlay(FakeCanvas(64, 32), walle.ENTER_S)
    assert walle.dust


def test_walle_art_is_uniform_and_every_cell_has_a_colour():
    art = animation.WallEReveal.ART
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.WallEReveal.COLORS)


def test_walle_features_stand_out_from_what_they_sit_on():
    assert _walle_colour_distance("L", "E") > 200, "lens against its housing"
    assert _walle_colour_distance("G", "L") > 300, "glint against the lens"
    assert _walle_colour_distance("Y", "K") > 300, "body against his outline"
    assert _walle_colour_distance("D", "Y") > 60, "shaded side against the lit front"
    assert _walle_colour_distance(animation.WallEReveal.PLANT_RGB["leaf"], "Y") > 150, "sprout against his body"
    assert _walle_colour_distance(animation.WallEReveal.CUBE_EDGE_RGB, "K") > 150, "cube against his outline"


# ---- WALL-E, side view ----

def _walle_side(height=32, seed=1):
    walle = animation.WallESideReveal(64, height, random.Random(seed))
    walle.capture_prev(_striped_screen, 0.0)
    return walle


@pytest.mark.parametrize("height", [32, 64])
def test_walle_side_finishes_and_never_draws_off_board(height):
    walle = _walle_side(height)
    for f in range(int(walle.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert walle.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert walle.overlay(FakeCanvas(64, height), walle.duration) is False


def test_walle_side_art_is_uniform_and_every_cell_has_a_colour():
    art = animation.WallESideReveal.ART
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.WallESideReveal.COLORS)
    assert set("".join(animation.WallESideReveal.HEAD_FRONT)) <= set(animation.WallESideReveal.COLORS)


def test_walle_side_faces_his_travel_with_his_chest_in_front():
    walle = _walle_side()
    ix, _ = walle.intake()
    assert ix > walle.STOP_X + walle.sprite_w / 2, "the chest door is on the right, the way he drives"


def test_walle_side_turns_to_look_at_us_then_back():
    walle = _walle_side()
    look = walle.phase_start("look")
    assert not walle.facing_us(look - 0.05)
    assert walle.facing_us(look + walle.LOOK_S / 2)
    assert not walle.facing_us(look + walle.LOOK_S - 0.01), "back to profile before he works"
    canvas = FakeCanvas(64, 32)
    walle.overlay(canvas, look + walle.TURN_S + 0.01)
    assert list(canvas.px.values()).count(walle.COLORS["L"]) >= 6, "both binocular lenses toward us"
    blink = FakeCanvas(64, 32)
    walle.overlay(blink, look + walle.BLINK_AT + walle.BLINK_S / 2)
    assert walle.COLORS["L"] not in blink.px.values(), "and blinks while he's facing us"
    assert walle.facing_us(look + walle.BLINK_AT + walle.BLINK_S)


def test_walle_side_bobs_his_head_once():
    walle = _walle_side()
    look = walle.phase_start("look")
    bobs = [walle.head_bob(look + f / animation.FPS) for f in range(int(walle.LOOK_S * animation.FPS))]
    assert 1 in bobs and bobs[0] == 0 and bobs[-1] == 0


def test_walle_side_works_like_a_baler_in_order():
    walle = _walle_side()
    names = [name for name, _ in walle.PHASES]
    assert names.index("open") < names.index("compact") < names.index("close") < names.index("press") \
        < names.index("eject") < names.index("pickup") < names.index("leave")
    assert walle.duration == pytest.approx(5.5)


def test_walle_side_door_is_open_to_collect_and_eject_and_shut_to_press():
    walle = _walle_side()
    during = lambda name: walle.phase_start(name) + 0.05
    assert not walle.door_open(during("look"))
    assert walle.door_open(during("compact")) and walle.door_open(during("eject"))
    shut = lambda name: walle.phase_start(name) + walle.DOOR_SWING_S + 0.01
    assert not walle.door_open(shut("press")) and not walle.door_open(shut("pickup"))
    canvas = FakeCanvas(64, 32)
    walle.overlay(canvas, during("compact"))
    yellow = lambda cells: all(canvas.px.get((walle.STOP_X + c, walle.y0 + r)) == walle.COLORS["Y"] for c, r in cells)
    hx, hy = walle.DOOR_HINGE
    assert yellow([(hx + i, hy) for i in range(walle.DOOR_LEN + 1)]), "flat open, joined to him by a yellow hinge"


def test_walle_side_door_swings_rather_than_popping_open():
    walle = _walle_side()
    opening = walle.phase_start("open")
    angles = [walle.door_angle(opening + f / 240) for f in range(int(walle.DOOR_SWING_S * 240) + 1)]
    assert angles == sorted(angles) and walle.door_angle(opening + walle.DOOR_SWING_S) == pytest.approx(1.0)
    cells = {tuple(walle.door_cells(a)) for a in angles}
    assert len(cells) >= 3, "shut, part way and flat: it moves through the in-between"
    assert walle.door_cells(0) == [(13, 14), (13, 13), (13, 12)], "shut, it's his front edge"
    for name in ("close", "pickup"):
        start = walle.phase_start(name)
        assert walle.door_angle(start + 0.001) > 0.5 and walle.door_angle(start + walle.DOOR_SWING_S) == pytest.approx(0)


def test_walle_side_everything_flies_into_his_chest():
    walle = _walle_side()
    t = walle.phase_start("compact") + walle.SWEEP_S / 2
    assert walle.flight_target(t) == walle.intake() == (walle.STOP_X + walle.INTAKE[0], walle.y0 + walle.INTAKE[1])
    done = FakeCanvas(64, 32)
    walle.overlay(done, walle.phase_start("close"))
    assert (200, 100, 50) not in done.px.values(), "every pixel of the old screen went in"


def test_walle_side_jolts_while_the_press_works():
    walle = _walle_side()
    press = walle.phase_start("press")
    jolts = {walle.jolt(press + f / animation.FPS) for f in range(int(walle.PRESS_S * animation.FPS))}
    assert jolts == {0, 1}
    assert walle.jolt(walle.phase_start("eject") + 0.05) == 0


def test_walle_side_cube_comes_out_his_front_and_lands_on_the_ground():
    walle = _walle_side()
    eject = walle.phase_start("eject")
    assert walle.cube_at(eject - 0.01) is None, "still inside him while he presses"
    x_start, _ = walle.cube_at(eject + 0.001)
    assert x_start + walle.CUBE_SIZE <= walle.FRONT_COL + 1, "starts inside his body"
    assert walle.cube_at(walle.phase_start("pickup") - 0.001) == pytest.approx(walle.CUBE_GROUND, abs=0.1)
    assert walle.CUBE_GROUND[1] + walle.CUBE_SIZE == walle.sprite_h, "sitting on the ground"
    canvas = FakeCanvas(64, 32)
    walle.overlay(canvas, eject + 0.05)
    front = walle.STOP_X + walle.FRONT_COL
    assert not [x for (x, y), rgb in canvas.px.items() if rgb == (160, 80, 40) and x <= front], \
        "only the part past his front shows as it comes out"


def test_walle_side_reaches_down_for_the_cube_and_carries_it_off():
    walle = _walle_side()
    pickup = walle.phase_start("pickup")
    drops = [walle.arm_drop(pickup + f / animation.FPS) for f in range(int(walle.PICKUP_S * animation.FPS))]
    assert max(drops) == walle.ARM_DROP and drops[0] == 0, "reaches all the way down"
    claw_tip = walle.ARM_ROWS[-1] + walle.ARM_DROP
    assert claw_tip + 1 == walle.CUBE_GROUND[1], "the claw meets the top of the cube"
    t = walle.phase_start("leave") + 0.05
    cube_x, cube_y = walle.cube_at(t)
    assert cube_y == walle.ARM_ROWS[-1] + 1, "hanging from the claw, lifted clear of the ground"
    canvas = FakeCanvas(64, 32)
    walle.overlay(canvas, t)
    cube = [x for (x, y), rgb in canvas.px.items() if rgb == (160, 80, 40)]
    assert cube and min(cube) >= int(walle.walle_x(t)) + walle.FRONT_COL, "out in front of him"
    assert walle.PLANT_RGB["leaf"] in canvas.px.values()


def test_walle_side_arm_moving_leaves_his_body_outline_alone():
    walle = _walle_side()
    t = walle.phase_start("pickup") + walle.PICKUP_S / 2
    canvas = FakeCanvas(64, 32)
    walle.overlay(canvas, t)
    front = walle.STOP_X + walle.FRONT_COL
    assert all(canvas.px.get((front, walle.y0 + row)) is not None for row in walle.ARM_ROWS), "no hole in his front"


@pytest.mark.parametrize("cls", [animation.WallEReveal, animation.WallESideReveal])
def test_walle_leaves_the_board_black_then_uncovers_the_new_screen_as_he_rolls_out(cls):
    walle = cls(64, 32, random.Random(1))
    walle.capture_prev(_striped_screen, 0.0)
    new = (1, 2, 3)

    def frame(t):
        canvas = FakeCanvas(64, 32)
        fill(new)(canvas, 0)
        walle.overlay(canvas, t)
        return canvas.px

    ate = walle.ENTER_S + walle.LOOK_S
    for t in (ate + walle.COMPACT_S / 2, ate + walle.COMPACT_S + walle.DROP_S / 2):
        assert new not in frame(t).values(), "blank while he eats and drops the cube"
    t = walle.duration - walle.LEAVE_S / 2
    px, rear = frame(t), int(walle.walle_x(t))
    assert px[(0, 0)] == new, "uncovered behind him"
    assert px[(63, 0)] != new, "still blank ahead of him"
    assert all(px[(x, 0)] == new for x in range(rear)), "a clean wake, no gaps"
    assert list(frame(walle.duration - 0.01).values()).count(new) > 64 * 32 * 0.6, "all but uncovered by the end"


def _army_men(height=32, seed=1):
    army = animation.ArmyMenReveal(64, height, random.Random(seed))
    army.capture_prev(_striped_screen, 0.0)
    army.capture_new(fill((10, 20, 30)), 0.0)
    return army


def _army_frame(army, t):
    canvas = FakeCanvas(army.width, army.height)
    army.overlay(canvas, t)
    return canvas.px


@pytest.mark.parametrize("height", [32, 64])
def test_army_men_finishes_and_never_draws_off_board(height):
    army = _army_men(height)
    for f in range(int(army.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert army.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert army.overlay(FakeCanvas(64, height), army.duration) is False


def test_army_men_art_is_uniform_and_every_cell_has_a_colour():
    for art in (animation.ArmyMenReveal.CANOPY_ART, animation.ArmyMenReveal.SOLDIER_ART):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(animation.ArmyMenReveal.COLORS)


def test_army_men_canopy_and_soldier_never_share_colour_keys():
    canopy = set("".join(animation.ArmyMenReveal.CANOPY_ART)) - {"."}
    soldier = set("".join(animation.ArmyMenReveal.SOLDIER_ART)) - {"."}
    assert not canopy & soldier, "the canopy's olive would otherwise repaint his plastic green"


def test_army_men_features_stand_out_from_what_they_sit_on():
    colors = animation.ArmyMenReveal.COLORS

    def distance(a, b):
        return sum(abs(x - y) for x, y in zip(colors[a], colors[b]))

    assert distance("*", "M") > 400, "the star against its roundel"
    assert distance("R", "G") > 100, "the rifle against his chest"
    assert distance("D", "L") > 150, "the helmet brim against the lit dome of the helmet"
    assert distance("G", "K") > 150, "his plastic against his outline"


def test_army_men_rifle_pokes_out_past_his_body_at_both_ends():
    art = animation.ArmyMenReveal.SOLDIER_ART
    cells = [(x, y) for y, row in enumerate(art) for x, ch in enumerate(row) if ch == "S"]
    assert any(x > len(art[0]) - 3 and y < 5 for x, y in cells), "the muzzle past his shoulder"
    assert any(x < 2 and y > 9 for x, y in cells), "the stock past his hip"


def test_army_men_stand_on_a_base():
    art = animation.ArmyMenReveal.SOLDIER_ART
    assert "BBBBBBBBB" in art[-2], "the molded base under his feet"


def test_army_men_opts_into_receiving_both_the_old_and_new_screens():
    assert animation.ArmyMenReveal.wants_prev is True
    assert animation.ArmyMenReveal.wants_new is True
    assert "army_men" in animation.TRANSITIONS


def test_army_men_three_soldiers_land_staggered_not_all_at_once():
    army = _army_men()
    land_times = [army._unit_land_time(delay) for _, delay in army.UNITS]
    assert len(set(land_times)) == 3, "three distinct landing times, not simultaneous"
    assert land_times == sorted(land_times), "left to right"
    assert max(land_times) == pytest.approx(army.DROP_S)


@pytest.mark.parametrize("height", [32, 64])
def test_army_men_soldiers_fall_from_above_the_board_to_the_ground(height):
    army = _army_men(height)
    for _, delay in army.UNITS:
        assert army._soldier_top(delay, delay) + army.soldier_h <= 0, "starts above the board"
        land_t = army._unit_land_time(delay)
        assert army._soldier_top(delay, land_t) == pytest.approx(army.height - army.soldier_h), "base on the bottom row"
        tops = [army._soldier_top(delay, delay + f / 30) for f in range(int(army.FALL_S * 30) + 1)]
        assert tops == sorted(tops), "never rises while falling"


@pytest.mark.parametrize("height", [32, 64])
def test_army_men_three_canopies_never_overlap(height):
    army = _army_men(height)
    for f in range(int(army.DROP_S * animation.FPS)):
        t = f / animation.FPS
        spans = []
        for i, (frac, delay) in enumerate(army.UNITS):
            if t < army._unit_land_time(delay):
                dx, _ = army._sway(i, delay, t)
                cx0 = int(round(frac * army.width + dx)) - army.canopy_w // 2
                spans.append((cx0, cx0 + army.canopy_w))
        spans.sort()
        assert all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), f"canopies touch at t={t:.2f}"


def test_army_men_rigging_joins_each_canopy_to_its_soldier():
    army = _army_men(height=64)
    delay = army.UNITS[1][1]
    t = delay + army.FALL_S * 0.6
    px = _army_frame(army, t)
    top = int(round(army._soldier_top(delay, t)))
    hem = top - army.RIG_GAP
    rig_rows = {y for (x, y), rgb in px.items() if rgb == army.RIG_RGB}
    assert set(range(hem, top)) <= rig_rows, "an unbroken run of rigging from hem to helmet"


def test_army_men_swing_like_a_pendulum_then_land_upright():
    army = _army_men()
    delay = army.UNITS[0][1]
    swings = [army._sway(0, delay, delay + f / 30) for f in range(int(army.FALL_S * 30 * 0.6))]
    assert max(abs(c) for c, _ in swings) > 1, "the canopy swings while he falls"
    assert all(abs(s) <= abs(c) + 1e-9 or abs(s) < 1 for c, s in swings), "he swings less than it does"
    assert army._sway(0, delay, army._unit_land_time(delay)) == (0.0, 0.0), "upright at touchdown"


def test_army_men_curtain_uncovers_the_new_screen_top_down_as_the_lead_soldier_falls():
    army = _army_men()
    land_t = army._unit_land_time(army.UNITS[0][1])
    ys = [army._curtain_y(t) for t in (0.0, land_t * 0.3, land_t * 0.6, land_t, army.duration - 0.01)]
    assert ys == sorted(ys), "the curtain only ever uncovers more, never less"
    assert ys[0] == 0, "nothing uncovered before he starts falling"
    assert ys[-1] == army.height, "fully uncovered once he's landed"


def test_army_men_new_screen_above_the_curtain_old_screen_below_it():
    army = _army_men()
    old_rgb, new_rgb = (200, 100, 50), (10, 20, 30)
    t = army._unit_land_time(army.UNITS[0][1]) * 0.5
    px = _army_frame(army, t)
    cy = army._curtain_y(t)
    assert 0 < cy < army.height, "test picked a moment mid-reveal"
    above = [rgb for (x, y), rgb in px.items() if y < cy and rgb in (old_rgb, new_rgb)]
    below = [rgb for (x, y), rgb in px.items() if y >= cy and rgb in (old_rgb, new_rgb)]
    assert new_rgb in above and old_rgb not in above
    assert old_rgb in below and new_rgb not in below


def test_army_men_chute_slumps_downwind_and_sinks_behind_him():
    army = _army_men(height=64)
    home = int(army.UNITS[0][0] * army.width)
    army._cy = army.height

    def chute(p):
        canvas = FakeCanvas(64, 64)
        army._draw_collapsing_chute(canvas, home, p)
        return canvas.px

    early, late = chute(0.1), chute(0.45)
    mean = lambda px, i: sum(k[i] for k in px) / len(px)
    assert mean(late, 0) > mean(early, 0), "blows off downwind, the way they'll hop"
    assert mean(late, 1) > mean(early, 1), "sinks toward the ground"
    assert max(y for _, y in chute(0.9)) == army.height - 1, "ends up lying on the ground"
    star = army.COLORS["*"]
    assert star not in early.values(), "the star folds away as soon as it deflates"


def test_army_men_chutes_are_gone_after_each_soldiers_own_collapse():
    army = _army_men(height=64)
    frac, delay = army.UNITS[0]
    land_t = army._unit_land_time(delay)
    home = int(frac * army.width)
    olive = army.COLORS["N"]

    def his_chute(t):
        px = _army_frame(army, t)
        return any(rgb == olive for (x, y), rgb in px.items() if abs(x - home) < army.canopy_w // 2)

    assert his_chute(land_t - 0.05), "chute up just before he lands"
    assert not his_chute(land_t + army.COLLAPSE_S + 0.02), "and gone once it's deflated"


def test_army_men_landing_kicks_up_dust_that_blends_with_the_screen():
    army = _army_men()
    land_t = army._unit_land_time(army.UNITS[0][1])
    new_rgb = (10, 20, 30)

    def dusty(t):
        return [rgb for (x, y), rgb in _army_frame(army, t).items()
                if y >= army.height - 4 and rgb not in (new_rgb, (200, 100, 50))
                and rgb[0] > rgb[1] > rgb[2] and rgb[0] > 40]

    assert not dusty(land_t - 0.02), "no dust before he lands"
    puff = dusty(land_t + army.DUST_S * 0.3)
    assert puff, "a puff at touchdown"
    assert all(rgb != army.DUST_RGB for rgb in puff), "blended over the screen, not painted solid"


def test_army_men_hop_off_in_step_after_everyone_has_landed():
    army = _army_men()
    assert army._hop(army.DROP_S) == (0, 0), "no hopping while the last one is landing"
    start = army.DROP_S + army.LAND_S
    xs = [army._hop(start + f / 30)[0] for f in range(int(army.MARCH_S * 30))]
    assert xs == sorted(xs), "always forward"
    mid_hop = [army._hop(start + (k + 0.5) * army.HOP_S)[1] for k in range(army.HOPS)]
    assert all(lift > 0 for lift in mid_hop), "each hop leaves the ground"
    between = [army._hop(start + k * army.HOP_S + 0.001)[1] for k in range(1, army.HOPS)]
    assert all(lift == 0 for lift in between), "and comes back down between hops"
    assert army._march_x(army.duration - 0.001) + min(int(f * 64) for f, _ in army.UNITS) \
        - army.HELMET_COL > army.width - army.soldier_w, "they've hopped off the right edge by the end"


def test_army_men_fall_slower_on_the_taller_board_so_they_do_not_plummet():
    short, tall = _army_men(32), _army_men(64)
    assert tall.FALL_S > short.FALL_S
    assert tall.duration == pytest.approx(tall.DROP_S + tall.LAND_S + tall.MARCH_S)
    speed = lambda a: a.height / a.FALL_S  # rows a second, top of the board to the ground
    assert speed(tall) < 1.75 * speed(short), "not twice the speed just because it's twice as far"


def _half_lit_screen(canvas, t):
    """An old screen lit only on its left half: its dark right half must stay dark."""
    for y in range(canvas.height):
        for x in range(canvas.width // 2):
            canvas.SetPixel(x, y, 200, 100, 50)
    return False


@pytest.mark.parametrize("transition,t", [("army_men", 0.3), ("falcon", 1.2)])
def test_new_screen_never_shows_through_the_old_screens_dark_pixels(transition, t):
    # show_screen draws the new screen first and the transition paints over it, so a
    # transition that draws only the old screen's lit pixels lets the new one bleed through.
    matrix = FakeMatrix()
    animation.show_screen(matrix, _half_lit_screen, 0.05)
    matrix.frames.clear()
    new = (1, 2, 3)
    animation.show_screen(matrix, fill(new), t + 0.1, transition=transition, rng=random.Random(1))
    frame = matrix.frames[int(t * animation.FPS)]
    low = [(x, y) for (x, y), rgb in frame.items() if rgb == new and x >= 40 and y >= 26]
    assert not low, "the new screen leaked into the old screen's dark half"


def _falcon(height=32, seed=1):
    falcon = animation.FalconReveal(64, height, random.Random(seed))
    falcon.capture_prev(_striped_screen, 0.0)
    falcon.capture_new(fill((10, 20, 30)), 0.0)
    return falcon


@pytest.mark.parametrize("height", [32, 64])
def test_falcon_finishes_and_never_draws_off_board(height):
    falcon = _falcon(height)
    for f in range(int(falcon.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        assert falcon.overlay(canvas, f / animation.FPS) is True
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
    assert falcon.overlay(FakeCanvas(64, height), falcon.duration) is False


def test_falcon_art_is_uniform_and_every_cell_has_a_colour():
    art = animation.FalconReveal.ART
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(animation.FalconReveal.COLORS)


def test_falcon_keeps_her_silhouette():
    art = animation.FalconReveal.ART
    mid = len(art) // 2
    assert art[mid].rstrip(".").endswith("K") and art[mid].rstrip(".") != art[mid], "the gap between the mandibles"
    assert art[mid - 1].rstrip(".") > art[mid].rstrip(".") and len(art[mid - 1].rstrip(".")) > len(art[mid].rstrip(".")) + 5
    assert "W" in art[-2], "the cockpit tube hangs off the bottom edge, her starboard side seen from above"
    assert all(row.lstrip(".").startswith("E") for row in art[5:16]), "the engine band runs along her back"


def test_falcon_features_stand_out_from_her_hull():
    colors = animation.FalconReveal.COLORS

    def distance(a, b):
        return sum(abs(x - y) for x, y in zip(colors[a], colors[b]))

    assert distance("W", "K") > 150, "cockpit windows against the tube's outline, not holes in it"
    assert distance("E", "H") > 200, "the engine band against the hull"
    assert distance("R", "H") > 200, "red markings against the hull"
    assert distance("D", "L") > 250, "the turret ring against its light centre"


def test_falcon_opts_into_receiving_both_screens():
    assert animation.FalconReveal.wants_prev is True
    assert animation.FalconReveal.wants_new is True
    assert "falcon" in animation.TRANSITIONS


@pytest.mark.parametrize("height,scale", [(32, 1), (64, 2)])
def test_falcon_doubles_on_64x64_and_stays_whole_while_she_cruises(height, scale):
    falcon = _falcon(height)
    assert falcon.scale == scale
    assert falcon.ship_h <= height
    for name in ("cruise", "charge"):
        for f in range(10):
            rear, nose = falcon.ship_span(falcon.phase_start(name) + f / 10 * dict(falcon.PHASES)[name])
            assert rear >= 0 and nose <= 64, "her mandibles and engine band stay on the board"


def test_falcon_arrives_as_a_streak_that_snaps_into_the_ship():
    falcon = _falcon()
    rear, nose = falcon.ship_span(0.1)
    assert nose - rear > falcon.ship_w * 3, "a long streak first"
    rear, nose = falcon.ship_span(falcon.phase_start("cruise"))
    assert nose - rear == falcon.ship_w, "her own length once she's braked"


def test_falcon_story_plays_in_order():
    falcon = _falcon()
    assert [n for n, _ in falcon.PHASES] == ["arrive", "cruise", "charge", "jump", "flash"]
    cool, hot = falcon.engine_rgb(falcon.phase_start("cruise")), falcon.engine_rgb(falcon.phase_start("jump"))
    assert sum(hot) > sum(cool) + 150, "the engine band flares before she jumps"
    assert falcon.old_stretch(falcon.phase_start("jump") - 0.01) == (0.0, 1.0), "the old screen holds still until the jump"
    shift, stretch = falcon.old_stretch(falcon.phase_start("jump") + falcon.JUMP_S * 0.7)
    assert shift > 0 and stretch > 2, "then streaks off to the right"


def test_falcon_old_screen_is_gone_by_the_end_of_the_jump():
    falcon = _falcon()
    canvas = FakeCanvas(64, 32)
    falcon.overlay(canvas, falcon.phase_start("flash") - 0.01)
    assert (200, 100, 50) not in canvas.px.values()


def test_falcon_flash_fades_to_the_new_screen():
    falcon = _falcon()
    new = (10, 20, 30)
    start, end = FakeCanvas(64, 32), FakeCanvas(64, 32)
    falcon.overlay(start, falcon.phase_start("flash") + 0.01)
    falcon.overlay(end, falcon.duration - 0.01)
    assert sum(start.px[(5, 5)]) > 600, "a white flash"
    assert sum(abs(a - b) for a, b in zip(end.px[(5, 5)], new)) < 10, "fading to the new ride"


def test_falcon_stars_snap_from_streaks_to_points_then_fade():
    falcon = _falcon()

    def stars(p):
        canvas = FakeCanvas(64, 32)
        falcon._draw_stars(canvas, p)
        return canvas.px

    assert len(stars(0.02)) > 3 * falcon.STARS, "streaks at first"
    assert len(stars(0.6)) == falcon.STARS, "then one point each"
    assert not any(sum(rgb) for rgb in stars(1.0).values()), "and gone by the time she's braked"


@pytest.mark.parametrize("plays_under", [False, True])
def test_a_screen_can_ask_to_keep_playing_while_the_wipe_uncovers_it(plays_under):
    seen = []

    def screen(canvas, t):
        seen.append(t)
        return True
    if plays_under:
        screen.plays_under_reveal = True
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((1, 2, 3)), 0.1)  # something for the sweep to cover
    seen.clear()
    animation.show_screen(matrix, screen, animation.COVER_S + animation.WIPE_S + 0.2)
    # The screen isn't drawn during the sweep, so its first frames are the wipe's.
    during_wipe = [t for t in seen[:int(animation.WIPE_S * animation.FPS) - 1] if t > 0]
    if plays_under:
        assert during_wipe, "its clock runs from the start of the wipe"
    else:
        assert not during_wipe, "held at its first frame until it's uncovered"
