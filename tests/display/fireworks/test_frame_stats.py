# tests/display/fireworks/test_frame_stats.py
import pytest

from display.fireworks import frame_stats
from display.fireworks.frame_stats import FrameStats


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _stats(fps=10, planned=4):
    mono, thread, process = Clock(), Clock(), Clock()
    return FrameStats("christmas", "64x32", fps, planned, (mono, thread, process)), mono, thread, process


def _frame(stats, mono, build, push, **kwargs):
    start = mono.now
    mono.now += build
    built = mono.now
    mono.now += push
    return stats.record(start, built, **kwargs)


def test_record_counts_late_frames_and_the_slowest_split():
    stats, mono, *_ = _stats(fps=10)  # 100 ms budget
    assert _frame(stats, mono, 0.02, 0.03, pixels=10) == pytest.approx(0.05)
    _frame(stats, mono, 0.05, 0.10, pixels=40)  # late
    _frame(stats, mono, 0.01, 0.02, pixels=25)
    assert (stats.frames, stats.late, stats.most_pixels) == (3, 1, 40)
    assert stats.slowest == pytest.approx(0.15)
    assert stats.slowest_build == pytest.approx(0.05)


def test_summary_line_content():
    stats, mono, thread, process = _stats(fps=10, planned=4)
    for _ in range(2):
        _frame(stats, mono, 0.02, 0.04, pixels=7)
        mono.now += 0.04  # the sleep
    _frame(stats, mono, 0.1, 0.1, pixels=9, sleigh=True)
    mono.now = 1.0
    thread.now, process.now = 0.5, 0.75
    line = stats.summary("load 1.0, 50°C")
    assert line.startswith("christmas fireworks 64x32: 1.0s, 3/4 frames, 3.0 fps (aiming for 10)")
    assert "1 late" in line
    assert "slowest frame 200 ms (build 100 / push 100)" in line
    assert "avg build 46.7 / push 60.0 ms" in line
    assert "9 px" in line
    assert "sleigh on 1 frames avg 200.0 ms vs off 60.0 ms" in line
    assert "CPU show 50% / process 75%" in line
    assert line.endswith("load 1.0, 50°C")


def test_summary_leaves_out_the_sleigh_split_and_board_when_there_is_none():
    stats, mono, *_ = _stats()
    _frame(stats, mono, 0.01, 0.01)
    line = stats.summary()
    assert "sleigh" not in line
    assert line.count(",") == line.replace("°C", "").count(",")  # no trailing board text
    assert "CPU show" in line


def test_summary_without_frames_does_not_divide_by_zero():
    stats, *_ = _stats()
    assert stats.summary() == "christmas fireworks 64x32: no frames drawn"


def test_log_writes_one_info_line_with_the_board_stats(monkeypatch):
    lines = []
    monkeypatch.setattr(frame_stats.debug, "info", lines.append)
    monkeypatch.setattr(frame_stats.system_stats, "describe", lambda: "throttled 0x0")
    stats, mono, *_ = _stats()
    _frame(stats, mono, 0.01, 0.01)
    mono.now = 1.0
    stats.log()
    assert len(lines) == 1 and lines[0].endswith("throttled 0x0")
