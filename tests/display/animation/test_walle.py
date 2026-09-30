"""WALL-E (both of him)."""

import math
import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, _striped_screen, fill


def test_walle_opts_into_receiving_the_previous_screen():
    assert animation.WallEReveal.wants_prev is True
    assert animation.TRANSITIONS["walle"] is animation.WallEReveal


def _walle(height=32, seed=1, screen=_striped_screen):
    walle = animation.WallEReveal(64, height, random.Random(seed))
    walle.capture_prev(screen, 0.0)
    return walle


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


def _walle_colour_distance(a, b):
    colors = animation.WallEReveal.COLORS
    return sum(abs(x - y) for x, y in zip(colors.get(a, a), colors.get(b, b)))


def test_walle_features_stand_out_from_what_they_sit_on():
    assert _walle_colour_distance("L", "E") > 200, "lens against its housing"
    assert _walle_colour_distance("G", "L") > 300, "glint against the lens"
    assert _walle_colour_distance("Y", "K") > 300, "body against his outline"
    assert _walle_colour_distance("D", "Y") > 60, "shaded side against the lit front"
    assert _walle_colour_distance(animation.WallEReveal.PLANT_RGB["leaf"], "Y") > 150, "sprout against his body"
    assert _walle_colour_distance(animation.WallEReveal.CUBE_EDGE_RGB, "K") > 150, "cube against his outline"


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
