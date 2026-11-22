"""The settings page's HTML: the form for config.json (fields named as form.apply_form reads
them), the PIN page, and the notices after a save. Everything is inline (styles, icons, a few
lines of script), since a phone on the setup hotspot has no internet to fetch anything from. It
works without JavaScript; the script adds trip rows and the "unsaved changes" state.

This module puts the page together; the pieces live beside it: markup.py (the document shell, fields, notices,
landmark pictures), cards/ (one module per card), page_style.py and page_script.py. It also re-exports every name
the page has always had, so callers and tests keep importing from here.
"""

from html import escape

from settings_page.cards.board_now import _board_now_card
from settings_page.cards.display import _brightness_previews, display_card  # noqa: F401  (re-exported)
from settings_page.cards.live import live_card, phone_card, weather_card
from settings_page.cards.panel import (  # noqa: F401  (re-exported)
    PANEL_SETTINGS,
    ROTATIONS,
    SIZE_SETTINGS,
    _matrix_field,
    _rotation_preview,
    advanced_card,
    panel_blanks,
    panel_card,
)
from settings_page.cards.parks import _park_chip, parks_card  # noqa: F401  (re-exported)
from settings_page.cards.shows import shows_card
from settings_page.cards.sound import sound_card
from settings_page.cards.surprises import surprises_card, testing_card
from settings_page.cards.trips import _countdown_preview, _same_trip, _trip, trips_card  # noqa: F401  (re-exported)
from settings_page.cards.updates import (  # noqa: F401  (re-exported)
    CHANGES_SHOWN,
    _beta_name,
    _changes,
    _found_name,
    _installed_name,
    _post,
    _pr_link,
    _run_name,
    _sentence,
    _short,
    _steps,
    _waiting,
    _when,
    check_result,
    updates_card,
)
from settings_page.markup import (  # noqa: F401  (re-exported)
    CASTLE_KEY,
    ICON,
    ICON_512,
    ICONS,
    LANDMARK_INDEX,
    SAVED,
    SENT,
    STATIC_DIR,
    TOUCH_ICON,
    _attr,
    _field,
    _hint,
    _input,
    _json_for_script,
    _key_field,
    _led,
    _notice,
    _options,
    _section,
    _switch,
    _switch_input,
    _topbar,
    debug,
    document,
    icon,
    landmark_src,
    landmarks,
    message_page,
    notices,
    wordmark,
)
from settings_page.page_script import FORM_SCRIPT, SCRIPT
from settings_page.page_style import STYLE  # noqa: F401  (re-exported)

SECTIONS = (  # id, nav title, icon
    ("updates", "Updates", "refresh"),
    ("live", "Live updates", "live"),
    ("weather", "Weather", "cloud"),
    ("phone", "PIN by Pushover", "phone"),
    ("parks", "Parks", "pin"),
    ("trips", "Trip countdown", "calendar"),
    ("sound", "Sound", "sound"),
    ("panel", "Panel", "board"),
    ("display", "Display", "sun"),
    ("shows", "Fireworks shows", "sparkle"),
    ("surprises", "Surprise characters", "sparkle"),
    ("testing", "Testing", "flask"),
    ("advanced", "Advanced", "sliders"),
)


def _top(problems, saved, hotspot, note):
    """The notices above the form: what a save said, problems, setup mode, why config.json couldn't be read."""
    return (
        f"{notices(problems, saved)}"
        + (
            _notice(
                "warn",
                f"<strong>Setup mode.</strong> Anyone who joins <strong>{escape(hotspot)}</strong> can "
                f"open this page while the board is in setup.",
            )
            if hotspot
            else ""
        )
        + (_notice("warn", escape(note)) if note else "")
    )


def _toc():
    return "".join(
        f'<a href="{"/surprises" if sid == "surprises" else "#" + sid}">{icon(glyph)}{escape(title)}</a>'
        for sid, title, glyph in SECTIONS
    )


def _before_the_form(now, updates, started):
    """First, and outside the settings form: its buttons post forms of their own."""
    if not (updates or now):
        return ""
    return (
        f'<div class="stack before">{_board_now_card(now) if now else ""}'
        f"{updates_card(updates, started) if updates else ''}</div>"
    )


def _cards(config, sound_cards, park_names, panel, today):
    """The cards inside the settings form, in order."""
    chosen_model, blanks = panel_blanks(config, panel)
    return "".join(
        (
            live_card(config),
            weather_card(config),
            phone_card(config),
            parks_card(config, park_names),
            trips_card(config, today),
            sound_card(config, sound_cards),
            panel_card(config, panel, chosen_model, blanks),
            display_card(config, blanks),
            shows_card(config),
            surprises_card(),
            testing_card(config),
            advanced_card(config, blanks),
        )
    )


def settings_page(  # noqa: PLR0913
    config,
    sound_cards,
    hotspot=None,
    problems=(),
    saved=None,
    board=None,
    note=None,
    park_names=(),
    panel=None,
    updates=None,
    started=None,
    now=None,
    today=None,
):
    """The settings form, filled from config. sound_cards: ALSA device names for the dropdown.
    note: why config.json couldn't be read, if it couldn't. park_names: [(name, destination)]
    for the park picker's suggestions, [] when the list hasn't loaded. panel: form.PanelChoices,
    the Pi model and Panel size dropdowns and what blank fields say; None leaves them off.
    updates: updates.Updates.view(), for the Updates card (None leaves it off); started: how
    starting an update or rollback went, one of updates.STARTS. now: board_status.BoardNow, for the
    "On the board now" card (None leaves it off). today: the date the countdown preview counts from."""
    mode = ("warn", "Setup mode") if hotspot else ("good", "Signed in")
    body = (
        _topbar(board, mode, sign_out=not hotspot)  # on the hotspot there's no PIN session to end
        + f'<div class="shell"><nav class="toc" aria-label="Sections">{_toc()}</nav><main>'
        + '<div class="page-head"><h1>Settings</h1><p>Changes are checked, saved to the board\'s config.json, '
        "and the app restarts to use them.</p></div>"
        + _top(problems, saved, hotspot, note)
        + _before_the_form(now, updates, started)
        + f'<form method="post" action="/save" id="settings"><div class="stack">'
        f"{_cards(config, sound_cards, park_names, panel, today)}</div>"
        + '<div class="savebar"><div class="savebar-in"><div class="status" id="save-status"><span class="dot"></span>'
        "<span>Saved keys stay as they are unless you replace them</span></div>"
        f'<button type="submit" class="primary" id="save">{icon("save")}<span>Save and restart</span></button>'
        "</div></div></form></main></div>"
    )
    return document("Board settings", body, SCRIPT)


def pin_page(shown_s=None, wrong=False, board=None, phone=False, sent=None, signed_out=False):
    """The sign-in page on the home network. shown_s: a PIN is on the board for this long.
    phone: offer to send it by Pushover; sent: how that went, one of SENT. signed_out: just signed out."""
    status = ""
    if signed_out:
        status = _notice("good", "Signed out. This browser needs a new PIN to change settings.")
    elif wrong:
        status = _notice("bad", "That isn't the PIN on the board. Try again, or ask for a new one.", "alert")
    elif sent == "sent":
        status = _notice("good", "The PIN is on its way to your phone. It's on the board too.")
    elif sent == "wait":
        status = _notice("warn", "A PIN went out less than a minute ago: check your phone, or try again in a minute.")
    elif sent == "used":
        status = _notice("bad", "That PIN is out of tries. Ask for a new one in a couple of minutes.", "alert")
    elif sent == "failed":
        status = _notice("bad", "Couldn't send the PIN (the board's log says why), but it's on the board.", "alert")
    elif shown_s:
        status = _notice(
            "good",
            f"The PIN is on the board for the next {max(1, round(shown_s / 60))} minute{'s' if shown_s > 90 else ''}.",
        )
    body = (
        _topbar(board) + f'<div class="center"><div class="card auth signin"><div class="auth-hero">'
        f'<img src="{ICON}" alt="" width="76" height="76"><div>{wordmark()}</div></div>'
        "<h1>Sign in to this board</h1><p>To change this board's settings, type in the PIN it shows.</p>"
        + status
        + '<div class="step"><span class="step-n">1</span><div class="step-body"><strong>Show a PIN</strong>'
        f"<p>It appears on the LED board for two minutes{' and can go to your phone' if phone else ''}.</p>"
        f'<div class="buttons"><form method="post" action="/pin/show"><button type="submit" class="secondary">'
        f"{icon('board')}Show a PIN on the board</button></form>"
        + (
            f'<form method="post" action="/pin/send"><button type="submit" class="secondary">{icon("phone")}'
            "Send the PIN to my phone</button></form>"
            if phone
            else ""
        )
        + "</div></div></div>"
        + '<div class="step"><span class="step-n">2</span><div class="step-body"><label for="pin"><strong>Type it in'
        "</strong></label><p>You stay signed in on this browser for an hour.</p>"
        '<form method="post" action="/pin"><input type="text" id="pin" name="pin" class="pin" inputmode="numeric" '
        'autocomplete="one-time-code" pattern="[0-9]*" maxlength="8" required autofocus aria-label="PIN">'
        '<button type="submit" class="primary block">Sign in</button></form></div></div>' + "</div></div>"
    )
    return document("Sign in · Board settings", body, FORM_SCRIPT)
