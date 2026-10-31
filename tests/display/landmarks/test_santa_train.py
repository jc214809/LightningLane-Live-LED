"""The Very Merry Christmas Party landmark: Santa's train drives in across a snowy night, engine first, and
stops on a billboard car with the party's name and hours."""

import math
import random

import pytest

import display.landmarks as landmarks
from display.landmarks import santa_train as st

from tests.display.landmarks.support import _scene_s

BOARDS = [(64, 32), (64, 64)]


def _scene(w, h, seed=3, park=None):
    return landmarks.SantaTrainLandmark(w, h, random.Random(seed), park=park)


def _party_park(opens="19:00", closes="23:59"):
    """Magic Kingdom on a party night, dated the park's today (test_pumpkins.py's, with the times to choose)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    return {"name": "Magic Kingdom", "timezone": "America/New_York", "seasonalEvent": "christmas",
            "schedule": [{"type": "TICKETED_EVENT", "date": today, "description": "Special Ticketed Event",
                          "openingTime": f"{today}T{opens}:00-05:00", "closingTime": f"{today}T{closes}:00-05:00"}]}


def _text(scene):
    """The billboard's lettering, read back from its sign: the red and green pixels inside its frame."""
    frame = st.FRAME_PX[scene.height >= 64]
    letters = (st.COLORS["R"], st.COLORS["G"])
    return {(x, y): rgb for x, col in enumerate(scene.columns[:scene.width]) for y, rgb in col
            if y < scene.sign_h and rgb in letters
            and frame <= x < scene.width - frame and frame <= y < scene.sign_h - frame}


def _train(scene, t):
    """The board pixels the train covers at scene time t."""
    left = scene.train_x(t)
    return {(x, y) for x in range(max(0, left), min(scene.width, left + scene.train_w))
            for y, _ in scene.columns[x - left]}


@pytest.mark.parametrize("train", [st.TRAIN_64, st.TRAIN_32])
def test_the_pieces_are_rectangular_the_same_height_and_use_only_the_palette(train):
    assert len({len(piece) for piece in train}) == 1
    for piece in train:
        assert len({len(row) for row in piece}) == 1
        assert set("".join(piece)) - {"."} <= set(st.COLORS)
        assert any(ch != "." for ch in piece[-1]), "every piece reaches the rail"


def test_the_engine_leads_and_the_riders_follow_in_the_approved_order():
    assert st.TRAIN_64 == [st.PLUTO_64, st.GOOFY_64, st.TREE_64, st.DONALD_64, st.GIFT_64, st.MICKEY_64, st.ENGINE_64]
    assert st.TRAIN_32 == [st.PLUTO_32, st.GOOFY_32, st.TREE_32, st.DONALD_32, st.GIFT_32, st.MICKEY_32, st.ENGINE_32]


def test_64x64_plutos_head_shows_the_night_through_it_above_his_brow():
    assert "W" not in "".join(st.PLUTO_64[:18])
    assert st.PLUTO_64[15][19:24] == ".....", "background, not his ears' outline"


def test_64x32_plutos_neck_reaches_his_collar():
    chin, neck, collar = st.PLUTO_32[16:19]
    assert neck[6:9] == "ooo" and collar[6:9] == "XXX"


@pytest.mark.parametrize("engine, big", [(st.ENGINE_64, True), (st.ENGINE_32, False)])
def test_the_smoke_is_puffed_not_painted_and_starts_over_the_stack(engine, big):
    x, y = st.STACK[big]
    assert set("".join(engine[:y + 1])) == {"."}, "nothing above the stack"
    assert engine[y + 1][math.floor(x)] == engine[y + 1][math.ceil(x)] == "k", "the stack's top under it"


@pytest.mark.parametrize("w, h", BOARDS)
def test_a_smoke_puff_stays_where_it_was_puffed_rising_growing_and_fading_off_the_top(w, h, monkeypatch):
    monkeypatch.setattr(st, "PUFF_S", 100.0)  # one puff all its life
    scene = _scene(w, h)
    x0, y0 = scene.train_x(0) + scene.stack[0], scene.stack[1]
    sizes, tops, light = [], [], []
    for t in [scene.puff_life * k / 5 for k in range(5)]:
        puff = scene.puffs(t)
        xs, ys = [x for x, _ in puff], [y for _, y in puff]
        assert (min(xs) + max(xs)) / 2 == pytest.approx(x0, abs=1), "left behind as the train goes on"
        sizes.append(len(puff)), tops.append(min(ys)), light.append(max(sum(rgb) for rgb in puff.values()))
    assert any(math.hypot(x - x0, y - y0) <= 1 for x, y in scene.puffs(0)), "out of the stack"
    assert tops == sorted(tops, reverse=True) and sizes == sorted(sizes) and light == sorted(light, reverse=True)
    assert all(y < 0 for _, y in scene.puffs(scene.puff_life - 0.001)), "off the top by its end"
    assert not scene.puffs(scene.puff_life + 0.001)


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_train_fits_the_board_with_its_wheels_on_the_rail(w, h):
    scene = _scene(w, h)
    assert scene.train_y >= 0
    assert scene.train_y + scene.train_h == scene.rail_y
    assert scene.rail_y < h - 1, "snow under the rail"


@pytest.mark.parametrize("w, h", BOARDS)
def test_it_drives_in_from_the_left_and_stops_with_the_billboard_filling_the_board(w, h):
    scene = _scene(w, h)
    assert not _train(scene, 0.0), "starts off the board"
    first = min(t / 20 for t in range(200) if _train(scene, t / 20))
    assert min(x for x, _ in _train(scene, first)) == 0, "comes in on the left"
    end = _scene_s(scene)
    xs = [scene.train_x(t / 20) for t in range(int(end * 20))]
    assert xs == sorted(xs), "always left to right"
    assert scene.train_x(scene.drive_s) == 0 and scene.train_x(end) == 0, "stopped on the billboard to the end"
    assert end - scene.drive_s == pytest.approx(st.HOLD_S), "held to be read"
    assert scene.SCREEN_S == pytest.approx(st.COVER_AND_WIPE_S + scene.drive_s + st.HOLD_S)


@pytest.mark.parametrize("w, h", BOARDS)
def test_it_cruises_then_brakes_evenly_to_the_stop(w, h):
    scene = _scene(w, h)
    brake_at = scene.drive_s - 2 * scene.stop_px / scene.cruise
    assert scene.travelled(brake_at / 2) == pytest.approx(scene.cruise * brake_at / 2)
    step = 0.05
    speeds = [(scene.travelled(t + step) - scene.travelled(t)) / step
              for t in [brake_at + i * step for i in range(int((scene.drive_s - brake_at) / step))]]
    assert speeds == sorted(speeds, reverse=True) and speeds[-1] < scene.cruise / 10, "slowing to a stop"
    assert scene.travelled(scene.drive_s + 1) == scene.train_w


@pytest.mark.parametrize("w, h", BOARDS)
def test_every_part_of_the_train_crosses_the_board(w, h):
    scene = _scene(w, h)
    lefts = {scene.train_x(t / 60) for t in range(int(scene.drive_s * 60))}
    assert max(b - a for a, b in zip(sorted(lefts), sorted(lefts)[1:])) <= 2, "no jumps past a rider"


@pytest.mark.parametrize("w, h", BOARDS)
def test_a_frame_fills_the_board_and_draws_the_train_over_the_snow(w, h):
    scene = _scene(w, h)
    for t in (scene.drive_s / 2, scene.drive_s - 1.5):
        frame = scene.frame(t)
        assert len(frame) == w * h
        assert set(frame) == {(x, y) for x in range(w) for y in range(h)}
        left = scene.train_x(t)
        over = {(left + x, y): rgb for x, y, rgb in scene.spin[scene.spin_step(t)]}
        bulbs = {(left + x, y) for x, y in scene.bulbs}
        for x in range(max(0, left), min(w, left + scene.train_w)):
            for y, rgb in scene.columns[x - left]:
                if (x, y) not in bulbs:
                    assert frame[(x, y)] == over.get((x, y), rgb)
        assert all(frame[p] == rgb for p, rgb in over.items() if 0 <= p[0] < w)
    assert all(frame[(x, scene.rail_y)] == st.RAIL_RGB for x in range(w))


@pytest.mark.parametrize("w, h", BOARDS)
def test_snow_falls_only_in_the_sky(w, h):
    scene = _scene(w, h)
    assert scene.flakes
    for t in (0.0, 1.3, 4.7, scene.drive_s):
        frame = scene.frame(t)
        assert all(frame[(x, y)] == st.SNOW_RGB for x in range(w) for y in range(scene.rail_y + 1, h))
        assert all(frame[(x, scene.rail_y)] == st.RAIL_RGB for x in range(w)), "no flake on the rail"


@pytest.mark.parametrize("w, h", BOARDS)
def test_no_snow_or_stars_show_under_the_cars_between_the_wheels(w, h):
    scene = _scene(w, h)
    under = {(x, y) for x, column in enumerate(scene.columns) for y, rgb in column
             if rgb == st.SKY_RGB and y >= scene.rail_y - st.WHEEL_ROWS[h >= 64]}
    assert under, "the cars have dark under them"
    for t in [scene.drive_s * k / 40 for k in range(40)]:
        frame, left = scene.frame(t), scene.train_x(t)
        over = {(x + left, y) for x, y, _ in scene.spin[scene.spin_step(t)]}
        for x, y in under:
            if 0 <= x + left < w and (x + left, y) not in over:
                assert frame[(x + left, y)] == st.SKY_RGB, (t, x, y)


@pytest.mark.parametrize("train, big", [(st.TRAIN_64, True), (st.TRAIN_32, False)])
def test_no_stray_white_round_the_wheels(train, big):
    for piece in train:
        assert "W" not in "".join(piece[-st.WHEEL_ROWS[big]:]), "only the 64x32 rim spot is white down there"


@pytest.mark.parametrize("train, big", [(st.TRAIN_64, True), (st.TRAIN_32, False)])
def test_every_car_has_two_wheels_and_the_engine_three_drivers(train, big):
    assert [len(st.wheels(piece, big)) for piece in train] == [2] * 6 + [3]


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_wheels_roll_with_the_train(w, h):
    scene = _scene(w, h)
    steps = [scene.spin_step(i / 60) for i in range(int(scene.drive_s * 60))]
    assert set(steps) == set(range(st.SPIN_STEPS)), "every position shows"
    assert all((b - a) % st.SPIN_STEPS <= 2 for a, b in zip(steps, steps[1:])), "forward, a step or two a frame"
    turn = 2 * math.pi * scene.roll_r / scene.cruise  # one turn per its rolling circumference
    assert scene.spin_step(turn * 0.999) == st.SPIN_STEPS - 1 and scene.spin_step(turn * 1.001) == 0
    stopped = scene.spin_step(scene.drive_s)
    assert all(scene.spin_step(scene.drive_s + k / 4) == stopped for k in range(16)), "still once stopped"


def test_the_64x64_spoke_bar_turns_and_stays_inside_the_rim():
    for piece in st.TRAIN_64[:-1]:
        seen = set()
        for step in range(st.SPIN_STEPS):
            spokes = {p for p, rgb in st.spin_pixels(piece, True, step).items() if rgb == st.COLORS["S"]}
            assert all(piece[y][x] == "k" for x, y in spokes), "only on the wheel's dark inside"
            seen.add(frozenset(spokes))
        assert len(seen) >= 4, "the bar is seen at several angles"


def test_the_64x32_wheels_light_one_rim_pixel_going_round():
    piece = st.TRAIN_32[0]
    lit = []
    for step in range(st.SPIN_STEPS):
        white = [p for p, rgb in st.spin_pixels(piece, False, step).items() if rgb == st.COLORS["W"]]
        assert len(white) == len(st.wheels(piece, False)), "one per wheel"
        lit.append(min(white))
    assert len(set(lit)) == len(st.RIM_32), "every rim pixel in turn"


@pytest.mark.parametrize("big", [True, False])
def test_the_side_rod_goes_round_with_the_drivers(big):
    engine = (st.TRAIN_64 if big else st.TRAIN_32)[-1]
    drivers = st.wheels(engine, big)
    span = range(int(drivers[0][0]), int(drivers[-1][0]) + 1)
    rows = engine[-6:-3] if big else engine[-2:-1]
    assert not any(row[x] in "Rr" for row in rows for x in span), "the art leaves the rod out"
    places = set()
    for step in range(st.SPIN_STEPS):
        rod = {p for p, rgb in st.spin_pixels(engine, big, step, engine=True).items() if rgb == st.COLORS["R"]}
        assert rod and len({y for _, y in rod}) == 1, "one straight rod"
        places.add((min(rod), max(rod)))
    assert len(places) >= (4 if big else 2), "it moves"
    assert st.COLORS["R"] not in st.spin_pixels(st.TRAIN_64[0], True, 0).values(), "cars have no rod"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_billboard_fills_the_board_above_its_flatcar_once_stopped(w, h):
    scene = _scene(w, h, park=_party_park())
    frame = scene.frame(scene.drive_s + 1)
    sign = {(x, y) for x in range(w) for y in range(scene.sign_h)}
    assert all(frame[p] != st.SKY_RGB for p in sign), "no sky showing"
    inside = st.FRAME_PX[h >= 64]
    white = [p for p in sign if frame[p] == st.SIGN_RGB]
    assert min(x for x, _ in white) == inside and max(x for x, _ in white) == w - 1 - inside
    assert len(st.wheels(st.flatcar(st.MICKEY_64 if h >= 64 else st.MICKEY_32, st.DECK_ROW[h >= 64], w), h >= 64)) == 2


@pytest.mark.parametrize("w, h, lines", [(64, 64, 5), (64, 32, 4)])
def test_the_billboard_says_the_party_and_tonights_hours(w, h, lines):
    scene = _scene(w, h, park=_party_park("19:00", "23:59"))
    assert scene.hours == ("7PM", "12AM")
    text = _text(scene)
    rows = sorted({y for _, y in text})
    runs = 1 + sum(1 for a, b in zip(rows, rows[1:]) if b > a + 1)
    assert runs == lines, "the name's lines and the hours"
    without = _scene(w, h)
    assert without.hours is None
    rows = sorted({y for _, y in _text(without)})
    assert 1 + sum(1 for a, b in zip(rows, rows[1:]) if b > a + 1) == lines - 1, "the name alone"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_lettering_fits_inside_the_frame_and_alternates_red_and_green(w, h):
    font = st.SMALL_FONT if h >= 64 else st.TINY_FONT
    names = st.NAME[h >= 64] + ["12PM-12AM"]  # the widest hours
    lines = [(font, text, st.COLORS["R" if i % 2 == 0 else "G"]) for i, text in enumerate(names)]
    sign_h = _scene(w, h).sign_h
    frame = st.FRAME_PX[h >= 64]
    sign = st.sign_pixels(w, sign_h, lines, frame)
    letters = {p for p, rgb in sign.items() if rgb != st.SIGN_RGB
               and frame <= p[0] < w - frame and frame <= p[1] < sign_h - frame}
    assert letters, "lettering drawn"
    for x, y in letters:
        assert frame <= x < w - frame and frame <= y < sign_h - frame
    blank = st.sign_pixels(w, sign_h, [], frame)
    assert all(sign[p] == blank[p] for p in blank if not (frame <= p[0] < w - frame and frame <= p[1] < sign_h - frame)), "frame untouched"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_bulbs_chase_round_the_frame(w, h):
    scene = _scene(w, h)
    stopped = scene.drive_s + 0.5
    x, y = scene.bulbs[0]
    seen = {scene.frame(stopped + k / st.CHASE_HZ)[(x, y)] for k in range(len(st.BULBS))}
    assert seen == set(st.BULBS), "each colour in turn"
    assert all(min(bx, by, w - 1 - bx, scene.sign_h - 1 - by) == 0 for bx, by in scene.bulbs), "on the frame's edge"


def test_it_plays_after_the_wipe():
    assert landmarks.landmark_screen(_scene(64, 32)).plays_under_reveal is False


def test_the_christmas_party_finds_it():
    assert landmarks.landmark_for("Magic Kingdom", "christmas") is st.SantaTrainLandmark
