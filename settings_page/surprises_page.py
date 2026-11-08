"""The Surprise characters page (/surprises): which characters may visit, how often, and on which rides.
Its own page and form, apart from the main settings form (form.apply_surprises saves it)."""
import os
from html import escape

from settings_page.form import character_label, default_rides, percent_text, surprise_rows
from settings_page.page import (_attr, _json_for_script, _notice, _section, _switch, _switch_input, _topbar, document,
                                icon, notices)
from utils.config import surprise_settings
from utils.surprises import SURPRISES

# (heading, how the column sorts, first direction): a click on a heading sorts by it, a second click reverses.
COLUMNS = (("On", "on", "descending"), ("Character", "name", "ascending"),
           ("% of all ride screens", "num", "descending"), ("% on their own rides", "num", "descending"),
           ("Rides", "rides", "descending"))

# The page's script lives in surprises.js (so an editor and `node --check` treat it as JavaScript).
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "surprises.js"), encoding="utf-8") as _f:
    SCRIPT = _f.read()


def _chance_cell(name, kind, default, saved):
    """A percent box, blank for the default (shown greyed out). saved: the chance set on this page, as a
    fraction, or None."""
    field = f"{kind}_{name}"
    where = "of ride screens" if kind == "chance" else "on its own rides"
    return (f'<td><input type="number" id="{field}" name="{field}" value="{"" if saved is None else percent_text(saved)}" '
            f'min="0" max="100" step="any" inputmode="decimal" placeholder="{_attr(default)}" '
            f'aria-label="{_attr(character_label(name))}, % {where}"></td>')


def _rides_cell(name, shown):
    """The Rides cell: the names of the rides the character visits and, at the right edge, a plus button that opens
    the panel under the row. shown: the ride names to say, one per line."""
    text = "".join(f'<span class="ride">{escape(ride)}</span>' for ride in shown) or "No rides"
    return (f'<td><div class="rides-cell"><span class="ride-names{"" if shown else " none"}">{text}</span>'
            f'<button type="button" class="secondary add-rides" aria-expanded="false" '
            f'aria-label="Add rides for {_attr(character_label(name))}" title="Add rides">{icon("plus")}</button></div></td>')


def _ride_panel(name, chosen, known):
    """The row under a character that holds its ride picker, hidden until Add: the page's script builds each park's
    checkboxes side by side when it first opens, with the ticked rides posted as hidden inputs until then. known: the
    marker value that says those are the rides to save, "saved" if they were saved, else "1" (an imported page, whose
    rides nobody has opened a picker to confirm, would otherwise lose them); "" when the ride list hasn't loaded and
    they're only the defaults, which can't be named yet."""
    marker = f'<input type="hidden" name="rides_set_{name}" value="{known}">' if known else ""
    hidden = marker + "".join(f'<input type="hidden" name="rides_{name}" value="{_attr(ride)}">' for ride in chosen)
    return f'<tr class="ride-row" hidden><td colspan="5"><div class="ride-pick">{hidden}</div></td></tr>'


def _row(row, on, settings, chosen, shown, known):
    label = character_label(row.name)
    switch = _switch_input(f"surprise_{row.name}", on, f' aria-label="Let {_attr(label)} visit"')
    return (f'<tr data-name="{_attr(row.name)}" data-label="{_attr(label)}"><td>{switch}</td><td>{escape(label)}</td>'
            + _chance_cell(row.name, "chance", row.anywhere, settings.chances.get(row.name))
            + _chance_cell(row.name, "ride_chance", row.own, settings.ride_chances.get(row.name))
            + _rides_cell(row.name, shown) + "</tr>"
            + _ride_panel(row.name, chosen, known))


def _import_notices(problems, imported):
    """What an Import did: refused (with why), or filled the page and left out these names."""
    if problems:
        items = "".join(f"<li>{escape(p)}</li>" for p in problems)
        return _notice("bad", f"<strong>Nothing imported.</strong> The pasted settings have problems:<ul>{items}</ul>",
                       "alert")
    left = (f" Left out because this board's version doesn't have them: {escape(', '.join(imported))}."
            if imported else "")
    return _notice("good", "<strong>Imported.</strong> The page now shows the pasted settings, which are "
                           f"<strong>not saved yet</strong>: look them over, then press Save and restart.{left}")


def _share_bar():
    """Export and Import, to move these settings to another board: one click each, no boxes. Export copies every
    setting on the page; Import reads the clipboard (or waits for a paste). See the page's script."""
    return ('<div class="share"><button type="button" class="secondary" id="export-btn" '
            'title="Copy every setting on this page">Export</button>'
            '<button type="button" class="secondary" id="import-btn" '
            'title="Paste settings copied with Export on another board">Import</button>'
            '<span class="share-status" id="share-status" role="status" aria-live="polite"></span></div>')


def surprises_page(data, problems=(), saved=None, board=None, hotspot=None, rides=None, imported=None):
    """The page, filled from surprises.json (data). hotspot: the setup hotspot's name when this browser is on it.
    rides: {park: [ride names]} for the ride pickers, from ride_names.RideNames; None or {} before it has loaded.
    imported: None for an ordinary page; a list of the names an Import left out when the page is filled from pasted
    settings (not yet saved); False when an Import was refused (the page is shown as it was)."""
    settings = surprise_settings(data)
    characters = data.get("characters") if isinstance(data.get("characters"), dict) else {}
    loaded = any((rides or {}).values())

    def chosen(name):
        """(the rides ticked, the rides to say, the marker to post with them): those saved, else the character's
        default ones. Until the ride list is known the defaults can't be ticked, so they're said by the pieces of
        their names, and not posted."""
        entry = characters.get(name) if isinstance(characters.get(name), dict) else {}
        if isinstance(entry.get("rides"), list):
            saved = [r for r in entry["rides"] if isinstance(r, str)]
            return saved, saved, "saved"
        ticked = default_rides(name, rides)
        return ticked, ticked if loaded else surprise_row_defaults[name], "1" if loaded else ""
    surprise_row_defaults = {row.name: row.rides for row in surprise_rows()}
    rows = "".join(_row(row, row.name not in settings.off, settings, *chosen(row.name))
                   for row in sorted(surprise_rows(), key=lambda r: character_label(r.name).lower()))
    heads = "".join(f'<th scope="col" aria-sort="none" data-sort="{kind}" data-first="{first}">'
                    f'<button type="button">{escape(text)}</button></th>' for text, kind, first in COLUMNS)
    shares = [(row.name, settings.chance(row.name, float(row.anywhere) / 100) * 100) for row in surprise_rows()]
    total = sum(share for _, share in shares)
    ticked = sum(share for name, share in shares if name not in settings.off)
    over = ' class="over"' if total > 100 else ""
    foot = ('<tfoot><tr><td></td><th scope="row">Total</th><td>'
            f'<strong id="total-all"{over}>{percent_text(total / 100)}%</strong>'
            f'<div class="total-sub" id="total-ticked">{percent_text(ticked / 100)}% from the ticked characters</div>'
            "</td><td></td><td></td></tr></tfoot>")
    card = _section("characters", "Characters", "Untick a character to stop them visiting.", (
        _switch("surprises_enabled", "Surprise characters", settings.enabled,
                "Off keeps every screen change a plain wipe.")
        + f'<div class="table-wrap"><table class="odds"><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody>{foot}</table></div>'
        + _notice("info", "Click a heading to sort by it. A chance left blank uses the default shown in grey. "
                          "<strong>% of all ride screens</strong> is the chance a character drops in on any ride; "
                          "<strong>% on their own rides</strong> is the chance on the rides in the <strong>Rides</strong> "
                          "list: press <strong>Add</strong> to see every park's rides side by side and tick the ones the "
                          "character should visit (the rides a character already visits are ticked). The <strong>Total</strong> "
                          "at the bottom adds up the first column (the defaults come to "
                          f"{percent_text(sum(SURPRISES.values()))}%) and can't pass 100%. A character you untick is "
                          "replaced by the plain wipe, not by another character, so the ticked characters' total is "
                          "how often a surprise really plays.")
    ), "sparkle")
    mode = ("warn", "Setup mode") if hotspot else ("good", "Signed in")
    body = (
        _topbar(board, mode, sign_out=not hotspot)
        + '<div class="shell"><nav class="toc" aria-label="Sections">'
          f'<a href="/">{icon("chevron")}Back to settings</a></nav><main>'
        + '<div class="page-head"><h1>Surprise characters</h1><p>Who drops in between ride screens, how '
          "often, and on which rides. Saved to the board's surprises.json; the app restarts to use it.</p></div>"
        + (_import_notices(problems, imported) if imported is not None else notices(problems, saved))
        + _share_bar()
        + f'<form method="post" action="/surprises" id="settings"><div class="stack">{card}</div>'
        + '<div class="savebar"><div class="savebar-in"><div class="status"><span class="dot"></span>'
          "<span>Blank chances use the defaults</span></div>"
          f'<button type="submit" class="primary" id="save">{icon("save")}<span>Save and restart</span></button>'
          "</div></div></form>"
        + f'<script type="application/json" id="ride-list">{_json_for_script(rides or {})}</script></main></div>')
    return document("Surprise characters", body, SCRIPT)
