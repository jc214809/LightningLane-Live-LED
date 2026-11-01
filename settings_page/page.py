"""The settings page's HTML: the form for config.json (fields named as form.apply_form reads
them), the PIN page, and the notices after a save. Everything is inline (styles, icons, a few
lines of script), since a phone on the setup hotspot has no internet to fetch anything from. It
works without JavaScript; the script adds trip rows and the "unsaved changes" state.
"""
from html import escape

import cli
from settings_page.form import BRIGHTNESS, WDW_PARKS, masked, show_names, surprise_names, trip_rows
from utils.config import SHOW_VERSIONS, WS_PROTOCOLS

# What a save says, by Settings.restart_app's outcome.
SAVED = ("restarted", "saved", "failed")

STYLE = """
:root {
  --bg: #f4f5f7; --surface: #fff; --surface-2: #f8f9fb; --border: #e3e6eb; --border-strong: #cfd4dc;
  --text: #111827; --text-2: #4b5563; --text-3: #6b7280;
  --accent: #2f54eb; --accent-hover: #2546c9; --accent-soft: #e8edff; --on-accent: #fff;
  --good: #067647; --good-bg: #ecfdf3; --good-line: #abefc6;
  --bad: #b42318; --bad-bg: #fef3f2; --bad-line: #fecdca;
  --warn: #93370d; --warn-bg: #fffaeb; --warn-line: #fedf89;
  --shadow: 0 1px 2px rgba(16, 24, 40, .05), 0 1px 3px rgba(16, 24, 40, .06);
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) { :root {
  --bg: #0b0d12; --surface: #141821; --surface-2: #1a1f2a; --border: #262c38; --border-strong: #3a4252;
  --text: #eef1f6; --text-2: #b4bccb; --text-3: #8b94a5;
  --accent: #6b8cff; --accent-hover: #8aa4ff; --accent-soft: #1c2440; --on-accent: #0b0d12;
  --good: #75e0a7; --good-bg: #0c2a1c; --good-line: #14532d;
  --bad: #fda29b; --bad-bg: #2d1412; --bad-line: #5c1f1a;
  --warn: #fec84b; --warn-bg: #2b2110; --warn-line: #5c4313;
  --shadow: 0 1px 2px rgba(0, 0, 0, .4);
} }
* { box-sizing: border-box; }
html { scroll-padding-top: 84px; }
body { margin: 0; background: var(--bg); color: var(--text); -webkit-font-smoothing: antialiased;
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2;
  stroke-linecap: round; stroke-linejoin: round; flex: none; }
h1, h2, h3, p { margin: 0; }
a { color: var(--accent); }

/* Top bar */
.topbar { position: sticky; top: 0; z-index: 20; background: var(--surface); border-bottom: 1px solid var(--border); }
.topbar-in { max-width: 1080px; margin: 0 auto; padding: 0 16px; height: 60px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
.mark { width: 34px; height: 34px; border-radius: 9px; display: grid; place-items: center; color: #fff;
  background: linear-gradient(135deg, #2f54eb, #7c3aed); box-shadow: var(--shadow); flex: none; }
.mark svg { width: 18px; height: 18px; fill: #fde047; stroke: #fde047; }
.brand-name { font-weight: 650; letter-spacing: -.01em; white-space: nowrap; }
.brand-sub { color: var(--text-3); font-size: 12.5px; }
.top-meta { display: flex; align-items: center; gap: 8px; }
.chip { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border-radius: 999px;
  border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); font-size: 13px;
  font-weight: 500; white-space: nowrap; }
.chip svg { width: 14px; height: 14px; }
.chip.warn { color: var(--warn); background: var(--warn-bg); border-color: var(--warn-line); }
.chip.good { color: var(--good); background: var(--good-bg); border-color: var(--good-line); }
@media (max-width: 520px) { .brand-sub, .chip.board { display: none; } }

/* Layout */
.shell { max-width: 1080px; margin: 0 auto; padding: 28px 16px 128px; display: grid; gap: 32px; }
@media (min-width: 960px) { .shell { grid-template-columns: 200px minmax(0, 1fr); } }
.toc { display: none; }
@media (min-width: 960px) {
  .toc { display: block; position: sticky; top: 88px; align-self: start; }
  .toc a { display: flex; align-items: center; gap: 10px; padding: 7px 10px; border-radius: 8px;
    color: var(--text-2); text-decoration: none; font-weight: 500; font-size: 14px; }
  .toc a:hover { background: var(--surface); color: var(--text); }
  .toc a.on { background: var(--accent-soft); color: var(--accent); }
  .toc svg { width: 16px; height: 16px; }
}
.page-head { margin-bottom: 20px; }
.page-head h1 { font-size: 24px; font-weight: 700; letter-spacing: -.02em; }
.page-head p { color: var(--text-2); margin-top: 4px; }
.stack { display: grid; gap: 20px; }

/* Cards */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; box-shadow: var(--shadow); }
.card-head { display: flex; gap: 14px; align-items: flex-start; padding: 18px 20px; border-bottom: 1px solid var(--border); }
.card-icon { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center;
  background: var(--accent-soft); color: var(--accent); flex: none; }
.card-head h2 { font-size: 16px; font-weight: 650; letter-spacing: -.01em; }
.card-head p { color: var(--text-3); font-size: 13.5px; margin-top: 2px; }
.card-body { padding: 4px 20px 18px; }
details.card > summary { list-style: none; cursor: pointer; border-bottom: 0; border-radius: 14px; }
details.card > summary::-webkit-details-marker { display: none; }
details.card[open] > summary { border-bottom: 1px solid var(--border); border-radius: 14px 14px 0 0; }
.chev { margin-left: auto; align-self: center; color: var(--text-3); transition: transform .15s; }
details[open] .chev { transform: rotate(180deg); }
.card-body h3 { font-size: 12px; font-weight: 650; text-transform: uppercase; letter-spacing: .06em;
  color: var(--text-3); margin: 22px 0 4px; }

/* Fields */
.field { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 6px 28px;
  padding: 16px 0; border-top: 1px solid var(--border); align-items: start; }
.card-body > .field:first-child, .card-body > h3 + .field, .notice + .field { border-top: 0; }
.field.inline { grid-template-columns: minmax(0, 1fr) auto; align-items: center; }
.field-label label, .label { font-weight: 550; display: inline-block; }
.hint { color: var(--text-3); font-size: 13px; margin-top: 3px; }
.label-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
@media (max-width: 640px) { .field { grid-template-columns: 1fr; } .field.inline { grid-template-columns: 1fr auto; } }
input[type=text], input[type=password], input[type=number], input[type=date], input[type=time], select {
  width: 100%; height: 40px; font: inherit; color: var(--text); background: var(--surface);
  padding: 0 12px; border: 1px solid var(--border-strong); border-radius: 8px;
  transition: border-color .15s, box-shadow .15s; }
input::placeholder { color: var(--text-3); }
select { appearance: none; padding-right: 34px; background-repeat: no-repeat; background-position: right 11px center;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%238b94a5' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E"); }
input:hover, select:hover { border-color: var(--text-3); }
input:focus, select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; }
.pair { display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center; }
.pair span { color: var(--text-3); font-size: 13px; }
.below { margin-top: 8px; }
.pill { display: inline-flex; align-items: center; gap: 4px; padding: 1px 8px; border-radius: 999px; font-size: 12px;
  font-weight: 550; background: var(--surface-2); color: var(--text-3); border: 1px solid var(--border); }
.pill.ok { color: var(--good); background: var(--good-bg); border-color: var(--good-line); }
.pill svg { width: 12px; height: 12px; }

/* Switches */
.switch { appearance: none; margin: 0; width: 42px; height: 24px; border-radius: 999px; position: relative;
  background: var(--border-strong); cursor: pointer; transition: background .15s; flex: none; }
.switch::after { content: ""; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%;
  background: #fff; box-shadow: 0 1px 2px rgba(0, 0, 0, .3); transition: transform .15s; }
.switch:checked { background: var(--accent); }
.switch:checked::after { transform: translateX(18px); }
.switch:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--accent-soft), 0 0 0 1px var(--accent); }

/* Park chips, numbered in the order the board shows them */
.park-chips { list-style: none; margin: 0; padding: 16px 0 4px; display: flex; flex-wrap: wrap; gap: 8px;
  counter-reset: park; }
.park-chip { counter-increment: park; display: inline-flex; align-items: center; gap: 6px; height: 36px;
  padding: 0 4px 0 6px; border-radius: 999px; border: 1px solid var(--accent); background: var(--accent-soft);
  color: var(--text); font-weight: 550; max-width: 100%; }
.park-chip::before { content: counter(park); width: 22px; height: 22px; border-radius: 50%; display: grid;
  place-items: center; flex: none; background: var(--accent); color: var(--on-accent); font-size: 12px; font-weight: 650; }
.park-chip.unknown { border-color: var(--bad-line); background: var(--bad-bg); color: var(--bad); }
.park-chip.unknown::before { background: var(--bad); }
.park-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
/* The X ticks the park's remove box, as a trip's does: gone from the page, and from config.json on save. */
.park-chip:has(.chip-x input:checked) { display: none; }
.chip-btn, .chip-x { position: relative; width: 28px; height: 28px; padding: 0; border-radius: 50%; display: grid;
  place-items: center; color: var(--text-3); background: transparent; cursor: pointer; flex: none; }
.chip-btn:hover { color: var(--accent); background: var(--surface); }
.chip-x:hover { color: var(--bad); background: var(--surface); }
.chip-btn svg, .chip-x svg { width: 15px; height: 15px; }
.chip-x input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.chip-x:has(input:focus-visible) { box-shadow: 0 0 0 3px var(--accent-soft), 0 0 0 1px var(--accent); }
.park-chip:first-child .chip-btn { display: none; }
.add-row { display: flex; gap: 8px; }
.add-row input { flex: 1; min-width: 0; }
.field-error { color: var(--bad); font-size: 13px; margin-top: 6px; }

/* Trips */
.schedule { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; padding: 4px 0 8px; }
.schedule-wrap[hidden] { display: none; }
.schedule-note { margin: 0 0 10px; }
@media (max-width: 640px) { .schedule { grid-template-columns: 1fr 1fr; } }
.trips { display: grid; gap: 10px; padding-top: 16px; }
.trip { position: relative; display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px; align-items: end; padding: 14px 44px 14px 14px; border: 1px solid var(--border); border-radius: 10px;
  background: var(--surface-2); }
/* The X ticks the trip's remove box; a removed trip is gone from the page, and from config.json on save. */
.trip:has(.trip-x input:checked) { display: none; }
@media (max-width: 640px) { .trip { grid-template-columns: 1fr 1fr; } .trip .wide { grid-column: 1 / -1; } }
.mini { display: block; font-size: 12.5px; font-weight: 550; color: var(--text-2); margin-bottom: 5px; }
.trip-x { position: absolute; top: 8px; right: 8px; width: 28px; height: 28px; border-radius: 8px; display: grid;
  place-items: center; color: var(--text-3); cursor: pointer; transition: background .15s, color .15s; }
.trip-x:hover { color: var(--bad); background: var(--bad-bg); }
.trip-x input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.trip-x svg { width: 16px; height: 16px; }
.trip-x:has(input:focus-visible) { box-shadow: 0 0 0 3px var(--accent-soft), 0 0 0 1px var(--accent); }

/* Shows */
.shows { display: grid; padding-top: 6px; }
.show { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px 24px; align-items: center;
  padding: 14px 0; border-top: 1px solid var(--border); }
.show:first-child { border-top: 0; }
.show-name { font-weight: 550; }
.show-ctl { display: flex; align-items: center; gap: 22px; }
.show-ctl select { width: 120px; }
.show-ctl label { display: flex; flex-direction: column; align-items: flex-start; gap: 5px; }
.show-ctl label .mini { margin: 0; }
@media (max-width: 640px) { .show { grid-template-columns: 1fr; } }

/* Buttons */
button, .btn { font: inherit; font-weight: 600; display: inline-flex; align-items: center; justify-content: center;
  gap: 8px; height: 40px; padding: 0 16px; border-radius: 9px; cursor: pointer; border: 1px solid transparent;
  transition: background .15s, border-color .15s; }
.primary { background: var(--accent); color: var(--on-accent); box-shadow: var(--shadow); }
.primary:hover { background: var(--accent-hover); }
.primary:disabled { opacity: .7; cursor: progress; }
.secondary { background: var(--surface); color: var(--text); border-color: var(--border-strong); box-shadow: var(--shadow); }
.secondary:hover { background: var(--surface-2); }
.ghost { background: transparent; color: var(--accent); padding: 0 10px; }
.ghost:hover { background: var(--accent-soft); }
button:focus-visible, summary:focus-visible, a:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--accent-soft), 0 0 0 1px var(--accent); }
.block { width: 100%; }

/* Notices */
.notice { display: flex; gap: 12px; align-items: flex-start; padding: 12px 14px; border-radius: 10px;
  border: 1px solid; margin-bottom: 16px; font-size: 14px; }
.notice svg { margin-top: 1px; }
.notice ul { margin: 4px 0 0; padding-left: 18px; }
.notice.good { color: var(--good); background: var(--good-bg); border-color: var(--good-line); }
.notice.bad { color: var(--bad); background: var(--bad-bg); border-color: var(--bad-line); }
.notice.warn { color: var(--warn); background: var(--warn-bg); border-color: var(--warn-line); }
.notice.info { color: var(--text-2); background: var(--surface-2); border-color: var(--border); }
.notice.info svg { color: var(--accent); }
.card-body > .notice { margin: 16px 0 0; }

/* Save bar */
.savebar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; border-top: 1px solid var(--border);
  background: color-mix(in srgb, var(--surface) 90%, transparent); backdrop-filter: saturate(1.4) blur(10px); }
.savebar-in { max-width: 1080px; margin: 0 auto; padding: 12px 16px; display: flex; align-items: center;
  justify-content: space-between; gap: 16px; }
.status { display: flex; align-items: center; gap: 8px; color: var(--text-3); font-size: 13.5px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--good); flex: none; }
.status.dirty { color: var(--text); font-weight: 550; }
.status.dirty .dot { background: #f79009; }

/* Sign-in and message pages */
.center { min-height: calc(100vh - 60px); display: grid; place-items: center; padding: 32px 16px; }
.auth { width: 100%; max-width: 420px; padding: 28px; }
.auth-icon { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; margin-bottom: 18px;
  background: var(--accent-soft); color: var(--accent); }
.auth-icon svg { width: 24px; height: 24px; }
.auth h1 { font-size: 21px; font-weight: 700; letter-spacing: -.02em; }
.auth > p { color: var(--text-2); margin: 6px 0 22px; }
.step { display: flex; gap: 12px; padding: 16px 0; border-top: 1px solid var(--border); }
.step-n { width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; flex: none;
  background: var(--surface-2); border: 1px solid var(--border-strong); font-size: 12.5px; font-weight: 650; color: var(--text-2); }
.step-body { flex: 1; min-width: 0; }
.step-body p { color: var(--text-3); font-size: 13.5px; margin: 2px 0 12px; }
input.pin { height: 56px; text-align: center; font-size: 26px; font-weight: 650; letter-spacing: .5em;
  padding-left: .5em; font-variant-numeric: tabular-nums; margin-bottom: 12px; }
"""

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
    "wifi": '<path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"/>',
    "save": '<path d="M20 6 9 17l-5-5"/>',
}

# Proper names for the surprise dropdown, where title case gets them wrong; the rest are title-cased.
CHARACTER_NAMES = {
    "tink": "Tinker Bell", "buzz": "Buzz Lightyear", "ralph": "Wreck-It Ralph", "slinky": "Slinky Dog",
    "slinky_wrap": "Slinky Dog (wrap)", "walle": "WALL-E", "walle_side": "WALL-E (side)", "army_men": "Green Army Men",
    "falcon": "Millennium Falcon", "mike": "Mike Wazowski", "mcqueen": "Lightning McQueen",
    "chip_dale": "Chip 'n' Dale", "chip_dale_swing": "Chip 'n' Dale (swing)", "pooh": "Winnie the Pooh",
    "donald": "Donald Duck", "jack_sally": "Jack & Sally", "grannies": "Bluey: Grannies",
    "keepy_uppy": "Bluey: Keepy Uppy", "saber_duel": "Saber Duel (random)", "saber_duel_obiwan": "Saber Duel Obi-Wan",
    "archer": "Merida (archer)",
}

SECTIONS = (  # id, nav title, icon
    ("live", "Live updates", "live"), ("weather", "Weather", "cloud"), ("parks", "Parks", "pin"), ("trips", "Trip countdown", "calendar"),
    ("sound", "Sound", "sound"), ("display", "Display", "sun"), ("shows", "Fireworks shows", "sparkle"),
    ("testing", "Testing", "flask"), ("advanced", "Advanced", "sliders"),
)

SCRIPT = """
const form = document.getElementById('settings');
const status = document.getElementById('save-status');
form.addEventListener('input', () => {
  form.dataset.dirty = '1';
  status.classList.add('dirty');
  status.querySelector('span:last-child').textContent = 'Unsaved changes';
});
form.addEventListener('submit', () => {
  form.dataset.submitting = '1';
  const button = document.getElementById('save');
  button.disabled = true;
  button.querySelector('span').textContent = 'Saving\\u2026';
});
window.addEventListener('beforeunload', e => {
  if (form.dataset.dirty && !form.dataset.submitting) e.preventDefault();
});
let nextTrip = document.querySelectorAll('#trip-list .trip').length;
document.getElementById('add-trip').addEventListener('click', () => {
  const trips = document.getElementById('trip-list');
  const n = nextTrip++;  // removed trips stay in the page, hidden, so counting them could repeat a number
  const row = document.getElementById('trip-row').content.cloneNode(true);
  row.querySelectorAll('[name]').forEach(el => { el.name = el.name.replace('_N', '_' + n); el.id = el.name; });
  row.querySelectorAll('label[for]').forEach(el => { el.htmlFor = el.htmlFor.replace('_N', '_' + n); });
  trips.appendChild(row);
  trips.querySelector('.trip:last-child input[type=text]').focus();
});
const parkList = document.getElementById('park-chips');
const parkAdd = document.getElementById('park_add');
const parkError = document.getElementById('park-error');
// Lower-case name to the name as listed; empty when the list hasn't loaded, and then names go as typed.
const parkNames = new Map([...document.querySelectorAll('#park-names option')].map(o => [o.value.toLowerCase(), o.value]));
const changed = () => form.dispatchEvent(new Event('input'));
const parkProblem = text => { parkError.textContent = text; parkError.hidden = !text; };
function addPark() {
  const typed = parkAdd.value.trim().replace(/\\s+/g, ' ');
  if (!typed) return;
  const name = parkNames.size ? parkNames.get(typed.toLowerCase()) : typed;
  if (!name) return parkProblem(`"${typed}" isn't a ThemeParks.wiki park: pick one from the list.`);
  const chosen = [...parkList.querySelectorAll('input[name=park]')].map(i => i.value.toLowerCase());
  if (chosen.includes(name.toLowerCase())) return parkProblem(`${name} is already on the board.`);
  const chip = document.getElementById('park-chip').content.cloneNode(true);
  chip.querySelector('input[name=park]').value = name;
  chip.querySelector('input[name=park_remove]').value = name;
  chip.querySelector('.park-name').textContent = name;
  chip.querySelectorAll('[aria-label]').forEach(el => { el.setAttribute('aria-label', el.getAttribute('aria-label') + ' ' + name); });
  parkList.appendChild(chip);
  parkAdd.value = '';
  parkProblem('');
  changed();
}
parkAdd.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); addPark(); } });
// Picking a suggestion adds it straight away; typing waits for Enter or Add, as a typed name can be
// the start of a longer one.
parkAdd.addEventListener('input', e => {
  parkProblem('');
  if (e.inputType === 'insertReplacementText' || e.inputType === undefined) addPark();
});
document.getElementById('park-add-btn').addEventListener('click', addPark);
parkList.addEventListener('change', e => {  // with the script, a removed park leaves the page, so it can be added back
  if (e.target.name === 'park_remove' && e.target.checked) { e.target.closest('.park-chip').remove(); parkAdd.focus(); }
});
parkList.addEventListener('click', e => {
  const move = e.target.closest('.chip-btn');
  if (!move) return;
  const chip = move.closest('.park-chip');
  if (chip.previousElementSibling) { parkList.insertBefore(chip, chip.previousElementSibling); changed(); }
  (chip.querySelector('.chip-btn:not([hidden])') || move).focus();
});
document.querySelectorAll('.js-only').forEach(el => { el.hidden = false; });
const device = document.getElementById('sound_device');
const custom = document.getElementById('custom-device');
const showCustom = () => { custom.hidden = device.value !== 'custom'; };
device.addEventListener('change', showCustom);
showCustom();
const scheduleOn = document.getElementById('brightness_schedule');
const showSchedule = () => { document.getElementById('schedule').hidden = !scheduleOn.checked; };
scheduleOn.addEventListener('change', showSchedule);
showSchedule();
const links = [...document.querySelectorAll('.toc a')];
const spy = new IntersectionObserver(entries => entries.forEach(e => {
  if (e.isIntersecting) links.forEach(a => a.classList.toggle('on', a.hash === '#' + e.target.id));
}), {rootMargin: '-80px 0px -65% 0px'});
document.querySelectorAll('main .card[id]').forEach(s => spy.observe(s));
"""


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def document(title, body, script=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta name="robots" content="noindex"><title>{escape(title)}</title><style>{STYLE}</style></head>'
            f'<body>{body}{f"<script>{script}</script>" if script else ""}</body></html>')


def _topbar(board=None, mode=None):
    """mode: ("warn" or "good", text) for the badge on the right."""
    chips = f'<span class="chip board">{icon("board")}{escape(board)}</span>' if board else ""
    if mode:
        kind, text = mode
        chips += f'<span class="chip {kind}">{icon("wifi" if kind == "warn" else "lock")}{escape(text)}</span>'
    return (f'<header class="topbar"><div class="topbar-in"><div class="brand"><span class="mark">{icon("bolt")}</span>'
            f'<div><div class="brand-name">LightningLane Live LED</div><div class="brand-sub">Board settings</div>'
            f'</div></div><div class="top-meta">{chips}</div></div></header>')


def message_page(title, text):
    """A plain page for errors (not found, not allowed)."""
    body = (f'{_topbar()}<div class="center"><div class="card auth"><div class="auth-icon">{icon("info")}</div>'
            f'<h1>{escape(title)}</h1><p>{escape(text)}</p><a class="btn secondary" href="/">Go to settings</a></div></div>')
    return document(title, body)


def _notice(kind, html, role="status"):
    glyph = {"good": "check", "bad": "alert", "warn": "info", "info": "info"}[kind]
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


def _trip(index, start="", end="", name=""):
    i = index
    name_input = _input(f"trip_name_{i}", name, extra=' placeholder="Spring Break"')
    remove = (f'<label class="trip-x" for="trip_remove_{i}" title="Remove this trip"><input type="checkbox" '
              f'id="trip_remove_{i}" name="trip_remove_{i}" aria-label="Remove this trip">{icon("x")}</label>')
    return (f'<div class="trip"><div class="wide"><label class="mini" for="trip_name_{i}">Name</label>'
            f'{name_input}</div>'
            f'<div><label class="mini" for="trip_start_{i}">Start</label>{_input(f"trip_start_{i}", start, "date")}</div>'
            f'<div><label class="mini" for="trip_end_{i}">End <span class="hint">(optional)</span></label>'
            f'{_input(f"trip_end_{i}", end, "date")}</div>{remove}</div>')


def _park_chip(name, unknown=False):
    """One chosen park: posted as "park" in page order. The X is a checkbox, so removing works
    without the script; the arrow (script only) moves it one place earlier."""
    label = _attr(name)
    title = ' title="Not a ThemeParks.wiki park name"' if unknown else ""
    return (f'<li class="park-chip{" unknown" if unknown else ""}"{title}><input type="hidden" name="park" value="{label}">'
            f'<span class="park-name">{escape(name)}</span>'
            f'<button type="button" class="chip-btn js-only" hidden aria-label="Move earlier: {label}">{icon("left")}</button>'
            f'<label class="chip-x" title="Remove"><input type="checkbox" name="park_remove" value="{label}" '
            f'aria-label="Remove {label}">{icon("x")}</label></li>')


def settings_page(config, sound_cards, hotspot=None, problems=(), saved=None, board=None, note=None, park_names=()):
    """The settings form, filled from config. sound_cards: ALSA device names for the dropdown.
    note: why config.json couldn't be read, if it couldn't. park_names: [(name, destination)]
    for the park picker's suggestions, [] when the list hasn't loaded."""
    ws = config.get("websocket") if isinstance(config.get("websocket"), dict) else {}
    sound = config.get("sound") if isinstance(config.get("sound"), dict) else {}
    countdown = config.get("trip_countdown") if isinstance(config.get("trip_countdown"), dict) else {}
    matrix = config.get("matrix") if isinstance(config.get("matrix"), dict) else {}
    parks = config.get("parks") if isinstance(config.get("parks"), list) else list(WDW_PARKS)
    weather = config.get("weather") if isinstance(config.get("weather"), dict) else {}

    top = (f"{notices(problems, saved)}"
           + (_notice("warn", f"<strong>Setup mode.</strong> Anyone who joins <strong>{escape(hotspot)}</strong> can "
                              f"open this page while the board is in setup.") if hotspot else "")
           + (_notice("warn", escape(note)) if note else ""))

    live = _section("live", "Live ride updates", "Wait times as they change, from ThemeParks.wiki.", (
        _key_field("themeparks_key", "ThemeParks.wiki API key", ws.get("api_key"), "Needed for live updates.")
        + _switch("ws_enabled", "Live ride updates", ws.get("enabled", True),
                  "When off, the board still checks wait times every 5 minutes.")
        + _field("ws_protocol", "Live update protocol",
                 _options("ws_protocol", [(p, p.capitalize()) for p in WS_PROTOCOLS], ws.get("protocol", "legacy")),
                 "Legacy unless you've been asked to try Preview.")
    ), "live")
    weather_html = _section("weather", "Weather", "The temperature and conditions on each park's screen.", (
        _key_field("weather_key", "OpenWeatherMap API key", weather.get("apikey"), "From openweathermap.org.")
    ), "cloud")

    known = {name.lower() for name, _ in park_names}
    chips = "".join(_park_chip(p, bool(known) and p.lower() not in known) for p in parks if isinstance(p, str))
    suggestions = "".join(f'<option value="{_attr(n)}">{escape(d)}</option>' for n, d in park_names)
    add_input = _input("park_add", extra=' list="park-names" autocomplete="off" placeholder="Start typing a park" '
                                         'aria-describedby="park-error"')
    add = (f'<div class="add-row">{add_input}'
           f'<button type="button" class="secondary js-only" id="park-add-btn" hidden>{icon("plus")}Add</button></div>'
           f'<datalist id="park-names">{suggestions}</datalist>'
           '<p class="field-error" id="park-error" role="alert" hidden></p>')
    park_html = _section("parks", "Parks", "Which parks the board cycles through, in this order.", (
        f'<ol class="park-chips" id="park-chips" aria-label="Parks, in order">{chips}</ol>'
        + f'<template id="park-chip">{_park_chip("")}</template>'
        + _field("park_add", "Add a park", add,
                 "Any park on ThemeParks.wiki: start typing and pick it from the list. It goes on the end; "
                 "the arrow moves a park earlier." if park_names else
                 "The list of parks hasn't loaded yet (the board needs the internet for it): type the name "
                 "exactly as ThemeParks.wiki has it.")
    ), "pin")

    rows = trip_rows(config)
    trips = _section("trips", "Trip countdown", "Days to go until your next trip, between the parks.", (
        _switch("trips_enabled", "Show the countdown", countdown.get("enabled", False))
        + '<div class="trips" id="trip-list">' + "".join(_trip(i, *row) for i, row in enumerate(rows))
        + ("" if rows else _trip(0)) + "</div>"  # a blank row to start from only when there are no trips
        + f'<template id="trip-row">{_trip("N")}</template>'
        + f'<p style="margin-top:12px"><button type="button" class="ghost" id="add-trip">{icon("plus")}Add a trip'
          f'</button></p>'
    ), "calendar")

    device = sound.get("device") or ""
    custom = bool(device) and device not in sound_cards
    quiet = sound.get("quiet_hours") if isinstance(sound.get("quiet_hours"), dict) else {}
    custom_input = _input("sound_device_custom", device if custom else "",
                          extra=' class="mono" placeholder="plughw:CARD=Device,DEV=0"')
    quiet_inputs = (_input("quiet_start", quiet.get("start", ""), "time", ' aria-label="Quiet from"') + "<span>to</span>"
                    + _input("quiet_end", quiet.get("end", ""), "time", ' aria-label="Quiet until"'))
    speaker = (_options("sound_device", [("", "The board's default")] + [(c, c) for c in sound_cards]
                        + [("custom", "Other device…")], "custom" if custom else device)
               + f'<div class="below" id="custom-device"><label class="mini" for="sound_device_custom">ALSA device'
                 f'</label>{custom_input}</div>')
    sound_html = _section("sound", "Sound", "The fireworks music, from a speaker on the board.", (
        _switch("sound_enabled", "Play the fireworks music", sound.get("enabled", False),
                "Needs a speaker, and the music in the sounds folder.")
        + _field("sound_device", "Speaker", speaker)
        + _field("quiet_start", "Quiet hours",
                 f'<div class="pair">{quiet_inputs}</div>',
                 "No music between these times. Leave both blank for none.")
    ), "sound")

    brightness = matrix.get(BRIGHTNESS)
    schedule = config.get("brightness_schedule") if isinstance(config.get("brightness_schedule"), dict) else None
    sched = schedule or {}
    level = ' min="1" max="100" inputmode="numeric"'

    def scheduled(key, label, value, start_key, start_label, start):
        return (f'<div><label class="mini" for="{key}">{label}</label>{_input(key, value, "number", level)}</div>'
                f'<div><label class="mini" for="{start_key}">{start_label}</label>{_input(start_key, start, "time")}</div>')
    display = _section("display", "Display", "How bright the LED panel is, all day or by the time of day.", (
        _field(f"matrix_{BRIGHTNESS}", "Brightness",
               _input(f"matrix_{BRIGHTNESS}", "" if brightness is None else brightness, "number",
                      level + ' placeholder="Board default"'),
               "1 to 100. Blank uses the board's own setting. A schedule, when on, takes over from it.")
        + _switch("brightness_schedule", "Day and night brightness", schedule is not None,
                  "Dim the board at night, by the board's clock.")
        + '<div class="schedule-wrap" id="schedule">'
        + ("" if schedule else '<p class="hint schedule-note">Not set up yet: these are suggested starting values, '
                                'saved only if you turn this on.</p>')
        + '<div class="schedule">'
        + scheduled("bright_day", "Day brightness", sched.get("day", 80), "day_start", "Day starts",
                    sched.get("day_start", "07:00"))
        + scheduled("bright_night", "Night brightness", sched.get("night", 15), "night_start", "Night starts",
                    sched.get("night_start", "22:00"))
        + "</div></div>"
    ), "sun")

    shows_by_name = {e["name"]: e for e in config.get("shows") or []
                     if isinstance(e, dict) and isinstance(e.get("name"), str)}
    show_rows = ""
    for i, name in enumerate(show_names(config)):
        entry = shows_by_name.get(name, {})
        label = _attr(name)
        show_rows += (
            f'<div class="show"><div class="show-name">{escape(name)}'
            f'<input type="hidden" name="show_name_{i}" value="{label}"></div><div class="show-ctl">'
            f'<label><span class="mini">Version</span>'
            + _options(f"show_version_{i}", [(v, v.upper() if v != "default" else "Default") for v in SHOW_VERSIONS],
                       entry.get("version", "default"), f' aria-label="{label} version"')
            + f'</label><label><span class="mini">Play</span>'
            + _switch_input(f"show_enabled_{i}", entry.get("enabled", True), f' aria-label="Play {label}"')
            + f'</label><label><span class="mini">Test</span>'
            + _switch_input(f"show_force_{i}", entry.get("force"), f' aria-label="Play {label} at start-up"')
            + "</label></div></div>")
    shows = _section("shows", "Fireworks shows", "What plays when each show starts in the park.", (
        f'<div class="shows">{show_rows}</div>'
        + _notice("info", "<strong>Default</strong> plays the castle fireworks for five minutes. <strong>V1</strong> "
                          "and <strong>V2</strong> play the whole show in time with its music. <strong>Test</strong> "
                          "plays a show once each time the app starts; turn it off when you're done.")
    ), "sparkle")

    panel = ""
    for key, help_text, options, switch, _ in cli.matrix_settings():
        if key == BRIGHTNESS:
            continue
        value = matrix.get(key)
        label = key.removeprefix("led_").replace("_", " ").capitalize()
        name = f"matrix_{key}"
        if switch:
            chosen = "" if value is None else ("true" if value else "false")
            control = _options(name, [("", "Board default"), ("true", "On"), ("false", "Off")], chosen)
        elif options:
            chosen = "" if value is None else str(value)
            control = _options(name, [("", "Board default")] + [(str(o), str(o) or "None") for o in options], chosen)
        else:
            control = _input(name, "" if value is None else value, extra=' class="mono" placeholder="Board default"')
        panel += _field(name, label, control, help_text or "")
    advanced = (
        '<details class="card" id="advanced"><summary class="card-head">'
        f'<span class="card-icon">{icon("sliders")}</span><div><h2>Advanced</h2>'
        '<p>Panel hardware. Most boards never need these.</p></div>'
        f'<span class="chev">{icon("chevron")}</span></summary><div class="card-body">'
        + _notice("warn", "The wrong panel settings can leave the board dark or flickering. Blank leaves each one to "
                          "the board's own settings (boards.json).")
        + panel
        + "</div></details>")
    testing = _section("testing", "Testing", "For checking the board; turn them off when you're done.", (
        _switch("debug", "Debug logging", config.get("debug", False), "More detail in the board's log.")
        + _field("force_surprise", "Surprise on every ride screen",
                 _options("force_surprise", [("", "None")] + sorted(
                     ((n, CHARACTER_NAMES.get(n, n.replace("_", " ").title())) for n in surprise_names()), key=lambda o: o[1]),
                     config.get("force_surprise") or ""),
                 "Plays that character on every ride screen, for checking it on the board. "
                 "Set it back to None when you're done.")
    ), "flask")

    toc = "".join(f'<a href="#{sid}">{icon(glyph)}{escape(title)}</a>' for sid, title, glyph in SECTIONS)
    mode = ("warn", "Setup mode") if hotspot else ("good", "Signed in")
    body = (
        _topbar(board, mode)
        + f'<div class="shell"><nav class="toc" aria-label="Sections">{toc}</nav><main>'
        + '<div class="page-head"><h1>Settings</h1><p>Changes are checked, saved to the board\'s config.json, '
          'and the app restarts to use them.</p></div>'
        + top
        + f'<form method="post" action="/save" id="settings"><div class="stack">'
          f'{live}{weather_html}{park_html}{trips}{sound_html}{display}{shows}{testing}{advanced}</div>'
        + '<div class="savebar"><div class="savebar-in"><div class="status" id="save-status"><span class="dot"></span>'
          '<span>Saved keys stay as they are unless you replace them</span></div>'
          f'<button type="submit" class="primary" id="save">{icon("save")}<span>Save and restart</span></button>'
          '</div></div></form></main></div>')
    return document("Board settings", body, SCRIPT)


def pin_page(shown_s=None, wrong=False, board=None):
    """The sign-in page on the home network. shown_s: a PIN is on the board for this long."""
    status = ""
    if wrong:
        status = _notice("bad", "That isn't the PIN on the board. Try again, or ask for a new one.", "alert")
    elif shown_s:
        status = _notice("good", f"The PIN is on the board for the next {max(1, round(shown_s / 60))} "
                                 f"minute{'s' if shown_s > 90 else ''}.")
    body = (
        _topbar(board)
        + f'<div class="center"><div class="card auth"><div class="auth-icon">{icon("lock")}</div>'
          '<h1>Sign in to this board</h1><p>To change this board\'s settings, type in the PIN it shows.</p>'
        + status
        + '<div class="step"><span class="step-n">1</span><div class="step-body"><strong>Show a PIN</strong>'
          '<p>It appears on the LED board for two minutes.</p>'
          f'<form method="post" action="/pin/show"><button type="submit" class="secondary">{icon("board")}'
          'Show a PIN on the board</button></form></div></div>'
        + '<div class="step"><span class="step-n">2</span><div class="step-body"><label for="pin"><strong>Type it in'
          '</strong></label><p>You stay signed in on this browser for an hour.</p>'
          '<form method="post" action="/pin"><input type="text" id="pin" name="pin" class="pin" inputmode="numeric" '
          'autocomplete="one-time-code" pattern="[0-9]*" maxlength="8" required autofocus aria-label="PIN">'
          '<button type="submit" class="primary block">Sign in</button></form></div></div>'
        + "</div></div>")
    return document("Sign in · Board settings", body)
