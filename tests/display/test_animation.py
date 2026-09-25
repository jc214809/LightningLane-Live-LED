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


FLYBYS = [animation.TinkReveal, animation.BuzzReveal, animation.FigmentReveal, animation.DumboReveal]


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


def test_slinky_stretches_out_then_snaps_shut():
    slinky = animation.SlinkyReveal(64, 32, random.Random(1))
    gaps = [slinky.gap(f / animation.FPS) for f in range(int(slinky.duration * animation.FPS))]
    peak = max(gaps)
    peak_at = gaps.index(peak)
    assert peak > 20, "the spring really pulls open across the board"
    assert gaps[0] < peak / 2, "starts bunched up"
    assert gaps[peak_at // 2] < peak, "grows into the stretch"
    assert gaps[-1] < peak / 2, "rear catches up and the coil compresses again"


def test_slinky_head_leads_the_rear_the_whole_way_across():
    slinky = animation.SlinkyReveal(64, 32, random.Random(2))
    for f in range(int(slinky.duration * animation.FPS)):
        t = f / animation.FPS
        assert slinky.head_x(t) >= slinky.rear_x(t), "the head always leads"
    assert slinky.head_x(0) < 1, "starts at the left edge"
    assert slinky.head_x(slinky.duration) + slinky.head_w >= 64, "nose clears the right edge"


def test_slinky_reveal_front_follows_the_stretch_across_the_board():
    fronts = []
    for height in (32, 64):
        slinky = animation.SlinkyReveal(64, height, random.Random(3))
        seen = []
        for f in range(int(slinky.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            fill((9, 9, 9))(canvas, 0)
            slinky.overlay(canvas, f / animation.FPS)
            revealed = [x for (x, y), rgb in canvas.px.items() if rgb == (9, 9, 9)]
            seen.append(max(revealed) if revealed else -1)
        assert seen == sorted(seen), "the reveal only ever moves right"
        assert seen[0] < 32 < seen[-1], "starts on the left and finishes past the far edge"
        fronts.append(seen)
    assert all(f[-1] >= 63 for f in fronts), "the whole board is revealed by the end"


def test_slinky_reveal_tracks_his_nose_rather_than_a_fixed_sweep():
    slinky = animation.SlinkyReveal(64, 64, random.Random(4))
    mid = slinky.STRETCH_S / 2
    canvas = FakeCanvas(64, 64)
    fill((9, 9, 9))(canvas, 0)
    slinky.overlay(canvas, mid)
    nose = int(round(slinky.head_x(mid) + slinky.head_w))
    assert canvas.px[(0, 0)] == (9, 9, 9), "behind him the new screen is showing"
    assert canvas.px[(min(63, nose + 2), 0)] == (0, 0, 0), "ahead of his nose is still dark"


def test_slinky_finishes_and_never_draws_outside_the_board():
    for height in (32, 64):
        slinky = animation.SlinkyReveal(64, height, random.Random(5))
        for f in range(int(slinky.duration * animation.FPS)):
            canvas = FakeCanvas(64, height)
            assert slinky.overlay(canvas, f / animation.FPS) is True
            for x, y in canvas.px:
                assert 0 <= x < 64 and 0 <= y < height
        assert slinky.overlay(FakeCanvas(64, height), slinky.duration) is False


def test_slinky_coils_spread_apart_when_stretched_and_bunch_when_short():
    slinky = animation.SlinkyReveal(64, 32, random.Random(6))

    def coil_xs(span):
        canvas = FakeCanvas(64, 32)
        slinky._draw_coils(canvas, 2, 2 + span, 16)
        return sorted({x for (x, _), rgb in canvas.px.items()
                       if rgb in (slinky.COIL_RGB, slinky.COIL_SHADE_RGB)})

    short, long = coil_xs(12), coil_xs(50)
    assert short and long
    assert max(long) - min(long) > max(short) - min(short), "a stretched spring spans further"
    # Ring centres are one step apart; a long spring's rings sit further from each other.
    assert (max(long) - min(long)) / max(1, len(long)) > (max(short) - min(short)) / max(1, len(short))


def test_slinky_art_rows_are_even_and_use_defined_colors():
    for art in (animation.SlinkyReveal.HEAD_ART, animation.SlinkyReveal.REAR_ART):
        assert len({len(row) for row in art}) == 1, "every row is the same width"
        assert {ch for row in art for ch in row} - {"."} <= set(animation.SlinkyReveal.COLORS)
    assert animation.TRANSITIONS["slinky"] is animation.SlinkyReveal


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
