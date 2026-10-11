import random

import pytest

from display.fireworks import show_effects
from display.fireworks.music_show import CASTLE_LOOKS, EFFECTS, SHAPES, MusicShow
from display.fireworks.score import Cue, load_score


def _cue(start=0.0, end=20.0, effects=(), castle=None, rate=0.0, title="x"):
    return Cue("s", title, start, end, ((255, 0, 0),), rate, castle, (), frozenset(effects))


def _run(show, cue, seconds, start=None, fps=30):
    start = cue.start if start is None else start
    for i in range(int(seconds * fps)):
        t = start + i / fps
        show.set_cue(cue, t)
        show.step()


def _frame(effects, seconds=12, height=32, seed=1, castle=None):
    show = MusicShow(64, height, random.Random(seed))
    show.stars = []  # the background twinkle differs frame to frame
    _run(show, _cue(effects=effects, castle=castle), seconds)
    return show, show.frame_pixels()


def test_every_effect_is_known_to_the_score():
    assert set(show_effects.EFFECTS) <= EFFECTS


@pytest.mark.parametrize("name", sorted(show_effects.EFFECTS))
@pytest.mark.parametrize("height", [32, 64])
def test_each_effect_draws_something_on_the_board(name, height):
    """Somewhere in its first 12 seconds (some come and go, like flame jets)."""
    _, plain = _frame((), height=height)
    show = MusicShow(64, height, random.Random(1))
    show.stars = []
    cue, drew = _cue(effects=(name,)), False
    for i in range(12 * 30):
        show.set_cue(cue, i / 30)
        show.step()
        if i % 10:
            continue
        frame = show.frame_pixels()
        drew = drew or frame != plain
        for (x, y), rgb in frame.items():
            assert 0 <= x < 64 and 0 <= y < height
            assert len(rgb) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)
    assert drew, f"{name} drew nothing"


@pytest.mark.parametrize("name", sorted(show_effects.EFFECTS))
def test_each_effect_clears_away_after_its_scene(name):
    show = MusicShow(64, 32, random.Random(2))
    show.stars = []
    _run(show, _cue(effects=(name,)), 15)
    _run(show, _cue(start=15, end=60, title="next"), 30)
    assert not _leftovers(show), f"{name} still draws long after its scene"


def _leftovers(show):
    """Anything an effect still draws once its scene is long over."""
    pixels = {}
    put = lambda x, y, rgb: pixels.__setitem__((int(x), int(y)), rgb)
    for effect in show.extras.values():
        effect.draw_behind(put, pixels, False)
        effect.draw_front(put, pixels, False)
    return pixels


def test_the_water_rises_only_from_halfway_and_drains_after():
    show = MusicShow(64, 32, random.Random(3))
    touch = _cue(start=0, end=40, effects=("water",))
    _run(show, touch, 19)
    assert show.extras["water"].level == 0, "dry for the first half"
    _run(show, touch, 15, start=20)
    risen = show.extras["water"].level
    assert risen > 0.9
    interlude = _cue(start=40, end=47, effects=("water",), title="interlude")
    _run(show, interlude, 2, start=40)
    assert show.extras["water"].level >= risen, "the next scene with water keeps it up from its start"
    _run(show, _cue(start=50, end=90, title="dry"), 15, start=50)
    assert show.extras["water"].level == 0


def test_the_water_covers_the_bottom_of_the_castle_in_front():
    show = MusicShow(64, 32, random.Random(4))
    _run(show, _cue(start=0, end=60, effects=("water",)), 50)
    pixels = show.frame_pixels()
    door_x = show.castle_x + show.castle_w // 2
    assert pixels[(door_x, show.height - 1)][2] > pixels[(door_x, show.height - 1)][0], "blue over the door"


def test_the_moon_rises_from_behind_the_castle_and_stays_up_through_its_scenes():
    show = MusicShow(64, 64, random.Random(5))
    _run(show, _cue(start=0, end=36, effects=("moon_rise",)), 20)
    moon = show.extras["moon_rise"]
    assert moon.rise == 1 and moon.level == 1
    _run(show, _cue(start=36, end=52, effects=("moon_rise",), title="love tonight"), 5, start=36)
    assert moon.level == 1
    _run(show, _cue(start=52, end=80, title="next"), 5, start=52)
    assert moon.level == 0


def test_blocks_land_on_the_ground_beside_the_castle():
    show = MusicShow(64, 64, random.Random(6))
    _run(show, _cue(effects=("blocks",)), 12)
    blocks = show.extras["blocks"]
    landed = [b for b in blocks.blocks if b[1] == show.height - blocks.size]
    assert landed
    for x, _, _, _, _ in landed:
        assert x + blocks.size <= show.castle_x or x >= show.castle_x + show.castle_w, "not on the castle"


def test_bolts_flash_the_castle():
    show = MusicShow(64, 32, random.Random(7))
    peak = 0
    for i in range(300):
        show.set_cue(_cue(effects=("bolts",)), i / 30)
        show.step()
        peak = max(peak, max(show.flash))
    assert peak > 0.3


def test_the_keyhole_opens_from_the_door_to_the_whole_sky():
    show = MusicShow(64, 32, random.Random(8))
    show.stars = []
    cue = _cue(start=0, end=19, effects=("keyhole_open",))
    _run(show, cue, 1)
    early = sum(1 for rgb in show.frame_pixels().values() if rgb[0] > 0)
    _run(show, cue, 11, start=1)
    late = sum(1 for rgb in show.frame_pixels().values() if rgb[0] > 0)
    assert late > 3 * early


def test_the_keyhole_stays_open_into_the_next_scene_that_keeps_it():
    """The last hit is its own scene: the keyhole mustn't close and open again on it."""
    show = MusicShow(64, 32, random.Random(8))
    _run(show, _cue(start=0, end=13, effects=("keyhole_open",)), 13)
    keyhole = show.extras["keyhole_open"]
    assert keyhole.opened() == 1
    _run(show, _cue(start=13, end=17, effects=("keyhole_open",), title="last hit"), 1, start=13)
    assert keyhole.opened() == 1
    _run(show, _cue(start=17, end=30, title="after"), 1, start=17)
    assert keyhole.opened() == 0


@pytest.mark.parametrize("name, colours", [
    ("searchlights", show_effects.Searchlights.COLOURS),
    ("searchlights_gold", show_effects.GoldSearchlights.COLOURS),
    ("searchlights_green", show_effects.GreenSearchlights.COLOURS),
    ("searchlights_teal", show_effects.TealSearchlights.COLOURS),
])
def test_searchlights_shine_in_their_colours(name, colours):
    show = MusicShow(64, 32, random.Random(14))
    show.set_cue(_cue(effects=(name,)), 1)
    pixels = {}
    show.extras[name].draw_behind(lambda x, y, rgb: pixels.__setitem__((int(x), int(y)), rgb), pixels, True)
    # The beam's brightest LED, at its foot, is 85% of its colour.
    assert {tuple(int(c * 0.85) for c in rgb) for rgb in colours} <= set(pixels.values())


def test_party_searchlights_change_colour():
    show = MusicShow(64, 32, random.Random(15))
    beams = show.extras["searchlights_party"]
    show.t = 0
    first = beams.colours()
    show.t = 2
    assert beams.colours() != first


def test_comet_fans_rise_from_the_castles_foot_and_spread_out():
    show = MusicShow(64, 32, random.Random(16))
    _run(show, _cue(effects=("comet_fan",)), 1 / 30)
    comets = show.extras["comet_fan"].comets
    assert len(comets) >= 5
    assert all(c[1] >= show.height - 2 and c[3] < 0 for c in comets), "from the ground, going up"
    assert min(c[2] for c in comets) < 0 < max(c[2] for c in comets), "fanning both ways"


def test_crossing_comets_cross_over_the_spire():
    show = MusicShow(64, 32, random.Random(17))
    effect = show.extras["crossing_comets"]
    _run(show, _cue(effects=("crossing_comets",)), 1 / 30)
    left, right = sorted(effect.comets[:2], key=lambda c: c[0])
    assert left[0] < show.spire[0] < right[0] and left[2] > 0 > right[2], "from either side, heading in"


def test_flame_jets_burst_from_the_castle_and_light_it():
    show = MusicShow(64, 32, random.Random(18))
    show.set_cue(_cue(effects=("flame_jets",)), 0)
    show.step()
    jets = show.extras["flame_jets"].jets
    assert jets and all((x, y) in show.extras["flame_jets"].spots for x, y, _ in jets)
    assert show.flash[0] > 0.5, "the castle lights up red-orange"


def test_willow_bursts_hang_in_gold():
    show = MusicShow(64, 32, random.Random(19))
    show.set_cue(_cue(effects=("willow",)), 0)
    from display.fireworks.music_show import WILLOW_RGB, _Rocket
    for _ in range(10):
        show._explode(_Rocket(32, 10, 0, -1, 10, (0, 0, 255)))
    gold = [s for s in show.sparks if s.color == WILLOW_RGB]
    assert gold and min(s.life for s in gold) >= 60, "long-lived gold"


@pytest.mark.parametrize("shape, colours", [
    ("lion", {(255, 200, 60), (220, 60, 30)}),
    ("smiley", {(255, 220, 40)}),
    ("bullseye", {(230, 40, 40), (255, 255, 255)}),
])
def test_coloured_shapes_burst_in_their_own_colours(shape, colours):
    show = MusicShow(64, 64, random.Random(9))
    show.set_cue(_cue(), 0)
    from display.fireworks.music_show import _Rocket
    show._explode(_Rocket(32, 20, 0, -1, 20, (0, 0, 255), shape))
    assert {s.color for s in show.sparks} == colours


@pytest.mark.parametrize("shape", ["door", "jellyfish"])
def test_plain_shapes_burst_in_the_rockets_colour(shape):
    show = MusicShow(64, 64, random.Random(10))
    show.set_cue(_cue(), 0)
    from display.fireworks.music_show import _Rocket
    show._explode(_Rocket(32, 20, 0, -1, 20, (0, 0, 255), shape))
    colours = {s.color for s in show.sparks}
    assert (0, 0, 255) in colours and len(colours) <= 2, "a door's knob is gold"


def test_stained_glass_tiles_the_walls_in_colour():
    show, frame = _frame((), castle="stained_glass", seconds=3)
    walls = {frame[(show.castle_x + dx, show.castle_y + dy)] for dx, dy, kind in show.castle_pixels if kind == "W"}
    assert len(walls) >= 4


@pytest.mark.parametrize("look", ["jungle", "pink"])
def test_new_castle_looks_change_the_walls(look):
    show, frame = _frame((), castle=look, seconds=3)
    dx, dy, _ = next(p for p in show.castle_pixels if p[2] == "W")
    assert frame[(show.castle_x + dx, show.castle_y + dy)] == tuple(int(c * 0.75) for c in CASTLE_LOOKS[look]["W"])


def test_every_scene_in_the_show_has_a_look():
    plain = [c.title for c in load_score("happily-ever-after").cues if not (c.effects or c.shapes or c.castle)]
    assert plain == []
