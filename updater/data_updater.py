import time
import logging
import asyncio
from api.disney_api import fetch_parks_and_attractions, fetch_live_data, update_parks_operating_status


def update_parks_live_data(parks):
    """
    For each park in parks, update its attractions with live data.
    Each park object in parks has a key 'attractions' that is a list of rides.
    """
    for park in parks:
        if park.get("attractions"):
            updated_attractions = asyncio.run(fetch_live_data(park["attractions"]))
            park["attractions"] = updated_attractions

    logging.debug(f"Updated parks data: {parks}")

    return parks

def live_data_updater(disney_park_list, update_interval, parks_holder):
    """
    Background thread that re-fetches parks (with their attractions) and updates live data
    every 'update_interval' seconds. The results are stored in the shared list 'parks_holder'.
    """
    while True:
        parks = fetch_parks_and_attractions(disney_park_list)
        if parks:
            updated_parks = update_parks_live_data(parks)
            # Update each park with operating status.
            updated_parks = update_parks_operating_status(updated_parks)
            parks_holder[:] = updated_parks  # Update shared list in-place.
            logging.info("Parks live data updated in background.")
        else:
            logging.warning("No parks found during live data update.")
        time.sleep(update_interval)
