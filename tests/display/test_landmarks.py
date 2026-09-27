# tests/display/test_landmarks.py
import random

import pytest

import display.landmarks as landmarks

ALL = [landmarks.CastleLandmark, landmarks.SpaceshipEarthLandmark,
       landmarks.TowerOfTerrorLandmark, landmarks.TreeOfLifeLandmark, landmarks.ScaryJackOLanternLandmark,
       type("WinkingPumpkin", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": "wink"}),
       type("BouncingPumpkin", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": "bounce"})]


@pytest.mark.parametrize("name, cls", [
    ("Magic Kingdom", landmarks.CastleLandmark),
    ("EPCOT", landmarks.SpaceshipEarthLandmark),
    ("Epcot", landmarks.SpaceshipEarthLandmark),
    ("Hollywood Studios", landmarks.TowerOfTerrorLandmark),
    ("Disney's Hollywood Studios", landmarks.TowerOfTerrorLandmark),
    ("Animal Kingdom", landmarks.TreeOfLifeLandmark),
    ("Cedar Point", None),
    ("", None),
    (None, None),
])
def test_landmark_for_matches_park_names_loosely(name, cls):
    assert landmarks.landmark_for(name) is cls


def test_a_party_swaps_in_its_own_landmark():
    assert landmarks.landmark_for("Magic Kingdom", "halloween") is landmarks.FriendlyJackOLanternLandmark
    assert landmarks.landmark_for("Magic Kingdom", None) is landmarks.CastleLandmark
    assert landmarks.landmark_for("Magic Kingdom", "not-a-party") is landmarks.CastleLandmark


def test_every_special_events_landmark_exists():
    for key, event in landmarks.SPECIAL_EVENTS.items():
        if not event.get("landmark"):
            continue
        cls = landmarks.landmark_for("Anywhere", key)
        assert isinstance(cls, type) and issubclass(cls, landmarks.Landmark), key


def test_an_event_without_a_landmark_keeps_the_parks_own():
    assert landmarks.landmark_for("Magic Kingdom", "christmas") is landmarks.CastleLandmark
    assert landmarks.landmark_for("EPCOT", "extended_evening") is landmarks.SpaceshipEarthLandmark


@pytest.mark.parametrize("cls", ALL)
@pytest.mark.parametrize("height", [32, 64])
def test_every_frame_stays_on_the_board_with_valid_colors(cls, height):
    scene = cls(64, height, random.Random(1))
    for f in range(int(landmarks.LANDMARK_S * 30)):
        pixels = scene.frame(f / 30)
        assert pixels
        for (x, y), rgb in pixels.items():
            assert 0 <= x < 64 and 0 <= y < height
            assert len(rgb) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)


@pytest.mark.parametrize("cls", ALL)
def test_scenes_actually_move(cls):
    scene = cls(64, 64, random.Random(2))
    frames = [scene.frame(f / 30) for f in range(int(landmarks.LANDMARK_S * 30))]
    assert any(a != b for a, b in zip(frames, frames[1:]))


def _tower_scene_s():
    """Scene time the tower gets: its screen minus the sweep and the wipe in front of it."""
    import display.animation as animation
    return (landmarks.TowerOfTerrorLandmark.SCREEN_S - animation.COVER_S
            - animation.TRANSITIONS["wipe"].duration)


def test_tower_screen_is_longer_than_the_other_landmarks():
    assert landmarks.TowerOfTerrorLandmark.SCREEN_S == 3.5
    for cls in (landmarks.CastleLandmark, landmarks.SpaceshipEarthLandmark, landmarks.TreeOfLifeLandmark):
        assert cls.SCREEN_S == landmarks.LANDMARK_S


@pytest.mark.parametrize("height", [32, 64])
def test_tower_story_plays_out_inside_its_screen(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    assert tower.STRIKE_AT < tower.DOORS_AT < tower.DROP_AT < tower.LAND_AT
    assert tower.LAND_AT <= _tower_scene_s() - 0.2, "the car lands with a beat to spare"
    if tower.pans:
        assert tower.PAN_S < tower.STRIKE_AT, "the tilt finishes before anything happens"


def _scene_s(cls):
    """Scene time a landmark gets: its screen minus the sweep and the wipe in front of it."""
    import display.animation as animation
    return cls.SCREEN_S - animation.COVER_S - animation.TRANSITIONS["wipe"].duration


@pytest.mark.parametrize("motion", ["wink", "bounce"])
def test_pumpkin_story_plays_out_inside_its_screen_with_time_to_read_the_name(motion):
    cls = type("P", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": motion})
    pumpkin = cls(64, 64, random.Random(16))
    scene_s = _scene_s(cls)
    frames = [i / 30 for i in range(int(scene_s * 30))]
    lit_at = pumpkin.IGNITE_AT + pumpkin.IGNITE_S
    moving = [t for t in frames if (pumpkin._winking(t) if motion == "wink" else pumpkin._hop(t))]
    assert moving, "the motion happens on screen"
    assert lit_at <= moving[0], "the candle is lit before it moves"
    assert moving[-1] <= scene_s - 1.5, "then it holds on the lit face long enough to read the name"
    assert pumpkin._lit(scene_s - 0.05) == 1.0 and pumpkin.title(scene_s - 0.05), "still lit at the end, no loop"


@pytest.mark.parametrize("height", [32, 64])
def test_tower_lightning_strikes_once_out_of_the_cloud(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    struck = [f for f in range(int(_tower_scene_s() * 30))
              if tower.BOLT_RGB in tower.frame(f / 30).values()]
    assert struck, "the bolt appears"
    assert struck == list(range(struck[0], struck[-1] + 1)), "one continuous strike"
    assert len(struck) < 10, "a quick flash"
    cloud_bottom = max(y for _, y in tower.clouds[0])
    assert min(y for _, y in tower.bolt) == cloud_bottom + 1, "it starts from the underside of the cloud"


@pytest.mark.parametrize("height", [32, 64])
def test_tower_doors_open_then_the_car_drops_in_view(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    x0, _, x1, y1 = tower.doors
    before = tower.frame(tower.DOORS_AT - 0.05)
    # On 64x32 the doors finish opening just as the car drops, so look a moment before.
    opened = tower.frame(min(tower.DOORS_AT + tower.DOORS_OPEN_S, tower.DROP_AT) - 0.02)
    assert before[((x0 + x1) // 2, y1)] != tower.COLORS["win_lit"]
    assert opened[((x0 + x1) // 2, y1)] == tower.COLORS["win_lit"], "the doors open onto the lit car"
    assert tower.CAR_RGB in tower.frame(tower.DROP_AT + 0.05).values(), "the falling car is on screen"
    assert tower.CAR_RGB not in tower.frame(tower.LAND_AT + 0.05).values(), "and gone once it lands"


def test_tower_tilts_up_from_the_trees_to_the_dome_on_64x32():
    tower = landmarks.TowerOfTerrorLandmark(64, 32, random.Random(3))
    trees = {tower.COLORS["tree"], tower.COLORS["tree_lit"]}
    start, settled = tower.frame(0), tower.frame(tower.PAN_S)
    assert sum(rgb in trees for rgb in start.values()) > 50, "starts down among the trees"
    assert not any(rgb in trees for rgb in settled.values())
    assert settled[(31, 0)] == tower.COLORS["spire"], "and stops with the dome's spire at the top"
    tall = landmarks.TowerOfTerrorLandmark(64, 64, random.Random(3))
    assert not tall.pans and tall.frame(0)[(31, 0)] == tall.COLORS["spire"], "64x64 shows it all at once"


def _distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def test_scary_jack_o_lantern_starts_dark_then_its_face_lights_up():
    pumpkin = landmarks.ScaryJackOLanternLandmark(64, 64, random.Random(6))
    before = pumpkin.frame(pumpkin.IGNITE_AT - 0.1)
    after = pumpkin.frame(pumpkin.IGNITE_AT + pumpkin.IGNITE_S + 0.5)
    face = pumpkin.carved
    assert face, "the face is carved"
    assert all(sum(before[p]) < 100 for p in face), "unlit carving is dark"
    assert all(sum(after[p]) > 400 for p in face), "lit carving glows"


def test_scary_jack_o_lantern_face_stands_out_from_its_shell():
    pumpkin = landmarks.ScaryJackOLanternLandmark(64, 64, random.Random(7))
    lit = pumpkin.frame(2.2)
    glow = [lit[p] for p in pumpkin.carved]
    shell = [lit[p] for p in pumpkin.shell]
    brightest_shell = max(shell, key=sum)
    assert min(_distance(g, brightest_shell) for g in glow) > 150


def test_scary_jack_o_lantern_face_sits_inside_the_head_below_the_ears():
    pumpkin = landmarks.ScaryJackOLanternLandmark(64, 64, random.Random(8))
    for x, y in pumpkin.carved:
        assert (x - pumpkin.cx) ** 2 + (y - pumpkin.cy) ** 2 < pumpkin.R ** 2
        assert y > pumpkin.cy - pumpkin.R


def test_friendly_jack_o_lantern_has_a_pink_tongue_at_the_bottom_of_its_smile():
    pumpkin = landmarks.FriendlyJackOLanternLandmark(64, 64, random.Random(9))
    lit = pumpkin.frame(1.5)
    assert pumpkin.tongue
    assert min(y for _, y in pumpkin.tongue) > max(y for _, y in pumpkin.eye_of)
    smile = [p for p in pumpkin.carved if p not in pumpkin.eye_of]
    assert max(y for _, y in pumpkin.tongue) >= max(y for _, y in smile)
    tongue_rgb = lit[pumpkin.tongue[0]]
    assert tongue_rgb[0] > tongue_rgb[1] + 100, "pink-red, not orange or yellow"
    assert min(_distance(tongue_rgb, lit[p]) for p in smile) > 150


def test_friendly_jack_o_lantern_eyes_keep_a_gap_between_them():
    pumpkin = landmarks.FriendlyJackOLanternLandmark(64, 64, random.Random(10))
    left = max(x for (x, _), e in pumpkin.eye_of.items() if e == 0)
    right = min(x for (x, _), e in pumpkin.eye_of.items() if e == 1)
    assert right - left >= 3


def _pinned(motion):
    return type(f"{motion}Pumpkin", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": motion})


def test_friendly_jack_o_lantern_picks_wink_or_bounce_at_random():
    seen = {landmarks.FriendlyJackOLanternLandmark(64, 64, random.Random(seed)).motion for seed in range(20)}
    assert seen == {"wink", "bounce"}


def test_friendly_jack_o_lantern_winks_one_eye_then_reopens():
    pumpkin = _pinned("wink")(64, 64, random.Random(11))

    def lit_eye(frame, eye):
        return sum(1 for p, e in pumpkin.eye_of.items() if e == eye and sum(frame[p]) > 400)

    before = pumpkin.frame(pumpkin.WINK_AT - 0.1)
    shut = pumpkin.frame(pumpkin.WINK_AT + pumpkin.WINK_S / 2)
    after = pumpkin.frame(pumpkin.WINK_AT + pumpkin.WINK_S + 0.05)
    assert lit_eye(shut, 1) < lit_eye(before, 1) / 2, "the winking eye closes"
    assert lit_eye(shut, 0) == lit_eye(before, 0), "the other eye stays open"
    assert lit_eye(after, 1) == lit_eye(before, 1), "and it opens again"


def test_bouncing_jack_o_lantern_hops_then_lands():
    pumpkin = _pinned("bounce")(64, 64, random.Random(12))
    lifts = [pumpkin._hop(f / 30) for f in range(int(landmarks.LANDMARK_S * 30))]
    assert max(lifts) >= 3
    assert lifts[0] == 0 and lifts[-1] == 0
    assert _pinned("wink")(64, 64, random.Random(12))._hop(1.4) == 0, "winker stays put"


TITLE_CHAR_W, TITLE_H = 4, 6  # the 4x6 title font both boards use


@pytest.mark.parametrize("height", [32, 64])
def test_friendly_jack_o_lantern_title_lights_up_with_the_candle(height):
    pumpkin = _pinned("wink")(64, height, random.Random(13))
    assert pumpkin.title(pumpkin.IGNITE_AT - 0.1) == [], "dark pumpkin, no title yet"
    lit = pumpkin.title(2.0)
    assert " ".join(text for text, *_ in lit).replace("- ", "-") == "MICKEY'S NOT-SO-SCARY HALLOWEEN PARTY"
    half = pumpkin.title(pumpkin.IGNITE_AT + pumpkin.IGNITE_S / 2)
    assert all(sum(h[3]) < sum(f[3]) for h, f in zip(half, lit)), "fades in with the candle"


@pytest.mark.parametrize("height", [32, 64])
def test_friendly_jack_o_lantern_title_fits_the_board_and_clears_the_pumpkin(height):
    pumpkin = _pinned("wink")(64, height, random.Random(14))
    for text, center_x, top, _ in pumpkin.title(2.0):
        w = len(text) * TITLE_CHAR_W
        left = round(center_x - w / 2)
        assert left >= 0 and left + w <= 64, text
        assert top >= 0 and top + TITLE_H <= height, text
        box = {(x, y) for x in range(left, left + w + 1) for y in range(top, top + TITLE_H + 1)}
        assert not box & set(pumpkin.shell), f"{text} overlaps the pumpkin"


def test_landmark_screen_draws_the_title_with_a_shadow(monkeypatch):
    class Font:
        baseline = 5

        def CharacterWidth(self, ch):
            return TITLE_CHAR_W

    class Canvas:
        def SetPixel(self, *a):
            pass

    calls = []
    monkeypatch.setitem(landmarks.loaded_fonts, "title", Font())
    monkeypatch.setattr(landmarks.graphics, "Color", lambda *rgb: rgb, raising=False)
    monkeypatch.setattr(landmarks.graphics, "DrawText",
                        lambda canvas, font, x, y, color, text: calls.append((x, y, color, text)), raising=False)
    pumpkin = _pinned("wink")(64, 64, random.Random(15))
    landmarks.landmark_screen(pumpkin)(Canvas(), 2.0)
    drawn = [c for c in calls if c[2] != landmarks.TITLE_SHADOW_RGB]
    shadows = [c for c in calls if c[2] == landmarks.TITLE_SHADOW_RGB]
    assert [c[3] for c in drawn] == [text for text, *_ in pumpkin.title(2.0)]
    assert [(x - 1, y - 1, text) for x, y, _, text in shadows] == [(x, y, text) for x, y, _, text in drawn]


def test_landmark_screen_draws_every_pixel_and_keeps_animating():
    class Canvas:
        def __init__(self):
            self.px = {}

        def SetPixel(self, x, y, r, g, b):
            self.px[(x, y)] = (r, g, b)

    scene = landmarks.TreeOfLifeLandmark(64, 32, random.Random(4))
    canvas = Canvas()
    assert landmarks.landmark_screen(scene)(canvas, 1.0) is True
    assert canvas.px == scene.frame(1.0)
