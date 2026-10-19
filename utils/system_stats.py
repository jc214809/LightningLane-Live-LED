"""
A board's own state for the logs: load, CPU temperature and clock, and the Pi's throttle flags. They show
whether a slow stretch of the show came from the board (too hot, under-voltage, busy) or from the
drawing. Reads small sysfs files only, no subprocess, so it's cheap enough to call from the show's loop.
A value the machine doesn't have (any of them, off a Pi) is left out of the text, not an error.
"""
import os

THERMAL_PATH = "/sys/class/thermal/thermal_zone0/temp"  # millidegrees C
CPU_FREQ_PATH = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"  # kHz
THROTTLED_PATH = "/sys/devices/platform/soc/soc:firmware/get_throttled"  # the firmware's bit flags, in hex


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def describe():
    """The board's state as "load 1.4, 61°C, 1500 MHz, throttled 0x0", leaving out what it can't read.
    Throttled 0x0 is healthy; bit 0 is under-voltage now, 1 frequency capped, 2 throttled, 3 soft
    temperature limit, and bits 16-19 are the same since boot."""
    parts = []
    try:
        parts.append(f"load {os.getloadavg()[0]:.1f}")
    except (OSError, AttributeError):
        pass
    for path, scale, template in ((THERMAL_PATH, 1000, "{:.0f}°C"), (CPU_FREQ_PATH, 1000, "{:.0f} MHz")):
        text = _read(path)
        try:
            if text is not None:
                parts.append(template.format(int(text) / scale))
        except ValueError:
            pass
    text = _read(THROTTLED_PATH)
    try:
        if text is not None:
            parts.append(f"throttled {int(text, 16):#x}")
    except ValueError:
        pass
    return ", ".join(parts)
