import random

import pytest

from display.fireworks.actors.mufasa import MufasaInTheStars, _halved
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue

START, END = 849.0, 889.0


def _scene():
    return Cue("s", "Embers", START, END, ((255, 70, 20),), 0.0, "dark", (), frozenset(), "castle", ("mufasa",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _play(height, until, fps=30, seed=1):
    show = MusicShow(64, height, random.Random(seed))
    actor = MufasaInTheStars(show)
    cue = _scene()
    i, out = 0, {}
    while START + i / fps <= until:
        out = _frame(show, actor, cue, START + i / fps)
        i += 1
    return show, actor, out


def _colours(out):
    return {xy for xy, rgb in out.items() if rgb != (0, 0, 0)}


@pytest.mark.parametrize("height, size", [(32, (21, 21)), (64, (42, 43))])
def test_mufasa_fills_the_top_right_corner_at_his_size(height, size):
    _, actor, out = _play(height, START + 20)
    assert (actor.w, actor.h) == size, "the traced face on 64x64, halved on 64x32"
    assert actor.left == 64 - actor.w, "flush with the right edge"
    xs, ys = [x for x, _ in out], [y for _, y in out]
    assert max(xs) == 63 and min(ys) <= 1 and all(0 <= x < 64 and 0 <= y < height for x, y in out)


def test_mufasa_faces_in_toward_the_middle():
    """Three-quarters left: his muzzle and nose are on the left of his face, toward the board's middle."""
    art = MufasaInTheStars.ART
    nose = [x for row in art for x, k in enumerate(row) if k == "N"]
    mane = [x for row in art for x, k in enumerate(row) if k == "M"]
    assert sum(nose) / len(nose) < sum(mane) / len(mane) - 8


@pytest.mark.parametrize("height", [32, 64])
def test_mufasa_fades_in_holds_and_fades_out_by_the_end(height):
    _, _, early = _play(height, START + 3)
    _, actor, mid = _play(height, START + 20)
    _, _, last = _play(height, END - 0.05)
    assert not early and not last, "dark before he appears and gone by the scene's end"
    nose = MufasaInTheStars.COLORS["N"]
    assert any(max(abs(a - b) for a, b in zip(rgb, nose)) < 30 for rgb in mid.values()), "his face shows"


def test_the_bottom_of_his_mane_melts_into_the_sky():
    _, actor, out = _play(64, START + 20)
    row = lambda y: [out[(x, y)] for x in range(64) if (x, y) in out]
    top_level = max(max(rgb) for rgb in row(10))
    low_level = max(max(rgb) for rgb in row(actor.h - 2))
    assert low_level < top_level * 0.3


def test_halving_keeps_his_features():
    small = _halved(MufasaInTheStars.ART, MufasaInTheStars.RANK)
    for k in "LN":  # his eyes' amber shares its block with his brow, so on 64x32 they're dark slits
        assert any(k in row for row in small), f"{k} survives the shrink"


def test_mufasa_draws_nothing_when_inactive():
    show, actor, _ = _play(64, START + 20)
    assert _frame(show, actor, _scene(), START + 20.1, active=False) == {}


def test_mufasa_follows_the_clock_not_the_frames():
    _, _, fast = _play(64, START + 12, fps=30)
    _, _, slow = _play(64, START + 12, fps=7)
    assert fast == slow


def test_his_outline_is_all_mane():
    """No gold face or cream muzzle on his border, or within two pixels of it: the mane frames him."""
    art = MufasaInTheStars.ART
    h, w = len(art), len(art[0])
    lit = lambda x, y: 0 <= x < w and 0 <= y < h and art[y][x] != "."
    for y in range(h):
        for x in range(w):
            if lit(x, y) and any(not lit(x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3)
                                 if abs(dx) + abs(dy) <= 2):
                assert art[y][x] not in "FC", f"gold or cream at ({x}, {y}) on his outline"


def test_mufasa_mouths_his_lines_by_the_clock():
    from display.fireworks.score import Lips
    # 20 s shut, then a second each of half, open, shut; a last line well after, so he isn't fading yet
    track = "0" * 300 + "1" * 15 + "2" * 15 + "0" * 60 + "2" * 15
    show = MusicShow(64, 64, random.Random(9), {"mufasa": Lips(START, 15.0, track)})
    actor, cue = MufasaInTheStars(show), _scene()
    for t in range(0, 19):
        _frame(show, actor, cue, START + t)
    def light(t, x, y):  # how bright a cell of his mouth is
        return sum(_frame(show, actor, cue, t).get((actor.left + x, y), (0, 0, 0)))
    assert light(START + 19.5, 11, 28) > 400, "shut: his chin's cream under the smile"
    assert light(START + 20.5, 11, 27) < 250 and light(START + 20.5, 11, 28) < 250, "half: open, then his lip"
    assert light(START + 21.5, 11, 28) < 250 and light(START + 21.5, 11, 29) < 250, "open: deeper"
    assert light(START + 22.5, 11, 28) > 400, "shut again"


def test_on_64x32_his_halved_face_mouths_too():
    from display.fireworks.score import Lips
    show = MusicShow(64, 32, random.Random(10), {"mufasa": Lips(START, 15.0, "2" * 600)})
    actor = MufasaInTheStars(show)
    assert actor.cells[2] != actor.cells[0], "the open mouth survives halving"


def test_mufasa_is_on_the_board_for_every_word_he_says():
    """Through to his echoing last "Remember": he's still clearly there while his mouth moves."""
    import json
    from display.fireworks.score import SHOWS_DIR, parse_lips
    with open(f"{SHOWS_DIR}/happily-ever-after.v2.lips.json") as f:
        lips = parse_lips(json.load(f))["mufasa"]
    show = MusicShow(64, 64, random.Random(13), {"mufasa": lips})
    actor = MufasaInTheStars(show)
    _frame(show, actor, _scene(), START)
    spoken = [lips.start + i / lips.fps for i, k in enumerate(lips.track) if k != "0"]
    assert max(spoken) > 882.5, "his last echoing Remember is in his track"
    assert actor.last_line_s() + START == pytest.approx(877.67, abs=0.1), "fading from Remember who you are"
    assert all(actor.glow(t - START) > 0.25 for t in spoken), "still there to mouth the echo"
    assert actor.glow(880 - START) < 0.95, "already fading as he says Remember who you are"


def test_he_fades_away_as_he_says_his_last_line():
    """As in the film, he fades while saying "Remember who you are": the fade starts with his last line."""
    from display.fireworks.score import Lips
    track = "0" * 150 + "2" * 30 + "0" * 60 + "2" * 45  # lines at 10-12 s and 16-19 s into the scene
    show = MusicShow(64, 64, random.Random(11), {"mufasa": Lips(START, 15.0, track)})
    actor, cue = MufasaInTheStars(show), _scene()
    _frame(show, actor, cue, START)
    assert actor.last_line_s() == pytest.approx(16.0) and actor.last_word_s() == pytest.approx(19.0)
    assert actor.glow(15.5) > 0.85, "full until his last line"
    assert 0.5 < actor.glow(18) < 0.85 and actor.glow(19) < actor.glow(18), "fading through it"
    assert actor.glow(19 + MufasaInTheStars.FADE_TAIL_S + 0.05) == 0, "gone just after his last word"
    no_track = MufasaInTheStars(MusicShow(64, 64, random.Random(12)))
    _frame(no_track.show, no_track, cue, START)
    assert no_track.last_line_s() is None and no_track.glow(30) > 0.8, "without a track: the scene's last seconds"

