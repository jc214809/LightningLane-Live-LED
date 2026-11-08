import json

import pytest

from datetime import time

from utils.config import (ShowSettings, forced_show_name, SoundSettings, show_settings, debug_enabled, has_api_key, load_config, pushover_keys, sound_settings,
                          weather_api_key, websocket_protocol, websocket_settings)


def test_load_config(tmp_path):
    config_data = {"debug": True, "trip_countdown": {"trip_date": "2023-10-01", "enabled": True}}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config_data))
    assert load_config(str(path)) == config_data


def test_load_config_reads_config_json_by_default():
    # tests/stubs/conftest.py serves its dummy config for any "config.json".
    assert load_config()["debug"] is True


def test_load_config_nonexistent(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nonexistent_config.json"))


@pytest.mark.parametrize("config, expected", [
    ({"debug": True}, True),
    ({"debug": False}, False),
    ({}, False),  # used to be a KeyError at import, before the board even started
])
def test_debug_enabled(config, expected):
    assert debug_enabled(config) is expected


@pytest.mark.parametrize("config, expected", [
    ({"weather": {"apikey": "k"}}, "k"),
    ({"weather": {}}, None),
    ({}, None),
    ({"weather": "k"}, None),
])
def test_weather_api_key(config, expected):
    assert weather_api_key(config) == expected


@pytest.mark.parametrize("api_key", [None, "", "   ", "<THEMEPARKS_API_KEY>", 123])
def test_has_api_key_is_false_without_a_real_key(api_key):
    # The server closes keyless connections (3000 "Authentication timeout"), so these poll REST instead.
    assert not has_api_key(api_key)


@pytest.mark.parametrize("section, expected", [
    ({"user_key": " u-1 ", "app_token": "t-2"}, ("u-1", "t-2")),
    ({"user_key": "u-1", "app_token": "t-2", "enabled": True}, ("u-1", "t-2")),
    ({"user_key": "u-1", "app_token": "t-2", "enabled": False}, None),
    ({"user_key": "u-1", "app_token": "t-2", "enabled": "yes"}, None),
    ({"user_key": "u-1"}, None),
    ({"user_key": "<PUSHOVER_USER_KEY>", "app_token": "t-2"}, None),
    ("u-1", None),
    (None, None),
])
def test_pushover_keys_need_both_real_keys_and_not_turned_off(section, expected):
    assert pushover_keys({} if section is None else {"pushover": section}) == expected


def test_has_api_key_is_true_for_a_real_key():
    assert has_api_key("real-key")


@pytest.mark.parametrize("config, expected", [
    ({"websocket": {"enabled": True, "api_key": "real-key"}}, (True, "real-key")),
    ({"websocket": {"api_key": "real-key"}}, (True, "real-key")),  # enabled defaults to true
    ({"websocket": {"enabled": False, "api_key": "real-key"}}, (False, "real-key")),
    ({"websocket": {"enabled": True, "api_key": "<THEMEPARKS_API_KEY_HERE>"}}, (False, "<THEMEPARKS_API_KEY_HERE>")),
    ({"websocket": {"enabled": True}}, (False, None)),
    ({"websocket": {"enabled": "false", "api_key": "real-key"}}, (False, "real-key")),  # not a bool: off
    ({"websocket": "real-key"}, (False, None)),
    # Boards' configs from before the section keep working off the top-level key.
    ({"themeparks_api_key": "real-key"}, (True, "real-key")),
    ({"themeparks_api_key": "<KEY>", "websocket_only": True}, (False, "<KEY>")),
    ({}, (False, None)),
    # The section wins over a leftover top-level key.
    ({"themeparks_api_key": "old-key", "websocket": {"enabled": False, "api_key": "new-key"}}, (False, "new-key")),
])
def test_websocket_settings(config, expected):
    assert websocket_settings(config) == expected


@pytest.mark.parametrize("config, expected", [
    ({}, "legacy"),
    ({"websocket": {"api_key": "k"}}, "legacy"),
    ({"websocket": {"protocol": "preview"}}, "preview"),
    ({"websocket": {"protocol": "legacy"}}, "legacy"),
    ({"websocket": {"protocol": "Preview"}}, "legacy"),  # unknown values fall back, with a warning
    ({"websocket": "k"}, "legacy"),
])
def test_websocket_protocol(config, expected):
    assert websocket_protocol(config) == expected


@pytest.mark.parametrize("config, expected", [
    ({}, SoundSettings(False, None, None)),  # no section: a board without a speaker stays silent
    ({"sound": {}}, SoundSettings(True, None, None)),  # enabled defaults to true, like websocket
    ({"sound": {"enabled": False}}, SoundSettings(False, None, None)),
    ({"sound": {"enabled": True, "device": "plughw:1,0"}}, SoundSettings(True, "plughw:1,0", None)),
    ({"sound": {"quiet_hours": {"start": "22:00", "end": "08:00"}}},
     SoundSettings(True, None, (time(22, 0), time(8, 0)))),
    ({"sound": {"device": None, "quiet_hours": None}}, SoundSettings(True, None, None)),
])
def test_sound_settings(config, expected):
    assert sound_settings(config) == expected


@pytest.mark.parametrize("section", [
    "on", {"enabled": "yes"},
    # A broken quiet_hours turns sound off rather than risk playing in the night.
    {"quiet_hours": {"start": "22:00"}}, {"quiet_hours": {"start": "10pm", "end": "8am"}},
    {"quiet_hours": "22:00-08:00"}, {"quiet_hours": {"start": 22, "end": 8}},
])
def test_bad_sound_settings_turn_sound_off(section):
    assert sound_settings({"sound": section}).enabled is False


@pytest.mark.parametrize("device", ["", "  ", 1])
def test_a_bad_sound_device_falls_back_to_the_default(device):
    assert sound_settings({"sound": {"device": device}}) == SoundSettings(True, None, None)


HEA = "Happily Ever After"


@pytest.mark.parametrize("config, expected", [
    ({}, {}),
    ({"shows": []}, {}),
    ({"shows": [{"name": HEA}]}, {HEA: ShowSettings(True, "default")}),
    ({"shows": [{"name": HEA, "enabled": False, "version": "v2"}, {"name": "Other", "version": "v1"}]},
     {HEA: ShowSettings(False, "v2"), "Other": ShowSettings(True, "v1")}),
    # bad fields take their defaults; a show without a name is skipped
    ({"shows": [{"name": HEA, "enabled": "yes", "version": "v3"}]}, {HEA: ShowSettings()}),
    ({"shows": [{"name": HEA, "version": "full"}]}, {HEA: ShowSettings()}),
    ({"shows": [{"name": HEA, "force": True}]}, {HEA: ShowSettings(True, "default", True)}),
    ({"shows": [{"name": HEA, "force": "yes"}]}, {HEA: ShowSettings()}),
    ({"shows": [{"name": ""}, {"enabled": False}, "Happily Ever After", 5]}, {}),
    ({"shows": {HEA: "v2"}}, {}),
    ({"shows": None}, {}),
])
def test_show_settings(config, expected, monkeypatch):
    monkeypatch.setattr("utils.config.debug.warning", lambda message: None)
    assert show_settings(config) == expected


@pytest.mark.parametrize("config, expected", [
    ({}, None),
    ({"shows": [{"name": HEA}]}, None),
    ({"shows": [{"name": "Other"}, {"name": HEA, "force": True}]}, HEA),
    ({"shows": [{"name": "Other", "force": True}, {"name": HEA, "force": True}]}, "Other"),  # the first, with a warning
    ({"force_show": HEA}, HEA),  # the old top-level key still works, with a warning
    ({"force_show": ""}, None),
    ({"force_show": HEA, "shows": [{"name": "Other", "force": True}]}, "Other"),  # the new place wins
])
def test_forced_show_name(config, expected, monkeypatch):
    warnings = []
    monkeypatch.setattr("utils.config.debug.warning", warnings.append)
    assert forced_show_name(config) == expected
    assert bool(warnings) == (config.get("force_show") == HEA and expected == HEA or
                              len([s for s in config.get("shows", []) if s.get("force")]) > 1)


# ---- brightness_schedule ----

def test_brightness_schedule_is_read_as_peloton_leds():
    from datetime import time
    from utils.config import BrightnessSchedule, brightness_schedule
    config = {"brightness_schedule": {"day": 80, "night": 15, "day_start": "07:00", "night_start": "22:00"}}
    assert brightness_schedule(config) == BrightnessSchedule(80, 15, time(7), time(22))
    assert brightness_schedule({}) is None and brightness_schedule({"brightness_schedule": None}) is None


@pytest.mark.parametrize("section, problem", [
    ({"day": 80}, "needs day, night, day_start and night_start"),
    ("bright", "needs day, night, day_start and night_start"),
    ({"day": 0, "night": 15, "day_start": "07:00", "night_start": "22:00"}, '"day" should be 1 to 100'),
    ({"day": 80, "night": True, "day_start": "07:00", "night_start": "22:00"}, '"night" should be 1 to 100'),
    ({"day": 80, "night": 15, "day_start": "7am", "night_start": "22:00"}, '"day_start" should be a time'),
])
def test_a_bad_brightness_schedule_is_warned_about_and_ignored(monkeypatch, section, problem):
    import utils.config as config_module
    warnings = []
    monkeypatch.setattr(config_module.debug, "warning", warnings.append)
    assert config_module.brightness_schedule({"brightness_schedule": section}) is None
    assert len(warnings) == 1 and problem in warnings[0]


@pytest.mark.parametrize("volume, expected", [(None, 80), (0, 0), (65, 65), (100, 100)])
def test_sound_volume_defaults_to_80(volume, expected):
    assert sound_settings({"sound": {"volume": volume}}).volume == expected


@pytest.mark.parametrize("volume", [101, -1, "80", 80.5, True])
def test_a_bad_sound_volume_is_80_with_a_warning(monkeypatch, volume):
    from utils import config as config_module
    warnings = []
    monkeypatch.setattr(config_module.debug, "warning", warnings.append)
    assert sound_settings({"sound": {"volume": volume}}).volume == 80
    assert "sound.volume" in warnings[0]


# ---- surprises ----

def test_surprises_are_all_on_unless_the_file_says_otherwise():
    from utils.config import SurpriseSettings, surprise_settings
    assert surprise_settings({}) == SurpriseSettings()
    assert SurpriseSettings().allows("tron") and SurpriseSettings().allows("wipe")


def test_a_character_turned_off_takes_all_its_looks_with_it():
    from utils.config import surprise_settings
    settings = surprise_settings({"characters": {n: {"on": False} for n in ("tron", "saber_duel", "walle_side")}})
    assert not settings.allows("tron")
    assert not settings.allows("saber_duel_yoda") and not settings.allows("walle")
    assert settings.allows("genie") and settings.allows("wipe")


def test_the_master_switch_off_allows_only_the_wipe():
    from utils.config import surprise_settings
    settings = surprise_settings({"enabled": False})
    assert settings.allows("wipe") and not settings.allows("genie") and not settings.allows("tink")


def test_chances_are_read_as_percents_into_fractions():
    from utils.config import surprise_settings
    settings = surprise_settings({"characters": {"genie": {"chance": 1.5}, "tron": {"chance": 0},
                                                 "falcon": {"ride_chance": 25}}})
    assert settings.chance("genie", 0.005) == pytest.approx(0.015) and settings.chance("tron", 0.008) == 0
    assert settings.chance("baymax", 0.007) == 0.007, "not set: the default"
    assert settings.ride_chance("falcon", 0.10) == 0.25 and settings.ride_chance("rex", 0.10) == 0.10


@pytest.mark.parametrize("data, field", [
    ({"enabled": "no"}, "enabled"), ({"characters": ["tron"]}, "characters"), ({"characters": {"tron": "off"}}, "tron"),
    ({"characters": {"tron": {"on": "no"}}}, "on"), ({"characters": {"genie": {"chance": 120}}}, "chance"),
    ({"characters": {"genie": {"chance": -1}}}, "chance"), ({"characters": {"genie": {"chance": "5"}}}, "chance"),
    ({"characters": {"genie": {"chance": True}}}, "chance"), ({"characters": {"falcon": {"ride_chance": None}}}, "ride_chance"),
])
def test_bad_surprise_settings_warn_and_fall_back_to_the_defaults(data, field, monkeypatch):
    from utils.config import SurpriseSettings, surprise_settings
    warnings = []
    monkeypatch.setattr("utils.config.debug.warning", warnings.append)
    assert surprise_settings(data) == SurpriseSettings()
    assert len(warnings) == 1 and field in warnings[0]


def test_surprises_json_is_read_whole_and_a_bad_or_missing_file_means_defaults(tmp_path, monkeypatch):
    from utils.config import load_surprises
    warnings = []
    monkeypatch.setattr("utils.config.debug.warning", warnings.append)
    path = tmp_path / "surprises.json"
    assert load_surprises(str(path)) == {} and warnings == [], "missing is fine: nothing was ever changed"
    path.write_text(json.dumps({"enabled": False}))
    assert load_surprises(str(path)) == {"enabled": False}
    for bad in ("{not json", "[1]", "3"):
        path.write_text(bad)
        assert load_surprises(str(path)) == {}
    assert len(warnings) == 3


def test_chosen_rides_are_read_lowercased_and_trimmed_and_an_empty_list_means_no_rides():
    from utils.config import surprise_settings
    settings = surprise_settings({"characters": {"genie": {"rides": ["Space Mountain", " Test Track "]},
                                                 "tron": {"rides": []}, "falcon": {"rides": ["", " "]}}})
    assert settings.rides == {"genie": ("space mountain", "test track"), "tron": (), "falcon": ()}


def test_a_character_with_settings_but_no_rides_key_keeps_its_default_rides():
    from utils.config import surprise_settings
    assert surprise_settings({"characters": {"falcon": {"chance": 5, "on": False}}}).rides == {}


@pytest.mark.parametrize("rides", ["Space Mountain", [1], ["Space Mountain", None]])
def test_bad_rides_warn_and_keep_the_usual_ones(rides, monkeypatch):
    from utils.config import surprise_settings
    warnings = []
    monkeypatch.setattr("utils.config.debug.warning", warnings.append)
    assert surprise_settings({"characters": {"genie": {"rides": rides}}}).rides == {}
    assert len(warnings) == 1 and "rides" in warnings[0]


# ---- save_config: who owns a file it creates ----

def test_a_new_file_takes_the_mode_and_owner_of_the_file_it_is_beside(tmp_path, monkeypatch):
    import os
    from utils.config import save_config
    config = tmp_path / "config.json"
    config.write_text("{}")
    os.chmod(config, 0o640)
    owned = []
    monkeypatch.setattr("utils.config.os.chown", lambda path, uid, gid: owned.append((os.path.basename(path), uid, gid)))
    target = tmp_path / "surprises.json"
    save_config({"enabled": True}, str(target), like=str(config))
    assert oct(os.stat(target).st_mode & 0o777) == "0o640", "config.json's, not the default 600"
    assert owned == [("surprises.json.new", os.stat(config).st_uid, os.stat(config).st_gid)]
    assert not (tmp_path / "surprises.json.bak").exists(), "nothing to back up the first time"


def test_a_file_that_exists_keeps_its_own_owner_and_mode_whatever_it_is_beside(tmp_path, monkeypatch):
    import os
    from utils.config import save_config
    config, target = tmp_path / "config.json", tmp_path / "surprises.json"
    config.write_text("{}")
    target.write_text('{"old": 1}')
    os.chmod(config, 0o640)
    os.chmod(target, 0o600)
    monkeypatch.setattr("utils.config.os.chown", lambda *args: None)
    save_config({"new": 1}, str(target), like=str(config))
    assert oct(os.stat(target).st_mode & 0o777) == "0o600"
    assert json.loads((tmp_path / "surprises.json.bak").read_text()) == {"old": 1}


def test_with_nothing_to_copy_a_new_file_is_600_and_nothing_is_chowned(tmp_path, monkeypatch):
    import os
    from utils.config import save_config
    owned = []
    monkeypatch.setattr("utils.config.os.chown", lambda *args: owned.append(args))
    save_config({"a": 1}, str(tmp_path / "one.json"))
    save_config({"a": 1}, str(tmp_path / "two.json"), like=str(tmp_path / "missing.json"))
    assert oct(os.stat(tmp_path / "one.json").st_mode & 0o777) == oct(os.stat(tmp_path / "two.json").st_mode & 0o777) == "0o600"
    assert owned == []
