import json
import urllib.error

import pytest

import settings_page.park_names as park_names
from settings_page.park_names import MAX_AGE_S, RETRY_S, ParkNames

DESTINATIONS = [{"id": "cp", "name": "Cedar Point", "parks": [{"id": "1", "name": "Cedar Point"}]}]


class Clock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


class Fetch:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def __call__(self):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def run_now(monkeypatch):
    """Background fetches run at once, in the test's thread."""
    class Thread:
        def __init__(self, target, **_):
            self.target = target

        def start(self):
            self.target()
    monkeypatch.setattr(park_names.threading, "Thread", Thread)


def saved(path, fetched, parks):
    path.write_text(json.dumps({"fetched": fetched, "parks": parks}))


def test_a_fresh_list_on_disk_is_used_without_fetching(tmp_path, run_now):
    clock, fetch = Clock(), Fetch()
    saved(tmp_path / "names.json", clock.now - MAX_AGE_S + 60, [["EPCOT", "Walt Disney World® Resort"]])
    names = ParkNames(str(tmp_path / "names.json"), fetch, clock)
    assert names.names() == [("EPCOT", "Walt Disney World® Resort")] and fetch.calls == 0


def test_a_day_old_list_is_fetched_again_and_saved(tmp_path, run_now):
    clock, fetch = Clock(), Fetch(DESTINATIONS)
    path = tmp_path / "names.json"
    saved(path, clock.now - MAX_AGE_S, [["EPCOT", "Walt Disney World® Resort"]])
    assert ParkNames(str(path), fetch, clock).names() == [("Cedar Point", "Cedar Point")]
    assert json.loads(path.read_text()) == {"fetched": clock.now, "parks": [["Cedar Point", "Cedar Point"]]}


def test_a_failed_fetch_keeps_the_old_list_and_waits_before_trying_again(tmp_path, run_now, monkeypatch):
    warnings = []
    monkeypatch.setattr(park_names.debug, "warning", warnings.append)
    clock = Clock()
    fetch = Fetch(urllib.error.URLError("no internet"), ValueError("bad JSON"), [], DESTINATIONS)
    path = tmp_path / "names.json"
    saved(path, clock.now - 2 * MAX_AGE_S, [["EPCOT", "Walt Disney World® Resort"]])
    names = ParkNames(str(path), fetch, clock)
    assert names.names() == [("EPCOT", "Walt Disney World® Resort")]
    assert "keeping the last one" in warnings[-1]
    names.names()
    assert fetch.calls == 1, "not again until RETRY_S"
    for _ in range(3):  # bad JSON, then an empty list (kept out too), then a good one
        clock.now += RETRY_S
        names.names()
    assert fetch.calls == 4 and names.names() == [("Cedar Point", "Cedar Point")]


def test_with_no_file_and_no_internet_there_are_no_names(tmp_path, run_now, monkeypatch):
    warnings = []
    monkeypatch.setattr(park_names.debug, "warning", warnings.append)
    names = ParkNames(str(tmp_path / "names.json"), Fetch(OSError("unreachable")), Clock())
    assert names.names() == [] and "not checked" in warnings[-1]


@pytest.mark.parametrize("text", ["not json", "[]", '{"fetched": "soon", "parks": []}', '{"parks": [["a"]]}'])
def test_a_broken_file_is_ignored(tmp_path, monkeypatch, text):
    warnings = []
    monkeypatch.setattr(park_names.debug, "warning", warnings.append)
    (tmp_path / "names.json").write_text(text)
    names = ParkNames(str(tmp_path / "names.json"), Fetch(), Clock())
    assert (names.fetched, names.parks) == (None, []) and warnings


def test_a_list_that_cant_be_saved_is_still_used(tmp_path, run_now, monkeypatch):
    warnings = []
    monkeypatch.setattr(park_names.debug, "warning", warnings.append)
    names = ParkNames(str(tmp_path / "missing-folder" / "names.json"), Fetch(DESTINATIONS), Clock())
    assert names.names() == [("Cedar Point", "Cedar Point")] and "can't save" in warnings[-1]


def test_only_one_fetch_at_a_time(tmp_path, monkeypatch):
    started = []
    monkeypatch.setattr(park_names.threading, "Thread",
                        lambda target, **_: type("T", (), {"start": lambda self: started.append(target)})())
    names = ParkNames(str(tmp_path / "names.json"), Fetch(), Clock())
    assert names.refresh_if_due() and not names.refresh_if_due()
    assert len(started) == 1


def test_fetch_destinations_reads_the_list_and_refuses_a_reply_without_one(monkeypatch):
    class Reply:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, *_):
            return self.body

    requests = []

    def urlopen(request, timeout, context):
        requests.append((request.full_url, timeout))
        return Reply(next(bodies))
    bodies = iter([json.dumps({"destinations": DESTINATIONS}).encode(), b'{"error": "nope"}'])
    monkeypatch.setattr(park_names.urllib.request, "urlopen", urlopen)
    assert park_names.fetch_destinations() == DESTINATIONS
    assert requests == [("https://api.themeparks.wiki/v1/destinations", park_names.TIMEOUT_S)]
    with pytest.raises(ValueError):
        park_names.fetch_destinations()
