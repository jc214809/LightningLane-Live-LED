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


def _tower_scene_s(tower):
    """Scene time the tower gets: its screen minus the sweep and the wipe in front of it."""
    import display.animation as animation
    return tower.SCREEN_S - animation.COVER_S - animation.TRANSITIONS["wipe"].duration


def test_tower_screen_is_longer_than_the_other_landmarks_and_longest_on_64x32():
    tall = landmarks.TowerOfTerrorLandmark(64, 64, random.Random(3))
    short = landmarks.TowerOfTerrorLandmark(64, 32, random.Random(3))
    assert (tall.SCREEN_S, short.SCREEN_S) == (4.5, 5.5)
    for cls in (landmarks.CastleLandmark, landmarks.SpaceshipEarthLandmark, landmarks.TreeOfLifeLandmark):
        assert cls.SCREEN_S == landmarks.LANDMARK_S < tall.SCREEN_S


@pytest.mark.parametrize("height", [32, 64])
def test_tower_story_plays_out_inside_its_screen(height):
    tower = landmarks.TowerOfTerrorLandmark(64, height, random.Random(3))
    assert tower.STRIKE_AT < tower.DOORS_AT < tower.DROP_AT < tower.LAND_AT
    assert tower.LAND_AT <= _tower_scene_s(tower) - 0.8, "the car lands with time to take it in"
    beats = (0.0, tower.STRIKE_AT, tower.DOORS_AT, tower.DROP_AT, tower.LAND_AT)
    assert min(b - a for a, b in zip(beats[1:], beats[2:])) >= 0.5, "each beat gets room"
    if tower.pans:
        assert tower.PAN_S + 0.3 <= tower.STRIKE_AT, "the tilt settles before anything happens"


def _scene_s(cls):
    """Scene time a landmark gets: its screen minus the sweep, and minus the wipe unless it plays under it."""
    import display.animation as animation
    wipe = 0 if cls.PLAYS_UNDER_WIPE else animation.TRANSITIONS["wipe"].duration
    return cls.SCREEN_S - animation.COVER_S - wipe


def test_the_pumpkins_light_up_while_the_wipe_is_still_uncovering_them():
    import display.animation as animation
    wipe = animation.TRANSITIONS["wipe"].duration
    for cls in (landmarks.ScaryJackOLanternLandmark, landmarks.FriendlyJackOLanternLandmark):
        pumpkin = cls(64, 64, random.Random(5))
        assert landmarks.landmark_screen(pumpkin).plays_under_reveal is True
        assert pumpkin.IGNITE_AT < wipe, "the candle catches before the wipe has finished"
    for cls in (landmarks.CastleLandmark, landmarks.SpaceshipEarthLandmark, landmarks.TreeOfLifeLandmark,
                landmarks.TowerOfTerrorLandmark):
        assert landmarks.landmark_screen(cls(64, 64, random.Random(5))).plays_under_reveal is False, cls


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
    struck = [f for f in range(int(_tower_scene_s(tower) * 30))
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
    pumpkin = _pinned("wink")(64, 64, random.Random(9))  # a hop would move the tongue off its resting pixels
    # The pumpkin's own colours: on 64x64 it sits on the bottom edge, where the mist rolls over its smile.
    lit = {}
    pumpkin._draw_pumpkin(lit, 1.5)
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


TITLE_CHAR_W, TITLE_H = 4, 6  # the 4x6 landmark font both boards use


def _text_w(text):
    """Width of text in the landmark font: 4 columns a letter, 5 for its wider N."""
    return sum(5 if ch == "N" else TITLE_CHAR_W for ch in text)


def _bdf_glyphs(path):
    """{char: (DWIDTH, BBX, bitmap rows)} from a BDF font."""
    glyphs, cur = {}, None
    for line in open(path):
        key, _, rest = line.strip().partition(" ")
        if key == "ENCODING":
            cur = {"code": int(rest), "rows": []}
        elif cur is not None and key == "DWIDTH":
            cur["dwidth"] = rest
        elif cur is not None and key == "BBX":
            cur["bbx"] = rest
        elif cur is not None and key == "ENDCHAR":
            glyphs[chr(cur["code"])] = (cur["dwidth"], cur["bbx"], tuple(cur["rows"]))
            cur = None
        elif cur is not None and key not in ("SWIDTH", "BITMAP", "STARTCHAR") and line.strip():
            cur["rows"].append(line.strip())
    return glyphs


def test_landmark_font_is_the_title_font_with_a_readable_n():
    import display.display as display
    for height in (32, 64):
        assert display.fonts()[height]["landmark_title"].endswith("4x6-landmark.bdf")
    legacy = _bdf_glyphs("assets/fonts/patched/4x6-legacy.bdf")
    landmark = _bdf_glyphs("assets/fonts/patched/4x6-landmark.bdf")
    assert {ch for ch in legacy if legacy[ch] != landmark[ch]} == {"N"}, "only N changes"
    dwidth, bbx, rows = landmark["N"]
    assert dwidth.split()[0] == "5" and bbx.split()[0] == "4", "4 pixels wide, with a gap after it"
    bits = [format(int(r, 16) >> 4, "04b") for r in rows]
    assert bits[1] == "1101" and bits[2] == "1011", "a diagonal from top left to bottom right"


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
        w = _text_w(text)
        left = round(center_x - w / 2)
        assert left >= 0 and left + w <= 64, text
        assert top >= 0 and top + TITLE_H <= height, text
        box = {(x, y) for x in range(left, left + w + 1) for y in range(top, top + TITLE_H + 1)}
        assert not box & set(pumpkin.shell), f"{text} overlaps the pumpkin"


def _party_park():
    """Magic Kingdom on a party night, 7pm to midnight, dated the park's today."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    return {"name": "Magic Kingdom", "timezone": "America/New_York", "seasonalEvent": "halloween",
            "schedule": [{"type": "TICKETED_EVENT", "date": today, "description": "Special Ticketed Event",
                          "openingTime": f"{today}T19:00:00-04:00", "closingTime": f"{today}T23:59:00-04:00"}]}


@pytest.mark.parametrize("motion", ["wink", "bounce"])
def test_party_hours_fade_into_the_mist_on_cue_and_fit_clear_of_the_pumpkin(motion):
    height, expected = 64, ["7PM", "11PM"]
    pumpkin = _pinned(motion)(64, height, random.Random(17), park=_party_park())
    assert pumpkin.hours == ("7PM", "11PM")
    # Down in the mist, fading in slowly from the moment the wink or hop starts.
    begin, fade_s = pumpkin._motion_start(), pumpkin.MIST_HOURS_FADE_S
    assert fade_s >= 1.0, "a slow fade"
    names = {text for text, *_ in pumpkin.title(begin - 0.05)}
    assert not names & set(expected), "not before their cue"
    end = _scene_s(landmarks.FriendlyJackOLanternLandmark) - 0.05
    hours = [line for line in pumpkin.title(end) if line[0] in expected]
    assert [line[0] for line in hours] == expected
    half = [line for line in pumpkin.title(begin + fade_s / 2) if line[0] in expected]
    assert sum(half[0][3]) < sum(hours[0][3]), "they fade in"
    assert end - (begin + fade_s) >= 1.2, "and stay long enough to read"
    assert all(top + TITLE_H >= 63 for text, _, top, _ in hours), "on the bottom rows, in the mist"
    for text, center_x, top, _ in pumpkin.title(end):
        w = _text_w(text)
        left = round(center_x - w / 2)
        assert left >= 0 and left + w <= 64 and 0 <= top and top + TITLE_H <= height, text
        box = {(x, y) for x in range(left, left + w + 1) for y in range(top, top + TITLE_H + 1)}
        assert not box & set(pumpkin.shell), f"{text} overlaps the pumpkin"


def _short_scene_s(pumpkin):
    import display.animation as animation
    return pumpkin.SCREEN_S - animation.COVER_S - animation.TRANSITIONS["wipe"].duration


def _box(text, center_x, top):
    w = _text_w(text)
    left = round(center_x - w / 2)
    return left, left + w, top, top + TITLE_H


def test_short_board_pumpkin_gets_a_longer_screen():
    assert landmarks.FriendlyJackOLanternLandmark(64, 32, random.Random(21)).SCREEN_S == 6.5
    assert landmarks.FriendlyJackOLanternLandmark(64, 64, random.Random(21)).SCREEN_S == 6.0
    assert landmarks.ScaryJackOLanternLandmark.SCREEN_S == 6.0


def test_short_board_pumpkin_jumps_into_the_titles_spot_and_shoves_it_off():
    pumpkin = landmarks.FriendlyJackOLanternLandmark(64, 32, random.Random(22), park=_party_park())
    title = [text for text, _ in pumpkin.TITLE_SHORT]
    before = pumpkin.title(pumpkin.JUMP_AT - 0.05)
    assert [line[0] for line in before] == title, "the whole title holds to be read first"
    assert all(x == pumpkin.TITLE_COLUMN_X for _, x, _, _ in before), "not nudged before the jump"
    assert pumpkin._jump(pumpkin.JUMP_AT - 0.05) == (0.0, 0)
    for f in range(int(pumpkin.JUMP_S * 30) + 1):
        t = pumpkin.JUMP_AT + f / 30
        dx, lift = pumpkin._jump(t)
        ear_left = pumpkin.cx + dx - pumpkin.R * pumpkin.EAR_REACH
        for text, center_x, top, _ in pumpkin.title(t):
            if text in title:
                assert _box(text, center_x, top)[1] <= ear_left + 1, f"{text} stays ahead of the ear at {t:.2f}"
    landed = pumpkin.JUMP_AT + pumpkin.JUMP_S
    assert not {line[0] for line in pumpkin.title(landed)} & set(title), "shoved clean off"
    dx, lift = pumpkin._jump(landed)
    assert lift == 0 and 0 <= pumpkin.cx + dx - pumpkin.R * pumpkin.EAR_REACH < 2, "lands at the left edge"
    assert pumpkin._jump(pumpkin.JUMP_AT + pumpkin.JUMP_S / 2)[1] > 0, "an arc, not a slide"


def test_short_board_hours_fade_in_where_the_pumpkin_was_then_it_winks():
    pumpkin = _pinned("bounce")(64, 32, random.Random(23), park=_party_park())
    assert pumpkin.motion == "wink", "the jump is its move on 64x32; it winks after landing"
    end = _short_scene_s(pumpkin) - 0.05
    hours = ["TONIGHT", "7PM TO", "11PM"]
    assert not {line[0] for line in pumpkin.title(pumpkin.TONIGHT_AT - 0.05)} & set(hours)
    lines = [line for line in pumpkin.title(end) if line[0] in hours]
    assert [line[0] for line in lines] == hours
    first_left = min(_box(*line[:3])[0] for line in lines)
    for f in range(int((end - pumpkin.TONIGHT_AT) * 30)):
        t = pumpkin.TONIGHT_AT + f / 30
        dx, _ = pumpkin._jump(t)
        assert pumpkin.cx + dx + pumpkin.R * pumpkin.EAR_REACH < first_left, "the pumpkin has cleared their spot"
    for text, center_x, top, _ in lines:
        left, right, y0, y1 = _box(text, center_x, top)
        assert 0 <= left and right <= 64 and 0 <= y0 and y1 <= 32, text
    assert end - (pumpkin.TONIGHT_AT + pumpkin.TONIGHT_FADE_S) >= 1.2, "long enough to read"
    winking = [f / 30 for f in range(int(end * 30)) if pumpkin._winking(f / 30)]
    assert winking and winking[0] >= pumpkin.JUMP_AT + pumpkin.JUMP_S, "winks after it lands"


@pytest.mark.parametrize("height", [32, 64])
def test_friendly_pumpkin_stem_sits_centred_on_the_head(height):
    pumpkin = _pinned("wink")(64, height, random.Random(20))
    stem = [p for p, rgb in pumpkin.shell.items() if rgb in (pumpkin.STEM, (40, 85, 28))]
    base_y = max(y for _, y in stem)
    base = [x for x, y in stem if y == base_y]
    assert (min(base) + max(base)) / 2 == pumpkin.cx, "the base is square in the middle"


def test_pumpkin_sky_has_twice_the_stars():
    castle = landmarks.CastleLandmark(64, 64, random.Random(19))
    pumpkin = _pinned("wink")(64, 64, random.Random(19))
    assert len(pumpkin.stars) == 2 * len(castle.stars)
    lit = pumpkin.frame(3.0)
    visible = [s for s in pumpkin.stars if (s[0], s[1]) not in pumpkin.shell]
    assert all(sum(lit[(x, y)]) > 100 for x, y, _ in visible), "they show over the sky"


def test_no_party_hours_without_a_special_event_in_the_schedule():
    assert _pinned("wink")(64, 64, random.Random(18)).hours is None, "no park"
    park = dict(_party_park(), schedule=[])
    assert _pinned("wink")(64, 64, random.Random(18), park=park).hours is None
    park = _party_park()
    del park["schedule"][0]["closingTime"]
    assert _pinned("wink")(64, 64, random.Random(18), park=park).hours is None, "a missing time shows nothing"


def test_landmark_screen_draws_the_title_with_a_shadow(monkeypatch):
    class Font:
        baseline = 5

        def CharacterWidth(self, ch):
            return TITLE_CHAR_W

    class Canvas:
        def SetPixel(self, *a):
            pass

    calls = []
    monkeypatch.setitem(landmarks.loaded_fonts, "landmark_title", Font())
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
