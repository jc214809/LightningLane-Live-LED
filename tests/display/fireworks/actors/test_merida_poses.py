"""Merida's baked poses for Touch the Sky: every frame whole (no holes where the bow or her hand was)."""
import pytest

from display.animation.characters.archer import ArcherReveal as Archer
from display.fireworks.actors import merida_poses as poses


@pytest.fixture(scope="module")
def frames():
    return {key: poses.build(key) for key in poses.frame_keys()}


def _skirt(key):
    """Her own skirt cells for a frame's pose (the part behind the bow included), sheared after her hips."""
    kind, _, n = key.partition("/")
    if kind in ("aim", "loose", "after"):
        release = None if kind == "aim" else int(n) / poses.FPS if kind == "loose" else poses.LOOSE_S + 10
        tip = float(n) if kind != "loose" else poses.after_tip(int(n) / poses.FPS)
        lower = poses.split("draw", release)[0]
    else:
        tip, lower = 0.0, poses.split("rest")[0]
    hip = poses.HIP_PX * tip / poses.AIM
    return {(x + int(round(hip * (poses.GROUND - y) / (poses.GROUND - poses.WAIST))), y) for x, y in lower}


def test_her_skirt_is_whole_in_every_frame(frames):
    for key, cells in frames.items():
        missing = _skirt(key) - set(cells)
        assert not missing, f"{key}: her skirt has a hole at {sorted(missing)[:6]}"


def test_she_has_a_mouth_in_every_frame(frames):
    for key, cells in frames.items():
        assert any(k in "mX" and 19 <= y <= 26 for (x, y), k in cells.items()), f"{key} has no mouth"


def test_her_mouth_opens_wider_with_each_shape(frames):
    inside = [sum(k == "X" for k in frames["talk/%d" % m].values()) for m in (0, 1, 2)]
    assert inside[0] == 0 < inside[1] < inside[2], "a closed smile, then half, then open"
    assert inside[2] >= 8 and "m" in frames["talk/0"].values()


def test_no_small_holes_inside_her(frames):
    """Seams between the parts of her turned by different angles are filled; only the bow's inside stays open."""
    for key, cells in frames.items():
        assert poses.fill_small_holes(cells) == cells, key


def test_the_arrow_shows_while_she_aims_and_is_gone_once_loosed(frames):
    for d in range(int(poses.AIM) + 2):
        cells = frames["aim/%d" % d]
        assert sum(k == "a" for k in cells.values()) >= 8, f"aim/{d}: the shaft is hidden"
        assert "t" in cells.values() and "f" in cells.values()
    for key in [k for k in frames if k.startswith(("loose", "after"))]:
        assert not {"a", "t", "f"} & set(frames[key].values()), f"{key}: the arrow's still on the string"


def test_the_planted_bow_stands_string_out_and_is_caught_string_in(frames):
    def string_and_wood(cells):
        string = [x for (x, y), k in cells.items() if k == "S" and 30 <= y <= 40]
        wood = [x for (x, y), k in cells.items() if k in "OP" and x > 22 and 30 <= y <= 40]
        return sum(string) / len(string), sum(wood) / len(wood)

    s, w = string_and_wood(frames["talk/0"])
    assert s > w, "planted: the string on the far side of the wood"
    s, w = string_and_wood(frames["held"])
    assert s < w, "caught: the string toward her, ready to draw"
    assert max(y for (x, y), k in frames["talk/0"].items() if k in "OPK" and x > 30) >= poses.GROUND, \
        "its foot on the ground"


def test_the_toss_throws_the_bow_up_over_her(frames):
    tops = [min(y for (x, y), k in frames["toss/%d" % i].items() if k == "S") for i in range(poses.TOSS_FRAMES)]
    assert min(tops) <= min(y for (x, y), k in frames["held"].items() if k == "S") - 8, "it rises well up"
    assert tops.index(min(tops)) not in (0, len(tops) - 1), "up, then back down to her hand"


def test_after_the_release_her_hand_leaves_her_chin_and_hangs_at_her_side(frames):
    drawn = frames["aim/20"]
    assert sum(k == "X" or k == "m" for (x, y), k in drawn.items() if y >= 22) <= 2, "her hand at her chin"
    later = frames["after/%d" % int(poses.AIM - poses.RELAX)]
    hand = [(x, y) for (x, y), k in later.items() if k == "F" and y >= 30]
    assert hand and max(y for _, y in hand) >= 32, "her hand down by her quiver"
    assert "m" in later.values(), "her smile uncovered"


def test_the_string_snaps_straight_and_rings_after_the_release(frames):
    def bow_out(cells):
        """How far the string bows from the straight line between its ends (0 straight, big at full draw)."""
        string = sorted((y, x) for (x, y), k in cells.items() if k == "S")
        (y0, x0), (y1, x1) = string[0], string[-1]
        return max(abs(x - (x0 + (x1 - x0) * (y - y0) / (y1 - y0))) for y, x in string)

    drawn = bow_out(frames["aim/%d" % int(poses.AIM)])
    after = [bow_out(frames["loose/%d" % i]) for i in range(int(poses.LOOSE_S * poses.FPS))]
    assert drawn > 3, "a V at full draw"
    assert min(after[:4]) < drawn / 2, "it springs straight"
    assert after[-1] <= 1.5 and bow_out(frames["after/%d" % int(poses.AIM)]) <= 1.5, "and settles straight"


def test_frame_key_follows_the_scene():
    assert poses.frame_key(3.0, 2) == "talk/2" and poses.frame_key(3.0) == "talk/0"
    assert poses.frame_key(poses.WIND + 0.01) == "toss/0"
    assert poses.frame_key(poses.DIP - 0.001) == "toss/%d" % (poses.TOSS_FRAMES - 1)
    assert poses.frame_key(poses.DRAW - 0.01) == "held"
    assert poses.frame_key(poses.DRAW + 0.01) == "aim/0"
    assert poses.frame_key(poses.RELEASE - 0.05) == "aim/%d" % int(poses.AIM)
    assert poses.frame_key(poses.RELEASE) == "loose/0"
    assert poses.frame_key(poses.RELEASE + 5) == "after/%d" % int(poses.AIM - poses.RELAX)
    shown = {poses.frame_key(i / 100, 1 + i % 2) for i in range(0, 3500)}
    assert shown <= set(poses.frame_keys()), "every frame the scene shows is baked"


def test_she_lets_go_on_touch():
    assert poses.RELEASE == pytest.approx(295.36 - 268.0)
    assert Archer.ART is poses.ART, "the archer's own art"
