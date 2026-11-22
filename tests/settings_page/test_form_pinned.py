"""Pins what settings_page/form.py's apply_form, apply_surprises and import_surprises return today, for the
code-health refactor (docs/plans/CODE-HEALTH-PLAN.md, item 2a): each case's exact result (the config or
surprises.json, key order included, and the problems in the order they're raised) is stored in
fixtures/form_pinned.json. A change that alters any of them fails here. To rewrite the fixture on purpose,
run once with PIN_REGEN=1 and read the diff."""
import copy
import json
import os
import re

import pytest

from settings_page.form import apply_form, apply_surprises, import_surprises, surprise_names

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXTURE = os.path.join(HERE, "fixtures", "form_pinned.json")

PARK_NAMES = [("Magic Kingdom", "x"), ("EPCOT", "x"), ("Hollywood Studios", "x"), ("Animal Kingdom", "x")]
RIDES = {"Magic Kingdom": ["Space Mountain", "Haunted Mansion"],
         "Hollywood Studios": ["Millennium Falcon: Smugglers Run", "Star Wars: Rise of the Resistance",
                               "Tower of Terror"]}


def example(**changes):
    with open(os.path.join(ROOT, "config.json-example"), encoding="utf-8") as f:
        config = json.load(f)
    config["websocket"]["api_key"] = "tp-secret-1234"
    config.update(changes)
    return config


def form(**fields):
    return {k: [v] if isinstance(v, str) else list(v) for k, v in fields.items()}


# What the page posts for the example config, untouched.
BASE = form(ws_enabled="on", ws_protocol="legacy", themeparks_key="", weather_key="", park=[
    "Magic Kingdom", "EPCOT", "Hollywood Studios", "Animal Kingdom"], park_add="",
    trips_enabled="on", trip_start_0="2027-03-14", trip_end_0="2027-03-19", trip_name_0="Spring Break",
    trip_start_1="2027-06-01", trip_end_1="", trip_name_1="", trip_start_2="", trip_end_2="", trip_name_2="",
    sound_device="", sound_device_custom="", quiet_start="22:00", quiet_end="08:00", force_surprise="",
    show_name_0="Happily Ever After", show_version_0="default", show_enabled_0="on")


def minimal():
    return form(park="EPCOT")


FULL = form(
    ws_enabled="on", ws_protocol="preview", themeparks_key="  tp-new-5555 ", weather_key="owm-new",
    pushover_user=" u-1 ", pushover_token="t-2", pushover_enabled="on",
    park=["Magic Kingdom", "EPCOT", "Animal Kingdom"], park_remove=["epcot"], park_add="hollywood  studios, ,MAGIC kingdom",
    trips_enabled="on",
    trip_start_0="2027-09-01", trip_end_0="2027-09-05", trip_name_0="Fall", trip_start_1="2027-03-14",
    trip_end_1="", trip_name_1="Spring", trip_start_2="2027-02-01", trip_end_2="2027-02-03", trip_name_2="",
    trip_start_3="2027-01-01", trip_end_3="", trip_name_3="", trip_remove_3="on",
    trip_start_4="", trip_end_4="", trip_name_4="",
    sound_enabled="on", sound_device="custom", sound_device_custom=" hw:1,0 ", sound_volume="55",
    quiet_start="21:30", quiet_end="07:15",
    show_name_0="Happily Ever After", show_version_0="v2", show_enabled_0="on", show_force_0="on",
    show_name_1="Brand New Show", show_version_1="v1", show_name_2="Christmas Party", show_version_2="default",
    show_enabled_2="on",
    pi_model="pi4", panel_size="64x32",
    matrix_led_rows="32", matrix_led_cols="64", matrix_led_chain="2", matrix_led_parallel="1", matrix_led_pwm_bits="9",
    matrix_led_brightness="60", matrix_led_gpio_mapping="adafruit-hat", matrix_led_scan_mode="1",
    matrix_led_pwm_lsb_nanoseconds="130", matrix_led_show_refresh="true", matrix_led_slowdown_gpio="2",
    matrix_led_no_hardware_pulse="", matrix_led_rgb_sequence="RGB", matrix_led_panel_type="FM6126A",
    matrix_led_pixel_mapper="", matrix_led_row_addr_type="0", matrix_led_multiplexing="0",
    matrix_led_limit_refresh="0", matrix_led_pwm_dither_bits="0", matrix_emulated="false",
    matrix_drop_privileges="true",
    brightness_schedule="on", bright_day="90", bright_night="20", day_start="07:00", night_start="21:00",
    debug="on", force_surprise=surprise_names()[0])

SHOWS_BASE = [{"name": "Happily Ever After", "enabled": True, "version": "v2", "force": True},
              {"name": "Other", "enabled": False, "version": "v1"}, "junk", {"name": 5}]


def form_cases():
    """(id, config, form, park_names)."""
    ex = example
    cases = [
        ("full", ex(), FULL, PARK_NAMES),
        ("full_no_park_list", ex(), FULL, ()),
        ("untouched", ex(), BASE, PARK_NAMES),
        ("empty_form", ex(), {}, ()),
        ("minimal", ex(), minimal(), ()),
        ("minimal_on_empty_config", {}, minimal(), ()),
        ("minimal_on_odd_sections", {"websocket": "x", "matrix": None, "sound": [], "trip_countdown": 3,
                                    "shows": "no", "pushover": "no", "weather": 1, "old": {"keep": True}},
         minimal(), ()),
        ("bad_protocol", ex(), {**BASE, **form(ws_protocol="carrier-pigeon")}, ()),
        ("protocol_blank_field_absent", ex(), {k: v for k, v in BASE.items() if k != "ws_protocol"}, ()),
        ("live_updates_without_key", ex(websocket={"enabled": True, "api_key": "<THEMEPARKS_API_KEY_HERE>"}),
         BASE, ()),
        ("live_updates_off", ex(), {k: v for k, v in BASE.items() if k != "ws_enabled"}, ()),
        ("pushover_nothing_typed", ex(), {**BASE, **form(pushover_user="", pushover_token="", pushover_enabled="on")}, ()),
        ("pushover_nothing_typed_none_saved", ex(pushover=None),
         {**BASE, **form(pushover_user="", pushover_token="", pushover_enabled="on")}, ()),
        ("pushover_one_key_on", ex(), {**BASE, **form(pushover_user="u-1", pushover_token="", pushover_enabled="on")}, ()),
        ("pushover_one_key_off", ex(), {**BASE, **form(pushover_user="u-1", pushover_token="")}, ()),
        ("pushover_both_keys", ex(), {**BASE, **form(pushover_user="u-1", pushover_token="t-2", pushover_enabled="on")}, ()),
        ("pushover_saved_keys_blank_form", ex(), {**BASE, **form(pushover_user="", pushover_token="")}, ()),
        ("unknown_park", ex(), {**BASE, **form(park=["Magic Kingdom", "Narnia"], park_add="")}, PARK_NAMES),
        ("no_parks", ex(), {**BASE, **form(park=[], park_add="")}, ()),
        ("all_parks_removed", ex(), {**BASE, **form(park_remove=["magic kingdom", " EPCOT ", "hollywood studios",
                                                                 "animal kingdom"])}, ()),
        ("park_added_unknown_and_duplicate", ex(), {**BASE, **form(park_add="Narnia, epcot,Narnia")}, PARK_NAMES),
        ("trip_end_before_start", ex(), {**BASE, **form(trip_start_0="2027-03-14", trip_end_0="2027-03-01",
                                                          trip_name_0="Backwards")}, ()),
        ("trip_end_before_start_no_name", ex(), {**BASE, **form(trip_start_0="2027-03-14", trip_end_0="2027-03-01",
                                                                  trip_name_0="")}, ()),
        ("trip_bad_start", ex(), {**BASE, **form(trip_start_0="soon", trip_end_0="", trip_name_0="Someday")}, ()),
        ("trip_bad_start_no_name", ex(), {**BASE, **form(trip_start_0="soon", trip_end_0="", trip_name_0="")}, ()),
        ("trip_no_start_with_name", ex(), {**BASE, **form(trip_start_0="", trip_end_0="", trip_name_0="Nameless")}, ()),
        ("trip_bad_end", ex(), {**BASE, **form(trip_start_0="2027-03-14", trip_end_0="later", trip_name_0="")}, ()),
        ("trip_removed_and_blank", ex(), {**BASE, **form(trip_remove_0="on", trip_start_1="", trip_end_1="",
                                                           trip_name_1="")}, ()),
        ("trips_off_old_single_date", ex(trip_countdown={"enabled": True, "trip_date": "2027-01-01"}),
         {k: v for k, v in BASE.items() if not k.startswith(("trip_", "trips_"))}, ()),
        ("volume_set", ex(), {**BASE, **form(sound_volume="0")}, ()),
        ("volume_bad", ex(), {**BASE, **form(sound_volume="loud")}, ()),
        ("volume_over", ex(), {**BASE, **form(sound_volume="101")}, ()),
        ("volume_blank_clears", ex(), {**BASE, **form(sound_volume="")}, ()),
        ("volume_absent_keeps", ex(), BASE, ()),
        ("sound_device_listed", ex(), {**BASE, **form(sound_device="plughw:2,0", sound_enabled="on")}, ()),
        ("quiet_hours_cleared", ex(), {**BASE, **form(quiet_start="", quiet_end="")}, ()),
        ("quiet_hours_half", ex(), {**BASE, **form(quiet_start="22:00", quiet_end="")}, ()),
        ("quiet_hours_garbage", ex(), {**BASE, **form(quiet_start="late", quiet_end="early")}, ()),
        ("show_bad_version", ex(), {**BASE, **form(show_version_0="v9", show_name_1="Another", show_version_1="v1")}, ()),
        ("show_new_added_and_old_updated", ex(shows=copy.deepcopy(SHOWS_BASE)),
         {**BASE, **form(show_name_0="Happily Ever After", show_version_0="v1", show_name_1="Other",
                         show_version_1="v2", show_enabled_1="on", show_name_2="Third", show_version_2="default")}, ()),
        ("show_two_forced", ex(), {**BASE, **form(show_name_1="Second", show_version_1="v1", show_force_0="on",
                                                    show_force_1="on")}, ()),
        ("show_two_forced_already_saved", ex(shows=copy.deepcopy(SHOWS_BASE) + [{"name": "Z", "force": True}]),
         BASE, ()),
        ("show_no_default_version_field", ex(), {k: v for k, v in {**BASE, **form(show_name_1="Late")}.items()
                                                  if k != "show_version_0"}, ()),
        ("shows_not_a_list", ex(shows={"name": "x"}), BASE, ()),
        ("pi_model_auto", ex(pi_model="pi4"), {**BASE, **form(pi_model="auto")}, ()),
        ("pi_model_blank", ex(pi_model="pi4"), {**BASE, **form(pi_model="")}, ()),
        ("pi_model_pi3", ex(), {**BASE, **form(pi_model="pi3")}, ()),
        ("pi_model_unknown", ex(), {**BASE, **form(pi_model="pi9")}, ()),
        ("panel_size_good", ex(), {**BASE, **form(panel_size="128x32")}, ()),
        ("panel_size_bad", ex(), {**BASE, **form(panel_size="big")}, ()),
        ("matrix_blank_text_and_number_fields", ex(matrix={"led_rows": 64, "led_brightness": 50, "emulated": True}),
         {**BASE, **form(matrix_led_rows="", matrix_led_brightness="", matrix_emulated="", matrix_led_gpio_mapping="x")}, ()),
        ("matrix_bad_number_stays_text", ex(), {**BASE, **form(matrix_led_rows="tall", matrix_led_chain="-3")}, ()),
        ("matrix_negative_number", ex(), {**BASE, **form(matrix_led_slowdown_gpio="-1")}, ()),
        ("matrix_switch_values", ex(), {**BASE, **form(matrix_emulated="true", matrix_drop_privileges="false",
                                                         matrix_led_show_refresh="maybe")}, ()),
        ("matrix_not_a_dict", ex(matrix=[1]), {**BASE, **form(matrix_led_rows="32")}, ()),
        ("brightness_low", ex(), {**BASE, **form(matrix_led_brightness="0")}, ()),
        ("brightness_high", ex(), {**BASE, **form(matrix_led_brightness="101")}, ()),
        ("brightness_text", ex(), {**BASE, **form(matrix_led_brightness="bright")}, ()),
        ("brightness_ok", ex(), {**BASE, **form(matrix_led_brightness="100")}, ()),
        ("brightness_saved_bad_and_not_posted", ex(matrix={"led_brightness": True}), BASE, ()),
        ("schedule_on", ex(), {**BASE, **form(bright_day="80", bright_night="10", brightness_schedule="on",
                                                day_start="06:30", night_start="20:30")}, ()),
        ("schedule_bad", ex(), {**BASE, **form(bright_day="bright", bright_night="500", brightness_schedule="on",
                                                 day_start="nope", night_start="")}, ()),
        ("schedule_off", ex(brightness_schedule={"day": 1}), {**BASE, **form(bright_day="80", bright_night="10")}, ()),
        ("schedule_absent_keeps", ex(brightness_schedule={"day": 1}), BASE, ()),
        ("debug_on", ex(), {**BASE, **form(debug="on")}, ()),
        ("surprise_forced", ex(), {**BASE, **form(force_surprise=surprise_names()[1])}, ()),
        ("surprise_unknown", ex(force_surprise="old"), {**BASE, **form(force_surprise="not_a_character")}, ()),
        ("surprise_absent_clears", ex(force_surprise="old"), {k: v for k, v in BASE.items() if k != "force_surprise"}, ()),
        ("many_problems_in_order", ex(), form(
            ws_enabled="on", ws_protocol="x", park=["Narnia"], trip_start_0="soon", sound_volume="x",
            quiet_start="a", quiet_end="b", show_name_0="s", show_version_0="zz", show_force_0="on",
            pi_model="zz", panel_size="q", matrix_led_rows="tall", matrix_led_brightness="0", bright_day="x",
            brightness_schedule="on", force_surprise="zzz", pushover_user="u", pushover_enabled="on"), PARK_NAMES),
    ]
    ids = [c[0] for c in cases]
    assert len(ids) == len(set(ids))
    return cases


def surprise_form(**changes):
    from settings_page.form import surprise_characters
    out = {"surprises_enabled": ["on"], **{f"surprise_{n}": ["on"] for n in surprise_characters()}}
    out.update({k: [v] if isinstance(v, str) else list(v) for k, v in changes.items()})
    return out


MANY_RIDES = [f"Ride {i}" for i in range(301)]
DEFAULTS = ["Millennium Falcon: Smugglers Run", "Star Wars: Rise of the Resistance"]


def surprise_cases():
    """(id, data, form, rides)."""
    full = {"enabled": False, "future": 1, "characters": {
        "genie": {"on": False, "chance": 9, "ride_chance": 5, "rides": ["x"], "junk": 1},
        "falcon": {"rides": ["Tower of Terror"]}, "newer_one": {"on": False}, "tron": "bad", "mike": {}}}
    return [
        ("s_empty", {}, surprise_form(), None),
        ("s_data_not_dict", [1], {}, None),
        ("s_everything_off_no_switch", {}, {}, None),
        ("s_saved_state_kept", full, surprise_form(), RIDES),
        ("s_saved_cleared_by_defaults", full, surprise_form(chance_genie="", ride_chance_genie="",
                                                              rides_set_falcon="1", rides_falcon=DEFAULTS), RIDES),
        ("s_characters_not_dict", {"characters": [1]}, surprise_form(), None),
        ("s_chances", {}, surprise_form(chance_genie="1.5", chance_tron="", ride_chance_falcon="25",
                                        ride_chance_mike="12.0", surprise_baymax="off"), None),
        ("s_bad_chances", {}, surprise_form(chance_genie="lots", ride_chance_tron="101", chance_mike="-1",
                                            chance_olaf="1e3"), None),
        ("s_total_over_100", {}, surprise_form(chance_genie="60", chance_tron="50"), None),
        ("s_total_over_100_with_defaults_added", {}, surprise_form(chance_genie="99.5", chance_tron="0.8"), None),
        ("s_rides_picked", {}, surprise_form(rides_set_falcon="1", rides_falcon=DEFAULTS + ["Space Mountain"]), RIDES),
        ("s_rides_default_set_is_dropped", {}, surprise_form(rides_set_falcon="1", rides_falcon=DEFAULTS), RIDES),
        ("s_rides_none_for_visitor", {}, surprise_form(rides_set_falcon="1"), RIDES),
        ("s_rides_none_saved", {}, surprise_form(rides_set_falcon="saved"), {"EPCOT": ["Test Track"]}),
        ("s_rides_none_saved_non_visitor", {}, surprise_form(rides_set_genie="saved"), {"EPCOT": ["Test Track"]}),
        ("s_rides_none_not_saved", {}, surprise_form(rides_set_genie="1"), RIDES),
        ("s_rides_deduped_and_stripped", {}, surprise_form(rides_set_tron="1", rides_tron=[" B ", "a", "B", "", "a"]), None),
        ("s_rides_too_many", {}, surprise_form(rides_set_tron="1", rides_tron=MANY_RIDES), None),
        ("s_rides_name_too_long", {}, surprise_form(rides_set_tron="1", rides_tron=["x" * 121]), None),
        ("s_rides_untouched_picker_keeps_saved", {"characters": {"falcon": {"rides": ["Tower of Terror"]}}},
         surprise_form(), RIDES),
        ("s_rides_picker_replaces_saved", {"characters": {"falcon": {"rides": ["Tower of Terror"]}}},
         surprise_form(rides_set_falcon="1", rides_falcon=DEFAULTS), RIDES),
        ("s_many_problems_in_order", {}, surprise_form(chance_genie="x", ride_chance_genie="x",
                                                        rides_set_tron="1", rides_tron=MANY_RIDES,
                                                        chance_mike="70", chance_olaf="70"), None),
    ]


def import_cases():
    """(id, text, rides)."""
    def j(obj):
        return json.dumps(obj)
    export = {"enabled": False, "future_key": 1, "characters": {
        "genie": {"on": False, "chance": 1.5, "ride_chance": 20, "rides": ["Test Track", "Space Mountain", " "], "junk": 1},
        "falcon": {"on": True}}}
    return [
        ("i_export", j(export), None),
        ("i_export_with_rides", j(export), RIDES),
        ("i_empty_object", "{}", None),
        ("i_invalid_json", "{not json", None),
        ("i_array", "[1, 2]", None),
        ("i_string", '"hello"', None),
        ("i_enabled_not_bool", '{"enabled": "yes"}', None),
        ("i_characters_not_object", '{"characters": []}', None),
        ("i_enabled_and_characters_bad", '{"enabled": 1, "characters": 2}', None),
        ("i_unknown_and_park_titles_skipped", j({"characters": {"genie": {"chance": 2}, "new_one": {"chance": 5},
                                                                "tink": {"on": False}}}), None),
        ("i_entry_not_object", '{"characters": {"genie": "on", "tron": {"on": false}}}', None),
        ("i_on_not_bool", '{"characters": {"genie": {"on": "no"}}}', None),
        ("i_on_true_dropped_on_false_kept", j({"characters": {"genie": {"on": True}, "tron": {"on": False}}}), None),
        ("i_chance_over", '{"characters": {"genie": {"chance": 101}}}', None),
        ("i_chance_bool", '{"characters": {"genie": {"chance": true}}}', None),
        ("i_chance_negative_string_and_ride_chance_text", '{"characters": {"genie": {"chance": -1, "ride_chance": "5"}}}', None),
        ("i_chances_at_default_dropped", j({"characters": {"genie": {"chance": 0.5, "ride_chance": 10},
                                                             "falcon": {"chance": 0, "ride_chance": 11.0}}}), None),
        ("i_chance_edge_values", j({"characters": {"genie": {"chance": 0.0, "ride_chance": 100},
                                                      "tron": {"chance": 25.0}}}), None),
        ("i_rides_not_list", '{"characters": {"genie": {"rides": "Test Track"}}}', None),
        ("i_rides_not_strings", '{"characters": {"genie": {"rides": [1]}}}', None),
        ("i_rides_too_many", j({"characters": {"genie": {"rides": MANY_RIDES}}}), None),
        ("i_rides_name_too_long", j({"characters": {"genie": {"rides": ["x" * 121]}}}), None),
        ("i_rides_sorted_deduped", j({"characters": {"tron": {"rides": [" b", "A", "b ", "", "a"]}}}), None),
        ("i_rides_none_for_non_visitor_dropped", j({"characters": {"genie": {"rides": []}}}), None),
        ("i_rides_none_for_visitor_kept", j({"characters": {"falcon": {"rides": []}}}), None),
        ("i_rides_defaults_by_name_dropped", j({"characters": {"falcon": {"rides": DEFAULTS}}}), RIDES),
        ("i_rides_defaults_by_pieces_dropped", j({"characters": {"falcon": {"rides": ["rise of the resistance",
                                                                                       "Smugglers Run"]}}}), None),
        ("i_rides_other_kept", j({"characters": {"falcon": {"rides": ["Space Mountain"]}}}), RIDES),
        ("i_total_over_100", '{"characters": {"genie": {"chance": 60}, "tron": {"chance": 50}}}', None),
        ("i_many_problems_in_order", j({"enabled": "x", "characters": {
            "genie": {"on": 1, "chance": 200, "ride_chance": "x", "rides": "x"}, "tron": 5,
            "mike": {"rides": MANY_RIDES, "chance": 70}, "olaf": {"chance": 70}, "gone": {}}}), None),
    ]


def run_all():
    results = {}
    for case_id, config, posted, names in form_cases():
        before = copy.deepcopy(config)
        new, problems = apply_form(config, posted, names)
        assert config == before, f"{case_id}: apply_form changed its input"
        results[case_id] = {"config": new, "problems": problems}
    for case_id, data, posted, rides in surprise_cases():
        before = copy.deepcopy(data)
        new, problems = apply_surprises(data, posted, rides)
        assert data == before, f"{case_id}: apply_surprises changed its input"
        results[case_id] = {"data": new, "problems": problems}
    for case_id, text, rides in import_cases():
        data, problems, skipped = import_surprises(text, rides)
        results[case_id] = {"data": data, "problems": problems, "skipped": skipped}
    return results


def stored():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def test_regenerate_fixture_when_asked():
    if os.environ.get("PIN_REGEN") != "1":
        pytest.skip("set PIN_REGEN=1 to rewrite the fixture")
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    with open(FIXTURE, "w", encoding="utf-8") as f:
        json.dump(run_all(), f, indent=1, ensure_ascii=False)
        f.write("\n")


ALL_IDS = ([c[0] for c in form_cases()] + [c[0] for c in surprise_cases()] + [c[0] for c in import_cases()])


def test_every_case_has_a_stored_result_and_none_is_left_over():
    assert sorted(stored()) == sorted(ALL_IDS)


@pytest.mark.parametrize("case_id", ALL_IDS)
def test_result_is_exactly_the_stored_one(case_id):
    actual = _results()[case_id]
    expected = stored()[case_id]
    # dumps, not ==: key order is part of what config.json looks like on disk
    assert _same_on_every_python(json.dumps(actual, ensure_ascii=False)) == \
        _same_on_every_python(json.dumps(expected, ensure_ascii=False))


_CHOICE = re.compile(r"invalid choice: [^(]*\(choose from [^)]*\)")


def _same_on_every_python(text):
    """argparse's "invalid choice" message quotes the value and the choices from Python 3.12
    ('-1' ... '0', '1') but not on 3.11 (-1 ... 0, 1); the panel problems pass it through, so the
    quotes aren't ours to pin."""
    return _CHOICE.sub(lambda m: m.group(0).replace("'", ""), text)


_CACHE = {}


def _results():
    if not _CACHE:
        _CACHE.update(run_all())
    return _CACHE
