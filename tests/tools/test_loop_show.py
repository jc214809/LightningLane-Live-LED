import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("loop_show", os.path.join(ROOT, "tools", "loop_show.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)


def test_the_show_starts_from_the_loops_start():
    """render_music_show counts from its first clock reading, so the loop's clock puts that in the past."""
    ticks = iter([100.0, 100.0, 101.5])
    clock = tool.offset_clock(46.0, now=lambda: next(ticks))
    t0 = clock()
    assert clock() - t0 == 46.0, "the first frame is 46 s into the show"
    assert clock() - t0 == 47.5, "and it runs on with the real clock"


def test_each_loop_gets_a_fresh_clock():
    ticks = iter([10.0, 10.0, 20.0, 20.0])
    first, second = tool.offset_clock(5.0, now=lambda: next(ticks)), tool.offset_clock(5.0, now=lambda: next(ticks))
    a0 = first()
    assert first() - a0 == 5.0
    b0 = second()
    assert second() - b0 == 5.0


def test_the_music_clip_is_named_for_its_part():
    path = tool.clip_path(0, 98)
    assert path.endswith(os.path.join("build", "loop_show", "happily-ever-after-0-98.wav"))
    assert tool.clip_path(45.8, 47) != path


def test_start_must_come_before_end():
    with pytest.raises(SystemExit):
        tool.main(["98", "0"])
