import re

from settings_page.page import settings_page

CONFIG = {"trip_countdown": {"enabled": True, "trip_dates": [
    {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"}, "2027-06-01"]}}


def test_every_trip_has_an_x_in_its_corner_that_ticks_its_remove_box():
    html = settings_page(CONFIG, [])
    xs = re.findall(r'<label class="trip-x" for="(trip_remove_\w+)"[^>]*><input type="checkbox" id="\1" name="\1"', html)
    # the two saved trips and the template "Add a trip" copies
    assert xs == ["trip_remove_0", "trip_remove_1", "trip_remove_N"]
    assert "Remove</label>" not in html, "no Remove button left"


def test_a_blank_trip_row_only_when_there_are_no_trips():
    assert 'id="trip_start_2"' not in settings_page(CONFIG, []), "two trips: Add a trip, no blank row"
    html = settings_page({}, [])
    assert 'id="trip_start_0" name="trip_start_0" value=""' in html and 'id="trip_start_1"' not in html


def test_the_surprise_is_a_dropdown_of_characters_with_the_saved_one_chosen():
    html = settings_page({"force_surprise": "chip_dale_swing"}, [])
    select = re.search(r'<select id="force_surprise" name="force_surprise">(.*?)</select>', html).group(1)
    assert select.startswith('<option value="">None</option>')
    assert '<option value="chip_dale_swing" selected>Chip &#x27;n&#x27; Dale (swing)</option>' in select
    assert '<option value="mcqueen">Lightning McQueen</option>' in select and 'value="wipe"' not in select
    assert '<option value="baymax">Baymax</option>' in select, "title case for the rest"


def test_every_proper_name_is_for_a_real_character():
    from settings_page.form import surprise_names
    from settings_page.page import CHARACTER_NAMES
    assert set(CHARACTER_NAMES) <= set(surprise_names())


def test_debug_and_the_surprise_are_their_own_testing_card_not_under_advanced():
    html = settings_page({}, [])
    testing = html.index('<section class="card" id="testing"')
    assert testing < html.index('id="debug"') < html.index('id="force_surprise"') < html.index('id="advanced"')
    assert '<a href="#testing">' in html


def test_the_brightness_schedule_is_filled_from_config_or_peloton_leds_defaults():
    html = settings_page({}, [])
    assert re.search(r'id="brightness_schedule" name="brightness_schedule">', html), "off with none"
    assert 'id="bright_day" name="bright_day" value="80"' in html and 'value="22:00"' in html
    html = settings_page({"brightness_schedule": {"day": 60, "night": 5, "day_start": "08:30",
                                                  "night_start": "21:00"}}, [])
    assert 'id="brightness_schedule" name="brightness_schedule" checked>' in html
    assert 'id="bright_night" name="bright_night" value="5"' in html and 'value="08:30"' in html


def test_weather_is_its_own_card_apart_from_the_live_ride_updates():
    html = settings_page({}, [])
    live, weather = html.index('id="live"'), html.index('id="weather"')
    assert live < html.index('id="themeparks_key"') < html.index('id="ws_protocol"') < weather
    assert weather < html.index('id="weather_key"') < html.index('id="parks"')


def test_schedule_values_are_marked_as_suggestions_until_one_is_saved():
    assert "Not set up yet" in settings_page({}, [])
    saved = {"day": 60, "night": 5, "day_start": "08:30", "night_start": "21:00"}
    assert "Not set up yet" not in settings_page({"brightness_schedule": saved}, [])


def test_parks_are_chips_in_order_with_suggestions_from_the_list():
    names = [("EPCOT", "Walt Disney World® Resort"), ("Magic Kingdom", "Walt Disney World® Resort")]
    html = settings_page({"parks": ["Magic Kingdom", "EPCOT", "Old Park"]}, [], park_names=names)
    chips = re.findall(r'<li class="park-chip( unknown)?"[^>]*><input type="hidden" name="park" value="([^"]*)">', html)
    assert chips == [("", "Magic Kingdom"), ("", "EPCOT"), (" unknown", "Old Park"), ("", "")], \
        "saved order, a name not on the list marked, then the template's"
    assert 'name="park_remove" value="Old Park"' in html
    assert '<datalist id="park-names"><option value="EPCOT">Walt Disney World® Resort</option>' in html
    assert 'id="park_add" name="park_add" value="" list="park-names"' in html


def test_with_no_park_list_the_picker_says_so_and_marks_nothing():
    html = settings_page({"parks": ["Old Park"]}, [])
    assert "hasn&#x27;t loaded yet" in html or "hasn't loaded yet" in html
    assert 'class="park-chip unknown"' not in html and '<datalist id="park-names"></datalist>' in html


def test_no_parks_saved_shows_walt_disney_worlds_four():
    from settings_page.form import WDW_PARKS
    html = settings_page({}, [])
    assert re.findall(r'name="park" value="([^"]+)"', html) == list(WDW_PARKS)
