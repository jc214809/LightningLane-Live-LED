import random

import pytest

from display.fireworks.actors.toy_story import BLOCK_COLOURS, BUZZ_ART, BUZZ_BOOTS_ROW, BUZZ_COLORS, WOODY_COLORS, BuzzAndWoody
from display.animation.characters.buzz import BuzzReveal
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue


def _scene(start=453.0, end=459.0, stage="ghost"):
    return Cue("s", "scene", start, end, ((255, 0, 0),), 0.0, None, (), frozenset(), stage, ("buzz_woody",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _buzz_pixels(out):
    """Where his lime green and purple are drawn (neither is in Woody's art or the blocks)."""
    return {xy for xy, rgb in out.items() if rgb in (BUZZ_COLORS["I"], BUZZ_COLORS["G"])}


@pytest.mark.parametrize("height", [32, 64])
def test_woody_slides_in_waves_and_slides_off_before_buzz_comes(height):
    show = MusicShow(64, height, random.Random(1))
    actor, cue = BuzzAndWoody(show), _scene(start=459.3, end=473.3, stage="castle")
    assert actor.woody_top_left(0.0) is None, "not there at first"
    x, y = actor.woody_top_left(actor.SLIDE_S / 2)
    assert -actor.woody_w < x < 0, "sliding in from the left edge"
    for e in (actor.SLIDE_S, 2.0, 4.0, actor.WOODY_OFF - actor.SLIDE_S):
        x, y = actor.woody_top_left(e)
        assert (x, y + actor.woody_h) == (0, height), "standing on the ground at the left edge"
        assert x + actor.woody_w // 2 < show.castle_x + show.castle_w // 2, "by the castle's left side"
        out = _frame(show, actor, cue, cue.start + e)
        assert out.get((5, height - actor.woody_h + 11)) == WOODY_COLORS["O"], "Woody's face is drawn"
        assert not _buzz_pixels(out), "and no Buzz yet"
    x, y = actor.woody_top_left(actor.WOODY_OFF - actor.SLIDE_S / 2)
    assert -actor.woody_w < x < 0 and y + actor.woody_h <= height, "sliding back off, on the board's rows"
    assert actor.woody_top_left(actor.WOODY_OFF) is None
    assert actor.WOODY_OFF <= actor.SWOOP_AT, "gone before Buzz comes"
    for e in (actor.SWOOP_AT + 0.4, actor.SWOOP_AT + 0.8, actor.SWOOP_AT + 1.2):
        out = _frame(show, actor, cue, cue.start + e)
        assert _buzz_pixels(out) and all(0 <= x < 64 and 0 <= y < height for x, y in out), "Buzz, on the board"
        assert actor.woody_top_left(e) is None


def test_they_are_their_charts_size_on_both_boards():
    small, big = BuzzAndWoody(MusicShow(64, 32)), BuzzAndWoody(MusicShow(64, 64))
    assert (small.buzz_w, small.buzz_h) == (big.buzz_w, big.buzz_h) == (40, 26), "Buzz flying, his grid's, 1x on both"
    assert (small.woody_w, small.woody_h) == (big.woody_w, big.woody_h) == (21, 26), \
        "Woody, the chibi chart's 19 x 26 plus room for his raised hand, 1x on both"
    assert all(len(row) == 40 for row in BUZZ_ART) and set("".join(BUZZ_ART)) <= set(BUZZ_COLORS) | {"."}


def test_buzz_flies_fist_first_with_his_trail_from_his_boots():
    show = MusicShow(64, 64, random.Random(1))
    actor, cue = BuzzAndWoody(show), _scene(start=459.3, end=473.3, stage="castle")
    assert actor.buzz == [row[::-1] for row in BUZZ_ART], "mirrored: drawn flying right, he flies left"
    assert actor.buzz[12][0] != "." and actor.buzz[12][-1] == ".", "his fist leads, at the left"
    assert actor.buzz[25][-1] != "." and actor.buzz[25][0] == ".", "his boots trail, at the right"
    e = actor.SWOOP_AT + actor.SWOOP_S / 2
    left, top = (round(v) for v in actor.buzz_top_left(e))
    out = _frame(show, actor, cue, cue.start + e)
    flames = {xy for xy, rgb in out.items() if rgb in BuzzReveal.flame_colors}
    assert flames and all(x >= left + actor.buzz_w for x, _ in flames), "behind him, to the right"
    assert {y - top for _, y in flames} <= set(range(BUZZ_BOOTS_ROW - 2, BUZZ_BOOTS_ROW + 3)), "level with his boots"


def test_woody_waves_by_the_clock():
    actor = BuzzAndWoody(MusicShow(64, 32))
    poses = {tuple(actor.woody_pose(i * 0.1)) for i in range(12)}
    assert len(poses) == 2, "his arm swings between two poses"
    assert actor.woody_pose(0.0) != actor.woody_pose(BuzzAndWoody.WAVE_S)


@pytest.mark.parametrize("pose", [0.0, BuzzAndWoody.WAVE_S])
def test_woodys_wave_raises_his_arm_beside_his_hat(pose):
    """His right hand leaves his side (by the holster) and goes up beside the hat brim, in both halves."""
    art = BuzzAndWoody(MusicShow(64, 32)).woody_pose(pose)
    assert all(len(row) == len(art[0]) for row in art)
    hand_rows = [r for r, row in enumerate(art) if "O" in row[17:]]
    assert hand_rows and max(hand_rows) <= 9, "his hand is up by his hat"
    assert all(row[15:18] == "..." for row in art[16:19]), "and gone from his side"
    assert set("".join(art)) <= set(WOODY_COLORS) | {"."}


def test_they_follow_the_clock_not_the_frames():
    cue = _scene()
    seen = []
    for fps in (30, 7):
        show = MusicShow(64, 64, random.Random(2))
        actor = BuzzAndWoody(show)
        i = 0
        while cue.start + i / fps < cue.start + 4:
            _frame(show, actor, cue, cue.start + i / fps)
            i += 1
        seen.append(_frame(show, actor, cue, cue.start + 4))
    assert seen[0] == seen[1]


def test_nothing_is_drawn_when_inactive():
    show = MusicShow(64, 32, random.Random(3))
    actor, cue = BuzzAndWoody(show), _scene()
    _frame(show, actor, cue, cue.start + 2)
    assert _frame(show, actor, cue, cue.start + 6.5, active=False) == {}


def _block_pixels(out):
    return {xy for xy, rgb in out.items() if rgb in BLOCK_FACES}


BLOCK_FACES = set(BLOCK_COLOURS)


@pytest.mark.parametrize("height", [32, 64])
def test_blocks_fill_the_castle_from_its_base_up_on_its_pixels_only(height):
    show = MusicShow(64, height, random.Random(1))
    actor, cue = BuzzAndWoody(show), _scene(stage="castle")
    assert not _block_pixels(_frame(show, actor, cue, cue.start)), "none yet"
    tops = [b[1] for b in sorted(actor.blocks, key=lambda b: b[4])]
    assert tops == sorted(tops, reverse=True), "bottom row first"
    full = _frame(show, actor, cue, cue.start + actor.FILL_START + actor.FILL_S + 0.5)
    blocks = _block_pixels(full)
    assert blocks <= actor.facade, "projected on the castle: its outline and doorway kept"
    n = actor.block
    covered = {(b[0] + i, b[1] + j) for b in actor.blocks for i in range(n) for j in range(n)} & actor.facade
    assert len(covered) > 0.8 * len(actor.facade), "the castle is full of them (bar slivers at its edges)"
    assert all(full[(b[0] + n // 2, b[1] + n // 2)] in (b[2], (245, 240, 225)) for b in actor.blocks
               if (b[0] + n // 2, b[1] + n // 2) in actor.facade and b[0] + n // 2 >= actor.woody_w), "and drawn"
    tops = {top for _, top, *_ in actor.blocks}
    assert min(tops) <= show.castle_y + 2 * actor.block, "up to the spire"
    assert (actor.block, actor.block) == ((5, 5) if height == 64 else (3, 3))
    held = _frame(show, actor, cue, cue.start + actor.SWOOP_AT - 0.1)
    assert _block_pixels(held) == blocks, "and they stay put until Buzz comes back"


def test_the_64x64_blocks_carry_letters():
    show = MusicShow(64, 64, random.Random(1))
    actor, cue = BuzzAndWoody(show), _scene(stage="castle")
    out = _frame(show, actor, cue, cue.start + actor.SWOOP_AT - 0.5)
    assert sum(1 for rgb in out.values() if rgb == (245, 240, 225)) > 50, "pale A, B, C faces"


@pytest.mark.parametrize("height", [32, 64])
def test_buzz_flies_through_the_castle_and_knocks_every_block_down(height):
    show = MusicShow(64, height, random.Random(1))
    actor, cue = BuzzAndWoody(show), _scene(start=459.3, end=473.3, stage="castle")
    xs = [actor.buzz_top_left(actor.SWOOP_AT + k * actor.SWOOP_S / 8)[0] for k in range(9)]
    assert xs == sorted(xs, reverse=True), "right to left"
    assert xs[0] >= 64 and xs[-1] + actor.buzz_w < 0.001, "from off the right edge to off the left"
    left, top = actor.buzz_top_left(actor.SWOOP_AT + actor.SWOOP_S / 2)
    assert top < show.castle_y + show.castle_h / 2 < top + actor.buzz_h, "through the castle's middle"
    assert 0 <= top and top + actor.buzz_h <= height, "wholly on the board"
    trail_gone = actor.SWOOP_AT + actor.SWOOP_S * (64 + actor.buzz_w + actor.TRAIL * actor.px) / (64 + actor.buzz_w)
    out = _frame(show, actor, cue, cue.start + trail_gone + 0.05)
    assert not _buzz_pixels(out) and not set(out.values()) & set(BuzzReveal.flame_colors), "he and his trail fly off"
    assert all(actor.SWOOP_AT <= b[5] <= actor.SWOOP_AT + actor.SWOOP_S for b in actor.blocks), "all loosened as he passes"
    s = actor.px
    hit = [b for b in actor.blocks if b[1] < actor.swoop_top + actor.buzz_h and b[1] + actor.block > actor.swoop_top]
    assert hit and (len(hit) < len(actor.blocks)) == (height == 64), "on 64x32 he's taller than the castle: he hits them all"
    for b in actor.blocks:
        x, y, _ = actor.block_at(b, b[5] + 0.3)
        if b in hit:
            assert x < b[0] - 2 * s, "the ones in his path fly off ahead of him"
        else:
            assert abs(x - b[0]) < 3 * s and y >= b[1], "the rest topple (the bottom row is on the ground already)"
    clipped = {}
    draw_block = actor._draw_block
    actor._draw_block = lambda out, block, x, y, f, clip: (clipped.__setitem__(block, clip),
                                                          draw_block(out, block, x, y, f, clip))
    _frame(show, actor, cue, cue.start + actor.SWOOP_AT - 0.1)
    assert clipped and all(clipped.values()), "standing, they're projected on the castle"
    clipped.clear()
    _frame(show, actor, cue, cue.start + actor.SWOOP_AT + actor.SWOOP_S)
    assert clipped and not any(clipped.values()), "knocked loose, they tumble whole"
    assert not _block_pixels(_frame(show, actor, cue, cue.start + actor.GONE_BY)), "all gone before the mash-up"
    assert actor.GONE_BY < cue.end - cue.start
