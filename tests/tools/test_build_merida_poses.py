import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("build_merida_poses",
                                               os.path.join(ROOT, "tools", "build_merida_poses.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)


def test_the_baked_poses_are_what_the_poses_build():
    poses = tool.load_poses()
    with open(poses.BAKED, encoding="utf-8") as f:
        committed = f.read()
    assert committed == tool.render(poses.bake()), "Merida's poses changed: run python3 tools/build_merida_poses.py"


def test_the_bake_is_json_with_every_frame_the_scene_shows():
    poses = tool.load_poses()
    frames = json.loads(tool.render(poses.bake()))["frames"]
    assert list(frames) == poses.frame_keys()
    assert all(set(f) == {"x", "y", "rows"} and f["rows"] for f in frames.values())
