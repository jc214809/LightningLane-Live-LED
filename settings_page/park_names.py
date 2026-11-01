"""Every ThemeParks.wiki park name, for the settings page's park picker and for refusing a name
the app wouldn't find. Fetched from /v1/destinations at most once a day (a failed fetch is retried
after RETRY_S) and kept in a file, so a phone on the setup hotspot, with no internet, still gets
the list. Fetches run in the background: a page never waits on the API.
"""
import json
import os
import ssl
import threading
import time
import urllib.request

import certifi

from parks.names import config_names
from utils import debug

DESTINATIONS_URL = "https://api.themeparks.wiki/v1/destinations"
MAX_AGE_S = 24 * 60 * 60
RETRY_S = 10 * 60
TIMEOUT_S = 10


def fetch_destinations():
    """/v1/destinations' list. Raises on a network error, a bad status or bad JSON."""
    request = urllib.request.Request(DESTINATIONS_URL, headers={"User-Agent": "LightningLane-Live-LED settings page"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S,
                                context=ssl.create_default_context(cafile=certifi.where())) as response:
        destinations = json.load(response).get("destinations")
    if not isinstance(destinations, list):
        raise ValueError("no destinations list in the reply")
    return destinations


class ParkNames:
    """The cached names. names() is [(name, destination name)], or [] before the first fetch
    that worked (the page then doesn't check names: it can't know them)."""

    def __init__(self, path, fetch=fetch_destinations, clock=time.time):
        self.path, self.fetch, self.clock = path, fetch, clock
        self.lock = threading.Lock()
        self.fetching = False
        self.last_try = None
        self.fetched, self.parks = self._read()

    def _read(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                saved = json.load(f)
            parks = [(str(n), str(d)) for n, d in saved["parks"]]
            return float(saved["fetched"]), parks
        except FileNotFoundError:
            return None, []
        except (OSError, ValueError, KeyError, TypeError) as e:
            debug.warning(f"Settings page: ignoring the park list in {self.path}: {e}")
            return None, []

    def names(self):
        """The names now; starts a fetch in the background when they're a day old (or missing)."""
        self.refresh_if_due()
        with self.lock:
            return list(self.parks)

    def refresh_if_due(self):
        now = self.clock()
        with self.lock:
            fresh = self.fetched is not None and now - self.fetched < MAX_AGE_S
            tried = self.last_try is not None and now - self.last_try < RETRY_S
            if fresh or tried or self.fetching:
                return False
            self.fetching, self.last_try = True, now
        threading.Thread(target=self.refresh, name="park-names", daemon=True).start()
        return True

    def refresh(self):
        """Fetch now and save; on any failure keep what's there. True if it worked."""
        try:
            parks = config_names(self.fetch())
            if not parks:
                raise ValueError("the reply listed no parks")
            self._write(parks)
        except Exception as e:  # a bad reply or full disk: log it, keep the old list, retry later
            debug.warning(f"Settings page: couldn't refresh the park list ({type(e).__name__}: {e}); "
                          f"{'keeping the last one' if self.parks else 'names are not checked until it works'}.")
            return False
        finally:
            with self.lock:
                self.fetching = False
        debug.info(f"Settings page: {len(parks)} park names from ThemeParks.wiki.")
        return True

    def _write(self, parks):
        """Use the new list, then keep it for next time. A file that can't be written only costs
        a fetch after a restart."""
        fetched = self.clock()
        with self.lock:
            self.fetched, self.parks = fetched, parks
        temp = self.path + ".new"
        try:
            with open(temp, "w", encoding="utf-8") as f:
                json.dump({"fetched": fetched, "parks": parks}, f)
            os.replace(temp, self.path)
        except OSError as e:
            debug.warning(f"Settings page: can't save the park list to {self.path}: {e}")
