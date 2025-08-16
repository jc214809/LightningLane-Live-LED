import sys

from driver.mode import DriverMode
from utils import debug
from utils.utils import args


class DriverWrapper:
    def __init__(self):
        self.hardware_load_failed = False
        self.mode = None

        if 'unittest' in sys.modules or args().emulated:
            self.set_mode(DriverMode.SOFTWARE_EMULATION)
        else:
            self.set_mode(DriverMode.HARDWARE)

        if self.hardware_load_failed:
            debug.info("Failed to load hardware driver. Using software emulation.")

        debug.info(f"Driver mode: {self.mode}")
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
                import RGBMatrixEmulator

                self.mode = DriverMode.SOFTWARE_EMULATION
                self.driver = RGBMatrixEmulator
                self.hardware_load_failed = True
        else:
            import RGBMatrixEmulator

            self.driver = RGBMatrixEmulator

    def __getattr__(self, name):
        return getattr(self.driver, name)


sys.modules['driver'] = DriverWrapper()
