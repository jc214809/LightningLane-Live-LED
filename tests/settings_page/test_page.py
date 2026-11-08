import pytest
import json
import re
import time

from settings_page.page import SENT, _when, check_result, pin_page, settings_page

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


def test_the_main_page_links_to_the_surprises_page_instead_of_listing_them():
    html = settings_page({}, [])
    assert html.count('href="/surprises"') == 2, "the heading link in the nav, and the card's button"
    assert 'id="surprises"' in html and 'name="surprise_genie"' not in html
    assert 'action="/surprises"' not in html


def test_the_surprises_page_ticks_every_character_but_those_saved_as_off():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({"enabled": True, "characters": {"tron": {"on": False}}})
    assert re.search(r'id="surprises_enabled" name="surprises_enabled" checked', html)
    assert re.search(r'id="surprise_genie" name="surprise_genie" checked', html)
    assert re.search(r'id="surprise_tron" name="surprise_tron"(?! checked)', html)
    assert 'id="surprise_walle"' not in html and '<td>WALL-E (side)</td>' in html
    assert 'action="/surprises"' in html and 'href="/"' in html, "its own form, and a way back"


def test_the_surprises_page_is_all_on_with_nothing_saved_and_shows_the_defaults_greyed():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({})
    assert re.search(r'id="surprises_enabled" name="surprises_enabled" checked', html)
    assert not re.search(r'name="surprise_\w+"(?! checked)', html)
    genie = re.search(r'<input type="number" id="chance_genie"[^>]*>', html).group(0)
    assert 'value=""' in genie and 'placeholder="0.5"' in genie
    assert 'placeholder="10"' in re.search(r'<input type="number" id="ride_chance_falcon"[^>]*>', html).group(0)
    assert 'placeholder="0"' in re.search(r'<input type="number" id="chance_falcon"[^>]*>', html).group(0), \
        "every character can be added to any ride, at 0% until someone does"
    assert 'id="chance_tink"' not in html and 'data-name="tink"' not in html and 'data-name="buzz"' not in html, \
        "Tink and Buzz aren't ride-screen surprises: not on the page"
    assert "12.9%" in html, "the defaults come to"


def test_the_surprises_page_fills_the_saved_chances_and_totals_them():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({"characters": {"genie": {"chance": 1.5}, "falcon": {"ride_chance": 25, "chance": 1}}})
    assert 'id="chance_genie" name="chance_genie" value="1.5"' in html
    assert 'id="ride_chance_falcon" name="ride_chance_falcon" value="25"' in html
    assert 'id="total-all">14.9%</strong>' in html, "12.9 + 1 + 1 (Genie's 0.5 became 1.5)"


def test_every_column_heading_is_a_sort_button_and_the_rows_start_in_alphabetical_order():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({})
    heads = re.findall(r'<th scope="col" aria-sort="none" data-sort="(\w+)" data-first="(\w+)"><button type="button">([^<]+)', html)
    assert heads == [("on", "descending", "On"), ("name", "ascending", "Character"),
                     ("num", "descending", "% of all ride screens"), ("num", "descending", "% on their own rides"),
                     ("rides", "descending", "Rides")]
    labels = re.findall(r'<tr data-name="\w+" data-label="([^"]+)"', html)
    assert labels == sorted(labels, key=str.lower) and len(labels) > 25
    assert "aria-sort" in html and "table.querySelectorAll('thead th')" in html, "the script that sorts them"


RIDES = {"Magic Kingdom": ["Space Mountain"], "Hollywood Studios": ["Millennium Falcon: Smugglers Run",
                                                                      "Star Wars: Rise of the Resistance", "Test Track"]}


def row(html, name):
    return re.search(rf'<tr data-name="{name}".*?</tr><tr class="ride-row"[^>]*>.*?</tr>', html, re.S).group(0)


def test_each_character_has_a_plus_button_after_their_rides_and_a_hidden_panel_under_the_row():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({}, rides=RIDES)
    genie = row(html, "genie")
    button = re.search(r'<button type="button" class="secondary add-rides"[^>]*>.*?</button>', genie, re.S).group(0)
    assert 'aria-expanded="false" aria-label="Add rides for Genie" title="Add rides"' in button
    assert "<svg" in button and "Add</span>" not in button, "a plus sign and no text"
    assert genie.index('class="ride-names') < genie.index("add-rides"), "the names are to its left"
    assert '<tr class="ride-row" hidden><td colspan="5"><div class="ride-pick">' in genie


def test_the_names_of_the_rides_a_character_visits_are_said_and_their_default_rides_are_ticked():
    from settings_page.surprises_page import surprises_page
    falcon = row(surprises_page({}, rides=RIDES), "falcon")
    assert ('<span class="ride-names">Millennium Falcon: Smugglers Run, Star Wars: Rise of the Resistance</span>'
            in falcon)
    assert falcon.count('<input type="hidden" name="rides_falcon"') == 2
    assert 'value="Millennium Falcon: Smugglers Run"' in falcon and 'value="Test Track"' not in falcon
    assert '<span class="ride-names none">No rides</span>' in row(surprises_page({}, rides=RIDES), "genie")


def test_saved_rides_replace_the_default_ones_and_an_empty_list_says_no_rides():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({"characters": {"falcon": {"rides": ["Test Track"]}, "tron": {"rides": ["Space Mountain", "Test Track"]},
                                          "rex": {"rides": []}}}, rides=RIDES)
    assert '<span class="ride-names">Test Track</span>' in row(html, "falcon") and 'value="Test Track"' in row(html, "falcon")
    assert '<span class="ride-names">Space Mountain, Test Track</span>' in row(html, "tron")
    assert '<span class="ride-names none">No rides</span>' in row(html, "rex") and 'name="rides_rex"' not in row(html, "rex")


def test_before_the_ride_list_loads_the_default_rides_are_named_by_their_pieces_but_not_posted():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({})
    assert '<span class="ride-names">Smugglers Run, Rise Of The Resistance</span>' in row(html, "falcon")
    assert 'name="rides_falcon"' not in html, "nothing ticked is posted, so nothing is saved over them"
    assert '<span class="ride-names none">No rides</span>' in row(html, "genie")
    saved = surprises_page({"characters": {"falcon": {"rides": []}}})
    assert '<span class="ride-names none">No rides</span>' in row(saved, "falcon"), "saved as none: not the defaults"


def test_the_ride_panel_can_be_closed_and_shows_every_ride_without_a_scrolling_cap():
    from settings_page.page import STYLE
    from settings_page.surprises_page import SCRIPT, surprises_page
    html = surprises_page({}, rides=RIDES)
    assert "close.className = 'secondary close-rides'" in SCRIPT, "a Close button"
    assert "bar.append(search, closeButton())" in SCRIPT and "foot.appendChild(closeButton())" in SCRIPT, \
        "at the top and the bottom of a long list"
    assert "event.key === 'Escape'" in SCRIPT and "button.title = open ? 'Close' : 'Add rides'" in SCRIPT
    assert SCRIPT in html
    assert ".add-rides[aria-expanded=true] svg { transform: rotate(45deg); }" in STYLE, "the plus turns into a cross"
    assert ".ride-park { max-height" not in STYLE, "a park's rides aren't hidden behind a scrollbar"


def test_enter_in_the_ride_search_box_does_not_submit_the_form_which_would_save_and_restart_the_app():
    from settings_page.surprises_page import SCRIPT
    assert "search.addEventListener('keydown', event => { if (event.key === 'Enter') event.preventDefault(); })" in SCRIPT


def test_hidden_rides_really_disappear_because_the_label_style_would_otherwise_override_hidden():
    from settings_page.page import STYLE
    from settings_page.surprises_page import SCRIPT
    assert ".ride-pick label { display: flex;" in STYLE, "which is why hidden needs its own rule"
    assert ".ride-pick label[hidden], .ride-park[hidden], .ride-pick p[hidden] { display: none; }" in STYLE
    assert "column.hidden = !matches" in SCRIPT and "No rides match" in SCRIPT, "empty parks and no matches are handled"


def test_the_pages_script_is_valid_javascript(tmp_path):
    """Every other check here is that some text is in the script: a quote in the wrong place would pass them all and
    leave the page dead (sorting, the pickers, the totals, Export)."""
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node isn't installed")
    from settings_page.surprises_page import SCRIPT
    path = tmp_path / "surprises.js"
    path.write_text(SCRIPT, encoding="utf-8")
    done = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_export_and_import_are_two_plain_buttons_above_the_form_with_no_text_boxes():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({}, rides=RIDES)
    assert '<button type="button" class="secondary" id="export-btn"' in html and ">Export</button>" in html
    assert '<button type="button" class="secondary" id="import-btn"' in html and ">Import</button>" in html
    share = re.search(r'<div class="share">.*?</span></div>', html, re.S).group(0)
    assert "<textarea" not in share and "<form" not in share and "<input" not in share, "one click, nothing to fill in"
    assert html.index('class="share"') < html.index('<form method="post" action="/surprises" id="settings">')
    assert 'id="share-status" role="status" aria-live="polite"' in share, "says what happened"
    assert "<textarea" not in html and "export-text" not in html and "import-box" not in html, "no boxes anywhere"


def test_export_copies_in_one_click_from_a_snapshot_kept_fresh_so_the_click_is_still_fresh():
    from settings_page.surprises_page import SCRIPT
    assert "fetch('/surprises/export', {method: 'POST', body: new URLSearchParams(new FormData(form))})" in SCRIPT
    assert "refresh();" in SCRIPT and "form.addEventListener('input', stale)" in SCRIPT and "setTimeout(refresh, 300)" in SCRIPT, \
        "fetched ahead on load and after each edit"
    assert "const reply = ready || await refresh();" in SCRIPT, "a click right after an edit waits for the new one"
    assert "if (mine === version) ready = reply" in SCRIPT, "an answer to an older page is dropped"
    assert "document.execCommand('copy')" in SCRIPT and "area.style.cssText = 'position:fixed;top:0;left:-9999px;opacity:0'" in SCRIPT, \
        "a hidden textarea, which works on plain http"
    assert "navigator.clipboard.writeText(text)" in SCRIPT and "Not copied: " in SCRIPT


def test_import_reads_the_clipboard_where_it_may_and_otherwise_waits_for_one_paste():
    from settings_page.surprises_page import SCRIPT
    assert "navigator.clipboard.readText && window.isSecureContext" in SCRIPT, "one click where the browser allows"
    assert "document.addEventListener('paste', onPaste, {once: true})" in SCRIPT and "event.clipboardData.getData('text')" in SCRIPT
    assert "Press Ctrl+V (Cmd+V on a Mac) now to paste the settings." in SCRIPT
    assert "headers: {Accept: 'application/json'}" in SCRIPT and "'Nothing imported: '" in SCRIPT.replace('"', "'"), \
        "a bad paste is checked first and says why, leaving the page as it is"
    assert "send.action = '/surprises/import'" in SCRIPT and "send.submit()" in SCRIPT, "then the board draws the page"


def test_an_imported_page_says_it_is_not_saved_and_a_refused_one_says_why():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({"characters": {"genie": {"chance": 2}}}, imported=["new_one", "tink"])
    assert "<strong>not saved yet</strong>" in html and "new_one, tink" in html and "Saved." not in html
    assert "<strong>Imported.</strong>" in surprises_page({}, imported=[]) and "Left out" not in surprises_page({}, imported=[])
    html = surprises_page({}, ["It isn't JSON."], imported=False)
    assert "Nothing imported." in html and "It isn&#x27;t JSON." in html and "Not saved." not in html


def test_the_rides_on_the_page_are_posted_with_a_marker_whenever_they_are_the_ones_to_save():
    from settings_page.surprises_page import surprises_page
    marker = lambda html, name: re.findall(rf'<input type="hidden" name="rides_set_{name}" value="(\w*)">', html)
    html = surprises_page({"characters": {"genie": {"rides": ["Test Track"]}, "falcon": {"rides": []}}}, rides=RIDES)
    assert marker(html, "genie") == ["saved"] and marker(html, "falcon") == ["saved"], "saved rides, even none"
    assert marker(html, "rex") == ["1"], "the default rides, ticked and known"
    html = surprises_page({"characters": {"genie": {"rides": ["Test Track"]}}})
    assert marker(html, "genie") == ["saved"] and marker(html, "rex") == [], "no list: the defaults can't be named"


def test_opening_a_picker_keeps_saying_the_rides_were_saved():
    from settings_page.surprises_page import SCRIPT
    assert "set.value = markerValue" in SCRIPT
    assert SCRIPT.index("const markerValue") < SCRIPT.index("box.textContent = ''"), "read before the box is cleared"
    assert 'input[type=hidden][name="\' + field + \'"]' in SCRIPT or "input[type=hidden][name=" in SCRIPT, \
        "the marker isn't mistaken for a ride"


def test_the_ride_list_goes_to_the_script_as_json_and_cannot_end_the_script_early():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({}, rides={"Magic Kingdom": ["Space Mountain", "</script><b>"]})
    data = re.search(r'<script type="application/json" id="ride-list">(.*?)</script>', html, re.S).group(1)
    assert json.loads(data) == {"Magic Kingdom": ["Space Mountain", "</script><b>"]}
    assert json.loads(re.search(r'id="ride-list">(.*?)</script>', surprises_page({}), re.S).group(1)) == {}, "not loaded yet"


def test_the_total_is_a_footer_row_with_all_the_chances_and_the_ticked_ones():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({})
    foot = re.search(r"<tfoot>.*?</tfoot>", html, re.S).group(0)
    assert '<th scope="row">Total</th>' in foot and 'id="total-all">12.9%</strong>' in foot
    assert '12.9% from the ticked characters' in foot and "over" not in foot
    assert html.index("</tbody>") < html.index("<tfoot>"), "at the bottom, outside the rows that sort"
    html = surprises_page({"characters": {"genie": {"on": False}, "baymax": {"on": False, "chance": 2}}})
    foot = re.search(r"<tfoot>.*?</tfoot>", html, re.S).group(0)
    assert 'id="total-all">14.2%</strong>' in foot, "12.9 and Baymax's 0.7 became 2: off characters still hold their slice"
    assert "11.7% from the ticked characters" in foot, "14.2 less Genie's 0.5 and Baymax's 2"


def test_a_total_past_100_is_marked_and_the_script_keeps_the_footer_live():
    from settings_page.surprises_page import surprises_page
    html = surprises_page({"characters": {"genie": {"chance": 100}}})
    assert '<strong id="total-all" class="over">' in html
    assert "const showTotals" in html and "table.addEventListener('input', showTotals)" in html


def test_the_surprises_page_shows_problems_and_saved():
    from settings_page.surprises_page import surprises_page
    assert "Not saved." in surprises_page({}, ["Genie: nope."]) and "Genie: nope." in surprises_page({}, ["Genie: nope."])
    assert "restarting with the new settings" in surprises_page({}, saved="restarted")


def test_every_proper_name_is_for_a_real_character():
    from settings_page.form import surprise_names
    from settings_page.form import CHARACTER_NAMES
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


from settings_page.form import panel_choices  # noqa: E402

PANEL = panel_choices({}, "pizero2w", "Raspberry Pi Zero 2 W Rev 1.0")


def _card(html, sid):
    """One card's HTML: a section, or the Advanced <details>."""
    start = html.index(f'id="{sid}"')
    return html[start:html.index("</details>" if sid == "advanced" else "</section>", start)]


def _select(html, name):
    return re.search(rf'<select id="{name}" name="{name}"[^>]*>(.*?)</select>', html).group(1)


def test_pi_model_and_panel_size_head_the_panel_card_with_the_saved_ones_chosen():
    html = settings_page({}, [], panel=PANEL)
    assert _select(html, "pi_model").startswith('<option value="auto" selected>Automatic (Pi Zero 2 W)</option>')
    assert '<option value="64x32" selected>' in _select(html, "panel_size"), "unset: the driver's 64x32"
    panel = _card(html, "panel")
    assert panel.index('id="pi_model"') < panel.index('id="panel_size"') < panel.index('id="matrix_led_pixel_mapper"')
    html = settings_page({"pi_model": "pi4", "matrix": {"led_rows": 64, "led_cols": 64}}, [], panel=PANEL)
    assert '<option value="pi4" selected>' in _select(html, "pi_model")
    assert '<option value="64x64" selected>' in _select(html, "panel_size")
    assert 'id="pi_model"' not in settings_page({}, []), "no choices: no dropdowns"
    assert '<option value="auto" selected>' in settings_page({"pi_model": "pi9"}, [], panel=PANEL)


def test_the_models_settings_are_in_panel_size_is_its_dropdown_and_the_rest_under_advanced():
    html = settings_page({}, [], panel=PANEL)
    panel, advanced = _card(html, "panel"), _card(html, "advanced")
    for key in ("led_pixel_mapper", "led_gpio_mapping", "led_slowdown_gpio", "led_pwm_lsb_nanoseconds"):
        assert f'id="matrix_{key}"' in panel and f'id="matrix_{key}"' not in advanced, key
    for key in ("led_rows", "led_cols"):
        assert f'id="matrix_{key}"' not in html, "the Panel size dropdown sets them"
    assert 'id="matrix_led_chain"' in advanced and 'id="matrix_led_brightness"' not in advanced


def test_blank_fields_say_the_chosen_models_default():
    html = settings_page({}, [], panel=PANEL)  # Automatic: Pi Zero 2 W
    assert re.search(r'id="matrix_led_slowdown_gpio"[^>]*><option value="" selected>Pi Zero 2 W default: 2</option>',
                     html)
    assert 'placeholder="Default: 130" data-key="led_pwm_lsb_nanoseconds"' in html
    assert 'placeholder="Pi Zero 2 W default: 100" data-key="led_brightness"' in html
    html = settings_page({"pi_model": "pi4"}, [], panel=PANEL)
    assert re.search(r'id="matrix_led_slowdown_gpio"[^>]*><option value="" selected>Pi 4 default: 4</option>', html)
    assert 'placeholder="Default" data-key="led_brightness"' in settings_page({}, [])


def test_the_page_carries_each_models_blanks_for_the_script():
    html = settings_page({}, [], panel=PANEL)
    data = json.loads(re.search(r'<script type="application/json" id="panel-blanks">(.*?)</script>', html).group(1))
    assert data == {"auto": "pizero2w", "blanks": PANEL.blanks}
    evil = PANEL._replace(blanks={"pizero2w": {"led_pixel_mapper": "</script><b>"}})
    assert "</script><b>" not in settings_page({}, [], panel=evil)


def test_rotation_is_a_dropdown_that_keeps_a_custom_saved_mapper():
    html = settings_page({"matrix": {"led_pixel_mapper": "Rotate:180"}}, [], panel=PANEL)
    assert '<option value="Rotate:180" selected>Upside down (Rotate:180)</option>' in html
    html = settings_page({"matrix": {"led_pixel_mapper": "U-mapper;Rotate:90"}}, [], panel=PANEL)
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


def test_pushover_is_its_own_card_after_weather_with_masked_keys():
    html = settings_page({"pushover": {"user_key": "u-secret-abcd", "app_token": "t-secret-wxyz"}}, [])
    assert html.index('id="weather"') < html.index('id="phone"') < html.index('id="pushover_user"') < html.index(
        'id="pushover_token"') < html.index('id="pushover_enabled"') < html.index('id="parks"')
    assert "abcd" in html and "wxyz" in html and "secret" not in html
    assert 'id="pushover_enabled" name="pushover_enabled" checked' in html


def test_the_sign_in_page_offers_to_send_the_pin_only_with_pushover():
    assert 'action="/pin/send"' not in pin_page()
    html = pin_page(phone=True)
    assert html.index('action="/pin/show"') < html.index('action="/pin/send"') < html.index('action="/pin"')


def test_every_send_outcome_says_something_different():
    plain = pin_page(phone=True)
    assert all(pin_page(phone=True, sent=outcome) != plain for outcome in SENT)
    assert len({pin_page(phone=True, sent=outcome) for outcome in SENT}) == len(SENT)


def test_signed_in_the_top_bar_has_sign_out_but_not_on_the_hotspot():
    assert 'action="/signout"' in settings_page({}, [])
    assert 'action="/signout"' not in settings_page({}, [], hotspot="Disneypi-setup")
    assert 'action="/signout"' not in pin_page() and "Signed out." in pin_page(signed_out=True)


UPDATES = {"version": "2.1.0", "sha": "a" * 40, "branch": "develop-beta", "running": False, "phase": "idle",
           "status": None, "step": None, "from": None, "outcome": None, "check": None, "channel": "releases",
           "auto_check": False}


def _updates(started=None, **changes):
    return settings_page({}, [], updates={**UPDATES, **changes}, started=started)


def test_the_updates_card_is_first_outside_the_settings_form_with_its_own_forms():
    html = _updates()
    assert html.index('id="updates"') < html.index('id="settings"'), "first, and not part of Save"
    assert html.index('href="#updates"') < html.index('href="#live"')
    assert "<strong>2.1.0</strong>" in html and "aaaaaaa" in html and "on develop-beta" in html
    assert re.search(r'<form method="post" action="/update/check"[^>]*><select id="channel" name="channel">'
                     r'<option value="releases" selected>Releases</option><option value="beta">Beta</option>', html)
    assert "/update/start" not in html and "/update/rollback" not in html, "nothing found, nothing to undo"
    assert 'id="updates"' not in settings_page({}, []), "no view: no card"


def test_a_check_that_found_one_offers_update_now_on_its_channel():
    found = {"channel": "beta", "result": "would_update", "message": "would update to develop-beta (bbbbbbb)",
             "ok": True, "at": 0}
    html = _updates(check={**found, "ref": "develop-beta", "sha": "b" * 40}, channel="beta")
    assert '<div class="notice new" role="status">' in html
    assert '<strong>Update available on Beta: Beta <span class="mono">bbbbbbb</span></strong>' in html, "its commit"
    html = _updates(check={**found, "ref": "v9", "sha": "b" * 40, "channel": "releases"})
    assert "<strong>Update available on Releases: v9 bbbbbbb</strong>" in html, "no version: ref and commit"
    html = _updates(check={**found, "ref": "develop-beta", "sha": "b" * 40}, channel="beta")
    assert re.search(r'action="/update/start"[^>]*><input type="hidden" name="channel" value="beta">', html)
    assert 'class="changes"' not in html, "the check couldn't list them: no list"
    html = _updates(check={**found, "result": "current", "message": "no release newer than 2.1.0"})
    assert '<div class="notice good" role="status">' in html and "this is the newest on Beta" in html
    assert "No release newer than 2.1.0." in html and "/update/start" not in html


def test_a_check_says_up_to_date_waiting_or_blocked_apart():
    check = {"channel": "beta", "ok": True, "at": 0}
    html = _updates(check={**check, "result": "waiting", "message": "3333333's CI is still running (test)"})
    assert "Up to date for now" in html and "isn't ready yet" in html and "CI is still running" in html
    assert '<div class="notice info"' in html and "/update/start" not in html
    assert "3333333&#x27;s CI is still running (test)." in html, "a sha isn't capitalised"
    html = _updates(check={**check, "result": "blocked", "ok": False, "message": "fireworks is playing"})
    assert '<div class="notice warn"' in html and "Can't update right now:</strong> Fireworks is playing." in html
    assert "Up to date" not in html


def test_a_beta_waiting_on_its_tests_lists_each_run():
    check = {"channel": "beta", "result": "waiting", "ok": True, "at": 0, "message": "3333333's CI is still running"}
    html = _updates(check={**check, "runs": [["test (3.13)", "passed"], ["test (3.11)", "running"]]})
    assert "<strong>A newer Beta is being tested.</strong>" in html and "Up to date for now" not in html
    assert ('<ol class="steps" aria-label="Tests"><li class="now">Tests on Python 3.11: running</li>'
            '<li class="done">Tests on Python 3.13: passed</li></ol>') in html, "in name order, step styles"
    assert "It can be installed once both pass." in html and "/update/start" not in html
    html = _updates(check={**check, "runs": [["test (3.11)", "passed"], ["lint", "failed"]]})
    assert "<strong>A newer Beta didn't pass its tests.</strong>" in html
    assert '<li class="failed">lint: failed</li>' in html and "the next Beta that passes can be" in html
    html = _updates(check={**check, "runs": []})
    assert "<strong>A newer Beta hasn't been tested yet.</strong>" in html and 'aria-label="Tests"' not in html
    html = _updates(check={**check, "runs": [["a", "running"], ["b", "running"], ["c", "passed"]]})
    assert "once they all pass" in html


def test_with_no_check_the_page_checks_the_installed_channel_by_itself():
    html = _updates(auto_check=True, channel="beta")
    assert '<div id="update-check" data-auto="beta">' in html and "Checking Beta for a newer version" in html
    assert "fetch('/update/check'" in html
    assert 'id="update-check"' not in _updates(), "nothing to check, nothing said"
    assert check_result({**UPDATES, "auto_check": True})
    assert check_result(UPDATES) == ""


def test_after_an_update_the_card_offers_a_rollback_that_warns_about_config_json():
    html = _updates(phase="updated", branch=None, **{"from": {"version": "2.0.9", "sha": "c" * 40}},
                    outcome={"command": "update", "result": "updated", "message": "updated to v2.2.0 (ddddddd)",
                             "ok": True, "at": 0})
    assert "as installed by an update" in html
    assert '<div class="notice good" role="status">' in html and "Last update" in html
    assert re.search(r'action="/update/rollback"[^>]*data-confirm="[^"]*undoing settings saved since', html)
    assert "Back to 2.0.9 (ccccccc)" in html
    html = _updates(phase="updated", **{"from": {"version": "2.0.9", "sha": "c" * 40, "branch": "develop-beta"}})
    assert "Back to Beta ccccccc on develop-beta, as before the last update" in html, "its commit, not a channel"
    html = _updates(phase="updated", **{"from": {"version": "2.0.9", "sha": "c" * 40, "channel": "beta"}})
    assert "Back to Beta ccccccc, as before the last update" in html, "a detached Beta (an earlier update's)"
    html = _updates(phase="updated", **{"from": {"version": "2.0.9", "sha": "c" * 40, "branch": "main"}})
    assert "Back to 2.0.9 (ccccccc) on main, as before the last update" in html
    assert "/update/rollback" not in _updates(phase="rolled_back", **{"from": {"version": "2.0.9", "sha": "c"}})


def test_a_failed_update_and_a_failed_rollback_say_so():
    html = _updates(phase="rolled_back", outcome={"command": "update", "result": "rolled_back", "ok": False,
                                                  "message": "rolled back to 2.1.0: the app crashed", "at": 0})
    assert '<div class="notice bad" role="alert">' in html and "Rolled back to 2.1.0: the app crashed." in html
    html = _updates(phase="rollback_failed", **{"from": {"version": "2.0.9", "sha": "c" * 40}})
    assert "The last rollback failed" in html and "sudo lll-rollback" in html and "/update/rollback" in html
    assert "stopped midway" in _updates(phase="checking", **{"from": {"version": "2.0.9", "sha": "c" * 40}})


def test_while_one_runs_the_card_follows_it_with_the_buttons_off():
    html = _updates(running=True, phase="switched", status="Installing the new version", step=2,
                    **{"from": {"version": "2.0.9", "sha": "c" * 40}},
                    outcome={"command": "update", "result": "updated", "message": "old news", "ok": True, "at": 0})
    assert 'id="update-running"' in html and "Installing the new version" in html
    assert ('<ol class="steps" id="update-steps" aria-label="Steps"><li class="done">Checking it can update</li>'
            '<li class="done">Saving a rollback point</li><li class="now" aria-current="step">Installing the new '
            'version</li><li>Restarting and checking it works</li></ol>') in html
    assert "Old news" not in html and "stopped midway" not in html
    assert re.search(r'action="/update/rollback".*?<button type="submit" class="secondary" disabled>', html)
    assert "fetch('/update/status'" in html
    html = _updates(running=True, phase="rolling_back", status="Rolling back", step=None, auto_check=True,
                    check={"channel": "beta", "result": "current", "ok": True, "at": 0, "message": "x"})
    assert 'id="update-steps" aria-label="Steps" hidden>' in html, "a rollback has no steps"
    assert 'id="update-check"' not in html, "no check while it runs"


def test_starting_says_how_it_went():
    assert "Couldn't start it" in _updates(started="failed")
    assert "already running" in _updates(started="busy")
    assert "<strong>Started.</strong>" in _updates(started="started")
    assert "<strong>Started.</strong>" not in _updates(started="started", running=True, status="Saving a rollback point")


def test_an_update_found_lists_whats_in_it_linked_to_github():
    changes = [[200 + n, f"Change {n}"] for n in range(14, 0, -1)]
    found = {"channel": "releases", "result": "would_update", "message": "would update to v2.2.0 (2222222)",
             "ok": True, "at": 0, "ref": "v2.2.0", "sha": "2" * 40, "version": "2.2.0", "changes": changes,
             "packages": True}
    html = _updates(check=found)
    assert "Update available on Releases: 2.2.0" in html and "<strong>2.1.0 \u2192 2.2.0</strong>" in html
    assert ('<li><a href="https://github.com/jc214809/LightningLane-Live-LED/pull/214" target="_blank" '
            'rel="noopener">#214</a><span>Change 14</span></li>') in html
    assert "Change 3<" in html and "Change 2<" not in html and "and 2 more" in html
    assert "up to hours on a Pi Zero" in html
    html = _updates(check={**found, "changes": [[None, "Fix <a> typo"]], "packages": False})
    assert "<span>Fix &lt;a&gt; typo</span>" in html and "up to hours" not in html


def test_while_it_runs_the_card_says_what_its_installing():
    html = _updates(running=True, phase="checking", status="Checking the new version works",
                    to={"ref": "develop-beta", "sha": "9" * 40, "version": "2.2.0", "changes": [[201, "Updates card"]]})
    assert 'Updating to Beta <span class="mono">9999999</span>' in html and "Updates card" in html
    html = _updates(running=True, phase="checking", status="x", to={"ref": "v2.2.0", "sha": "9" * 40, "version": "2.2.0"})
    assert "Updating to 2.2.0" in html


def test_a_beta_build_shows_as_beta_not_as_the_release_it_grew_from():
    html = _updates(installed_channel="beta", version="2.0.0")
    assert '<strong>Beta <span class="mono">aaaaaaa</span></strong>' in html
    assert "A Beta (test) version on develop-beta, newer than release 2.0.0" in html
    assert "<strong>2.0.0</strong>" not in html
    html = _updates(installed_channel="releases", branch="main", version="2.1.0")
    assert '<strong>2.1.0</strong> <span class="mono">aaaaaaa</span>' in html and "Beta (test)" not in html
    found = {"channel": "beta", "result": "would_update", "message": "m", "ok": True, "at": 0,
             "ref": "develop-beta", "sha": "b" * 40, "version": "2.0.0", "changes": []}
    html = _updates(installed_channel="beta", check=found, channel="beta")
    assert '<strong>Beta <span class="mono">aaaaaaa</span> \u2192 Beta <span class="mono">bbbbbbb</span></strong>' in html
    html = _updates(installed_channel="beta", channel="releases",
                    check={**found, "channel": "releases", "ref": "v2.1.0", "version": "2.1.0"})
    assert '<strong>Beta <span class="mono">aaaaaaa</span> \u2192 2.1.0</strong>' in html


def test_a_tagged_beta_shows_by_its_number():
    html = _updates(installed_channel="beta", version="2.1.5-beta")
    assert "<strong>Beta 2.1.5</strong>" in html and "newer than release 2.1.0" in html
    html = _updates(installed_channel="beta", version="2.1.5-beta-2-gaaaaaaa")
    assert '<strong>Beta <span class="mono">aaaaaaa</span></strong>' in html, "past a Beta: by its commit"
    found = {"channel": "beta", "result": "would_update", "message": "m", "ok": True, "at": 0,
             "ref": "develop-beta", "sha": "b" * 40, "version": "2.1.6-beta", "changes": []}
    html = _updates(installed_channel="beta", version="2.1.5-beta", check=found, channel="beta")
    assert "<strong>Beta 2.1.5 \u2192 Beta 2.1.6</strong>" in html


def test_each_pull_request_shows_its_notes_under_its_title_and_the_behind_the_scenes_ones_together():
    found = {"channel": "beta", "result": "would_update", "message": "m", "ok": True, "at": 0,
             "ref": "develop-beta", "sha": "b" * 40, "changes": [
                 [206, "Sparkle", ["The castle sparkles.", "So do <the> rides."]],
                 [205, "Faster CI", []], [204, "Tidy tests", []],
                 [203, "Updates card polish", None]]}
    html = _updates(check=found, channel="beta")
    assert ('#206</a><span>Sparkle<span class="hint note">The castle sparkles.</span>'
            '<span class="hint note">So do &lt;the&gt; rides.</span></span></li>') in html, "notes under the title"
    assert '#203</a><span>Updates card polish</span></li>' in html, "from before release notes: the title alone"
    assert re.search(r"Behind the scenes, nothing you'd notice: <a [^>]*>#205</a>, <a [^>]*>#204</a></span>", html)
    assert "Faster CI" not in html
    html = _updates(check={**found, "changes": [[None, "Fix a typo", None]]}, channel="beta")
    assert "<span>Fix a typo</span>" in html and "Behind the scenes" not in html


def test_update_times_use_a_12_hour_clock():
    def at(hour, minute):
        return time.mktime((2026, 11, 4, hour, minute, 0, 0, 0, -1))
    assert _when(at(19, 5)) == "04 Nov 7:05 PM"
    assert _when(at(0, 30)) == "04 Nov 12:30 AM" and _when(at(12, 0)) == "04 Nov 12:00 PM"
    assert _when(at(9, 41)) == "04 Nov 9:41 AM"
    assert _when(None) == "?" and _when("soon") == "?"
