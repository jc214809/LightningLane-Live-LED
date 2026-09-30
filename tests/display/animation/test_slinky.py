"""Slinky (both of him)."""

import random

import display.animation as animation

from tests.display.animation.support import FakeCanvas, FakeMatrix, fill


def test_slinky_plays_as_a_screen_transition():
    matrix = FakeMatrix()
    animation.show_screen(matrix, fill((10, 200, 90)), animation.SlinkyReveal.duration + 0.5,
                          transition="slinky", rng=random.Random(7))
    assert matrix.frames[0].get((63, 5)) in (None, (0, 0, 0)), "far side still dark at the start"
    assert matrix.frames[-1][(63, 5)] == (10, 200, 90), "screen fully revealed by the end"


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


def _wrap(height=32, seed=0):
    return animation.SlinkyWrapReveal(64, height, random.Random(seed))


def test_slinky_wrap_pause_is_random_and_the_visit_fits_a_ride_screen():
    pauses = set()
    for seed in range(40):
        dog = _wrap(seed=seed)
        assert 1.0 <= dog.pause <= 3.0
        assert animation.COVER_S + dog.duration <= 8 - 1 / animation.FPS, "done before the screen changes"
        pauses.add(round(dog.pause, 2))
    assert len(pauses) > 20


def _at(dog, name, frac):
    """A time `frac` of the way through the named phase."""
    names = ["walk_in", "walk_off", "pause", "peek", "look", "cross", "follow", "exit"]
    i = names.index(name)
    start = dog.beats[i - 1] if i else 0.0
    return start + (dog.beats[i] - start) * frac


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
