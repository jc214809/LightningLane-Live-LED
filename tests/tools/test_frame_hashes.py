import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("frame_hashes", os.path.join(ROOT, "tools", "frame_hashes.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

SUBSET = ["--only", "landmark/CastleLandmark@64x32", "--only", "fireworks/everyday@64x32"]


def run_tool(*args):
    """The tool as a script, as refactor agents run it (the real emulator driver, not this suite's stub)."""
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "frame_hashes.py"), *args],
                          capture_output=True, text=True, cwd=ROOT)


def test_frame_bytes_are_raw_rgb_in_row_order_with_black_where_nothing_is_lit():
    raw = tool.frame_bytes({(1, 0): (1, 2, 3), (0, 1): (4, 5, 6), (9, 9): (7, 7, 7), (-1, 0): (8, 8, 8)}, 2, 2)
    assert raw == bytes([0, 0, 0, 1, 2, 3, 4, 5, 6, 0, 0, 0]), "off-board pixels are dropped"


def test_frame_bytes_clamp_a_channel_a_panel_would_clamp():
    assert tool.frame_bytes({(0, 0): (300, -5, 12.7)}, 1, 1) == bytes([255, 0, 12])


def test_a_frame_canvas_keeps_black_pixels_so_a_blackout_erases():
    canvas = tool.FrameCanvas(4, 2)
    canvas.SetPixel(1, 1, 9, 9, 9)
    canvas.SetPixel(1, 1, 0, 0, 0)
    canvas.SetPixel(10, 1, 1, 1, 1)
    assert canvas.px == {(1, 1): (0, 0, 0)}


def test_the_digest_depends_on_every_frame_and_on_their_order():
    def digest(*frames):
        d = tool.Digest()
        for frame in frames:
            d.frame(frame, 2, 1)
        return d.hex()
    a, b = {(0, 0): (1, 1, 1)}, {(1, 0): (1, 1, 1)}
    assert digest(a, b) == digest(a, b)
    assert len({digest(a, b), digest(b, a), digest(a), digest(a, a)}) == 4


def test_only_filters_by_substring_and_no_filter_keeps_everything():
    names = ["landmark/A@64x32", "landmark/B@64x32", "show/x.v1@64x32"]
    assert tool.selected(names, None) == names
    assert tool.selected(names, ["landmark/"]) == names[:2]
    assert tool.selected(names, ["B@", "show"]) == names[1:]


def test_compare_lists_every_changed_missing_and_added_name():
    old = {"a": "1" * 64, "b": "2" * 64, "c": "3" * 64}
    new = {"a": "1" * 64, "b": "9" * 64, "d": "4" * 64}
    assert [(n, why.split(" (")[0]) for n, why in tool.compare(old, new)] == [
        ("b", "differs"), ("c", "missing from the new run"), ("d", "not in the old run")]
    assert tool.compare(old, new, only=["a"]) == [], "a filtered compare ignores the rest"
    assert tool.compare(old, old) == []


def test_the_catalog_covers_every_kind_of_thing_on_both_boards():
    names = list(tool.catalog())
    for kind in ("landmark/CastleLandmark", "landmark-screen/CastleLandmark", "transition/wipe", "transition/mike",
                 "fireworks/everyday", "fireworks/halloween", "fireworks/christmas", "fireworks-title",
                 "show/happily-ever-after.v1", "show/happily-ever-after.v2", "screen/park-info/party",
                 "screen/ride/down", "screen/countdown/days-to-go", "landmark/FriendlyJackOLantern-wink"):
        assert [f"{kind}@64x32", f"{kind}@64x64"] == [n for n in names if n.startswith(kind + "@")], kind
    from display.animation import TRANSITIONS
    assert {n.split("/")[1].split("@")[0] for n in names if n.startswith("transition/")} == set(TRANSITIONS)
    assert names == list(dict.fromkeys(names))


def test_a_landmark_hashes_the_same_twice_and_one_changed_pixel_changes_it(monkeypatch):
    from display.landmarks.castle import CastleLandmark

    first = tool.hash_landmark(CastleLandmark, 64, 32)
    assert tool.hash_landmark(CastleLandmark, 64, 32) == first

    build = CastleLandmark.build

    def one_pixel_more(self):
        build(self)
        self.base[(0, 0)] = (1, 2, 3)
    monkeypatch.setattr(CastleLandmark, "build", one_pixel_more)
    assert tool.hash_landmark(CastleLandmark, 64, 32) != first


def test_a_thing_that_raises_is_recorded_as_an_error_not_a_crash(monkeypatch):
    def boom():
        raise ValueError("nope")
    monkeypatch.setattr(tool, "catalog", lambda: {"x/ok": lambda: "a" * 64, "x/bad": boom})
    assert tool.run() == {"x/ok": "a" * 64, "x/bad": "error: ValueError: nope"}
    assert tool.run(["ok"]) == {"x/ok": "a" * 64}


def test_the_frozen_clock_makes_the_party_park_hold_its_party_tonight():
    from utils.special_events import special_event_hours
    assert special_event_hours(tool.party_park()) != ("7PM", "12AM"), "the real clock: no party today"
    with tool.frozen_clock():
        assert special_event_hours(tool.party_park()) == ("7PM", "12AM")


def test_a_run_of_the_script_is_identical_every_time_and_compares_clean(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    first = run_tool("--out", str(a), *SUBSET)
    assert first.returncode == 0, first.stderr[-2000:]
    again = run_tool("--out", str(b), "--compare", str(a), *SUBSET)
    assert again.returncode == 0, again.stdout + again.stderr[-2000:]
    assert "0 differences" in again.stdout
    assert a.read_text() == b.read_text()
    assert sorted(json.loads(a.read_text())) == ["fireworks/everyday@64x32", "landmark/CastleLandmark@64x32"]
    assert all(len(h) == 64 for h in json.loads(a.read_text()).values())


def test_the_script_exits_1_and_names_what_differs(tmp_path):
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"landmark/CastleLandmark@64x32": "0" * 64}))
    result = run_tool("--compare", str(old), "--only", "landmark/CastleLandmark@64x32")
    assert result.returncode == 1
    assert "DIFFERENT landmark/CastleLandmark@64x32" in result.stdout
    assert "1 differences" in result.stdout


def test_list_prints_the_names_without_rendering():
    result = run_tool("--list", "--only", "screen/ride/")
    assert result.returncode == 0
    assert result.stdout.split() == [f"screen/ride/{n}@64x{h}" for h in (32, 64) for n in ("wait", "down", "long-name", "walk-on")]
