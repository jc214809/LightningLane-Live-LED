import random

import pytest

import display.fireworks.music_show as music_show
from display.fireworks import show_actors
from display.fireworks.fireworks import _CASTLE_COLORS
from display.fireworks.music_show import CASTLE_LOOKS, SHAPES, MusicShow, render_music_show
from display.animation.characters.tink import TinkReveal
from display.fireworks.score import Cue, Hit, Score, load_score


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
    show.set_cue(_cue(start=0, end=6, rate=0), 5.9)
    assert show.white == 0, "not before its scene"
    last_hit = _cue(title="last hit", start=6, end=10, rate=0, effects={"final_flash"})
    show.set_cue(last_hit, 6)
    pixels = show.frame_pixels()
    assert len(pixels) == 64 * 32 and min(min(rgb) for rgb in pixels.values()) == 255, "on the hit"
    for i in range(60):
        show.step()
        show.set_cue(last_hit, 6 + i / 30)
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



def test_each_scene_logs_how_fast_the_board_kept_up(clock, monkeypatch):
    slow = clock(0.25)  # 4 fps
    logged = []
    monkeypatch.setattr(music_show.debug, "info", logged.append)
    monkeypatch.setattr(music_show.system_stats, "describe", lambda: "load 1.0, 60°C")
    render_music_show(FakeMatrix(), _score(), rng=random.Random(0), clock=slow)
    rates = [line for line in logged if "fps" in line]
    assert len(rates) == 2, "each scene, the last one too"
    for line, title in zip(rates, ("one", "two")):
        assert line.startswith(f"test {title}: 4.0 fps (aiming for 30), slowest frame 250 ms (build 0 / push 250), "
                               "8 late, ")
        assert line.endswith(", load 1.0, 60°C")
        assert " px, CPU show " in line and " / process " in line


def test_a_scenes_log_counts_only_the_frames_past_their_slot(clock, monkeypatch):
    quick = clock(0.01)
    logged = []
    monkeypatch.setattr(music_show.debug, "info", logged.append)
    render_music_show(FakeMatrix(), _score(), rng=random.Random(0), clock=quick)
    assert all(", 0 late, " in line for line in logged if "fps" in line)


def test_a_scenes_log_reports_cpu_of_the_show_thread_against_the_process(clock, monkeypatch):
    quick = clock(0.01)
    logged = []
    monkeypatch.setattr(music_show.debug, "info", logged.append)
    monkeypatch.setattr(music_show.system_stats, "describe", lambda: "")
    cpu = {"thread": 0.0, "process": 0.0}

    def thread_time():  # a second of the show thread per 4s scene check, twice that for the whole process
        cpu["thread"] += 0.5
        cpu["process"] += 1.0
        return cpu["thread"]
    monkeypatch.setattr(music_show.time, "thread_time", thread_time)
    monkeypatch.setattr(music_show.time, "process_time", lambda: cpu["process"])
    render_music_show(FakeMatrix(), _score(), rng=random.Random(0), clock=quick)
    first = next(line for line in logged if "test one" in line and "fps" in line)
    assert "CPU show 25% / process 50%" in first, "0.5s and 1s of CPU over the scene's 2s"
    assert not first.endswith(", "), "no board state, no trailing comma"


def test_the_start_line_says_which_version_plays(clock, monkeypatch):
    logged = []
    monkeypatch.setattr(music_show.debug, "info", logged.append)
    render_music_show(FakeMatrix(), _score()._replace(version="v2"), rng=random.Random(0), clock=clock(0.01))
    assert logged[0].startswith("Playing the test show (v2) for 4s")


def test_building_the_show_doesnt_put_the_picture_behind_the_music(clock, monkeypatch):
    fake = clock(0.01)
    built = MusicShow.__init__

    def slow_build(self, *args, **kwargs):  # a Pi Zero drawing every character's poses up front
        built(self, *args, **kwargs)
        fake.now += 1.5
    monkeypatch.setattr(MusicShow, "__init__", slow_build)
    seen = []
    original = MusicShow.set_cue
    monkeypatch.setattr(MusicShow, "set_cue", lambda self, cue, t: (seen.append(t), original(self, cue, t)))
    render_music_show(FakeMatrix(), _score(), rng=random.Random(0), clock=fake)
    assert seen[0] >= 1.5, "the first frame is where the music is by then, not its start"

# ---- Tink in "You Can Fly" ----

def _tink_cue():
    return _cue(title="You Can Fly", start=100, end=142, rate=1.4, effects={"tink"})


@pytest.mark.parametrize("height", [32, 64])
def test_tink_takes_off_from_the_spire_and_flies_out_to_the_right(height):
    show = MusicShow(64, height, random.Random(14))
    cue = _tink_cue()
    show.set_cue(cue, 100)
    x0, y0 = show.tink_at()
    assert x0 == pytest.approx(show.spire[0])
    assert y0 + show.tink_h / 2 == pytest.approx(show.spire[1], abs=1), "feet on the spire"
    path = []
    for i in range(int(music_show.TINK_FLY_S * 10)):
        show.set_cue(cue, 100 + i / 10)
        path.append(show.tink_at())
    xs = [x for x, _ in path]
    assert xs == sorted(xs), "always heading right"
    # The spire is near the top, so she climbs only a little: to the top fifth of the sky.
    assert min(y for _, y in path) < y0 and min(y for _, y in path) <= height * 0.2 + show.tink_scale
    assert xs[-1] - show.tink_w / 2 > 60, "nearly off the right edge"
    show.set_cue(cue, 100 + music_show.TINK_FLY_S)
    assert show.tink_at() is None, "gone after her flight"


@pytest.mark.parametrize("height, size", [(32, (9, 8)), (64, (18, 16))])
def test_tink_is_her_fly_by_size_and_drawn_over_the_castle(height, size):
    show = MusicShow(64, height, random.Random(15))
    show.set_cue(_tink_cue(), 100.5)
    assert (show.tink_w, show.tink_h) == size
    pixels = show.frame_pixels()
    dress = TinkReveal.colors["G"]
    assert sum(1 for rgb in pixels.values() if rgb == dress) >= 8 * (size[0] // 9) ** 2


def test_tink_leaves_pixie_dust_that_fades_after_she_has_gone():
    show = MusicShow(64, 32, random.Random(16))
    cue = _tink_cue()
    _run(show, cue, 6, start=100)
    assert show.dust and {d[6] for d in show.dust} <= set(TinkReveal.dust_colors)
    _run(show, cue, 4, start=100 + music_show.TINK_FLY_S)
    assert not show.dust


def test_the_fireworks_hold_back_while_tink_flies():
    show = MusicShow(64, 32, random.Random(17))
    cue = _tink_cue()
    show.set_cue(cue, 101)
    assert show.rate == pytest.approx(1.4 * music_show.TINK_RATE)
    show.set_cue(cue, 100 + music_show.TINK_FLY_S)
    assert show.rate == pytest.approx(1.4)


def test_tink_flies_in_happily_ever_afters_you_can_fly():
    assert "tink" in load_score("happily-ever-after").cue_at(1043).effects


# ---- stages and actors (later versions) ----

def _castle_max(show):
    """The brightest channel of any castle pixel this frame, with the stars and flash out of the way."""
    show.stars, show.flash = [], [0.0, 0.0, 0.0]
    pixels = show.frame_pixels()
    return max((max(pixels.get((show.castle_x + dx, show.castle_y + dy), (0, 0, 0)))
                for dx, dy, _ in show.castle_pixels), default=0)


@pytest.mark.parametrize("height", [32, 64])
def test_the_castle_fades_to_a_ghost_then_off_and_back(height):
    show = MusicShow(64, height, random.Random(20))
    show.set_cue(_cue(rate=0), 0)
    full = _castle_max(show)
    ghost = _cue(title="ghost", start=10, end=20, rate=0)._replace(stage="ghost")
    show.set_cue(ghost, 10)
    assert _castle_max(show) == full, "starts from full"
    show.set_cue(ghost, 10 + music_show.CASTLE_FADE_S)
    assert _castle_max(show) == int(full * music_show.STAGE_LEVELS["ghost"])
    off = _cue(title="off", start=20, end=30, rate=0)._replace(stage="off")
    show.set_cue(off, 20)
    show.set_cue(off, 20 + music_show.CASTLE_FADE_S / 2)
    assert 0 < _castle_max(show) < full * music_show.STAGE_LEVELS["ghost"], "fading from the ghost"
    show.set_cue(off, 20 + music_show.CASTLE_FADE_S)
    assert _castle_max(show) == 0
    back = _cue(title="back", start=30, end=40, rate=0)
    show.set_cue(back, 30)
    show.set_cue(back, 30 + music_show.CASTLE_FADE_S)
    assert _castle_max(show) == full


def test_a_timed_stage_change_brings_the_castle_back_mid_scene():
    show = MusicShow(64, 32, random.Random(22))
    show.set_cue(_cue(rate=0), 0)
    full = _castle_max(show)
    scene = _cue(title="stars then castle", start=10, end=30, rate=0)._replace(
        stage="off", stage_changes=((20.0, "castle"),))
    show.set_cue(scene, 10)
    show.set_cue(scene, 10 + music_show.CASTLE_FADE_S)
    assert _castle_max(show) == 0
    show.set_cue(scene, 20)
    show.set_cue(scene, 20 + music_show.CASTLE_FADE_S)
    assert _castle_max(show) == full


def test_a_timed_castle_change_fades_to_the_new_look_mid_scene():
    show = MusicShow(64, 64, random.Random(23))
    scene = _cue(start=0, end=20, rate=0, castle="green", effects=("wipe_down",))._replace(
        castle_changes=((10.0, "pink"),))
    show.set_cue(scene, 0)
    show.set_cue(scene, music_show.WIPE_S + 1)
    green = _castle_rgb(show)
    show.set_cue(scene, 10)
    assert not show.castle_wipe, "only the scene's own look wipes down"
    assert _castle_rgb(show) == green, "starts from the green"
    show.set_cue(scene, 10 + music_show.CASTLE_FADE_S)
    assert _castle_rgb(show) == tuple(int(c * 0.75) for c in CASTLE_LOOKS["pink"]["W"])


def test_fireworks_show_through_a_ghost_castle():
    show = MusicShow(64, 32, random.Random(21))
    ghost = _cue(rate=0)._replace(stage="ghost")
    show.set_cue(ghost, 0)
    show.set_cue(ghost, music_show.CASTLE_FADE_S)
    dx, dy, _ = show.castle_pixels[len(show.castle_pixels) // 2]
    x, y = show.castle_x + dx, show.castle_y + dy
    show.sparks.append(music_show._Spark(x, y, 0, 0, 40, (0, 255, 0), gravity=0))
    show.flash = [0.0, 0.0, 0.0]
    assert show.frame_pixels()[(x, y)][1] > 200, "a ghost doesn't hide what's behind it"


class _Marker(show_actors.Actor):
    """A test actor: a white pixel on the castle's middle while its scene is on, at a spot that moves
    one column a second, and a record of each step."""
    def __init__(self, show):
        super().__init__(show)
        self.steps = []

    def step(self, active):
        self.steps.append(active)

    def draw(self, put, out, active):
        if active:
            show = self.show
            out[(show.castle_x + int(self.elapsed()), show.castle_y + show.castle_h // 2)] = (255, 255, 255)


@pytest.fixture
def marker(monkeypatch):
    monkeypatch.setitem(show_actors.ACTORS, "marker", _Marker)


def test_an_actor_draws_in_front_of_the_castle_only_in_its_scene(marker):
    show = MusicShow(64, 32, random.Random(22))
    plain, with_marker = _cue(rate=0), _cue(title="m", start=10, end=20, rate=0)._replace(actors=("marker",))
    spot = (show.castle_x + 3, show.castle_y + show.castle_h // 2)
    show.set_cue(plain, 9)
    show.step()
    assert show.frame_pixels().get(spot) != (255, 255, 255)
    show.set_cue(with_marker, 13)
    show.step()
    assert show.frame_pixels()[spot] == (255, 255, 255), "placed by the clock: 3 s into its scene"
    assert show.actors["marker"].steps == [False, True]


# ---- a scene's set-moment hits ----

def _hit_cue(*hits):
    return _cue(rate=0)._replace(hits=tuple(hits))


def _bursts(show, monkeypatch):
    """Record every burst as (t, x, y, colour, style), still exploding it."""
    bursts, explode = [], show._explode
    monkeypatch.setattr(show, "_explode", lambda r: (bursts.append((show.t, r.x, r.y, r.color, r.style)), explode(r)))
    return bursts


@pytest.mark.parametrize("height", [32, 64])
def test_a_shell_hit_bursts_once_where_and_when_the_score_says(monkeypatch, height):
    show = MusicShow(64, height, random.Random(1))
    bursts = _bursts(show, monkeypatch)
    _run(show, _hit_cue(Hit(5.0, "shell", (255, 0, 0), 0.3, 0.25, "willow")), 10)
    assert len(bursts) == 1
    t, x, y, rgb, style = bursts[0]
    assert t == pytest.approx(5.0, abs=0.4), "launched early by its climb, so it bursts on the hit"
    assert x == pytest.approx(0.3 * 64) and y == pytest.approx(0.25 * height, abs=2)
    assert (rgb, style) == ((255, 0, 0), "willow")


def test_a_curtain_shell_is_bigger_and_hangs_longer_than_a_willow(monkeypatch):
    sparks = {}
    for style in ("willow", "curtain"):
        show = MusicShow(64, 32, random.Random(1))
        _run(show, _hit_cue(Hit(1.0, "shell", (60, 230, 90), style=style)), 1.5)
        sparks[style] = show.sparks
    assert len(sparks["curtain"]) > len(sparks["willow"])
    assert max(s.life for s in sparks["curtain"]) > max(s.life for s in sparks["willow"])
    assert all(s.color == (60, 230, 90) for s in sparks["curtain"]), "in the hit's own colour"


def test_a_hit_already_well_past_when_the_show_starts_is_skipped(monkeypatch):
    show = MusicShow(64, 32, random.Random(1))
    bursts = _bursts(show, monkeypatch)
    _run(show, _hit_cue(Hit(5.0, "shell", (255, 0, 0))), 2, start=7.0)
    assert not bursts and not show.rockets


@pytest.mark.parametrize("height", [32, 64])
def test_a_roof_fan_hit_fires_comets_outward_from_both_side_roofs(height):
    show = MusicShow(64, height, random.Random(1))
    cue = _hit_cue(Hit(2.0, "roof_fan", (255, 255, 255)))
    _run(show, cue, 1.9)
    assert not show.hit_comets.comets
    _run(show, cue, 0.2, start=1.9)
    comets = show.hit_comets.comets
    left = [c for c in comets if c[0] < show.width / 2]
    right = [c for c in comets if c[0] >= show.width / 2]
    assert len(left) == len(right) == show.hit_comets.FAN
    assert all(c[2] < 0 for c in left) and all(c[2] > 0 for c in right), "fanning outward"
    assert all(c[3] < 0 for c in comets), "and up"
    pixels = show.frame_pixels()
    assert any((round(c[0]), round(c[1])) in pixels for c in comets)
    _run(show, cue, 3, start=2.1)
    assert not show.hit_comets.comets, "fired once, then gone"


def test_a_comet_hit_flies_up_and_away_from_its_side():
    show = MusicShow(64, 32, random.Random(1))
    _run(show, _hit_cue(Hit(1.0, "comet", (255, 200, 60), side="right")), 1.5)
    (x, y, vx, *_), = show.hit_comets.comets
    assert x < 63 and y < 31 and vx < 0


@pytest.mark.parametrize("height", [32, 64])
def test_a_wipe_down_turns_the_castle_from_the_spire_to_its_base(height):
    show = MusicShow(64, height, random.Random(1))
    _run(show, _cue(castle="red", rate=0), 2)
    wipe = _cue(title="drop", start=2, end=20, castle="blue", rate=0, effects=("wipe_down",))
    top_dx, top_dy, _ = min((p for p in show.castle_pixels if p[2] == "W"), key=lambda p: p[1])
    low_dx, low_dy, _ = max((p for p in show.castle_pixels if p[2] == "W"), key=lambda p: p[1])
    top = (show.castle_x + top_dx, show.castle_y + top_dy)
    low = (show.castle_x + low_dx, show.castle_y + low_dy)
    _run(show, wipe, music_show.WIPE_S * 0.45, start=2)
    show.flash = [0.0, 0.0, 0.0]
    frame = show.frame_pixels()
    assert frame[top][2] > frame[top][0], "blue at the top"
    assert frame[low][0] > frame[low][2], "still red at the base"
    _run(show, wipe, music_show.WIPE_S * 0.6, start=2 + music_show.WIPE_S * 0.45)
    show.flash = [0.0, 0.0, 0.0]
    frame = show.frame_pixels()
    assert frame[low][2] > frame[low][0], "blue all the way down"
