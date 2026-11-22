import json
import os

import utils.heartbeat as heartbeat
from version import version


def test_a_beat_says_when_and_who(tmp_path):
    path = str(tmp_path / "health")
    assert heartbeat.beat(path=path, clock=lambda: 1000.0) is True
    with open(path) as f:
        found = json.load(f)
    assert found == {"at": 1000.0, "pid": os.getpid(), "version": version()}
    assert heartbeat.read(path) == found
    assert not [name for name in os.listdir(tmp_path) if name.endswith(".new")], "written through a temp file"


def test_it_writes_the_default_file(tmp_path):
    heartbeat.beat()  # the root conftest points HEARTBEAT_FILE into tmp_path
    assert heartbeat.read()["pid"] == os.getpid()


def test_a_show_is_playing_until_its_end_and_the_next_beat_clears_it(tmp_path):
    path = str(tmp_path / "health")
    heartbeat.beat(show="Happily Ever After", show_s=1080, path=path, clock=lambda: 1000.0)
    beat = heartbeat.read(path)
    assert heartbeat.show_playing(beat, 2079.0) == "Happily Ever After"
    assert heartbeat.show_playing(beat, 2080.0) is None, "an app that died mid-show doesn't block updates for ever"
    heartbeat.beat(path=path, clock=lambda: 2000.0)
    assert heartbeat.show_playing(heartbeat.read(path), 2001.0) is None


def test_a_beat_that_cant_be_written_warns_once_and_never_raises(tmp_path, monkeypatch):
    warnings = []
    monkeypatch.setattr(heartbeat.debug, "warning", warnings.append)
    path = str(tmp_path / "missing-folder" / "health")
    assert heartbeat.beat(path=path) is False
    assert heartbeat.beat(path=path) is False
    assert len(warnings) == 1 and path in warnings[0]


def test_reading_a_missing_or_bad_heartbeat_gives_none(tmp_path):
    path = tmp_path / "health"
    assert heartbeat.read(str(path)) is None
    for text in ("not json", "[]", '{"pid": 1}', '{"at": "soon"}'):
        path.write_text(text)
        assert heartbeat.read(str(path)) is None, text
    assert heartbeat.show_playing(None, 0) is None
    assert heartbeat.show_playing({"at": 1, "show": "X"}, 0) is None, "no end written: not playing"
