"""The Aliens and the claw."""
import random

import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill

YELLOW = animation.AliensReveal.TEXT_RGB


def _frames(aliens):
    return [f / animation.FPS for f in range(int(aliens.duration * animation.FPS))]


def _draw(aliens, t, under=None):
    canvas = FakeCanvas(aliens.width, aliens.height)
    if under:
        fill(under)(canvas, 0)
    aliens.overlay(canvas, t)
    return canvas.px


def test_aliens_are_registered_with_well_formed_art():
    cls = animation.TRANSITIONS["aliens"]
    assert cls is animation.AliensReveal
    for art, colors in ((cls.ART, cls.colors), (cls.CLAW_OPEN_ART, cls.CLAW_COLORS), (cls.CLAW_SHUT_ART, cls.CLAW_COLORS)):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(colors)


def test_his_three_eyes_look_up_at_the_claw():
    cls = animation.AliensReveal
    up = animation.characters.aliens._looking_up(cls.ART)
    pupils = lambda art: [(r, c) for r, row in enumerate(art) for c, k in enumerate(row) if k == "K"]
    assert len(pupils(cls.ART)) == 3 and len(pupils(up)) == 3
    assert all(r == pupils(cls.ART)[0][0] - 1 for r, _ in pupils(up)), "each pupil a row higher"


@pytest.mark.parametrize("height", [32, 64])
def test_a_different_alien_is_chosen_from_one_time_to_the_next(height):
    picks = {animation.AliensReveal(64, height, random.Random(seed)).chosen for seed in range(40)}
    assert len(picks) >= 4, "random, not always the same one"
    aliens = animation.AliensReveal(64, height)
    for x, y in picks:
        assert (x, y) in aliens.spots and 0 <= x <= 64 - aliens.w, "wholly on the board"
        assert y + aliens.CLAW_GRIP - len(aliens.CLAW_OPEN_ART) + 1 >= 0, "the whole claw in sight when it grabs"
    if height == 32:
        assert {y for _, y in picks} == {14}, "on 64x32, only the front row: the back row is too high for the claw"


@pytest.mark.parametrize("height", [32, 64])
def test_the_claw_comes_down_shuts_on_him_and_lifts_him_off_the_top(height):
    aliens = animation.AliensReveal(64, height, random.Random(1))
    x, y = aliens.chosen
    assert aliens.claw_tip(aliens.claw_at - .01) is None, "no claw while they shuffle in"
    tips = [aliens.claw_tip(t) for t in _frames(aliens) if aliens.claw_at <= t < aliens.grab_at]
    assert tips == sorted(tips) and tips[-1] <= y + aliens.CLAW_GRIP, "down to his head"
    assert aliens.claw_tip(aliens.lift_at - .01) == y + aliens.CLAW_GRIP, "held there while it shuts"
    assert aliens.chosen_y(aliens.lift_at - .01) == y, "he waits on the ground"
    lifted = [aliens.chosen_y(t) for t in _frames(aliens) if aliens.lift_at <= t < aliens.text_at]
    assert lifted == sorted(lifted, reverse=True) and lifted[-1] + aliens.h <= 2, "up and off the top"
    assert aliens.chosen_y(aliens.text_at) is None and aliens.claw_tip(aliens.text_at) is None


@pytest.mark.parametrize("height", [32, 64])
def test_youve_been_chosen_shows_once_he_is_gone_and_fits_the_board(height):
    aliens = animation.AliensReveal(64, height, random.Random(2))
    for t in _frames(aliens):
        shown = YELLOW in _draw(aliens, t).values()
        assert shown == (aliens.text_at <= t < aliens.exit_at), t
    (_, (w1, h1)), (_, (w2, h2)) = aliens.lines
    assert w1 <= 62 and w2 <= 62 and h1 + h2 + 4 <= height, "both lines, with their black edge, on the board"


@pytest.mark.parametrize("height", [32, 64])
def test_the_ride_shows_only_as_the_crowd_leaves_and_they_stay_on_the_board(height):
    aliens = animation.AliensReveal(64, height, random.Random(3))
    ride = (1, 2, 3)
    for t in _frames(aliens):
        px = _draw(aliens, t, ride)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in px)
        if t < aliens.exit_at:
            assert ride not in px.values(), "a dark board until they leave"
    leaving = _draw(aliens, aliens.exit_at + .7 * aliens.EXIT_S, ride)
    assert leaving[(32, height // 2)] == ride, "uncovered down the middle first"
    assert aliens.overlay(FakeCanvas(64, height), aliens.duration) is False


@pytest.mark.parametrize("height", [32, 64])
def test_the_crowd_shuffles_in_from_both_sides_and_out_again(height):
    aliens = animation.AliensReveal(64, height, random.Random(4))
    shifts = [aliens.shift(t) for t in _frames(aliens)]
    assert shifts[0] >= 64 // 2 and shifts[-1] > 64 // 2, "off the board at each end"
    assert all(s == 0 for t, s in zip(_frames(aliens), shifts) if aliens.ENTER_S <= t < aliens.exit_at), "standing still meanwhile"


def test_the_colors_read_on_the_board():
    colors = animation.AliensReveal.colors

    def distance(a, b):
        return sum(abs(x - y) for x, y in zip(colors[a], colors[b]))

    assert distance("K", "W") > 600 and distance("W", "G") > 150, "pupils in white eyes on a green face"
    assert distance("m", "G") > 150 and distance("P", "B") > 100, "his smile, and the collar on the suit"


def test_buzz_and_woody_art_is_well_formed():
    cls = animation.AliensToysReveal
    assert animation.TRANSITIONS["aliens_toys"] is cls
    for art in (cls.BUZZ_ART, cls.WOODY_ART, cls.WOODY_HANGING_ART):
        assert len({len(row) for row in art}) == 1 and len(art[0]) == len(cls.ART[0])
        assert set("".join(art)) - {"."} <= set(cls.colors)
    assert cls.WOODY_HANGING_ART[cls.HAND[0]][cls.HAND[1]] == "O", "his raised hand"
    assert cls.BUZZ_ART[-1][cls.BOOT] != ".", "Buzz's boot, where Woody grabs"


@pytest.mark.parametrize("height", [32, 64])
def test_the_claw_chooses_buzz_with_woody_beside_him_at_random(height):
    picks = {(a.chosen, a.woody) for a in (animation.AliensToysReveal(64, height, random.Random(s)) for s in range(40))}
    assert len(picks) >= 3, "a different place in the crowd each time"
    for (bx, by), (wx, wy) in picks:
        assert wy == by and abs(wx - bx) == animation.AliensToysReveal.PITCH, "side by side in one row"
        assert 0 <= wx <= 64 - 14, "Woody wholly on the board"


@pytest.mark.parametrize("height", [32, 64])
def test_woody_jumps_for_buzzs_boot_and_they_go_up_together(height):
    toys = animation.AliensToysReveal(64, height, random.Random(5))
    assert toys.lift_at < toys.jump_at < toys.text_at, "he waits for the boot to come within reach"
    assert toys.figure(toys.woody, toys.jump_at - .01, True) == toys.WOODY_ART, "standing until he jumps"
    assert toys.figure(toys.woody, toys.jump_at, True) is None
    hung = toys.jump_at + toys.LEAP_S + .05
    assert toys.woody_at(hung) == toys._hang(hung), "hanging from the boot"
    wy = [toys.woody_at(t)[1] for t in _frames(toys) if toys.jump_at <= t < toys.text_at]
    assert wy == sorted(wy, reverse=True), "only ever up: he never drops below where he stood"
    assert wy[0] <= toys.reach[1]
    last = toys.text_at - 1 / animation.FPS
    assert toys.woody_at(last)[1] + len(toys.WOODY_HANGING_ART) <= 4, "both hauled off the top"
    assert toys.lines[0] != animation.AliensReveal(64, height).lines[0], "THE CLAW CHOOSES, not YOU'VE BEEN CHOSEN"


@pytest.mark.parametrize("height", [32, 64])
def test_buzz_and_woody_stay_on_the_board_and_the_ride_waits(height):
    toys = animation.AliensToysReveal(64, height, random.Random(6))
    ride = (1, 2, 3)
    for t in _frames(toys):
        px = _draw(toys, t, ride)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in px)
        if t < toys.exit_at:
            assert ride not in px.values(), "a dark board until the aliens leave"
    assert toys.overlay(FakeCanvas(64, height), toys.duration) is False
