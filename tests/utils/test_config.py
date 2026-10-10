import json

import pytest

from utils.config import (debug_enabled, has_api_key, load_config, weather_api_key, websocket_protocol,
                          websocket_settings)


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
