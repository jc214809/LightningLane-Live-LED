"""Frame timing for the castle fireworks, logged so a slow board can be diagnosed from its journal."""

import time

from utils import debug, system_stats

SLICE_S = 60  # a show longer than this also logs one line per slice, to show a slowdown growing partway


class _Window:
    """Counters for the frames since `start` (the monotonic, thread and process clocks at that moment)."""

    def __init__(self, start):
        self.start = start
        self.frames = self.late = self.most_pixels = self.sleigh_frames = 0
        self.build_total = self.push_total = self.sleigh_total = self.plain_total = 0.0
        self.slowest = self.slowest_build = 0.0

    def merge(self, other):
        """Fold a finished slice into this window (once a slice, not per frame)."""
        self.frames += other.frames
        self.late += other.late
        self.sleigh_frames += other.sleigh_frames
        self.build_total += other.build_total
        self.push_total += other.push_total
        self.sleigh_total += other.sleigh_total
        self.plain_total += other.plain_total
        self.most_pixels = max(self.most_pixels, other.most_pixels)
        if other.slowest > self.slowest:
            self.slowest, self.slowest_build = other.slowest, other.slowest_build


class FrameStats:
    """Counts frames, late frames and build/push time; the summary is the log line.

    Per frame it costs a few additions and comparisons: the caller passes when a frame began and when its
    pixels were built. A show longer than SLICE_S logs a line per slice, then the whole-show summary.
    The clocks are injectable so tests need no real time."""

    def __init__(self, label, size, fps, planned, clocks=(time.monotonic, time.thread_time, time.process_time)):
        self.label, self.size, self.fps, self.planned = label, size, fps, planned
        self.frame_time = 1.0 / fps
        self._clocks = clocks
        self._first = tuple(clock() for clock in clocks)
        self.total = _Window(self._first)
        self.window = _Window(self._first)
        self.sliced = planned / fps > SLICE_S
        self._next_slice = self._first[0] + SLICE_S

    def record(self, start, built, pixels=0, sleigh=False):
        """Count a frame that began at `start`, had its pixels built at `built` and was pushed just now
        (all on the monotonic clock). Returns the seconds the frame took, for the caller's sleep."""
        end = self._clocks[0]()
        w, build, spent = self.window, built - start, end - start
        w.frames += 1
        w.build_total += build
        w.push_total += end - built
        w.most_pixels = max(w.most_pixels, pixels)
        if spent > self.frame_time:
            w.late += 1
        if spent > w.slowest:
            w.slowest, w.slowest_build = spent, build
        if sleigh:
            w.sleigh_frames += 1
            w.sleigh_total += spent
        else:
            w.plain_total += spent
        if self.sliced and end >= self._next_slice:
            self._log_slice()
        return spent

    def _log_slice(self):
        first = self._next_slice - SLICE_S - self._first[0]
        span = f" [{self._stamp(first)}-{self._stamp(first + SLICE_S)}]"
        debug.info(self._line(self.window, span, system_stats.describe()))
        self.total.merge(self.window)
        self.window = _Window(tuple(clock() for clock in self._clocks))
        self._next_slice += SLICE_S

    @staticmethod
    def _stamp(seconds):
        return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"

    def summary(self, board=None):
        """The whole-show log line; `board` is system_stats.describe()'s text."""
        whole = _Window(self._first)
        whole.merge(self.total)
        whole.merge(self.window)
        return self._line(whole, "", board)

    def _line(self, w, span, board):
        head = f"{self.label} fireworks {self.size}{span}"
        now = tuple(clock() for clock in self._clocks)
        wall, thread, process = (n - s for n, s in zip(now, w.start, strict=True))
        if not w.frames or wall <= 0:
            return f"{head}: no frames drawn"
        planned = "" if span else f"/{self.planned}"
        parts = [
            f"{head}: {wall:.1f}s, {w.frames}{planned} frames, {w.frames / wall:.1f} fps (aiming for {self.fps})",
            f"{w.late} late",
            f"slowest frame {w.slowest * 1000:.0f} ms "
            f"(build {w.slowest_build * 1000:.0f} / push {(w.slowest - w.slowest_build) * 1000:.0f})",
            f"avg build {w.build_total / w.frames * 1000:.1f} / push {w.push_total / w.frames * 1000:.1f} ms",
            f"{w.most_pixels} px",
        ]
        if w.sleigh_frames:
            plain = w.frames - w.sleigh_frames
            plain_text = f"{w.plain_total / plain * 1000:.1f} ms" if plain else "n/a"
            sleigh_ms = w.sleigh_total / w.sleigh_frames * 1000
            parts.append(f"sleigh on {w.sleigh_frames} frames avg {sleigh_ms:.1f} ms vs off {plain_text}")
        parts.append(f"CPU show {thread / wall:.0%} / process {process / wall:.0%}")
        if board:
            parts.append(board)
        return ", ".join(parts)

    def log(self):
        debug.info(self.summary(system_stats.describe()))
