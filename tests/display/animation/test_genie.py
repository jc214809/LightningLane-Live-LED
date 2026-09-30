"""Genie."""

import math
import random

import display.animation as animation

from tests.display.animation.support import FLYBYS, FakeCanvas, fill


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
