"""Lightning McQueen."""
import pytest

import display.animation as animation
from tests.display.animation.support import FakeCanvas, fill


def test_mcqueen_is_registered_with_well_formed_art():
    cls = animation.TRANSITIONS["mcqueen"]
    assert cls is animation.McQueenReveal
    assert len({len(row) for row in cls.ART}) == 1
    assert set("".join(cls.ART)) - {"."} <= set(cls.colors)


@pytest.mark.parametrize("height", [32, 64])
def test_mcqueen_zooms_in_skids_to_a_stop_then_peels_out(height):
    car = animation.McQueenReveal(64, height)
    assert car.x_at(0) <= -car.w + 1, "in from off the left"
    assert car.x_at(car.ZOOM_S) == car.x_at(car.PEEL_S - 0.01) == car.stop_x, "parked mid-board"
    assert car.speed(0.05) > car.speed(car.ZOOM_S - 0.1) > 0, "braking into the skid"
    assert car.speed(car.duration - 0.1) > car.speed(car.PEEL_S + 0.1) > 0, "flooring it on the way out"
    assert car.x_at(car.duration) > 64, "gone off the right"


@pytest.mark.parametrize("height", [32, 64])
def test_mcqueen_uncovers_the_ride_behind_him_with_streaks_while_moving(height):
    car = animation.McQueenReveal(64, height)
    ride = (0, 140, 0)

    def frame(t):
        canvas = FakeCanvas(64, height)
        fill(ride)(canvas, t)
        more = car.overlay(canvas, t)
        return canvas.px, more

    px, _ = frame(car.PEEL_S - 0.3)
    assert px[(0, 0)] == ride and px[(63, 0)] == (0, 0, 0), "ride behind him, dark ahead"
    def behind(px, t):  # his streaks' colours are his own orange and yellow, so look only behind him
        return {rgb for (x, y), rgb in px.items() if x < car.x_at(t)}

    t = car.PEEL_S - 0.3
    assert not set(car.STREAKS) & behind(frame(t)[0], t), "no streaks while he's parked"
    t = car.PEEL_S + 0.4
    assert set(car.STREAKS) & behind(frame(t)[0], t), "streaks as he peels out"
    px, more = frame(car.duration)
    assert not more and set(px.values()) == {ride}


@pytest.mark.parametrize("height", [32, 64])
def test_mcqueen_stays_on_the_board(height):
    car = animation.McQueenReveal(64, height)
    for f in range(int(car.duration * animation.FPS)):
        canvas = FakeCanvas(64, height)
        car.overlay(canvas, f / animation.FPS)
        assert all(0 <= x < 64 and 0 <= y < height for x, y in canvas.px)
