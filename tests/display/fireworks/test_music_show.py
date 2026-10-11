import random

import pytest

import display.fireworks.music_show as music_show
from display.fireworks.fireworks import _CASTLE_COLORS
from display.fireworks.music_show import CASTLE_LOOKS, SHAPES, MusicShow, render_music_show
from display.fireworks.score import Cue, Score, load_score


def _cue(title="x", start=0.0, end=10.0, palette=((255, 0, 0),), rate=1.0, castle=None, shapes=(),
         effects=()):
    return Cue("s", title, start, end, tuple(palette), rate, castle, tuple(shapes), frozenset(effects))


def _run(show, cue, seconds, start=0.0, fps=30):
    for i in range(int(seconds * fps)):
        t = start + i / fps
        show.set_cue(cue, t)
        show.step()


def _castle_rgb(show, kind="W"):
    dx, dy, _ = next(p for p in show.castle_pixels if p[2] == kind)
    show.flash = [0.0, 0.0, 0.0]
    return show.frame_pixels()[(show.castle_x + dx, show.castle_y + dy)]


@pytest.mark.parametrize("height", [32, 64])
def test_the_whole_show_stays_on_the_board_with_valid_colours(height):
    hea = load_score("happily-ever-after")
    show = MusicShow(64, height, random.Random(1))
    for i in range(0, int(hea.end * 30), 7):  # every scene, a frame now and then
        t = i / 30
        show.set_cue(hea.cue_at(t), t)
        show.step()
        for (x, y), rgb in show.frame_pixels().items():
            assert 0 <= x < 64 and 0 <= y < height
            assert len(rgb) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)


def test_a_dark_scene_launches_nothing():
    show = MusicShow(64, 32, random.Random(2))
    _run(show, _cue(rate=0), 10)
    assert not show.rockets and not show.sparks


def test_a_busier_scene_launches_more():
    def launches(rate):
        show = MusicShow(64, 32, random.Random(3))
        count = 0
        original = show.launch

        def counted():
            nonlocal count
            count += 1
            original()
        show.launch = counted
        _run(show, _cue(rate=rate), 20)
        return count
    assert launches(2.5) > 1.8 * launches(1.0) > 0


def test_bursts_use_the_scenes_palette():
    show = MusicShow(64, 32, random.Random(4))
    _run(show, _cue(palette=[(0, 255, 0)]), 3)
    assert {r.color for r in show.rockets} | {s.color for s in show.sparks} <= {(0, 255, 0)}


def test_rainbow_bursts_cycle_through_colours():
    show = MusicShow(64, 32, random.Random(5))
    _run(show, _cue(rate=2.5, effects={"rainbow"}), 6)
    assert len({s.color for s in show.sparks}) > 5


@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("height", [32, 64])
def test_shape_bursts_fit_on_the_board(shape, height):
    for seed in range(30):
        show = MusicShow(64, height, random.Random(seed))
        show.set_cue(_cue(shapes=[(shape, 1.0)]), 0)
        show.launch()
        rocket = show.rockets[-1]
        assert rocket.shape == shape
        reach = show.shape_radius
        assert reach <= rocket.x <= 64 - reach and rocket.burst_y - reach >= 0


def test_a_shape_burst_keeps_its_outline():
    show = MusicShow(64, 64, random.Random(6))
    show.set_cue(_cue(rate=0), 0)
    show._explode(music_show._Rocket(32, 20, 0, -1, 20, (255, 0, 0), "heart"))
    assert len(show.sparks) == len(SHAPES["heart"])
    assert len({s.max_life for s in show.sparks}) == 1, "the shape grows and fades together"


def test_the_castle_fades_to_a_new_look():
    show = MusicShow(64, 32, random.Random(7))
    show.set_cue(_cue(rate=0), 0)
    everyday = _castle_rgb(show)
    show.set_cue(_cue(title="gold", start=10, end=20, rate=0, castle="gold"), 10)
    assert _castle_rgb(show) == everyday, "starts from the old look"
    show.set_cue(show.cue, 10 + music_show.CASTLE_FADE_S / 2)
    halfway = _castle_rgb(show)
    show.set_cue(show.cue, 10 + music_show.CASTLE_FADE_S)
    gold = _castle_rgb(show)
    assert gold == tuple(int(c * 0.75) for c in CASTLE_LOOKS["gold"]["W"])
    assert halfway not in (everyday, gold)


def test_the_castle_turns_blue_only_once_the_wishing_star_lands():
    show = MusicShow(64, 64, random.Random(8))
    show.set_cue(_cue(rate=0), 0)
    everyday = _castle_rgb(show)
    wish = _cue(title="wish", start=10, end=20, rate=0, castle="blue", effects={"wishing_star"})
    show.set_cue(wish, 13)
    assert _castle_rgb(show) == everyday, "still falling"
    show.set_cue(wish, 10 + 10 * music_show.WISH_LANDS_AT + music_show.CASTLE_FADE_S)
    assert _castle_rgb(show) == tuple(int(c * 0.75) for c in CASTLE_LOOKS["blue"]["W"])


@pytest.mark.parametrize("height", [32, 64])
def test_the_wishing_star_falls_onto_the_spire(height):
    show = MusicShow(64, height, random.Random(9))
    wish = _cue(start=0, end=10, rate=0, effects={"wishing_star"})
    show.set_cue(wish, 0)
    first = show._wish_path(0)
    assert first[1] < show.spire[1] and first[0] > show.spire[0], "from the top right"
    assert show._wish_path(music_show.WISH_LANDS_AT) == pytest.approx(show.spire)
    assert show._wish_path(1.0) == pytest.approx(show.spire), "and stays"
    show.set_cue(wish, 9)
    assert show.frame_pixels()[show.spire] == music_show.WISH_RGB


def test_lanterns_rise_and_stop_coming_after_their_scene():
    show = MusicShow(64, 32, random.Random(10))
    _run(show, _cue(rate=0, effects={"lanterns"}), 8)
    assert len(show.lanterns) > 10
    y = {id(lantern): lantern[1] for lantern in show.lanterns}
    show.step()
    assert all(lantern[1] < y[id(lantern)] for lantern in show.lanterns if id(lantern) in y)
    _run(show, _cue(title="next", rate=0), 30, start=8)
    assert not show.lanterns


def test_embers_fall_and_fade():
    show = MusicShow(64, 32, random.Random(11))
    _run(show, _cue(rate=0, effects={"embers"}), 4)
    assert show.embers
    _run(show, _cue(title="next", rate=0), 10, start=4)
    assert not show.embers


def test_the_final_flash_whites_out_the_board_once_then_fades():
    show = MusicShow(64, 32, random.Random(12))
    final = _cue(start=0, end=10, rate=0, effects={"final_flash"})
    show.set_cue(final, 8.5)
    assert show.white == 0, "not until the last second"
    show.set_cue(final, 9.2)
    pixels = show.frame_pixels()
    assert len(pixels) == 64 * 32 and min(min(rgb) for rgb in pixels.values()) == 255
    for _ in range(60):
        show.step()
        show.set_cue(final, 9.5)
    assert show.white < 0.02, "fades, and doesn't fire again"


def test_the_fire_castle_flickers():
    show = MusicShow(64, 32, random.Random(13))
    show.set_cue(_cue(rate=0, castle="fire"), 0)
    show.set_cue(show.cue, 5)
    frames = []
    for _ in range(5):
        show.step()
        frames.append(_castle_rgb(show))
    assert len(set(frames)) > 1


class FakeCanvas:
    def __init__(self):
        self.pixels = {}

    def Clear(self):
        self.pixels = {}

    def SetPixel(self, x, y, r, g, b):
        self.pixels[(x, y)] = (r, g, b)


class FakeMatrix:
    def __init__(self, width=64, height=32):
        self.width, self.height = width, height
        self.swaps = 0
        self.cleared = False

    def CreateFrameCanvas(self):
        return FakeCanvas()

    def SwapOnVSync(self, canvas):
        self.swaps += 1
        return FakeCanvas()

    def Clear(self):
        self.cleared = True


class FakeClock:
    """Time moves only when a frame is drawn (frame_s of drawing) or the show sleeps."""

    def __init__(self, frame_s):
        self.now, self.frame_s = 0.0, frame_s

    def __call__(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    def make(frame_s):
        fake = FakeClock(frame_s)
        monkeypatch.setattr(music_show.time, "sleep", lambda s: setattr(fake, "now", fake.now + s))

        def present(matrix, canvas):
            fake.now += fake.frame_s
            matrix.swaps += 1
            return canvas
        monkeypatch.setattr(music_show, "present", present)
        return fake
    return make


def _score():
    return Score("test", 4.0, (_cue("one", 0, 2), _cue("two", 2, 4, castle="gold")))


def test_render_plays_until_the_score_ends(clock):
    fast = clock(0.01)  # a quick board: draws in 10ms, sleeps out the rest of each frame
    matrix = FakeMatrix()
    render_music_show(matrix, _score(), rng=random.Random(0), clock=fast)
    assert 118 <= matrix.swaps <= 122, "4s at 30fps"
    assert matrix.cleared


def test_a_slow_board_keeps_time_with_the_music(clock, monkeypatch):
    # 4 fps instead of 30: fewer frames, but each scene still starts on its second.
    slow = clock(0.25)
    seen = []
    original = MusicShow.set_cue
    monkeypatch.setattr(MusicShow, "set_cue", lambda self, cue, t: (seen.append((t, cue.title)), original(self, cue, t)))
    render_music_show(FakeMatrix(), _score(), rng=random.Random(0), clock=slow)
    assert len(seen) == 16
    assert all(title == ("one" if t < 2 else "two") for t, title in seen)
    assert seen[-1][0] >= 3.5

