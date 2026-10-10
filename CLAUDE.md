# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
# Run all tests / one file / one test
pytest
pytest tests/api/test_disney_api.py
pytest tests/api/test_disney_api.py::test_function_name

# Run the app in emulator mode (no hardware); --led-rows=64 for the 64x64 board
./disney.py --emulated --led-cols=64 --led-rows=32

# Check version
python3 version.py

# Install for development (the app plus the test tools), on Python 3.11 like the boards
uv venv --python 3.11 .venv && uv pip install --python .venv -r requirements-dev.txt

# Rebuild the sprite editor after changing any character art (a test fails until you do)
python3 tools/build_sprite_editor.py

# Measure a new reference image for docs/references/README.md (a test fails until it has a row)
python3 tools/analyze_reference.py docs/references/<image> [--box x0,y0,x1,y1] [--lines] [--art]
```

- **Python:** 3.11 is the target everywhere (`.python-version`, pyproject's `requires-python`, CI) because it's Raspberry Pi OS Bookworm's. CI also runs 3.13, the next OS's (Trixie). When the boards move, raise all three together.
- **Requirements:** edit `requirements.txt` (what the boards need) and pyproject.toml's `dependencies` by hand and keep them in sync; test tools go in `requirements-dev.txt`. Don't run pipreqs: it rewrites requirements.txt from imports and drops the caps and comments.

## Architecture

A continuous display loop that fetches Disney World wait times and renders them on an RGB LED matrix (64x32 and 64x64 boards). Two or three threads:

- **Main thread** (`disney.py`): castle fireworks intro (`display/fireworks/fireworks.py`) → optional trip countdown → per operating park: landmark → park title → ride screens, forever. Before every screen, `play_fireworks_show_if_due` cuts in with the castle fireworks (no title, themed) for `FIREWORKS_SHOW_S` after tonight's show starts (`utils/special_events.py:fireworks_show()`, showtimes from live data via `parse_showtimes`, checked by `parks/live.py:show_start_due`), once per performance.
- **REST thread** (`updater/data_updater.py:live_data_updater`): fetches live data every 5 min and updates the shared `parks_data` list in place. Always runs, even in WebSocket mode, as the backstop that corrects WS-sourced status; it also refreshes weather, rechecks operating status and services deferred schedule fetches every cycle. With the preview protocol it skips the startup fetch when the WS snapshot arrives within `LIVE_FEED_STARTUP_WAIT_SECS` (15), and polls live data only when `rest_poll_due`: the feed isn't healthy (`updater/shared.py:live_feed_healthy`, synced and a frame within 90s) or `REST_INTERVAL_WITH_LIVE_FEED_SECS` (30 min) has passed.
- **WebSocket thread** (`updater/websocket_updater.py:websocket_live_updater`): only when `config.json`'s `websocket` section has `enabled` (default true) and a real `api_key` (`websocket_settings`; `has_api_key` rejects empty and `<...>` placeholders). A config without the section falls back to the old top-level `themeparks_api_key`, because the installer doesn't migrate boards' configs. The server requires one: it accepts a keyless handshake, then closes with 3000 "Authentication timeout". Connects to `wss://api.themeparks.wiki/v1/live` (the only supported host) with the `legacy` subprotocol, which keeps the `{"event": ...}` frames we parse after the server's default moves to `preview`. Subscribes each destination once per `WS_ENTITY_TYPES` (`ATTRACTION`, `SHOW`): `entityTypeFilter` takes one type (a list or `"A,B"` gets `Invalid entityTypeFilter`), and unfiltered, restaurants were two thirds of the traffic. A key gets 15 subscriptions; server `error` frames are logged as warnings. `websocket.protocol` picks the protocol: `"legacy"` (default, `_ws_loop`) or `"preview"` (`_preview_ws_loop`, see below).

### Data flow

1. `api/disney_api.py`: `fetch_list_of_disney_world_parks()` (the 4 theme parks, no water parks) → `fetch_parks_and_attractions()` → one `fetch_park_live_data()` per park (`/entity/{parkId}/live`, all children in one request; never one call per attraction), parsed by `build_live_updates()`/`parse_queue_wait()`, merged by `updater/data_updater.py:merge_live_data()`. WS events go through `_apply_live_update()`, which reuses `parse_queue_wait()`. `api/disney_api.py` only fetches and parses; decisions over the data live in `parks/`.
2. **Operating** (`parks/operating.py`): `update_parks_operating_status()` sets each park's `operating` and `operatingReason` from `operating_and_why()`, and logs only when a park opens or closes. With a usable schedule, the schedule alone decides: open from the park day's first opening (Early Entry included) until `actual_park_closing_time()` (the latest close of the day's entries, so a party's close on a party night; stored as `park["actualParkClosingTime"]`), whatever the rides report. That is what stops a stuck-open park; shows and bands report OPERATING with no wait forever. The day in progress is the latest `date` that has opened, so a party that ends at 1am is still the previous day's at 12:30am (the schedule keeps yesterday's entries for this). `closingTime` is only the regular hours, for display. With no usable schedule, or one more than `_SCHEDULE_TRUST_HOURS` (6) past its close with no next opening (probably stale), a park is open while some ride is `OPERATING` with a wait and a `lastUpdatedTs` within `_ATTRACTION_FRESHNESS_MINUTES` (20). The REST cycle's summary line shows the decision next to the rides with a wait, so a mismatch is visible. The main loop skips parks that aren't operating.
3. **Schedules:** `schedule_refresh_needed` is set on a closed→open transition and by a daily refresh from 3am park-local time (`park["timezone"]`), retried every 30 min until the day's schedule appears, giving up at 9am. The WS thread always passes `fetch_schedules=False` (never block the event loop); the REST thread does the fetch, through `api/disney_api.py:handle_park_schedule_update`.
4. **Special events** (`utils/special_events.py`): the API only says "Special Ticketed Event", so each `SPECIAL_EVENTS` entry is matched by a string in the park's entity names. Order is match priority (generic `after_hours` stays last). An entry can set the park screen's star colour, a landmark, and its own fireworks show and theme. Whether a party is on is decided at draw time by `special_event_now()`. Add a party by adding one entry.
5. **Weather** (`api/weather.py`, OpenWeatherMap via pyowm): `fetch_weather_data` never raises. It caches, retries, pauses all parks on an outage, rechecks a rejected key (immediately if `config.json`'s key changes), and serves the last good reading until it's an hour old. pyowm puts the key in the URL, so log its errors through `_redact`.

### Shared state: rules

- Mutations of `parks_data` (WS and REST threads) hold `updater/shared.py:parks_data_lock`, but only for in-memory writes, never across HTTP calls.
- `merge_live_data` mutates attraction dicts in place and returns the same list. Don't rebuild the list: that drops concurrent WS updates.
- The display thread reads without locking, by design. `loop_through_attractions` snapshots each ride dict before animating it.

### Preview protocol (`websocket.protocol: "preview"`)

`_PreviewFeed.handle()` takes one frame and returns the replies as `(delay_s, frame)`; `_preview_ws_loop` does the I/O. Spec and live-probe results: themeparks.wiki/api/websockets.
- Subscribes on the `welcome` frame (which carries the key's `limits`): one per destination per `WS_ENTITY_TYPES`, or one unfiltered per destination if `maxSubscriptions` is too low. `snapshot` and `update` data are REST `/live` elements, merged through `build_live_updates` + `merge_live_data` like a REST poll, so `lastUpdatedTs` is the ride's real change time.
- **Resume:** the cursor of every applied `snapshot`, `update`, `resumed` and `ping` frame is kept in memory; a reconnect subscribes with `since: cursor` and the server replays what was missed (or sends a fresh snapshot past its window). A restart starts from a snapshot. A retryable refusal is re-sent after `_SUBSCRIBE_RETRY_SECS`; "Resume incomplete" re-subscribes that channel with a snapshot.
- `merge_live_data` skips an update older than the ride's `lastUpdatedTs` (replays, late REST polls); it applies anything it can't compare.
- Dead connection: `ws_receive=90` (the server pings idle connections every ~30s; we reply `pong`). The watchdog counts only `update` frames. Close codes in `_REFUSED_CLOSE_CODES` (4029 connection cap, 3000 bad key) wait `_REFUSED_RETRY_SECS` (10 min); other reconnects use `_next_delay` with jitter.
- The account has 2 connections for 3 boards, and an emulator run takes one too.

### WebSocket resilience

Layered defenses in `updater/websocket_updater.py` (the legacy loop; preview's are above); each one fixed a real incident:
- `ws_connect(..., heartbeat=30, timeout=ClientWSTimeout(ws_receive=120, ws_close=10))` forces a reconnect on a dead socket within ~2 min. The float `receive_timeout=` is deprecated in aiohttp 3.14; give `ws_close` explicitly, or the 10s close default is dropped.
- `_watchdog` force-reconnects if no messages arrive for 5 min while any park is operating (alive at the protocol level but not streaming).
- Backoff (`_next_delay`) resets to 5s only after a connection stays up 60s; otherwise it doubles to 60s, so a connect-then-die loop can't hammer the server.
- Each ride's `updateSource` is `"rest"` or `"websocket"`: whichever path wrote it last (`build_live_updates` / `_apply_live_update`'s `livedata` branch); the "Displaying ride" log shows it.
- WS messages carry no `lastUpdated` (REST's do), so `lastUpdatedTs` is the receive time and `down_since` the receive time of the first DOWN message. The REST poll writes the real `lastUpdated` back every 5 min.

### Display layer

- **Fonts:** loaded once by `display/display.py:initialize_fonts()` into `loaded_fonts`, keyed by board height (32 or 64); sizes and paths differ per board.
- **Shared helpers:** `display/motion.py` (`ease_out`, `smooth`, `progress`, `ramp`) and `display/pixels.py` (`put`/`set_pixel` with bounds check, `paint`, `blend`, `art_pixels`, `rotate_art`, `noise`). Use these before writing another copy.
- **Screens:** every screen after the intro plays through `display/animation/player.py:show_screen(matrix, draw, hold_s, transition)`. It sweeps the old screen away, reveals the new one with the transition, then calls `draw(canvas, t)` each frame until it returns False.
- **Transitions** (`display/animation/`): `mechanics.py` has the kinds (`Wipe`, `FlyByReveal`, `PeekReveal`, `CapturesScreens`), `player.py` the playback, `characters/` one file per character, registered in `TRANSITIONS` in `characters/__init__.py`. Each character's class docstring describes what it does. Who appears where is in `disney.py`: `PARK_REVEALS` (park titles), `SURPRISES` (ride screens, under 13% in all, held by a test) and `RIDE_VISITORS` (only on their own rides; the Mine Train's wait picks its train in `_mine_train_for_wait`); the rest are built but unused. A reveal longer than its screen sets `hold_after_s`, and `show_screen` stretches the hold to fit it; `run_frames`' `play_s` then plays the reveal in full even on a board too slow for `FPS` (scenes step by frame number, so a slow board runs them in slow motion). `display/animation/__init__.py` re-exports everything, so `animation.X` works. `config.json`'s `force_surprise` plays one on every ride screen, for checking on a real board.
- **Characters:** read `display/CHARACTERS.md` before adding or reworking one (what works at this resolution); planned work and its open questions are in `ROADMAP.md`. Add one with a file under `characters/` and a line in `TRANSITIONS`. `tools/sprite_editor.html` edits every sprite and palette (its Image to pixels has a Pattern / beads mode: it finds the grid in a chart or bead photo, one cell per LED, with new color keys, straightening a photo shot at a tilt (Turn; a turn typed in or calibrated is kept by Detect grid, clear it to auto-detect again; `gridTurn` skips the diagonal rows round beads line up in), or from two clicks on bead middles (Calibrate); drag a box to read one character from a sheet, and Grid lines only drops a picture backdrop; the detection is pure JS in its `core` script, tested under Node); a sprite drawn at a fixed size on both boards declares `SCALE` or `<NAME>_SCALE` so the editor previews it right.
- **References** (`docs/references/`): every image needs a README row (one per character on a sheet), held by `tests/tools/test_analyze_reference.py`. `tools/analyze_reference.py` drafts it with the editor's Pattern-mode core under Node; the SessionStart hook in `.claude/settings.json` (checked in; personal permissions go in the ignored `settings.local.json`) lists images with no row.
- **Landmarks** (`display/landmarks/`, one file each, `Landmark` base in `scene.py`): play before each park title for their `SCREEN_S`, matched loosely on the park name by `landmark_for()`; a party can swap in its own (`active_party()`). `PLAYS_UNDER_WIPE` landmarks keep animating while the wipe uncovers them.
- **Ride screen** (`display/attractions/attraction_info.py`): long names scroll; the wait drops into spare rows (`wait_drop`); DOWN rides pulse red with a full bar. It draws 2px word spaces (`SPACE_PX`): wrap, measure and draw text through `wrap_text`/`get_text_width`/`draw_text` with `space_px` so all three agree.
- **Network badge:** `present()` stamps a red "!" (`display/network.py`) while `updater/shared.py:network_issues()` is set, driven by `note_network_result()`. Tests reset the flag in the root `conftest.py`.

Display rules:
- A transition that takes the old screen (`wants_prev`) must paint every pixel of it, black included: `show_screen` has already drawn the new screen underneath, and it bleeds through otherwise. Add each new one to `test_new_screen_never_shows_through_the_old_screens_dark_pixels`.
- Screens draw onto an offscreen canvas and are redrawn every frame, so they must be cheap and side-effect free: no per-draw INFO logs or uncached HTTP.
- All drawing shares one canvas per matrix via `frame_canvas()`/`present()`, because rgbmatrix never frees canvases from `CreateFrameCanvas`.
- Call `forget_screen()` after anything that bypasses `show_screen`, so the next sweep doesn't redraw a stale screen.
- `over_screen` transitions play over a finished screen and let it keep animating underneath.
- Fireworks: the castle is `_CASTLE_ART`, doubled on 64-row boards; `_BIG_CASTLE_ROW_PATCH` adjusts only the doubled one.

### Driver abstraction

`driver/` wraps `rgbmatrix` (real hardware, Pi only) and `RGBMatrixEmulator`; `driver/__init__.py` picks one, falling back to the emulator if rgbmatrix fails to import. Use `driver.is_emulated()` to branch.

### Configuration

`config.json` (gitignored; copy from `config.json-example`): `trip_countdown` (`enabled`, `trip_dates` as ISO dates or `{"start", "end", "name"}`, legacy `trip_date`; `utils/trips.py:active_trip()` picks the one to show), `weather.apikey`, `websocket` (`enabled`, `api_key`, `protocol`: `"legacy"` or `"preview"`; old configs' top-level `themeparks_api_key` still read, `websocket_only` ignored), `force_surprise`, `debug`.

### Testing

- `tests/stubs/conftest.py` intercepts `config.json` reads with a dummy config and stubs the `driver` module, so tests run without hardware. Stubs for `aiohttp`, `requests` and `pyowm` live in `tests/stubs/` and mirror the real libraries' names and exceptions; check real-library behaviour separately when upgrading one.
- Animation tests mirror the package (`tests/display/animation/`, one file per module or character); shared fakes (`FakeCanvas`, `FakeMatrix`, …) in `support.py`; its `conftest.py` stubs `graphics` by patching `animation.drawing`. Landmark tests do the same in `tests/display/landmarks/`.

### Gotchas

- Run the app from the repo root: fonts, `config.json` and `emulator_config.json` are resolved relative to the cwd.
- The emulator's browser adapter binds port 8888 (`emulator_config.json`); a second instance fails with `[Errno 48] Address already in use`.
- On a Pi, rgbmatrix's `graphics.DrawText`/`DrawLine` only accept rgbmatrix's own canvas, which can't be read back. Anything that needs a screen's pixels must go through `display/capture.py:capture_screen()`. The emulator accepts any canvas, so tests and previews won't catch a direct capture; this crashed a board once.
- The ThemeParks.wiki WS server closes duplicate/rate-limited connections with close code 4029.
- Every character transition logs its achieved fps; `journalctl -u LightningLane-Live-LED.service -f` shows a board's real speed.
- `LLL-install.sh` installs with `pip install --upgrade --prefer-binary`. `--upgrade` keeps the boards current (plain `pip install -r` never moves a package that meets its floor). `--prefer-binary` matters on the 32-bit boards (`armhf`: PlutoPi, ZeroPi), whose piwheels builds lag PyPI; without it pip compiles a newer numpy on a Pi Zero, which takes hours or runs out of memory. The caps in `requirements.txt` keep upgrades compatible.
- Pillow is capped `<12`: the boards' rgbmatrix `SetImage` reads `ImagingCore.unsafe_ptrs`, which Pillow 12 removed, so the first image drawn (the weather icon) crashes the service into a restart loop. The emulator and tests don't touch that path, so check on a real board before raising the cap.
- macOS has no GNU `timeout`; use `perl -e 'alarm N; exec "python3", @ARGV' disney.py ...` for time-boxed runs.
