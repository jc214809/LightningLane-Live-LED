import copy
import json
import os

import pytest

from settings_page.form import WDW_PARKS, apply_form, masked, show_names, trip_rows

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
        "park": [p for p in config["parks"] if p in WDW_PARKS], "parks_other": [""],
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


def test_parks_keep_the_pages_order_then_others_as_typed_and_one_is_needed():
    new, _ = apply_form(CONFIG, form_for(CONFIG, park=["Animal Kingdom", "Magic Kingdom"],
                                         parks_other="Cedar Point,  Kings Island ,,Magic Kingdom"))
    assert new["parks"] == ["Magic Kingdom", "Animal Kingdom", "Cedar Point", "Kings Island"]
    _, problems = apply_form(CONFIG, form_for(CONFIG, park=[]))
    assert problems == ["Pick at least one park."]


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
