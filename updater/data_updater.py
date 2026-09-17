import asyncio
import time
import traceback

from api.disney_api import fetch_parks_and_attractions, fetch_park_live_data, get_down_time, update_parks_operating_status
from api.weather import fetch_weather_data
from updater.shared import parks_data_lock
from utils import debug


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
            # Merge only the fields present in the update; a CLOSED/REFURBISHMENT
            # update omits waitTime so the last known value is preserved.
            existing = attraction_map[attr_id]
            existing.update({
                key: new_attr[key]
                for key in ("waitTime", "status", "lastUpdatedTs")
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


def update_parks_live_data(parks, weather_api_key=None):
    """Fetch and merge live attraction data for every park via REST, then
    refresh weather for operating parks. See CLAUDE.md for why this runs
    continuously even when the WS thread is also active."""
    for park, new_live_data in asyncio.run(_fetch_all_live_data(parks)):
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
            park["weather"] = fetch_weather_data(
                park.get("location").get("latitude"), park.get("location").get("longitude"), api_key=weather_api_key
            )

    return parks


def live_data_updater(disney_park_list, update_interval, parks_data, use_websocket=False, weather_api_key=None):
    """
    Background thread that updates live data for parks every 'update_interval' seconds.
    use_websocket only controls the initial synchronous fetch below and the
    schedule_refresh_needed handling further down — update_parks_live_data
    itself always polls REST. See CLAUDE.md for the WS/REST design.

    weather_api_key overrides config.json's weather.apikey — for callers (e.g.
    the bullpen plugin) that have no config.json in the process cwd.
    """
    parks_data[:] = fetch_parks_and_attractions(disney_park_list, weather_api_key=weather_api_key)
    if use_websocket:
        debug.info("WebSocket mode: performing initial REST live data fetch before WS takes over per-event updates.")
        initial_parks = update_parks_live_data(list(parks_data), weather_api_key=weather_api_key)
        initial_parks = update_parks_operating_status(initial_parks)
        with parks_data_lock:
            parks_data[:] = initial_parks
        debug.info("Initial REST live data fetch complete — WS will now deliver per-event updates; REST continues polling as a backstop.")
    consecutive_failures = 0
    while True:
        try:
            if parks_data:
                updated_parks = update_parks_live_data(parks_data, weather_api_key=weather_api_key)
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
                        f"REST poll [{park['name']}]: {len(operating)} operating, "
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