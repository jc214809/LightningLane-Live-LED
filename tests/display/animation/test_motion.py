"""Easing and progress through a span of time."""

import display.animation as animation


def test_ease_out_is_clamped_and_monotonic():
    samples = [animation.ease_out(p / 10) for p in range(-2, 13)]
    assert samples[0] == 0 and samples[-1] == 1
    assert samples == sorted(samples)


def test_progress_runs_zero_to_one_across_its_span():
    assert [animation.progress(t, 1.0, 3.0) for t in (0.0, 1.0, 2.0, 3.0, 9.0)] == [0.0, 0.0, 0.5, 1.0, 1.0]
