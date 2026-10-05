#!/usr/bin/env python3
"""
Measure a reference image in docs/references/ and print a draft row for its README table: size in
cells, whether it fits each board as is, and its colours. The grid is found the way the sprite editor's
Pattern mode finds it (its JS core, run under Node), so the tool and the editor read an image the same.

    python3 tools/analyze_reference.py docs/references/Forky.jpg
    python3 tools/analyze_reference.py <image> --box 435,275,665,590   # one character on a sheet
    python3 tools/analyze_reference.py <image> --lines --art           # chart over a picture; print the sprite
    python3 tools/analyze_reference.py --missing                       # images with no README row

--missing needs only the standard library (the SessionStart hook runs it with whatever python3 is
on the PATH). Measuring needs Pillow and Node.
"""
import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCES = os.path.join(ROOT, "docs", "references")
README = os.path.join(REFERENCES, "README.md")
EDITOR = os.path.join(ROOT, "tools", "sprite_editor.html")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
# findGrid's score is the edge profile's autocorrelation at one cell: near 0 is no grid.
MIN_GRID_SCORE = .15
# LED cells are square: column and row sizes this far apart are a misread (a whole sheet, a pin photo).
MAX_CELL_ASPECT = 1.15
# A separate piece this many cells or more counts as a character, not a stray cell of backdrop.
MIN_PIECE_CELLS = 40
# README's Tight: the character fills the board's height, or is within a row or two of it.
TIGHT_ROWS = 2

logger = logging.getLogger(__name__)


# ---- Which images have a README row (stdlib only) ----

def readme_links(readme_text):
    """The files the README table's rows link to, from each row's first cell."""
    links = re.findall(r"^\|\s*\[[^\]]*\]\(([^)]*)\)", readme_text, re.M)
    return {urllib.parse.unquote(link.strip("<>")) for link in links}


def reference_images(folder=None):
    return sorted(f for f in os.listdir(folder or REFERENCES) if os.path.splitext(f)[1].lower() in IMAGE_EXTS)


def missing_rows(folder=None):
    """Reference images the README table has no row for."""
    folder = folder or REFERENCES
    with open(os.path.join(folder, "README.md"), encoding="utf-8") as f:
        linked = readme_links(f.read())
    return [f for f in reference_images(folder) if f not in linked]


def missing_report(missing):
    """What the SessionStart hook prints: nothing when every image has a row."""
    if not missing:
        return ""
    names = "\n".join(f"- docs/references/{f}" for f in missing)
    return (f"These reference images have no row in docs/references/README.md yet:\n{names}\n"
            "Before other work, measure each with `python3 tools/analyze_reference.py <image>` (one row per "
            "character: `--box x0,y0,x1,y1` for each on a sheet), look at the image, fill in who it shows, "
            "and add the rows. tests/tools/test_analyze_reference.py fails until they're there.")


# ---- From the editor's reading to a README row ----

def fits_64x32(w, h):
    if w > 64:
        return f"No ({w - 64} columns too wide)"
    if h > 32:
        over = h - 32
        return f"No ({over} row{'s' if over > 1 else ''} over)"
    return "Tight" if h > 32 - TIGHT_ROWS - 1 else "Yes"


def fits_64x64(w, h):
    if w > 64 or h > 64:
        parts = [f"{w - 64} columns too wide" if w > 64 else "", f"{h - 64} rows too tall" if h > 64 else ""]
        return f"No ({', '.join(p for p in parts if p)})"
    if h > 64 - TIGHT_ROWS - 1:
        return "Tight"
    return "Yes (2x too)" if w <= 32 and h <= 32 else "Yes"


def pieces(rows, min_cells=MIN_PIECE_CELLS):
    """Sizes (w, h) of the separate pieces of lit cells big enough to be a character, largest first."""
    lit = {(x, y) for y, row in enumerate(rows) for x, k in enumerate(row) if k != "."}
    found = []
    while lit:
        stack, cells = [lit.pop()], []
        while stack:
            x, y = stack.pop()
            cells.append((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in lit:
                    lit.remove(n)
                    stack.append(n)
        if len(cells) >= min_cells:
            xs, ys = [c[0] for c in cells], [c[1] for c in cells]
            found.append((len(cells), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
    return [(w, h) for _, w, h in sorted(found, reverse=True)]


def _rgb_hex(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def grid_found(reading):
    """Whether the reading found a believable grid: both axes repeat, with square cells."""
    fx, fy = reading.get("fx"), reading.get("fy")
    if not fx or not fy or min(fx["score"], fy["score"]) < MIN_GRID_SCORE:
        return False
    big, small = max(fx["period"], fy["period"]), min(fx["period"], fy["period"])
    return big <= small * MAX_CELL_ASPECT


def draft_row(name, reading):
    """The README row and the notes under it, from what read_image() returned."""
    link = f"[{name}](<{name}>)" if " " in name else f"[{name}]({name})"
    fx, fy = reading.get("fx"), reading.get("fy")
    if not grid_found(reading):
        row = (f"| {link} | TODO: who it shows | | Needs tracing | Needs tracing | "
               f"No grid found: trace it, or Pattern mode's Calibrate (two clicks on cell middles) |")
        return row, ["No reliable grid: a photo with no cells to count (trace it), a sheet whose characters each "
                     "sit on their own grid (measure each with --box x0,y0,x1,y1), or one the detection misses "
                     "(tools/sprite_editor.html, Image to pixels, Pattern mode, Calibrate)."]
    rows = reading["rows"]
    if not rows:
        return f"| {link} | TODO: who it shows | | | | |", ["A grid, but nothing on it once the background is dropped."]
    w, h = len(rows[0]), len(rows)
    notes = [f"Grid: {fx['period']:.1f} x {fy['period']:.1f} px cells (score {min(fx['score'], fy['score']):.2f})."]
    how = "Pattern mode reads it"
    if reading.get("turn"):
        notes.append(f"Turned {reading['turn']:g} degrees to straighten it: a photo shot at a tilt.")
        how += " (Detect grid straightens it)"
    if reading.get("box"):
        how = "Pattern mode: drag a box round it" + (", tick Grid lines only" if reading.get("lines") else "")
    elif reading.get("lines"):
        how += ", with Grid lines only"
    found = pieces(rows)
    if len(found) > 1:
        sizes = ", ".join(f"{pw} x {ph}" for pw, ph in found)
        notes.append(f"{len(found)} separate pieces ({sizes}): probably a sheet. Give each character its own row, "
                     "measured with --box x0,y0,x1,y1 (pixels of the image).")
    colors = reading.get("colors", {})
    notes.append("Colours: " + ", ".join(f"{k} {_rgb_hex(c)}" for k, c in colors.items()))
    if reading.get("extraColors"):
        notes.append(f"{reading['extraColors']} more colour groups than keys: raise the merge in the editor.")
    row = f"| {link} | TODO: who it shows | {w} x {h} | {fits_64x32(w, h)} | {fits_64x64(w, h)} | {how} |"
    return row, notes


# ---- Reading the image with the editor's core under Node ----

def _core():
    with open(EDITOR, encoding="utf-8") as f:
        return re.search(r'<script id="core">(.*?)</script>', f.read(), re.S).group(1)


_PIPELINE = """
const fs = require("fs"), opt = %s;
let data = new Uint8ClampedArray(fs.readFileSync(opt.raw)), W = opt.W, H = opt.H;
if (opt.box) ({ data, W, H } = cropImage(data, W, H, opt.box));
const turn = opt.turn ? gridTurn(data, W, H) : 0;
if (turn) ({ data, W, H } = rotateImage(data, W, H, turn));
const prof = edgeProfiles(data, W, H), fx = findGrid(prof.x), fy = findGrid(prof.y);
let out = { turn, fx, fy, rows: [], colors: {}, extraColors: 0 };
if (fx && fy) {
  const { offsetX, offsetY } = alignGrid(data, W, H, fx.period, fy.period, fx.offset, fy.offset);
  const gx = gridCells(W, fx.period, offsetX), gy = gridCells(H, fy.period, offsetY);
  const p = buildPattern(sampleCells(data, W, H, gx, gy), { lined: opt.lines ? gridLineCells(data, W, H, gx, gy) : null });
  Object.assign(out, { rows: p.rows, colors: p.colors, extraColors: p.extraColors });
  if (opt.art) out.art = exportArt(p.rows, opt.name, "") + "\\n\\n" + exportColors(p.colors, opt.palette, "");
}
console.log(JSON.stringify(out));
"""


def read_image(path, box=None, lines=False, turn=True, art=False, name="ART", palette="COLORS"):
    """Run Pattern mode's pipeline on an image: crop, straighten, find the grid, read the cells."""
    from PIL import Image  # only measuring needs Pillow, not --missing
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node isn't installed: the grid detection is the sprite editor's JS core")
    im = Image.open(path).convert("RGBA")
    with tempfile.NamedTemporaryFile(suffix=".rgba", delete=False) as raw:
        raw.write(im.tobytes())
    try:
        opt = {"raw": raw.name, "W": im.width, "H": im.height, "box": list(box) if box else None,
               "lines": lines, "turn": turn, "art": art, "name": name, "palette": palette}
        # On stdin: the core embeds every sprite and is past Linux's limit for one argument.
        out = subprocess.run([node], input=_core() + "\n" + _PIPELINE % json.dumps(opt),
                             capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(raw.name)
    if out.returncode != 0:
        raise RuntimeError(f"the editor's core failed under Node: {out.stderr.strip()[-500:]}")
    reading = json.loads(out.stdout)
    reading.update(box=box, lines=lines)
    return reading


def _box(text):
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box takes x0,y0,x1,y1")
    return parts


def main(argv=None):
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("image", nargs="?", help="the reference image to measure")
    parser.add_argument("--missing", action="store_true", help="list reference images with no README row")
    parser.add_argument("--box", type=_box, help="measure only this box, x0,y0,x1,y1 in image pixels")
    parser.add_argument("--lines", action="store_true", help="Grid lines only: art drawn over a picture")
    parser.add_argument("--no-turn", dest="turn", action="store_false", help="don't straighten a tilted photo")
    parser.add_argument("--art", action="store_true", help="also print the sprite rows and palette to paste")
    parser.add_argument("--name", default="ART", help="the art's name in --art's output (default ART)")
    parser.add_argument("--palette", default="COLORS", help="the palette's name in --art's output")
    args = parser.parse_args(argv)

    if args.missing:
        try:
            report = missing_report(missing_rows())
        except OSError as e:  # a hook must not break the session over a moved folder
            logger.warning("couldn't check docs/references: %s", e)
            return 0
        if report:
            print(report)
        return 0
    if not args.image:
        parser.error("give an image, or --missing")
    try:
        reading = read_image(args.image, box=args.box, lines=args.lines, turn=args.turn, art=args.art,
                             name=args.name, palette=args.palette)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        logger.error("%s: %s", args.image, e)
        return 1
    row, notes = draft_row(os.path.basename(args.image), reading)
    print(row)
    for note in notes:
        print(f"  {note}")
    if args.art and reading.get("art"):
        print()
        print(reading["art"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
