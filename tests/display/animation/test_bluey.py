"""Bluey and Bingo."""
import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill

GRANNIES = animation.GranniesReveal


def distance(colors, a, b):
    return sum(abs(x - y) for x, y in zip(colors[a], colors[b]))


@pytest.mark.parametrize("attr, colors", [
    ("BINGO_ART", "BINGO_COLORS"), ("BIG_BINGO_ART", "BINGO_COLORS"),
    ("WALKER_ART", "BINGO_COLORS"), ("BIG_WALKER_ART", "BINGO_COLORS"),
    ("BLUEY_ART", "BLUEY_COLORS"), ("BIG_BLUEY_ART", "BLUEY_COLORS"),
])
def test_grannies_art_is_uniform_and_every_cell_has_a_colour(attr, colors):
    art = getattr(GRANNIES, attr)
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(getattr(GRANNIES, colors))


def test_the_grannies_are_registered_and_a_rare_surprise():
    import disney
    assert animation.TRANSITIONS["grannies"] is GRANNIES
    assert 0 < disney.SURPRISES["grannies"] <= 0.005


@pytest.mark.parametrize("attr", ["BLUEY_ART", "BIG_BLUEY_ART"])
def test_bluey_faces_the_way_they_walk_with_her_nose_showing(attr):
    art = getattr(GRANNIES, attr)
    nose = [row.rfind("J") for row in art if "J" in row]
    eyes = [row.find("P") for row in art if "P" in row]
    assert min(nose) > max(eyes), "snout out to the right, ahead of her eyes"
    assert distance(GRANNIES.BLUEY_COLORS, "J", "T") > 200, "nose against the snout it sits on"
    assert sum(GRANNIES.BLUEY_COLORS["J"]) > 150, "lifted off black, which the board draws as off"


@pytest.mark.parametrize("attr", ["BINGO_ART", "BIG_BINGO_ART"])
def test_bingos_eyes_sit_in_white_inside_her_purple_hood(attr):
    art = getattr(GRANNIES, attr)
    for r, row in enumerate(art):
        for c, ch in enumerate(row):
            if ch == "P":
                assert "W" in (row[c - 1], row[c + 1]), "a pupil in the white of her eye"
    assert distance(GRANNIES.BINGO_COLORS, "P", "W") > 600


@pytest.mark.parametrize("height", [32, 64])
def test_the_pair_fits_the_board_and_64x64_gets_the_full_pattern(height):
    run = GRANNIES(64, height)
    assert len(run.bluey) <= height and run.pair_w < 64
    assert len(run.bluey) == (40 if height == 64 else 24)
    assert len(run.walker) < len(run.bingo), "the frame comes up to her hand"


@pytest.mark.parametrize("height", [32, 64])
def test_they_shuffle_slowly_in_from_the_left_and_off_the_right(height):
    run = GRANNIES(64, height)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS) + 1)]
    assert run.bingo_x(0) == -run.pair_w and run.bluey_x(0) + run.bluey_w <= 0, "starting off the left"
    assert run.bingo_x(run.duration) >= 64, "Bingo, last, gone off the right"
    for x_at in (run.bingo_x, run.bluey_x):
        steps = {x_at(b) - x_at(a) for a, b in zip(frames, frames[1:])}
        assert steps <= {0, 1}, "never back, never more than a pixel a frame"
    assert 8 <= run.duration <= 12, "a granny's pace, about 10 pixels a second"
    assert run.hold_after_s > 0, "so the ride still gets its screen after they leave"


@pytest.mark.parametrize("height", [32, 64])
def test_bingo_lifts_her_walker_plants_it_ahead_then_shuffles_up_to_it(height):
    run = GRANNIES(64, height)
    step = [k / animation.FPS for k in range(run.step_f)]
    assert all(run.walker_ahead(t)[1] == 1 and run.bingo_pose(t) is None for t in step[:run.lift_f]), \
        "the frame is up and moving while she stands"
    assert run.walker_ahead(step[run.lift_f]) == (run.step, 0), "planted a whole step ahead"
    assert run.bingo_x(step[-1]) > run.bingo_x(step[run.lift_f]), "then she shuffles up to it"
    assert run.walker_ahead(run.step_f / animation.FPS) == (0, 1), "caught up, and lifts it again"
    assert {run.bingo_pose(t) % 4 for t in step[run.lift_f:]} == {0, 1, 2, 3}, "feet through the whole step"


@pytest.mark.parametrize("height", [32, 64])
def test_bingos_arm_reaches_after_the_walker_unbroken(height):
    run = GRANNIES(64, height)
    col, rows = run.sleeve
    for ahead in range(run.step + 1):
        pixels = {p for p, _ in run._bingo_pixels(0, 0, None, ahead)}
        row = rows[len(rows) // 2]
        reach = max(x for x, y in pixels if y == row)
        assert all((x, row) in pixels for x in range(col, reach + 1)), "no gap in the sleeve"
        assert reach == max(x for (x, y), _ in run._bingo_pixels(0, 0, None, 0) if y == row) + ahead


@pytest.mark.parametrize("height", [32, 64])
def test_bluey_never_bumps_the_walker_and_they_bob_out_of_step(height):
    run = GRANNIES(64, height)
    frames = [f / animation.FPS for f in range(int(run.duration * animation.FPS))]
    walker_w = len(run.walker[0])
    for t in frames:
        assert run.bingo_x(t) + run.walker_x + run.walker_ahead(t)[0] + walker_w <= run.bluey_x(t)
    for art, feet in ((run.bingo, run.bingo_feet), (run.bluey, run.bluey_feet)):
        poses = {frozenset(animation.walking_pixels(art, 0, 0, {k: (1, 1, 1) for k in "".join(art)}, feet, p))
                 for p in range(4)}
        assert len(poses) == 4, "every pose of the shuffle moves the feet"
    moving = [t for t in frames if run.bingo_pose(t) is not None]
    assert any(run.bingo_pose(t) % 2 != run.bluey_pose(t) % 2 for t in moving), "not in lockstep"


@pytest.mark.parametrize("height", [32, 64])
def test_the_ride_is_uncovered_behind_them_and_they_stay_on_the_board(height):
    run = GRANNIES(64, height)
    ride = (0, 140, 0)
    t = run.duration / 2
    canvas = FakeCanvas(64, height)
    fill(ride)(canvas, t)
    run.overlay(canvas, t)
    assert canvas.px[(0, 0)] == ride, "behind them"
    assert canvas.px[(63, 0)] == (0, 0, 0), "still dark ahead of Bluey"
    for f in range(int(run.duration * animation.FPS)):
        c = FakeCanvas(64, height)
        fill(ride)(c, f / animation.FPS)
        run.overlay(c, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
    end = FakeCanvas(64, height)
    fill(ride)(end, run.duration - 1 / animation.FPS)
    run.overlay(end, run.duration - 1 / animation.FPS)
    assert all(end.px[(x, 0)] == ride for x in range(64)), "all of it by the time they leave"
    assert run.overlay(FakeCanvas(64, height), run.duration) is False


KEEPY = animation.KeepyUppyReveal


@pytest.mark.parametrize("attr, colors", [
    ("BINGO_ART", "BINGO_COLORS"), ("BIG_BINGO_ART", "BINGO_COLORS"),
    ("BLUEY_ART", "BLUEY_COLORS"), ("BIG_BLUEY_ART", "BLUEY_COLORS"),
    ("BALLOON_ART", "BALLOON_COLORS"), ("BIG_BALLOON_ART", "BALLOON_COLORS"),
])
def test_keepy_uppy_art_is_uniform_and_every_cell_has_a_colour(attr, colors):
    art = getattr(KEEPY, attr)
    assert len({len(row) for row in art}) == 1
    assert set("".join(art)) - {"."} <= set(getattr(KEEPY, colors))


def test_keepy_uppy_is_registered_and_the_rarest_surprise():
    import disney
    assert animation.TRANSITIONS["keepy_uppy"] is KEEPY
    assert disney.SURPRISES["keepy_uppy"] == 0.001


def test_the_balloon_is_red_and_stands_out_from_both_of_them():
    red = KEEPY.BALLOON_COLORS["R"]
    assert red[0] > 200 and red[1] < 60 and red[2] < 60
    fur = [KEEPY.BINGO_COLORS[k] for k in "BOTC"] + [KEEPY.BLUEY_COLORS[k] for k in "NML"]
    assert all(sum(abs(a - b) for a, b in zip(red, c)) > 100 for c in fur), "against their fur and gowns"


@pytest.mark.parametrize("height", [32, 64])
def test_they_fit_side_by_side_and_leave_the_balloon_room_above(height):
    run = KEEPY(64, height)
    assert run.bingo_stop + run.bingo_w <= run.bluey_stop, "never overlapping"
    assert run.bluey_stop + run.bluey_w <= 64 and run.bingo_stop >= 0
    tallest = max(len(run.bingo), len(run.bluey))
    assert height - tallest >= len(run.balloon) - 2, "room for the balloon over their heads"


@pytest.mark.parametrize("height", [32, 64])
def test_they_run_in_play_facing_each_other_and_run_off_after_it(height):
    run = KEEPY(64, height)
    assert run.bluey_x(0) + run.bluey_w <= 0, "from off the left"
    assert run.bluey_facing(0) == 1, "facing the way they run"
    assert all(run.bluey_facing(at) == -1 for at in run.contacts), "turned to Bingo for every hit"
    assert run.bluey_facing(run.duration - 0.01) == 1, "turned to run off after it"
    assert run.bingo_x(run.duration) >= 64, "both gone off the right"
    assert len(run.HITS) >= 4 and all(a != b for a, b in zip(run.HITS, run.HITS[1:])), "taking turns"
    assert run.duration < 7, "leaves the ride screen time"


@pytest.mark.parametrize("height", [32, 64])
def test_the_balloon_meets_each_hitters_near_hand_and_rises_between_hits(height):
    run = KEEPY(64, height)
    middle = (run.bingo_stop + run.bingo_w + run.bluey_stop) / 2
    for at, who in zip(run.contacts, run.HITS):
        x, y = run.balloon_at(at)
        centre = x + run.balloon_w / 2
        assert (centre < middle) == (who == "bingo"), "over the hitter's side"
        assert run.lift(at, who) > 0, "the hitter hops to bat it"
        assert y + run.balloon_body <= height - min(len(run.bingo), len(run.bluey)) + 10, "up at hand height"
    for a, b in zip(run.contacts, run.contacts[1:]):
        peak = min(run.balloon_at(a + k * (b - a) / 10)[1] for k in range(1, 10))
        assert peak < min(run.balloon_at(a)[1], run.balloon_at(b)[1]) - 3, "up between hits"
        assert peak >= 0, "never off the top"
    x, _ = run.balloon_at(run.duration - 0.01)
    assert x >= 64 - run.balloon_w // 2 or run.contacts[-1] + run.FLY_S <= run.duration, "sailed off"


@pytest.mark.parametrize("height", [32, 64])
def test_keepy_uppy_uncovers_the_ride_and_stays_on_the_board(height):
    run = KEEPY(64, height)
    ride = (0, 140, 0)
    canvas = FakeCanvas(64, height)
    fill(ride)(canvas, run.run_s / 2)
    run.overlay(canvas, run.run_s / 2)
    assert canvas.px[(63, 0)] == (0, 0, 0), "still dark ahead of them"
    for f in range(int(run.duration * animation.FPS)):
        c = FakeCanvas(64, height)
        fill(ride)(c, f / animation.FPS)
        run.overlay(c, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
        if f / animation.FPS >= run.contacts[1]:
            assert all(c.px[(x, 0)] in (ride,) + tuple(run.BALLOON_COLORS.values()) for x in range(64)), \
                "all of the ride once the game's going"
    assert run.overlay(FakeCanvas(64, height), run.duration) is False
