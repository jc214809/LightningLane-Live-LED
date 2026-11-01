import copy
import json
import os

import pytest

from settings_page.form import (apply_form, board_types, chosen_device, masked, show_names, trip_rows,
                                volume_from_form)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG = {
    "parks": ["Magic Kingdom", "EPCOT"],
    "websocket": {"enabled": True, "api_key": "tp-secret-1234", "protocol": "legacy"},
    "trip_countdown": {"enabled": True, "trip_dates": [
        {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"}, "2027-06-01"]},
    "sound": {"enabled": False, "device": None, "quiet_hours": {"start": "22:00", "end": "08:00"}},
    "weather": {"apikey": "owm-secret-9876"},
    "matrix": {"led_rows": 64, "led_brightness": None},
    "shows": [{"name": "Happily Ever After", "enabled": True, "version": "v2"}],
    "force_surprise": "",
    "debug": False,
    "show_version": "v1",  # an old key the page doesn't know: kept
}


def form_for(config, **changes):
    """The form as the page would post it for config, untouched, with changes on top."""
    ws, sound = config["websocket"], config["sound"]
    form = {
        "ws_protocol": [ws["protocol"]], "themeparks_key": [""], "weather_key": [""],
        "park": list(config["parks"]), "park_add": [""],
        "sound_device": [sound["device"] or ""], "sound_device_custom": [""],
        "quiet_start": [sound["quiet_hours"]["start"]], "quiet_end": [sound["quiet_hours"]["end"]],
        "matrix_led_brightness": [""], "force_surprise": [""],
    }
    if ws["enabled"]:
        form["ws_enabled"] = ["on"]
    if config["trip_countdown"]["enabled"]:
        form["trips_enabled"] = ["on"]
    for i, (start, end, name) in enumerate(trip_rows(config) + [("", "", "")]):
        form.update({f"trip_start_{i}": [start], f"trip_end_{i}": [end], f"trip_name_{i}": [name]})
    entries = {e["name"]: e for e in config["shows"]}
    for i, name in enumerate(show_names(config)):
        entry = entries.get(name, {})
        form.update({f"show_name_{i}": [name], f"show_version_{i}": [entry.get("version", "default")]})
        if entry.get("enabled", True):
            form[f"show_enabled_{i}"] = ["on"]
    form.update({k: [v] if isinstance(v, str) else v for k, v in changes.items()})
    return form


def test_an_untouched_form_changes_nothing_that_was_set():
    new, problems = apply_form(CONFIG, form_for(CONFIG))
    assert problems == []
    for key in ("parks", "websocket", "trip_countdown", "sound", "weather", "show_version", "debug"):
        assert new[key] == CONFIG[key], key
    assert new["matrix"]["led_rows"] == 64, "Advanced fields not posted leave their settings alone"
    assert new["shows"][0] == {"name": "Happily Ever After", "enabled": True, "version": "v2"}


def test_the_config_passed_in_is_not_changed():
    before = copy.deepcopy(CONFIG)
    apply_form(CONFIG, form_for(CONFIG, park=["EPCOT"], themeparks_key="new-key"))
    assert CONFIG == before


def test_saved_keys_show_only_their_last_letters_and_a_blank_keeps_them():
    assert masked("tp-secret-1234") == "••••1234"
    assert masked("<THEMEPARKS_API_KEY_HERE>") == "" and masked(None) == "" and masked("  ") == ""
    new, _ = apply_form(CONFIG, form_for(CONFIG, themeparks_key="  tp-new-5555 ", weather_key="owm-new"))
    assert new["websocket"]["api_key"] == "tp-new-5555"
    assert new["weather"]["apikey"] == "owm-new"


def test_live_updates_on_with_no_key_is_refused():
    config = copy.deepcopy(CONFIG)
    config["websocket"]["api_key"] = "<THEMEPARKS_API_KEY_HERE>"
    _, problems = apply_form(config, form_for(config))
    assert problems == ["Live updates need a ThemeParks.wiki API key (or turn them off)."]
    form = form_for(config)
    del form["ws_enabled"]
    new, problems = apply_form(config, form)
    assert problems == [] and new["websocket"]["enabled"] is False


def test_an_unknown_protocol_is_refused():
    _, problems = apply_form(CONFIG, form_for(CONFIG, ws_protocol="carrier-pigeon"))
    assert "Live update protocol" in problems[0]


PARK_NAMES = [("Animal Kingdom", "Walt Disney World® Resort"), ("Cedar Point", "Cedar Point"),
              ("EPCOT", "Walt Disney World® Resort"), ("Kings Island", "Kings Island"),
              ("Magic Kingdom", "Walt Disney World® Resort")]


def test_parks_keep_the_chips_order_then_the_added_ones_and_one_is_needed():
    new, problems = apply_form(CONFIG, form_for(CONFIG, park=["Animal Kingdom", "Magic Kingdom"],
                                                park_add="cedar point,  Kings   Island ,,MAGIC kingdom"), PARK_NAMES)
    assert problems == []
    assert new["parks"] == ["Animal Kingdom", "Magic Kingdom", "Cedar Point", "Kings Island"], \
        "the chips' order, then the added, named as listed, no repeats"
    _, problems = apply_form(CONFIG, form_for(CONFIG, park=[]), PARK_NAMES)
    assert problems == ["Pick at least one park."]


def test_a_ticked_park_x_removes_it():
    new, _ = apply_form(CONFIG, form_for(CONFIG, park_remove="Magic Kingdom"), PARK_NAMES)
    assert new["parks"] == ["EPCOT"]


def test_a_name_thats_not_on_themeparks_wiki_is_refused_wherever_it_came_from():
    _, problems = apply_form(CONFIG, form_for(CONFIG, park_add="Epcot Center"), PARK_NAMES)
    assert problems == ["'Epcot Center' isn't a ThemeParks.wiki park: pick one from the list."]
    new, problems = apply_form({**CONFIG, "parks": ["EPCOT", "Old Park"]},
                               form_for({**CONFIG, "parks": ["EPCOT", "Old Park"]}), PARK_NAMES)
    assert problems == ["'Old Park' isn't a ThemeParks.wiki park: pick one from the list."]
    assert new["parks"] == ["EPCOT", "Old Park"], "kept on the page to be removed"


def test_with_no_park_list_yet_names_are_taken_as_typed():
    new, problems = apply_form(CONFIG, form_for(CONFIG, park_add="Somewhere New"))
    assert problems == [] and new["parks"] == ["Magic Kingdom", "EPCOT", "Somewhere New"]


def test_trips_are_saved_as_the_app_reads_them_and_blank_or_removed_rows_dropped():
    form = form_for(CONFIG, trip_start_2="2027-12-20", trip_name_2="Christmas", trip_remove_1="on")
    new, problems = apply_form(CONFIG, form)
    assert problems == []
    assert new["trip_countdown"]["trip_dates"] == [
        {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"},
        {"start": "2027-12-20", "name": "Christmas"}]
    from utils.trips import parse_trips
    assert len(parse_trips(new)) == 2


def test_the_old_single_trip_date_is_moved_into_the_list():
    config = copy.deepcopy(CONFIG)
    config["trip_countdown"] = {"enabled": True, "trip_date": "2027-01-02T00:00:00"}
    assert trip_rows(config) == []
    new, _ = apply_form(config, form_for(config, trip_start_0="2027-01-02"))
    assert new["trip_countdown"] == {"enabled": True, "trip_dates": ["2027-01-02"]}


@pytest.mark.parametrize("fields, problem", [
    ({"trip_start_0": "soon"}, "the start date should be a date"),
    ({"trip_start_0": "", "trip_name_0": "Someday"}, "the start date should be a date"),
    ({"trip_end_0": "2027-03-01"}, "it ends before it starts"),
])
def test_a_bad_trip_is_refused(fields, problem):
    _, problems = apply_form(CONFIG, form_for(CONFIG, **fields))
    assert len(problems) == 1 and problem in problems[0]


def test_sound_device_from_the_list_or_typed_and_blank_quiet_hours_mean_none():
    new, _ = apply_form(CONFIG, form_for(CONFIG, sound_enabled="on", sound_device="plughw:CARD=Device,DEV=0",
                                         quiet_start="", quiet_end=""))
    assert new["sound"] == {"enabled": True, "device": "plughw:CARD=Device,DEV=0"}
    new, _ = apply_form(CONFIG, form_for(CONFIG, sound_device="custom", sound_device_custom="hw:2,0"))
    assert new["sound"]["device"] == "hw:2,0"
    _, problems = apply_form(CONFIG, form_for(CONFIG, quiet_start="22:00", quiet_end=""))
    assert problems == ["Quiet hours need both a start and an end time (or neither)."]


def test_shows_the_board_plays_are_all_offered_and_only_one_can_be_forced():
    names = show_names(CONFIG)
    assert names[0] == "Happily Ever After" and "Disney's Not-So-Spooky Spectacular" in names
    form = form_for(CONFIG, show_force_1="on", show_version_1="v1")
    new, problems = apply_form(CONFIG, form)
    assert problems == []
    assert new["shows"][1] == {"name": names[1], "enabled": True, "version": "v1", "force": True}
    _, problems = apply_form(CONFIG, form_for(CONFIG, show_force_0="on", show_force_1="on"))
    assert problems == ["Only one show can be forced to play at start-up."]
    _, problems = apply_form(CONFIG, form_for(CONFIG, show_version_0="v9"))
    assert "should be one of default, v1, v2" in problems[0]


def test_brightness_and_panel_settings_are_checked_like_the_app_does():
    new, problems = apply_form(CONFIG, form_for(CONFIG, matrix_led_brightness="80", matrix_led_show_refresh="true",
                                                matrix_led_gpio_mapping="adafruit-hat"))
    assert problems == []
    assert new["matrix"] == {"led_rows": 64, "led_brightness": 80, "led_show_refresh": True,
                             "led_gpio_mapping": "adafruit-hat"}
    new, _ = apply_form(CONFIG, form_for(CONFIG, matrix_led_rows=""))
    assert new["matrix"]["led_rows"] is None, "blank leaves it to the board's preset"
    for fields, problem in (({"matrix_led_brightness": "150"}, "Brightness should be 1 to 100"),
                            ({"matrix_led_rows": "48"}, "--led-rows must be one of (32, 64)"),
                            ({"matrix_led_slowdown_gpio": "9"}, "invalid choice"),
                            ({"matrix_led_cols": "wide"}, "invalid int value")):
        _, problems = apply_form(CONFIG, form_for(CONFIG, **fields))
        assert len(problems) == 1 and problem in problems[0], (fields, problems)


def test_a_config_missing_its_sections_gets_them():
    new, problems = apply_form({}, {"park": ["EPCOT"], "trip_start_0": ["2027-01-01"]})
    assert problems == []
    assert new["parks"] == ["EPCOT"]
    assert new["websocket"] == {"enabled": False, "protocol": "legacy"}
    assert new["trip_countdown"] == {"enabled": False, "trip_dates": ["2027-01-01"]}
    assert new["sound"] == {"enabled": False, "device": None}


def test_the_example_config_round_trips():
    with open(os.path.join(ROOT, "config.json-example"), encoding="utf-8") as f:
        example = json.load(f)
    example["websocket"]["enabled"] = False  # the example's key is a placeholder
    new, problems = apply_form(example, form_for(example))
    assert problems == []
    assert new["matrix"] == example["matrix"] and new["trip_countdown"] == example["trip_countdown"]


def test_the_surprise_choices_are_every_character_transition_read_without_importing_them(tmp_path):
    from display.animation import TRANSITIONS
    from settings_page.form import surprise_names
    assert surprise_names() == [name for name in TRANSITIONS if name != "wipe"]
    assert surprise_names(str(tmp_path / "missing.py")) == []


def test_a_surprise_from_the_list_is_saved_and_anything_else_refused():
    new, problems = apply_form(CONFIG, form_for(CONFIG, force_surprise="mcqueen"))
    assert problems == [] and new["force_surprise"] == "mcqueen"
    new, problems = apply_form(CONFIG, form_for(CONFIG, force_surprise=""))
    assert problems == [] and new["force_surprise"] == ""
    _, problems = apply_form(CONFIG, form_for(CONFIG, force_surprise="wipe"))
    assert problems == ["Surprise on every ride screen: 'wipe' isn't a character."]


def test_the_brightness_schedule_is_saved_as_peloton_leds_or_null():
    fields = dict(brightness_schedule="on", bright_day="80", bright_night="15", day_start="07:00", night_start="22:00")
    new, problems = apply_form(CONFIG, form_for(CONFIG, **fields))
    assert problems == []
    assert new["brightness_schedule"] == {"day": 80, "night": 15, "day_start": "07:00", "night_start": "22:00"}
    del fields["brightness_schedule"]
    new, _ = apply_form(new, form_for(CONFIG, **fields))
    assert new["brightness_schedule"] is None, "switched off"
    _, problems = apply_form(CONFIG, form_for(CONFIG, **dict(fields, brightness_schedule="on", bright_night="0")))
    assert problems == ['Day and night brightness: "night" should be 1 to 100, not 0.']
    _, problems = apply_form(CONFIG, form_for(CONFIG, **dict(fields, brightness_schedule="on", day_start="")))
    assert problems == ['Day and night brightness: "day_start" should be a time like "07:00", not \'\'.']


def test_volume_is_saved_as_a_number_blank_means_the_default_and_bad_is_refused():
    new, problems = apply_form(CONFIG, form_for(CONFIG, sound_volume="65"))
    assert problems == [] and new["sound"]["volume"] == 65
    saved = copy.deepcopy(CONFIG)
    saved["sound"]["volume"] = 70
    assert "volume" not in apply_form(saved, form_for(saved, sound_volume=""))[0]["sound"]
    assert apply_form(saved, form_for(saved))[0]["sound"]["volume"] == 70, "not posted: left alone"
    for bad in ("101", "-5", "loud"):
        _, problems = apply_form(CONFIG, form_for(CONFIG, sound_volume=bad))
        assert problems == [f"Volume should be 0 to 100, not {bad!r}."]


PRESETS = {"pi4-64x64": {"led_rows": 64}, "pi4-64x32": {"led_rows": 32}, "pizero2w-64x32": {"led_rows": 32}}
MODELS = ("pi4", "pizero2w")


def test_pi_model_is_saved_auto_removes_it_and_an_unknown_one_is_refused():
    new, problems = apply_form(CONFIG, form_for(CONFIG, pi_model="pi4"), models=MODELS)
    assert problems == [] and new["pi_model"] == "pi4"
    assert "pi_model" not in apply_form(new, form_for(new, pi_model="auto"), models=MODELS)[0]
    assert apply_form(new, form_for(new), models=MODELS)[0]["pi_model"] == "pi4", "not posted: kept"
    _, problems = apply_form(CONFIG, form_for(CONFIG, pi_model="pi5"), models=MODELS)
    assert problems == ["Pi model: 'pi5' isn't one of Pi 4, Pi Zero 2 W."]


def test_panel_size_sets_rows_and_columns_and_automatic_clears_them():
    new, problems = apply_form(CONFIG, form_for(CONFIG, panel_size="64x32"))
    assert problems == [] and (new["matrix"]["led_cols"], new["matrix"]["led_rows"]) == (64, 32)
    new, _ = apply_form(new, form_for(new, panel_size=""))
    assert (new["matrix"]["led_cols"], new["matrix"]["led_rows"]) == (None, None)
    _, problems = apply_form(CONFIG, form_for(CONFIG, panel_size="big"))
    assert problems == ["Panel size should be like 64x32, not 'big'."]
    _, problems = apply_form(CONFIG, form_for(CONFIG, panel_size="64x48"))
    assert "--led-rows must be one of (32, 64)" in problems[0], "checked like the app does"
    assert apply_form(CONFIG, form_for(CONFIG))[0]["matrix"]["led_rows"] == 64, "not posted: kept"


def test_the_dropdowns_say_what_automatic_is_on_this_board():
    types = board_types(CONFIG, None, "pi4", "Raspberry Pi 4 Model B Rev 1.5", PRESETS)
    assert types.models == [("auto", "Automatic (Pi 4, detected Pi 4)"), ("pi4", "Pi 4"), ("pizero2w", "Pi Zero 2 W")]
    assert types.sizes == [("", "Automatic (64x32, default)"), ("64x64", "64x64"), ("64x32", "64x32")]
    assert (types.auto_model, types.auto_size) == ("pi4", "64x32")
    types = board_types({}, {"preset": "pizero2w-64x64"}, "pi4", "x", PRESETS)
    assert types.models[0][1] == "Automatic (Pi Zero 2 W, boards.json entry)"
    assert types.sizes[0][1] == "Automatic (64x64, boards.json entry)"
    assert board_types({}, None, None, "Raspberry Pi 5 Model B Rev 1.0", PRESETS).models[0][1] == \
        "Automatic (none: Raspberry Pi 5 Model B Rev 1.0 isn't supported by the LED driver)"
    assert board_types({}, None, None, None, {}).models == [("auto", "Automatic (none: not a Pi)")]


def test_a_hand_set_size_is_offered_as_it_is():
    sizes = board_types({"matrix": {"led_cols": 128, "led_rows": 32}}, None, None, None, PRESETS).sizes
    assert sizes[-1] == ("128x32", "128x32")


def test_each_presets_defaults_are_the_preset_then_the_boards_own_entry():
    board = {"preset": "pizero2w-64x32", "led_pixel_mapper": "Rotate:180"}
    types = board_types({}, board, "pi4", "x", PRESETS)
    assert types.defaults == {"pi4-64x64": {"led_rows": 64, "led_pixel_mapper": "Rotate:180"},
                              "pi4-64x32": {"led_rows": 32, "led_pixel_mapper": "Rotate:180"},
                              "pizero2w-64x32": {"led_rows": 32, "led_pixel_mapper": "Rotate:180"}}
    assert types.own == {"led_pixel_mapper": "Rotate:180"}


def test_rotation_from_the_dropdown_is_saved_and_blank_goes_back_to_the_preset():
    new, problems = apply_form(CONFIG, form_for(CONFIG, matrix_led_pixel_mapper="Rotate:180"))
    assert problems == [] and new["matrix"]["led_pixel_mapper"] == "Rotate:180"
    assert apply_form(new, form_for(new, matrix_led_pixel_mapper=""))[0]["matrix"]["led_pixel_mapper"] is None


def test_the_volume_buttons_read_the_forms_volume_and_speaker():
    assert volume_from_form({"sound_volume": ["35"]}) == (35, None)
    assert volume_from_form({"sound_volume": [""]}) == (80, None) and volume_from_form({}) == (80, None)
    assert volume_from_form({"sound_volume": ["120"]}) == (None, "Volume should be 0 to 100, not '120'.")
    assert chosen_device({"sound_device": ["plughw:CARD=Device,DEV=0"]}) == "plughw:CARD=Device,DEV=0"
    assert chosen_device({"sound_device": ["custom"], "sound_device_custom": [" hw:2,0 "]}) == "hw:2,0"
    assert chosen_device({"sound_device": [""]}) is None and chosen_device({}) is None
