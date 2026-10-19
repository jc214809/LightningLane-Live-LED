import random

from display.animation.characters.archer import ArcherReveal as Archer
from display.fireworks.actors import merida_poses as poses
from display.fireworks.actors.merida import MeridaShoots
from display.fireworks.music_show import MusicShow
from display.fireworks.score import Cue, Lips

START, END = 268.0, 303.0  # Touch the Sky


def _scene():
    return Cue("s", "Touch the Sky", START, END, ((255, 0, 0),), 0.0, None, (), frozenset(), "ghost", ("merida",))


def _frame(show, actor, cue, t, active=True):
    show.set_cue(cue, t)
    actor.follow(active)
    actor.step(active)
    out = {}
    actor.draw(lambda *a: None, out, active)
    return out


def _at(t, height=64, lips=None):
    show = MusicShow(64, height, random.Random(1), lips)
    actor = MeridaShoots(show)
    _frame(show, actor, _scene(), START)
    return actor, _frame(show, actor, _scene(), t)


def _her(out):
    dress = {MeridaShoots.COLORS[k] for k in "DNT"}
    return {xy for xy, rgb in out.items() if rgb in dress}


def test_merida_rises_full_size_at_the_bottom_left_and_stands_there():
    _, early = _at(START + 0.1)
    actor, standing = _at(START + 5)
    her = _her(standing)
    assert len(_her(early)) < len(her), "still rising"
    boots = MeridaShoots.COLORS["z"]
    assert max(y for (x, y), rgb in standing.items() if rgb == boots) == 62 and max(y for _, y in standing) == 63, \
        "her boots (and their outline) on the bottom rows"
    assert min(x for x, _ in her) <= MeridaShoots.LEFT + 1, "at the left"
    assert max(y for _, y in standing) - min(y for _, y in standing) == 47, "full size: hair to boots, 1x"
    _, gone = _at(END - 0.001)
    assert not _her(gone), "sunk away by her scene's end"


def test_she_sinks_away_two_seconds_after_the_hit():
    actor, _ = _at(START + 1)
    leave = actor.hit_s + MeridaShoots.LEAVE_S
    _, standing = _at(START + leave - 0.05)
    _, sinking = _at(START + leave + MeridaShoots.ENTER_S / 2)
    _, gone = _at(START + leave + MeridaShoots.ENTER_S + 0.05)
    assert len(_her(sinking)) < len(_her(standing)), "going down"
    assert gone == {}, "off the board (the bullseye's sparks long done)"
    assert _at(START + 32)[1] == {}, "and stays gone for the rest of her scene"


def test_she_stays_on_the_board_all_scene():
    show = MusicShow(64, 64, random.Random(4))
    actor, cue = MeridaShoots(show), _scene()
    for i in range(int((END - START) * 10)):
        out = _frame(show, actor, cue, START + i / 10)
        assert all(0 <= x < 64 and 0 <= y < 64 for x, y in out)


def test_every_frame_she_shows_is_baked():
    show = MusicShow(64, 64, random.Random(5))
    actor = MeridaShoots(show)
    assert actor.built == {}
    for i in range(0, int((END - START) * 30)):
        actor.frame(poses.frame_key(i / 30, i % 3))
    assert actor.built == {}, "nothing had to be built on the board"


def test_a_frame_missing_from_the_bake_is_built_once_with_a_warning(monkeypatch):
    from display.fireworks.actors import merida as module
    warnings = []
    monkeypatch.setattr(module.debug, "warning", warnings.append)
    monkeypatch.setattr(MeridaShoots, "_frames", {})
    actor = MeridaShoots(MusicShow(64, 64, random.Random(6)))
    first = actor.frame("held")
    assert first == poses.pack(poses.build("held")) and actor.frame("held") is first
    assert len(warnings) == 1 and "build_merida_poses" in warnings[0]


def test_on_64x32_she_stays_off():
    _, out = _at(START + 5, height=32)
    assert out == {}
    actor, _ = _at(START + 5)
    _, shot = _at((START + actor.LOOSE_S + START + actor.hit_s) / 2, height=32)
    assert shot == {}


def test_she_mouths_her_line_by_the_clock():
    track = "0" * 15 + "1" * 15 + "2" * 15  # a second each of closed, half, open
    lips = {"merida": Lips(START + 5, 15.0, track)}
    inside = MeridaShoots.COLORS["X"]
    mouths = [{xy for xy, rgb in _at(START + t, lips=lips)[1].items() if rgb == inside} for t in (5.5, 6.5, 7.5)]
    assert len(mouths[0]) == 0 < len(mouths[1]) < len(mouths[2]), "shut (her smile), then half, then open"
    _, smiling = _at(START + 5.5, lips=lips)
    assert MeridaShoots.COLORS["m"] in smiling.values(), "a closed smile"


def test_the_nocked_arrow_shows_while_she_aims():
    shaft = MeridaShoots.COLORS["a"]
    for t in (poses.DRAW + 0.1, poses.LEAN_AT + 0.4, MeridaShoots.LOOSE_S - 0.05):
        _, out = _at(START + t)
        assert sum(rgb == shaft for rgb in out.values()) >= 8, f"{t}: the arrow's hidden"


def test_on_touch_her_arrow_flies_off_the_string_fast_into_the_bullseye_and_it_shatters():
    actor, before = _at(START + MeridaShoots.TARGET_S - 0.1)
    cx, cy = actor.target
    gold = MeridaShoots.RINGS[0][1]
    assert (cx, cy) not in before, "no target before its burst"
    assert actor.hit_s - actor.LOOSE_S < 0.25, "the archer's speed, not a drift"
    _, hanging = _at(START + MeridaShoots.LOOSE_S - 0.05)
    r, g, b = hanging[(cx, cy)]
    assert r > 150 and g > 3 * b, "its gold centre (twinkling)"
    actor, leaving = _at(START + MeridaShoots.LOOSE_S + 0.01)
    assert actor.arrow_tail(actor.elapsed()) < 1, "it leaves from where it sat on the string"
    actor, hit = _at(START + actor.hit_s - 0.005)
    d = actor.arrow_tail(actor.elapsed())
    (nx, ny), (ux, uy) = actor.nock, actor.aim
    head = (nx + ux * (d + Archer.ARROW_LEN - 1), ny + uy * (d + Archer.ARROW_LEN - 1))
    assert abs(head[0] - (cx + 0.5)) <= 1.5 and abs(head[1] - (cy + 0.5)) <= 1.5, "it strikes the centre"
    assert hit.get((int(head[0]), int(head[1]))) == Archer.TIP_RGB
    _, shattered = _at(START + actor.hit_s + 0.4)
    ring = {(x, y) for x in range(cx - 4, cx + 5) for y in range(cy - 4, cy + 5)}
    assert gold not in [shattered.get(xy) for xy in ring], "the target's gone"
    assert any(abs(x - cx) > 5 and y < 40 for x, y in shattered if x > 36), "its sparks fly out"
    _, after = _at(START + actor.hit_s + MeridaShoots.SHATTER_S + 0.1)
    assert all(x < 40 for x, _ in after), "then only Merida again"


def test_the_bullseye_sits_on_her_aim_high_on_the_right():
    actor, _ = _at(START + 1)
    cx, cy = actor.target
    assert cx == MeridaShoots.TARGET_X and 8 <= cy <= 26
    (nx, ny), (ux, uy) = actor.nock, actor.aim
    k = (cx + 0.5 - nx) / ux
    assert abs(ny + uy * k - (cy + 0.5)) <= 0.5


def test_merida_follows_the_clock_not_the_frames():
    frames = []
    for fps in (30, 7):
        show = MusicShow(64, 64, random.Random(2))
        actor, cue = MeridaShoots(show), _scene()
        i = 0
        while START + i / fps <= START + MeridaShoots.LOOSE_S + 0.1:
            _frame(show, actor, cue, START + i / fps)
            i += 1
        frames.append(_frame(show, actor, cue, START + MeridaShoots.LOOSE_S + 0.1))
    assert frames[0] == frames[1]


def test_merida_draws_nothing_when_inactive():
    show = MusicShow(64, 64, random.Random(3))
    actor = MeridaShoots(show)
    assert _frame(show, actor, _scene(), START + 5, active=False) == {}
