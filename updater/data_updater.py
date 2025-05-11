import time
from datetime import datetime
import pytz

import asyncio
from api.disney_api import fetch_parks_and_attractions, fetch_live_data, update_parks_operating_status
from api.weather import fetch_weather_data
from utils import debug

def merge_live_data(existing_attractions, new_live_data):
    """ Update existing attractions with new live data. Preserve the 'down_since' field if it already exists. """

    # Create a mapping from attraction id to the existing attraction object.
    attraction_map = {attr["id"]: attr for attr in existing_attractions}
    debug.info(f"Starting to update new live data for attractions.")
    for new_attr in new_live_data:
        debug.info(f"Processing new live data for attraction {new_attr['name']} - Wait time: {new_attr['waitTime']} status: {new_attr['status']} ({get_eastern(new_attr['lastUpdatedTs'])})" )
        attr_id = new_attr.get("id")
        if attr_id in attraction_map:
            # Merge the new live data fields into the existing attraction.
            existing = attraction_map[attr_id]

            new_ts = new_attr.get("lastUpdatedTs")
            existing_ts = existing.get("lastUpdatedTs")

            # Check if the new timestamp is newer before updating
            if new_ts:  # Ensure new timestamp exists
                debug.info(f"Should we update for {new_attr['name']}? {'No' if existing_ts not in (None, '') and new_ts <= existing_ts else 'Yes'}")
                if existing_ts in (None, "") or new_ts > existing_ts:  # Compare timestamps
                    debug.info(
                        f"Updating attraction {new_attr['name']} - Wait time: {existing['waitTime']} vs {new_attr['waitTime']} ({get_eastern(new_ts)})")
                    existing.update({
                        "waitTime": new_attr.get("waitTime"),
                        "status": new_attr.get("status"),
                        "lastUpdatedTs": new_ts
                    })

                    # Do not overwrite down_since if already set, unless status is no longer DOWN.
                    if new_attr.get("status") != "DOWN":
                        existing["down_since"] = ""
                    else:
                        # If it's still DOWN and down_since is not set, set it now.
                        if not existing.get("down_since"):
                            existing["down_since"] = new_ts
            else:
                debug.warning(f"New timestamp is missing for attraction {new_attr['name']}")

        else:
            # If new attraction is not present in the existing map, add it.
            attraction_map[attr_id] = new_attr
            debug.info(f"Adding new attraction {attr_id}: {new_attr}")

    return list(attraction_map.values())


def get_eastern(utc_timestamp):
    # Parse the timestamp and create a UTC datetime object
    utc_time = datetime.fromisoformat(utc_timestamp[:-1])  # Remove 'Z' for parsing
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    # Define the Eastern Time zone
    eastern = pytz.timezone('US/Eastern')
    # Convert to Eastern Time
    eastern_time = utc_time.astimezone(eastern)
    # Format the time in a non-military format (12-hour) with AM/PM
    return eastern_time.strftime("%Y-%m-%d %I:%M %p")  # e.g., "2025-05-10 04:11 PM"


def update_parks_live_data(parks):
    """
    For each park in parks, update its attractions with live data.
    """
    for park in parks:
        location = park.get("location")
        if location and park.get("operating"):
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            park["weather"] = fetch_weather_data(latitude, longitude) # Update weather data
        if park.get("attractions"):
            # Fetch the latest live data for the current attractions.
            new_live_data = asyncio.run(fetch_live_data(park["attractions"]))
            # Merge new live data into the existing attractions list.
            park["attractions"] = merge_live_data(park["attractions"], new_live_data)

    debug.log(f"Updated parks data: {parks}")
    return parks


def live_data_updater(disney_park_list, update_interval, parks_data):
    """
    Background thread that updates live data for parks every 'update_interval' seconds.
    The initial fetch of parks is done only once, and then live data is updated on the existing parks.
    """
    # Initial fetch of parks and attractions.
    parks_data[:] = fetch_parks_and_attractions(disney_park_list)
    while True:
        if parks_data:
            # Only update live data for existing parks.
            updated_parks = update_parks_live_data(parks_data)
            # Update each park with operating status.
            updated_parks = update_parks_operating_status(updated_parks)
            parks_data[:] = updated_parks  # Update shared list in-place.
            debug.info("Parks live data updated in background.")
        else:
            debug.warning("No parks found during live data update.")
        time.sleep(update_interval)
