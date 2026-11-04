"""The lightsaber clash."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas

OLD, NEW = (90, 0, 90), (0, 140, 0)


def _saber(height):
    saber = animation.SaberClashReveal(64, height, random.Random(1))
    saber.prev_px = {(x, y): OLD for x in range(64) for y in range(height) if x % 2}  # half lit, half black
    return saber


def _frame(saber, t):
    canvas = FakeCanvas(64, saber.height)
    for x in range(64):
        for y in range(saber.height):
            canvas.SetPixel(x, y, *NEW)
    more = saber.overlay(canvas, t)
    return canvas.px, more


def _blade_colors(saber):
    """The clash's two blades (BLADES also has the duels' green)."""
    return {name: set(saber.BLADES[name]) for name in ("red", "blue")}


def test_the_saber_clash_is_registered_and_takes_the_old_screen():
    assert animation.TRANSITIONS["saber_clash"] is animation.SaberClashReveal
    assert animation.SaberClashReveal.wants_prev


@pytest.mark.parametrize("height", [32, 64])
def test_the_blades_swing_in_from_off_the_board(height):
    saber = _saber(height)
    px, _ = _frame(saber, 0)
    blades = set().union(*_blade_colors(saber).values())
    assert not blades & set(px.values()), "both start upright, off the board"
    px, _ = _frame(saber, saber.SWING_S * 0.9)
    red = [x for (x, _), rgb in px.items() if rgb in saber.BLADES["red"]]
    blue = [x for (x, _), rgb in px.items() if rgb in saber.BLADES["blue"]]
    assert red and blue, "both on the board as they swing in"
    assert min(red) < min(blue) and max(blue) > max(red), "red from the left, blue from the right"


@pytest.mark.parametrize("height", [32, 64])
def test_the_blades_lock_in_an_x_at_the_centre_and_spark(height):
    saber = _saber(height)
    for name, (x, y, _) in saber.blades(saber.SWING_S + 0.1).items():
        assert (x, y) == (saber.cx, saber.cy), f"{name} crosses the centre"
    px, _ = _frame(saber, saber.SWING_S + 0.1)
    colors = set(px.values())
    assert colors & set(saber.SPARKS), "sparks at the crossing"
    assert NEW not in colors, "the old screen stays up through the clash, black pixels included"
    for name, shades in _blade_colors(saber).items():
        corners = [(x, y) for (x, y), rgb in px.items() if rgb in shades and (y < 3 or y >= height - 3)]
        assert {x < 32 for x, _ in corners} == {True, False}, f"{name} runs corner to corner"
    shivers = {round(saber.blades(saber.SWING_S + f / animation.FPS)["red"][2], 3) for f in range(6)}
    assert len(shivers) == 2, "the locked blades shiver"


@pytest.mark.parametrize("height", [32, 64])
def test_the_blades_go_upright_then_sweep_apart_to_reveal_the_new_ride(height):
    saber = _saber(height)
    unlocked = saber.SWING_S + saber.CLASH_S + saber.UNLOCK_S
    px, _ = _frame(saber, unlocked - 0.01)
    assert NEW not in set(px.values()), "nothing revealed until they spread"
    px, _ = _frame(saber, unlocked)
    row = {px[(x, height // 2)] for x in range(64)}
    assert row & set(saber.BLADES["red"]) and row & set(saber.BLADES["blue"]), "upright side by side, neither hiding the other"
    assert saber.gap(unlocked - 0.01) is None

    px, _ = _frame(saber, unlocked + saber.SPREAD_S / 4)
    left, right = saber.gap(unlocked + saber.SPREAD_S / 4)
    assert left < 31.5 < right
    assert px[(32, height // 2)] == NEW, "the new ride between the blades"
    assert px[(0, 0)] == (0, 0, 0) and px[(63, 0)] == OLD, "the old one outside them"
    assert px[(int(round(left)), 0)] in saber.BLADES["red"] and px[(int(round(right)), height - 1)] in saber.BLADES["blue"]

    px, more = _frame(saber, saber.duration - 0.01)
    assert set(px.values()) == {NEW}, "both blades off the edges"
    assert more
    _, more = _frame(saber, saber.duration)
    assert not more


def test_with_no_old_screen_it_clashes_over_black():
    saber = animation.SaberClashReveal(64, 32, random.Random(1))
    px, _ = _frame(saber, saber.SWING_S + 0.1)
    assert NEW not in set(px.values())
