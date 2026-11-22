# Live data: the API, parks and the update threads

<!-- Moved from CLAUDE.md on 2026-11-12 so it loads only when needed. Keep it current with the code it describes. -->

Read before changing `api/`, `parks/`, `updater/`, `utils/special_events.py` or the weather.

## Threads

- **REST thread** (`updater/data_updater.py:live_data_updater`): every 5 min, updates the shared `parks_data` in place, refreshes weather, rechecks operating status and does deferred schedule fetches. Always runs, as the backstop for WS-sourced status. With the preview protocol it skips the startup fetch if the WS snapshot comes within `LIVE_FEED_STARTUP_WAIT_SECS` (15), then polls live data only when `rest_poll_due`: the feed is unhealthy (`updater/shared.py:live_feed_healthy`) or 30 min have passed.
- **WebSocket thread** (`updater/websocket_updater.py`, running `ws_legacy.py` or `ws_preview.py` per `websocket.protocol`; shared parts in `ws_common.py`): only with `websocket.enabled` (default true) and a real `api_key` (`utils/config.py:websocket_settings`; placeholders don't count; an old top-level `themeparks_api_key` is still read, since the installer doesn't migrate configs). Keyless, the server closes with 3000 "Authentication timeout". Host: `wss://api.themeparks.wiki/v1/live` only. Each destination is subscribed once per `WS_ENTITY_TYPES` (`ATTRACTION`, `SHOW`): `entityTypeFilter` takes one type, and unfiltered, restaurants were two thirds of the traffic. A key gets 15 subscriptions.

## Data flow

1. `api/disney_api.py` fetches and parses; decisions over the data live in `parks/`. `fetch_list_of_disney_world_parks()` (4 theme parks, no water parks) → `fetch_parks_and_attractions()` → one `fetch_park_live_data()` per park (`/entity/{parkId}/live`; never one call per attraction) → `build_live_updates()`/`parse_queue_wait()` → `updater/data_updater.py:merge_live_data()`.
2. **Operating** (`parks/operating.py`): `update_parks_operating_status()` sets `operating` and `operatingReason` from `operating_and_why()`, logging only on open/close. With a usable schedule, it alone decides: open from the day's first opening (Early Entry included) to `actual_park_closing_time()` (the latest close of the day's entries, so a party's; stored as `actualParkClosingTime`), whatever the rides say, since shows report OPERATING forever. The day in progress is the latest `date` that has opened, so a 1am party end is still the previous day's. `closingTime` is the regular hours, for display. With no usable schedule (or one `_SCHEDULE_TRUST_HOURS` past its close with no next opening), a park is open while a ride is `OPERATING` with a wait and a `lastUpdatedTs` within `_ATTRACTION_FRESHNESS_MINUTES` (20). The main loop skips closed parks.
3. **Schedules:** `schedule_refresh_needed` is set on a closed→open transition and by a daily refresh from 3am park-local time (`park["timezone"]`), retried every 30 min until the day's schedule appears, giving up at 9am. The WS thread always passes `fetch_schedules=False` (never block the event loop); the REST thread does the fetch, through `api/disney_api.py:handle_park_schedule_update`.
4. **Special events** (`utils/special_events.py`): the API only says "Special Ticketed Event", so each `SPECIAL_EVENTS` entry is matched by a string in the park's entity names. Order is match priority (generic `after_hours` stays last). An entry can set the park screen's star colour, a landmark, and its own fireworks show and theme. Whether a party is on is decided at draw time by `special_event_now()`. Add a party by adding one entry.
5. **Weather** (`api/weather.py`, OpenWeatherMap via pyowm): `fetch_weather_data` never raises (steps: `_read_api_key`, `_backing_off`, `_fetch_with_retries`, which asks `_should_retry` after each failure). It caches, retries, pauses all parks on an outage, rechecks a rejected key (immediately if `config.json`'s key changes), and serves the last good reading until it's an hour old.
   **Weather icon**: after each park's reading the REST thread calls `updater/data_updater.py:_ensure_weather_icon`, which has `api/weather_icons.py:fetch_icon` download the OpenWeatherMap icon (15x15, 5 s timeout, cached per code, a failure not retried for 5 min) and publishes it in `updater.shared.weather_icons`, outside `parks_data_lock` (no lock needed: whole-key assignment). The park screen (`display/park/park_details.py`) only reads that dict, so a never-seen icon appears one REST cycle after its weather and a missing one simply isn't drawn (temperature and description go with the icon). pyowm puts the key in the URL, so log its errors through `_redact`.

## Shared state: rules

- Mutations of `parks_data` (WS and REST threads) hold `updater/shared.py:parks_data_lock`, but only for in-memory writes, never across HTTP calls.
- `merge_live_data` mutates attraction dicts in place and returns the same list. Don't rebuild the list: that drops concurrent WS updates.
- The display thread reads without locking, by design. `loop_through_attractions` snapshots each ride dict before animating it.

### Preview protocol (`websocket.protocol: "preview"`)

In `updater/ws_preview.py`. `_PreviewFeed.handle()` takes one frame, dispatches it by type through `_FRAME_HANDLERS`, and returns the replies as `(delay_s, frame)`; `_preview_ws_loop` does the I/O (`_read_frames`, `_handle_text`). Spec and live-probe results: themeparks.wiki/api/websockets.
- Subscribes on the `welcome` frame (which carries the key's `limits`): one per destination per `WS_ENTITY_TYPES`, or one unfiltered per destination if `maxSubscriptions` is too low. `snapshot` and `update` data are REST `/live` elements, merged through `build_live_updates` + `merge_live_data` like a REST poll, so `lastUpdatedTs` is the ride's real change time.
- **Resume:** the cursor of every applied `snapshot`, `update`, `resumed` and `ping` frame is kept in memory; a reconnect subscribes with `since: cursor` and the server replays what was missed (or sends a fresh snapshot past its window). A restart starts from a snapshot. A retryable refusal is re-sent after `_SUBSCRIBE_RETRY_SECS`; "Resume incomplete" re-subscribes that channel with a snapshot.
- `merge_live_data` skips an update older than the ride's `lastUpdatedTs` (replays, late REST polls); it applies anything it can't compare.
- Dead connection: `ws_receive=90` (the server pings idle connections every ~30s; we reply `pong`). The watchdog counts only `update` frames. Close codes in `_REFUSED_CLOSE_CODES` (4029 connection cap, 3000 bad key) wait `_REFUSED_RETRY_SECS` (10 min); other reconnects use `_next_delay` with jitter.
- The account has 2 connections for 3 boards, and an emulator run takes one too.

### WebSocket resilience

Layered defenses in `updater/ws_legacy.py` (which asks for the `legacy` subprotocol to keep its `{"event": ...}` frames), with the watchdog and backoff in `ws_common.py`; each fixed a real incident:
- `ws_connect(..., heartbeat=30, timeout=ClientWSTimeout(ws_receive=120, ws_close=10))` forces a reconnect on a dead socket within ~2 min. The float `receive_timeout=` is deprecated in aiohttp 3.14; give `ws_close` explicitly, or the 10s close default is dropped.
- `_watchdog` force-reconnects if no messages arrive for 5 min while any park is operating (alive at the protocol level but not streaming).
- Backoff (`_next_delay`) resets to 5s only after a connection stays up 60s; otherwise it doubles to 60s, so a connect-then-die loop can't hammer the server.
- Each ride's `updateSource` is `"rest"` or `"websocket"`: whichever path wrote it last (`build_live_updates` / `ws_legacy._apply_livedata`); the "Displaying ride" log shows it.
- WS messages carry no `lastUpdated` (REST's do), so `lastUpdatedTs` is the receive time and `down_since` the receive time of the first DOWN message. The REST poll writes the real `lastUpdated` back every 5 min.

## Gotchas

- The ThemeParks.wiki WS server closes duplicate/rate-limited connections with close code 4029.
