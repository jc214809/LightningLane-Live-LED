#!/usr/bin/env python3
"""
Make a mouth track for a character who sings in a synced show: the soundtrack between two seconds,
its vocals split from the music by demucs, turned into one mouth shape per frame (0 closed, 1 half,
2 open) and written to display/fireworks/shows/<show>.<version>.lips.json, which score.py reads for
that version. The board only looks the shape up by the clock, so nothing here runs on a board.

    python3 tools/lip_sync.py genie 525 565 --mute 551-559.7 --close 549.82   # Genie in Friend Like Me

demucs splits all the singing from the music, not one singer from another: --mute the stretches where
someone else sings (the woman's part above), and the mouth stays shut there. An m, b or p sung straight
out of a held note (his first "like me") makes no dip to find: --close shuts the lips there for CLOSE_S.
A word drowned in reverb (Mufasa's last echoing "Remember...") can land in demucs's music instead:
--from-mix reads the mouth from the original mix over that stretch.

Voices are split by demucs's fine-tuned model (htdemucs_ft: the cleanest voice, silent between words,
so the music doesn't move the mouth; --model htdemucs is quicker). demucs (with PyTorch, about 2 GB)
lives in its own venv under build/, not the app's:

    uv venv --python 3.11 build/lipsync-venv
    uv pip install --python build/lipsync-venv demucs==4.0.1 soundfile torch==2.8.0 torchaudio==2.8.0

(torchaudio 2.9+ can't save without torchcodec, so demucs 4.0.1 fails on its last step there.)
Needs ffmpeg and the show's music in sounds/ (gitignored; copy it from a board).
"""
import argparse
import json
import logging
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from display.fireworks.score import SHOWS_DIR  # noqa: E402

WORK_DIR = os.path.join(ROOT, "build", "lipsync")
DEMUCS_PYTHON = os.path.join(ROOT, "build", "lipsync-venv", "bin", "python")
SOUNDS_DIR = os.path.join(ROOT, "sounds")
FPS = 15  # mouth shapes a second: sung syllables come 4-6 a second
RATE = 16000
SUB = 4  # loudness measured SUB times a frame, to catch a syllable starting inside one
SILENT_DB = -35  # quieter than this, the mouth is shut
PEAK_S = 0.2  # each frame is judged against the loudest within this either side...
OPEN_DB, HALF_DB = -4, -10  # ...open within OPEN_DB of it, half within HALF_DB
ONSET_DB = 5  # a rise this sharp into the next frame is a new syllable: an open mouth half-closes first
CLOSE_S = 0.13  # how long --close shuts the lips: an m's hum

logger = logging.getLogger(__name__)


def loudness(samples, rate=RATE, per_s=FPS * SUB):
    """dB of each 1/per_s second of mono samples. Each block starts on its exact sample: a whole number
    of samples a block (rate // per_s) drifts a frame late over half a minute."""
    k = int(len(samples) * per_s / rate)
    edges = np.round(np.arange(k + 1) * rate / per_s).astype(int)
    power = np.asarray(samples, dtype=np.float64) ** 2
    sums = np.add.reduceat(power[:edges[-1]], edges[:-1])
    return 20 * np.log10(np.sqrt(sums / np.diff(edges)) + 1e-6)


def mouth_track(samples, rate=RATE, fps=FPS, muted=(), closes=(), mix=None, from_mix=()):
    """The mouth shape for each 1/fps second of a vocal stem, as a string of 0 (closed), 1 (half) and
    2 (open). Loud against the moment's peak is open, so the mouth moves syllable by syllable rather
    than staying open through a loud phrase. muted: (from, to) seconds into the stem where someone
    else sings; the mouth is shut there. closes: seconds into the stem where the lips meet (an m, b or
    p the loudness can't show), shut for CLOSE_S. from_mix: (from, to) seconds where the voice is in
    `mix` (the original's samples, same rate) rather than the stem; the mouth reads from it there."""
    fine = loudness(samples, rate, fps * SUB)
    if mix is not None and from_mix:
        from_mix_fine = loudness(mix, rate, fps * SUB)
        n = min(len(fine), len(from_mix_fine))
        for a, b in from_mix:
            lo, hi = max(0, int(a * fps * SUB)), min(n, int(b * fps * SUB))
            fine[lo:hi] = from_mix_fine[lo:hi]
    frames = len(fine) // SUB
    db = fine[:frames * SUB].reshape(frames, SUB).mean(1)
    reach = max(1, round(PEAK_S * fps))
    shapes = []
    for i in range(frames):
        peak = db[max(0, i - reach):i + reach + 1].max()
        if db[i] < SILENT_DB:
            shape = 0
        elif db[i] - peak > OPEN_DB:
            shape = 2
        elif db[i] - peak > HALF_DB:
            shape = 1
        else:
            shape = 0
        rise = fine[(i + 1) * SUB:(i + 2) * SUB].max(initial=-999) - fine[i * SUB:(i + 1) * SUB].min()
        if shape == 2 and rise > ONSET_DB:
            shape = 1
        if any(a <= i / fps < b for a, b in muted) or any(c <= (i + 0.5) / fps < c + CLOSE_S for c in closes):
            shape = 0
        shapes.append(shape)
    return "".join(map(str, shapes))


def read_mono(path, rate=RATE):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(rate), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


MODEL = "htdemucs_ft"


def separate_vocals(music, start, end, name, model=MODEL):
    """The vocals of music from start to end seconds, as a wav under WORK_DIR (demucs's two-stem split)."""
    if not os.path.exists(DEMUCS_PYTHON):
        raise RuntimeError(f"demucs isn't installed: see the top of {__file__}")
    os.makedirs(WORK_DIR, exist_ok=True)
    clip = os.path.join(WORK_DIR, f"{name}.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start}", "-t", f"{end - start}", "-i", music,
                    "-ac", "2", "-ar", "44100", clip], check=True)
    out = os.path.join(WORK_DIR, "sep")
    subprocess.run([DEMUCS_PYTHON, "-m", "demucs", "--two-stems", "vocals", "-n", model, "-o", out, clip],
                   check=True, capture_output=True)
    return os.path.join(out, model, name, "vocals.wav")


def write_lips(path, actor, entry):
    """Add or replace one actor's track in the lips file, keeping the others."""
    data = {"note": "Mouth tracks made by tools/lip_sync.py from the vocals: one shape per 1/fps second "
                    "from start (audio seconds), 0 closed, 1 half, 2 open. Don't edit by hand; re-run the tool.",
            "lips": {}}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data["lips"][actor] = entry
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("actor", help="the show_actors.ACTORS name whose mouth moves")
    parser.add_argument("start", type=float, help="audio seconds: where the track starts")
    parser.add_argument("end", type=float, help="audio seconds: where it ends")
    parser.add_argument("--show", default="happily-ever-after")
    parser.add_argument("--version", default="v2")
    parser.add_argument("--model", default=MODEL, help="the demucs model that splits the voice out")
    parser.add_argument("--mute", action="append", default=[], metavar="FROM-TO",
                        help="audio seconds where someone else sings, like 551-559.7 (repeatable)")
    parser.add_argument("--from-mix", action="append", default=[], metavar="FROM-TO",
                        help="audio seconds where the voice is drowned in reverb: read the mouth from the mix")
    parser.add_argument("--close", action="append", default=[], type=float, metavar="SECONDS",
                        help="audio seconds where the lips meet but the loudness doesn't dip (repeatable)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.end <= args.start:
        logger.error("end must be after start")
        return 1
    try:
        muted = [tuple(float(x) for x in m.split("-")) for m in args.mute]
        from_mix = [tuple(float(x) for x in m.split("-")) for m in args.from_mix]
        if any(len(m) != 2 or m[1] <= m[0] for m in muted + from_mix):
            raise ValueError
    except ValueError:
        logger.error("--mute and --from-mix take FROM-TO in audio seconds, like 551-559.7")
        return 1
    music = os.path.join(SOUNDS_DIR, f"{args.show}.wav")
    if not os.path.exists(music):
        logger.error("no %s (gitignored; copy it from a board)", music)
        return 1
    name = f"{args.actor}-{args.start:g}"
    try:
        logger.info("splitting the vocals from %g to %g s...", args.start, args.end)
        vocals = separate_vocals(music, args.start, args.end, name, args.model)
        mix = read_mono(os.path.join(WORK_DIR, f"{name}.wav")) if from_mix else None
        track = mouth_track(read_mono(vocals), muted=[(a - args.start, b - args.start) for a, b in muted],
                            closes=[c - args.start for c in args.close], mix=mix,
                            from_mix=[(a - args.start, b - args.start) for a, b in from_mix])
    except (OSError, RuntimeError, subprocess.CalledProcessError) as e:
        logger.error("%s", e)
        return 1
    path = os.path.join(SHOWS_DIR, f"{args.show}.{args.version}.lips.json")
    entry = {"start": args.start, "fps": FPS, "track": track}
    # A record of how it was made, for re-running; the board ignores them.
    if muted:
        entry["muted"] = [list(m) for m in muted]
    if args.close:
        entry["closes"] = args.close
    if from_mix:
        entry["from_mix"] = [list(m) for m in from_mix]
    write_lips(path, args.actor, entry)
    for s in range(0, len(track), FPS):
        logger.info("%6.0f %s", args.start + s / FPS, track[s:s + FPS].translate(str.maketrans("012", "_-O")))
    logger.info("wrote %s (%d shapes)", path, len(track))
    return 0


if __name__ == "__main__":
    sys.exit(main())
