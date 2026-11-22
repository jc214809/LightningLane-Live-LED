"""What every page of the settings service is built from: the document shell, the top bar, notices, the landmark
pictures and the field, switch and card helpers. settings_page/page.py re-exports all of it."""
import functools
import json
import os
from html import escape

from settings_page.form import masked
from settings_page.page_style import STYLE
from utils import debug

# The page's pictures, served by server.py from settings_page/static (no internet on the setup hotspot):
# the logo and its PNGs for phones, and the board's park landmarks, rendered by tools/build_settings_art.py.
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ICON, TOUCH_ICON, ICON_512 = "/static/icon.svg", "/static/apple-touch-icon.png", "/static/icon-512.png"
LANDMARK_INDEX = "landmarks.json"
CASTLE_KEY = "magic kingdom"  # the castle stands in for the board in the brightness, rotation and show previews

# What a save says, by Settings.restart_app's outcome.
SAVED = ("restarted", "saved", "failed", "volume", "volume_failed")
SENT = ("sent", "wait", "used", "failed")  # pins.PinGate.send_pin's outcomes

ICONS = {
    "bolt": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "live": '<circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49'
            'M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "sound": '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41'
           'M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
    "sparkle": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>'
               '<path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "flask": '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3M7 15h10"/>',
    "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "alert": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "left": '<path d="m15 18-6-6 6-6"/>',
    "board": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M6 9h.01M10 9h.01M14 9h.01M18 9h.01'
             'M6 13h.01M10 13h.01M14 13h.01M18 13h.01"/>',
    "cloud": '<path d="M17.5 19H7a5 5 0 1 1 1.02-9.9A6 6 0 0 1 19.5 11a4 4 0 0 1-2 8z"/>',
    "phone": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
    "wifi": '<path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"/>',
    "save": '<path d="M20 6 9 17l-5-5"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/>',
    "undo": '<path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-15-6.7L3 13"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


@functools.lru_cache(maxsize=None)
def landmarks(path=None):
    """{park key: "/static/<file>"} from tools/build_settings_art.py's index; {} if it can't be read (logged), so
    the page still works, just without the pictures."""
    path = path or os.path.join(STATIC_DIR, LANDMARK_INDEX)
    try:
        with open(path, encoding="utf-8") as f:
            index = json.load(f)
    except (OSError, ValueError) as e:
        debug.warning(f"Settings page: no landmark pictures ({path}: {e})")
        return {}
    if not isinstance(index, dict):
        debug.warning(f"Settings page: no landmark pictures ({path} isn't a key-to-file map)")
        return {}
    return {str(k): f"/static/{v}" for k, v in index.items() if isinstance(v, str) and "/" not in v}


def landmark_src(park):
    """The landmark picture the board plays before this park, matched loosely on its name as
    display/landmarks/screen.py landmark_for does, or None (the board shows its title alone)."""
    name = (park or "").lower()
    return next((src for key, src in landmarks().items() if key in name), None)


def document(title, body, script=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta name="robots" content="noindex"><meta name="theme-color" content="#0e1440">'
            f'<link rel="icon" href="{ICON}" type="image/svg+xml">'
            f'<link rel="icon" href="{ICON_512}" type="image/png" sizes="512x512">'
            f'<link rel="apple-touch-icon" href="{TOUCH_ICON}">'
            f'<title>{escape(title)}</title><style>{STYLE}</style></head>'
            f'<body>{body}{f"<script>{script}</script>" if script else ""}</body></html>')


def wordmark():
    return '<div class="brand-name">LightningLane</div><div class="brand-sub">LED</div>'


def _topbar(board=None, mode=None, sign_out=False):
    """mode: ("warn" or "good", text) for the badge on the right. sign_out: a Sign out button after it."""
    chips = f'<span class="chip board">{icon("board")}{escape(board)}</span>' if board else ""
    if mode:
        kind, text = mode
        chips += f'<span class="chip {kind}">{icon("wifi" if kind == "warn" else "lock")}{escape(text)}</span>'
    if sign_out:
        chips += '<form method="post" action="/signout"><button type="submit" class="ghost">Sign out</button></form>'
    return (f'<header class="topbar"><div class="topbar-in"><div class="brand"><span class="mark">'
            f'<img src="{ICON}" alt="" width="38" height="38"></span><div>{wordmark()}</div></div>'
            f'<div class="top-meta">{chips}</div></div></header>')


def _led(src, alt="", extra=""):
    """A picture of the board's screen, on the panel's black."""
    return f'<span class="led"><img src="{src}" alt="{_attr(alt)}"{extra}></span>'


def message_page(title, text):
    """A plain page for errors (not found, not allowed)."""
    body = (f'{_topbar()}<div class="center"><div class="card auth"><div class="auth-icon">{icon("info")}</div>'
            f'<h1>{escape(title)}</h1><p>{escape(text)}</p><a class="btn secondary" href="/">Go to settings</a></div></div>')
    return document(title, body)


def _notice(kind, html, role="status"):
    glyph = {"good": "check", "bad": "alert", "warn": "info", "info": "info", "new": "refresh"}[kind]
    return f'<div class="notice {kind}" role="{role}">{icon(glyph)}<div>{html}</div></div>'


def notices(problems=(), saved=None):
    """saved: None (nothing saved), or one of SAVED."""
    html = ""
    if problems:
        items = "".join(f"<li>{escape(p)}</li>" for p in problems)
        html += _notice("bad", f"<strong>Not saved.</strong> Fix these and save again:<ul>{items}</ul>", "alert")
    if saved == "restarted":
        html += _notice("good", "<strong>Saved.</strong> The board is restarting with the new settings.")
    elif saved == "saved":
        html += _notice("good", "<strong>Saved.</strong> Restart the app for the new settings.")
    elif saved == "volume":
        html += _notice("good", "<strong>Saved.</strong> The speaker is at the new volume now; no restart needed.")
    elif saved == "volume_failed":
        html += _notice("bad", "<strong>Saved, but the speaker didn't change.</strong> The board's log says why; "
                               "the next show tries again.", "alert")
    elif saved == "failed":
        html += _notice("bad", "<strong>Saved, but the app didn't restart.</strong> Unplug the board and plug it "
                               "back in to use the new settings.", "alert")
    return html


def _attr(value):
    return escape(str(value), quote=True)


def _hint(text):
    return f'<p class="hint">{escape(text)}</p>' if text else ""


def _field(name, label, control, hint="", badge="", inline=False):
    """A labelled row: label and hint on the left, the control on the right (stacked on a phone)."""
    return (f'<div class="field{" inline" if inline else ""}"><div class="field-label"><div class="label-row">'
            f'<label for="{name}">{escape(label)}</label>{badge}</div>{_hint(hint)}</div>'
            f'<div class="field-control">{control}</div></div>')


def _input(name, value="", kind="text", extra=""):
    return f'<input type="{kind}" id="{name}" name="{name}" value="{_attr(value)}"{extra}>'


def _options(name, options, chosen, extra=""):
    """options: (value, text) pairs."""
    opts = "".join(f'<option value="{_attr(v)}"{" selected" if v == chosen else ""}>{escape(t)}</option>'
                   for v, t in options)
    return f'<select id="{name}" name="{name}"{extra}>{opts}</select>'


def _switch_input(name, on, extra=""):
    return f'<input type="checkbox" class="switch" role="switch" id="{name}" name="{name}"{" checked" if on else ""}{extra}>'


def _switch(name, label, on, hint=""):
    return _field(name, label, _switch_input(name, on), hint, inline=True)


def _key_field(name, label, saved, hint):
    shown = masked(saved)
    badge = (f'<span class="pill ok">{icon("check")}Saved {escape(shown)}</span>' if shown
             else '<span class="pill">Not set</span>')
    control = _input(name, kind="password", extra=f' class="mono" autocomplete="off" spellcheck="false" '
                     f'placeholder="{"Paste a new key to replace it" if shown else "Paste your key"}"')
    return _field(name, label, control, hint + (" Leave blank to keep the saved one." if shown else ""), badge)


def _section(sid, title, description, body, glyph):
    return (f'<section class="card" id="{sid}" aria-labelledby="{sid}-title"><div class="card-head">'
            f'<span class="card-icon">{icon(glyph)}</span><div><h2 id="{sid}-title">{escape(title)}</h2>'
            f'<p>{escape(description)}</p></div></div><div class="card-body">{body}</div></section>')


def _json_for_script(value):
    """JSON to put inside a <script>: a "<" escaped, so "</script>" in a value can't end it."""
    return json.dumps(value).replace("<", "\\u003c")


def sub_dict(config, key):
    """config[key] if it is a settings object, else {}: a hand-edited config.json may hold anything."""
    return config.get(key) if isinstance(config.get(key), dict) else {}
