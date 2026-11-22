"""The "On the board now" card: what the app's heartbeat says."""
from html import escape

from settings_page.board_status import NONE, QUIET, SHOW, ago
from settings_page.markup import CASTLE_KEY, _led, landmarks


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
