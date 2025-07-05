import os
import sys
import types
from zoneinfo import ZoneInfo

# Add project root to sys.path for module imports in tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide lightweight stubs for optional third-party libraries that may not be installed
if 'requests' not in sys.modules:
    sys.modules['requests'] = types.ModuleType('requests')

if 'pytz' not in sys.modules:
    fake_pytz = types.ModuleType('pytz')

    def timezone(name):
        # Provide a basic UTC-4 timezone for tests when tzdata isn't available.
        from datetime import timezone as dt_timezone, timedelta
        if name in {'US/Eastern', 'America/New_York'}:
            return dt_timezone(timedelta(hours=-4))
        return dt_timezone.utc

    fake_pytz.timezone = timezone
    fake_pytz.utc = timezone('UTC')
    sys.modules['pytz'] = fake_pytz

if 'pyowm' not in sys.modules:
    fake_pyowm = types.ModuleType('pyowm')
    fake_commons = types.ModuleType('pyowm.commons')
    fake_commons.exceptions = types.ModuleType('pyowm.commons.exceptions')
    fake_pyowm.commons = fake_commons
    sys.modules['pyowm'] = fake_pyowm
    sys.modules['pyowm.commons'] = fake_commons
    sys.modules['pyowm.commons.exceptions'] = fake_commons.exceptions

if 'aiohttp' not in sys.modules:
    sys.modules['aiohttp'] = types.ModuleType('aiohttp')

# Stub for LED matrix libraries used during import
if 'RGBMatrixEmulator' not in sys.modules:
    fake_emulator = types.ModuleType('RGBMatrixEmulator')
    class FakeMatrix:
        pass
    fake_emulator.RGBMatrix = FakeMatrix
    fake_emulator.__version__ = '0'
    sys.modules['RGBMatrixEmulator'] = fake_emulator

if 'rgbmatrix' not in sys.modules:
    fake_rgbmatrix = types.ModuleType('rgbmatrix')
    class FakeMatrix:
        pass
    fake_rgbmatrix.RGBMatrix = FakeMatrix
    fake_rgbmatrix.__version__ = '0'
    sys.modules['rgbmatrix'] = fake_rgbmatrix

# Stub heavy display/updater modules with minimal attributes used during import
stubbed_modules = {
    'display.park.park_details': ['render_park_information_screen'],
    'display.display': ['initialize_fonts'],
    'display.startup': ['render_mickey_logo'],
    'display.attractions.attraction_info': ['render_attraction_info'],
    'display.countdown.countdown': ['render_countdown_to_disney'],
    'updater.data_updater': ['live_data_updater'],
}
for module_name, attrs in stubbed_modules.items():
    if module_name not in sys.modules:
        mod = types.ModuleType(module_name)
        for attr in attrs:
            setattr(mod, attr, lambda *a, **kw: None)
        sys.modules[module_name] = mod
