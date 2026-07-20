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

The application is a continuous display loop that fetches Disney World attraction wait times and renders them on an RGB LED matrix. Two threads run concurrently:

- **Main thread** (`disney.py`): Drives the display loop — renders Mickey logo → optional trip countdown → park title screen → attraction wait times, cycling indefinitely.
- **Background thread** (`updater/data_updater.py:live_data_updater`): Fetches updated live wait times every 5 minutes and updates the shared `parks_data` list in-place.

### Data flow

1. `api/disney_api.py:fetch_list_of_disney_world_parks()` — fetches the 4 WDW theme parks (excluding water parks) from the ThemeParks Wiki API.
2. `api/disney_api.py:fetch_parks_and_attractions()` — fetches each park's attraction list; initial wait times are empty placeholders.
3. Background thread calls `fetch_live_data()` (async, via `aiohttp`) to concurrently fetch live wait times for all attractions, then `merge_live_data()` merges them into the shared list.
4. `api/weather.py` provides weather data per park, fetched via OpenWeatherMap (requires API key in `config.json`).

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

### Gotchas

- The app must run from the repo root — font paths (`assets/fonts/...`) and `config.json`/`emulator_config.json` are resolved relative to the cwd.
- The emulator's browser adapter binds port 8888 (`emulator_config.json`); a second instance fails with `[Errno 48] Address already in use`.
- The ThemeParks.wiki WS server closes duplicate/rate-limited connections with close code 4029; `ws.close_code` is logged when the receive loop ends.
- macOS has no GNU `timeout`; use `perl -e 'alarm N; exec "python3", @ARGV' disney.py ...` for time-boxed runs.
