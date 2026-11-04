import json
import os

import pytest

from self_update import state as states
from self_update.state import Busy, State


def test_a_board_that_never_updated_is_idle(tmp_path):
    assert State(str(tmp_path / "lll-update")).load() == {"phase": "idle", "good": []}


@pytest.mark.parametrize("text", ["not json", "[]", '{"phase": "updated", "good": "abc"}'])
def test_a_bad_state_file_reads_as_fresh(tmp_path, text):
    (tmp_path / "state.json").write_text(text)
    found = State(str(tmp_path)).load()
    assert found["good"] == [] and found["phase"] in ("idle", "updated")


def test_a_phase_is_saved_whole(tmp_path):
    state = State(str(tmp_path / "lll-update"))
    record = state.set_phase(state.load(), states.READY, to={"sha": "abc"})
    assert json.loads((tmp_path / "lll-update" / "state.json").read_text()) == record
    assert state.load()["phase"] == "ready" and "ready" in states.UNFINISHED
    assert not list((tmp_path / "lll-update").glob("*.new"))


@pytest.mark.parametrize("text", [None, "not json", "[]"])
def test_no_outcome_or_a_bad_one_reads_as_none(tmp_path, text):
    if text is not None:
        (tmp_path / "outcome.json").write_text(text)
    assert State(str(tmp_path)).load_outcome() is None


def test_an_outcome_is_saved_whole_beside_the_state(tmp_path):
    state = State(str(tmp_path / "lll-update"))
    state.save_outcome({"command": "update", "result": "updated"})
    assert state.load_outcome() == {"command": "update", "result": "updated"}
    assert state.load() == {"phase": "idle", "good": []}, "state.json untouched"
    assert not list((tmp_path / "lll-update").glob("*.new"))


def test_good_commits_keep_the_newest_three_without_repeats():
    record = {"good": ["c", "b", "a"]}
    states.remember_good(record, "d")
    assert record["good"] == ["d", "c", "b"]
    states.remember_good(record, "b")
    assert record["good"] == ["b", "d", "c"]


def test_only_one_update_at_a_time(tmp_path):
    state = State(str(tmp_path))
    with state.lock():
        with pytest.raises(Busy):
            with State(str(tmp_path)).lock():
                pass
    with state.lock():  # released
        pass


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads everything")
def test_a_folder_only_root_can_open_is_unreadable_not_idle(tmp_path):
    state = State(str(tmp_path / "lll-update"))
    assert not state.unreadable(), "no folder yet: never updated"
    state.save({"phase": "updated"})
    assert not state.unreadable()
    os.chmod(state.folder, 0)
    try:
        assert state.unreadable()
    finally:
        os.chmod(state.folder, 0o700)
