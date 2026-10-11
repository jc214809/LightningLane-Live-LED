import json

import pytest

from display.fireworks import score as score_module
from display.fireworks.music_show import CASTLE_LOOKS, SHAPES
from display.fireworks.score import EFFECTS, load_score, parse_score


@pytest.fixture(scope="module")
def hea():
    return load_score("happily-ever-after")


def test_happily_ever_after_has_a_score(hea):
    assert hea.name == "happily-ever-after"
    assert hea.end == 1102


def test_the_scenes_cover_the_show_end_to_end(hea):
    assert hea.cues[0].start == 0
    for before, after in zip(hea.cues, hea.cues[1:]):
        assert before.end == after.start, f"gap or overlap between {before.title} and {after.title}"
    assert hea.cues[-1].end == hea.end


def test_every_cue_uses_known_looks_shapes_and_effects(hea):
    for cue in hea.cues:
        assert cue.castle is None or cue.castle in CASTLE_LOOKS
        assert all(shape in SHAPES for shape, _ in cue.shapes)
        assert cue.effects <= EFFECTS
        assert sum(chance for _, chance in cue.shapes) <= 1
        assert cue.palette and all(max(c) >= 80 for c in cue.palette), "bursts bright enough to see"


@pytest.mark.parametrize("t, title, rate, castle, effects", [
    (0, "Theme instrumental", 1.0, None, {"searchlights", "keyhole_glow"}),
    (140, "Wishing star lands on the castle", 0, "blue", {"wishing_star"}),
    (400, "Silence", 0, None, set()),
    (700, "I See the Light", 0, None, {"lanterns"}),
    (830, "He's a Pirate", 1.6, "fire", set()),
    (865, "Embers", 0, "dark", {"embers"}),
    (950, "Go the Distance", 1.2, "stained_glass", set()),
    (1100, "Final chorus, keyhole opens", 2.5, None, {"rainbow", "final_flash", "keyhole_open"}),
])
def test_cue_at(hea, t, title, rate, castle, effects):
    cue = hea.cue_at(t)
    assert (cue.title, cue.rate, cue.castle, set(cue.effects)) == (title, pytest.approx(rate), castle, effects)


def test_cue_at_past_either_end_holds_the_first_or_last_scene(hea):
    assert hea.cue_at(-5) is hea.cues[0]
    assert hea.cue_at(5000) is hea.cues[-1]


def test_rate_defaults_to_the_sections_intensity(hea):
    # Touch the Sky sets no rate: the journey section's 0.7 against the everyday 0.6.
    assert hea.cue_at(300).rate == pytest.approx(0.7 / 0.6)


def test_dim_palette_colours_are_dropped(tmp_path):
    (tmp_path / "show.json").write_text(json.dumps(_show(palette=["#101820", "#FF0000"])))
    assert load_score("show", shows_dir=str(tmp_path)).cue_at(1).palette == ((255, 0, 0),)


def test_progress_through_a_scene(hea):
    wish = hea.cue_at(140)
    assert wish.progress(wish.start) == 0 and wish.progress(wish.end) == 1
    assert wish.progress((wish.start + wish.end) / 2) == pytest.approx(0.5)


def _show(**scene):
    return {"show_end": 10, "sections": [{"id": "s", "palette": ["#FF0000"], "intensity": 0.6,
                                          "scenes": [{"start": 0, "end": 10, "title": "x", **scene}]}]}


def test_a_missing_score_is_none(tmp_path):
    assert load_score("no-such-show", shows_dir=str(tmp_path)) is None


@pytest.mark.parametrize("data", [
    "{not json",
    json.dumps({"sections": []}),
    json.dumps(_show(castle="plaid")),
    json.dumps(_show(shapes={"dragon": 0.5})),
    json.dumps(_show(effects=["confetti"])),
    json.dumps(_show(palette=["#000000"])),  # nothing bright enough
    json.dumps(_show(palette=["red"])),
    json.dumps({"show_end": 10, "sections": [{"id": "s"}]}),
])
def test_a_broken_score_is_logged_and_none(tmp_path, data):
    (tmp_path / "show.json").write_text(data)
    assert load_score("show", shows_dir=str(tmp_path)) is None


def test_a_good_score_from_a_folder(tmp_path):
    (tmp_path / "show.json").write_text(json.dumps(_show(castle="gold", shapes={"heart": 0.5})))
    score = load_score("show", shows_dir=str(tmp_path))
    assert score.cue_at(5).castle == "gold" and score.cue_at(5).shapes == (("heart", 0.5),)


def test_shows_dir_is_next_to_the_module_not_the_cwd():
    assert score_module.SHOWS_DIR.endswith("display/fireworks/shows")
