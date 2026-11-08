import importlib.util
import json
import os

import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("build_settings_art", os.path.join(ROOT, "tools", "build_settings_art.py"))
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


@pytest.fixture(scope="module")
def rendered():
    return builder.render()


def test_checked_in_stills_match_the_current_landmarks(rendered):
    with open(os.path.join(builder.STATIC, builder.INDEX), encoding="utf-8") as f:
        index = json.load(f)
    assert index == {key: name for key, (name, _) in rendered.items()}, "run python3 tools/build_settings_art.py"
    for key, (name, image) in rendered.items():
        with Image.open(os.path.join(builder.STATIC, name)) as saved:
            small = saved.convert("RGB").resize((builder.WIDTH, builder.HEIGHT), Image.NEAREST)
            assert list(small.getdata()) == list(image.getdata()), \
                f"the {key} landmark changed: run python3 tools/build_settings_art.py"


def test_every_park_landmark_has_a_still(rendered):
    from display.landmarks.screen import LANDMARKS
    assert set(rendered) == set(LANDMARKS)
    for name, image in rendered.values():
        assert image.size == (builder.WIDTH, builder.HEIGHT) and len(set(image.getdata())) > 8, name


def test_spaceship_earth_is_taken_lit_and_without_tinker_bell(monkeypatch):
    from display.landmarks import SpaceshipEarthLandmark
    landmarks, sky = builder.load_landmarks()

    def never(*args, **kwargs):
        raise AssertionError("the still draws the landmark alone")
    monkeypatch.setattr(SpaceshipEarthLandmark, "_draw_tink", never)
    image = builder.still(SpaceshipEarthLandmark, sky)
    assert len(set(image.getdata())) > 20, "its facets lit"


def test_build_writes_the_pngs_scaled_up_and_the_index(tmp_path):
    index = builder.build(str(tmp_path))
    assert json.loads((tmp_path / builder.INDEX).read_text()) == index
    for name in index.values():
        with Image.open(tmp_path / name) as im:
            assert im.size == (builder.WIDTH * builder.SCALE, builder.HEIGHT * builder.SCALE)
