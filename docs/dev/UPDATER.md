# Releases and the updater

<!-- Moved from CLAUDE.md on 2026-11-12 so it loads only when needed. Keep it current with the code it describes. -->

Read before changing `self_update/`, `.github/workflows/`, `tools/auto_tag.py`, `version.py` or the settings page's Updates card.

```sh
# Release: merge a develop-beta -> main PR. auto-tag.yml (tools/auto_tag.py) tags main's merge vX.(Y+1).0
# and makes the GitHub release; each PR merged into develop-beta gets vX.Y.N-beta. Tags only, no commits.

# Update a board from GitHub, with rollback (ROADMAP #17): status (sudo: state.json is root's), check (changes nothing), update, rollback, recover
venv/bin/python3 -m self_update check [--channel beta]
sudo venv/bin/python3 -m self_update update [--channel beta]
```

- **Updater** (`self_update/`, ROADMAP #17; not `updater/`, which is live data): `update.py` decides (channels `releases`, from `MIN_RELEASE` up, never a downgrade, and `beta`, develop-beta's tip once its CI passed, which is why coverage.yml runs on develop-beta pushes; pre-flight; rollback point; health; rollback), `board.py` runs git (as the checkout's owner), pip, `LLL-install.sh -p -m -w [--skip-requirements]` and systemctl through one injectable `run`, `state.py` keeps `/var/lib/lll-update/state.json` (phases; `UNFINISHED` ones block the next update; the rollback point's `channel`, from `update.channel_of`, names a Beta "Beta 2.1.5" or "Beta <sha>" via `name_of`), `github.py` the API, `release_notes.py` a PR's `## Release notes` (from `.github/pull_request_template.md`; `release-notes.yml` fails a PR without them, "None" allowed): the repo's merge commits are "<PR title> (#N)" with the description as the body (GitHub's PR_TITLE + PR_BODY, since 2026-11-04; before, "Merge pull request #N from owner/branch"), so `Board.what_changed` reads titles and notes from git, no API call; a merge that brings in other PRs' merges is a release and is skipped. Merging with `gh pr merge`, pass `--body` with the description. Versions are tags (`version.py` reads `git describe`; `update.installed_number` counts 2.1.5-beta as 2.1.5, `parse_version` takes only exact releases): the card names a Beta "Beta 2.1.5" when it's exactly that tag, else "Beta <sha>". Health: the app writes `utils/heartbeat.py`'s `/run/lll-health` after the intro and each ride screen (not just ride screens: closed parks at night show none), and with the show and its end while one plays (no update mid-show); the root conftest points it at a temp file. A version without `self_update/` is never installed: the way back would be gone. Backstops, from `board-setup.sh`'s `setup_updater` (also in `--wifi-setup-only`, so `LLL-install.sh` boards get them): `lll-update-recover.service`, a boot oneshot running `self_update recover` (rolls back an `UNFINISHED` phase; not ordered before the app, since rolling back restarts it), and `sudo lll-rollback`.

## Gotchas

- An update runs the *new* version's `LLL-install.sh` but the *old* version's `self_update`, so a fix that must reach boards with a broken updater goes in the installer. Its git calls run as root in the user's checkout, from systemd with no `SUDO_UID`: pass `-c safe.directory="$PWD"` or git stops with "dubious ownership".
- `self_update` imports nothing from `settings_page` (import-linter contract); its failure alert uses `utils/pushover.py`, imported at the top of `update.py` so a failed rollback can still alert.
