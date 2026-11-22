"""The Updates card: what is installed, how the last update went, a channel to check, Update now and Roll back.
Its back end is settings_page/updates.py; the card only draws what updates.Updates.view() says."""
import re
import time
from html import escape

from self_update.github import FAILED, PASSED, REPO, RUNNING
from self_update.state import ROLLBACK_FAILED, UNFINISHED
from self_update.update import (
    BETA,
    BETA_BRANCH,
    CURRENT,
    RELEASES,
    WAITING,
    WOULD_UPDATE,
    beta_number,
    name_of,
    release_of,
)
from settings_page.markup import _attr, _field, _notice, _options, _section, icon
from settings_page.updates import BUSY, START_FAILED, STARTED, STEPS


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


def _post(action, label, glyph, busy, kind="secondary", fields="", confirm=None, disabled=False):  # noqa: PLR0913
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
    check_form = ('<form method="post" action="/update/check" data-busy="Checking\u2026" class="add-row">'
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
