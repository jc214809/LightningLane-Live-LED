import threading

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
