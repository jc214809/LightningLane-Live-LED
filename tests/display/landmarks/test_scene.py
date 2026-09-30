"""Every landmark: stays on the board with valid colours, and moves."""

import random

import pytest

import display.landmarks as landmarks


ALL = [landmarks.CastleLandmark, landmarks.SpaceshipEarthLandmark,
       landmarks.TowerOfTerrorLandmark, landmarks.TreeOfLifeLandmark, landmarks.ScaryJackOLanternLandmark,
       type("WinkingPumpkin", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": "wink"}),
       type("BouncingPumpkin", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": "bounce"})]


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
