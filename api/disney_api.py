import requests
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from utils.utils import logJSONPrettyPrint

troublesome_attraction_64x64_ids = ["8d7ccdb1-a22b-4e26-8dc8-65b1938ed5f0","06c599f9-1ddf-4d47-9157-a992acafc96b", "22f48b73-01df-460e-8969-9eb2b4ae836c",  "9211adc9-b296-4667-8e97-b40cf76108e4","64a6915f-a835-4226-ba5c-8389fc4cade3"]
troublesome_attraction_64x32_ids = ["9211adc9-b296-4667-8e97-b40cf76108e4","64a6915f-a835-4226-ba5c-8389fc4cade3"]


def fetch_disney_world_parks():
    """
    Fetch and return a list of Walt Disney World parks with their respective IDs
    and schedule info, excluding water parks. The schedule is filtered to only include
    events for today and the day before.
    """
    api_url = "https://api.themeparks.wiki/v1/entity/e957da41-3552-4cf6-b636-5babc5cbc4e5/schedule"
    logging.info("Fetching Disney World schedule data...")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"API Response (Schedule): {data}")

        parks_data = data.get("parks", [])
        if not isinstance(parks_data, list):
            logging.error(f"Unexpected format for 'parks' key: {parks_data}")
            return []

        # Determine today's date and yesterday's date as strings.
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

        filtered_parks = []
        for park in parks_data:
            if isinstance(park, dict) and "Water Park" not in park.get("name", ""):
                schedule = park.get("schedule", [])
                # Filter schedule events to include only those from today or yesterday.
                schedule_filtered = [
                    event for event in schedule if event.get("date") in (today_str, yesterday_str)
                ]
                filtered_parks.append({
                    "name": park.get("name", "Unknown"),
                    "id": park.get("id", "Unknown"),
                    "schedule": schedule_filtered
                })

        logging.info(f"Found {len(filtered_parks)} parks under Walt Disney World after filtering by date.")
        logging.debug(f"Filtered Parks: {filtered_parks}")
        return filtered_parks

    except requests.RequestException as e:
        logging.error(f"Failed to fetch schedule data: {e}")
        return []


def fetch_parks_and_attractions(disney_park_list):
    """
    For each park in disney_park_list (a list of dicts with keys 'name', 'id', 'schedule'),
    fetch the attractions and return a list of park objects.
    Each park object is a dict with keys:
      - 'id'
      - 'name'
      - 'attractions'
      - 'specialTicketedEvent': boolean indicating if any schedule event is a Special Ticketed Event.
      - 'closingTime': from the first OPERATING event.
      - 'openingTime': from the first OPERATING event.
      - 'LigtningLaneMultiPassPrice': from the purchase list in the OPERATING event.
    """
    parks = []
    for park_info in disney_park_list:
        park_name = park_info.get("name", "Unknown")
        park_id = park_info.get("id", "Unknown")
        schedule = park_info.get("schedule", [])

        # Determine if a "Special Ticketed Event" exists in the schedule.
        special_ticketed_event = any(
            event.get("type") == "TICKETED_EVENT" and "Special Ticketed Event" in event.get("description", "")
            for event in schedule
        )

        # Use the first OPERATING event to extract opening/closing times and pricing info.
        operating_event = next((event for event in schedule if event.get("type") == "OPERATING"), {})
        closing_time = operating_event.get("closingTime", "")
        opening_time = operating_event.get("openingTime", "")
        lightning_lane_multi_pass_price = ""
        if operating_event and "purchases" in operating_event:
            for purchase in operating_event["purchases"]:
                if purchase.get("name") == "Lightning Lane Multi Pass":
                    lightning_lane_multi_pass_price = purchase.get("price", {}).get("formatted", "")
                    break

        logging.info(f"Fetching attractions for park: {park_name} (ID: {park_id})")
        api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}/children"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            park_data = response.json()
            logging.debug(f"{park_name} Park Data: {logJSONPrettyPrint(park_data)}")
        except requests.RequestException as e:
            logging.error(f"Failed to fetch attractions for park {park_name}: {e}")
            continue

        attractions = []
        for item in park_data.get("children", []):
            if item.get("entityType") == "ATTRACTION": # and (item.get("id") in troublesome_attraction_64x64_ids or item.get("id") in troublesome_attraction_64x32_ids):
                attraction = {
                    "id": item.get("id"),
                    "name": item.get("name", "").replace("\u2122", "").replace("–", "-").replace("*", " ").replace("An Original", ""),
                    "entityType": item.get("entityType"),
                    "parkId": park_id,
                    "waitTime": '',      # Placeholder for wait time
                    "status": '',        # Placeholder for status
                    "lastUpdatedTs": ''  # Placeholder for timestamp
                }
                logging.info(f"Attraction found: {attraction}")
                attractions.append(attraction)

        park_obj = {
            "id": park_id,
            "name": park_name.replace("Theme", " ").replace("Park", " ").replace("Disney's", "").strip(),
            "attractions": attractions,
            "specialTicketedEvent": special_ticketed_event,
            "closingTime": closing_time,
            "openingTime": opening_time,
            "llmpPrice": lightning_lane_multi_pass_price
        }
        parks.append(park_obj)
    return parks


def get_down_time(last_updated_date, date_format='%Y-%m-%dT%H:%M:%SZ'):
    target_date = datetime.strptime(last_updated_date, date_format)
    current_time = datetime.utcnow()
    time_diff = current_time - target_date
    minutes = time_diff.total_seconds() / 60
    return round(minutes)

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
                    attraction["lastUpdatedTs"] = live_data_entry.get("lastUpdated", None)
                    attraction["status"] = live_data_entry.get("status", None)
                    if live_data_entry.get("status") == "DOWN":
                        attraction["waitTime"] = f"Down {get_down_time(live_data_entry.get('lastUpdated'))}"
                    if live_data_entry.get("status") not in ["CLOSED", "REFURBISHMENT","DOWN"]:
                        attraction["waitTime"] = live_data_entry.get("queue", {}) \
                            .get("STANDBY", {}) \
                            .get("waitTime", None)
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
            f"Wait Time: {attraction['waitTime']} | Status: {attraction['status']}"
        )
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Fetch parks with filtered schedule (today and yesterday)
    parks_list = fetch_disney_world_parks()
    logging.info("Parks List:")
    logging.info(parks_list)

    # Fetch attractions and additional schedule-derived fields
    parks_with_attractions = fetch_parks_and_attractions(parks_list)
    logging.info("Parks with Attractions:")
    logging.info(parks_with_attractions)
