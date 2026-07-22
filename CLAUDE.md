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
```

## Architecture

The application is a continuous display loop that fetches Disney World attraction wait times and renders them on an RGB LED matrix. Two or three threads run concurrently:

- **Main thread** (`disney.py`): Drives the display loop — renders Mickey logo → optional trip countdown → park title screen → attraction wait times, cycling indefinitely.
- **REST thread** (`updater/data_updater.py:live_data_updater`): Fetches live wait times every `update_interval` seconds (5 min) and updates the shared `parks_data` list in-place. Always does the initial fetch/populate, even in WebSocket mode.
- **WebSocket thread** (`updater/websocket_updater.py:websocket_live_updater`), started only when `config.json`'s `themeparks_api_key` is set or `websocket_only: true`: maintains a persistent connection to `wss://ws.themeparks.wiki/v1/live` for real-time attraction updates. When active, the REST thread skips attraction polling (`use_websocket=True`) but keeps refreshing weather and servicing deferred schedule fetches.

### Data flow

1. `api/disney_api.py:fetch_list_of_disney_world_parks()` — fetches the 4 WDW theme parks (excluding water parks) from the ThemeParks Wiki API.
2. `api/disney_api.py:fetch_parks_and_attractions()` — fetches each park's attraction list; initial wait times are empty placeholders.
3. Live wait times come from one `api/disney_api.py:fetch_park_live_data()` call per park (`/entity/{parkId}/live` — all children in one request, not one call per attraction), parsed by `build_live_updates()`/`parse_queue_wait()`, then merged into the shared list by `updater/data_updater.py:merge_live_data()`. In WebSocket mode, per-event updates arrive instead via `updater/websocket_updater.py:_apply_live_update()`, which reuses `parse_queue_wait()`; the per-park REST fetch still runs once at startup and after every WS reconnect.
4. `api/weather.py` provides weather data per park, fetched via OpenWeatherMap (requires API key in `config.json`).

### WebSocket resilience

`updater/websocket_updater.py` maintains the live connection with several layered defenses (see git history on `feature/websocket` and its stack for the incident that motivated each):
- `ws_connect(..., heartbeat=30, receive_timeout=120)` detects a dead socket and forces a reconnect within ~2 minutes.
- A per-connection `_watchdog` task force-reconnects if zero messages arrive in a 5-minute window while any park is `operating` — catches a connection that's alive at the protocol level but has stopped streaming data.
- Reconnect backoff (`_next_delay`) only resets to 5s after a connection stays up 60s+; otherwise it doubles (capped at 60s), so a connect-then-die loop can't hammer the server.
- `attr["lastUpdatedTs"]`/`down_since` are stamped from the event's own `lastUpdated`, not receive time — confirmed present on all ATTRACTION/SHOW entries from the live API.

### Display layer

All rendering lives under `display/`. Fonts are loaded once at startup by `display/display.py:initialize_fonts()` into the module-level `loaded_fonts` dict, keyed by board height (32 or 64). Each sub-module (`park/park_details.py`, `attractions/attraction_info.py`, `countdown/countdown.py`, `startup.py`) imports from that shared dict. Font sizes and paths differ between 64-row and 32-row boards.

### Driver abstraction

`driver/` wraps both `rgbmatrix` (real hardware, Raspberry Pi only) and `RGBMatrixEmulator` (software). The `driver/__init__.py` auto-selects based on whether hardware is available. `driver/mode.py` defines the `DriverMode` enum. Use `driver.is_emulated()` to branch on hardware vs. emulator.

### Configuration

`config.json` (gitignored; copy from `config.json-example`) controls:
- `trip_countdown.enabled` — show/hide countdown
- `trip_countdown.trip_dates` — list of ISO date strings (`YYYY-MM-DD`); supports multiple trips
- `trip_countdown.trip_date` — legacy single-date fallback
- `weather.apikey` — OpenWeatherMap API key
- `debug` — enables verbose logging

### Testing

Tests use `pytest`. The `tests/stubs/conftest.py` patches `builtins.open` to intercept `config.json` reads (returns a dummy config) and stubs out the `driver` module entirely so tests run without hardware or the `rgbmatrix` binary. Stub modules for `aiohttp`, `requests`, `pyowm`, and `pytz` live in `tests/stubs/`.

The `operating` field on a park dict is set by `update_parks_operating_status()` — a park is considered operating only if at least one attraction has a non-null wait time and `OPERATING` status. The main loop skips parks where `operating` is falsy. Its `fetch_schedules` flag controls whether a closed→open transition fetches the park schedule immediately (blocking HTTP) or only sets `schedule_refresh_needed`; the WebSocket thread always passes `fetch_schedules=False` (never block the asyncio event loop) and the REST thread services the flag on its next 5-minute cycle.

Mutations of the shared `parks_data` structure (WS thread and REST thread) must hold `updater/shared.py:parks_data_lock` — but only for in-memory writes, never across HTTP calls. `merge_live_data` mutates attraction dicts in place and returns the same list; don't rebuild the list, that drops concurrent WS updates. The display thread reads without locking by design.

### Gotchas

- The app must run from the repo root — font paths (`assets/fonts/...`) and `config.json`/`emulator_config.json` are resolved relative to the cwd.
- The emulator's browser adapter binds port 8888 (`emulator_config.json`); a second instance fails with `[Errno 48] Address already in use`.
- The ThemeParks.wiki WS server closes duplicate/rate-limited connections with close code 4029; `ws.close_code` is logged when the receive loop ends.
- macOS has no GNU `timeout`; use `perl -e 'alarm N; exec "python3", @ARGV' disney.py ...` for time-boxed runs.
