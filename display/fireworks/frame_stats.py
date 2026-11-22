"""Frame timing for the castle fireworks, logged once per show so a slow board can be diagnosed from its journal."""

import time

from utils import debug, system_stats


class FrameStats:
    """Counts frames, late frames and build/push time; summary() is the one log line.

    Per frame it costs a few additions and comparisons: the caller passes the seconds it spent building
    the pixels and pushing them to the matrix. The clocks are injectable so tests need no real time."""

    def __init__(self, label, size, fps, planned, clocks=(time.monotonic, time.thread_time, time.process_time)):
        self.label, self.size, self.fps, self.planned = label, size, fps, planned
        self.frame_time = 1.0 / fps
        self.frames = self.late = self.most_pixels = 0
        self.build_total = self.push_total = 0.0
        self.slowest = self.slowest_build = 0.0
        self.sleigh_frames, self.sleigh_total, self.plain_total = 0, 0.0, 0.0
        self._clocks = clocks
        self._start = tuple(clock() for clock in clocks)

    def record(self, start, built, pixels=0, sleigh=False):
        """Count a frame that began at `start`, had its pixels built at `built` and was pushed just now
        (all on the monotonic clock). Returns the seconds the frame took, for the caller's sleep."""
        end = self._clocks[0]()
        build, spent = built - start, end - start
        self.frames += 1
        self.build_total += build
        self.push_total += end - built
        self.most_pixels = max(self.most_pixels, pixels)
        if spent > self.frame_time:
            self.late += 1
        if spent > self.slowest:
            self.slowest, self.slowest_build = spent, build
        if sleigh:
            self.sleigh_frames += 1
            self.sleigh_total += spent
        else:
            self.plain_total += spent
        return spent

    def summary(self, board=None):
        """The log line for the show so far; `board` is system_stats.describe()'s text."""
        now = tuple(clock() for clock in self._clocks)
        wall, thread, process = (n - s for n, s in zip(now, self._start, strict=True))
        if not self.frames or wall <= 0:
            return f"{self.label} fireworks {self.size}: no frames drawn"
        parts = [
            f"{self.label} fireworks {self.size}: {wall:.1f}s, {self.frames}/{self.planned} frames, "
            f"{self.frames / wall:.1f} fps (aiming for {self.fps})",
            f"{self.late} late",
            f"slowest frame {self.slowest * 1000:.0f} ms "
            f"(build {self.slowest_build * 1000:.0f} / push {(self.slowest - self.slowest_build) * 1000:.0f})",
            f"avg build {self.build_total / self.frames * 1000:.1f} / push {self.push_total / self.frames * 1000:.1f} ms",
            f"{self.most_pixels} px",
        ]
        if self.sleigh_frames:
            plain = self.frames - self.sleigh_frames
            sleigh_ms = self.sleigh_total / self.sleigh_frames * 1000
            plain_text = f"{self.plain_total / plain * 1000:.1f} ms" if plain else "n/a"
            parts.append(f"sleigh on {self.sleigh_frames} frames avg {sleigh_ms:.1f} ms vs off {plain_text}")
        parts.append(f"CPU show {thread / wall:.0%} / process {process / wall:.0%}")
        if board:
            parts.append(board)
        return ", ".join(parts)

    def log(self):
        debug.info(self.summary(system_stats.describe()))
