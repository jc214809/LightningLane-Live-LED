"""The "Board status" card: what the app's heartbeat says. Text only: the page never shows the board's screen,
which would mean copying frames off the display thread."""

from html import escape

from settings_page.board_status import NONE, QUIET, SHOW, ago


def _fact(term, value):
    return f"<div><dt>{term}</dt><dd>{value}</dd></div>"


def _board_now_card(now):
    """The "Board status" card, from board_status.BoardNow."""
    facts, note = [], ""
    if now.state == NONE:
        beat = '<span class="beat none">No word yet</span>'
        note = (
            "The app hasn't written its heartbeat since the board started: it may still be starting, or not be running."
        )
    elif now.state == QUIET:
        beat = '<span class="beat quiet">Quiet</span>'
        facts.append(_fact("Last screen", ago(now.age_s)))
        note = "No screen for over 5 minutes: the app may have stopped. Saving restarts it."
    elif now.state == SHOW:
        beat = '<span class="beat">Showtime</span>'
        facts.append(_fact("Playing", escape(now.show)))
    else:
        beat = '<span class="beat">Running</span>'
        facts.append(_fact("Last screen", ago(now.age_s)))
    if now.version:
        facts.append(_fact("Version", escape(now.version)))
    facts_html = f'<dl class="facts">{"".join(facts)}</dl>' if facts else ""
    note_html = f'<p class="now-note">{note}</p>' if note else ""
    return (
        f'<section class="card board-now" aria-labelledby="now-title"><div class="now-head">'
        f'<h2 id="now-title">Board status</h2>{beat}</div>{facts_html}{note_html}'
        "<p>From the app's heartbeat, as of when this page loaded.</p></section>"
    )
