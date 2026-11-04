"""Rewrite each WATCH.md scene's heading, Audio/Video line and "Our score now" line from the score, so /watch
asks about what the board does now. Scenes pair up in order; answers, checks and notes are left alone.

    python3 docs/shows/happily-ever-after/sync_headers.py
"""
import json, math, re

WATCH = "docs/shows/happily-ever-after/WATCH.md"
SCORE = "display/fireworks/shows/happily-ever-after.json"


def mmss(x):
    return f"{int(x // 60)}:{int(x % 60):02d}"


def video(a):  # README.md, Clock
    return a * 1.001 + 10.19


def header(num, scene):
    a, b = scene["start"], scene["end"]
    chars = ", ".join(scene["characters"]) or "none"
    return (f"### {num} {scene['title']}\n\n"
            f"- **Audio:** {a:g}-{b:g} s ({mmss(a)}-{mmss(b)}, {round(b - a, 1):g} s) · "
            f"**Video:** `--start {mmss(math.floor(video(a)))} --end {mmss(math.floor(video(b)))}`\n"
            f"- **Our score now:** {scene['look'].rstrip('.')}. Characters: {chars}.\n")


def main():
    s = open(WATCH).read()
    scenes = [x for sec in json.load(open(SCORE))["sections"] for x in sec["scenes"]]
    pat = re.compile(r"^### (\S+) .+\n\n- \*\*Audio:\*\*.*\n- \*\*Our score now:\*\*.*\n", re.M)
    nums = [m.group(1) for m in pat.finditer(s)]
    if len(nums) != len(scenes):
        raise SystemExit(f"WATCH.md has {len(nums)} scenes, the score {len(scenes)}: add or remove a section first")
    by_num = dict(zip(nums, scenes))
    open(WATCH, "w").write(pat.sub(lambda m: header(m.group(1), by_num[m.group(1)]), s))
    print(f"synced {len(nums)} scenes")


if __name__ == "__main__":
    main()
