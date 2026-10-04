import asyncio
import time
import traceback
from api.disney_api import (fetch_parks_and_attractions, fetch_park_live_data, get_down_time, parse_timestamp,
                            update_parks_operating_status)
from api.weather import fetch_weather_data
from updater.shared import live_feed_healthy, note_network_result, parks_data_lock, wait_for_live_feed
from utils import debug

# With the preview WebSocket healthy, REST checks every ride this often instead of every cycle.
REST_INTERVAL_WITH_LIVE_FEED_SECS = 30 * 60
# At startup the preview WebSocket's snapshot replaces REST's first fetch if it comes this fast.
LIVE_FEED_STARTUP_WAIT_SECS = 15


def _is_older(new_ts, existing_ts):
    """True only when both are real timestamps and new_ts is before existing_ts."""
    new, existing = parse_timestamp(new_ts), parse_timestamp(existing_ts)
    return bool(new and existing and new < existing)


def merge_live_data(existing_attractions, new_live_data):
    """
    Update existing attractions in place with new live data. Preserve the
    'down_since' field if it already exists. Returns the same list object —
    rebuilding the list would silently drop concurrent WS-thread updates to
    the dicts it contains.
    """

    # Create a mapping from attraction id to the existing attraction object.
    attraction_map = {attr["id"]: attr for attr in existing_attractions}
    debug.log(f"Starting to update new live data for attractions.")
    for new_attr in new_live_data:
        attr_id = new_attr.get("id")

        if attr_id in attraction_map:
            existing = attraction_map[attr_id]
            if _is_older(new_attr.get("lastUpdatedTs"), existing.get("lastUpdatedTs")):
                # A replayed WS update, or a REST poll that landed after a newer WS one.
                debug.log(f"Skipping older live data for {existing.get('name')}")
                continue
            # Merge only the fields present in the update; a CLOSED/REFURBISHMENT
            # update omits waitTime so the last known value is preserved.
            existing.update({
                key: new_attr[key]
                for key in ("waitTime", "status", "lastUpdatedTs", "updateSource", "forecast", "showtimes")
                if key in new_attr
            })

            # Do not overwrite down_since if already set, unless status is no longer DOWN.
            if new_attr.get("status") != "DOWN":
                existing["down_since"] = ""
            else:
                # If it's still DOWN and down_since is not set, set it now.
                if not existing.get("down_since"):
                    existing["down_since"] = new_attr.get("lastUpdatedTs")
                    debug.info(f"DOWN (REST): {existing.get('name')} — down_since set to {existing['down_since']}")
                down_time = get_down_time(existing.get("down_since"))
                existing["waitTime"] = f"Down {down_time}" if down_time is not None else "Down"
        else:
            # Unknown ids are skipped: live updates carry no name/entityType, and
            # roster changes are handled by refresh_park_attractions.
            debug.log(f"Ignoring live data for unknown attraction id {attr_id}")
    return existing_attractions


async def _fetch_all_live_data(parks):
    """Fetch every park's live data concurrently on one shared event loop."""
    fetchable = [park for park in parks if park.get("attractions")]
    results = await asyncio.gather(*(fetch_park_live_data(park) for park in fetchable))
    return list(zip(fetchable, results))


def update_parks_live_data(parks, fetch_live=True):
    """Fetch and merge live attraction data for every park via REST (unless fetch_live is
    False: the preview WebSocket is keeping it current), then refresh weather for operating
    parks. See CLAUDE.md for why this runs continuously even when the WS thread is also active."""
    results = asyncio.run(_fetch_all_live_data(parks)) if fetch_live else []
    if results:
        # One park getting through proves the connection; only all failing flags it.
        note_network_result(any(data is not None for _, data in results))
    for park, new_live_data in results:
        if new_live_data is None:
            # Fetch failed (rate limit, timeout, bad response): keep existing
            # data and flag it stale so the next cycle is a retry, not a skip.
            park["live_data_stale"] = True
            debug.warning(f"Live data fetch failed for {park.get('name')}; keeping existing data.")
        else:
            with parks_data_lock:
                park["live_data_stale"] = False
                merge_live_data(park["attractions"], new_live_data)

    for park in parks:
        if park.get("location") and park.get("operating"):
            park["weather"] = fetch_weather_data(park.get("location").get("latitude"), park.get("location").get("longitude"))

    return parks


def rest_poll_due(last_fetch, now):
    """With the preview WebSocket: poll REST when the feed isn't healthy, or every
    REST_INTERVAL_WITH_LIVE_FEED_SECS as the backstop that catches anything it got wrong."""
    return (not live_feed_healthy() or last_fetch is None
            or now - last_fetch >= REST_INTERVAL_WITH_LIVE_FEED_SECS)


def live_data_updater(disney_park_list, update_interval, parks_data, use_websocket=False, ws_protocol="legacy"):
    """
    Background thread that updates live data for parks every 'update_interval' seconds.
    With the legacy WebSocket, use_websocket only adds the initial synchronous fetch below;
    REST polls every cycle. With the preview one, its snapshot replaces that fetch and REST
    polls only when rest_poll_due. Operating status, schedules and weather run every cycle
    either way. See CLAUDE.md for the WS/REST design.
    """
    parks_data[:] = fetch_parks_and_attractions(disney_park_list)
    preview = use_websocket and ws_protocol == "preview"
    last_rest_fetch = None
    if preview:
        if wait_for_live_feed(LIVE_FEED_STARTUP_WAIT_SECS):
            debug.info("WebSocket snapshot arrived; skipping the startup REST live fetch.")
            last_rest_fetch = time.monotonic()
        else:
            debug.warning(f"No WebSocket snapshot within {LIVE_FEED_STARTUP_WAIT_SECS}s; fetching live data over REST.")
    elif use_websocket:
        debug.info("WebSocket mode: performing initial REST live data fetch before WS takes over per-event updates.")
        initial_parks = update_parks_live_data(list(parks_data))
        initial_parks = update_parks_operating_status(initial_parks)
        with parks_data_lock:
            parks_data[:] = initial_parks
        debug.info("Initial REST live data fetch complete — WS will now deliver per-event updates; REST continues polling as a backstop.")
    consecutive_failures = 0
    while True:
        try:
            if parks_data:
                fetch_live = not preview or rest_poll_due(last_rest_fetch, time.monotonic())
                if preview and not fetch_live:
                    debug.log("WebSocket healthy; skipping this cycle's REST live fetch.")
                updated_parks = update_parks_live_data(parks_data, fetch_live=fetch_live)
                if preview and fetch_live:
                    last_rest_fetch = time.monotonic()
                # Runs in websocket mode too: the WS thread defers schedule
                # fetches (schedule_refresh_needed) to this thread.
                updated_parks = update_parks_operating_status(updated_parks)
                # No-op today (both calls above mutate parks_data in place and
                # return it unchanged) — but if either starts rebuilding the
                # list instead, this line starts silently dropping concurrent
                # WS writes to the old dicts. Don't remove without checking.
                with parks_data_lock:
                    parks_data[:] = updated_parks
                for park in updated_parks:
                    attrs = park.get("attractions") or []
                    total = len(attrs)
                    down = [a for a in attrs if a.get("status") == "DOWN"]
                    operating = [a for a in attrs if a.get("status") == "OPERATING"]
                    debug.info(
                        f"{'REST poll' if fetch_live else 'Live status'} [{park['name']}]: {len(operating)} operating, "
                        f"{len(down)} DOWN, {total} total"
                        + (f" | DOWN: {', '.join(a['name'] for a in down)}" if down else "")
                    )
            else:
                debug.warning("No parks found during live data update.")
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            debug.error(f"Error during live data update (consecutive failure #{consecutive_failures}): {e}")
            debug.error(traceback.format_exc())
        time.sleep(update_interval)