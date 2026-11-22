# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Keep this file short: it loads in every session.** Feature detail goes in docs/dev/<topic>.md; this file gets one pointer line (see [Topic notes](#topic-notes)). `tests/test_claude_md.py` fails above 16,000 characters, on a pointer to a missing file, or on a `docs/dev` note not listed here. Keep the rule a story produced; put the story in the topic note. Planned work: `ROADMAP.md`.

## Commands

```sh
# Run all tests (in parallel, as CI does; plain pytest runs them one at a time) / one file / one test
pytest -n auto
pytest tests/api/test_disney_api.py
pytest tests/api/test_disney_api.py::test_function_name

# Run the app in emulator mode (no hardware); --led-rows=64 for the 64x64 board
./disney.py --emulated --led-cols=64 --led-rows=32

# Check version (git describe: 2.1.0, 2.1.5-beta, 2.1.5-beta-3-g1a2b3c4; git fetch --tags if stale)
python3 version.py

# Install for development (the app plus the test tools), on Python 3.11 like the boards
uv venv --python 3.11 .venv && uv pip install --python .venv -r requirements-dev.txt
```

Generated files: a test fails until you rerun the builder after changing what it reads: `tools/build_sprite_editor.py` (any character art), `tools/build_settings_art.py` (a park landmark), `tools/build_merida_poses.py` (Merida's poses or art), `tools/draw_wiring.py` (the wiring diagrams). The other tools' commands are in the topic notes that use them.

- **Python:** 3.11 is the target everywhere (`.python-version`, pyproject's `requires-python`, CI) because it's Raspberry Pi OS Bookworm's. CI also runs 3.13, the next OS's (Trixie). When the boards move, raise all three together.
- **Requirements:** edit `requirements.txt` (what the boards need) and pyproject.toml's `dependencies` by hand and keep them in sync; test tools go in `requirements-dev.txt`. Don't run pipreqs: it rewrites requirements.txt from imports and drops the caps and comments.

## Branches and releases

PRs go into `develop-beta`; a release is a `develop-beta` → `main` PR. Every PR needs a `## Release notes` section (`.github/pull_request_template.md`; "None" allowed), read from merge commit bodies, so merge with the PR description as the body (`gh pr merge --merge --body ...`). Each merge is auto-tagged (`vX.Y.N-beta`, main's `vX.(Y+1).0`); boards update themselves from those tags. Details: `docs/dev/UPDATER.md`.

## Never commit

`config.json` (the live config; `config.json-example` is the template), `surprises.json`, `park_names.json`, `ride_names.json` (written beside config.json on a board), `sounds/*` other than its README, `.claude/settings.local.json` (personal permissions; the checked-in `.claude/settings.json` holds the SessionStart hook).

## Architecture

A continuous display loop that fetches Disney World wait times and renders them on an RGB LED matrix (64x32 and 64x64 boards). Two or three threads: the **main thread** (`disney.py`: fireworks intro, trip countdown, then per operating park its landmark, title and ride screens, forever), the **REST thread** (`updater/data_updater.py`, every 5 min, always running as the backstop) and, with a real API key, the **WebSocket thread** (`updater/websocket_updater.py`, live ThemeParks.wiki updates). Details: `docs/dev/LIVE-DATA.md` and `docs/dev/DISPLAY.md`.

Rules that bite everywhere:
- Mutations of `parks_data` (WS and REST threads) hold `updater/shared.py:parks_data_lock`, but only for in-memory writes, never across HTTP calls. The display thread reads without locking, by design.
- `merge_live_data` mutates attraction dicts in place and returns the same list. Don't rebuild the list: that drops concurrent WS updates.
- Screens draw onto an offscreen canvas and are redrawn every frame, so they must be cheap and side-effect free: no per-draw INFO logs or uncached HTTP.
- All drawing shares one canvas per matrix via `frame_canvas()`/`present()`, because rgbmatrix never frees canvases from `CreateFrameCanvas`.
- On a Pi, rgbmatrix's `graphics.DrawText`/`DrawLine` only accept rgbmatrix's own canvas, which can't be read back. Anything that needs a screen's pixels must go through `display/capture.py:capture_screen()`. The emulator accepts any canvas, so tests and previews won't catch a direct capture; this crashed a board once.
- Driver and start-up changes get checked on a real board before merging: tests run on the emulator (`docs/dev/BOARD-SETUP.md`).

## Testing

- `tests/stubs/conftest.py` intercepts `config.json` reads with a dummy config and stubs the `driver` module, so tests run without hardware. Stubs for `aiohttp`, `requests` and `pyowm` live in `tests/stubs/` and mirror the real libraries' names and exceptions; check real-library behaviour separately when upgrading one.
- CI (`coverage.yml`) runs `pytest -n auto`: 3.11 and 3.13 without coverage, 3.14 with it (`COVERAGE_CORE=sysmon` measures branches only from 3.14; the older tracer made the run four times slower), uploaded to Codecov (`codecov.yml`: fixed 90% project and patch targets; its checks also gate the updater's Beta channel).
- Before pushing: `ruff check . && lint-imports` (CI's `lint` job; rules, the 600-line cap and `tools/frame_hashes.py`, which proves a display refactor changed nothing, are in `docs/dev/CODE-QUALITY.md`).
- App code logs through `utils/debug` (logger `disney-lll`), which pytest's `caplog` doesn't see: check a warning with `monkeypatch.setattr(module.debug, "warning", warnings.append)`. `tools/` scripts use plain `logging`, so `caplog` works there.
- `board-setup.sh` must run under macOS's bash 3.2 (its tests do): no associative arrays, `mapfile` or `${x,,}`.

## Gotchas

- Run the app from the repo root: fonts, `config.json` and `emulator_config.json` are resolved relative to the cwd.
- The emulator's browser adapter binds port 8888 (`emulator_config.json`); a second instance fails with `[Errno 48] Address already in use`.
- macOS has no GNU `timeout`; use `perl -e 'alarm N; exec "python3", @ARGV' disney.py ...` for time-boxed runs.

## Topic notes

Read the note before changing its area; update it in the same PR.

| Area | Note |
|---|---|
| API fetch and parse, operating status, schedules, special events, weather, REST/WS threads, preview protocol, WebSocket resilience | `docs/dev/LIVE-DATA.md` (plans: `docs/plans/`) |
| Main loop, screens and `show_screen`, fonts, landmarks, ride screen, badges | `docs/dev/DISPLAY.md` |
| Transitions, characters, sprite editor, reference images | `docs/dev/CHARACTERS.md`, then `display/CHARACTERS.md`; reference rows in `docs/references/README.md` |
| Castle fireworks, synced shows, V2 overlays, lip-sync, show tools | `docs/dev/SHOWS.md` (each show: `docs/shows/<clip_name>/`) |
| Settings page (`settings_page/`), PIN, Pushover | `docs/dev/SETTINGS-PAGE.md` |
| Surprise characters page, `surprises.json`, Export/Import | `docs/dev/SURPRISES.md` |
| Releases, auto-tagging, `self_update/`, health, rollback | `docs/dev/UPDATER.md` |
| `board-setup.sh`, `LLL-install.sh`, comitup Wi-Fi, Tailscale, driver and Pi models, pinned packages | `docs/dev/BOARD-SETUP.md` (wiring: `docs/hardware/`) |
| Every `config.json` key | `docs/dev/CONFIG.md` |
| Lint, complexity `noqa` ratchet, 600-line cap, import layers, frame hashes, clean-code rules | `docs/dev/CODE-QUALITY.md` (plan: `docs/plans/CODE-HEALTH-PLAN.md`) |

## File map

- `disney.py`: entry point and display loop (`PARK_REVEALS`, `SURPRISES`, `RIDE_VISITORS`); `cli.py`: flags and Pi model defaults; `version.py`
- `api/`: ThemeParks.wiki and weather fetching
- `parks/`: decisions over park data (operating, live showtimes, names); `utils/names.py` holds the cleaning helpers it re-exports
- `updater/`: live data threads (REST, WebSocket); not `self_update/`
- `display/`: screens, `animation/` (transitions and characters), `landmarks/`, `fireworks/` (shows; `fireworks/effects/` the synced shows' scene looks), badges
- `driver/`: rgbmatrix or the emulator
- `utils/`: config, special events, trips, sound, surprises, heartbeat, brightness, debug logging
- `settings_page/`: the board's settings page (its own service, port 8080)
- `self_update/`: the board updater
- `tools/`: builders, previews, show tools, reference measuring, release tagging, `frame_hashes.py` (display no-change proof)
- `tests/`: mirrors the packages; `tests/stubs/` fakes hardware and HTTP libraries
- `docs/`: `dev/` topic notes, `references/`, `shows/`, `hardware/`, `plans/`
- `board-setup.sh`, `LLL-install.sh`: set up and install a board
