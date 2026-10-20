#!/usr/bin/env python3
"""
Line up the show video's audio with our board file and print how one maps to the other, so moments
seen in the video (Gemini's timestamps) convert to the score's seconds exactly.

    python3 docs/shows/happily-ever-after/align_audio.py              # windows + fitted line
    python3 docs/shows/happily-ever-after/align_audio.py --at 788     # a video time in audio seconds

Cross-correlates onset envelopes (10 ms frames of rising loudness), which survive crowd noise and
different mixes better than raw samples. Needs yt-dlp and ffmpeg on the PATH, and numpy.
"""
import argparse
import logging
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OURS = os.path.join(ROOT, "sounds", "happily-ever-after.wav")
URL = "https://www.youtube.com/watch?v=-LncKUxWMsQ"
SR = 4000
HOP = 40  # 10 ms
FPS = SR // HOP
WIN_S, STEP_S, SEARCH_S = 30, 20, 25
SHOW_S = 1110
STRONG = 4.8  # peaks above this were all on one line in 2026-10-11's run; weaker ones wander

logger = logging.getLogger(__name__)


def _mono(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", dst],
                   check=True)
    return np.fromfile(dst, dtype=np.float32)


def onset_envelope(x):
    n = len(x) // HOP
    loud = np.log(np.sqrt((x[: n * HOP].reshape(n, HOP) ** 2).mean(axis=1) + 1e-12))
    rise = np.maximum(np.diff(loud, prepend=loud[0]), 0)
    return rise - rise.mean()


def best_offset(ours, vid, t, guess):
    """Where ours[t : t+WIN] sits in the video, searching guess ± SEARCH. Returns (offset_s, peak)."""
    a = ours[t * FPS:(t + WIN_S) * FPS]
    lo = max(0, int((t + guess - SEARCH_S) * FPS))
    b = vid[lo:int((t + guess + SEARCH_S + WIN_S) * FPS)]
    if len(b) < len(a) or a.std() == 0:
        return None
    a = (a - a.mean()) / a.std()
    n = len(a) + len(b)
    corr = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)[: len(b) - len(a) + 1]
    corr /= np.sqrt(np.maximum(np.convolve(b ** 2, np.ones(len(a)), "valid"), 1e-9))
    k = int(np.argmax(corr))
    return (lo + k) / FPS - t, float(corr[k])


def align(ours, vid):
    """Every window's (t, offset, peak), and the line video = audio * scale + shift fitted to strong ones."""
    rows, guess = [], 8.0
    for t in range(0, SHOW_S, STEP_S):
        found = best_offset(ours, vid, t, guess)
        if found is None:
            continue
        off, peak = found
        rows.append((t, off, peak))
        if peak > STRONG:
            guess = off
    strong = np.array([(t, off) for t, off, peak in rows if peak > STRONG])
    if len(strong) < 3:
        raise SystemExit("too few strong matches to fit a line; is it the same recording?")
    ts, offs = strong.T
    for tolerance in (1.0, 0.15):  # drop the far outliers, refit, then the near ones
        slope, shift = np.polyfit(ts, offs, 1)
        keep = abs(offs - (slope * ts + shift)) < tolerance
        ts, offs = ts[keep], offs[keep]
    return rows, 1 + slope, shift, len(ts)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--at", type=float, action="append", default=[], help="video seconds to convert")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not os.path.exists(OURS):
        sys.exit(f"missing {OURS} (gitignored; copy it from a board)")
    with tempfile.TemporaryDirectory() as tmp:
        logger.info("downloading the video's audio...")
        subprocess.run(["yt-dlp", "-q", "-f", "bestaudio", "-x", "--audio-format", "wav",
                        "-o", os.path.join(tmp, "video.%(ext)s"), URL], check=True)
        vid = onset_envelope(_mono(os.path.join(tmp, "video.wav"), os.path.join(tmp, "v.raw")))
        ours = onset_envelope(_mono(OURS, os.path.join(tmp, "o.raw")))
    rows, scale, shift, used = align(ours, vid)
    for t, off, peak in rows:
        print(f"audio {t:5d}s -> video {t + off:7.2f}s  offset {off:+6.2f}  peak {peak:5.2f}"
              f"{'' if peak > STRONG else '  (weak, ignored)'}")
    print(f"\nvideo = audio x {scale:.5f} + {shift:.2f} s   (fitted to {used} strong windows)")
    for v in args.at:
        print(f"video {v:.2f}s = audio {(v - shift) / scale:.2f}s")


if __name__ == "__main__":
    main()
