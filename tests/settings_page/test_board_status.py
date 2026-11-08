import json

import pytest

from settings_page import board_status
from settings_page.board_status import NONE, QUIET, QUIET_S, RUNNING, SHOW, BoardNow, ago, board_now

NOW = 1_800_000_000.0


def write(tmp_path, data):
    path = tmp_path / "lll-health"
    path.write_text(data if isinstance(data, str) else json.dumps(data))
    return str(path)


def test_a_fresh_heartbeat_is_running_with_its_age_and_version(tmp_path):
    path = write(tmp_path, {"at": NOW - 12, "pid": 1, "version": "2.1.5-beta"})
    assert board_now(path, NOW) == BoardNow(RUNNING, 12, "2.1.5-beta")


def test_a_show_playing_says_which(tmp_path):
    path = write(tmp_path, {"at": NOW - 3, "version": "2.1.5", "show": "Happily Ever After", "show_until": NOW + 60})
    assert board_now(path, NOW) == BoardNow(SHOW, 3, "2.1.5", "Happily Ever After")


def test_a_show_that_should_have_ended_is_not_playing(tmp_path):
    path = write(tmp_path, {"at": NOW - 3, "show": "Happily Ever After", "show_until": NOW - 1})
    assert board_now(path, NOW).state == RUNNING


def test_no_screen_for_longer_than_the_health_window_is_quiet(tmp_path):
    assert board_now(write(tmp_path, {"at": NOW - QUIET_S}), NOW).state == RUNNING
    assert board_now(write(tmp_path, {"at": NOW - QUIET_S - 1}), NOW).state == QUIET


@pytest.mark.parametrize("data", ["not json", "[]", '{"version": "2.1.5"}', '{"at": "soon"}'])
def test_a_missing_or_bad_heartbeat_is_none_and_never_raises(tmp_path, data):
    assert board_now(write(tmp_path, data), NOW) == BoardNow(NONE)
    assert board_now(str(tmp_path / "missing"), NOW) == BoardNow(NONE)


def test_a_version_that_isnt_text_is_left_out(tmp_path):
    assert board_now(write(tmp_path, {"at": NOW, "version": 2}), NOW).version is None


def test_a_clock_behind_the_heartbeat_is_zero_seconds_not_negative(tmp_path):
    assert board_now(write(tmp_path, {"at": NOW + 30}), NOW).age_s == 0


def test_board_now_uses_the_clock_when_not_given_one(tmp_path, monkeypatch):
    monkeypatch.setattr(board_status.time, "time", lambda: NOW)
    assert board_now(write(tmp_path, {"at": NOW - 5})).age_s == 5


@pytest.mark.parametrize("seconds, said", [(0, "0 seconds ago"), (1, "1 second ago"), (59, "59 seconds ago"),
                                           (60, "1 minute ago"), (150, "2 minutes ago"), (3600, "1 hour ago"),
                                           (2 * 86400 + 5, "2 days ago")])
def test_ago(seconds, said):
    assert ago(seconds) == said
