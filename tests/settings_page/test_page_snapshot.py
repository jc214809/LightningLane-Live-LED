"""Pins every byte of HTML the settings page's modules produce today, for the code-health refactor
(docs/plans/CODE-HEALTH-PLAN.md, item 2b): the main page for the example config and for a config with every
optional section filled, the PIN-locked and signed-out sign-in pages, problems and saved notices, the Updates card in
each state, the Surprise characters page, and the plain message page. Each output is stored under fixtures/page/.
The page's stylesheet and script are the same in every output, so they are stored once (style.css, script.js) and
replaced by a marker in the rest. A change that alters any byte fails here. To rewrite the fixtures on purpose,
run once with PIN_REGEN=1 and read the diff.

Frozen: the clock's zone (update times print in it), the countdown's "today", and the board's version, landmark
pictures and Pi model, which the cases pass in or which are read from files in the repo."""

import copy
import json
import os
import time
from datetime import date

import pytest

from settings_page import page, surprises_page
from settings_page.board_status import QUIET, RUNNING, SHOW, BoardNow
from settings_page.form import panel_choices
from settings_page.page import check_result, message_page, notices, pin_page, settings_page, updates_card

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXTURES = os.path.join(HERE, "fixtures", "page")
STYLE_MARK, SCRIPT_MARK, SURPRISES_SCRIPT_MARK = "@@STYLE@@", "@@SCRIPT@@", "@@SURPRISES_SCRIPT@@"
FORM_SCRIPT_MARK = "@@FORM_SCRIPT@@"  # the sign-in page's only script: the form helper
TODAY = date(2027, 1, 15)
PANEL = panel_choices({}, "pi4", "Raspberry Pi 4 Model B Rev 1.5")


def example():
    with open(os.path.join(ROOT, "config.json-example"), encoding="utf-8") as f:
        return json.load(f)


# Every optional section of config.json filled, odd values included (a custom sound device, a park off the
# picker's list, a show config for a show the page doesn't know, a matrix with every setting).
FULL = {
    "parks": ["Magic Kingdom", "EPCOT", "Hollywood Studios", "Animal Kingdom", "Cedar Point", "Pretend <Park>"],
    "websocket": {"enabled": False, "api_key": "tp-secret-1234", "protocol": "preview"},
    "weather": {"apikey": "owm-secret-9876"},
    "pushover": {"user_key": "u-secret-abcd", "app_token": "t-secret-wxyz", "enabled": False},
    "trip_countdown": {
        "enabled": True,
        "trip_dates": [
            {"start": "2027-01-01", "end": "2027-01-03", "name": "Past"},
            {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring <Break>"},
            "2027-06-01",
            {"start": "2027-09-09", "name": "Fall"},
        ],
    },
    "sound": {"enabled": True, "device": "hw:9,9", "volume": 55, "quiet_hours": {"start": "22:00", "end": "08:00"}},
    "brightness_schedule": {"day": 90, "night": 20, "day_start": "06:30", "night_start": "21:15"},
    "shows": [
        {"name": "Happily Ever After", "enabled": False, "version": "v2", "force": True},
        {"name": "Christmas Party", "enabled": True, "version": "v1"},
        {"name": "Old Show", "version": "v1"},
        "junk",
        {"name": 5},
    ],
    "force_surprise": "chip_dale_swing",
    "debug": True,
    "pi_model": "pi4",
    "matrix": {
        "led_rows": 32,
        "led_cols": 64,
        "led_chain": 2,
        "led_parallel": 1,
        "led_pwm_bits": 9,
        "led_brightness": 60,
        "led_gpio_mapping": "adafruit-hat",
        "led_scan_mode": 1,
        "led_pwm_lsb_nanoseconds": 130,
        "led_show_refresh": True,
        "led_slowdown_gpio": 2,
        "led_no_hardware_pulse": False,
        "led_rgb_sequence": "RGB",
        "led_panel_type": "FM6126A",
        "led_pixel_mapper": "Rotate:45",
        "led_row_addr_type": 0,
        "led_multiplexing": 0,
        "led_limit_refresh": 0,
        "led_pwm_dither_bits": 0,
        "emulated": False,
        "drop_privileges": True,
    },
}
PARK_NAMES = [
    ("Magic Kingdom", "Walt Disney World Resort"),
    ("EPCOT", "Walt Disney World Resort"),
    ("Cedar Point", "Cedar Point & <More>"),
]
CARDS = ["plughw:CARD=Headphones,DEV=0", "plughw:CARD=Device,DEV=0"]

VIEW = {
    "version": "2.1.0",
    "sha": "a" * 40,
    "branch": "develop-beta",
    "running": False,
    "phase": "idle",
    "status": None,
    "step": None,
    "from": None,
    "outcome": None,
    "check": None,
    "channel": "releases",
    "auto_check": False,
}
FOUND = {
    "channel": "beta",
    "result": "would_update",
    "message": "would update to develop-beta (bbbbbbb)",
    "ok": True,
    "at": 1_700_000_000,
    "ref": "develop-beta",
    "sha": "b" * 40,
}
CHANGES = [
    [206, "Sparkle", ["The castle sparkles.", "So do <the> rides."]],
    [205, "Faster CI", []],
    [204, "Tidy tests", []],
    [203, "Updates card polish", None],
    [None, "Fix a typo", None],
] + [[100 + i, f"Change {i}", ["Note"]] for i in range(14)]


def view(**changes):
    return {**VIEW, **changes}


def full_updates():
    return view(
        version="2.1.5-beta",
        installed_channel="beta",
        channel="beta",
        check={**FOUND, "version": "2.1.6-beta", "packages": True, "changes": CHANGES},
        outcome={"command": "update", "ok": True, "at": 1_699_990_000, "message": "updated to 2.1.5-beta"},
        **{
            "from": {"version": "2.1.0", "sha": "c" * 40, "branch": "develop-beta", "channel": "releases"},
            "phase": "updated",
        },
    )


def page_cases():
    """{name: callable returning the HTML}."""

    def main(config, **kw):
        return lambda: settings_page(config, CARDS, today=TODAY, **kw)

    full_kw = dict(
        hotspot=None,
        board="Disneypi",
        park_names=PARK_NAMES,
        panel=PANEL,
        updates=full_updates(),
        now=BoardNow(RUNNING, 12, "2.1.5-beta"),
    )
    cases = {
        "main_example": main(
            example(),
            board="Disneypi",
            park_names=PARK_NAMES,
            panel=PANEL,
            updates=view(),
            now=BoardNow(SHOW, 2, "2.1.5", "Happily <Ever> After"),
        ),
        "main_example_bare": main(example()),
        "main_empty": main({}, board="board.local"),
        "main_full": main(FULL, **full_kw),
        "main_full_hotspot": main(FULL, **{**full_kw, "hotspot": "Disneypi <setup>"}),
        "main_full_no_names": main(FULL, board="Disneypi", panel=PANEL, now=BoardNow(QUIET, 400)),
        "main_problems": main(
            FULL,
            problems=["Parks: bad <name>", "Sound volume must be 0 to 100"],
            board="Disneypi",
            note="config.json can't be read (<oops>)",
            updates=view(),
        ),
        "main_none_now": main(
            {"matrix": "junk", "websocket": [], "sound": 5, "parks": "x", "shows": None}, now=BoardNow("none")
        ),
    }
    for saved in page.SAVED:
        cases[f"main_saved_{saved}"] = main(example(), saved=saved, board="Disneypi", updates=view())
    cases["main_saved_unknown_is_silent"] = main(example(), saved="bogus")
    for started in ("started", "busy", "failed"):
        cases[f"main_update_{started}"] = main(example(), updates=view(), started=started)
    cases["main_update_started_while_running"] = main(
        example(),
        updates=view(
            running=True,
            status="Installing",
            step=1,
            to={"ref": "develop-beta", "sha": "d" * 40, "version": "2.2.0-beta"},
        ),
        started="started",
    )
    return cases


def card_cases():
    running = view(
        running=True,
        status="Installing <the> new version",
        step=2,
        to={"ref": "v2.2.0", "sha": "d" * 40, "version": "2.2.0", "changes": CHANGES[:2]},
    )
    cases = {
        "updates_idle": lambda: updates_card(view()),
        "updates_running": lambda: updates_card(running),
        "updates_running_rollback": lambda: updates_card(view(running=True, status="Rolling back", to={})),
        "updates_running_no_ref": lambda: updates_card(view(running=True, status=None, to={"sha": "e" * 7})),
        "updates_unfinished": lambda: updates_card(view(phase="switched")),
        "updates_rollback_failed": lambda: updates_card(view(phase="rollback_failed")),
        "updates_no_branch": lambda: updates_card(view(branch=None)),
        "updates_full": lambda: updates_card(full_updates()),
        "updates_busy": lambda: updates_card(view(), "busy"),
        "updates_failed": lambda: updates_card(view(), "failed"),
        "updates_started": lambda: updates_card(view(), "started"),
        "updates_old_beta_point": lambda: updates_card(
            view(phase="updated", **{"from": {"version": "2.0.9", "sha": "f" * 40, "branch": "develop-beta"}})
        ),
        "updates_old_release_point": lambda: updates_card(
            view(phase="updated", **{"from": {"version": "2.0.9", "sha": "f" * 40, "branch": None}})
        ),
        "updates_beta_past_release": lambda: updates_card(
            view(version="2.1.5-beta-2-gaaaaaaa", installed_channel="beta")
        ),
        "updates_outcome_rollback": lambda: updates_card(
            view(outcome={"command": "rollback", "ok": False, "at": 1_699_990_000, "message": "a1b2c3d went wrong"})
        ),
        "updates_outcome_recover": lambda: updates_card(
            view(outcome={"command": "recover", "ok": True, "at": "soon", "message": ""})
        ),
        "check_pending": lambda: check_result(view(auto_check=True, channel="beta")),
        "check_pending_releases": lambda: check_result(view(auto_check=True)),
        "check_nothing": lambda: check_result(view()),
    }
    for n, (result, extra) in enumerate(
        (
            ("would_update", {"changes": CHANGES[:3], "version": "9.0"}),
            ("would_update", {}),
            ("current", {}),
            ("waiting", {}),
            ("waiting", {"runs": []}),
            ("waiting", {"runs": [["test (3.11)", "running"], ["test (3.13)", "passed"]]}),
            ("waiting", {"runs": [["test (3.11)", "failed"], ["lint", "passed"]]}),
            ("waiting", {"runs": [["a", "passed"], ["b", "passed"], ["c", "running"]]}),
            ("waiting", {"runs": [["a", "running"]]}),
            ("error", {}),
        )
    ):
        for channel in ("releases", "beta"):
            name = f"check_{n}_{result}_{channel}"
            check = {**FOUND, "channel": channel, "result": result, "message": "message <here>", **extra}
            cases[name] = lambda check=check, channel=channel: check_result(view(check=check, channel=channel))
    return cases


def sign_in_cases():
    return {
        "pin_plain": lambda: pin_page(),
        "pin_shown": lambda: pin_page(shown_s=120),
        "pin_shown_long": lambda: pin_page(shown_s=300, board="Disney<pi>"),
        "pin_wrong": lambda: pin_page(wrong=True, board="Disneypi"),
        "pin_phone": lambda: pin_page(phone=True),
        **{f"pin_sent_{s}": (lambda s=s: pin_page(phone=True, sent=s)) for s in page.SENT},
        "pin_signed_out": lambda: pin_page(signed_out=True),
        "message_not_found": lambda: message_page("Not found", "There's nothing at this address."),
        "message_not_allowed": lambda: message_page("Not <allowed>", "That form came from another site."),
        "notices_none": lambda: notices(),
        "notices_problems": lambda: notices(["One <1>", "Two"]),
        **{f"notices_{s}": (lambda s=s: notices(saved=s)) for s in page.SAVED},
        "notices_both": lambda: notices(["Bad"], "restarted"),
    }


def surprise_cases():
    data = {
        "enabled": True,
        "characters": {
            "tron": {"on": False},
            "genie": {"chance": 1.5},
            "falcon": {"ride_chance": 25, "chance": 1, "rides": ["Space Mountain"]},
        },
    }
    rides = {"Magic Kingdom": ["Space Mountain", "Haunted <Mansion>"], "EPCOT": ["Test Track"]}
    return {
        "surprises_empty": lambda: surprises_page.surprises_page({}),
        "surprises_saved_data": lambda: surprises_page.surprises_page(data, board="Disneypi", rides=rides),
        "surprises_problems": lambda: surprises_page.surprises_page(
            data, problems=["Bad <chance>"], board="Disneypi", hotspot="Disneypi-setup", rides=rides
        ),
        **{
            f"surprises_saved_{s}": (lambda s=s: surprises_page.surprises_page(data, saved=s, rides=rides))
            for s in page.SAVED
        },
        "surprises_import_refused": lambda: surprises_page.surprises_page(
            {}, ["Not JSON <x>"], rides=rides, imported=False
        ),
        "surprises_import_ok": lambda: surprises_page.surprises_page(data, rides=rides, imported=[]),
        "surprises_import_skipped": lambda: surprises_page.surprises_page(
            data, rides=rides, imported=["old_one", "older <two>"]
        ),
    }


def all_cases():
    return {**page_cases(), **card_cases(), **sign_in_cases(), **surprise_cases()}


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    """Update times print on the board's clock: pin the zone (restored after)."""
    if not hasattr(time, "tzset"):
        pytest.skip("needs time.tzset")
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def marked(html):
    """html with the stylesheet and scripts (stored once) replaced by markers."""
    return (
        html.replace(page.STYLE, STYLE_MARK)
        .replace(page.SCRIPT, SCRIPT_MARK)
        .replace(surprises_page.SCRIPT, SURPRISES_SCRIPT_MARK)
        .replace(page.FORM_SCRIPT, FORM_SCRIPT_MARK)
    )


def path_of(name):
    return os.path.join(FIXTURES, f"{name}.html")


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


CASES = all_cases()


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_html_is_byte_for_byte_what_it_was(name):
    html = CASES[name]()
    assert isinstance(html, str)
    assert marked(html) == read(path_of(name))


def test_the_stylesheet_and_scripts_are_byte_for_byte_what_they_were():
    assert page.STYLE == read(os.path.join(FIXTURES, "style.css"))
    assert page.SCRIPT == read(os.path.join(FIXTURES, "script.js"))
    assert page.FORM_SCRIPT == read(os.path.join(FIXTURES, "form_script.js"))


def test_every_case_has_a_stored_page_and_none_is_left_over():
    stored = {f[: -len(".html")] for f in os.listdir(FIXTURES) if f.endswith(".html")}
    assert stored == set(CASES)


def test_the_cases_do_not_all_say_the_same_thing():
    assert len({marked(CASES[n]()) for n in CASES}) > len(CASES) * 0.8


def test_the_example_config_is_not_changed_by_drawing_it():
    config = example()
    before = copy.deepcopy(config)
    settings_page(config, CARDS, today=TODAY, panel=PANEL, updates=view())
    assert config == before


def test_regenerate_fixtures_when_asked():
    if os.environ.get("PIN_REGEN") != "1":
        pytest.skip("set PIN_REGEN=1 to rewrite the fixtures")
    os.makedirs(FIXTURES, exist_ok=True)
    for old in os.listdir(FIXTURES):
        os.remove(os.path.join(FIXTURES, old))
    write(os.path.join(FIXTURES, "style.css"), page.STYLE)
    write(os.path.join(FIXTURES, "script.js"), page.SCRIPT)
    write(os.path.join(FIXTURES, "form_script.js"), page.FORM_SCRIPT)
    for name, make in all_cases().items():
        write(path_of(name), marked(make()))
