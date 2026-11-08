import copy
import json
import os

import pytest

from settings_page.form import (apply_form, chosen_device, masked, panel_choices, show_names, trip_rows,
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


def test_pushover_keys_are_saved_kept_when_blank_and_left_out_until_typed():
    new, problems = apply_form(CONFIG, form_for(CONFIG, pushover_user="", pushover_token="", pushover_enabled="on"))
    assert problems == [] and "pushover" not in new, "nothing typed: no section"
    new, problems = apply_form(CONFIG, form_for(CONFIG, pushover_user=" u-1 ", pushover_token="t-2",
                                                pushover_enabled="on"))
    assert problems == [] and new["pushover"] == {"user_key": "u-1", "app_token": "t-2", "enabled": True}
    again, problems = apply_form(new, form_for(new, pushover_user="", pushover_token=""))
    assert problems == [] and again["pushover"] == {"user_key": "u-1", "app_token": "t-2", "enabled": False}
    untouched, _ = apply_form(new, form_for(new))
    assert untouched["pushover"] == new["pushover"], "a form without the Pushover fields leaves it alone"


def test_sending_the_pin_with_one_key_is_refused_unless_its_off():
    _, problems = apply_form(CONFIG, form_for(CONFIG, pushover_user="u-1", pushover_token="", pushover_enabled="on"))
    assert problems == ["Sending the PIN needs both a Pushover user key and an app token (or turn it off)."]
    new, problems = apply_form(CONFIG, form_for(CONFIG, pushover_user="u-1", pushover_token=""))
    assert problems == [] and new["pushover"] == {"user_key": "u-1", "enabled": False}


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


def test_the_surprise_list_is_one_entry_per_character_that_a_roll_can_pick():
    from display.animation import TRANSITIONS
    from settings_page.form import surprise_characters
    from utils.config import SURPRISE_LOOKS, SURPRISES_UNUSED
    from utils.surprises import PARK_REVEALS
    names = surprise_characters()
    assert "genie" in names and "walle_side" in names and "saber_duel" in names
    for hidden in ("wipe", "walle", "chip_dale_swing", "saber_duel_yoda", "mine_train_all", "aliens_toys",
                   *SURPRISES_UNUSED, *PARK_REVEALS):
        assert hidden not in names
    assert set(names) | {look for group in SURPRISE_LOOKS.values() for look in group} | set(SURPRISES_UNUSED) \
        | set(PARK_REVEALS) == set(TRANSITIONS) - {"wipe"}, \
        "a new character is listed (or declared unused, or a park title's) rather than silently missing"


def surprise_form(**changes):
    """The Surprise characters page's form with every character ticked and the switch on, plus changes."""
    from settings_page.form import surprise_characters
    form = {"surprises_enabled": ["on"], **{f"surprise_{n}": ["on"] for n in surprise_characters()}}
    form.update({k: [v] if isinstance(v, str) else v for k, v in changes.items()})
    return form


def test_the_main_form_knows_nothing_of_the_surprises():
    new, _ = apply_form(CONFIG, form_for(CONFIG))
    assert "surprises" not in new and "characters" not in new


def test_unticked_characters_are_saved_as_off_and_the_switch_as_enabled():
    from settings_page.form import apply_surprises
    form = surprise_form()
    del form["surprise_tron"], form["surprise_genie"]
    new, problems = apply_surprises({}, form)
    assert problems == [] and new == {"enabled": True, "characters": {"genie": {"on": False}, "tron": {"on": False}}}
    new, _ = apply_surprises({}, {k: v for k, v in surprise_form().items() if k != "surprises_enabled"})
    assert new == {"enabled": False, "characters": {}}, "the switch is a checkbox: absent means off; all at defaults"


def test_typed_chances_are_saved_as_percents_and_blank_ones_go_back_to_the_default():
    from settings_page.form import apply_surprises
    data = {"enabled": True, "characters": {"genie": {"chance": 3}, "tron": {"chance": 2, "on": False}}}
    new, problems = apply_surprises(data, surprise_form(chance_genie="1.5", chance_tron="", ride_chance_falcon="25"))
    assert problems == []
    assert new["characters"] == {"genie": {"chance": 1.5}, "falcon": {"ride_chance": 25}}, \
        "tron is ticked again with its default chance, so it has no entry"


@pytest.mark.parametrize("typed", ["abc", "-1", "101", "1e2", "nan"])
def test_a_chance_that_is_not_a_percent_from_0_to_100_is_refused(typed):
    from settings_page.form import apply_surprises
    _, problems = apply_surprises({}, surprise_form(chance_genie=typed))
    assert problems == [f"Genie: the chance should be a percent from 0 to 100, not {typed!r}."]


def test_the_ride_screen_chances_together_cannot_pass_100_percent():
    from settings_page.form import apply_surprises
    _, problems = apply_surprises({}, surprise_form(chance_genie="60", chance_tron="50"))
    assert len(problems) == 1 and "can't pass 100%" in problems[0] and "121.6%" in problems[0]
    _, problems = apply_surprises({}, surprise_form(chance_genie="60", chance_tron="30"))
    assert len(problems) == 1, "the other characters' defaults count too"
    _, problems = apply_surprises({}, surprise_form(chance_genie="0", chance_tron="0", chance_baymax="0"))
    assert problems == []


RIDES = {"Magic Kingdom": ["Space Mountain", "Haunted Mansion"],
         "Hollywood Studios": ["Millennium Falcon: Smugglers Run", "Star Wars: Rise of the Resistance", "Tower of Terror"]}


def test_any_character_can_take_a_chance_on_any_ride_screen_and_rides_of_their_own():
    from settings_page.form import apply_surprises
    new, problems = apply_surprises({}, surprise_form(chance_falcon="2", ride_chance_genie="30",
                                                      rides_set_genie="1", rides_genie=["Space Mountain", "Test Track"]), RIDES)
    assert problems == []
    assert new["characters"] == {"falcon": {"chance": 2}, "genie": {"ride_chance": 30, "rides": ["Space Mountain", "Test Track"]}}
    assert [type(v) for v in (new["characters"]["falcon"]["chance"], new["characters"]["genie"]["ride_chance"])] == [int, int], \
        "25 is written 25, not 25.0, so an export reads cleanly"


def test_a_character_s_default_rides_are_the_rides_whose_names_have_their_pieces_in_them():
    from settings_page.form import default_rides
    assert default_rides("falcon", RIDES) == ["Millennium Falcon: Smugglers Run", "Star Wars: Rise of the Resistance"]
    assert default_rides("genie", RIDES) == [] and default_rides("falcon", {}) == [] and default_rides("falcon", None) == []


def test_ticking_just_the_default_rides_saves_nothing_so_they_keep_following_the_defaults():
    from settings_page.form import apply_surprises
    defaults = ["Star Wars: Rise of the Resistance", "Millennium Falcon: Smugglers Run"]
    new, _ = apply_surprises({}, surprise_form(rides_set_falcon="1", rides_falcon=defaults), RIDES)
    assert new["characters"] == {}
    new, _ = apply_surprises({}, surprise_form(rides_set_falcon="1", rides_falcon=defaults + ["Space Mountain"]), RIDES)
    assert new["characters"]["falcon"]["rides"] == ["Millennium Falcon: Smugglers Run", "Space Mountain",
                                                    "Star Wars: Rise of the Resistance"]


def test_unticking_every_ride_saves_an_empty_list_which_means_no_rides_at_all():
    from settings_page.form import apply_surprises
    new, _ = apply_surprises({}, surprise_form(rides_set_falcon="1"), RIDES)
    assert new["characters"] == {"falcon": {"rides": []}}
    new, _ = apply_surprises({}, surprise_form(rides_set_genie="1"), RIDES)
    assert new["characters"] == {}, "Genie has none by default: nothing to save"


def test_a_ride_picker_that_was_never_opened_leaves_the_saved_rides_alone():
    from settings_page.form import apply_surprises
    data = {"characters": {"falcon": {"rides": ["Space Mountain"]}, "genie": {"rides": []}}}
    new, _ = apply_surprises(data, surprise_form(), RIDES)
    assert new["characters"] == data["characters"], "no rides_set_ field: not touched, even with the list unloaded"
    new, _ = apply_surprises(data, surprise_form(rides_set_falcon="1", rides_falcon=["Haunted Mansion"]), RIDES)
    assert new["characters"]["falcon"] == {"rides": ["Haunted Mansion"]} and new["characters"]["genie"] == {"rides": []}


def test_none_saved_as_none_stays_none_even_when_the_ride_list_has_none_of_the_default_rides():
    from settings_page.form import apply_surprises
    epcot_only = {"EPCOT": ["Test Track"]}
    new, _ = apply_surprises({}, surprise_form(rides_set_falcon="saved"), epcot_only)
    assert new["characters"] == {"falcon": {"rides": []}}, "saved as none: not mistaken for the defaults"
    new, _ = apply_surprises({}, surprise_form(rides_set_falcon="1"), epcot_only)
    assert new["characters"] == {}, "no marker of that: nothing ticked, nothing unticked, so the defaults"
    new, _ = apply_surprises({}, surprise_form(rides_set_genie="saved"), epcot_only)
    assert new["characters"] == {}, "Genie has no default rides, so none is nothing to save"
    both = {"Hollywood Studios": ["Millennium Falcon: Smugglers Run"]}
    new, _ = apply_surprises({}, surprise_form(rides_set_falcon="saved", rides_falcon=["Millennium Falcon: Smugglers Run"]), both)
    assert new["characters"] == {}, "saved rides that are just the defaults are the defaults"


def test_chosen_rides_are_saved_sorted_without_blanks_or_repeats():
    from settings_page.form import apply_surprises
    new, _ = apply_surprises({}, surprise_form(rides_set_tron="1",
                                               rides_tron=["Test Track", " ", "Space Mountain", "Test Track"]), RIDES)
    assert new["characters"]["tron"] == {"rides": ["Space Mountain", "Test Track"]}


def test_tink_and_buzz_are_not_on_the_page_and_a_hand_saved_entry_for_them_survives_a_save():
    from settings_page.form import apply_surprises, surprise_rows
    assert not {"tink", "buzz"} & {row.name for row in surprise_rows()}
    data = {"characters": {"tink": {"on": False}}}
    new, problems = apply_surprises(data, surprise_form(chance_tink="5", rides_set_tink="1", rides_tink=["Space Mountain"]), RIDES)
    assert problems == [] and new["characters"] == {"tink": {"on": False}}, "the form can't change them"


def test_too_many_rides_or_a_huge_name_are_refused():
    from settings_page.form import MAX_RIDE_NAME, MAX_RIDES_PER_CHARACTER, apply_surprises
    many = [f"Ride {i}" for i in range(MAX_RIDES_PER_CHARACTER + 1)]
    _, problems = apply_surprises({}, surprise_form(rides_set_tron="1", rides_tron=many), RIDES)
    assert problems == ["Tron: that's too many rides, or a ride name that's too long."]
    _, problems = apply_surprises({}, surprise_form(rides_set_tron="1", rides_tron=["x" * (MAX_RIDE_NAME + 1)]), RIDES)
    assert len(problems) == 1


def test_characters_and_settings_a_newer_version_saved_survive_a_save():
    from settings_page.form import apply_surprises
    data = {"enabled": True, "future": 1, "characters": {"from_the_future": {"chance": 4},
                                                         "genie": {"on": False, "note": "keep"}}}
    new, _ = apply_surprises(data, surprise_form())
    assert new == {"enabled": True, "future": 1, "characters": {"from_the_future": {"chance": 4},
                                                                 "genie": {"note": "keep"}}}


def test_the_rows_carry_each_characters_default_chances_and_rides():
    from settings_page.form import surprise_rows
    rows = {r.name: r for r in surprise_rows()}
    assert (rows["genie"].anywhere, rows["genie"].own, rows["genie"].rides) == ("0.5", "10", []), \
        "a character with no rides of its own gets the 10% a new ride choice would use"
    assert rows["walle_side"].anywhere == "1.2"
    assert rows["falcon"].anywhere == "0" and rows["falcon"].own == "10"
    assert rows["falcon"].rides == ["Smugglers Run", "Rise Of The Resistance"]
    assert (rows["mike"].anywhere, rows["mike"].own) == ("0.8", "10"), "Mike has both"
    assert "tink" not in rows and "buzz" not in rows, "park titles aren't ride-screen surprises"


def test_import_takes_what_export_wrote_and_keeps_only_what_the_page_would_save():
    from settings_page.form import import_surprises
    text = json.dumps({"enabled": False, "future_key": 1, "characters": {
        "genie": {"on": False, "chance": 1.5, "ride_chance": 20, "rides": ["Test Track", "Space Mountain", " "], "junk": 1},
        "falcon": {"on": True}}})
    data, problems, skipped = import_surprises(text)
    assert problems == [] and skipped == []
    assert data == {"enabled": False, "characters": {
        "genie": {"on": False, "chance": 1.5, "ride_chance": 20, "rides": ["Space Mountain", "Test Track"]}}}, \
        "no future_key or junk, and a character at its defaults ('on' only) has no entry"


def test_import_skips_characters_this_version_does_not_have_and_says_so():
    from settings_page.form import import_surprises
    data, problems, skipped = import_surprises(json.dumps({"characters": {"genie": {"chance": 2}, "new_one": {"chance": 5},
                                                                          "tink": {"on": False}}}))
    assert problems == [] and sorted(skipped) == ["new_one", "tink"], "Tink and Buzz aren't on the page"
    assert data["characters"] == {"genie": {"chance": 2}}


@pytest.mark.parametrize("text, problem", [
    ("{not json", "isn't settings the Export button copied: it isn't valid JSON"),
    ("[1, 2]", "it should be an object"), ('"hello"', "it should be an object"),
    ('{"enabled": "yes"}', '"enabled" should be true or false'),
    ('{"characters": []}', '"characters" should be an object'),
    ('{"characters": {"genie": "on"}}', "Genie: its settings should be an object"),
    ('{"characters": {"genie": {"on": "no"}}}', 'Genie: "on" should be true or false'),
    ('{"characters": {"genie": {"chance": 101}}}', 'Genie: "chance" should be a percent from 0 to 100, not 101'),
    ('{"characters": {"genie": {"chance": true}}}', "Genie: \"chance\" should be a percent"),
    ('{"characters": {"genie": {"ride_chance": "5"}}}', 'Genie: "ride_chance" should be a percent'),
    ('{"characters": {"genie": {"rides": "Test Track"}}}', 'Genie: "rides" should be a list of ride names'),
    ('{"characters": {"genie": {"rides": [1]}}}', 'Genie: "rides" should be a list of ride names'),
    ('{"characters": {"genie": {"chance": 60}, "tron": {"chance": 50}}}', "can't pass 100%"),
])
def test_import_refuses_what_the_page_would_not_save(text, problem):
    from settings_page.form import import_surprises
    data, problems, _ = import_surprises(text)
    assert any(problem in p for p in problems)


def test_a_snapshot_has_every_character_with_its_on_chances_and_rides_defaults_included():
    from settings_page.form import character_label, snapshot_surprises, surprise_rows
    snap = snapshot_surprises({"enabled": True, "characters": {"tron": {"on": False}, "genie": {"chance": 1.5}}}, RIDES)
    assert snap["enabled"] is True and set(snap["characters"]) == {row.name for row in surprise_rows()}
    assert snap["characters"]["tron"] == {"on": False, "chance": 0.8, "ride_chance": 10, "rides": []}
    assert snap["characters"]["genie"]["chance"] == 1.5 and snap["characters"]["genie"]["on"] is True
    assert snap["characters"]["falcon"]["rides"] == ["Millennium Falcon: Smugglers Run", "Star Wars: Rise of the Resistance"], \
        "the rides it visits by default, by name"
    assert snap["characters"]["jack_sally"]["ride_chance"] == 50
    assert list(snap["characters"]) == sorted(snap["characters"], key=lambda n: character_label(n).lower()), "readable order"


def test_a_snapshot_names_the_default_rides_by_their_pieces_when_the_ride_list_has_none_of_them():
    from settings_page.form import snapshot_surprises
    for rides in ({}, {"EPCOT": ["Test Track"]}):
        snap = snapshot_surprises({}, rides)
        assert snap["characters"]["falcon"]["rides"] == ["smugglers run", "rise of the resistance"]
        assert snap["characters"]["mike"]["rides"] == ["laugh floor"]
        assert snap["characters"]["genie"]["rides"] == [], "no default rides: an empty list is just that"


def test_a_snapshots_rides_import_back_to_the_defaults_wherever_the_ride_list_is_missing_them():
    from settings_page.form import import_surprises, snapshot_surprises
    for rides in (None, {}, {"EPCOT": ["Test Track"]}, RIDES):
        data, problems, _ = import_surprises(json.dumps(snapshot_surprises({}, rides)), rides)
        assert problems == [] and data == {"enabled": True, "characters": {}}, rides


def test_saved_rides_win_in_a_snapshot_even_none():
    from settings_page.form import snapshot_surprises
    snap = snapshot_surprises({"characters": {"falcon": {"rides": []}, "genie": {"rides": ["Test Track"]}}}, RIDES)
    assert snap["characters"]["falcon"]["rides"] == [] and snap["characters"]["genie"]["rides"] == ["Test Track"]


def test_importing_a_whole_snapshot_keeps_only_what_differs_from_the_defaults():
    from settings_page.form import import_surprises, snapshot_surprises
    snap = snapshot_surprises({"characters": {"tron": {"on": False}, "genie": {"chance": 1.5, "rides": ["Test Track"]}}}, RIDES)
    data, problems, skipped = import_surprises(json.dumps(snap), RIDES)
    assert problems == [] and skipped == []
    assert data == {"enabled": True, "characters": {"tron": {"on": False},
                                                    "genie": {"chance": 1.5, "rides": ["Test Track"]}}}


def test_importing_none_for_a_character_whose_default_rides_are_missing_from_the_list_keeps_the_none():
    from settings_page.form import import_surprises
    text = json.dumps({"characters": {"falcon": {"rides": []}, "genie": {"rides": []}}})
    data, _, _ = import_surprises(text, {"EPCOT": ["Test Track"]})
    assert data["characters"] == {"falcon": {"rides": []}}, "Falcon has defaults to switch off; Genie has none"


def test_what_one_board_exports_another_imports_as_the_same_settings():
    from settings_page.form import apply_surprises, import_surprises
    form = surprise_form(chance_genie="1.5", ride_chance_falcon="25", rides_set_genie="1",
                         rides_genie=["Space Mountain", "Test Track"], rides_set_falcon="1", rides_falcon=[])
    del form["surprise_tron"]
    exported, problems = apply_surprises({}, form, RIDES)
    assert problems == []
    from settings_page.form import snapshot_surprises
    imported, problems, skipped = import_surprises(json.dumps(snapshot_surprises(exported, RIDES), indent=2), RIDES)
    assert problems == [] and skipped == [] and imported == exported


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


def test_pi_model_is_saved_auto_removes_it_and_an_unknown_one_is_refused():
    new, problems = apply_form(CONFIG, form_for(CONFIG, pi_model="pi4"))
    assert problems == [] and new["pi_model"] == "pi4"
    assert "pi_model" not in apply_form(new, form_for(new, pi_model="auto"))[0]
    assert apply_form(new, form_for(new))[0]["pi_model"] == "pi4", "not posted: kept"
    _, problems = apply_form(CONFIG, form_for(CONFIG, pi_model="pi5"))
    assert problems == ["Pi model: 'pi5' isn't one of Pi 4, Pi 3, Pi Zero 2 W."]


def test_panel_size_sets_rows_and_columns():
    new, problems = apply_form(CONFIG, form_for(CONFIG, panel_size="64x32"))
    assert problems == [] and (new["matrix"]["led_cols"], new["matrix"]["led_rows"]) == (64, 32)
    _, problems = apply_form(CONFIG, form_for(CONFIG, panel_size="big"))
    assert problems == ["Panel size should be like 64x32, not 'big'."]
    _, problems = apply_form(CONFIG, form_for(CONFIG, panel_size="64x48"))
    assert "--led-rows must be one of (32, 64)" in problems[0], "checked like the app does"
    assert apply_form(CONFIG, form_for(CONFIG))[0]["matrix"]["led_rows"] == 64, "not posted: kept"


def test_the_pi_model_dropdown_says_what_automatic_is_on_this_pi():
    choices = panel_choices(CONFIG, "pi4", "Raspberry Pi 4 Model B Rev 1.5")
    assert choices.models == [("auto", "Automatic (Pi 4)"), ("pi4", "Pi 4"), ("pi3", "Pi 3"),
                              ("pizero2w", "Pi Zero 2 W")]
    assert choices.auto_model == "pi4"
    assert panel_choices({}, None, "Raspberry Pi 5 Model B Rev 1.0").models[0][1] == \
        "Automatic (none: Raspberry Pi 5 Model B Rev 1.0 isn't supported by the LED driver)"
    assert panel_choices({}, None, None).models[0] == ("auto", "Automatic (none: not a Pi)")


def test_panel_size_offers_both_sizes_and_a_hand_set_one():
    assert panel_choices({}, None, None).sizes == [("64x64", "64x64"), ("64x32", "64x32")]
    assert panel_choices({"matrix": {"led_cols": 128, "led_rows": 32}}, None, None).sizes[-1] == ("128x32", "128x32")


def test_blank_fields_say_each_models_default_or_the_drivers():
    blanks = panel_choices({}, "pi4", "Raspberry Pi 4 Model B Rev 1.5").blanks
    assert blanks["pi4"]["led_slowdown_gpio"] == "Pi 4 default: 4"
    assert blanks["pi4"]["led_pwm_lsb_nanoseconds"] == "Pi 4 default: 200"
    assert blanks["pizero2w"]["led_pwm_lsb_nanoseconds"] == "Default: 130", "the driver's, not the model's"
    assert blanks["pizero2w"]["led_pixel_mapper"] == "Default", "no rotation"
    assert blanks["pi3"]["led_show_refresh"] == "Default: Off"
    assert blanks[""]["led_gpio_mapping"] == "Default: adafruit-hat-pwm", "a Pi we don't know: the bonnet's"
    assert panel_choices({}, None, None).blanks[""]["led_gpio_mapping"] == "Default", "the emulator: the driver's"


def test_rotation_from_the_dropdown_is_saved_and_blank_goes_back_to_the_default():
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


def test_trips_are_listed_soonest_first_whatever_order_config_json_has_them_in():
    config = {"trip_countdown": {"trip_dates": [
        {"start": "2027-12-20", "name": "Christmas"}, "soon", "2027-06-01",
        {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"}]}}
    assert trip_rows(config) == [("2027-03-14", "2027-03-19", "Spring Break"), ("2027-06-01", "", ""),
                                 ("2027-12-20", "", "Christmas"), ("soon", "", "")], "a start that isn't a date goes last"


def test_trips_are_saved_soonest_first_so_config_json_reads_in_order():
    form = form_for(CONFIG, trip_start_0="2027-12-20", trip_name_0="Christmas", trip_end_0="",
                    trip_start_2="2027-01-05", trip_name_2="New Year")
    new, problems = apply_form(CONFIG, form)
    assert problems == []
    assert [t["start"] if isinstance(t, dict) else t for t in new["trip_countdown"]["trip_dates"]] == [
        "2027-01-05", "2027-06-01", "2027-12-20"]
