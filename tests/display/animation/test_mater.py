"""Mater."""
import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill


def test_mater_is_registered_with_well_formed_art():
    cls = animation.TRANSITIONS["mater"]
    assert cls is animation.MaterReveal
    assert len({len(row) for row in cls.ART}) == 1
    assert set("".join(cls.ART)) - {"."} <= set(cls.colors)


@pytest.mark.parametrize("height", [32, 64])
def test_mater_drives_across_backwards_right_to_left(height):
    truck = animation.MaterReveal(64, height)
    xs = [truck.x_at(i / 10) for i in range(int(truck.duration * 10) + 1)]
    assert xs == sorted(xs, reverse=True), "travelling left"
    assert xs[0] > 63 and xs[-1] + truck.w < 0, "in from past the right edge, out past the left"
    # Facing right while he goes left: his face (the grille) is on the right of his art.
    grille = [c for row in truck.ART for c, k in enumerate(row) if k == "R"]
    assert sum(grille) / len(grille) > truck.w / 2


@pytest.mark.parametrize("height", [32, 64])
def test_mater_uncovers_the_ride_on_the_side_he_has_passed(height):
    truck = animation.MaterReveal(64, height)
    ride = (0, 140, 0)
    canvas = FakeCanvas(64, height)
    fill(ride)(canvas, 0)
    truck.overlay(canvas, truck.duration / 2)
    assert canvas.px[(63, 0)] == ride and canvas.px[(0, 0)] == (0, 0, 0)
    for f in range(int(truck.duration * animation.FPS)):
        c = FakeCanvas(64, height)
        truck.overlay(c, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in c.px)
    assert truck.overlay(FakeCanvas(64, height), truck.duration) is False
