import importlib.util
import json
import os
import re

import pytest

from display.fireworks.score import load_score, parse_score

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("render_show", os.path.join(ROOT, "tools", "render_show.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

PAGE = os.path.join(ROOT, "tools", "show_sync_checker.html")
TINY = {
    "show_end": 4,
    "recording": {"url": "https://example.com/show", "scale": 1.001, "offset": 10.19},
    "sections": [{"id": "opening", "start": 0, "end": 4, "palette": ["#FFFFFF", "#FF0000"], "intensity": .6,
                  "scenes": [{"start": 0, "end": 1, "title": "Dark", "rate": 0, "castle": "blue", "characters": []},
                             {"start": 1, "end": 4, "title": "Fire", "castle": "fire", "effects": ["flame_jets"],
                              "characters": ["Pirates"]}]}],
}


@pytest.fixture
def tiny():
    return parse_score("tiny", TINY)


def test_panel_image_draws_each_led_as_a_square_and_leaves_the_rest_black():
    img = tool.panel_image({(1, 0): (200, 10, 20)}, 4, 2, px=4)
    assert img.shape == (8, 16, 3)
    assert (img[0:4, 4:8] == (200, 10, 20)).all(), "LED (1, 0) fills its 4 x 4 square"
    assert img[0:4, 0:4].max() == 0 and img[4:8].max() == 0, "unlit LEDs are black"


def test_frames_are_one_per_frame_and_the_same_every_render(tiny):
    a = list(tool.frames(tiny, 32, fps=10))
    assert len(a) == 40, "4 s at 10 fps"
    assert a == list(tool.frames(tiny, 32, fps=10)), "the seed makes every render of a score match"
    assert all(0 <= x < 64 and 0 <= y < 32 for f in a for (x, y) in f)


def test_frames_follow_the_score_like_the_board(tiny):
    """The castle turns to its fire look in the fire scene (once its 1.5 s fade is done), as on the board."""
    dark, fire = list(tool.frames(tiny, 32, fps=10))[9], list(tool.frames(tiny, 32, fps=10))[-1]
    reds = lambda f: sum(1 for r, g, b in f.values() if r > 150 and b < 80)
    assert reds(fire) > reds(dark) + 50


def test_render_pipes_every_frame_to_ffmpeg(tiny, monkeypatch):
    written, cmds = [], []

    class FakeProc:
        def __init__(self, cmd, stdin):
            cmds.append(cmd)
            self.stdin = self

        def write(self, data):
            written.append(len(data))

        def close(self):
            pass

        def wait(self):
            return 0

    monkeypatch.setattr(tool.subprocess, "Popen", FakeProc)
    tool.render(tiny, 32, "out.mp4", audio="show.wav", fps=10)
    assert len(written) == 40 and set(written) == {64 * 4 * 32 * 4 * 3}
    cmd = cmds[0]
    assert cmd[cmd.index("-s") + 1] == "256x128" and "show.wav" in cmd and cmd[-1] == "out.mp4"
    assert cmd[cmd.index("-t") + 1] == "4.000", "cut to the show's end, not the music file's"


def test_a_failed_ffmpeg_is_an_error(tiny, monkeypatch):
    class FakeProc:
        def __init__(self, cmd, stdin):
            self.stdin = self

        def write(self, data):
            pass

        def close(self):
            pass

        def wait(self):
            return 1

    monkeypatch.setattr(tool.subprocess, "Popen", FakeProc)
    with pytest.raises(RuntimeError, match="ffmpeg failed"):
        tool.render(tiny, 32, "out.mp4", fps=10)


def test_ffmpeg_command_without_music_is_silent():
    cmd = tool.ffmpeg_command("o.mp4", 256, 128, 30)
    assert cmd.count("-i") == 1 and "-c:a" not in cmd and "-t" not in cmd


def test_sync_data_lists_every_scene_with_what_the_board_does(tiny):
    data = tool.sync_data(tiny, TINY, {"64x32": "tiny-64x32.mp4"}, "tiny-recording.mp4")
    assert [s["title"] for s in data["scenes"]] == ["Dark", "Fire"]
    fire = data["scenes"][1]
    assert fire["castle"] == "fire" and fire["effects"] == ["flame_jets"] and fire["characters"] == ["Pirates"]
    assert data["scenes"][0]["rate"] == 0
    assert data["recording"] == {**TINY["recording"], "file": "tiny-recording.mp4"}
    assert data["end"] == 4 and data["boards"] == {"64x32": "tiny-64x32.mp4"}


def test_sync_data_has_no_recording_until_one_is_downloaded(tiny):
    assert tool.sync_data(tiny, TINY, {}, None)["recording"] is None
    no_entry = {k: v for k, v in TINY.items() if k != "recording"}
    assert tool.sync_data(tiny, no_entry, {}, "x.mp4")["recording"] is None


def test_the_data_file_is_a_script_the_page_can_load_from_disk(tiny, tmp_path):
    path = tmp_path / "tiny.js"
    tool.write_sync_js(tool.sync_data(tiny, TINY, {}, None), path)
    text = path.read_text()
    assert text.startswith("window.SHOW_SYNC = ") and text.rstrip().endswith(";")
    assert json.loads(text[len("window.SHOW_SYNC = "):].rstrip().rstrip(";"))["name"] == "tiny"


def test_happily_ever_after_has_its_recording_and_every_scene_maps(tmp_path):
    with open(os.path.join(tool.SHOWS_DIR, "happily-ever-after.json")) as f:
        raw = json.load(f)
    rec = raw["recording"]
    assert rec["url"].startswith("https://") and rec["scale"] == pytest.approx(1.001) and rec["offset"] == pytest.approx(10.19)
    score = load_score("happily-ever-after")
    data = tool.sync_data(score, raw, {}, "r.mp4")
    assert len(data["scenes"]) == len(score.cues), "scene titles are unique, so each finds its characters"


def test_the_page_reads_what_the_script_writes():
    with open(PAGE) as f:
        page = f.read()
    rel = os.path.relpath(tool.OUT_DIR, os.path.dirname(PAGE)).replace(os.sep, "/") + "/"
    assert f'const DIR = "{rel}"' in page
    assert "window.SHOW_SYNC" in page
    assert re.search(r'"happily-ever-after"', page), "the default show"


def test_main_needs_ffmpeg(monkeypatch, caplog):
    monkeypatch.setattr(tool.shutil, "which", lambda name: None)
    assert tool.main([]) == 1
    assert "ffmpeg" in caplog.text


def test_main_with_an_unknown_show_is_an_error(monkeypatch, caplog):
    monkeypatch.setattr(tool.shutil, "which", lambda name: "/usr/bin/" + name)
    assert tool.main(["--show", "no-such-show"]) == 1
    assert "no usable score" in caplog.text
