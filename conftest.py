import os
import tempfile

# Redirect utils.debug's log file into a throwaway temp directory before any
# test module can import utils.debug (that import wires up a RotatingFileHandler
# pointed at the real logs/app.log). Without this, running pytest alongside a
# live app instance interleaves test fixture data into the real log and can
# even trip live logic that reacts to log-derived state (e.g. the WebSocket
# watchdog's message counter).
os.environ.setdefault('LLL_LOG_DIR', tempfile.mkdtemp(prefix='lll-test-logs-'))


import pytest


@pytest.fixture(autouse=True)
def _network_ok():
    # The network flag is process-wide; a test that fails a fetch would otherwise
    # leave the badge drawn over every later test's frames.
    import updater.shared as shared
    shared._network_issues = False
    yield
    shared._network_issues = False
