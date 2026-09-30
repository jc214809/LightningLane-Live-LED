"""display.motion: easing and progress, shared across the board."""
import pytest

from display import motion


def test_ease_out_and_smooth_are_clamped_and_run_zero_to_one():
    for ease in (motion.ease_out, motion.smooth):
        assert ease(-1) == 0.0 and ease(0) == 0.0 and ease(1) == 1.0 and ease(2) == 1.0
        values = [ease(i / 20) for i in range(21)]
        assert values == sorted(values)


def test_smooth_is_gentle_at_both_ends_and_half_way_at_the_middle():
    assert motion.smooth(0.5) == 0.5
    assert motion.smooth(0.1) < 0.1 and motion.smooth(0.9) > 0.9


def test_progress_and_ramp_agree_on_a_span():
    for t in (0.0, 1.0, 1.5, 2.0, 3.0, 5.0):
        assert motion.progress(t, 1.0, 3.0) == pytest.approx(motion.ramp(t, 1.0, 2.0))
    assert [motion.ramp(t, 1.0, 2.0) for t in (0.0, 2.0, 9.0)] == [0.0, 0.5, 1.0]
