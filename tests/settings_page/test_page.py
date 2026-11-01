import json
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


from settings_page.form import BoardTypes  # noqa: E402

TYPES = BoardTypes(
    [("auto", "Automatic (Pi Zero 2 W, boards.json entry)"), ("pi4", "Pi 4"), ("pizero2w", "Pi Zero 2 W")],
    [("", "Automatic (64x32, boards.json entry)"), ("64x64", "64x64"), ("64x32", "64x32")],
    "pizero2w", "64x32",
    {"pi4-64x64": {"led_rows": 64, "led_slowdown_gpio": 4, "led_brightness": 100, "led_pixel_mapper": "Rotate:180"},
     "pi4-64x32": {"led_rows": 32, "led_slowdown_gpio": 4, "led_brightness": 100, "led_pixel_mapper": "Rotate:180"},
     "pizero2w-64x32": {"led_rows": 32, "led_slowdown_gpio": 2, "led_brightness": 90,
                        "led_pixel_mapper": "Rotate:180"}},
    {"led_pixel_mapper": "Rotate:180"})


def _card(html, sid):
    """One card's HTML: a section, or the Advanced <details>."""
    start = html.index(f'id="{sid}"')
    return html[start:html.index("</details>" if sid == "advanced" else "</section>", start)]


def _select(html, name):
    return re.search(rf'<select id="{name}" name="{name}"[^>]*>(.*?)</select>', html).group(1)


def test_pi_model_and_panel_size_head_the_panel_card_with_the_saved_ones_or_automatic_chosen():
    html = settings_page({}, [], board_types=TYPES)
    assert _select(html, "pi_model").startswith('<option value="auto" selected>Automatic (Pi Zero 2 W, boards.json entry)')
    assert _select(html, "panel_size").startswith('<option value="" selected>Automatic (64x32, boards.json entry)')
    panel = _card(html, "panel")
    assert panel.index('id="pi_model"') < panel.index('id="panel_size"') < panel.index('id="matrix_led_pixel_mapper"')
    html = settings_page({"pi_model": "pi4", "matrix": {"led_rows": 64, "led_cols": 64}}, [], board_types=TYPES)
    assert '<option value="pi4" selected>' in _select(html, "pi_model")
    assert '<option value="64x64" selected>' in _select(html, "panel_size")
    assert 'id="pi_model"' not in settings_page({}, []), "no board types: no dropdowns"
    assert '<option value="auto" selected>' in settings_page({"pi_model": "pi9"}, [], board_types=TYPES)


def test_the_presets_settings_are_in_panel_size_is_its_dropdown_and_the_rest_under_advanced():
    html = settings_page({}, [], board_types=TYPES)
    panel, advanced = _card(html, "panel"), _card(html, "advanced")
    for key in ("led_pixel_mapper", "led_gpio_mapping", "led_slowdown_gpio", "led_pwm_lsb_nanoseconds"):
        assert f'id="matrix_{key}"' in panel and f'id="matrix_{key}"' not in advanced, key
    for key in ("led_rows", "led_cols"):
        assert f'id="matrix_{key}"' not in html, "the Panel size dropdown sets them"
    assert 'id="matrix_led_chain"' in advanced and 'id="matrix_led_brightness"' not in advanced


def test_blank_fields_name_the_value_for_the_chosen_model_and_size():
    html = settings_page({}, [], board_types=TYPES)  # Automatic: Pi Zero 2 W at 64x32
    assert re.search(r'id="matrix_led_slowdown_gpio"[^>]*><option value="" selected>Board default: 2</option>', html)
    assert 'placeholder="Board default: 90" data-key="led_brightness"' in html
    html = settings_page({"pi_model": "pi4", "matrix": {"led_rows": 64, "led_cols": 64}}, [], board_types=TYPES)
    assert re.search(r'id="matrix_led_slowdown_gpio"[^>]*><option value="" selected>Board default: 4</option>', html)
    assert re.search(r'id="matrix_led_pixel_mapper"[^>]*><option value="" selected>Board default: Rotate:180</option>',
                     html)
    html = settings_page({"pi_model": "pizero2w", "matrix": {"led_rows": 64}}, [], board_types=TYPES)
    assert re.search(r'id="matrix_led_slowdown_gpio"[^>]*><option value="" selected>Board default</option>', html), \
        "no preset for that pair: only the board's own settings"
    assert 'placeholder="Board default" data-key="led_brightness"' in settings_page({}, [])


def test_the_page_carries_the_presets_for_the_script():
    html = settings_page({}, [], board_types=TYPES)
    data = json.loads(re.search(r'<script type="application/json" id="board-defaults">(.*?)</script>', html).group(1))
    assert data == {"auto_model": "pizero2w", "auto_size": "64x32", "presets": TYPES.defaults, "own": TYPES.own}
    evil = TYPES._replace(own={"led_pixel_mapper": "</script><b>"})
    assert "</script><b>" not in settings_page({}, [], board_types=evil)


def test_rotation_is_a_dropdown_that_keeps_a_custom_saved_mapper():
    html = settings_page({"matrix": {"led_pixel_mapper": "Rotate:180"}}, [], board_types=TYPES)
    assert '<option value="Rotate:180" selected>Upside down (Rotate:180)</option>' in html
    html = settings_page({"matrix": {"led_pixel_mapper": "U-mapper;Rotate:90"}}, [], board_types=TYPES)
    assert '<option value="U-mapper;Rotate:90" selected>U-mapper;Rotate:90</option>' in html


def test_volume_shows_the_saved_one_or_80_as_a_placeholder():
    html = settings_page({"sound": {"volume": 65}}, [])
    assert re.search(r'<input type="number" id="sound_volume" name="sound_volume" value="65"[^>]*placeholder="80"', html)
    assert 'id="sound_volume" name="sound_volume" value=""' in settings_page({}, [])


def test_volume_has_a_slider_and_buttons_that_never_take_enter_from_save():
    html = settings_page({"sound": {"volume": 65}}, [])
    assert re.search(r'<input type="range" id="volume_slider" class="js-only" min="0" max="100" value="65"', html)
    assert 'value="80" aria-label="Volume slider"' in settings_page({}, []), "blank: the slider sits at 80"
    for action in ("set", "test"):
        assert f'<button type="button" class="secondary" name="volume_action" value="{action}">' in html
    form = html[html.index('<form method="post" action="/save"'):]
    first_submit = re.search(r'<button type="submit"[^>]*>', form).group(0)
    assert 'id="save"' in first_submit, "Enter in a field presses the first submit button: it must be Save"
