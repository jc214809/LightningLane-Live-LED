import requests
import logging
import asyncio
import aiohttp
from utils.utils import logJSONPrettyPrint

def fetch_disney_world_parks():
    """
    Fetch and return a list of Walt Disney World parks with their respective IDs,
    excluding water parks.
    """
    api_url = "https://api.themeparks.wiki/v1/destinations"
    logging.info("Fetching Disney World park data...")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        parks_data = response.json()
        logging.debug(f"API Response (Parks): {parks_data}")

        if not isinstance(parks_data, dict):
            logging.error(f"Unexpected API response format: {parks_data}")
            return []

        destinations = parks_data.get("destinations", [])
        if not isinstance(destinations, list):
            logging.error(f"Unexpected format for 'destinations' key: {destinations}")
            return []

        disney_world = next(
            (destination for destination in destinations
             if isinstance(destination, dict) and "Walt Disney World" in destination.get("name", "")),
            None
        )

        if not disney_world:
            logging.warning("Walt Disney World data not found in API response.")
            return []

        disney_parks = disney_world.get("parks", [])
        if not isinstance(disney_parks, list):
            logging.error(f"Unexpected format for 'parks' key: {disney_parks}")
            return []

        logging.info(f"Found {len(disney_parks)} parks under Walt Disney World.")

        # Filter out water parks.
        filtered_parks = [
            (park.get("name", "Unknown"), park.get("id", "Unknown"))
            for park in disney_parks
            if isinstance(park, dict) and "Water Park" not in park.get("name", "") and "Magic" not in park.get("name", "")
        ]

        logging.debug(f"Filtered Parks: {filtered_parks}")
        return filtered_parks

    except requests.RequestException as e:
        logging.error(f"Failed to fetch park data: {e}")
        return []

def fetch_parks_and_attractions(disney_park_list):
    """
    For each park in disney_park_list (a list of tuples of (park_name, park_id)),
    fetch the attractions and return a list of park objects.
    Each park object is a dict with keys: 'name', 'id', and 'attractions'.
    """
    parks = []
    for park_name, park_id in disney_park_list:
        api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}/children"
        logging.info(f"Fetching attractions for park: {park_name} (ID: {park_id})")
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            park_data = response.json()
            logging.debug(f"{park_name} Park Data: {logJSONPrettyPrint(park_data)}")
            logging.debug(f"API Response (Attractions for {park_name}): {park_data}")
        except requests.RequestException as e:
            logging.error(f"Failed to fetch attractions for park {park_name}: {e}")
            continue

        attractions = []
        if "entityType" in park_data and park_data["entityType"] == "ATTRACTION":
            if "children" not in park_data:
                logging.warning(f"No 'children' section found for attraction {park_name} (ID: {park_id}).")
                continue

        for item in park_data.get("children", []):
            if item.get("entityType") == "ATTRACTION":
                attraction = {
                    "id": item.get("id"),
                    "name": item.get("name", "").replace("\u2122", "").replace("–", "-").replace("*", " "),
                    "entityType": item.get("entityType"),
                    "parkId": park_id,
                    "waitTime": '',      # Placeholder for wait time
                    "status": '',        # Placeholder for status
                    "lastUpdatedTs": ''  # Placeholder for timestamp
                }
                logging.info(f"attraction {attraction}")
                attractions.append(attraction)
        park_obj = {
            "id": park_id,
            "name": park_name,
            "attractions": attractions
        }
        parks.append(park_obj)
    return parks

async def fetch_live_data_for_attraction(session, attraction):
    """
    Fetch live data for a single attraction.
    If the status is not "CLOSED" or "REFURBISHMENT", update the waitTime.
    """
    api_url = f"https://api.themeparks.wiki/v1/entity/{attraction['id']}/live"
    logging.info(f"Fetching live data for attraction: {attraction['name']} (ID: {attraction['id']})")
    try:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Live Data for {attraction['name']}: {data}")
                live_data_info = data.get('liveData', [])
                if live_data_info:
                    live_data_entry = live_data_info[0]  # Use the first liveData entry
                    logging.debug(f"Live Data for {live_data_entry}")
                    if live_data_entry.get("status") not in ["CLOSED", "REFURBISHMENT"]:
                        attraction["waitTime"] = live_data_entry.get("queue", {}) \
                                                              .get("STANDBY", {}) \
                                                              .get("waitTime", None)
                    attraction["status"] = live_data_entry.get("status", None)
                    attraction["lastUpdatedTs"] = live_data_entry.get("lastUpdated", None)
            else:
                logging.error(f"Failed to fetch live data for {attraction['name']}, Status Code: {response.status}")
    except Exception as e:
        logging.error(f"Error occurred while fetching live data for {attraction['name']}: {e}")
    return attraction

async def fetch_live_data(attractions):
    """
    Fetch live data for all attractions concurrently.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_live_data_for_attraction(session, attraction) for attraction in attractions]
        results = await asyncio.gather(*tasks)
    logging.info(f"Total live data fetched: {len(results)}")
    return results

def park_has_operating_attraction(park):
    """
    Check if any attraction in the park is operating and has a wait time.
    Returns True if at least one attraction is operating (i.e. its 'status' is not "CLOSED" or "REFURBISHMENT")
    and its 'waitTime' is not None or empty, otherwise returns False.
    """
    for attraction in park.get("attractions", []):
        wait_time = attraction.get("waitTime")
        status = attraction.get("status")
        logging.info(
            f"Attraction: {attraction['name']} (Park: {park['name']}) | " 
            f"Wait Time: {attraction['waitTime']} min | Status: {attraction['status']}")
        if wait_time not in [None, ''] and status not in ["CLOSED", "REFURBISHMENT"]:
            return True
    return False

def update_parks_operating_status(parks):
    """
    Updates each park object in the list with a new key 'operating' that is True
    if the park has at least one operating attraction with a valid wait time, otherwise False.
    """
    for park in parks:
        park["operating"] = park_has_operating_attraction(park)
    return parks

