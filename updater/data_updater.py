import asyncio
import time
import traceback

from api.disney_api import fetch_parks_and_attractions, fetch_live_data, update_parks_operating_status
from api.weather import fetch_weather_data
from utils import debug
from utils.utils import get_eastern


def merge_live_data(existing_attractions, new_live_data):
    """ Update existing attractions with new live data. Preserve the 'down_since' field if it already exists. """

    # Create a mapping from attraction id to the existing attraction object.
    attraction_map = {attr["id"]: attr for attr in existing_attractions}
    debug.log(f"Starting to update new live data for attractions.")
    for new_attr in new_live_data:
        attr_id = new_attr.get("id")

        if attr_id in attraction_map:
            # Merge the new live data fields into the existing attraction.
            existing = attraction_map[attr_id]
            existing.update({
                "waitTime": new_attr.get("waitTime"),
                "status": new_attr.get("status"),
                "lastUpdatedTs": new_attr.get("lastUpdatedTs")
            })

            # Do not overwrite down_since if already set, unless status is no longer DOWN.
            if new_attr.get("status") != "DOWN":
                existing["down_since"] = ""
            else:
                # If it's still DOWN and down_since is not set, set it now.
                if not existing.get("down_since"):
                    existing["down_since"] = new_attr.get("lastUpdatedTs")
                    debug.info(f"DOWN (REST): {existing.get('name')} — down_since set to {existing['down_since']}")
        else:
            # If new attraction is not present in the existing map, add it.
            attraction_map[attr_id] = new_attr
            debug.info(f"Adding new attraction {attr_id}: {new_attr}")
    return list(attraction_map.values())


def update_parks_live_data(parks, use_websocket=False):
    """
    For each park in parks, update live data for attractions.
    If use_websocket is True, skip HTTP live data fetching — the WS handles it.
    """
    for park in parks:
        if not use_websocket and park.get("attractions"):
            new_live_data = asyncio.run(fetch_live_data(park["attractions"]))
            park["attractions"] = merge_live_data(park["attractions"], new_live_data)

        if park.get("location") and park.get("operating"):
            park["weather"] = fetch_weather_data(park.get("location").get("latitude"), park.get("location").get("longitude"))

    debug.log(f"Updated parks data: {parks}")
    return parks


def live_data_updater(disney_park_list, update_interval, parks_data, use_websocket=False):
    """
    Background thread that updates live data for parks every 'update_interval' seconds.
    When use_websocket is True, skips HTTP live data polling — the WS thread handles that —
    but continues to poll weather every update_interval seconds.
    Always performs an initial REST live data fetch so attractions have data before WS catches up.
    """
    parks_data[:] = fetch_parks_and_attractions(disney_park_list)
    if use_websocket:
        debug.info("WebSocket mode: performing initial REST live data fetch, then handing off to WS.")
        initial_parks = update_parks_live_data(list(parks_data), use_websocket=False)
        initial_parks = update_parks_operating_status(initial_parks)
        parks_data[:] = initial_parks
        debug.info("Initial REST live data fetch complete — WebSocket will handle attraction updates.")
    while True:
        try:
            if parks_data:
                updated_parks = update_parks_live_data(parks_data, use_websocket=use_websocket)
                # Runs in websocket mode too: the WS thread defers schedule
                # fetches (schedule_refresh_needed) to this thread.
                updated_parks = update_parks_operating_status(updated_parks)
                parks_data[:] = updated_parks
                if use_websocket:
                    debug.info("REST loop (websocket_only mode): weather refreshed, attraction polling skipped.")
                else:
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
        except Exception as e:
            debug.error(f"Error during live data update: {e}")
            debug.error(traceback.format_exc())
        time.sleep(update_interval)