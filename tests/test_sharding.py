"""The root conftest's TEST_SHARD split, which CI uses to run the coverage tests as two jobs."""
import importlib.util
import os

import pytest

_spec = importlib.util.spec_from_file_location(
    "root_conftest", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conftest.py"))
root_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(root_conftest)


class Config:
    def __init__(self):
        self.deselected = []
        self.hook = self

    def pytest_deselected(self, items):
        self.deselected += items


def _shard(monkeypatch, value, n=7):
    monkeypatch.setenv("TEST_SHARD", value)
    items, config = list(range(n)), Config()
    root_conftest.pytest_collection_modifyitems(config, items)
    return items, config.deselected


def test_the_shards_take_turns_and_together_run_everything(monkeypatch):
    first, skipped = _shard(monkeypatch, "1/2")
    second, _ = _shard(monkeypatch, "2/2")
    assert first == [0, 2, 4, 6] and second == [1, 3, 5] and skipped == second


def test_without_a_shard_everything_runs(monkeypatch):
    monkeypatch.delenv("TEST_SHARD", raising=False)
    items, config = list(range(3)), Config()
    root_conftest.pytest_collection_modifyitems(config, items)
    assert items == [0, 1, 2] and config.deselected == []


@pytest.mark.parametrize("value", ["3/2", "0/2"])
def test_a_shard_out_of_range_is_a_usage_error(monkeypatch, value):
    with pytest.raises(pytest.UsageError):
        _shard(monkeypatch, value)
