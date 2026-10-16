#!/usr/bin/env python3
"""
Loop part of a synced fireworks show in the emulator, with its music cut to the same part, for
checking a section live while working on it. The real show code plays from FROM to TO seconds of
the show (audio time, as in the score), then starts over. Nothing here changes the show.

    python3 tools/loop_show.py 0 98                     # the opening, 64x32, silent
    python3 tools/loop_show.py 0 98 --rows 64 --sound   # 64x64, with the music (afplay, on a Mac)
    python3 tools/loop_show.py 98 137 --version v1      # another part, another version

Run it from a folder whose emulator_config.json sets the browser port (the repo root's is 8888), so
two boards can loop side by side; fonts and config.json resolve from there too. The music clip is
cut once into build/loop_show/ (gitignored). Needs ffmpeg for --sound.
"""
import argparse
import logging
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SHOW = "happily-ever-after"


def offset_clock(start_s, now=time.monotonic):
    """A clock for render_music_show that starts the show start_s seconds in: the show counts from
    its first reading of the clock, so that one reading is start_s seconds early."""
    first = [True]

    def clock():
        t = now()
        if first[0]:
            first[0] = False
            return t - start_s
        return t
    return clock


def clip_path(start_s, end_s, show=SHOW):
    """Where the music for this part is cut to."""
    return os.path.join(ROOT, "build", "loop_show", f"{show}-{start_s:g}-{end_s:g}.wav")


def cut_clip(start_s, end_s, show=SHOW):
    """The music from start_s to end_s, cut once with ffmpeg."""
    path = clip_path(start_s, end_s, show)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start_s), "-to", str(end_s), "-i",
                        os.path.join(ROOT, "sounds", f"{show}.wav"), path], check=True)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("start", type=float, help="seconds into the show to loop from")
    parser.add_argument("end", type=float, help="seconds into the show to loop to")
    parser.add_argument("--rows", type=int, choices=(32, 64), default=32)
    parser.add_argument("--version", default="v2")
    parser.add_argument("--sound", action="store_true", help="play the music too (afplay)")
    args = parser.parse_args(argv)
    if not 0 <= args.start < args.end:
        parser.error("start must be before end")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    import driver
    from cli import arguments, led_matrix_options
    from display.display import initialize_fonts
    from display.fireworks.music_show import render_music_show
    from display.fireworks.score import load_score

    driver.set_mode(driver.DriverMode.SOFTWARE_EMULATION)
    matrix = driver.RGBMatrix(options=led_matrix_options(
        arguments(["--emulated", "--led-cols=64", f"--led-rows={args.rows}"])))
    initialize_fonts(matrix.height)
    score = load_score(SHOW, version=args.version)
    if score is None:
        parser.error(f"no score for {SHOW}")
    score = score._replace(end=min(args.end, score.end))
    clip = cut_clip(args.start, score.end) if args.sound else None
    logging.getLogger("disney-lll").info(f"Looping {SHOW} {args.start:g}-{score.end:g}s ({args.version}).")
    while True:
        player = subprocess.Popen(["afplay", clip]) if clip else None
        try:
            render_music_show(matrix, score, clock=offset_clock(args.start))
        finally:
            if player:
                player.terminate()
                player.wait()


if __name__ == "__main__":
    main()
