"""The Green Army Men."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas, _striped_screen, fill


def _army_men(height=32, seed=1):
    army = animation.ArmyMenReveal(64, height, random.Random(seed))
    army.capture_prev(_striped_screen, 0.0)
    army.capture_new(fill((10, 20, 30)), 0.0)
    return army


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


def _army_frame(army, t):
    canvas = FakeCanvas(army.width, army.height)
    army.overlay(canvas, t)
    return canvas.px


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
