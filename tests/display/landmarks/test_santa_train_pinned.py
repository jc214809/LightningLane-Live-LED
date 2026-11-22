"""The Santa train's pixels, pinned by hash on the variants the frame-hash run (tools/frame_hashes.py) doesn't reach:
a billboard with no hours, hours too wide for 64x32's "TONIGHT" line, every rider pose, every wheel position, and
art pieces the code's defensive bounds checks meet. Hashes were taken from the code before display/landmarks/
santa_train.py was split into sibling modules; they must not change (a deliberate art change updates them)."""

import hashlib
import random

import pytest

from display.landmarks import santa_train as st

BOARDS = [(64, 32), (64, 64)]
HOURS = {"none": None, "evening": ("7PM", "12AM"), "wide": ("10PM", "12AM")}
FRAME_STEP_S = 0.1


def _digest(parts):
    h = hashlib.sha256()
    for part in parts:
        h.update(repr(part).encode())
    return h.hexdigest()[:16]


def _scene(w, h, hours, monkeypatch):
    monkeypatch.setattr(st, "special_event_hours", lambda park: hours)
    return st.SantaTrainLandmark(w, h, random.Random(3), park=None)


def _frames_digest(scene):
    steps = int(scene.SCREEN_S / FRAME_STEP_S) + 1
    return _digest(sorted(scene.frame(k * FRAME_STEP_S).items()) for k in range(steps))


def _every_pose(scene, big):
    """rider_patch for every rider in every state rider_state can give it (bob, blink, wave, wag, pant)."""
    out = []
    for _, piece, kind, _ in scene.riders:
        bobs = (False, True) if kind in st.RIM_EDGE else (False,)
        blinks = (False, True) if big or kind != "santa" else (False,)
        waves = (None, 0, 1) if big and kind in ("santa", "mickey") else (None,)
        wags, pants = ((None, 0, 1, 2), (None, False, True)) if kind == "pluto" else ((None,), (None,))
        for bob in bobs:
            for blink in blinks:
                for wave in waves:
                    for wag in wags:
                        for pant in pants:
                            out.append(st.rider_patch(piece, kind, big, (bob, blink, wave, wag, pant)))
    return out


def _every_wheel(big):
    train = st.TRAIN_64 if big else st.TRAIN_32
    return [(st.wheels(piece, big), [sorted(st.spin_pixels(piece, big, step, engine=i == len(train) - 1).items())
                                     for step in range(st.SPIN_STEPS)]) for i, piece in enumerate(train)]


def _edges():
    tiny = ["." * 4 for _ in range(4)]
    posed = [st.rider_patch(tiny, "pluto", big, (False, False, None, 1, True)) for big in (True, False)]
    narrow = ["....", "...."] + ["S.S."]
    return [posed, [st.wheels(narrow, False), st.wheels(narrow, True), st.wheels(["...."] * 3, True)]]


PINNED_FRAMES = {
    ("none", 32): "60b6db7d2d38c811", ("evening", 32): "2073be62d0fb0360", ("wide", 32): "0b28e84be73e223f",
    ("none", 64): "c4ca9140260c48a5", ("evening", 64): "f332fe7bb74feac9", ("wide", 64): "4387a4ea07f68ab5",
}
PINNED_POSES = {32: "fb84a8d8931c8e02", 64: "21f3230dce53bd40"}
PINNED_WHEELS = {32: "6867be6d464dfe2d", 64: "c6843f88d715276e"}
PINNED_EDGES = "eabd31ae6faee326"


@pytest.mark.parametrize("name", HOURS)
@pytest.mark.parametrize("w, h", BOARDS)
def test_every_frame_of_the_run_is_unchanged(w, h, name, monkeypatch):
    assert _frames_digest(_scene(w, h, HOURS[name], monkeypatch)) == PINNED_FRAMES[name, h]


@pytest.mark.parametrize("w, h", BOARDS)
def test_every_rider_pose_is_unchanged(w, h, monkeypatch):
    scene = _scene(w, h, HOURS["evening"], monkeypatch)
    assert _digest(_every_pose(scene, h >= 64)) == PINNED_POSES[h]


@pytest.mark.parametrize("h", [32, 64])
def test_every_wheel_position_is_unchanged(h):
    assert _digest(_every_wheel(h >= 64)) == PINNED_WHEELS[h]


def test_art_the_bounds_checks_guard_against_is_unchanged():
    """A rider piece too small for Pluto's tongue (laid off its edge), and bottom rows whose rim runs are narrower
    than any wheel: nothing is drawn for them and nothing raises."""
    assert _digest(_edges()) == PINNED_EDGES
