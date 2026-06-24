import asyncio
import re
import ssl
from datetime import datetime, timedelta, timezone

import aiohttp
import certifi
import requests

from api.weather import fetch_weather_data
from utils import debug
from utils.utils import get_eastern

troublesome_attraction_64x64_ids = ["8d7ccdb1-a22b-4e26-8dc8-65b1938ed5f0","06c599f9-1ddf-4d47-9157-a992acafc96b", "22f48b73-01df-460e-8969-9eb2b4ae836c",  "9211adc9-b296-4667-8e97-b40cf76108e4","64a6915f-a835-4226-ba5c-8389fc4cade3"]
troublesome_attraction_64x32_ids = ["9211adc9-b296-4667-8e97-b40cf76108e4","64a6915f-a835-4226-ba5c-8389fc4cade3"]
troublesome_attraction_single_ids = ["1e735ffb-4868-47f1-b2cd-2ac1156cd5f0"]

DISNEY_WORLD_DESTINATION_ID = "e957da41-3552-4cf6-b636-5babc5cbc4e5"
_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


def resolve_destination_id(name_or_id):
    """Return a destination UUID. If name_or_id already looks like a UUID, return it as-is.
    Otherwise fetch the destinations list and match by name (case-insensitive)."""
    if _UUID_RE.match(name_or_id):
        return name_or_id
    try:
        response = requests.get("https://api.themeparks.wiki/v1/destinations")
        response.raise_for_status()
        destinations = response.json().get("destinations", [])
        name_lower = name_or_id.lower()
        for dest in destinations:
            if dest.get("name", "").lower() == name_lower:
                debug.info(f"Resolved destination '{name_or_id}' → {dest['id']}")
                return dest["id"]
        debug.error(f"No destination found matching '{name_or_id}'")
        return None
    except requests.RequestException as e:
        debug.error(f"Failed to fetch destinations list: {e}")
        return None


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

WATER_PARK_KEYWORDS = ("Water Park", "Shores")

def fetch_parks_from_destination(destination_id):
    """
    Fetch parks from any ThemeParks Wiki destination, excluding water parks.
    Schedule is filtered to today and yesterday only.
    """
    api_url = f"https://api.themeparks.wiki/v1/entity/{destination_id}/schedule"
    debug.info("Fetching parks for destination %s", destination_id)

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        parks_data = response.json().get("parks", [])

        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

        is_disney = destination_id == DISNEY_WORLD_DESTINATION_ID
        filtered_parks = []
        for park in parks_data:
            if not isinstance(park, dict):
                continue
            park_name = park.get("name", "")
            if any(kw in park_name for kw in WATER_PARK_KEYWORDS):
                continue
            schedule = park.get("schedule") or []
            schedule_filtered = [
                event for event in schedule if event.get("date") in (today_str, yesterday_str)
            ]
            debug.log(f"Schedule Filter: {schedule_filtered}")
            filtered_parks.append({
                "name": clean_park_name(park_name) if is_disney else park_name,
                "id": park.get("id", "Unknown"),
                "schedule": schedule_filtered,
                "weather": [],
                "location": get_park_location(park.get("id"))
            })

        debug.info(f"Found {len(filtered_parks)} parks for destination {destination_id}.")
        return filtered_parks

    except requests.RequestException as e:
        debug.error(f"Failed to fetch parks for destination {destination_id}: {e}")
        return []


def fetch_list_of_disney_world_parks():
    """Fetch Walt Disney World parks. Retained for backward compatibility."""
    return fetch_parks_from_destination(DISNEY_WORLD_DESTINATION_ID)


def resolve_parks_from_config(park_names):
    """
    Given a list of park names from config, fetch only the destinations that contain
    those parks and return the matching park dicts. Matches against both raw API names
    and Disney-cleaned names, case-insensitively. If park_names is empty, returns all
    Walt Disney World parks.
    """
    if not park_names:
        return fetch_list_of_disney_world_parks()

    try:
        response = requests.get("https://api.themeparks.wiki/v1/destinations")
        response.raise_for_status()
        destinations = response.json().get("destinations", [])
    except requests.RequestException as e:
        debug.error(f"Failed to fetch destinations list: {e}")
        return []

    names_lower = {n.lower() for n in park_names}

    # Map destination_id -> set of matched park IDs
    dest_park_ids = {}
    for dest in destinations:
        dest_id = dest["id"]
        is_disney = dest_id == DISNEY_WORLD_DESTINATION_ID
        for park in dest.get("parks", []):
            raw = park.get("name", "")
            cleaned = clean_park_name(raw) if is_disney else raw
            if raw.lower() in names_lower or cleaned.lower() in names_lower:
                dest_park_ids.setdefault(dest_id, set()).add(park["id"])

    if not dest_park_ids:
        debug.error(f"No destinations found for parks: {park_names}")
        return []

    result = []
    for dest_id, park_ids in dest_park_ids.items():
        parks = fetch_parks_from_destination(dest_id)
        result.extend(p for p in parks if p["id"] in park_ids)

    name_to_index = {n.lower(): i for i, n in enumerate(park_names)}
    result.sort(key=lambda p: name_to_index.get(p["name"].lower(), len(park_names)))

    debug.info(f"Resolved {len(result)} park(s) from config: {[p['name'] for p in result]}")
    return result


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
            if item.get("entityType") in ("ATTRACTION", "SHOW"):
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
            "name": park_name,
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


def clean_park_name(raw_name):
    return raw_name.replace("Theme", " ").replace("Park", " ").replace("Disney's", "").strip()


def get_attraction_name(item):
    return item.get("name", "").replace("\u2122", "").replace("–", "-").replace("*", " ").replace("An Original", "").replace(" at Mickey's Not-So-Scary Halloween Party", "")


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
                        queue = live_data_entry.get("queue", {})
                        standby_wait = queue.get("STANDBY", {}).get("waitTime", None)
                        if standby_wait is not None:
                            attraction["waitTime"] = standby_wait
                        else:
                            bg = queue.get("BOARDING_GROUP", {})
                            start = bg.get("currentGroupStart")
                            end = bg.get("currentGroupEnd")
                            if start is not None and end is not None:
                                attraction["waitTime"] = f"Groups {start}-{end}"
                            elif start is not None:
                                attraction["waitTime"] = f"Group {start}+"
                            else:
                                attraction["waitTime"] = None
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
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(connector=connector) as session:
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
    debug.info(f"Searching for open attraction's in {park['name']}")
    for attraction in park.get("attractions", []):
        wait_time = attraction.get("waitTime")
        status = attraction.get("status")
        debug.log(
            f"Attraction: {attraction['name']} (Park: {park['name']}) | "
            f"Wait Time: {attraction['waitTime']} | Status: {attraction['status']}"
        )
        if wait_time not in [None, ''] and status.upper() == "OPERATING":
            debug.info(f"Found open attraction in {park['name']}: {attraction['name']}")
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
        handle_park_schedule_update(is_park_open, park)
        # Update the operating status
        park["operating"] = is_park_open

    return parks


def handle_park_schedule_update(is_park_open, park):
    # Check if the park was previously closed
    previously_operating = park.get("operating")
    # If the park was previously closed but is now open
    if not previously_operating and is_park_open:
        debug.info(f"{park.get('name')} is now operating. Fetching schedule...")
        schedule = fetch_park_schedule(park.get("id"))
        park["schedule"] = schedule
        debug.info(f"Updated schedule for {park.get('name')}")

        # Update park schedule details
        operating_event = next((event for event in schedule if event.get("type") == "OPERATING"), {})
        park["llmpPrice"] = determine_llmp_price(operating_event)
        park["specialTicketedEvent"] = is_special_event(schedule)
        park["closingTime"] = operating_event.get("closingTime", "")
        park["openingTime"] = operating_event.get("openingTime", "")

        refresh_park_attractions(park)


def refresh_park_attractions(park):
    """
    Re-fetch the children endpoint when a park opens and reconcile the attraction list:
    update names, add new attractions, remove ones no longer returned.
    """
    park_id = park.get("id")
    park_name = park.get("name", "Unknown")
    api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}/children"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        children = response.json().get("children", [])
    except requests.RequestException as e:
        debug.error(f"Failed to refresh attractions for {park_name}: {e}")
        return

    fresh = {
        item["id"]: item
        for item in children
        if item.get("entityType") in ("ATTRACTION", "SHOW")
    }

    existing = park.get("attractions", [])

    for attr in existing:
        if attr["id"] in fresh:
            attr["name"] = get_attraction_name(fresh[attr["id"]])

    existing_ids = {a["id"] for a in existing}
    for attr_id, item in fresh.items():
        if attr_id not in existing_ids:
            existing.append({
                "id": attr_id,
                "name": get_attraction_name(item),
                "entityType": item.get("entityType"),
                "parkId": park_id,
                "waitTime": "",
                "status": "",
                "lastUpdatedTs": "",
                "down_since": ""
            })
            debug.info(f"New attraction added to {park_name}: {get_attraction_name(item)}")

    before = len(existing)
    park["attractions"] = [a for a in existing if a["id"] in fresh]
    removed = before - len(park["attractions"])
    if removed:
        debug.info(f"Removed {removed} attraction(s) from {park_name} no longer in roster")

    debug.info(f"Refreshed {len(park['attractions'])} attractions for {park_name}")


if __name__ == "__main__":
    # Fetch parks with filtered schedule (today and yesterday)
    parks_list = fetch_list_of_disney_world_parks()
    debug.info(f"Parks List: {parks_list}")

    # Fetch attractions and additional schedule-derived fields
    parks_with_attractions = fetch_parks_and_attractions(parks_list)
    debug.info(f"Parks with Attractions: {parks_with_attractions}")