"""Updates the board from GitHub, with rollback (ROADMAP #17): python3 -m self_update (see __main__).

github.py asks GitHub what's newer, board.py does the git/pip/systemctl work, state.py keeps the
rollback point in /var/lib/lll-update, update.py decides. Its own package, not part of the app or
the settings page, because an update restarts both. A version without it can't be updated to:
the way back would be gone.
"""
