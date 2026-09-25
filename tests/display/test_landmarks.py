# tests/display/test_landmarks.py
import random

import pytest

import display.landmarks as landmarks

ALL = [landmarks.CastleLandmark, landmarks.SpaceshipEarthLandmark,
       landmarks.TowerOfTerrorLandmark, landmarks.TreeOfLifeLandmark]


@pytest.mark.parametrize("name, cls", [
    ("Magic Kingdom", landmarks.CastleLandmark),
    ("EPCOT", landmarks.SpaceshipEarthLandmark),
    ("Epcot", landmarks.SpaceshipEarthLandmark),
    ("Hollywood Studios", landmarks.TowerOfTerrorLandmark),
    ("Disney's Hollywood Studios", landmarks.TowerOfTerrorLandmark),
    ("Animal Kingdom", landmarks.TreeOfLifeLandmark),
    ("Cedar Point", None),
    ("", None),
    (None, None),
])
def test_landmark_for_matches_park_names_loosely(name, cls):
    assert landmarks.landmark_for(name) is cls


@pytest.mark.parametrize("cls", ALL)
@pytest.mark.parametrize("height", [32, 64])
def test_every_frame_stays_on_the_board_with_valid_colors(cls, height):
    scene = cls(64, height, random.Random(1))
    for f in range(int(landmarks.LANDMARK_S * 30)):
        pixels = scene.frame(f / 30)
        assert pixels
        for (x, y), rgb in pixels.items():
            assert 0 <= x < 64 and 0 <= y < height
            assert len(rgb) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)


@pytest.mark.parametrize("cls", ALL)
def test_scenes_actually_move(cls):
    scene = cls(64, 64, random.Random(2))
    frames = [scene.frame(f / 30) for f in range(int(landmarks.LANDMARK_S * 30))]
    assert any(a != b for a, b in zip(frames, frames[1:]))


def test_tower_lightning_strikes_once_per_scene():
    tower = landmarks.TowerOfTerrorLandmark(64, 64, random.Random(3))
    bolt_px = set(tower.bolt)
    struck = [f for f in range(int(landmarks.LANDMARK_S * 30))
              if any(tower.frame(f / 30).get(p) == (230, 230, 255) for p in bolt_px)]
    assert struck, "the bolt appears"
    assert struck == list(range(struck[0], struck[-1] + 1)), "one continuous strike"
    assert len(struck) < 10, "a quick flash"


def test_landmark_screen_draws_every_pixel_and_keeps_animating():
    class Canvas:
        def __init__(self):
            self.px = {}

        def SetPixel(self, x, y, r, g, b):
            self.px[(x, y)] = (r, g, b)

    scene = landmarks.TreeOfLifeLandmark(64, 32, random.Random(4))
    canvas = Canvas()
    assert landmarks.landmark_screen(scene)(canvas, 1.0) is True
    assert canvas.px == scene.frame(1.0)
