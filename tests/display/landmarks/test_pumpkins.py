"""The Halloween-party jack-o'-lanterns."""

import random

import pytest

import display.landmarks as landmarks

from tests.display.landmarks.support import TITLE_CHAR_W, _pinned, _scene_s


def test_the_pumpkins_light_up_while_the_wipe_is_still_uncovering_them():
    import display.animation as animation
    wipe = animation.TRANSITIONS["wipe"].duration
    for cls in (landmarks.ScaryJackOLanternLandmark, landmarks.FriendlyJackOLanternLandmark):
        pumpkin = cls(64, 64, random.Random(5))
        assert landmarks.landmark_screen(pumpkin).plays_under_reveal is True
        assert pumpkin.IGNITE_AT < wipe, "the candle catches before the wipe has finished"
    for cls in (landmarks.CastleLandmark, landmarks.TreeOfLifeLandmark, landmarks.TowerOfTerrorLandmark):
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


def test_scary_jack_o_lantern_starts_dark_then_its_face_lights_up():
    pumpkin = landmarks.ScaryJackOLanternLandmark(64, 64, random.Random(6))
    before = pumpkin.frame(pumpkin.IGNITE_AT - 0.1)
    after = pumpkin.frame(pumpkin.IGNITE_AT + pumpkin.IGNITE_S + 0.5)
    face = pumpkin.carved
    assert face, "the face is carved"
    assert all(sum(before[p]) < 100 for p in face), "unlit carving is dark"
    assert all(sum(after[p]) > 400 for p in face), "lit carving glows"


def _distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


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


@pytest.mark.parametrize("height", [32, 64])
def test_friendly_jack_o_lantern_title_lights_up_with_the_candle(height):
    pumpkin = _pinned("wink")(64, height, random.Random(13))
    assert pumpkin.title(pumpkin.IGNITE_AT - 0.1) == [], "dark pumpkin, no title yet"
    lit = pumpkin.title(2.0)
    assert " ".join(text for text, *_ in lit).replace("- ", "-") == "MICKEY'S NOT-SO-SCARY HALLOWEEN PARTY"
    half = pumpkin.title(pumpkin.IGNITE_AT + pumpkin.IGNITE_S / 2)
    assert all(sum(h[3]) < sum(f[3]) for h, f in zip(half, lit)), "fades in with the candle"


TITLE_H = 6


def _text_w(text):
    """Width of text in the landmark font: 4 columns a letter, 5 for its wider N."""
    return sum(5 if ch == "N" else TITLE_CHAR_W for ch in text)


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


def test_short_board_pumpkin_gets_a_longer_screen():
    assert landmarks.FriendlyJackOLanternLandmark(64, 32, random.Random(21)).SCREEN_S == 6.5
    assert landmarks.FriendlyJackOLanternLandmark(64, 64, random.Random(21)).SCREEN_S == 6.0
    assert landmarks.ScaryJackOLanternLandmark.SCREEN_S == 6.0


def _box(text, center_x, top):
    w = _text_w(text)
    left = round(center_x - w / 2)
    return left, left + w, top, top + TITLE_H


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


def _short_scene_s(pumpkin):
    import display.animation as animation
    return pumpkin.SCREEN_S - animation.COVER_S - animation.TRANSITIONS["wipe"].duration


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
