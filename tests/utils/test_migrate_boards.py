"""The one-time move of each board's boards.json settings into its config.json. The file is
"board-config.json": tests/stubs/conftest.py fakes every "config.json" read."""
import json
import os

import pytest

from utils.migrate_boards import OLD_BOARDS, main, migrate


def test_a_board_gets_its_size_and_rotation_where_its_config_has_none():
    config = {"parks": ["EPCOT"], "matrix": {"led_rows": None, "led_brightness": 80}}
    new, moved = migrate(config, "PlutoPi.local")
    assert new == {"parks": ["EPCOT"], "matrix": {"led_rows": 32, "led_brightness": 80, "led_cols": 64,
                                                  "led_pixel_mapper": "Rotate:180"}}
    assert moved == ["led_rows", "led_cols", "led_pixel_mapper"]
    assert config["matrix"]["led_rows"] is None, "the config passed in is left as it was"


def test_settings_already_in_config_win_so_a_rerun_changes_nothing():
    config = {"matrix": {"led_rows": 32, "led_cols": 64}}
    new, moved = migrate(config, "Disneypi")
    assert new == config and moved == []
    once, _ = migrate({}, "TinyPi")
    assert migrate(once, "TinyPi") == (once, [])


def test_a_board_that_was_never_in_boards_json_is_left_alone():
    assert migrate({"matrix": {}}, "DonaldPi") == ({"matrix": {}}, [])


def test_only_whats_not_the_pi_models_moves():
    for name, settings in OLD_BOARDS.items():
        assert set(settings) <= {"led_rows", "led_cols", "led_pixel_mapper", "emulated"}, name


def test_main_saves_with_a_backup_and_says_what_moved(tmp_path, capsys):
    path = tmp_path / "board-config.json"
    path.write_text(json.dumps({"matrix": {"led_rows": None}}))
    os.chmod(path, 0o600)
    assert main([str(path)], "ZeroPi") == 0
    assert json.loads(path.read_text())["matrix"] == {"led_rows": 32, "led_cols": 64}
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"
    assert json.loads((tmp_path / "board-config.json.bak").read_text()) == {"matrix": {"led_rows": None}}
    assert f"Panel settings moved into {path}: led_rows=32, led_cols=64." in capsys.readouterr().out
    assert main([str(path)], "ZeroPi") == 0
    assert "nothing to move" in capsys.readouterr().out


@pytest.mark.parametrize("contents, code, says", [(None, 0, "No "), ("{not json", 1, "Can't read")])
def test_main_with_no_config_or_a_broken_one_writes_nothing(tmp_path, capsys, contents, code, says):
    path = tmp_path / "board-config.json"
    if contents is not None:
        path.write_text(contents)
    assert main([str(path)], "ZeroPi") == code
    assert says in capsys.readouterr().out
    assert not (tmp_path / "board-config.json.bak").exists()
