from types import MappingProxyType

import requests

import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone

from api.weather import fetch_weather_data
from utils.utils import get_eastern
from utils import debug

troublesome_attraction_64x64_ids = ["8d7ccdb1-a22b-4e26-8dc8-65b1938ed5f0","06c599f9-1ddf-4d47-9157-a992acafc96b", "22f48b73-01df-460e-8969-9eb2b4ae836c",  "9211adc9-b296-4667-8e97-b40cf76108e4","64a6915f-a835-4226-ba5c-8389fc4cade3"]
troublesome_attraction_64x32_ids = ["9211adc9-b296-4667-8e97-b40cf76108e4","64a6915f-a835-4226-ba5c-8389fc4cade3"]
troublesome_attraction_single_ids = ["1e735ffb-4868-47f1-b2cd-2ac1156cd5f0"]


def get_park_location(park_id):
    api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}"
    debug.info("Fetching Disney World schedule data...")

    try:
        response = requests.get(api_url)
        park_data = response.json()
        return park_data.get("location")
    except requests.RequestException as e:
        debug.error(f"Failed get park data with location data: {e}")
        return []

def fetch_park_schedule(park_id):
    """
    Fetch and return the schedule for a specific park using its park_id.
    """
    # Determine today's date and yesterday's date as strings.
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}/schedule"
    debug.info(f"Fetching schedule for park with ID: {park_id}")

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        schedule_data = response.json().get("schedule", [])

        # Filter schedule events to include only those from today or yesterday.
        schedule_filtered = [
            event for event in schedule_data if event.get("date") in (today_str, yesterday_str)
        ]

        debug.info(f"Schedule Data for park ID {park_id}: {schedule_data}")
        return schedule_filtered
    except requests.RequestException as e:
        debug.error(f"Failed to fetch schedule for park ID {park_id}: {e}")
        return []

def fetch_list_of_disney_world_parks():
    """
    Fetch and return a list of Walt Disney World parks with their respective IDs
    and schedule info, excluding water parks. The schedule is filtered to only include
    events for today and the day before.
    """
    walt_disney_world_entity_id = "e957da41-3552-4cf6-b636-5babc5cbc4e5"
    api_url = f"https://api.themeparks.wiki/v1/entity/{walt_disney_world_entity_id}/schedule"
    debug.info("Fetching Disney World schedule data...")

    try:
        response = requests.get(api_url)

        parks_data = response.json().get("parks", [])

        # Determine today's date and yesterday's date as strings.
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

        filtered_parks = []
        for park in parks_data:
            # debug.log(f"Park Location: {pretty_print_json(park)}")
            if isinstance(park, dict) and "Water Park" not in park.get("name", ""):
                schedule = park.get("schedule")
                # Filter schedule events to include only those from today or yesterday.
                schedule_filtered = [
                    event for event in schedule if event.get("date") in (today_str, yesterday_str)
                ]
                debug.log(f"Schedule Filter: {schedule_filtered}")
                filtered_parks.append({
                    "name": park.get("name", "Unknown"),
                    "id": park.get("id", "Unknown"),
                    "schedule": schedule_filtered,
                    "weather": [],  # Get initial weather data
                    "location": get_park_location(park.get("id"))
                })

        debug.info(f"Found {len(filtered_parks)} parks under Walt Disney World after filtering by date.")
        debug.log(f"Filtered Parks: {filtered_parks}")
        return filtered_parks

    except requests.RequestException as e:
        debug.error(f"Failed to fetch schedule data: {e}")
        return []


def fetch_parks_and_attractions(disney_park_list):
    parks = []
    for park_info in disney_park_list:
        park_name = park_info.get("name", "Unknown")
        park_id = park_info.get("id", "Unknown")
        schedule = park_info.get("schedule", [])
        location = park_info.get("location")

        # Use the first OPERATING event to extract opening/closing times and pricing info.
        operating_event = next((event for event in schedule if event.get("type") == "OPERATING"), {})

        debug.info(f"Fetching attractions for park: {park_name} (ID: {park_id})")
        api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}/children"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            park_data = response.json()
            debug.log(f"{park_name} Park Data: {park_data}")
        except requests.RequestException as e:
            debug.error(f"Failed to fetch attractions for park {park_name}: {e}")
            continue

        attractions = []
        for item in park_data.get("children", []):
            if (item.get("entityType") == "ATTRACTION") or (item.get("entityType") == "SHOW" and "Meet" in item.get("name", "")): # and (item.get("id") in troublesome_attraction_64x64_ids or item.get("id") in troublesome_attraction_64x32_ids):
                attraction = {
                    "id": item.get("id"),
                    "name": get_attraction_name(item),
                    "entityType": item.get("entityType"),
                    "parkId": park_id,
                    "waitTime": '',      # Placeholder for wait time
                    "status": '',        # Placeholder for status
                    "lastUpdatedTs": ''  # Placeholder for timestamp
                }
                debug.log(f"Attraction found: {attraction}")
                attractions.append(attraction)
        debug.info(f"{len(attractions)} were found in {park_name}")
        park_obj = {
            "id": park_id,
            "name": park_name.replace("Theme", " ").replace("Park", " ").replace("Disney's", "").strip(),
            "attractions": attractions,
            "specialTicketedEvent": is_special_event(schedule),
            "closingTime": operating_event.get("closingTime", ""),
            "openingTime": operating_event.get("openingTime", ""),
            "llmpPrice": determine_llmp_price(operating_event),
            "weather": fetch_weather_data(location.get("latitude"), location.get("longitude")),
            "location": location
        }
        parks.append(park_obj)
    return parks


def get_attraction_name(item):
    return item.get("name", "").replace("\u2122", "").replace("–", "-").replace("*", " ").replace("An Original", "")


def is_special_event(schedule):
    return any(
        event.get("type") == "TICKETED_EVENT" and (
            "special ticketed event" in event.get("description", "").lower() or
            "extended evening" in event.get("description", "").lower()
        )
        for event in schedule
    )

def determine_llmp_price(operating_event):
    lightning_lane_multi_pass_price = ""
    if operating_event and "purchases" in operating_event:
        for purchase in operating_event["purchases"]:
            if purchase.get("name") == "Lightning Lane Multi Pass":
                lightning_lane_multi_pass_price = purchase.get("price", {}).get("formatted", "")
                break
    return lightning_lane_multi_pass_price


def get_down_time(last_updated_date, date_format='%Y-%m-%dT%H:%M:%SZ'):
    try:
        target_date = datetime.strptime(last_updated_date, date_format).replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        time_diff = current_time - target_date
        minutes = time_diff.total_seconds() / 60
        return round(minutes)
    except ValueError:
        debug.error(f"Invalid date format: {last_updated_date}")
        return None

async def fetch_live_data_for_attraction(session, attraction):
    """
    Fetch live data for a single attraction.
    If the status is not "CLOSED" or "REFURBISHMENT", update the waitTime.
    """
    current_data = attraction.copy()

    api_url = f"https://api.themeparks.wiki/v1/entity/{attraction['id']}/live"
    debug.info(f"Fetching live data for attraction: {attraction['name']} (ID: {attraction['id']})")
    try:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                live_data_info = data.get('liveData', [])
                if live_data_info:
                    live_data_entry = live_data_info[0]  # Use the first liveData entry
                    attraction["lastUpdatedTs"] = live_data_entry.get("lastUpdated", None)
                    attraction["status"] = live_data_entry.get("status", None)
                    if live_data_entry.get("status") == "DOWN" and live_data_entry.get("entityType") == "ATTRACTION":
                        attraction["waitTime"] = f"Down {get_down_time(live_data_entry.get('lastUpdated'))}"
                    if live_data_entry.get("status") not in ["CLOSED", "REFURBISHMENT","DOWN"]:
                        attraction["waitTime"] = live_data_entry.get("queue", {}) \
                            .get("STANDBY", {}) \
                            .get("waitTime", None)
            else:
                debug.error(f"Failed to fetch live data for {attraction['name']}, Status Code: {response.status}")
    except Exception as e:
        debug.error(f"Error occurred while fetching live data for {attraction['name']}: {e}")
    if current_data != attraction:
        debug.info(f"There is new data for {attraction['name']} | Wait time: {current_data['waitTime']}(Existing) vs {attraction['waitTime']}(New) | Status: {current_data['status']}(Existing) vs {attraction['status']}(New) | Last updated: {get_eastern(current_data['lastUpdatedTs'])}(Existing) vs {get_eastern(attraction['lastUpdatedTs'])}(New)")
    else:
        debug.info(f"No new data for {attraction['name']}")
    return attraction

async def fetch_live_data(attractions):
    """
    Fetch live data for all attractions concurrently.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_live_data_for_attraction(session, attraction) for attraction in attractions]
        results = await asyncio.gather(*tasks)
    debug.info(f"Total live data fetched: {len(results)}")
    return results

def park_has_operating_attraction(park):
    """
    Check if any attraction in the park is operating and has a wait time.
    Returns True if at least one attraction is operating (i.e. its 'status' is not "CLOSED" or "REFURBISHMENT")
    and its 'waitTime' is not None or empty, otherwise returns False.
    """
    debug.info(f"Searching for open rides in {park['name']}")
    for attraction in park.get("attractions", []):
        wait_time = attraction.get("waitTime")
        status = attraction.get("status")
        debug.log(
            f"Attraction: {attraction['name']} (Park: {park['name']}) | "
            f"Wait Time: {attraction['waitTime']} | Status: {attraction['status']}"
        )
        if wait_time not in [None, ''] and status.upper() == "OPERATING":
            debug.info(f"Found open ride in {park['name']}: {attraction['name']}")
            return True
    return False


def update_parks_operating_status(parks):
    """
    Updates each park object in the list with a new key 'operating' that is
    True if the park has at least one operating attraction with a valid
    wait time, otherwise False.
    """

    for park in parks:
        is_park_open = park_has_operating_attraction(park)  # Check if any attractions are operating

        # Check if the park was previously closed
        previously_operating = park.get("operating")

        # If the park was previously closed but is now open
        if not previously_operating and is_park_open:
            debug.info(f"{park.get('name')} is now operating. Fetching schedule...")
            park["schedule"] = fetch_park_schedule(park.get("id"))  # Fetch the updated schedule
            debug.info(f"Updated schedule for {park.get('name')}")

        # Update the operating status
        park["operating"] = is_park_open

    return parks

if __name__ == "__main__":
    # Fetch parks with filtered schedule (today and yesterday)
    parks_list = fetch_list_of_disney_world_parks()
    debug.info(f"Parks List: {parks_list}")

    # Fetch attractions and additional schedule-derived fields
    parks_with_attractions = fetch_parks_and_attractions(parks_list)
    debug.info(f"Parks with Attractions: {parks_with_attractions}")