import importlib.util
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location("lip_sync", os.path.join(ROOT, "tools", "lip_sync.py"))
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

RATE = tool.RATE


def _tone(seconds, level=0.3):
    t = np.arange(int(seconds * RATE)) / RATE
    return (level * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def _silence(seconds):
    return np.zeros(int(seconds * RATE), np.float32)


def test_silence_keeps_the_mouth_shut():
    assert set(tool.mouth_track(_silence(2))) == {"0"}
    assert len(tool.mouth_track(_silence(2))) == 2 * tool.FPS, "one shape per frame"


def test_syllables_open_and_close_the_mouth_with_each_one():
    sung = np.concatenate([np.concatenate([_tone(0.2), _silence(0.13)]) for _ in range(6)])
    track = tool.mouth_track(sung)
    assert "2" in track and "0" in track
    changes = sum(a != b for a, b in zip(track, track[1:]))
    assert changes / (len(track) / tool.FPS) >= 4, "about one open and close per syllable"


def test_a_quiet_moment_inside_a_loud_phrase_is_half_open():
    phrase = np.concatenate([_tone(0.4, 0.4), _tone(0.2, 0.2), _tone(0.4, 0.4)])  # 6 dB under: half
    track = tool.mouth_track(phrase)
    middle = track[int(0.45 * tool.FPS):int(0.55 * tool.FPS)]
    assert set(middle) <= {"1", "0"} and "1" in track


def test_write_lips_keeps_the_other_characters_tracks(tmp_path):
    path = tmp_path / "show.v2.lips.json"
    tool.write_lips(str(path), "genie", {"start": 1.0, "fps": 15, "track": "012"})
    tool.write_lips(str(path), "olaf", {"start": 2.0, "fps": 15, "track": "2"})
    tool.write_lips(str(path), "genie", {"start": 1.0, "fps": 15, "track": "210"})
    lips = json.loads(path.read_text())["lips"]
    assert lips == {"genie": {"start": 1.0, "fps": 15, "track": "210"}, "olaf": {"start": 2.0, "fps": 15, "track": "2"}}


def test_main_checks_its_times_and_the_music(monkeypatch, tmp_path, caplog):
    assert tool.main(["genie", "10", "5"]) == 1
    assert "end must be after start" in caplog.text
    monkeypatch.setattr(tool, "SOUNDS_DIR", str(tmp_path))
    assert tool.main(["genie", "1", "5"]) == 1
    assert "copy it from a board" in caplog.text


def test_main_without_demucs_says_how_to_install_it(monkeypatch, tmp_path, caplog):
    (tmp_path / "happily-ever-after.wav").write_bytes(b"")
    monkeypatch.setattr(tool, "SOUNDS_DIR", str(tmp_path))
    monkeypatch.setattr(tool, "DEMUCS_PYTHON", str(tmp_path / "no-venv" / "python"))
    assert tool.main(["genie", "1", "5"]) == 1
    assert "demucs isn't installed" in caplog.text


def test_a_sound_lands_in_its_own_frame_however_far_into_the_track():
    """Regression: blocks of a whole number of samples (16000 // 60) drifted the mouth over a frame late
    by half a minute in, so Genie's last lines missed their words."""
    clip = np.concatenate([_silence(36.0), _tone(0.4), _silence(0.6)])
    track = tool.mouth_track(clip)
    first = track.index("2") if "2" in track else track.index("1")
    assert first == 36 * tool.FPS


def test_muted_stretches_keep_the_mouth_shut():
    sung = np.concatenate([np.concatenate([_tone(0.2), _silence(0.13)]) for _ in range(9)])
    track = tool.mouth_track(sung, muted=[(1.0, 2.0)])
    assert set(track[tool.FPS:2 * tool.FPS]) == {"0"}
    assert "2" in track[:tool.FPS] and "2" in track[2 * tool.FPS:]


def test_main_rejects_a_bad_mute(caplog):
    assert tool.main(["genie", "1", "5", "--mute", "9-3"]) == 1
    assert "--mute and --from-mix take FROM-TO" in caplog.text


def test_a_close_shuts_the_lips_inside_a_held_note():
    held = _tone(2.0)
    track = tool.mouth_track(held, closes=[1.0])
    assert track[14] == "2" and track[15] == "0" and track[16] == "0" and track[17] == "2", "about 0.13 s at 1.0 s"


def test_from_mix_reads_a_reverb_drowned_word_from_the_mix():
    """A word demucs left in the music (Mufasa's echoing last "Remember") is silent in the stem, so the
    mouth reads the original mix over that stretch instead."""
    stem = np.concatenate([_tone(1.0), _silence(1.0)])
    mix = np.concatenate([_tone(1.0), np.concatenate([_tone(0.2), _silence(0.13)] * 3)[:RATE]])
    plain = tool.mouth_track(stem)
    mixed = tool.mouth_track(stem, mix=mix, from_mix=[(1.0, 2.0)])
    assert set(plain[tool.FPS:]) == {"0"} and "2" in mixed[tool.FPS:], "the word's mouth comes from the mix"
    assert mixed[:tool.FPS - 3] == plain[:tool.FPS - 3], "and only there"
