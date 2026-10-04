import importlib.util
import json
import os
import re
import shutil
import subprocess

import pytest

import display.animation as animation

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("build_sprite_editor", os.path.join(ROOT, "tools", "build_sprite_editor.py"))
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="the editor's JS core runs under Node")


@pytest.fixture(scope="module")
def sprites():
    return builder.collect_sprites(animation)


def test_collects_both_slinky_halves_with_their_palette(sprites):
    for attr in ("FRONT_ART", "REAR_ART"):
        s = sprites[f"slinky/{attr}"]
        assert s["rows"] == getattr(animation.SlinkyReveal, attr)
        assert s["palette_attr"] == "COLORS"
        assert s["colors"]["K"] == list(animation.SlinkyReveal.COLORS["K"])


def test_fixed_size_sprites_carry_their_scale(sprites):
    assert sprites["genie/LAMP_ART"]["scale"] == animation.GenieReveal.LAMP_SCALE == 1
    assert sprites["genie/ART"]["scale"] is None, "Genie himself doubles on 64-row boards"


class _Generated:
    """A character with one named pose, one built at import time, and a placeholder key in its base art."""
    _BASE = ["K##K", "KKKK"]
    POSE_ART = ["KWPK", "KKKK"]
    art = [POSE_ART, ["KPWK", "KKKK"]]
    colors = {"K": (0, 0, 0), "W": (255, 255, 255), "P": (60, 60, 90)}


def _generated_sprites():
    return builder.collect_sprites(type("Animation", (), {"TRANSITIONS": {"gen": _Generated}}))


def test_aliases_appear_once_and_animation_frames_are_split(sprites):
    assert "dumbo/EARS_UP" in sprites and "dumbo/art" not in sprites, "art = EARS_UP is one sprite"
    generated = _generated_sprites()
    assert "gen/POSE_ART" in generated and "gen/art[0]" not in generated, "a named pose in art appears once, by name"
    assert "gen/art[1]" in generated, "an unnamed frame is editable too"
    assert {s["character"] for s in sprites.values()} >= {"tink", "buzz", "genie", "mickey", "ralph", "dumbo"}


def test_every_key_has_a_color_and_placeholders_are_flagged(sprites):
    for sid, s in sprites.items():
        used = {ch for row in s["rows"] for ch in row} - {"."}
        assert used <= set(s["colors"]), sid
    base = _generated_sprites()["gen/_BASE"]
    assert base["unmapped"] == ["#"], "a slot filled at draw time is flagged"
    assert base["colors"]["#"] == builder.UNMAPPED_RGB


def test_checked_in_editor_matches_the_current_art(sprites):
    with open(builder.EDITOR, encoding="utf-8") as f:
        embedded = builder.embedded_sprites(f.read())
    assert embedded == json.loads(json.dumps(sprites)), \
        "character art changed: run python3 tools/build_sprite_editor.py"


def test_build_rewrites_only_the_sprite_block(tmp_path):
    page = tmp_path / "editor.html"
    page.write_text(f"<p>before</p><script>const S = {builder.BEGIN}{{}}{builder.END};</script><p>after</p>")
    count = builder.build(str(page), animation)
    html = page.read_text()
    assert count == len(builder.embedded_sprites(html)) > 10
    assert html.startswith("<p>before</p><script>const S = ") and html.endswith(";</script><p>after</p>")
    builder.build(str(page), animation)
    assert page.read_text() == html, "rebuilding unchanged art is a no-op"


def _run_core(body):
    with open(builder.EDITOR, encoding="utf-8") as f:
        core = re.search(r'<script id="core">(.*?)</script>', f.read(), re.S).group(1)
    # The script goes in on stdin: with every sprite embedded it's past Linux's limit for one argument.
    out = subprocess.run([NODE], input=core + "\n" + body, capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


@needs_node
def test_export_then_import_round_trips_every_sprite(sprites):
    result = _run_core(f"""
        const sprites = {json.dumps(sprites)}, bad = [];
        for (const [id, s] of Object.entries(sprites)) {{
          const p = parseSprite(exportArt(s.rows, s.attr) + "\\n" + exportColors(s.colors, s.palette_attr));
          if (JSON.stringify(p.rows) !== JSON.stringify(s.rows) || JSON.stringify(p.colors) !== JSON.stringify(s.colors)
              || p.name !== s.attr || p.paletteName !== s.palette_attr) bad.push(id);
        }}
        console.log(JSON.stringify(bad));""")
    assert result == []


@needs_node
def test_import_reads_json_bare_rows_and_art_without_colors():
    result = _run_core("""
        console.log(JSON.stringify([
          parseSprite('{"rows": ["AB", ".A"], "colors": {"A": [1, 2, 3]}}'),
          parseSprite("..K..\\n.KYK.\\nKYYYK"),
          parseSprite('HEAD = [\\n    "K.K",\\n    ".K.",\\n]'),
        ]));""")
    as_json, bare, art_only = result
    assert as_json["rows"] == ["AB", ".A"] and as_json["colors"] == {"A": [1, 2, 3]}
    assert bare["rows"] == ["..K..", ".KYK.", "KYYYK"]
    assert art_only == {"rows": ["K.K", ".K."], "colors": None, "name": "HEAD", "paletteName": None}


@needs_node
def test_contrast_check_catches_a_feature_lost_in_its_outline():
    """Slinky's first nose: dark on the muzzle, but touching an outline it matched."""
    result = _run_core("""
        const colors = {K: [35, 22, 14], N: [28, 24, 24], T: [232, 196, 138]};
        console.log(JSON.stringify([
          contrastIssues(["TKT", "TNT", "TTT"], colors),
          contrastIssues(["TTT", "TNT", "TTT"], colors),
        ]));""")
    lost, fine = result
    assert {"kind": "touch", "a": "K", "b": "N", "distance": 19} in lost
    assert not [i for i in fine if i["kind"] == "touch"], "the same nose ringed by muzzle is fine"
    assert any(i["kind"] == "dark" and i["a"] == "K" for i in lost), "and K sinks into the black board"


@needs_node
def test_fill_color_conversion_and_nearest_key():
    result = _run_core("""
        const cells = ["..K", ".KK", "..."].map(r => [...r]);
        const n = floodFill(cells, 0, 0, "Y");
        console.log(JSON.stringify({
          n, cells: cells.map(r => r.join("")),
          same: floodFill(cells, 0, 0, "Y"),
          rgb: [[250, 200, 60], [46, 28, 16], [0, 0, 0], [255, 255, 255]].map(c => hsvToRgb(...rgbToHsv(c))),
          hex: [rgbToHex([250, 200, 60]), hexToRgb("#fac83c"), hexToRgb("nope")],
          nearest: nearestKey([240, 190, 70], {K: [46, 28, 16], Y: [250, 200, 60]}),
        }));""")
    assert result["n"] == 6 and result["cells"] == ["YYK", "YKK", "YYY"]
    assert result["same"] == 0, "filling a region with its own key does nothing"
    assert result["rgb"] == [[250, 200, 60], [46, 28, 16], [0, 0, 0], [255, 255, 255]]
    assert result["hex"] == ["#fac83c", [250, 200, 60], None]
    assert result["nearest"] == "Y"


# A heart in red with a blue centre: what the synthetic images below draw, one letter per cell.
_PATTERN = [
    ".RR.RR.",
    "RRRRRRR",
    "RRRBRRR",
    ".RRRRR.",
    "..RRR..",
    "...R...",
]
_PATTERN_JS = """
const PATTERN = %s, INK = {R: [220, 30, 40], B: [30, 60, 220]};
// Seeded noise, so a failure reproduces.
let seed = 7;
const noise = amp => { seed = (seed * 1103515245 + 12345) %% 2147483648; return Math.round((seed / 2147483648 - .5) * 2 * amp); };
function image(W, H, paint) {
  const data = new Uint8ClampedArray(W * H * 4);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) data.set([...paint(x, y), 255], (y * W + x) * 4);
  return data;
}
// A printed chart: white paper, a 1px grey line between cells, and a margin round the grid.
function chart(P, off, cols, rows) {
  const W = Math.ceil(off + cols * P + 9), H = Math.ceil(off + rows * P + 9);
  const data = image(W, H, (x, y) => {
    const cx = (x - off) / P, cy = (y - off) / P;
    if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) return [255, 255, 255];
    if (Math.abs(cx - Math.round(cx)) * P < .6 || Math.abs(cy - Math.round(cy)) * P < .6) return [90, 90, 90];
    const k = (PATTERN[Math.floor(cy) - 1] || "")[Math.floor(cx) - 1];
    return INK[k] || [255, 255, 255];
  });
  return { data, W, H };
}
// A bead photo: round beads with holes, on a grey pegboard, with sensor noise.
function beads(P, off, cols, rows) {
  const W = Math.ceil(off + cols * P), H = Math.ceil(off + rows * P);
  const data = image(W, H, (x, y) => {
    const cx = (x - off) / P, cy = (y - off) / P, r = Math.hypot(cx - Math.floor(cx) - .5, cy - Math.floor(cy) - .5);
    const k = (PATTERN[Math.floor(cy) - 1] || "")[Math.floor(cx) - 1], base = INK[k] || [120, 120, 125];
    const c = r < .14 || r > .47 ? [40, 40, 45] : base;
    return c.map(v => v + noise(14));
  });
  return { data, W, H };
}
function read({ data, W, H }, options) {
  const prof = edgeProfiles(data, W, H), fx = findGrid(prof.x), fy = findGrid(prof.y);
  const { offsetX, offsetY } = alignGrid(data, W, H, fx.period, fy.period, fx.offset, fy.offset);
  const gx = gridCells(W, fx.period, offsetX), gy = gridCells(H, fy.period, offsetY);
  const result = buildPattern(sampleCells(data, W, H, gx, gy), options);
  return { fx, fy, gx, gy, rows: result.rows, keys: Object.keys(result.colors), colors: result.colors };
}
""" % json.dumps(_PATTERN)


@needs_node
def test_pattern_mode_reads_a_chart_with_fractional_cells_and_a_margin():
    result = _run_core(_PATTERN_JS + "console.log(JSON.stringify(read(chart(11.5, 6, 9, 8))));")
    for axis, cells in (("fx", 9), ("fy", 8)):
        assert abs(result[axis]["period"] - 11.5) * cells < 1, "under a pixel of drift across the grid"
        assert abs(result[axis]["offset"] - 6.5) < .5, "boundaries on the middle of the 1px lines"
    assert result["rows"] == _PATTERN, "the paper is dropped and the art trimmed to the heart"
    assert result["keys"] == ["R", "B"], "most-used first, named for their color"


@needs_node
def test_pattern_mode_reads_a_noisy_bead_photo():
    result = _run_core(_PATTERN_JS + "console.log(JSON.stringify(read(beads(14, 3, 9, 8))));")
    assert abs(result["fx"]["period"] - 14) * 9 < 1
    assert result["rows"] == _PATTERN, "holes, gaps and noise don't change a bead's color"
    r, g, b = result["colors"]["R"]
    assert abs(r - 220) + abs(g - 30) + abs(b - 40) < 30


@needs_node
def test_build_pattern_drops_the_background_merges_shades_and_keeps_it_on_request():
    result = _run_core("""
        const W = [250, 250, 250], R1 = [200, 20, 20], R2 = [215, 30, 25], K = [10, 10, 10];
        const cells = [[W, W, W, W], [W, R1, R2, W], [W, K, null, W], [W, W, W, W]];
        console.log(JSON.stringify([
          buildPattern(cells, {background: 60, merge: 40}),
          buildPattern(cells, {background: 0, merge: 40}),
          buildPattern(cells, {background: 60, merge: 10}),
          buildPattern([[W, W], [W, W]]),
        ]));""")
    dropped, kept, unmerged, blank = result
    assert dropped["rows"] == ["RR", "K."], "two close reds share a key; a transparent cell is empty"
    assert kept["rows"][0] == "WWWW" and set(kept["colors"]) == {"W", "R", "K"}, "background 0 keeps the paper"
    assert len(unmerged["colors"]) == 3 and set(unmerged["rows"][0]) == {"R", "r"}, "a tight merge gives each red its own key"
    assert blank["rows"] == [], "an all-background image has nothing to apply"


@needs_node
def test_build_pattern_keeps_enclosed_background_and_follows_lighting():
    result = _run_core("""
        const W = [250, 250, 250], K = [10, 10, 10], _ = null;
        // Mickey-style eyes: white walled in by the outline. And a board that brightens left to right.
        const eyes = [[W, W, W, W, W], [W, K, K, K, W], [W, K, W, K, W], [W, K, K, K, W], [W, W, W, W, W]];
        const lit = v => [v, v, v + 5], R = [220, 30, 40];
        const board = [[lit(100), lit(115), lit(130), lit(145), lit(160)], [lit(100), R, R, R, lit(160)], [lit(100), lit(115), lit(130), lit(145), lit(160)]];
        // Transparent round the edge: the outline touching it is art, not background.
        const sprite = [[_, K, _], [K, R, K], [_, K, _]];
        console.log(JSON.stringify([
          buildPattern(eyes).rows, buildPattern(eyes, {enclosed: false}).rows,
          buildPattern(board).rows, buildPattern(board, {enclosed: false}).rows,
          buildPattern(sprite).rows,
        ]));""")
    eyes, eyes_all, board, board_global, sprite = result
    assert eyes == ["KKK", "KWK", "KKK"], "the walled-in white stays lit"
    assert eyes_all == ["KKK", "K.K", "KKK"], "unless enclosed background is dropped too"
    assert board == ["RRR"], "the flood follows the board as it brightens"
    assert len(board_global[0]) > 3, "one global match leaves the bright side of the board lit"
    assert sprite == [".K.", "KRK", ".K."]


@needs_node
def test_pattern_mode_stays_on_a_big_grid_to_its_far_edge():
    result = _run_core(_PATTERN_JS + "console.log(JSON.stringify(read(chart(18.3, 20, 64, 64))));")
    assert abs(result["fx"]["period"] - 18.3) * 64 < 1 and abs(result["fy"]["period"] - 18.3) * 64 < 1
    assert result["rows"] == _PATTERN


@needs_node
def test_find_grid_gives_up_on_an_image_too_small_for_four_cells():
    assert _run_core("console.log(JSON.stringify(findGrid([1, 5, 1, 5, 1, 5, 1, 5, 1, 5])));") is None


@needs_node
def test_keep_ratio_fills_in_the_other_side_and_stops_at_64():
    result = _run_core("""
        console.log(JSON.stringify([
          ratioSize(16, 13, 32, "width"), ratioSize(16, 13, 26, "height"),
          ratioSize(16, 13, 8, "width"), ratioSize(13, 16, 64, "width"), ratioSize(1, 3, 1, "width"),
        ]));""")
    assert result[0] == [32, 26] and result[1] == [32, 26], "either side drives the other"
    assert result[2] == [8, 7], "a fraction rounds to the nearest pixel"
    assert result[3] == [52, 64], "the taller side stops at 64 and the typed one shrinks to match"
    assert result[4] == [1, 3]


@needs_node
def test_fit_to_board_shrinks_both_sides_and_keeps_the_shape():
    result = _run_core("""
        console.log(JSON.stringify([
          fitSize(64, 64, 64, 32), fitSize(52, 64, 64, 32), fitSize(80, 20, 64, 32), fitSize(20, 10, 64, 32), fitSize(64, 64, 32, 32),
        ]));""")
    assert result[0] == [32, 32], "a square on the 64x32 board shrinks both ways, not just in height"
    assert result[1] == [26, 32]
    assert result[2] == [64, 16], "a wide one is limited by the width instead"
    assert result[3] == [20, 10], "art that already fits isn't enlarged"
    assert result[4] == [32, 32]
