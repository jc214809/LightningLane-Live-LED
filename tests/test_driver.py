"""The real driver/__init__.py. Every other test sees tests/stubs/conftest.py's stand-in, so this
loads the package for the test and puts the stand-in back after."""
import importlib
import sys
import types

import pytest


@pytest.fixture
def real_driver():
    stub = sys.modules.pop("driver", None)
    sys.modules.pop("driver.mode", None)
    try:
        yield importlib.import_module("driver")  # the DriverWrapper it puts in sys.modules
    finally:
        _restore(stub)


def _restore(stub):
    sys.modules.pop("driver.mode", None)
    if stub is None:
        sys.modules.pop("driver", None)
    else:
        sys.modules["driver"] = stub


def _fake_rgbmatrix():
    module = types.ModuleType("rgbmatrix")
    module.graphics = types.SimpleNamespace(DrawText="rgbmatrix DrawText")
    return module


def test_importing_the_driver_never_reads_the_command_line(monkeypatch):
    # disney.py owns sys.argv; anything else importing a display module mustn't exit on its flags.
    monkeypatch.setattr(sys, "argv", ["some-other-program", "--not-a-board-flag"])
    monkeypatch.delitem(sys.modules, "unittest")  # as outside the tests, where the driver used to parse
    monkeypatch.setitem(sys.modules, "rgbmatrix", None)
    stub = sys.modules.pop("driver", None)
    try:
        importlib.import_module("driver")
    finally:
        _restore(stub)


def test_tests_get_the_emulator(real_driver):
    assert real_driver.is_emulated()
    assert real_driver.driver.__name__ == "RGBMatrixEmulator"


def test_hardware_falls_back_to_the_emulator_without_rgbmatrix(real_driver, monkeypatch):
    monkeypatch.setitem(sys.modules, "rgbmatrix", None)  # import rgbmatrix raises ImportError
    real_driver.set_mode(real_driver.DriverMode.HARDWARE)
    assert real_driver.is_emulated()
    assert real_driver.hardware_load_failed


def test_emulated_on_a_pi_switches_graphics_imported_before_the_switch(real_driver, monkeypatch):
    # A Pi run with --emulated: display modules import graphics while the driver is still
    # rgbmatrix, then disney.main() switches to the emulator. rgbmatrix's DrawText would crash
    # on the emulator's canvas, so the graphics they hold must follow the switch.
    monkeypatch.setitem(sys.modules, "rgbmatrix", _fake_rgbmatrix())
    real_driver.set_mode(real_driver.DriverMode.HARDWARE)
    assert real_driver.is_hardware()
    graphics = real_driver.graphics
    assert graphics.DrawText == "rgbmatrix DrawText"

    real_driver.set_mode(real_driver.DriverMode.SOFTWARE_EMULATION)
    import RGBMatrixEmulator
    assert graphics.DrawText is RGBMatrixEmulator.graphics.DrawText
    assert real_driver.RGBMatrix is RGBMatrixEmulator.RGBMatrix


def test_swapping_a_graphics_function_patches_the_drivers_and_restores_cleanly(real_driver, monkeypatch):
    # display/capture.py swaps DrawText for its own while capturing a screen, then puts it back.
    monkeypatch.setitem(sys.modules, "rgbmatrix", _fake_rgbmatrix())
    real_driver.set_mode(real_driver.DriverMode.HARDWARE)
    graphics, hardware = real_driver.graphics, sys.modules["rgbmatrix"].graphics

    saved = graphics.DrawText
    graphics.DrawText = "software DrawText"
    assert hardware.DrawText == "software DrawText"
    graphics.DrawText = saved
    assert hardware.DrawText == "rgbmatrix DrawText"

    real_driver.set_mode(real_driver.DriverMode.SOFTWARE_EMULATION)
    import RGBMatrixEmulator
    assert graphics.DrawText is RGBMatrixEmulator.graphics.DrawText, "nothing pinned to the old driver"
