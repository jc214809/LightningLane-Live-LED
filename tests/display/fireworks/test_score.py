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
    assert hea.end == 1104, "the music has faded to silence by 1104"


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


# Times from watching the real show (docs/shows/happily-ever-after/README.md).
@pytest.mark.parametrize("t, title, rate, castle, effects", [
    (0, "Theme fanfare", 0, "amber", {"searchlights", "keyhole_glow"}),
    (140, "Wishing star lands on the castle", 0, "blue", {"wishing_star"}),
    (270, "Out There", 0.9, "stone", {"doves", "bells", "comet_fan", "willow"}),
    (400, "Aladdin: a best friend by your side", 0, "blue", {"smoke"}),
    (700, "I See the Light (lanterns)", 0.15, "blue", {"lanterns", "willow"}),
    (780, "He's a Pirate", 1.4, "fire", {"flame_jets"}),
    (865, "Embers", 0, "dark", {"embers"}),
    (950, "Go the Distance", 1.6, "stained_glass", {"willow", "comet_fan"}),
    (1095, "Final chorus, keyhole opens", 2.6, "gold", {"rainbow", "keyhole_open", "comet_fan"}),
    (1100, "The last hit", 0.6, "gold", {"final_flash", "keyhole_open", "willow"}),
])
def test_cue_at(hea, t, title, rate, castle, effects):
    cue = hea.cue_at(t)
    assert (cue.title, cue.rate, cue.castle, set(cue.effects)) == (title, pytest.approx(rate), castle, effects)


def test_the_sky_stays_dark_until_the_theme_chorus(hea):
    """The real show fires nothing for its first 98 seconds: the castle and searchlights carry it."""
    assert all(c.rate == 0 for c in hea.cues if c.start < 98)
    assert hea.cue_at(98).rate > 1


def test_the_flash_lands_on_the_last_hit(hea):
    """The music's last big hit is at 1099.6-1100 in the audio; the flash fires as its scene starts."""
    flash = next(c for c in hea.cues if "final_flash" in c.effects)
    assert 1099 <= flash.start <= 1100.5


def test_cue_at_past_either_end_holds_the_first_or_last_scene(hea):
    assert hea.cue_at(-5) is hea.cues[0]
    assert hea.cue_at(5000) is hea.cues[-1]


def test_rate_defaults_to_the_sections_intensity(hea):
    # Hakuna Matata sets no rate: the friendship section's 0.8 against the everyday 0.6.
    assert hea.cue_at(450).rate == pytest.approx(0.8 / 0.6)


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


# ---- versions: an overlay file on V1's scenes ----

def _write(tmp_path, show, overlay=None):
    (tmp_path / "show.json").write_text(json.dumps(show))
    if overlay is not None:
        (tmp_path / "show.v2.json").write_text(json.dumps(overlay))


def _two_scenes(**second):
    return {"show_end": 20, "sections": [{"id": "s", "palette": ["#FF0000"], "intensity": 0.6, "scenes": [
        {"start": 0, "end": 10, "title": "one"}, {"start": 10, "end": 20, "title": "two", **second}]}]}


def test_v1_scenes_keep_the_castle_and_have_no_actors(hea):
    assert all(c.stage == "castle" and c.actors == () for c in hea.cues)


def test_an_overlay_adds_a_stage_actors_and_rate_to_its_scene_only(tmp_path, monkeypatch):
    monkeypatch.setitem(score_module.ACTORS, "someone", object)
    _write(tmp_path, _two_scenes(), {"overlays": {"two": {"stage": "ghost", "actors": ["someone"], "rate": 0.4}}})
    v1 = load_score("show", shows_dir=str(tmp_path))
    v2 = load_score("show", shows_dir=str(tmp_path), version="v2")
    assert v2.cues[0] == v1.cues[0]
    assert (v2.cues[1].stage, v2.cues[1].actors, v2.cues[1].rate) == ("ghost", ("someone",), 0.4)
    assert v2.cues[1]._replace(stage="castle", actors=(), rate=v1.cues[1].rate) == v1.cues[1]


def test_without_an_overlay_file_v2_plays_v1(tmp_path):
    _write(tmp_path, _two_scenes())
    assert load_score("show", shows_dir=str(tmp_path), version="v2") == load_score("show", shows_dir=str(tmp_path))


@pytest.mark.parametrize("overlay", [
    {"overlays": {"three": {"stage": "off"}}},  # a renamed or missing scene can't drop silently
    {"overlays": {"two": {"stage": "aside"}}},
    {"overlays": {"two": {"actors": ["nobody"]}}},
    {"overlays": {"two": {"actors": "genie"}}},
    {"overlays": {"two": {"costume": "red"}}},
    {"scenes": {}},
    "{not json",
])
def test_a_broken_overlay_is_logged_and_v1_plays(tmp_path, overlay, monkeypatch):
    warnings = []
    monkeypatch.setattr(score_module.debug, "warning", warnings.append)
    _write(tmp_path, _two_scenes())
    (tmp_path / "show.v2.json").write_text(overlay if isinstance(overlay, str) else json.dumps(overlay))
    assert load_score("show", shows_dir=str(tmp_path), version="v2") == load_score("show", shows_dir=str(tmp_path))
    assert len(warnings) == 1 and "playing v1" in warnings[0]


@pytest.mark.parametrize("effect", sorted(score_module.CASTLE_EFFECTS))
def test_the_castle_cant_be_off_in_a_scene_whose_effects_draw_on_it(tmp_path, effect):
    _write(tmp_path, _two_scenes(effects=[effect]), {"overlays": {"two": {"stage": "off"}}})
    assert load_score("show", shows_dir=str(tmp_path), version="v2").cues[1].stage == "castle", "fell back to v1"
    _write(tmp_path, _two_scenes(effects=[effect]), {"overlays": {"two": {"stage": "ghost"}}})
    assert load_score("show", shows_dir=str(tmp_path), version="v2").cues[1].stage == "ghost"


def test_happily_ever_afters_v2_overlay_parses_onto_v1():
    # Parsed directly, so a mistake fails here instead of quietly playing V1.
    with open(f"{score_module.SHOWS_DIR}/happily-ever-after.json") as f:
        data = json.load(f)
    with open(f"{score_module.SHOWS_DIR}/happily-ever-after.v2.json") as f:
        overlay = json.load(f)
    v2 = parse_score("happily-ever-after", data, overlay)
    assert v2.end == parse_score("happily-ever-after", data).end
    assert {c.title for c in v2.cues if c.stage != "castle" or c.actors} <= set(overlay["overlays"])
    assert v2.cue_at(540).stage == "ghost", "Friend Like Me (Genie)"
