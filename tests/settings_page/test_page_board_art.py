"""The settings page's logo and what it shows of the board: the icon links, the top bar and sign-in wordmark, the
heartbeat card, park landmarks, the countdown preview, the brightness and rotation previews, the cast list."""
import json
import shutil
import subprocess
from datetime import date

import pytest

from settings_page import page
from settings_page.board_status import NONE, QUIET, RUNNING, SHOW, BoardNow
from settings_page.page import SCRIPT, document, landmark_src, landmarks, pin_page, settings_page
from utils.trips import Trip, countdown_message

TODAY = date(2026, 11, 8)
TRIPS = {"trip_countdown": {"enabled": True, "trip_dates": [
    {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"}, "2027-06-01"]}}


@pytest.fixture(autouse=True)
def fresh_landmarks():
    landmarks.cache_clear()
    yield
    landmarks.cache_clear()


def test_every_page_links_the_icon_for_the_tab_and_for_phones():
    html = document("Board settings", "<p>hi</p>")
    assert '<link rel="icon" href="/static/icon.svg" type="image/svg+xml">' in html
    assert '<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">' in html
    assert 'sizes="512x512"' in html and '<meta name="theme-color" content="#0e1440">' in html


def test_the_top_bar_has_the_logo_and_the_lightninglane_led_wordmark():
    html = settings_page({}, [])
    top = html[html.index('<header class="topbar">'):html.index("</header>")]
    assert '<span class="mark"><img src="/static/icon.svg"' in top
    assert '<div class="brand-name">LightningLane</div><div class="brand-sub">LED</div>' in top
    assert "Live LED" not in top


def test_the_sign_in_page_is_crowned_with_the_logo_not_a_lock():
    html = pin_page()
    card = html[html.index('<div class="card auth signin">'):]
    assert card.index('<div class="auth-hero"><img src="/static/icon.svg"') < card.index("Sign in to this board")
    assert '<div class="brand-name">LightningLane</div>' in card
    assert '<div class="auth-icon">' not in card


def test_the_static_files_the_pages_name_are_there():
    for name in ("icon.svg", "apple-touch-icon.png", "icon-512.png", page.LANDMARK_INDEX):
        assert (page.STATIC_DIR + "/" + name) and open(f"{page.STATIC_DIR}/{name}", "rb").read(), name


def test_the_phone_icons_are_square_pngs_at_their_sizes():
    from PIL import Image
    for name, size in (("apple-touch-icon.png", 180), ("icon-512.png", 512)):
        with Image.open(f"{page.STATIC_DIR}/{name}") as im:
            assert im.format == "PNG" and im.size == (size, size), name


def test_the_svg_icon_is_a_square_svg():
    import xml.etree.ElementTree as ET
    root = ET.parse(f"{page.STATIC_DIR}/icon.svg").getroot()
    assert root.tag.endswith("svg") and root.get("viewBox") == "0 0 240 240"


# --- landmarks

def test_each_wdw_park_gets_the_landmark_the_board_plays_and_others_get_title_only():
    assert landmark_src("Magic Kingdom Park") == "/static/landmark-magic-kingdom.png"
    assert landmark_src("EPCOT") == "/static/landmark-epcot.png"
    assert landmark_src("Disney's Hollywood Studios") == "/static/landmark-hollywood-studios.png"
    assert landmark_src("Disney's Animal Kingdom Theme Park") == "/static/landmark-animal-kingdom.png"
    assert landmark_src("Cedar Point") is None and landmark_src("") is None


def test_the_landmark_index_matches_the_boards_own_landmark_choice():
    from display.landmarks.screen import LANDMARKS, landmark_for
    assert set(landmarks()) == set(LANDMARKS)
    for park in ("Magic Kingdom Park", "EPCOT", "Disney's Hollywood Studios", "Disney's Animal Kingdom", "Cedar Point"):
        cls = landmark_for(park)
        key = next((k for k, c in LANDMARKS.items() if c is cls), None)
        assert landmark_src(park) == (landmarks()[key] if key else None), park


def test_park_chips_show_their_landmark_or_say_title_only():
    html = settings_page({"parks": ["Magic Kingdom", "Cedar Point"]}, [])
    mk = html[html.index('value="Magic Kingdom"'):html.index('<span class="park-name">Magic Kingdom</span>')]
    assert 'src="/static/landmark-magic-kingdom.png"' in mk and '<span class="noland" hidden>' in mk
    cp = html[html.index('value="Cedar Point"'):html.index('<span class="park-name">Cedar Point</span>')]
    assert 'src="" alt="" width="64" height="32" hidden>' in cp and '<span class="noland">Title only</span>' in cp


def test_the_script_gets_the_landmark_map_for_parks_added_on_the_page():
    html = settings_page({}, [])
    found = html[html.index('<script type="application/json" id="park-scenes">') + 49:]
    assert json.loads(found[:found.index("</script>")]) == landmarks()
    assert "parkScenes" in SCRIPT and "name.toLowerCase().includes(key)" in SCRIPT


@pytest.mark.parametrize("text", ["not json", "[]"])
def test_a_bad_landmark_index_means_no_pictures_and_a_warning_not_a_broken_page(tmp_path, monkeypatch, text):
    warnings = []
    monkeypatch.setattr(page.debug, "warning", warnings.append)
    bad = tmp_path / "landmarks.json"
    bad.write_text(text)
    monkeypatch.setattr(page, "STATIC_DIR", str(tmp_path))
    assert landmarks() == {} and len(warnings) == 1
    html = settings_page({"parks": ["Magic Kingdom"]}, [], now=BoardNow(RUNNING, 5))
    assert "Title only" in html and 'id="pv-all"' not in html and 'id="pv-rot"' not in html
    assert '<section class="card board-now"' in html, "the card stays, without its picture"


def test_an_index_entry_with_a_path_in_it_is_ignored(tmp_path, monkeypatch):
    (tmp_path / "landmarks.json").write_text(json.dumps({"epcot": "../../config.json", "magic kingdom": "mk.png"}))
    monkeypatch.setattr(page, "STATIC_DIR", str(tmp_path))
    assert landmarks() == {"magic kingdom": "/static/mk.png"}


# --- the heartbeat card

@pytest.mark.parametrize("now, says", [
    (BoardNow(RUNNING, 12, "2.1.5-beta"), ['<span class="beat">Running</span>', "<b>12 seconds ago</b>",
                                           "Version <b>2.1.5-beta</b>"]),
    (BoardNow(SHOW, 2, None, "Happily <Ever> After"), ['<span class="beat">Showtime</span>',
                                                       "Playing <b>Happily &lt;Ever&gt; After</b>"]),
    (BoardNow(QUIET, 600), ['<span class="beat quiet">Quiet</span>', "<b>10 minutes ago</b>", "Saving restarts it"]),
    (BoardNow(NONE), ['<span class="beat none">No word yet</span>']),
])
def test_the_board_now_card_says_what_the_heartbeat_says(now, says):
    html = settings_page({}, [], now=now)
    card = html[html.index('<section class="card board-now"'):]
    card = card[:card.index("</section>")]
    for text in says:
        assert text in card
    assert 'src="/static/landmark-magic-kingdom.png"' in card
    assert ("Version" in card) == bool(now.version)


def test_without_a_heartbeat_reading_there_is_no_card():
    assert '<section class="card board-now"' not in settings_page({}, [])


# --- the countdown preview

def test_the_countdown_preview_says_what_the_board_says_today_and_tags_that_trip():
    html = settings_page(TRIPS, [], today=TODAY)
    number, lines = countdown_message(Trip(date(2027, 3, 14), date(2027, 3, 19), "Spring Break"), TODAY)
    assert (number, lines) == ("126", ("DAYS TO", "SPRING BREAK"))
    assert '<span class="big">126</span><span class="line">DAYS TO</span><span class="line">SPRING BREAK</span>' in html
    assert 'aria-label="126 DAYS TO SPRING BREAK"' in html and "on March 14, 2027" in html
    rows = html[html.index('id="trip-list"'):html.index('<template id="trip-row">')]
    assert rows.count("On the board now") == 1
    assert rows.index("On the board now") < rows.index('value="Spring Break"') < rows.index('value="2027-06-01"')


def test_on_the_trip_the_preview_counts_its_days():
    html = settings_page(TRIPS, [], today=date(2027, 3, 16))
    assert '<span class="big">DAY 3</span><span class="line">OF 6</span>' in html


def test_a_message_day_has_no_big_number():
    html = settings_page(TRIPS, [], today=date(2027, 3, 13))
    assert '<span class="line">DISNEY</span><span class="line">TOMORROW</span>' in html and 'class="big"' not in html


def test_the_countdown_off_or_with_no_trip_ahead_says_so_and_tags_nothing():
    off = {"trip_countdown": {**TRIPS["trip_countdown"], "enabled": False}}
    html = settings_page(off, [], today=TODAY)
    assert "Off: the board goes straight from park to park." in html and "On the board now" not in html
    html = settings_page(TRIPS, [], today=date(2028, 1, 1))
    assert "No trip coming up" in html and "On the board now" not in html


# --- brightness, rotation, shows, characters

def test_the_display_card_shows_the_castle_at_each_brightness_for_the_script_to_dim():
    html = settings_page({}, [])
    display = html[html.index('id="display"'):html.index('id="shows"')]
    for k in ("all", "day", "night"):
        assert f'<img id="pv-{k}" src="/static/landmark-magic-kingdom.png"' in display
    assert "brightnessPreviews" in SCRIPT and "brightness(${0.25 + 0.75 * percent / 100})" in SCRIPT


def test_the_panel_card_shows_the_castle_turned_by_rotation():
    html = settings_page({"matrix": {"led_pixel_mapper": "Rotate:180"}}, [])
    panel = html[html.index('id="panel"'):html.index('id="display"')]
    assert '<img id="pv-rot" src="/static/landmark-magic-kingdom.png"' in panel
    assert "'Rotate:180': 'rotate(180deg)'" in SCRIPT


def test_the_shows_card_shows_the_castle_the_shows_play_over():
    html = settings_page({}, [])
    shows = html[html.index('id="shows"'):html.index('id="surprises"')]
    assert 'src="/static/landmark-magic-kingdom.png" alt="The castle on the board"' in shows


def test_the_surprises_card_names_every_character_and_counts_them():
    from settings_page.form import character_label, surprise_names
    cast = sorted(character_label(n) for n in surprise_names())
    html = settings_page({}, [])
    assert len(cast) > 10 and f"Choose from all {len(cast)} characters and their chances" in html
    from html import escape
    assert "".join(f"<li>{escape(n)}</li>" for n in cast) in html


def test_the_settings_pages_script_is_valid_javascript(tmp_path):
    if not shutil.which("node"):
        pytest.skip("node isn't installed")
    path = tmp_path / "settings.js"
    path.write_text(SCRIPT, encoding="utf-8")
    done = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
