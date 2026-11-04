"""The Tower of Terror."""

import random

import pytest

import display.landmarks as landmarks


def test_tower_screen_is_longer_than_the_other_landmarks_and_longest_on_64x32():
    tall = landmarks.TowerOfTerrorLandmark(64, 64, random.Random(3))
    short = landmarks.TowerOfTerrorLandmark(64, 32, random.Random(3))
    assert (tall.SCREEN_S, short.SCREEN_S) == (4.5, 5.5)
    for cls in (landmarks.CastleLandmark, landmarks.TreeOfLifeLandmark):
        assert cls.SCREEN_S == landmarks.LANDMARK_S < tall.SCREEN_S
    # Spaceship Earth's Tink story needs as long as the tower: longer than the plain landmarks.
    assert landmarks.LANDMARK_S < landmarks.SpaceshipEarthLandmark.SCREEN_S <= tall.SCREEN_S


def _tower_scene_s(tower):
    """Scene time the tower gets: its screen minus the sweep and the wipe in front of it."""
    import display.animation as animation
    return tower.SCREEN_S - animation.COVER_S - animation.TRANSITIONS["wipe"].duration


@pytest.mark.parametrize("height", [32, 64])
def test_tower_story_plays_out_inside_its_screen(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    assert tower.STRIKE_AT < tower.DOORS_AT < tower.DROP_AT < tower.LAND_AT
    assert tower.LAND_AT <= _tower_scene_s(tower) - 0.8, "the car lands with time to take it in"
    beats = (0.0, tower.STRIKE_AT, tower.DOORS_AT, tower.DROP_AT, tower.LAND_AT)
    assert min(b - a for a, b in zip(beats[1:], beats[2:])) >= 0.5, "each beat gets room"
    if tower.pans:
        assert tower.PAN_S + 0.3 <= tower.STRIKE_AT, "the tilt settles before anything happens"


@pytest.mark.parametrize("height", [32, 64])
def test_tower_lightning_strikes_once_out_of_the_cloud(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    struck = [f for f in range(int(_tower_scene_s(tower) * 30))
              if tower.BOLT_RGB in tower.frame(f / 30).values()]
    assert struck, "the bolt appears"
    assert struck == list(range(struck[0], struck[-1] + 1)), "one continuous strike"
    assert len(struck) < 10, "a quick flash"
    cloud_bottom = max(y for _, y in tower.clouds[0])
    assert min(y for _, y in tower.bolt) == cloud_bottom + 1, "it starts from the underside of the cloud"


@pytest.mark.parametrize("height", [32, 64])
def test_tower_doors_open_then_the_car_drops_in_view(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    x0, _, x1, y1 = tower.doors
    before = tower.frame(tower.DOORS_AT - 0.05)
    # On 64x32 the doors finish opening just as the car drops, so look a moment before.
    opened = tower.frame(min(tower.DOORS_AT + tower.DOORS_OPEN_S, tower.DROP_AT) - 0.02)
    assert before[((x0 + x1) // 2, y1)] != tower.COLORS["win_lit"]
    assert opened[((x0 + x1) // 2, y1)] == tower.COLORS["win_lit"], "the doors open onto the lit car"
    assert tower.CAR_RGB in tower.frame(tower.DROP_AT + 0.05).values(), "the falling car is on screen"
    assert tower.CAR_RGB not in tower.frame(tower.LAND_AT + 0.05).values(), "and gone once it lands"


def test_tower_tilts_up_from_the_trees_to_the_dome_on_64x32():
    tower = landmarks.TowerOfTerrorLandmark(64, 32, random.Random(3))
    trees = {tower.COLORS["tree"], tower.COLORS["tree_lit"]}
    start, settled = tower.frame(0), tower.frame(tower.PAN_S)
    assert sum(rgb in trees for rgb in start.values()) > 50, "starts down among the trees"
    assert not any(rgb in trees for rgb in settled.values())
    assert settled[(31, 0)] == tower.COLORS["spire"], "and stops with the dome's spire at the top"
    tall = landmarks.TowerOfTerrorLandmark(64, 64, random.Random(3))
    assert not tall.pans and tall.frame(0)[(31, 0)] == tall.COLORS["spire"], "64x64 shows it all at once"
