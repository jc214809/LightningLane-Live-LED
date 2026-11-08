"""Every ride and meet with a wait time at the board's parks, for the Surprise characters page's ride pickers:
the attractions and shows (the feed types a meet-and-greet as a SHOW) whose live feed has a standby or boarding-group
queue, whether or not a wait is posted right now, since a ride that's closed has none but isn't gone. Parades,
fireworks and walk-through exhibits have no queue, so they aren't listed. One seen once stays listed while it's
still there. Fetched from ThemeParks.wiki (the destinations, then each park's children
and live data) at most once a day, or when the board's parks change, and kept in a file, so a phone on the setup
hotspot, with no internet, still gets the list. Fetches run in the background: a page never waits on the API.
Same shape as park_names.py.
"""
import json
import os
import ssl
import threading
import time
import urllib.request

import certifi

from parks.names import clean_ride_name, park_ids
from settings_page.park_names import MAX_AGE_S, RETRY_S, TIMEOUT_S, fetch_destinations
from utils import debug

CHILDREN_URL = "https://api.themeparks.wiki/v1/entity/{}/children"
LIVE_URL = "https://api.themeparks.wiki/v1/entity/{}/live"
# What the app draws a ride screen for; only those with a wait queue are listed.
KINDS = ("ATTRACTION", "SHOW")
# The queues that carry a wait (api.disney_api.parse_queue_wait): an attraction without either never gets a ride screen.
WAIT_QUEUES = ("STANDBY", "BOARDING_GROUP")
# Bumped when what's kept changes, so an older ride_names.json is fetched again instead of trusted.
FORMAT = 2


def _get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "LightningLane-Live-LED settings page"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S,
                                context=ssl.create_default_context(cafile=certifi.where())) as response:
        return json.load(response)


def _has_wait_queue(entry):
    queue = entry.get("queue") if isinstance(entry, dict) else None
    return isinstance(queue, dict) and any(kind in queue for kind in WAIT_QUEUES)


def fetch_rides(park_names, keep=None):
    """{park: [ride names]} for these configured parks: each attraction or show (a meet is one) whose live entry has a
    wait queue, named as the app names it, plus any in keep ({park: [names]}, the last list) that is still there. Raises on a network
    error, a bad status or bad JSON; a park whose data can't be read fails the whole fetch."""
    rides = {}
    for park, park_id in park_ids(fetch_destinations(), park_names).items():
        children = _get_json(CHILDREN_URL.format(park_id)).get("children")
        live = _get_json(LIVE_URL.format(park_id)).get("liveData")
        if not isinstance(children, list) or not isinstance(live, list):
            raise ValueError(f"no children or live data for {park}")
        waiting = {entry.get("id") for entry in live if _has_wait_queue(entry)}
        listed = {c.get("id"): clean_ride_name(c["name"]).strip() for c in children
                       if isinstance(c, dict) and c.get("entityType") in KINDS and isinstance(c.get("name"), str)}
        names = {name for ride_id, name in listed.items() if ride_id in waiting}
        names |= set((keep or {}).get(park, [])) & set(listed.values())
        rides[park] = sorted((n for n in names if n), key=str.lower)
    return rides


class RideNames:
    """The cached rides. names(parks) is {park: [rides]} for those parks, or {} before the first fetch that
    worked (the page then says the list isn't loaded yet)."""

    def __init__(self, path, fetch=fetch_rides, clock=time.time):
        self.path, self.fetch, self.clock = path, fetch, clock
        self.lock = threading.Lock()
        self.fetching = False
        self.last_try = None
        self.fetched, self.parks, self.rides = self._read()

    def _read(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                saved = json.load(f)
            if saved.get("format") != FORMAT:  # kept by an older version, which listed shows too: fetch it again
                return None, [], {}
            rides = {str(park): [str(r) for r in names] for park, names in saved["rides"].items()}
            return float(saved["fetched"]), [str(p) for p in saved["parks"]], rides
        except FileNotFoundError:
            return None, [], {}
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
            debug.warning(f"Settings page: ignoring the ride list in {self.path}: {e}")
            return None, [], {}

    def names(self, parks):
        """The rides at these parks now; starts a fetch in the background when they're a day old, missing, or
        for other parks."""
        self.refresh_if_due(parks)
        with self.lock:
            return {park: list(names) for park, names in self.rides.items()}

    def refresh_if_due(self, parks):
        parks = list(parks)
        now = self.clock()
        with self.lock:
            fresh = self.fetched is not None and now - self.fetched < MAX_AGE_S and self.parks == parks
            tried = self.last_try is not None and now - self.last_try < RETRY_S
            if fresh or tried or self.fetching or not parks:
                return False
            self.fetching, self.last_try = True, now
        threading.Thread(target=self.refresh, args=(parks,), name="ride-names", daemon=True).start()
        return True

    def refresh(self, parks):
        """Fetch now and save; on any failure keep what's there. True if it worked."""
        try:
            with self.lock:
                keep = {park: list(names) for park, names in self.rides.items()}
            rides = self.fetch(parks, keep)
            if not any(rides.values()):
                raise ValueError("the parks listed no rides")
            self._write(parks, rides)
        except Exception as e:  # a bad reply or full disk: log it, keep the old list, retry later
            debug.warning(f"Settings page: couldn't refresh the ride list ({type(e).__name__}: {e}); "
                          f"{'keeping the last one' if self.rides else 'the pickers stay empty until it works'}.")
            return False
        finally:
            with self.lock:
                self.fetching = False
        debug.info(f"Settings page: {sum(len(r) for r in rides.values())} rides from ThemeParks.wiki.")
        return True

    def _write(self, parks, rides):
        """Use the new list, then keep it for next time. A file that can't be written only costs a fetch
        after a restart."""
        fetched = self.clock()
        with self.lock:
            self.fetched, self.parks, self.rides = fetched, list(parks), rides
        temp = self.path + ".new"
        try:
            with open(temp, "w", encoding="utf-8") as f:
                json.dump({"format": FORMAT, "fetched": fetched, "parks": list(parks), "rides": rides}, f)
            os.replace(temp, self.path)
        except OSError as e:
            debug.warning(f"Settings page: can't save the ride list to {self.path}: {e}")
