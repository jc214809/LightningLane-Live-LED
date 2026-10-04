"""Rex."""
import pytest

import display.animation as animation
from display.animation.characters.rex import _open_jaw
from tests.display.animation.support import FakeCanvas, fill


def _frames(rex):
    return [f / animation.FPS for f in range(int(rex.duration * animation.FPS))]


def test_rex_is_registered_with_well_formed_art():
    cls = animation.TRANSITIONS["rex"]
    assert cls is animation.RexReveal
    for art in (cls.ART, cls.BIG_ART):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(cls.colors)


@pytest.mark.parametrize("height", [32, 64])
def test_rex_fits_his_board_standing_on_the_ground(height):
    rex = animation.RexReveal(64, height)
    assert len(rex.art) <= height and rex.w <= 64
    assert rex.y0 + len(rex.art) == height
    # Wide open, the lifted snout still fits under the top edge.
    assert rex.y0 - (len(rex.mouth(1.0)) - len(rex.art)) >= 0


@pytest.mark.parametrize("height", [32, 64])
def test_rex_stomps_in_from_the_left_stops_to_roar_and_leaves_right(height):
    rex = animation.RexReveal(64, height)
    xs = [rex.x_at(t) for t in _frames(rex)]
    assert xs == sorted(xs), "always heading right"
    assert xs[0] + rex.w <= 0 and rex.x_at(rex.duration) >= 64, "in from past the left edge, out past the right"
    # Facing the way he walks: his head (eyes, teeth) is on the right of him.
    whites = [c for row in rex.art for c, k in enumerate(row) if k == "W"]
    assert sum(whites) / len(whites) > rex.w / 2
    stopped = [t for t in _frames(rex) if rex.x_at(t) == rex.stop_x]
    assert stopped[-1] - stopped[0] >= rex.OPEN_S + rex.ROAR_S, "he stands still for the roar"
    assert abs(rex.stop_x + rex.w / 2 - 32) <= 1, "mid-board"


@pytest.mark.parametrize("height", [32, 64])
def test_his_jaw_opens_only_while_he_stands_and_roars(height):
    rex = animation.RexReveal(64, height)
    for t in _frames(rex):
        if rex.opening(t):
            assert rex.x_at(t) == rex.stop_x
    assert rex.opening(rex.roar_at + 0.1) == 1.0
    assert rex.opening(rex.stop_at - 0.01) == 0 and rex.opening(rex.leave_at) == 0


@pytest.mark.parametrize("big", [False, True])
def test_an_open_jaw_shows_his_mouth_with_teeth_below_it(big):
    cls = animation.RexReveal
    art, jaw = (cls.BIG_ART, cls.BIG_JAW) if big else (cls.ART, cls.JAW)
    shut, wide = (["".join(row) for row in _open_jaw(art, jaw, o)[0]] for o in (0.0, 1.0))
    assert "M" not in "".join(shut)
    mouth = [(r, c) for r, row in enumerate(wide) for c, k in enumerate(row) if k == "M"]
    assert len(mouth) >= 20, "a mouth you can see, not a line"
    # Wider at the front of his face than at the hinge, like a jaw swung open.
    rows_at = lambda c: sum(1 for _, mc in mouth if mc == c)
    cols = sorted({c for _, c in mouth})
    assert rows_at(cols[0] + 1) > rows_at(cols[-1])
    # Teeth along the bottom of the mouth (the lower jaw's) and along its top (the upper jaw's).
    below = [(r, c) for r, c in mouth if r + 1 < len(wide) and wide[r + 1][c] == "W"]
    above = [(r, c) for r, c in mouth if wide[r - 1][c] == "W"]
    assert len(below) >= 3 and len(above) >= 3
    assert "W" not in shut[jaw[0] - 1] or shut[jaw[0] - 1] == art[jaw[0] - 1], "shut, his art as drawn"
    # The rest of him doesn't move.
    assert wide[-1] == art[-1] and wide[len(art) // 2][-1] == art[len(art) // 2][-1]


@pytest.mark.parametrize("height", [32, 64])
def test_he_tips_his_head_back_to_roar(height):
    rex = animation.RexReveal(64, height)
    shut, roar = rex.art, rex.mouth(1.0)
    lift = len(roar) - len(shut)

    def cells(art, key, pad=0):
        return [(r - pad, c) for r, row in enumerate(art) for c, k in enumerate(row) if k == key]

    # His eyes (the top whites) go back, toward his tail on the left, and his snout points up.
    def eyes(art, pad=0):
        """The whites up in his head with no mouth beside them (not teeth)."""
        def by_mouth(r, c):
            return any(0 <= r + pad + dr < len(art) and 0 <= c + dc < rex.w and art[r + pad + dr][c + dc] == "M"
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1))
        return [(r, c) for r, c in cells(art, "W", pad) if r < len(shut) // 3 and not by_mouth(r, c)]

    assert max(c for _, c in eyes(roar, lift)) < max(c for _, c in eyes(shut))
    mouth = cells(roar, "M")
    top_at = lambda c: min(r for r, mc in mouth if mc == c)
    cols = sorted({c for _, c in mouth})
    front = min(r for r, c in mouth if c >= (cols[0] + cols[-1]) / 2)
    assert front < top_at(cols[0]), "the upper jaw slopes up toward the front"
    # His feet and tail stay where they were.
    assert roar[-1] == shut[-1] and [row[:5] for row in roar[lift:]] == [row[:5] for row in shut]


def test_his_open_mouth_is_a_dark_gap_between_his_green_and_his_teeth():
    colors = animation.RexReveal.colors
    assert sum(colors["M"]) < sum(colors["g"]) / 3, "darker than his outline: nearly off"
    assert sum(colors["W"]) - sum(colors["M"]) > 600


@pytest.mark.parametrize("height", [32, 64])
def test_the_roar_shakes_the_whole_board_and_the_walk_does_not(height):
    rex = animation.RexReveal(64, height)
    shakes = {rex.shake(t) for t in _frames(rex) if rex.roar_at <= t < rex.shut_at}
    assert len(shakes) > 2 and (0, 0) not in shakes
    assert all(rex.shake(t) == (0, 0) for t in _frames(rex) if not rex.roar_at <= t < rex.shut_at)


@pytest.mark.parametrize("height", [32, 64])
def test_a_shaken_ride_never_shows_the_steady_one_underneath(height):
    rex = animation.RexReveal(64, height)
    under, shaken = (1, 2, 3), (9, 9, 9)
    # The captured ride is lit only in its middle, so a knocked frame has black edges to paint.
    rex.new_px = {(x, y): shaken for x in range(8, 56) for y in range(4, height - 4)}
    canvas = FakeCanvas(64, height)
    fill(under)(canvas, 0)
    rex.overlay(canvas, rex.roar_at + 0.05)
    assert under not in canvas.px.values()


@pytest.mark.parametrize("height", [32, 64])
def test_rex_uncovers_the_ride_behind_him_and_stays_on_the_board(height):
    rex = animation.RexReveal(64, height)
    ride = (0, 140, 0)
    canvas = FakeCanvas(64, height)
    fill(ride)(canvas, 0)
    rex.overlay(canvas, rex.stop_at / 2)
    assert canvas.px[(0, 0)] == ride and canvas.px[(63, 0)] == (0, 0, 0)
    for t in _frames(rex):
        c = FakeCanvas(64, height)
        rex.overlay(c, t)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
    assert rex.overlay(FakeCanvas(64, height), rex.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_his_feet_step_as_he_walks(height):
    rex = animation.RexReveal(64, height)
    rex.x_at = lambda t: rex.stop_x  # held on the board, so only his feet change

    def shape(t):
        c = FakeCanvas(64, height)
        rex.overlay(c, t)
        feet = height - 3  # the bottom rows: his jaw swings while he stands, his feet don't
        return frozenset((xy, rgb) for xy, rgb in c.px.items() if rgb != (0, 0, 0) and xy[1] >= feet)

    walking = {shape(i * rex.POSE_F / animation.FPS) for i in range(4)}
    assert len(walking) == 4, "four poses of the walk cycle"
    standing = {shape(rex.stop_at + i * rex.POSE_F / animation.FPS) for i in range(2)}
    assert len(standing) == 1, "still feet while he stops"
