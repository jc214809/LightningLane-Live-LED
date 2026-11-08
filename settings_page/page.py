"""The settings page's HTML: the form for config.json (fields named as form.apply_form reads
them), the PIN page, and the notices after a save. Everything is inline (styles, icons, a few
lines of script), since a phone on the setup hotspot has no internet to fetch anything from. It
works without JavaScript; the script adds trip rows and the "unsaved changes" state.
"""
import functools
import json
import os
import re
import time
from html import escape

import cli
from settings_page.board_status import NONE, QUIET, SHOW, ago
from settings_page.form import BRIGHTNESS, WDW_PARKS, masked, panel_size, character_label, show_names, surprise_names, trip_rows
from utils import debug
from utils.trips import active_trip, countdown_message, parse_trips
from settings_page.updates import BUSY, START_FAILED, STARTED, STEPS
from self_update.state import ROLLBACK_FAILED, UNFINISHED
from self_update.github import FAILED, PASSED, REPO, RUNNING
from self_update.update import (BETA, BETA_BRANCH, CURRENT, RELEASES, WAITING, WOULD_UPDATE, beta_number, name_of,
                                release_of)
from utils.config import DEFAULT_VOLUME, SHOW_VERSIONS, WS_PROTOCOLS

# The page's pictures, served by server.py from settings_page/static (no internet on the setup hotspot):
# the logo and its PNGs for phones, and the board's park landmarks, rendered by tools/build_settings_art.py.
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ICON, TOUCH_ICON, ICON_512 = "/static/icon.svg", "/static/apple-touch-icon.png", "/static/icon-512.png"
LANDMARK_INDEX = "landmarks.json"
CASTLE_KEY = "magic kingdom"  # the castle stands in for the board in the brightness, rotation and show previews

# What a save says, by Settings.restart_app's outcome.
SAVED = ("restarted", "saved", "failed", "volume", "volume_failed")
SENT = ("sent", "wait", "used", "failed")  # pins.PinGate.send_pin's outcomes

STYLE = """
/* The logo's storybook night: navy and indigo, with gold. */
:root {
  --navy: #0e1440; --indigo: #2b1d63; --gold: #f2b84b; --gold-lt: #ffe6a6; --led-bg: #04061a;
  --bg: #f4f2fa; --surface: #fff; --surface-2: #f8f6fd; --border: #e4e0f0; --border-strong: #cfc9e2;
  --text: #151a3f; --text-2: #454a6e; --text-3: #6b6f8f;
  --accent: #3a2d8f; --accent-hover: #2b2070; --accent-soft: #ece8fb; --on-accent: #fff;
  --primary-bg: linear-gradient(135deg, var(--navy), var(--indigo)); --primary-text: var(--gold-lt);
  --good: #067647; --good-bg: #ecfdf3; --good-line: #abefc6;
  --bad: #b42318; --bad-bg: #fef3f2; --bad-line: #fecdca;
  --warn: #93370d; --warn-bg: #fffaeb; --warn-line: #fedf89;
  --shadow: 0 1px 2px rgba(14, 20, 64, .06), 0 1px 3px rgba(14, 20, 64, .08);
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) { :root {
  --bg: #0a0d26; --surface: #121638; --surface-2: #181d45; --border: #262b58; --border-strong: #383e72;
  --text: #eef0fb; --text-2: #bcc0dc; --text-3: #8d92b5;
  --accent: #f2b84b; --accent-hover: #ffd27a; --accent-soft: #2c2748; --on-accent: #0e1440;
  --primary-bg: linear-gradient(135deg, #ffd27a, #f2b84b); --primary-text: #0e1440;
  --good: #75e0a7; --good-bg: #0c2a1c; --good-line: #14532d;
  --bad: #fda29b; --bad-bg: #2d1412; --bad-line: #5c1f1a;
  --warn: #fec84b; --warn-bg: #2b2110; --warn-line: #5c4313;
  --shadow: 0 1px 2px rgba(0, 0, 0, .45);
} }
.serif, .page-head h1, .brand-name, .auth h1 { font-family: ui-serif, "Iowan Old Style", Georgia, "Noto Serif", serif; }
* { box-sizing: border-box; }
html { scroll-padding-top: 84px; }
body { margin: 0; background: var(--bg); color: var(--text); -webkit-font-smoothing: antialiased;
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2;
  stroke-linecap: round; stroke-linejoin: round; flex: none; }
h1, h2, h3, p { margin: 0; }
a { color: var(--accent); }

/* Top bar: always the logo's night sky, a scatter of stars, a gold edge */
.topbar { position: sticky; top: 0; z-index: 20; color: #eef0fb; border-bottom: 1px solid rgba(242, 184, 75, .45);
  background: radial-gradient(1.6px 1.6px at 12% 30%, #fff8 50%, transparent 51%),
              radial-gradient(1.6px 1.6px at 38% 70%, #fff6 50%, transparent 51%),
              radial-gradient(2px 2px at 61% 25%, #fff9 50%, transparent 51%),
              radial-gradient(1.6px 1.6px at 79% 62%, #fff6 50%, transparent 51%),
              radial-gradient(1.6px 1.6px at 92% 22%, #fff7 50%, transparent 51%),
              linear-gradient(120deg, var(--navy), var(--indigo)); }
.topbar-in { max-width: 1080px; margin: 0 auto; padding: 0 16px; height: 60px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
.mark { width: 38px; height: 38px; border-radius: 10px; overflow: hidden; flex: none;
  box-shadow: 0 0 0 1px rgba(242, 184, 75, .5); }
.mark img { width: 100%; height: 100%; display: block; }
.brand-name { font-style: italic; font-weight: 600; font-size: 19px; color: var(--gold-lt); line-height: 1.1;
  white-space: nowrap; }
.brand-sub { color: #c9cdea; font-size: 10px; font-weight: 650; letter-spacing: .3em; text-transform: uppercase; }
.brand-sub::before, .brand-sub::after { content: "\\2726"; color: var(--gold); margin: 0 .45em; letter-spacing: 0; }
.top-meta { display: flex; align-items: center; gap: 8px; }
.chip { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border-radius: 999px;
  border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); font-size: 13px;
  font-weight: 500; white-space: nowrap; }
.chip svg { width: 14px; height: 14px; }
.chip.warn { color: var(--warn); background: var(--warn-bg); border-color: var(--warn-line); }
.chip.good { color: var(--good); background: var(--good-bg); border-color: var(--good-line); }
.topbar .chip { background: rgba(255, 255, 255, .08); border-color: rgba(255, 255, 255, .18); color: #e6e8f7; }
.topbar .chip.warn { color: #fec84b; border-color: #fec84b66; background: #fec84b1a; }
.topbar .chip.good { color: #75e0a7; border-color: #75e0a766; background: #75e0a71a; }
.topbar form { margin: 0; }
.topbar button { height: 28px; padding: 0 10px; font-size: 13px; }
.topbar .ghost { color: var(--gold-lt); }
.topbar .ghost:hover { background: rgba(255, 255, 255, .1); }
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
  .toc a.on { background: var(--accent-soft); color: var(--accent); box-shadow: inset 2px 0 0 var(--gold); }
  .toc svg { width: 16px; height: 16px; }
}
.page-head { margin-bottom: 20px; }
.page-head h1 { font-size: 28px; font-weight: 600; font-style: italic; letter-spacing: -.02em; }
.page-head h1::after { content: " \\2726"; color: var(--gold); font-style: normal; font-size: .7em; vertical-align: .2em; }
.page-head p { color: var(--text-2); margin-top: 4px; }
.stack { display: grid; gap: 20px; }
.stack.before { margin-bottom: 20px; }

/* Cards */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; box-shadow: var(--shadow); }
.card-head { display: flex; gap: 14px; align-items: flex-start; padding: 18px 20px; border-bottom: 1px solid var(--border); }
.card-icon { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; flex: none;
  background: linear-gradient(135deg, var(--navy), var(--indigo)); color: var(--gold);
  box-shadow: inset 0 0 0 1px rgba(242, 184, 75, .35); }
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
.volume { display: flex; gap: 12px; align-items: center; }
.volume input[type=range] { flex: 1; min-width: 0; accent-color: var(--accent); }
.volume input[type=number] { width: 5.5em; flex: none; }
.buttons { display: flex; flex-wrap: wrap; gap: 8px; }
.volume-status:empty { display: none; }
.volume-status[data-ok="false"] { color: var(--bad); }
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
  place-items: center; flex: none; background: var(--primary-bg); color: var(--primary-text); font-size: 12px; font-weight: 650; }
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
.share { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 0 0 16px; }
.share-status { color: var(--text-2); font-size: 13px; }
.share-status.bad { color: var(--bad); }
.table-wrap { overflow-x: auto; margin: 6px 0 14px; }
table.odds { width: 100%; border-collapse: collapse; font-size: 14px; }
.odds th, .odds td { text-align: left; padding: 9px 10px; border-top: 1px solid var(--border); vertical-align: top; }
.odds thead th { border-top: 0; font-size: 12px; font-weight: 600; color: var(--text-3); white-space: nowrap; }
.odds th button { background: none; border: 0; padding: 2px 4px; margin: -2px -4px; font: inherit; color: inherit;
  cursor: pointer; border-radius: 4px; }
.odds th button:hover { color: var(--text); }
.odds th button:focus-visible { outline: 2px solid var(--accent); }
.odds th button::after { content: " \2195"; opacity: .45; }
.odds th[aria-sort=ascending] button::after { content: " \25B2"; opacity: 1; }
.odds th[aria-sort=descending] button::after { content: " \25BC"; opacity: 1; }
.odds td:nth-child(2) { font-weight: 550; min-width: 150px; }
.odds td input[type=number] { width: 92px; }
.odds .none { color: var(--text-3); }
.odds th:last-child, .odds td:last-child { width: 100%; }
.odds tfoot th, .odds tfoot td { border-top: 2px solid var(--border-strong); font-weight: 600; }
.odds .total-sub { font-weight: 400; font-size: 12px; color: var(--text-3); }
.odds .over { color: var(--bad); }
.rides-cell { display: flex; align-items: flex-start; gap: 12px; }
.ride-names { flex: 1; min-width: 160px; color: var(--text-2); line-height: 1.4; padding-top: 4px; }
.ride-names.none { color: var(--text-3); }
.odds .add-rides { flex: none; margin-left: auto; width: 30px; height: 30px; padding: 0; display: inline-grid;
  place-items: center; }
.odds .add-rides svg { width: 16px; height: 16px; }
.odds tr.ride-row td { border-top: 0; padding: 0 10px 14px; }
.ride-pick { border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; background: var(--surface-2); }
.ride-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.ride-bar.ride-foot { margin: 12px 0 0; justify-content: flex-end; }
.ride-pick input[type=search] { width: 100%; max-width: 320px; }
.odds .add-rides[aria-expanded=true] svg { transform: rotate(45deg); }
.ride-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px 20px; align-items: start; }
.ride-pick h4 { margin: 0 0 6px; font-size: 12px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.ride-pick label { display: flex; gap: 8px; align-items: center; padding: 3px 0; font-weight: 400; }
.ride-pick label[hidden], .ride-park[hidden], .ride-pick p[hidden] { display: none; }
.ride-pick p { margin: 0; color: var(--text-3); }
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
.primary { background: var(--primary-bg); color: var(--primary-text); box-shadow: var(--shadow); }
.primary:hover { background: var(--primary-bg); filter: brightness(1.12); }
.primary:disabled { opacity: .7; cursor: progress; }
.secondary { background: var(--surface); color: var(--text); border-color: var(--border-strong); box-shadow: var(--shadow); }
.secondary:hover { background: var(--surface-2); }
.secondary:disabled { opacity: .55; cursor: not-allowed; }
.changes { margin: 0 0 12px; }
.changes ul { margin: 6px 0 0; padding-left: 0; list-style: none; display: grid; gap: 4px; font-size: 14px; }
.changes li { display: flex; gap: 8px; }
.changes li a, .changes li .mono { flex: none; min-width: 3.2em; color: var(--text-3); }
.changes .note { display: block; margin-top: 1px; }
.notice .changes { margin: 8px 0 0; }
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
.notice.new { color: var(--text); background: var(--accent-soft); border-color: var(--accent); }
.notice.new svg { color: var(--accent); }
.notice .when { color: var(--text-3); font-weight: 400; }
.steps { list-style: none; margin: 10px 0; padding: 0; display: grid; gap: 6px; }
.steps li { display: flex; align-items: center; gap: 10px; color: var(--text-3); }
.steps li::before { content: ""; flex: none; width: 8px; height: 8px; border-radius: 50%; border: 2px solid currentColor; }
.steps li.done { color: var(--good); }
.steps li.done::before { background: currentColor; }
.steps li.now { color: var(--text); font-weight: 600; }
.steps li.now::before { border-color: var(--accent); background: var(--accent); animation: beat 1.2s ease-in-out infinite; }
.steps li.failed { color: var(--bad); font-weight: 600; }
.steps li.failed::before { background: currentColor; }
@keyframes beat { 50% { opacity: .3; } }
@media (prefers-reduced-motion: reduce) { .steps li.now::before { animation: none; } }

/* Save bar */
.savebar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; border-top: 1px solid rgba(242, 184, 75, .5);
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
  background: linear-gradient(135deg, var(--navy), var(--indigo)); color: var(--gold);
  box-shadow: inset 0 0 0 1px rgba(242, 184, 75, .35); }
.auth-icon svg { width: 24px; height: 24px; }
.auth h1 { font-size: 21px; font-weight: 600; letter-spacing: -.02em; }
/* Sign-in: the logo and wordmark crown the card. */
.auth-hero { display: grid; justify-items: center; gap: 10px; margin: -4px 0 20px; text-align: center; }
.auth-hero img { width: 76px; height: 76px; border-radius: 19px; box-shadow: 0 6px 20px rgba(14, 20, 64, .3); }
.auth-hero .brand-name { color: var(--accent); font-size: 24px; }
@media (prefers-color-scheme: dark) { .auth-hero .brand-name { color: var(--gold-lt); } }
.auth-hero .brand-sub { color: var(--text-3); }
.auth.signin h1, .auth.signin > p { text-align: center; }

/* What the board draws, on the page: the LED panel's black, its pixels kept sharp */
.led { background: var(--led-bg); border-radius: 10px; padding: 6px; display: inline-block; line-height: 0;
  box-shadow: inset 0 0 0 1px rgba(242, 184, 75, .25), 0 1px 3px rgba(14, 20, 64, .25); }
.led img { image-rendering: pixelated; display: block; border-radius: 3px; width: 128px; height: 64px; }
.preview-label { font-size: 12px; color: var(--text-3); margin-top: 6px; text-align: center; }
.previews { display: flex; gap: 18px; flex-wrap: wrap; align-items: center; padding: 16px 0 4px; }
.previews .led img { transition: filter .2s, transform .3s; }
.previews .hint { max-width: 320px; margin: 0; }
.previews [hidden] { display: none; }
.board-now { display: flex; gap: 16px; align-items: center; padding: 16px 20px; flex-wrap: wrap; }
.board-now h2 { font-size: 16.5px; font-weight: 650; }
.board-now .card-text { flex: 1; min-width: 220px; }
.board-now p { color: var(--text-3); font-size: 13.5px; margin-top: 2px; }
.facts { display: flex; gap: 6px 18px; flex-wrap: wrap; margin-top: 8px; font-size: 13.5px; color: var(--text-2); }
.facts b { color: var(--text); font-weight: 600; }
.beat { display: inline-flex; align-items: center; gap: 8px; font-weight: 600; color: var(--good); }
.beat::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: currentColor;
  box-shadow: 0 0 0 4px var(--good-bg); animation: beat 2s ease-in-out infinite; }
.beat.quiet { color: var(--warn); } .beat.quiet::before { box-shadow: 0 0 0 4px var(--warn-bg); animation: none; }
.beat.none { color: var(--text-3); } .beat.none::before { box-shadow: none; animation: none; }
@media (prefers-reduced-motion: reduce) { .beat::before { animation: none; } }
.park-chips { gap: 12px; }
.park-chip { height: auto; border-radius: 12px; padding: 6px 6px 6px 8px; gap: 10px; }
.park-chip .led { padding: 3px; border-radius: 7px; }
.park-chip .led img { width: 64px; height: 32px; }
.noland { width: 64px; height: 32px; display: grid; place-items: center; font-size: 10px; color: #8d92b5;
  line-height: 1.2; text-align: center; }
.park-chip .led [hidden] { display: none; }
.countdown { display: flex; align-items: center; gap: 16px; margin: 16px 0 4px; flex-wrap: wrap; }
.countdown .led { padding: 10px 18px; line-height: 1.15; text-align: center; min-width: 140px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.countdown .big { display: block; color: #ffd23c; font-size: 26px; font-weight: 700; text-shadow: 0 0 8px rgba(255, 210, 60, .6); }
.countdown .line { display: block; color: #9fd8ff; font-size: 12px; letter-spacing: .08em; text-shadow: 0 0 6px rgba(159, 216, 255, .5); }
.countdown .hint { max-width: 360px; margin: 0; }
.trip.next { border-color: var(--gold); box-shadow: inset 3px 0 0 var(--gold); }
.trip .tag { position: absolute; top: -9px; left: 12px; font-size: 11px; font-weight: 650; padding: 0 8px;
  border-radius: 999px; background: var(--gold); color: #0e1440; }
.cast { list-style: none; margin: 0; padding: 16px 0 14px; display: flex; flex-wrap: wrap; gap: 6px; }
.cast li { font-size: 12.5px; padding: 2px 10px; border-radius: 999px; background: var(--surface-2);
  border: 1px solid var(--border); color: var(--text-2); }
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
    "phone": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
    "wifi": '<path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"/>',
    "save": '<path d="M20 6 9 17l-5-5"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/>',
    "undo": '<path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-15-6.7L3 13"/>',
}

SECTIONS = (  # id, nav title, icon
    ("updates", "Updates", "refresh"), ("live", "Live updates", "live"), ("weather", "Weather", "cloud"), ("phone", "PIN by Pushover", "phone"),
    ("parks", "Parks", "pin"), ("trips", "Trip countdown", "calendar"),
    ("sound", "Sound", "sound"), ("panel", "Panel", "board"), ("display", "Display", "sun"),
    ("shows", "Fireworks shows", "sparkle"), ("surprises", "Surprise characters", "sparkle"),
    ("testing", "Testing", "flask"), ("advanced", "Advanced", "sliders"),
)

# The Panel card's settings, the ones a Pi model sets (and rotation), with their labels; the rest
# are under Advanced. Rows and columns are the Panel size dropdown's.
PANEL_SETTINGS = {"led_pixel_mapper": "Rotation", "led_gpio_mapping": "GPIO mapping",
                  "led_slowdown_gpio": "GPIO slowdown", "led_pwm_lsb_nanoseconds": "PWM timing (ns)"}
SIZE_SETTINGS = ("led_rows", "led_cols")
# Rotation's choices: --led-pixel-mapper values. A saved one not here is offered as it is.
ROTATIONS = (("Rotate:180", "Upside down (Rotate:180)"), ("Rotate:90", "A quarter turn (Rotate:90)"),
             ("Rotate:270", "Three quarters (Rotate:270)"), ("Mirror:H", "Mirrored left to right (Mirror:H)"),
             ("Mirror:V", "Mirrored top to bottom (Mirror:V)"))

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
// The landmark the board plays before a park, by the loose name match the board uses.
const parkScenes = JSON.parse(document.getElementById('park-scenes')?.textContent || '{}');
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
  const scene = Object.entries(parkScenes).find(([key]) => name.toLowerCase().includes(key));
  if (scene) {
    const img = chip.querySelector('.park-landmark');
    img.src = scene[1];
    img.hidden = false;
    chip.querySelector('.noland').hidden = true;
  }
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
// Volume: the slider and the box follow each other; the buttons ask the board without leaving the page.
const volume = document.getElementById('sound_volume');
const volumeSlider = document.getElementById('volume_slider');
const volumeStatus = document.getElementById('volume-status');
volumeSlider.addEventListener('input', () => { volume.value = volumeSlider.value; });
volume.addEventListener('input', () => { if (volume.value !== '') volumeSlider.value = volume.value; });
document.querySelectorAll('button[name=volume_action]').forEach(button => button.addEventListener('click', async e => {
  // The rest of the form goes along (for the speaker picked) but stays unsaved.
  const data = new URLSearchParams(new FormData(form));
  data.set('volume_action', button.value);
  button.disabled = true;
  delete volumeStatus.dataset.ok;
  volumeStatus.textContent = button.value === 'test' ? 'Playing\u2026' : 'Setting\u2026';
  try {
    const reply = await fetch('/volume', {method: 'POST', body: data, headers: {Accept: 'application/json'}});
    const result = await reply.json();  // a signed-out page gets HTML back, and lands in catch
    volumeStatus.textContent = result.message;
    volumeStatus.dataset.ok = result.ok;
  } catch {
    volumeStatus.textContent = "That didn't reach the board: reload the page and try again.";
    volumeStatus.dataset.ok = false;
  } finally {
    button.disabled = false;
  }
}));
const scheduleOn = document.getElementById('brightness_schedule');
const showSchedule = () => { document.getElementById('schedule').hidden = !scheduleOn.checked; };
scheduleOn.addEventListener('change', showSchedule);
showSchedule();
// A blank panel setting says the Pi model's default (page.py's panel texts, per model): follow
// a new pick of model.
const piModel = document.getElementById('pi_model');
const panelData = JSON.parse(document.getElementById('panel-blanks')?.textContent || '{}');
piModel?.addEventListener('change', () => {
  const blanks = panelData.blanks[piModel.value === 'auto' ? panelData.auto : piModel.value] || {};
  document.querySelectorAll('[data-key]').forEach(el => {
    const text = blanks[el.dataset.key] || 'Default';
    if (el.tagName === 'SELECT') el.options[0].textContent = text; else el.placeholder = text;
  });
});
// Updates: the buttons say they're working (a check can take a while), Roll back asks first, and
// while an update runs the page follows it, reloading once it's done. The settings page restarts
// during an update, so a failed ask just tries again.
// On the document, not each form: the page's own check puts in an Update now form later.
document.addEventListener('submit', e => {
  const f = e.target;
  if (!f.matches('form[data-busy]')) return;
  if (f.dataset.confirm && !confirm(f.dataset.confirm)) return e.preventDefault();
  const button = f.querySelector('button[type=submit]');
  button.disabled = true;
  button.querySelector('span').textContent = f.dataset.busy;
});
const updateRunning = document.getElementById('update-running');
if (updateRunning) {
  const follow = async () => {
    try {
      const reply = await fetch('/update/status', {headers: {Accept: 'application/json'}});
      const now = await reply.json();
      if (!now.running) return location.replace('/?t=' + Date.now() + '#updates');
      document.getElementById('update-phase').textContent = now.phase;
      const steps = document.getElementById('update-steps');
      if (steps) {
        steps.hidden = now.step === null;
        steps.querySelectorAll('li').forEach((li, i) => {
          li.className = i < now.step ? 'done' : i === now.step ? 'now' : '';
          if (i === now.step) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current');
        });
      }
    } catch {}
    setTimeout(follow, 5000);
  };
  setTimeout(follow, 5000);
}
// No check yet: check the installed channel now (the board keeps it ten minutes), without
// reloading the page over unsaved settings.
const autoCheck = document.querySelector('#update-check[data-auto]');
if (autoCheck) (async () => {
  try {
    const reply = await fetch('/update/check', {method: 'POST', body: new URLSearchParams({channel: autoCheck.dataset.auto}),
                                                headers: {Accept: 'application/json'}});
    autoCheck.outerHTML = (await reply.json()).html;  // a signed-out page gets HTML back, and lands in catch
  } catch {
    autoCheck.querySelector('div').textContent = "Couldn't check: press Check to try again.";
  }
})();
// The castle previews: dimmed to the brightness the Display card sets, turned the way Rotation turns it.
const level = id => { const v = parseInt(document.getElementById(id)?.value, 10); return isNaN(v) ? null : v; };
const dim = (id, percent) => { const img = document.getElementById(id); if (img) img.style.filter = `brightness(${0.25 + 0.75 * percent / 100})`; };
function brightnessPreviews() {
  if (!document.getElementById('pv-all')) return;
  const scheduleOn = document.getElementById('brightness_schedule').checked;
  const day = level('bright_day') ?? 80, night = level('bright_night') ?? 15, all = level('matrix_led_brightness');
  document.getElementById('pv-all-box').hidden = scheduleOn;
  document.getElementById('pv-day-box').hidden = !scheduleOn;
  document.getElementById('pv-night-box').hidden = !scheduleOn;
  dim('pv-all', all ?? 100);
  dim('pv-day', day);
  dim('pv-night', night);
  document.getElementById('pv-all-l').textContent = all ? `All day, ${all}%` : "All day, the Pi model's default";
  document.getElementById('pv-day-l').textContent = `Day, ${day}%`;
  document.getElementById('pv-night-l').textContent = `Night, ${night}%`;
}
['bright_day', 'bright_night', 'matrix_led_brightness', 'brightness_schedule'].forEach(id =>
  document.getElementById(id)?.addEventListener('input', brightnessPreviews));
brightnessPreviews();
const rotation = document.getElementById('matrix_led_pixel_mapper');
const turns = {'Rotate:90': 'rotate(90deg) scale(.5)', 'Rotate:180': 'rotate(180deg)', 'Rotate:270': 'rotate(270deg) scale(.5)',
               'Mirror:H': 'scaleX(-1)', 'Mirror:V': 'scaleY(-1)'};
function rotationPreview() {
  const img = document.getElementById('pv-rot');
  if (!img || !rotation) return;
  img.style.transform = turns[rotation.value] || '';
  const text = rotation.options[rotation.selectedIndex].text.split(' (')[0];
  document.getElementById('pv-rot-l').textContent = rotation.value ? `Drawn ${text.toLowerCase()}` : 'Drawn as is';
}
rotation?.addEventListener('change', rotationPreview);
rotationPreview();
const links = [...document.querySelectorAll('.toc a')];
const spy = new IntersectionObserver(entries => entries.forEach(e => {
  if (e.isIntersecting) links.forEach(a => a.classList.toggle('on', a.hash === '#' + e.target.id));
}), {rootMargin: '-80px 0px -65% 0px'});
document.querySelectorAll('main .card[id]').forEach(s => spy.observe(s));
"""


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


def _trip(index, start="", end="", name="", on_board=False):
    """on_board: the trip the countdown shows now, tagged so."""
    i = index
    name_input = _input(f"trip_name_{i}", name, extra=' placeholder="Spring Break"')
    remove = (f'<label class="trip-x" for="trip_remove_{i}" title="Remove this trip"><input type="checkbox" '
              f'id="trip_remove_{i}" name="trip_remove_{i}" aria-label="Remove this trip">{icon("x")}</label>')
    tag = '<span class="tag">On the board now</span>' if on_board else ""
    return (f'<div class="trip{" next" if on_board else ""}">{tag}<div class="wide"><label class="mini" for="trip_name_{i}">Name</label>'
            f'{name_input}</div>'
            f'<div><label class="mini" for="trip_start_{i}">Start</label>{_input(f"trip_start_{i}", start, "date")}</div>'
            f'<div><label class="mini" for="trip_end_{i}">End <span class="hint">(optional)</span></label>'
            f'{_input(f"trip_end_{i}", end, "date")}</div>{remove}</div>')


def _park_chip(name, unknown=False):
    """One chosen park: posted as "park" in page order. The X is a checkbox, so removing works
    without the script; the arrow (script only) moves it one place earlier."""
    label = _attr(name)
    title = ' title="Not a ThemeParks.wiki park name"' if unknown else ""
    # The landmark the board plays before this park; the script fills it in for a park added on the page.
    src = landmark_src(name) if name else None
    scene = (f'<span class="led"><img class="park-landmark" src="{src or ""}" alt="" width="64" height="32"'
             f'{"" if src else " hidden"}><span class="noland"{" hidden" if src else ""}>Title only</span></span>')
    return (f'<li class="park-chip{" unknown" if unknown else ""}"{title}><input type="hidden" name="park" value="{label}">'
            f'{scene}<span class="park-name">{escape(name)}</span>'
            f'<button type="button" class="chip-btn js-only" hidden aria-label="Move earlier: {label}">{icon("left")}</button>'
            f'<label class="chip-x" title="Remove"><input type="checkbox" name="park_remove" value="{label}" '
            f'aria-label="Remove {label}">{icon("x")}</label></li>')


def _json_for_script(value):
    """JSON to put inside a <script>: a "<" escaped, so "</script>" in a value can't end it."""
    return json.dumps(value).replace("<", "\\u003c")


def _matrix_field(key, label, help_text, options, switch, value, blank="Default"):
    """A config.json "matrix" setting's row; blank, it says what the board gets (blank)."""
    name = f"matrix_{key}"
    data = f' data-key="{key}"'
    if key == "led_pixel_mapper":
        choices = list(ROTATIONS) + ([(value, value)] if value and value not in dict(ROTATIONS) else [])
        control = _options(name, [("", blank)] + choices, value or "", data)
        help_text = "Which way up the panel is mounted, for a board that shows upside down or sideways."
    elif switch:
        chosen = "" if value is None else ("true" if value else "false")
        control = _options(name, [("", blank), ("true", "On"), ("false", "Off")], chosen, data)
    elif options:
        chosen = "" if value is None else str(value)
        control = _options(name, [("", blank)] + [(str(o), str(o) or "None") for o in options], chosen, data)
    else:
        control = _input(name, "" if value is None else value,
                         extra=f' class="mono" placeholder="{_attr(blank)}"{data}')
    return _field(name, label, control, help_text or "")


def _board_now_card(now):
    """The "On the board now" card, from board_status.BoardNow."""
    castle = landmarks().get(CASTLE_KEY)
    picture = _led(castle, "The board's castle") if castle else ""
    if now.state == NONE:
        status = ('<span class="beat none">No word yet</span><span>The app hasn\'t written its heartbeat since the '
                  'board started: it may still be starting, or not be running.</span>')
    elif now.state == QUIET:
        status = (f'<span class="beat quiet">Quiet</span><span>Last screen <b>{ago(now.age_s)}</b>: the app may '
                  f'have stopped. Saving restarts it.</span>')
    elif now.state == SHOW:
        status = f'<span class="beat">Showtime</span><span>Playing <b>{escape(now.show)}</b></span>'
    else:
        status = f'<span class="beat">Running</span><span>Last screen <b>{ago(now.age_s)}</b></span>'
    version = f'<span>Version <b>{escape(now.version)}</b></span>' if now.version else ""
    return (f'<section class="card board-now" aria-labelledby="now-title">{picture}<div class="card-text">'
            '<h2 id="now-title">On the board now</h2><p>From the app\'s heartbeat, as of when this page loaded.</p>'
            f'<div class="facts">{status}{version}</div></div></section>')


def _countdown_preview(config, enabled, today=None):
    """(the LED-style preview of what the countdown shows today, the Trip it's counting to or None),
    in utils.trips' own words."""
    trip = active_trip(parse_trips(config), today)
    if not enabled:
        return '<p class="hint countdown">Off: the board goes straight from park to park.</p>', None
    if trip is None:
        return '<p class="hint countdown">No trip coming up: the board skips the countdown until you add one.</p>', None
    number, lines = countdown_message(trip, today)
    big = f'<span class="big">{escape(number)}</span>' if number else ""
    words = "".join(f'<span class="line">{escape(line)}</span>' for line in lines)
    when = f'{trip.start:%B} {trip.start.day}, {trip.start.year}'
    return (f'<div class="countdown"><div class="led" role="img" aria-label="{_attr(" ".join(filter(None, (number,) + lines)))}">'
            f'{big}{words}</div><p class="hint">What the board shows between parks today, counting to '
            f'<strong>{escape(trip.name or "your trip")}</strong> on {when}.</p></div>'), trip


def _same_trip(row, trip):
    """Whether a trip_rows row (start, end, name as the form shows them) is this Trip."""
    if trip is None:
        return False
    start, end, name = row
    return (start == trip.start.isoformat() and (end or None) == (trip.end.isoformat() if trip.end else None)
            and (name.strip() or None) == trip.name)


def _brightness_previews():
    """The castle at each brightness the Display card sets; the script dims them as the numbers change."""
    castle = landmarks().get(CASTLE_KEY)
    if not castle:
        return ""
    return ('<div class="previews" aria-hidden="true">'
            + "".join(f'<div id="pv-{k}-box"><span class="led"><img id="pv-{k}" src="{castle}" alt=""></span>'
                      f'<div class="preview-label" id="pv-{k}-l">{label}</div></div>'
                      for k, label in (("all", "All day"), ("day", "Day"), ("night", "Night")))
            + "</div>")


def _rotation_preview():
    castle = landmarks().get(CASTLE_KEY)
    if not castle:
        return ""
    return (f'<div class="previews"><div><span class="led"><img id="pv-rot" src="{castle}" alt=""></span>'
            '<div class="preview-label" id="pv-rot-l">Drawn as is</div></div><p class="hint">Rotation turns the whole '
            'picture. Pick the one that puts the castle the right way up on your panel.</p></div>')


def settings_page(config, sound_cards, hotspot=None, problems=(), saved=None, board=None, note=None, park_names=(),
                  panel=None, updates=None, started=None, now=None, today=None):
    """The settings form, filled from config. sound_cards: ALSA device names for the dropdown.
    note: why config.json couldn't be read, if it couldn't. park_names: [(name, destination)]
    for the park picker's suggestions, [] when the list hasn't loaded. panel: form.PanelChoices,
    the Pi model and Panel size dropdowns and what blank fields say; None leaves them off.
    updates: updates.Updates.view(), for the Updates card (None leaves it off); started: how
    starting an update or rollback went, one of updates.STARTS. now: board_status.BoardNow, for the
    "On the board now" card (None leaves it off). today: the date the countdown preview counts from."""
    ws = config.get("websocket") if isinstance(config.get("websocket"), dict) else {}
    sound = config.get("sound") if isinstance(config.get("sound"), dict) else {}
    countdown = config.get("trip_countdown") if isinstance(config.get("trip_countdown"), dict) else {}
    matrix = config.get("matrix") if isinstance(config.get("matrix"), dict) else {}
    parks = config.get("parks") if isinstance(config.get("parks"), list) else list(WDW_PARKS)
    weather = config.get("weather") if isinstance(config.get("weather"), dict) else {}
    push = config.get("pushover") if isinstance(config.get("pushover"), dict) else {}

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
    phone = _section("phone", "PIN by Pushover", "Optional: sign in from a board you can't see.", (
        _key_field("pushover_user", "Pushover user key", push.get("user_key"), "On your pushover.net dashboard.")
        + _key_field("pushover_token", "Pushover app token", push.get("app_token"),
                     "Make an app on pushover.net for the board.")
        + _switch("pushover_enabled", "Send the PIN to my phone", push.get("enabled", True),
                  "With both keys, the sign-in page can send its PIN to your phone (it still shows on the board).")
    ), "phone")

    known = {name.lower() for name, _ in park_names}
    chips = "".join(_park_chip(p, bool(known) and p.lower() not in known) for p in parks if isinstance(p, str))
    suggestions = "".join(f'<option value="{_attr(n)}">{escape(d)}</option>' for n, d in park_names)
    add_input = _input("park_add", extra=' list="park-names" autocomplete="off" placeholder="Start typing a park" '
                                         'aria-describedby="park-error"')
    add = (f'<div class="add-row">{add_input}'
           f'<button type="button" class="secondary js-only" id="park-add-btn" hidden>{icon("plus")}Add</button></div>'
           f'<datalist id="park-names">{suggestions}</datalist>'
           '<p class="field-error" id="park-error" role="alert" hidden></p>')
    park_html = _section("parks", "Parks", "Which parks the board cycles through, in this order, with the landmark "
                                           "it plays before each one.", (
        f'<ol class="park-chips" id="park-chips" aria-label="Parks, in order">{chips}</ol>'
        + f'<template id="park-chip">{_park_chip("")}</template>'
        + f'<script type="application/json" id="park-scenes">{_json_for_script(landmarks())}</script>'
        + _field("park_add", "Add a park", add,
                 "Any park on ThemeParks.wiki: start typing and pick it from the list. It goes on the end; "
                 "the arrow moves a park earlier." if park_names else
                 "The list of parks hasn't loaded yet (the board needs the internet for it): type the name "
                 "exactly as ThemeParks.wiki has it.")
    ), "pin")

    rows = trip_rows(config)
    preview, counting_to = _countdown_preview(config, countdown.get("enabled", False), today)
    trips = _section("trips", "Trip countdown", "Days to go until your next trip, between the parks.", (
        preview
        + _switch("trips_enabled", "Show the countdown", countdown.get("enabled", False))
        + '<div class="trips" id="trip-list">'
        + "".join(_trip(i, *row, on_board=_same_trip(row, counting_to)) for i, row in enumerate(rows))
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
    volume = sound.get("volume", "")
    volume_control = (
        '<div class="volume">'
        f'<input type="range" id="volume_slider" class="js-only" min="0" max="100" '
        f'value="{_attr(volume if volume != "" else DEFAULT_VOLUME)}" aria-label="Volume slider" hidden>'
        + _input("sound_volume", volume, "number", f' min="0" max="100" inputmode="numeric" placeholder="{DEFAULT_VOLUME}"')
        # Plain buttons, not submits: Enter in any field must still mean Save.
        + '</div><div class="below buttons js-only" hidden>'
        f'<button type="button" class="secondary" name="volume_action" value="set">{icon("check")}Set volume</button>'
        f'<button type="button" class="secondary" name="volume_action" value="test">{icon("sound")}Play test sound'
        '</button></div>'
        '<p class="hint volume-status" id="volume-status" role="status" aria-live="polite"></p>')
    sound_html = _section("sound", "Sound", "The fireworks music, from a speaker on the board.", (
        _switch("sound_enabled", "Play the fireworks music", sound.get("enabled", False),
                "Needs a speaker, and the music in the sounds folder.")
        + _field("sound_device", "Speaker", speaker)
        + _field("sound_volume", "Volume", volume_control,
                 f"0 to 100, set before each show. Blank is {DEFAULT_VOLUME}: louder can draw more power than "
                 "the Pi can spare and slow the show down. Set volume saves just this, with no restart; "
                 "Play test sound plays a few seconds at it without saving.")
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
    chosen_model = config.get("pi_model") if config.get("pi_model") in cli.MODEL_DEFAULTS else cli.AUTO
    blanks = (panel.blanks.get(panel.auto_model if chosen_model == cli.AUTO else chosen_model, {})
              if panel else {})
    display = _section("display", "Display", "How bright the LED panel is, all day or by the time of day.", (
        _brightness_previews()
        + _field(f"matrix_{BRIGHTNESS}", "Brightness",
               _input(f"matrix_{BRIGHTNESS}", "" if brightness is None else brightness, "number",
                      f'{level} placeholder="{_attr(blanks.get(BRIGHTNESS, "Default"))}" data-key="{BRIGHTNESS}"'),
               "1 to 100. Blank uses the Pi model's (see Panel). A schedule, when on, takes over from it.")
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
    castle = landmarks().get(CASTLE_KEY)
    show_scene = (f'<div class="previews">{_led(castle, "The castle on the board")}<p class="hint">Each show plays '
                  "over the board's castle when that show starts in the park, by ThemeParks.wiki's showtimes.</p></div>"
                  if castle else "")
    shows = _section("shows", "Fireworks shows", "What plays when each show starts in the park.", (
        show_scene
        + f'<div class="shows">{show_rows}</div>'
        + _notice("info", "<strong>Default</strong> plays the castle fireworks for five minutes. <strong>V1</strong> "
                          "and <strong>V2</strong> play the whole show in time with its music. <strong>Test</strong> "
                          "plays a show once each time the app starts; turn it off when you're done.")
    ), "sparkle")

    cast = sorted(character_label(n) for n in surprise_names())
    cast_list = (f'<ul class="cast" aria-label="The characters">{"".join(f"<li>{escape(n)}</li>" for n in cast)}</ul>'
                 if cast else "")
    surprises = _section("surprises", "Surprise characters",
                         "Who now and then drops in between ride screens and park titles, and how often.", (
        cast_list
        + f'<a class="btn secondary" href="/surprises">{icon("sparkle")}<span>Choose '
          f'{f"from all {len(cast)} characters and their" if cast else "characters and"} chances</span></a>'
    ), "sparkle")

    settings = {key: (help_text, options, switch) for key, help_text, options, switch, _ in cli.matrix_settings()}
    panel_fields = "".join(_matrix_field(key, label, *settings[key], matrix.get(key), blanks.get(key, "Default"))
                           for key, label in PANEL_SETTINGS.items())
    model_and_size = ""
    if panel:
        for_script = {"auto": panel.auto_model, "blanks": panel.blanks}
        model_and_size = (
            _field("pi_model", "Pi model", _options("pi_model", panel.models, chosen_model),
                   "Which Raspberry Pi drives the panel: it sets the defaults below. Automatic is the one "
                   "this board reports.")
            + _field("panel_size", "Panel size", _options("panel_size", panel.sizes, panel_size(matrix)),
                     "Columns x rows, as on the panel's label.")
            + f'<script type="application/json" id="panel-blanks">{_json_for_script(for_script)}</script>')
    panel_html = _section("panel", "Panel", "Which Pi and panel this is, and which way up it's mounted.", (
        _rotation_preview()
        + model_and_size
        + _notice("info", "Each setting left blank is the Pi model's default, shown greyed out. Set one to "
                          "customise this board, like Rotation for a panel mounted upside down; clear it to go back.")
        + panel_fields
    ), "board")
    advanced_fields = "".join(_matrix_field(key, key.removeprefix("led_").replace("_", " ").capitalize(), help_text,
                                            options, switch, matrix.get(key), blanks.get(key, "Default"))
                    for key, (help_text, options, switch) in settings.items()
                    if key != BRIGHTNESS and key not in PANEL_SETTINGS and key not in SIZE_SETTINGS)
    advanced = (
        '<details class="card" id="advanced"><summary class="card-head">'
        f'<span class="card-icon">{icon("sliders")}</span><div><h2>Advanced</h2>'
        '<p>Panel hardware. Most boards never need these.</p></div>'
        f'<span class="chev">{icon("chevron")}</span></summary><div class="card-body">'
        + _notice("warn", "The wrong panel settings can leave the board dark or flickering. Blank leaves each one to "
                          "the Pi model's default. Size, rotation and timing are in Panel.")
        + advanced_fields
        + "</div></details>")
    testing = _section("testing", "Testing", "For checking the board; turn them off when you're done.", (
        _switch("debug", "Debug logging", config.get("debug", False), "More detail in the board's log.")
        + _field("force_surprise", "Surprise on every ride screen",
                 _options("force_surprise", [("", "None")] + sorted(
                     ((n, character_label(n)) for n in surprise_names()), key=lambda o: o[1]),
                     config.get("force_surprise") or ""),
                 "Plays that character on every ride screen, for checking it on the board. "
                 "Set it back to None when you're done.")
    ), "flask")

    toc = "".join(f'<a href="{"/surprises" if sid == "surprises" else "#" + sid}">{icon(glyph)}{escape(title)}</a>'
                  for sid, title, glyph in SECTIONS)
    mode = ("warn", "Setup mode") if hotspot else ("good", "Signed in")
    body = (
        _topbar(board, mode, sign_out=not hotspot)  # on the hotspot there's no PIN session to end
        + f'<div class="shell"><nav class="toc" aria-label="Sections">{toc}</nav><main>'
        + '<div class="page-head"><h1>Settings</h1><p>Changes are checked, saved to the board\'s config.json, '
          'and the app restarts to use them.</p></div>'
        + top
        # First, and outside the settings form: its buttons post forms of their own.
        + (f'<div class="stack before">{_board_now_card(now) if now else ""}'
           f'{updates_card(updates, started) if updates else ""}</div>' if updates or now else "")
        + f'<form method="post" action="/save" id="settings"><div class="stack">'
          f'{live}{weather_html}{phone}{park_html}{trips}{sound_html}{panel_html}{display}{shows}{surprises}{testing}{advanced}</div>'
        + '<div class="savebar"><div class="savebar-in"><div class="status" id="save-status"><span class="dot"></span>'
          '<span>Saved keys stay as they are unless you replace them</span></div>'
          f'<button type="submit" class="primary" id="save">{icon("save")}<span>Save and restart</span></button>'
          '</div></div></form></main></div>')
    return document("Board settings", body, SCRIPT)


def _when(at):
    """A time on the board's clock, 12-hour: "04 Nov 7:05 PM"."""
    try:
        moment = time.localtime(float(at))
    except (TypeError, ValueError, OverflowError, OSError):
        return "?"
    return (time.strftime("%d %b ", moment) + f"{moment.tm_hour % 12 or 12}:{moment.tm_min:02d} "
            + ("PM" if moment.tm_hour >= 12 else "AM"))


def _sentence(text):
    """text as a sentence: a capital (unless it starts with a commit's sha) and a full stop."""
    text = str(text or "").strip()
    if not re.match(r"[0-9a-f]{7,40}\b", text):
        text = text[:1].upper() + text[1:]
    return escape(text + ("" if text.endswith(".") else "."))


def _short(sha):
    return escape(str(sha)[:7]) if sha else "?"


def _post(action, label, glyph, busy, kind="secondary", fields="", confirm=None, disabled=False):
    """A one-button form of the Updates card. busy: the button's text while it works."""
    extra = f' data-confirm="{_attr(confirm)}"' if confirm else ""
    return (f'<form method="post" action="{action}" data-busy="{_attr(busy)}"{extra}>{fields}'
            f'<button type="submit" class="{kind}"{" disabled" if disabled else ""}>{icon(glyph)}'
            f'<span>{escape(label)}</span></button></form>')


# What's in an update: at most this many of its pull requests, then "and N more".
CHANGES_SHOWN = 12


def _pr_link(number):
    return f'<a href="https://github.com/{REPO}/pull/{int(number)}" target="_blank" rel="noopener">#{int(number)}</a>'


def _beta_name(version, sha):
    """A Beta by its number when it's exactly one (v2.1.5-beta: "Beta 2.1.5"), else by its commit."""
    number = beta_number(version)
    return f"Beta {escape(number)}" if number else f'Beta <span class="mono">{_short(sha)}</span>'


def _installed_name(view):
    """What's installed, as the card names it: a Beta by its number or commit, else its version."""
    if view.get("installed_channel") == BETA:
        return _beta_name(view["version"], view["sha"])
    return escape(str(view["version"]))


def _found_name(found):
    """What a check found (or an update is installing), as the card names it: develop-beta's tip by
    its number or commit, a release by its version, else its ref and commit."""
    if found.get("ref") == BETA_BRANCH:
        return _beta_name(found.get("version"), found.get("sha"))
    if found.get("version"):
        return escape(str(found["version"]))
    return f'{escape(str(found.get("ref")))} {_short(found.get("sha"))}'


def _changes(view, found):
    """What an update brings (updates.Updates.details): from what to what, its pull requests (linked
    to GitHub) with their release notes under their titles, and whether pip runs. "" if the check
    couldn't say. Pull requests whose notes say None go in one "Behind the scenes" line."""
    changes = found.get("changes")
    if changes is None:
        return ""
    head = f"<strong>{_installed_name(view)} \u2192 {_found_name(found)}</strong>"
    shown, hidden = [], []
    for number, title, *rest in changes:
        notes = rest[0] if rest else None
        if notes == [] and number:
            hidden.append(number)
        else:
            shown.append((number, title, notes))
    items = ""
    for number, title, notes in shown[:CHANGES_SHOWN]:
        tag = _pr_link(number) if number else '<span class="mono">\u2022</span>'
        notes = "".join(f'<span class="hint note">{escape(str(note))}</span>' for note in notes or ())
        items += f"<li>{tag}<span>{escape(str(title))}{notes}</span></li>"
    more = len(shown) - CHANGES_SHOWN
    if more > 0:
        items += f'<li><span class="mono"></span><span class="hint">and {more} more</span></li>'
    if hidden:
        items += (f'<li><span class="mono"></span><span class="hint">Behind the scenes, nothing you\'d notice: '
                  f'{", ".join(_pr_link(number) for number in hidden)}</span></li>')
    packages = ('<p class="hint">Its Python packages change too, so it takes longer: up to hours on a Pi Zero.</p>'
                if found.get("packages") else "")
    return (f'<div class="changes"><p>{head}</p>'
            + (f'<ul aria-label="What\'s in it">{items}</ul>' if items else "")
            + f"{packages}</div>")


def updates_card(view, started=None):
    """The Updates card, from updates.Updates.view(): what's installed, how the last update went, a
    channel to check, and Update now (after a check found one) and Roll back."""
    running = view["running"]
    top = ""
    if started == STARTED and not running:
        top += _notice("info", "<strong>Started.</strong> It may be finished already: reload the page to see.")
    elif started == BUSY:
        top += _notice("warn", "An update or rollback is already running: this one didn't start.")
    elif started == START_FAILED:
        top += _notice("bad", "<strong>Couldn't start it.</strong> The board's log says why.", "alert")
    if running:
        to = view.get("to") or {}
        target = f' \u00b7 Updating to {_found_name(to)}' if to.get("ref") else ""
        top += _notice("info", f'<strong id="update-phase">{escape(view["status"] or "")}</strong>'
                               f'<span id="update-running"></span>{target}'
                               + _steps(view.get("step"))
                               + '<p>The board restarts as it updates, and so does this '
                               'page: it comes back by itself in a few minutes (sign in again if it asks). Don\'t change '
                               'settings until it\'s done: a rollback puts config.json back as it was before.</p>'
                               + _changes(view, to))
    elif view["phase"] in UNFINISHED:
        top += _notice("warn", f"<strong>An update stopped midway</strong> (at {escape(view['phase'])}). Roll it back "
                               "below, or restart the board: it rolls back at boot.", "alert")
    elif view["phase"] == ROLLBACK_FAILED:
        top += _notice("bad", "<strong>The last rollback failed.</strong> Try Roll back again, or over SSH: "
                              "<code>sudo lll-rollback</code>.", "alert")
    outcome = view.get("outcome")
    if outcome and not running:
        name = {"update": "update", "rollback": "rollback", "recover": "rollback at boot"}.get(outcome.get("command"),
                                                                                              "update")
        top += _notice("good" if outcome.get("ok") else "bad",
                       f"<strong>Last {name}</strong> ({_when(outcome.get('at'))}): {_sentence(outcome.get('message'))}",
                       "status" if outcome.get("ok") else "alert")

    where = f"on {escape(view['branch'])}" if view["branch"] else "as installed by an update"
    if view.get("installed_channel") == BETA:
        installed = (f'<p><strong>{_installed_name(view)}</strong></p><p class="hint">A Beta (test) version '
                     f'{where}, newer than release {escape(release_of(view["version"]))}</p>')
    else:
        installed = (f'<p><strong>{escape(str(view["version"]))}</strong> <span class="mono">{_short(view["sha"])}'
                     f'</span></p><p class="hint">{where}</p>')
    channel = view["channel"]
    check_form = (f'<form method="post" action="/update/check" data-busy="Checking\u2026" class="add-row">'
                  + _options("channel", [(RELEASES, "Releases"), (BETA, "Beta")], channel)
                  + f'<button type="submit" class="secondary"{" disabled" if running else ""}>{icon("refresh")}'
                    '<span>Check</span></button></form>')
    body = (top
            + _field("update_installed", "Installed", installed)
            + _field("channel", "Check for a newer version", check_form + ("" if running else check_result(view)),
                     "Releases: the newest release. Beta: the newest test version whose checks passed. "
                     "Never a downgrade: from Beta, Releases waits for a release newer than what's installed."))
    old = view.get("from")
    if old and view["phase"] not in ("idle", "rolled_back"):
        # The exact commit (and branch) from before the update, whatever channel is picked above.
        # Plain text: the hint escapes it.
        # A point taken before rollback points had a channel: on develop-beta, it was a Beta.
        back_to = name_of({**old, "channel": BETA} if old.get("branch") == BETA_BRANCH else old) \
            + (f" on {old['branch']}" if old.get("branch") else "")
        body += _field("update_rollback", "Roll back",
                       _post("/update/rollback", "Roll back", "undo", "Rolling back\u2026",
                             confirm="Roll back the last update? This also puts back config.json as it was "
                                     "before it, undoing settings saved since.", disabled=running),
                       f"Back to {back_to}, as before the last update. This also puts back config.json as it "
                       "was then, undoing settings saved since.")
    return _section("updates", "Updates", "This board's version, and newer ones from GitHub.", body, "refresh")


def _steps(step):
    """An update's STEPS, step (an index) the one it's on; hidden for a rollback (step None)."""
    items = ""
    for i, text in enumerate(STEPS):
        if step is not None and i < step:
            items += f'<li class="done">{escape(text)}</li>'
        elif i == step:
            items += f'<li class="now" aria-current="step">{escape(text)}</li>'
        else:
            items += f"<li>{escape(text)}</li>"
    return f'<ol class="steps" id="update-steps" aria-label="Steps"{" hidden" if step is None else ""}>{items}</ol>'


def _run_name(name):
    """A CI run's name in words: "test (3.11)" is "Tests on Python 3.11"."""
    found = re.fullmatch(r"test \((\d+\.\d+)\)", name)
    return f"Tests on Python {found.group(1)}" if found else name


def _waiting(runs, when):
    """A newer Beta held back by its CI (runs: [name, RUNNING/PASSED/FAILED] each), as a notice
    with one row per run, in the update steps' style."""
    states = [state for _, state in runs]
    if FAILED in states:
        headline, after = "A newer Beta didn't pass its tests", "It won't be installed; the next Beta that passes can be."
    elif runs:
        headline = "A newer Beta is being tested"
        after = f"It can be installed once {'both pass' if len(runs) == 2 else 'they all pass' if len(runs) > 2 else 'it passes'}."
    else:
        headline, after = "A newer Beta hasn't been tested yet", "It can be installed once its tests pass."
    rows = ""
    for name, state in sorted(runs):
        css = {RUNNING: ' class="now"', PASSED: ' class="done"', FAILED: ' class="failed"'}.get(state, "")
        rows += f"<li{css}>{escape(_run_name(name))}: {escape(state)}</li>"
    steps = f'<ol class="steps" aria-label="Tests">{rows}</ol>' if rows else "<br>"
    return _notice("info", f"<strong>{headline}.</strong>{when}{steps}" + f'<span class="when">{after}</span>')


def check_result(view):
    """What the last check found (updates.Updates.view()'s "check"), under the Check button: an
    update with Update now, the newest already, or why it can't; while the page's own check runs,
    a placeholder its script replaces. "" when there's nothing to say."""
    check = view.get("check")
    if not check:
        if not view.get("auto_check"):
            return ""
        name = "Beta" if view["channel"] == BETA else "Releases"
        return (f'<div id="update-check" data-auto="{_attr(view["channel"])}">'
                + _notice("info", f"Checking {name} for a newer version\u2026") + "</div>")
    name = "Beta" if check["channel"] == BETA else "Releases"
    when = f' <span class="when">\u00b7 checked {_when(check["at"])}</span>'
    if check["result"] == WOULD_UPDATE:
        found = (_notice("new", f"<strong>Update available on {name}: {_found_name(check)}</strong>{when}"
                                + _changes(view, check))
                 + '<div class="below">'
                 + _post("/update/start", "Update now", "refresh", "Starting\u2026", "primary",
                         f'<input type="hidden" name="channel" value="{_attr(check["channel"])}">')
                 + '</div><p class="hint">A few minutes, longer if its Python packages change. If the new '
                   'version doesn\'t work within 5 minutes, the board rolls back by itself.</p>')
    elif check["result"] == CURRENT:
        found = _notice("good", f"<strong>Up to date:</strong> this is the newest on {name}.{when}"
                                f'<br><span class="when">{_sentence(check["message"])}</span>')
    elif check["result"] == WAITING and isinstance(check.get("runs"), list):
        found = _waiting(check["runs"], when)
    elif check["result"] == WAITING:
        found = _notice("info", f"<strong>Up to date for now:</strong> a newer {name} version isn't ready yet."
                                f'{when}<br><span class="when">{_sentence(check["message"])}</span>')
    else:
        found = _notice("warn", f"<strong>Can't update right now:</strong> {_sentence(check['message'])}{when}")
    return f'<div id="update-check">{found}</div>'


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
        status = _notice("good", f"The PIN is on the board for the next {max(1, round(shown_s / 60))} "
                                 f"minute{'s' if shown_s > 90 else ''}.")
    body = (
        _topbar(board)
        + f'<div class="center"><div class="card auth signin"><div class="auth-hero">'
          f'<img src="{ICON}" alt="" width="76" height="76"><div>{wordmark()}</div></div>'
          '<h1>Sign in to this board</h1><p>To change this board\'s settings, type in the PIN it shows.</p>'
        + status
        + '<div class="step"><span class="step-n">1</span><div class="step-body"><strong>Show a PIN</strong>'
          f'<p>It appears on the LED board for two minutes{" and can go to your phone" if phone else ""}.</p>'
          f'<div class="buttons"><form method="post" action="/pin/show"><button type="submit" class="secondary">'
          f'{icon("board")}Show a PIN on the board</button></form>'
        + (f'<form method="post" action="/pin/send"><button type="submit" class="secondary">{icon("phone")}'
           'Send the PIN to my phone</button></form>' if phone else "")
        + '</div></div></div>'
        + '<div class="step"><span class="step-n">2</span><div class="step-body"><label for="pin"><strong>Type it in'
          '</strong></label><p>You stay signed in on this browser for an hour.</p>'
          '<form method="post" action="/pin"><input type="text" id="pin" name="pin" class="pin" inputmode="numeric" '
          'autocomplete="one-time-code" pattern="[0-9]*" maxlength="8" required autofocus aria-label="PIN">'
          '<button type="submit" class="primary block">Sign in</button></form></div></div>'
        + "</div></div>")
    return document("Sign in · Board settings", body)
