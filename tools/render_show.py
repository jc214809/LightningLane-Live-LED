#!/usr/bin/env python3
"""
Record a synced fireworks show as the boards draw it, for tools/show_sync_checker.html: the real
show code (display/fireworks/music_show.py) run ahead of time at the board's 30 fps, written to a
video of the LED panel (each LED a small square; the page draws them round), with the show's music
on it. Nothing here changes the show.

    python3 tools/render_show.py                    # both boards, plus the page's data file
    python3 tools/render_show.py --recording        # also download the real show's recording
    python3 tools/render_show.py --height 64        # one board only
    python3 tools/render_show.py --version v2       # a later version (its overlay file, see score.py)

Writes to build/show_sync/ (gitignored): <show>-64x32.mp4, <show>-64x64.mp4, <show>.js (the score,
for the page) and, with --recording, <show>-recording.mp4. A later version is named <show>.v2-64x32.mp4
and so on; open the page with ?show=<show>.v2. Re-run it after changing the score: the
whole show renders in about a minute. Needs ffmpeg (and yt-dlp for --recording) on the PATH.
"""
import argparse
import json
import logging
import os
import random
import shutil
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from display.fireworks.music_show import MusicShow  # noqa: E402
from display.fireworks.score import SHOWS_DIR, load_score, parse_lips, parse_score  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build", "show_sync")
SOUNDS_DIR = os.path.join(ROOT, "sounds")
FPS = 30  # render_music_show's frame rate
WIDTH = 64
HEIGHTS = (32, 64)
# Each LED is a 4x4 square: whole 2x2 colour blocks in the video's 4:2:0 encoding, so no LED's colour
# bleeds into the next, and flat squares compress to a few MB.
LED_PX = 4
SEED = 1  # the bursts are random: a seed makes every render of a score the same

logger = logging.getLogger(__name__)


def panel_image(pixels, width, height, px=LED_PX):
    """One frame ({(x, y): rgb}, as MusicShow.frame_pixels gives it) as height*px rows of width*px RGB
    pixels, each LED a px x px square; unlit LEDs are black."""
    leds = np.zeros((height, width, 3), np.uint8)
    for (x, y), rgb in pixels.items():
        leds[y, x] = rgb
    return leds.repeat(px, 0).repeat(px, 1)


def frames(score, height, fps=FPS, seed=SEED, seconds=None):
    """Every frame of the show on a 64 x height board, as the board steps it: the scene at each frame's
    time, then one simulation step, then the picture. seconds stops early (for tests)."""
    show = MusicShow(WIDTH, height, random.Random(seed), score.lips)
    for i in range(int((seconds if seconds is not None else score.end) * fps)):
        t = i / fps
        show.set_cue(score.cue_at(t), t)
        show.step()
        yield show.frame_pixels()


def ffmpeg_command(out, width, height, fps, audio=None, seconds=None):
    """ffmpeg reading raw RGB frames on stdin and writing an mp4 that seeks well, with the music if given."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{width}x{height}", "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "160k"]
    if seconds is not None:
        cmd += ["-t", f"{seconds:.3f}"]
    # A keyframe every second, so the page can jump anywhere without a wait.
    return cmd + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                  "-g", str(fps), "-movflags", "+faststart", out]


def render(score, height, out, audio=None, fps=FPS):
    """Write the show on a 64 x height board to out."""
    cmd = ffmpeg_command(out, WIDTH * LED_PX, height * LED_PX, fps, audio, score.end)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for pixels in frames(score, height, fps):
            proc.stdin.write(panel_image(pixels, WIDTH, height).tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code:
        raise RuntimeError(f"ffmpeg failed ({code}) writing {out}")


def sync_data(score, raw, boards, recording_file=None, version="v1"):
    """What the page needs, as a dict: the scenes (with what the board does in each), the sections'
    colours, the board videos, and how the recording's clock maps onto the show's."""
    by_title = {sc["title"]: (sec, sc) for sec in raw["sections"] for sc in sec["scenes"]}
    scenes = []
    for cue in score.cues:
        sec, sc = by_title[cue.title]
        scenes.append({"title": cue.title, "section": cue.section, "start": cue.start, "end": cue.end,
                       "castle": cue.castle, "effects": sorted(cue.effects), "rate": round(cue.rate, 2),
                       "stage": cue.stage, "actors": list(cue.actors), "characters": sc.get("characters", [])})
    rec = raw.get("recording")
    return {
        "name": score.name, "version": version, "end": score.end, "fps": FPS, "boards": boards,
        "sections": [{"id": s["id"], "start": s["start"], "end": s["end"], "palette": s["palette"]}
                     for s in raw["sections"]],
        "scenes": scenes,
        "recording": dict(rec, file=recording_file) if rec and recording_file else None,
    }


def write_sync_js(data, path):
    """The page's data as a script, so the page works opened straight from disk (no server, no fetch)."""
    with open(path, "w") as f:
        f.write("window.SHOW_SYNC = " + json.dumps(data, indent=1) + ";\n")


def download_recording(url, out):
    """The real show's recording (H.264 up to 1080p, which every browser plays; not AV1, which Safari often
    can't) from its video page, unless it's already there."""
    if os.path.exists(out):
        logger.info("recording already downloaded: %s", out)
        return
    if shutil.which("yt-dlp") is None:
        raise RuntimeError("yt-dlp isn't installed: brew install yt-dlp")
    logger.info("downloading the recording...")
    subprocess.run(["yt-dlp", "-q", "-f", "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/b[vcodec^=avc1]/b[ext=mp4]",
                    "--merge-output-format", "mp4", "-o", out, url], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--show", default="happily-ever-after", help="the show's clip name (its score's file name)")
    parser.add_argument("--height", type=int, choices=HEIGHTS, action="append", help="one board (default both)")
    parser.add_argument("--recording", action="store_true", help="also download the real show's recording")
    parser.add_argument("--version", default="v1", help="the show's version: v1, or a later one's overlay file")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if shutil.which("ffmpeg") is None:
        logger.error("ffmpeg isn't installed: brew install ffmpeg")
        return 1
    score = load_score(args.show)
    if score is None:
        logger.error("no usable score for %s in %s", args.show, SHOWS_DIR)
        return 1
    with open(os.path.join(SHOWS_DIR, f"{args.show}.json")) as f:
        raw = json.load(f)
    tag = args.show
    if args.version != "v1":
        # Parsed here rather than through load_score, which plays V1 on a bad overlay: say what's wrong.
        tag = f"{args.show}.{args.version}"
        try:
            with open(os.path.join(SHOWS_DIR, f"{tag}.json")) as f:
                score = parse_score(args.show, raw, json.load(f))
            lips_path = os.path.join(SHOWS_DIR, f"{tag}.lips.json")
            if os.path.exists(lips_path):
                with open(lips_path) as f:
                    score = score._replace(lips=parse_lips(json.load(f)))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
            logger.error("can't use %s's %s: %r", args.show, args.version, e)
            return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    audio = os.path.join(SOUNDS_DIR, f"{args.show}.wav")
    if not os.path.exists(audio):
        logger.warning("no %s (gitignored; copy it from a board): the videos will be silent", audio)
        audio = None

    boards = {}
    for height in args.height or HEIGHTS:
        name = f"{tag}-{WIDTH}x{height}.mp4"
        logger.info("rendering %s (%.0f s of show)...", name, score.end)
        try:
            render(score, height, os.path.join(OUT_DIR, name), audio)
        except (OSError, RuntimeError) as e:
            logger.error("%s", e)
            return 1
        boards[f"{WIDTH}x{height}"] = name
    # Keep boards rendered on an earlier run listed for the page.
    for height in HEIGHTS:
        name = f"{tag}-{WIDTH}x{height}.mp4"
        if f"{WIDTH}x{height}" not in boards and os.path.exists(os.path.join(OUT_DIR, name)):
            boards[f"{WIDTH}x{height}"] = name

    rec_name = f"{args.show}-recording.mp4"
    if args.recording:
        if not raw.get("recording"):
            logger.error("the score has no \"recording\" entry to download")
            return 1
        try:
            download_recording(raw["recording"]["url"], os.path.join(OUT_DIR, rec_name))
        except (OSError, RuntimeError, subprocess.CalledProcessError) as e:
            logger.error("couldn't download the recording: %s", e)
            return 1
    have_rec = os.path.exists(os.path.join(OUT_DIR, rec_name))
    write_sync_js(sync_data(score, raw, boards, rec_name if have_rec else None, args.version),
                  os.path.join(OUT_DIR, f"{tag}.js"))
    page = os.path.join(ROOT, "tools", "show_sync_checker.html") + ("" if tag == args.show else f"?show={tag}")
    logger.info("done. Open %s%s", page, "" if have_rec else " (add --recording for the real show beside it)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
