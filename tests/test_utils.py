import datetime
from utils.utils import center_text_position, split_string, deep_update, get_eastern


def test_center_text_position():
    assert center_text_position("Hello", 64, 6) == 49


def test_split_string():
    assert split_string("abcdefg", 3) == ["abc", "def", "g"]


def test_deep_update():
    source = {"a": 1, "b": {"c": 2, "d": 3}}
    overrides = {"b": {"c": 20}, "e": 5}
    expected = {"a": 1, "b": {"c": 20, "d": 3}, "e": 5}
    assert deep_update(source, overrides) == expected


def test_get_eastern():
    timestamp = "2025-05-10T20:11:00Z"
    assert get_eastern(timestamp) == "2025-05-10 04:11 PM"
