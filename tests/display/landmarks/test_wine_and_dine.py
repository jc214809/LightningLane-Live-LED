"""The Wine & Dine 5K landmark: Marie on a Paris night, clinking glasses beside a big 5K."""

import random

import pytest

import display.landmarks as landmarks
from display.landmarks import wine_and_dine as wd

from tests.display.landmarks.support import _scene_s

BOARDS = [(64, 32), (64, 64)]


def _scene(w, h):
    return landmarks.WineAndDine5KLandmark(w, h, random.Random(3))


def _box(pixels):
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    return min(xs), min(ys), max(xs), max(ys)


def _overlaps(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _marie_box(scene):
    x, y, w, h = scene.marie_box
    return x, y, x + w - 1, y + h - 1


@pytest.mark.parametrize("w, h", BOARDS)
def test_everything_fits_on_the_board(w, h):
    scene = _scene(w, h)
    x0, y0, x1, y1 = _marie_box(scene)
    assert 0 <= x0 and x1 < w and 0 <= y0 and y1 < h
    assert all(0 <= x < w and 0 <= y < h for x, y in scene.text), "the title isn't clipped"
    assert all(0 <= x < w and 0 <= y < h for x, y in scene._glass(scene.hers_x, scene.glass_y))


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_and_the_glasses_stay_clear_of_marie(w, h):
    scene = _scene(w, h)
    marie = _marie_box(scene)
    assert not _overlaps(_box(scene.text), marie)
    for x in (scene.hers_x, scene.friend_x):
        assert not _overlaps(_box(scene._glass(x, scene.glass_y)), marie), x


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_glasses_stay_clear_of_the_title_and_the_sparkle_too(w, h):
    scene = _scene(w, h)
    title = set(scene.text)
    for t in [i / 30 for i in range(int(_scene_s(type(scene)) * 30))]:
        glass = scene._glass(scene.friend_x, scene.friend_glass_y(t))
        assert not title & set(glass), t
        assert not title & set(scene.sparkle(t)), t
    assert not title & set(scene._glass(scene.hers_x, scene.glass_y))


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_title_reads_5k_over_wine_and_dine_in_its_own_fonts(w, h):
    scene = _scene(w, h)
    texts = [(font, text) for font, text, *_ in scene._layout()["title"]]
    assert texts == [(wd.BIG_FONT, "5K"), (wd.SMALL_FONT, "WINE &"), (wd.SMALL_FONT, "DINE")]
    pink = [p for p, rgb in scene.text.items() if rgb == wd.PINK]
    gold = [p for p, rgb in scene.text.items() if rgb == wd.GOLD]
    assert pink and gold
    assert _box(pink)[3] < _box(gold)[1], "5K sits above Wine & Dine"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_second_glass_rises_clinks_once_and_settles_level_with_hers(w, h):
    scene = _scene(w, h)
    scene_s = _scene_s(type(scene))
    assert scene.friend_glass_y(0) >= h, "hidden below the board at first"
    sparkling = [t for t in (i / 60 for i in range(int(scene_s * 60))) if scene.sparkle(t)]
    assert sparkling, "it clinks"
    assert sparkling[0] >= wd.RISE[1] - 1e-9, "only once it has risen"
    assert all(b - a < 0.05 for a, b in zip(sparkling, sparkling[1:])), "one clink, not a loop"
    assert sparkling[-1] <= scene_s - 1.0, "then it holds a second to read"
    assert scene.friend_glass_y(scene_s) == scene.glass_y, "level with hers at the end"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_rising_glass_comes_up_from_behind_the_tablecloth(w, h):
    scene = _scene(w, h)
    t = wd.RISE[0] + 0.15
    frame = scene.frame(t)
    glass = scene._glass(scene.friend_x, scene.friend_glass_y(t))
    under_cloth = [p for p in glass if p in scene.table]
    assert under_cloth, "part of it is still below the table edge"
    assert all(frame[p] == scene.table[p] for p in under_cloth)


def _distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


@pytest.mark.parametrize("w, h", BOARDS)
def test_marie_and_the_title_stand_out_from_the_purple_sky(w, h):
    scene = _scene(w, h)
    sky = scene.sky
    for p, rgb in scene.text.items():
        if rgb in (wd.PINK, wd.GOLD):
            assert _distance(rgb, sky[p]) > 250, p
    fur = [p for p, rgb in scene.base.items() if rgb == (255, 255, 255)]
    assert fur and all(_distance(scene.base[p], sky[p]) > 400 for p in fur)


@pytest.mark.parametrize("w, h", BOARDS)
def test_marie_has_her_blue_eyes_and_pink_bow(w, h):
    colours = set(_scene(w, h).base.values())
    assert (1, 169, 244) in colours
    assert any(r > 220 and g < 130 and b > 100 for r, g, b in colours), "a strong pink, not a pastel"


@pytest.mark.parametrize("w, h", BOARDS)
def test_maries_outline_is_black_and_drawn_over_the_sky(w, h):
    scene = _scene(w, h)
    outline = [p for p, rgb in scene.base.items() if rgb == wd.OUTLINE]
    assert wd.OUTLINE == (0, 0, 0) and outline, "her outline is black"
    assert (158, 158, 158) not in scene.base.values(), "no grey left from the charts' rim"
    frame = scene.frame(3.0)
    assert all(frame[p] == (0, 0, 0) for p in outline), "stars and sky don't show through it"
    assert all(_distance((0, 0, 0), scene.sky[p]) > 80 for p in outline), "dark against the purple"


def test_64x64_marie_faces_the_title_and_64x32_peeks_over_the_table():
    tall, peek = _scene(64, 64), _scene(64, 32)
    assert tall.marie_box[0] + tall.marie_box[2] == 64 and _box(tall.text)[2] < tall.marie_box[0]
    assert peek.marie_box[3] == len(wd.PEEK_MARIE) and tall.marie_box[3] == len(wd.TALL_MARIE)
    for scene in (tall, peek):
        assert scene.marie_box[1] + scene.marie_box[3] == min(y for _, y in scene.table), "sitting on the table"


def test_the_sprites_are_rectangular_and_use_only_their_palettes():
    for art, colors in ((wd.TALL_MARIE, wd.TALL_COLORS), (wd.PEEK_MARIE, wd.PEEK_COLORS),
                        (wd.WINE_GLASS, wd.GLASS_COLORS)):
        assert len({len(row) for row in art}) == 1
        assert set("".join(art)) - {"."} <= set(colors)


def test_it_plays_for_five_seconds():
    assert landmarks.WineAndDine5KLandmark.SCREEN_S == 5.0
    assert landmarks.landmark_screen(_scene(64, 32)).plays_under_reveal is False
