"""
Picks rgbmatrix (a Pi) or RGBMatrixEmulator, and stands in for whichever it is: `from driver import
RGBMatrix, graphics` works the same on both. Hardware unless running under tests or rgbmatrix won't
import; disney.py switches to the emulator with set_mode for --emulated (cli.py). Importing this
never reads the command line, as in mlb-led-scoreboard.
"""
import sys

from driver.mode import DriverMode
from utils import debug


class _Graphics:
    """driver.graphics, looked up on the current driver at each use. Display modules import it
    before disney.py has read --emulated, so a binding made then would keep rgbmatrix's graphics,
    which crash on an emulator canvas. Setting or deleting an attribute (display/capture.py swaps
    in its own DrawText while capturing) changes the current driver's graphics, as it always did."""

    def __init__(self, wrapper):
        object.__setattr__(self, "_wrapper", wrapper)

    def __getattr__(self, name):
        return getattr(self._wrapper.driver.graphics, name)

    def __setattr__(self, name, value):
        setattr(self._wrapper.driver.graphics, name, value)

    def __delattr__(self, name):
        delattr(self._wrapper.driver.graphics, name)


class DriverWrapper:
    DriverMode = DriverMode  # driver.mode can't be imported once this object replaces the package

    def __init__(self):
        self.hardware_load_failed = False
        self.mode = None
        self.graphics = _Graphics(self)

        if 'unittest' in sys.modules:
            self.set_mode(DriverMode.SOFTWARE_EMULATION)
        else:
            self.set_mode(DriverMode.HARDWARE)
    @property
    def __name__(self):
        return 'driver'

    def is_hardware(self):
        return self.mode == DriverMode.HARDWARE

    def is_emulated(self):
        return self.mode == DriverMode.SOFTWARE_EMULATION

    def set_mode(self, mode):
        self.mode = mode

        if self.is_hardware():
            try:
                import rgbmatrix

                self.driver = rgbmatrix
            except ImportError:
                self.mode = DriverMode.SOFTWARE_EMULATION
                self.hardware_load_failed = True
                debug.info("Failed to load hardware driver. Using software emulation.")

        if self.is_emulated():
            # Outside the except: the emulator's own load errors aren't chained to rgbmatrix's.
            import RGBMatrixEmulator

            self.driver = RGBMatrixEmulator

        debug.info(f"Driver mode: {self.mode}")

    def __getattr__(self, name):
        return getattr(self.driver, name)


sys.modules['driver'] = DriverWrapper()
