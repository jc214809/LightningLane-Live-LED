"""Jollywood Nights' landmark: the Tower of Terror decked out, with a neon sign, tonight's hours in the clouds,
and a gift for the elevator car that drops and bursts into confetti."""

import random

import pytest

import display.landmarks as landmarks
from display.landmarks import jollywood_tower as jt

BOARDS = [(64, 32), (64, 64)]


def _scene(w, h, park=None, seed=3, snow=False):
    """The scene; without its snow unless asked, so a flake can't land on a pixel a test looks at."""
    scene = landmarks.JollywoodTowerLandmark(w, h, random.Random(seed), park=park)
    if not snow:
        scene.flakes = []
    return scene


def _party_park(opens="19:00", closes="23:00"):
    """Hollywood Studios on a Jollywood night, dated the park's today (test_santa_train.py's)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    return {"name": "Hollywood Studios", "timezone": "America/New_York", "seasonalEvent": "jollywood",
            "schedule": [{"type": "TICKETED_EVENT", "date": today, "description": "Special Ticketed Event",
                          "openingTime": f"{today}T{opens}:00-05:00", "closingTime": f"{today}T{closes}:00-05:00"}]}


def _story_s(scene):
    """Scene time it gets: its screen (longer on 64x32) minus the sweep and the wipe."""
    import display.animation as animation
    return scene.SCREEN_S - animation.COVER_S - animation.TRANSITIONS["wipe"].duration


def _settled(scene):
    """A scene time once the tilt (64x32) and every sign's flicker are done, before the drop."""
    return scene.sign_delay + max(jt.HOURS_ON_AT) + jt.FLICKER_S + 0.05


def test_the_jollywood_party_finds_it():
    assert landmarks.landmark_for("Disney's Hollywood Studios", "jollywood") is jt.JollywoodTowerLandmark


@pytest.mark.parametrize("w, h", BOARDS)
def test_it_keeps_the_towers_story_inside_its_screen(w, h):
    scene = _scene(w, h)
    assert isinstance(scene, landmarks.TowerOfTerrorLandmark)
    assert scene.LAND_AT <= _story_s(scene) - 0.8, "the burst has time to play"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_lightning_is_red_and_green(w, h):
    scene = _scene(w, h)
    flash = scene.frame(scene.STRIKE_AT + 0.05)
    assert jt.JollywoodTowerLandmark.BOLT_RGB[0] > 200 > jt.JollywoodTowerLandmark.BOLT_RGB[1]
    assert jt.JollywoodTowerLandmark.BOLT_EDGE_RGB[1] > 200 > jt.JollywoodTowerLandmark.BOLT_EDGE_RGB[0]
    assert scene.BOLT_RGB in flash.values() and scene.BOLT_EDGE_RGB in flash.values()


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_bulbs_chase_round_the_hotel(w, h):
    scene = _scene(w, h)
    shown = [(i, p) for i, p in enumerate(scene.outline) if p[1] < jt.SIGN_Y - 1]  # above the sign, on both boards
    i, bulb = shown[0]
    seen = {scene.frame(_settled(scene) + k / jt.CHASE_HZ)[bulb] for k in range(len(jt.BULBS))}
    assert seen == set(jt.BULBS), "each colour in turn"
    frame, step = scene.frame(2.0), int(2.0 * jt.CHASE_HZ)
    assert [frame[p] for _, p in shown[:3]] == [jt.BULBS[(i + step) % 4] for i, _ in shown[:3]], "in order round it"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_lit_windows_are_red_and_green_never_the_plain_yellow(w, h):
    scene = _scene(w, h)
    frame = scene.frame(_settled(scene))
    shown = [frame[p] for p in scene.lit_windows if p in frame and frame[p] in (jt.WINDOW_RED, jt.WINDOW_GREEN)]
    assert jt.WINDOW_RED in shown and jt.WINDOW_GREEN in shown
    assert not any(frame.get(p) == scene.COLORS["win_lit"] for p in scene.lit_windows)


def test_the_searchlights_light_only_the_sky():
    scene = _scene(64, 64)
    for cells, _, _ in scene.beams:
        assert cells and not any((x, y) in scene.hotel for _, _, x, y, _ in cells)
    walls = {(x, y) for x in range(scene.TOWER_L, scene.TOWER_R + 1) for y in range(30, 50)}
    assert walls <= scene.hotel and all((x, y) not in walls for _, _, x, y, _ in scene.beams[0][0])
    frame, still = scene.frame(2.0), scene.frame(2.0)
    assert any(frame[(x, y)] != scene.base[(x, y)] for _, _, x, y, _ in scene.beams[0][0]) and frame == still


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_jollywood_sign_flickers_on_and_stays_lit(w, h):
    scene = _scene(w, h)
    before = scene.frame(scene.sign_delay + jt.SIGN_ON_AT - 0.05)
    assert all(before[p] == jt.NEON_OFF_RGB for p in scene.sign)
    flicker = [scene.frame(scene.sign_delay + jt.SIGN_ON_AT + k / 30)[scene.sign[0]] for k in range(int(jt.FLICKER_S * 30))]
    assert jt.NEON_RGB in flicker and jt.NEON_OFF_RGB in flicker, "it stutters"
    for t in (_settled(scene), scene.LAND_AT - 0.05):
        frame = scene.frame(t)
        assert all(frame[p] == jt.NEON_RGB for p in scene.sign)


def test_on_64x32_the_signs_wait_for_the_tilt():
    scene = _scene(64, 32, _party_park())
    assert scene.sign_delay + jt.SIGN_ON_AT >= scene.PAN_S - 0.2
    frame = scene.frame(scene.PAN_S)  # the tilt has stopped on the dome
    assert all(0 <= y < 32 for _, y in scene.sign), "the sign is in the top half"
    assert all(frame[p] in (jt.NEON_RGB, jt.NEON_OFF_RGB) for p in scene.sign)


@pytest.mark.parametrize("w, h", BOARDS)
def test_tonights_hours_light_the_top_corner_clouds(w, h):
    scene = _scene(w, h, _party_park("19:00", "23:00"))
    assert scene.hours == ("7PM", "11PM")
    frame = scene.frame(_settled(scene))
    (start, _, _), (end, _, _) = scene.hour_signs
    assert all(frame[p] == jt.HOURS_RGB for p in start + end)
    assert max(x for x, _ in start) < scene.TOWER_L - 1 < scene.TOWER_R + 1 < min(x for x, _ in end), "off the hotel"
    assert all(y < 8 for _, y in start + end), "in the clouds, on both boards"
    assert sum(p in scene.clouds[0] for p in start) > len(start) / 2, "mostly on the left cloud"
    assert sum(p in scene.clouds[1] for p in end) > len(end) / 2, "and the right"


@pytest.mark.parametrize("w, h", BOARDS)
def test_without_hours_the_clouds_stay_plain(w, h):
    scene = _scene(w, h)
    assert scene.hours is None and scene.hour_signs == []
    frame = scene.frame(_settled(scene))
    assert jt.HOURS_RGB not in frame.values() and jt.HOURS_OFF_RGB not in frame.values()


@pytest.mark.parametrize("times", [("12PM", "12AM"), ("10PM", "11PM")])
def test_the_widest_hours_fit_their_corners(times):
    for time, cx in zip(times, jt.HOURS_X):
        xs = [x for x, _ in jt.text_pixels(time, cx - jt.text_width(time) // 2, jt.HOURS_Y)]
        assert 1 <= min(xs) and max(xs) <= 62, "with room for the dark edge"


@pytest.mark.parametrize("w, h", BOARDS)
def test_the_car_is_a_gift_that_drops_and_bursts_in_view(w, h):
    scene = _scene(w, h)
    for t in (scene.DOORS_AT + 0.2, scene.DROP_AT + 0.05):  # then it passes behind the sign
        frame = scene.frame(t)
        assert jt.GIFT_RGB in frame.values() and jt.RIBBON_RGB in frame.values(), t
    landed = scene.frame(scene.LAND_AT - 0.01)
    gift = [(x, y) for (x, y), rgb in landed.items() if rgb == jt.GIFT_RGB]
    assert gift, "the gift is still in view as it lands"
    for t in range(int(_story_s(scene) * 30)):
        assert scene.CAR_RGB not in scene.frame(t / 30).values(), "never the plain car"
    burst = scene.frame(scene.LAND_AT + 0.05)
    centre = (scene.gift_left() + 2, scene.burst_y + 2)
    assert burst[centre] == jt.WHITE, "the flash is on the board"
    assert max(y for _, y in gift) >= centre[1] - 3, "it bursts where it lands"
    after = scene.frame(scene.LAND_AT + 0.5)
    assert sum(after.get(p) in jt.BULBS for p in after) > sum(burst.get(p) in jt.BULBS for p in burst), "confetti"


def test_on_64x32_the_gift_bursts_just_under_the_sign():
    scene = _scene(64, 32)
    burst = scene.frame(scene.LAND_AT + 0.05)
    flash = {(x, y) for x in range(64) for y in range(32)
             if (x - scene.gift_left() - 2) ** 2 + (y - scene.burst_y - 2) ** 2 <= 9}
    assert all(burst[p] == jt.WHITE for p in flash)
    assert not flash & set(scene.sign), "the flash leaves the letters readable"
    assert min(y for _, y in flash) > max(y for _, y in scene.sign) - 1


def test_the_snow_falls():
    scene = _scene(64, 64, snow=True)
    a, b = scene.frame(1.0), scene.frame(1.5)
    flakes = {p for p, rgb in a.items() if rgb == jt.SNOW_RGB}
    assert flakes and flakes != {p for p, rgb in b.items() if rgb == jt.SNOW_RGB}


def test_the_plain_tower_still_drops_its_car_to_the_arches():
    plain = landmarks.TowerOfTerrorLandmark(64, 32, random.Random(3))
    assert plain.CAR_FLOOR == 52 and _scene(64, 32).CAR_FLOOR == 28 and _scene(64, 64).CAR_FLOOR == 50
