import os
import sys
import types

dummy_driver = types.ModuleType("driver")
dummy_driver.RGBMatrix = lambda options=None: object()
dummy_driver.__version__ = "dummy"
dummy_driver.graphics = lambda *args, **kwargs: None

sys.modules["driver"] = dummy_driver


# Add the stubs directory to sys.path so tests use stub modules
STUBS_DIR = os.path.join(os.path.dirname(__file__), 'stubs')
if STUBS_DIR not in sys.path:
    sys.path.insert(0, STUBS_DIR)

