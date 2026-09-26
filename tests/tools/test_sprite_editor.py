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


def test_aliases_appear_once_and_animation_frames_are_split(sprites):
    assert "dumbo/EARS_UP" in sprites and "dumbo/art" not in sprites, "art = EARS_UP is one sprite"
    assert {"stitch/art[0]", "stitch/art[1]"} <= set(sprites), "each look direction is editable"
    assert {s["character"] for s in sprites.values()} >= {"tink", "buzz", "genie", "mickey", "ralph", "dumbo"}


def test_every_key_has_a_color_and_placeholders_are_flagged(sprites):
    for sid, s in sprites.items():
        used = {ch for row in s["rows"] for ch in row} - {"."}
        assert used <= set(s["colors"]), sid
    assert sprites["stitch/_BASE"]["unmapped"] == ["#"], "his eye slots are filled at draw time"
    assert sprites["stitch/_BASE"]["colors"]["#"] == builder.UNMAPPED_RGB


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
    out = subprocess.run([NODE, "-e", core + "\n" + body], capture_output=True, text=True, timeout=30)
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
