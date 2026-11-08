import json
import urllib.error

import pytest

import settings_page.ride_names as ride_names
from settings_page.park_names import MAX_AGE_S, RETRY_S
from settings_page.ride_names import FORMAT, RideNames, fetch_rides

PARKS = ["Magic Kingdom"]
RIDES = {"Magic Kingdom": ["Space Mountain", "Test Track"]}


class Clock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


class Fetch:
    def __init__(self, *replies):
        self.replies, self.calls, self.keeps = list(replies), [], []

    def __call__(self, parks, keep=None):
        self.calls.append(parks)
        self.keeps.append(keep)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def run_now(monkeypatch):
    """Background fetches run at once, in the test's thread."""
    class Thread:
        def __init__(self, target, args=(), **_):
            self.target, self.args = target, args

        def start(self):
            self.target(*self.args)
    monkeypatch.setattr(ride_names.threading, "Thread", Thread)


def saved(path, fetched, parks=PARKS, rides=RIDES):
    path.write_text(json.dumps({"format": FORMAT, "fetched": fetched, "parks": parks, "rides": rides}))


def test_a_fresh_list_for_the_same_parks_is_used_without_fetching(tmp_path, run_now):
    clock, fetch = Clock(), Fetch()
    saved(tmp_path / "rides.json", clock.now - MAX_AGE_S + 60)
    assert RideNames(str(tmp_path / "rides.json"), fetch, clock).names(PARKS) == RIDES and fetch.calls == []


def test_a_day_old_list_is_fetched_again_and_saved(tmp_path, run_now):
    clock, fetch = Clock(), Fetch({"Magic Kingdom": ["Haunted Mansion"]})
    path = tmp_path / "rides.json"
    saved(path, clock.now - MAX_AGE_S)
    assert RideNames(str(path), fetch, clock).names(PARKS) == {"Magic Kingdom": ["Haunted Mansion"]}
    assert json.loads(path.read_text()) == {"format": FORMAT, "fetched": clock.now, "parks": PARKS,
                                            "rides": {"Magic Kingdom": ["Haunted Mansion"]}}


def test_a_change_of_parks_fetches_at_once_even_if_the_list_is_fresh(tmp_path, run_now):
    clock, fetch = Clock(), Fetch({"EPCOT": ["Test Track"]})
    saved(tmp_path / "rides.json", clock.now)
    assert RideNames(str(tmp_path / "rides.json"), fetch, clock).names(["EPCOT"]) == {"EPCOT": ["Test Track"]}
    assert fetch.calls == [["EPCOT"]]


def test_a_failed_fetch_keeps_the_old_list_and_waits_before_trying_again(tmp_path, run_now, monkeypatch):
    warnings = []
    monkeypatch.setattr(ride_names.debug, "warning", warnings.append)
    clock = Clock()
    fetch = Fetch(urllib.error.URLError("no internet"), ValueError("bad JSON"), {"Magic Kingdom": []}, RIDES)
    path = tmp_path / "rides.json"
    saved(path, clock.now - 2 * MAX_AGE_S, rides={"Magic Kingdom": ["Old Ride"]})
    names = RideNames(str(path), fetch, clock)
    assert names.names(PARKS) == {"Magic Kingdom": ["Old Ride"]} and "keeping the last one" in warnings[-1]
    names.names(PARKS)
    assert len(fetch.calls) == 1, "not again until RETRY_S"
    for _ in range(3):  # bad JSON, then a reply with no rides (kept out too), then a good one
        clock.now += RETRY_S
        names.names(PARKS)
    assert len(fetch.calls) == 4 and names.names(PARKS) == RIDES


def test_no_parks_means_no_fetch_and_no_list(tmp_path, run_now):
    fetch = Fetch()
    assert RideNames(str(tmp_path / "rides.json"), fetch, Clock()).names([]) == {} and fetch.calls == []


@pytest.mark.parametrize("content", ["{not json", f'{{"format": {FORMAT}, "fetched": 1}}',
                                     f'{{"format": {FORMAT}, "fetched": 1, "parks": [], "rides": [1]}}', "[]"])
def test_a_bad_file_is_ignored_with_a_warning(tmp_path, monkeypatch, content):
    warnings = []
    monkeypatch.setattr(ride_names.debug, "warning", warnings.append)
    (tmp_path / "rides.json").write_text(content)
    assert RideNames(str(tmp_path / "rides.json"), Fetch(), Clock()).rides == {} and warnings


def test_a_file_kept_by_an_older_version_is_fetched_again_rather_than_trusted(tmp_path, run_now):
    clock, fetch = Clock(), Fetch(RIDES)
    path = tmp_path / "rides.json"
    path.write_text(json.dumps({"fetched": clock.now, "parks": PARKS, "rides": {"Magic Kingdom": ["A Parade"]}}))
    names = RideNames(str(path), fetch, clock)
    assert names.rides == {}, "its list had shows and parades in it"
    assert names.names(PARKS) == RIDES and len(fetch.calls) == 1


def test_a_refresh_hands_the_last_list_to_the_fetch_so_a_closed_ride_does_not_fall_off(tmp_path, run_now):
    clock, fetch = Clock(), Fetch(RIDES)
    saved(tmp_path / "rides.json", clock.now - MAX_AGE_S, rides={"Magic Kingdom": ["Space Mountain"]})
    RideNames(str(tmp_path / "rides.json"), fetch, clock).names(PARKS)
    assert fetch.keeps == [{"Magic Kingdom": ["Space Mountain"]}]


DESTINATIONS = [{"id": "e957da41-3552-4cf6-b636-5babc5cbc4e5", "name": "WDW", "parks": [
    {"id": "mk", "name": "Magic Kingdom Park"}, {"id": "ec", "name": "EPCOT"}]}]
CHILDREN = [
    {"id": "a1", "entityType": "ATTRACTION", "name": "Tron\u2122 Lightcycle Run"},
    {"id": "a2", "entityType": "ATTRACTION", "name": "Space Mountain"},
    {"id": "a3", "entityType": "ATTRACTION", "name": "Kali River Rapids"},  # closed: a queue, no wait
    {"id": "a4", "entityType": "ATTRACTION", "name": "Cinderella Castle"},  # an exhibit: no queue
    {"id": "a5", "entityType": "ATTRACTION", "name": "Rise of the Resistance"},  # boarding groups only
    {"id": "m1", "entityType": "SHOW", "name": "Meet Mickey at Town Square Theater"},  # a meet: a SHOW with a queue
    {"id": "s1", "entityType": "SHOW", "name": "Festival of Fantasy Parade"},  # no queue
    {"id": "r1", "entityType": "RESTAURANT", "name": "Be Our Guest"},
    {"id": "x1", "entityType": "ATTRACTION"}, "junk"]
LIVE = [
    {"id": "a1", "queue": {"STANDBY": {"waitTime": 40}}}, {"id": "a2", "queue": {"STANDBY": {"waitTime": None}}},
    {"id": "a3", "status": "CLOSED", "queue": {"STANDBY": {"waitTime": None}}}, {"id": "a4", "queue": {}},
    {"id": "a5", "queue": {"BOARDING_GROUP": {"currentGroupStart": 1}}}, {"id": "m1", "queue": {"STANDBY": {"waitTime": 5}}},
    {"id": "s1"}, {"id": "r1", "queue": {"STANDBY": {"waitTime": 10}}}, {"id": "x1", "queue": None}, "junk"]


@pytest.fixture
def api(monkeypatch):
    asked = []
    monkeypatch.setattr(ride_names, "fetch_destinations", lambda: DESTINATIONS)

    def get(url):
        asked.append(url)
        return {"children": CHILDREN} if url.endswith("/children") else {"liveData": LIVE}
    monkeypatch.setattr(ride_names, "_get_json", get)
    return asked


def test_the_rides_are_the_attractions_and_meets_with_a_wait_queue_named_as_the_app_names_them(api):
    assert fetch_rides(["Magic Kingdom"]) == {"Magic Kingdom": [
        "Kali River Rapids", "Meet Mickey at Town Square Theater", "Rise of the Resistance", "Space Mountain",
        "Tron Lightcycle Run"]}
    assert api == ["https://api.themeparks.wiki/v1/entity/mk/children", "https://api.themeparks.wiki/v1/entity/mk/live"], \
        "only the parks asked for"


def test_a_ride_with_a_queue_but_no_wait_right_now_stays_on_the_list(api):
    rides = fetch_rides(["Magic Kingdom"])["Magic Kingdom"]
    assert "Kali River Rapids" in rides and "Space Mountain" in rides, "closed, or no wait posted at the moment"
    assert "Cinderella Castle" not in rides and "Festival of Fantasy Parade" not in rides and "Be Our Guest" not in rides


def test_a_ride_seen_before_stays_while_it_is_still_there_but_not_once_it_is_gone(api):
    keep = {"Magic Kingdom": ["Cinderella Castle", "Space Mountain", "Retired Ride"]}
    rides = fetch_rides(["Magic Kingdom"], keep)["Magic Kingdom"]
    assert "Cinderella Castle" in rides, "it lost its queue, but it's still a child of the park"
    assert "Retired Ride" not in rides, "no longer in the park's children"


def test_a_park_whose_data_cannot_be_read_fails_the_whole_fetch(monkeypatch, api):
    monkeypatch.setattr(ride_names, "_get_json", lambda url: {"children": "none", "liveData": []})
    with pytest.raises(ValueError):
        fetch_rides(["Magic Kingdom"])
    monkeypatch.setattr(ride_names, "_get_json", lambda url: {"children": [], "liveData": "none"})
    with pytest.raises(ValueError):
        fetch_rides(["Magic Kingdom"])


def test_one_parks_outage_keeps_that_parks_last_list_and_the_others_are_fetched(monkeypatch, api):
    good = ride_names._get_json

    def get(url):
        if "/ec/" in url:
            raise urllib.error.URLError("down")
        return good(url)
    monkeypatch.setattr(ride_names, "_get_json", get)
    rides = fetch_rides(["Magic Kingdom", "EPCOT"], {"EPCOT": ["Test Track"]})
    assert rides["EPCOT"] == ["Test Track"], "its last list, not nothing"
    assert "Space Mountain" in rides["Magic Kingdom"]
    assert "EPCOT" not in fetch_rides(["Magic Kingdom", "EPCOT"]), "no last list: left out, and the others still show"


def test_every_park_down_is_a_failed_fetch(monkeypatch, api):
    def get(url):
        raise urllib.error.URLError("down")
    monkeypatch.setattr(ride_names, "_get_json", get)
    with pytest.raises(ValueError):
        fetch_rides(["Magic Kingdom"])
