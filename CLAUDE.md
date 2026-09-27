# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
# Run all tests
pytest

# Run a single test file
pytest tests/api/test_disney_api.py

# Run a single test by name
pytest tests/api/test_disney_api.py::test_function_name

# Run the app in emulator mode (no hardware required)
./disney.py --emulated --led-cols=64 --led-rows=32

# Run with specific board size
./disney.py --emulated --led-cols=64 --led-rows=64

# Check version
python3 version.py

# Update requirements (after adding/changing dependencies)
pipreqs . --force

# Rebuild the sprite editor after changing any character art (a test fails until you do)
python3 tools/build_sprite_editor.py
```

## Architecture

The application is a continuous display loop that fetches Disney World attraction wait times and renders them on an RGB LED matrix. Two or three threads run concurrently:

- **Main thread** (`disney.py`): Drives the display loop — renders castle fireworks intro (`display/fireworks/fireworks.py`; length is the `duration` default of `render_castle_fireworks`) → optional trip countdown → park title screen → attraction wait times, cycling indefinitely. Before every screen it checks `play_fireworks_show_if_due`: when Magic Kingdom's `Happily Ever After` (`disney.FIREWORKS_SHOW`) has a showtime that started within `FIREWORKS_SHOW_S`, it plays the castle fireworks without the title (`render_castle_fireworks(..., title=False)`) for the rest of that window, once per performance. Showtimes come from each SHOW's `showtimes` in live data (`parse_showtimes`), merged like `forecast` by both the REST and WS paths.
- **REST thread** (`updater/data_updater.py:live_data_updater`): Fetches live wait times every `update_interval` seconds (5 min) and updates the shared `parks_data` list in-place. Always does the initial fetch/populate, even in WebSocket mode.
- **WebSocket thread** (`updater/websocket_updater.py:websocket_live_updater`), started only when `config.json`'s `themeparks_api_key` is set or `websocket_only: true`: maintains a persistent connection to `wss://ws.themeparks.wiki/v1/live` for real-time attraction updates. When active, the REST thread keeps polling attractions on its normal interval too — since PR #73 made the per-park fetch cheap, REST runs continuously as an independent backstop/correction source for WS-sourced status, alongside refreshing weather and servicing deferred schedule fetches.

### Data flow

1. `api/disney_api.py:fetch_list_of_disney_world_parks()` — fetches the 4 WDW theme parks (excluding water parks) from the ThemeParks Wiki API.
2. `api/disney_api.py:fetch_parks_and_attractions()` — fetches each park's attraction list; initial wait times are empty placeholders.
3. Live wait times come from one `api/disney_api.py:fetch_park_live_data()` call per park (`/entity/{parkId}/live` — all children in one request, not one call per attraction), parsed by `build_live_updates()`/`parse_queue_wait()`, then merged into the shared list by `updater/data_updater.py:merge_live_data()`. In WebSocket mode, per-event updates also arrive via `updater/websocket_updater.py:_apply_live_update()`, which reuses `parse_queue_wait()`; the per-park REST fetch keeps running on its normal 5-minute interval as an independent backstop (both write paths hold `parks_data_lock`), not just at startup and after WS reconnects.
4. `api/weather.py` provides weather data per park, fetched via OpenWeatherMap (requires API key in `config.json`).

### WebSocket resilience

`updater/websocket_updater.py` maintains the live connection with several layered defenses (see git history on `feature/websocket` and its stack for the incident that motivated each):
- `ws_connect(..., heartbeat=30, receive_timeout=120)` detects a dead socket and forces a reconnect within ~2 minutes.
- A per-connection `_watchdog` task force-reconnects if zero messages arrive in a 5-minute window while any park is `operating` — catches a connection that's alive at the protocol level but has stopped streaming data.
- Reconnect backoff (`_next_delay`) only resets to 5s after a connection stays up 60s+; otherwise it doubles (capped at 60s), so a connect-then-die loop can't hammer the server.
- `attr["lastUpdatedTs"]`/`down_since` are stamped from the event's own `lastUpdated`, not receive time — confirmed present on all ATTRACTION/SHOW entries from the live API.

### Display layer

All rendering lives under `display/`. Fonts are loaded once at startup by `display/display.py:initialize_fonts()` into the module-level `loaded_fonts` dict, keyed by board height (32 or 64). Each sub-module (`park/park_details.py`, `attractions/attraction_info.py`, `countdown/countdown.py`, `fireworks/fireworks.py`) imports from that shared dict. Font sizes and paths differ between 64-row and 32-row boards.

Every screen after the intro plays through `display/animation.py:show_screen(matrix, draw, hold_s, transition)`: it sweeps the previous screen away, reveals the new one (`"wipe"`, or for park title screens a random character fly-by from `disney.PARK_REVEALS` — `"tink"` Tinker Bell or `"buzz"` Buzz Lightyear). `TRANSITIONS` registers twelve: a plain `Wipe`; `FlyByReveal` subclasses that cross the board revealing in their wake (tink, buzz, figment, dumbo); `PeekReveal` (stitch), which rises over an already-visible screen without blacking it out; `RalphReveal`, which opts in via `wants_prev` to shatter the OUTGOING screen's pixels; `MickeyReveal`, which opts in via `wants_new` to assemble the INCOMING screen's pixels; and standalone Genie (lamp emerge), Slinky (stretched from edge to edge), Baymax and `SlinkyWrapReveal` (spring wraps round the back of the board). Transitions marked `over_screen` (the peeks, Baymax, slinky_wrap) play over a finished screen and let it keep animating underneath instead of holding it at its first frame. Park title screens use tink/buzz; ride screens use the wipe, or a rare surprise rolled from `disney.SURPRISES` (genie, baymax, slinky_wrap); the rest are built but unused. **Read `display/CHARACTERS.md` before adding or reworking a character** — it collects what actually works at this resolution. `tools/sprite_editor.html` (open it in a browser) edits every sprite and palette in `animation.py` and exports Python to paste back; a sprite drawn at a fixed size on both boards declares `SCALE` or `<NAME>_SCALE` so the editor previews it right), then calls `draw(canvas, t)` each frame until it returns False, after which it just sleeps out the hold. Screens therefore draw onto an offscreen canvas and must be cheap and side-effect free to redraw (no per-draw INFO logs or uncached HTTP — see the weather icon back-off in `park_details.py`). All drawing shares one canvas per matrix via `frame_canvas()`/`present()`, because rgbmatrix never frees canvases from `CreateFrameCanvas`. Call `forget_screen()` after anything that bypasses `show_screen` so the next sweep doesn't redraw a stale screen.

`present()` stamps a red "!" network badge (`display/network.py`, after mlb-led-scoreboard's) in the bottom-right 7x7 of every frame while `updater/shared.py:network_issues()` is set. The updaters drive it via `note_network_result()`: a REST cycle where every park's fetch fails sets it and any success clears it; in WS mode, a socket-level connect failure (an `OSError`, not a server rejection) sets it and any received message clears it. Tests reset the flag in the root `conftest.py`.

The trip countdown (`display/countdown/countdown.py`) draws the fireworks castle at 1x (beside the text on 32-row, above it on 64-row) with its windows twinkling, and the days left rolling up (`COUNT_UP_S`) in big gold digits over a red "DAYS TO DISNEY" label; `countdown_message()` swaps in "DAY n / OF N" during a trip with an end date and gold messages for tomorrow, trip day, "Welcome Home" and the open-ended week after, picking the largest `countdown_message`/`countdown_label` font it fits in. Its spaces are half a cell wide (via `draw_text`'s `space_px`).

Before each park title screen, `display/landmarks.py` plays an animated landmark (castle, Spaceship Earth, Tower of Terror, Tree of Life) for its `SCREEN_S` (3s by default; the tower's is 3.5s because the sweep and wipe eat 1.2s of every landmark screen, and its story needs the rest; on 64x32 it tilts up from the trees to the dome first), matched loosely on the park name by `landmark_for()`; parks with no match go straight to the title. Long ride names that don't fit scroll vertically (`attraction_info.overflow_rows`/`scroll_offset`); the wait bar is drawn only when the text fits above it, and above it the wait (not the name) drops halfway into any spare rows beneath it (`render_attraction_info`'s `wait_drop`). A DOWN ride keeps the bar (full width, forecast tick included) in the same pulsing red as its "Down" text, and its text stays centered on the whole board unless that would run into the bar (`centered_clears_bar`). The ride screen draws 2px word spaces (`attraction_info.SPACE_PX`) instead of the fonts' full-cell space — wrap, measure and draw its text through `wrap_text`/`get_text_width`/`draw_text` with `space_px` so all three agree.

`display/fireworks/fireworks.py` splits a pure simulation (`FireworksShow.step()`/`frame_pixels()`, seedable via `rng`) from the matrix renderer, which double-buffers with `CreateFrameCanvas`/`SwapOnVSync`. The castle is ASCII art in `_CASTLE_ART`, doubled on 64-row boards; `_BIG_CASTLE_ROW_PATCH` adjusts the doubled castle only (taller door), so edits to the art show at 2x on 64x64.

### Driver abstraction

`driver/` wraps both `rgbmatrix` (real hardware, Raspberry Pi only) and `RGBMatrixEmulator` (software). The `driver/__init__.py` auto-selects based on whether hardware is available. `driver/mode.py` defines the `DriverMode` enum. Use `driver.is_emulated()` to branch on hardware vs. emulator.

### Configuration

`config.json` (gitignored; copy from `config.json-example`) controls:
- `trip_countdown.enabled` — show/hide countdown
- `trip_countdown.trip_dates` — list of trips, each an ISO date string (`YYYY-MM-DD`) or `{"start", "end", "name"}` (end and name optional); `utils/trips.py:active_trip()` shows only one — a trip under way (or ended within 2 days, "Welcome Home"; open-ended trips hold for 7 days after start), else the nearest upcoming. A name replaces "DISNEY" under the day count when it fits on one line (~10 chars on 32-row, ~12 on 64-row)
- `trip_countdown.trip_date` — legacy single-date fallback
- `weather.apikey` — OpenWeatherMap API key
- `force_surprise` — a transition name (e.g. `"genie"`, `"slinky_wrap"`) to play on every ride screen, for checking a character on a real board; empty/unset in normal use. Every character transition logs its achieved fps (`genie: 18 fps over 3.8s of animation (target 30)`), so `journalctl -u LightningLane-Live-LED.service -f` shows a board's real speed
- `debug` — enables verbose logging

### Testing

Tests use `pytest`. The `tests/stubs/conftest.py` patches `builtins.open` to intercept `config.json` reads (returns a dummy config) and stubs out the `driver` module entirely so tests run without hardware or the `rgbmatrix` binary. Stub modules for `aiohttp`, `requests`, `pyowm`, and `pytz` live in `tests/stubs/`.

The `operating` field on a park dict is set by `update_parks_operating_status()` — a park is considered operating only if at least one attraction has a non-null wait time, `OPERATING` status, and a `lastUpdatedTs` within `_ATTRACTION_FRESHNESS_MINUTES` (20 min). `closingTime` is not a gate on `operating` — a live, fresh ticketed/extended-hours event past the regular closing time still counts, so the freshness check alone protects against a stuck-open park once WS/REST both stop updating an attraction. The main loop skips parks where `operating` is falsy. Its `fetch_schedules` flag controls whether a schedule fetch happens immediately (blocking HTTP) or only sets `schedule_refresh_needed`; the WebSocket thread always passes `fetch_schedules=False` (never block the asyncio event loop) and the REST thread services the flag on its next 5-minute cycle. Two independent triggers set `schedule_refresh_needed`: a closed→open transition, and a once-daily proactive refresh starting at 3am in the park's own local timezone (`park["timezone"]`, captured at startup from the ThemeParks Wiki `/entity/{id}` endpoint) — the daily refresh retries every 30 minutes if the API hasn't published the new day's `OPERATING` event yet (checked via `schedule_date` vs. today's local date), giving up at 9am local per attempt-day to avoid hammering the API indefinitely when a schedule never arrives.

Mutations of the shared `parks_data` structure (WS thread and REST thread) must hold `updater/shared.py:parks_data_lock` — but only for in-memory writes, never across HTTP calls. `merge_live_data` mutates attraction dicts in place and returns the same list; don't rebuild the list, that drops concurrent WS updates. The display thread reads without locking by design.

### Gotchas

- The app must run from the repo root — font paths (`assets/fonts/...`) and `config.json`/`emulator_config.json` are resolved relative to the cwd.
- The emulator's browser adapter binds port 8888 (`emulator_config.json`); a second instance fails with `[Errno 48] Address already in use`.
- The ThemeParks.wiki WS server closes duplicate/rate-limited connections with close code 4029; `ws.close_code` is logged when the receive loop ends.
- macOS has no GNU `timeout`; use `perl -e 'alarm N; exec "python3", @ARGV' disney.py ...` for time-boxed runs.
