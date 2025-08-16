import os
import sys
import types

import io
import json

# Dummy JSON config that will be used whenever someone tries to open "config.json"
DUMMY_CONFIG = '{"debug": true, "trip_countdown": {"trip_date": "2023-10-01", "enabled": true}}'

# Define a dummy open function that always returns a StringIO over the dummy config when the requested file is config.json.
_original_open = open  # Save the original open in case you need it.

def dummy_open(file, mode='r', *args, **kwargs):
    if os.path.basename(file) == "config.json":
        return io.StringIO(DUMMY_CONFIG)
    return _original_open(file, mode, *args, **kwargs)

# Patch builtins.open so that tests that import disney.py (which calls load_config)
# will use our dummy_open function. This is done early in conftest.py.
import builtins
builtins.open = dummy_open

# (Optional) Add stubs directory to sys.path if needed.
STUBS_DIR = os.path.join(os.path.dirname(__file__), 'stubs')
if STUBS_DIR not in sys.path:
    sys.path.insert(0, STUBS_DIR)


dummy_driver = types.ModuleType("driver")
dummy_driver.RGBMatrix = lambda options=None: object()
dummy_driver.__version__ = "dummy"
dummy_driver.graphics = lambda *args, **kwargs: None

sys.modules["driver"] = dummy_driver


# Add the stubs directory to sys.path so tests use stub modules
STUBS_DIR = os.path.join(os.path.dirname(__file__), 'stubs')
if STUBS_DIR not in sys.path:
    sys.path.insert(0, STUBS_DIR)

