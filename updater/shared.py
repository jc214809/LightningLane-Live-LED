import threading
import time

# Guards mutations of the shared parks_data structure by the WebSocket and REST
# threads. Held only for in-memory writes (microseconds) — never across HTTP
# calls. The display thread deliberately reads without locking: a torn read
# costs one frame of slightly inconsistent pixels, not corrupted state.
parks_data_lock = threading.Lock()

# Set when the updater threads can't reach the ThemeParks API, cleared as soon as
# data gets through again; the display draws a badge while it's set. A lone bool
# written by the updaters and read by the display needs no lock.
_network_issues = False


def network_issues():
    return _network_issues


def note_network_result(ok):
    global _network_issues
    if _network_issues == (not ok):
        return
    _network_issues = not ok
    # Imported here so the display thread's import of this module stays dependency-free.
    from utils import debug
    if ok:
        debug.info("Network connection restored.")
    else:
        debug.warning("Network connection lost; showing the network badge.")


# The preview WebSocket's health, for the REST thread to decide whether it still needs to poll.
# Synced once a connection has delivered a snapshot or finished a resume; any frame keeps it
# alive. Written only by the WS thread; plain assignments, read by the REST thread without a lock.
LIVE_FEED_SILENCE_SECS = 90
_live_feed_synced = threading.Event()
_live_feed_last_frame = None


def note_live_feed_frame():
    global _live_feed_last_frame
    _live_feed_last_frame = time.monotonic()


def note_live_feed_synced():
    note_live_feed_frame()
    _live_feed_synced.set()


def note_live_feed_down():
    _live_feed_synced.clear()


def live_feed_healthy():
    """True while the preview WebSocket is synced and has sent something in the last 90s."""
    return (_live_feed_synced.is_set() and _live_feed_last_frame is not None
            and time.monotonic() - _live_feed_last_frame <= LIVE_FEED_SILENCE_SECS)


def wait_for_live_feed(timeout_s):
    """Block up to timeout_s for the WebSocket's first sync; True if it came."""
    return _live_feed_synced.wait(timeout_s)
