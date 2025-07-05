import builtins
import types

import pytest

from utils.utils import center_text_position, split_string, deep_update, get_eastern


def test_center_text_position():
    assert center_text_position("abc", 50, 5) == 43


def test_split_string():
    assert split_string("abcdef", 2) == ["ab", "cd", "ef"]


def test_deep_update():
    source = {"a": {"b": 1}}
    overrides = {"a": {"c": 2}, "d": 3}
    result = deep_update(source, overrides)
    assert result == {"a": {"b": 1, "c": 2}, "d": 3}
    assert source is result


def test_get_eastern():
    eastern_time = get_eastern("2024-01-01T12:00:00Z")
    assert eastern_time.endswith("07:00 AM")

    # During daylight saving time the offset should be UTC-4
    dst_time = get_eastern("2024-07-01T12:00:00Z")
    assert dst_time.endswith("08:00 AM")
