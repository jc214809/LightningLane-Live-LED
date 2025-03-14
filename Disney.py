#!/usr/bin/sudo
import os
import time
import logging
import asyncio
import aiohttp
from PIL import Image
import requests
import threading
from driver import RGBMatrix
from driver import graphics
from utils import args, led_matrix_options

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_disney_world_parks():
    """Fetch and return a list of Walt Disney World parks with their respective IDs."""
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

        filtered_parks = [(park.get("name", "Unknown"), park.get("id", "Unknown"))
                          for park in disney_parks if isinstance(park, dict)]
        logging.debug(f"Filtered Parks: {filtered_parks}")

        return filtered_parks

    except requests.RequestException as e:
        logging.error(f"Failed to fetch park data: {e}")
        return []


def fetch_attractions(disney_park_list):
    """Fetch and return a list of attractions with placeholders for live data."""
    attractions = []

    for park_name, park_id in disney_park_list:
        api_url = f"https://api.themeparks.wiki/v1/entity/{park_id}/children"
        logging.info(f"Fetching attractions for park: {park_name} (ID: {park_id})")

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            park_data = response.json()
            logging.debug(f"API Response (Attractions for {park_name}): {park_data}")
        except requests.RequestException as e:
            logging.error(f"Failed to fetch attractions for park {park_name}: {e}")
            continue

        if "entityType" in park_data and park_data["entityType"] == "ATTRACTION":
            if "children" not in park_data:
                logging.warning(f"No 'children' section found for attraction {park_name} (ID: {park_id}).")
                continue

        for item in park_data["children"]:
            if item.get("entityType") == "ATTRACTION":
                attraction = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "entityType": item.get("entityType"),
                    "parkId": park_id,
                    "waitTime": '',      # Placeholder for wait time
                    "status": '',        # Placeholder for status
                    "lastUpdatedTs": ''  # Placeholder for timestamp
                }
                logging.info(f"attraction {attraction}")
                attractions.append(attraction)

    return attractions


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


def wrap_text(font, text, max_width):
    """Wrap text to fit within the specified max_width."""
    lines = []
    current_line = ""
    for word in text.split():
        test_line = f"{current_line} {word}".strip() if current_line else word
        line_width = sum(font.CharacterWidth(ord(char)) for char in test_line)
        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def render_ride_info(matrix, ride_info):
    """Render Disney ride name and wait time in separate blocks with vertical centering and offset."""
    logging.debug(f"Rendering ride info: {ride_info}")

    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} mins"

    # Load a larger rideFont (adjust as desired).
    rideFont = graphics.Font()
    rideFont.LoadFont("assets/fonts/patched/6x9.bdf")
    waittimeFont = graphics.Font()
    waittimeFont.LoadFont("assets/fonts/patched/5x8.bdf")

    # The line height is often in rideFont.height; fallback to 9 if not provided.
    name_line_height = getattr(rideFont, "height", 9)
    waittime_line_height = getattr(waittimeFont, "height", 8)

    # This offset shifts the entire block up/down to fix top/bottom imbalance.
    baseline_offset = 4

    # Optional gap (in pixels) between the ride name block and the wait time block.
    gap = 2

    max_width = matrix.width

    # Wrap text so it doesn't overflow horizontally
    wrapped_ride_name = wrap_text(rideFont, ride_name, max_width)
    wrapped_wait_time = wrap_text(waittimeFont, wait_time, max_width)

    # Calculate the total height of each block
    ride_name_height = len(wrapped_ride_name) * name_line_height
    wait_time_height = len(wrapped_wait_time) * waittime_line_height

    # Combine both blocks' heights + gap to get total height
    total_height = ride_name_height + gap + wait_time_height

    # Compute the top Y position to center vertically
    start_y = (matrix.height - total_height) // 2 + baseline_offset

    logging.debug(f"Name Font height: {name_line_height}")
    logging.debug(f"Wait Time Font height: {waittime_line_height}")
    logging.debug(f"Ride Name Lines: {len(wrapped_ride_name)} => {ride_name_height} px")
    logging.debug(f"Wait Time Lines: {len(wrapped_wait_time)} => {wait_time_height} px")
    logging.debug(f"Total text block height: {total_height}")
    logging.debug(f"Starting Y position (with offset): {start_y}")

    color_white = graphics.Color(255, 255, 255)
    color_blue = graphics.Color(0, 0, 255)

    # Draw Ride Name block
    y_position_ride = start_y
    for i, line in enumerate(wrapped_ride_name):
        line_width = sum(rideFont.CharacterWidth(ord(ch)) for ch in line)
        x_position = (matrix.width - line_width) // 2
        graphics.DrawText(matrix, rideFont, x_position, y_position_ride + i * name_line_height, color_white, line)

    # Draw Wait Time block
    y_position_wait = start_y + ride_name_height + gap
    for i, line in enumerate(wrapped_wait_time):
        line_width = sum(waittimeFont.CharacterWidth(ord(ch)) for ch in line)
        x_position = (matrix.width - line_width) // 2
        graphics.DrawText(matrix, waittimeFont, x_position, y_position_wait + i * waittime_line_height, color_white, line)

def update_attractions_with_live_data(attractions):
    logging.info("Updating attractions with live wait times...")
    live_data = asyncio.run(fetch_live_data(attractions))
    return live_data


def live_data_updater(disney_park_list, update_interval, attractions_holder):
    """
    Background thread function that re-fetches attractions and updates live data
    every 'update_interval' seconds. The results are stored in the shared list 'attractions_holder'.
    """
    while True:
        attractions = fetch_attractions(disney_park_list)
        if attractions:
            updated_attractions = update_attractions_with_live_data(attractions)
            # Update the shared list safely by replacing its content
            attractions_holder[:] = updated_attractions
            logging.info("Attractions live data updated in background.")
        else:
            logging.warning("No attractions found during live data update.")
        time.sleep(update_interval)


def main():

    logo_path = os.path.abspath("./assets/MK.png")


    from driver import RGBMatrixOptions
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)
    matrix = RGBMatrix(options=matrixOptions)
    logging.info("Starting Disney Ride Wait Time Display...")

    # MLB image disabled when using renderer, for now.
    # see: https://github.com/ty-porter/RGBMatrixEmulator/issues/9#issuecomment-922869679
    if os.path.exists(logo_path) and False:
        logging.info("Logo found. Displaying...")
        logo = Image.open(logo_path)
        matrix.SetImage(logo.convert("RGB"))
        logo.close()

    disney_park_list = fetch_disney_world_parks()
    if not disney_park_list:
        logging.error("No Disney parks found. Exiting.")
        return

    # Shared list for attractions updated by the background thread.
    attractions_holder = []

    # Start a background thread to update live data every 5 minutes (300 seconds).
    update_interval = 300  # seconds
    update_thread = threading.Thread(
        target=live_data_updater,
        args=(disney_park_list, update_interval, attractions_holder),
        daemon=True
    )
    update_thread.start()

    try:
        # Main display loop: cycle through the attractions from the shared list.
        while True:
            if attractions_holder:
                for ride_info in attractions_holder:
                    matrix.Clear()
                    logging.info(f"Displaying ride: {ride_info['name']} | Wait Time: {ride_info['waitTime']} min | "
                                 f"Status: {ride_info['status']}")
                    if (ride_info.get("status") not in ["CLOSED", "REFURBISHMENT"]
                            and ride_info.get("waitTime") is not None):
                        render_ride_info(matrix, ride_info)
                        # Display each ride for 15 seconds
                        time.sleep(15)
            else:
                logging.info("No attractions data yet, waiting...")
                time.sleep(5)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        matrix.Clear()


if __name__ == "__main__":
    main()
