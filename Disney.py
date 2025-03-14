#!/usr/bin/sudo
import json
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
    """Fetch and return a list of Walt Disney World parks with their respective IDs, excluding water parks."""
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

        # For this example, let's say we want parks with "Animal" in their name.
        filtered_parks = [
            (park.get("name", "Unknown"), park.get("id", "Unknown"))
            for park in disney_parks
            if isinstance(park, dict) and "Water Park" not in park.get("name", "")
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


def draw_text_with_dynamic_spacing(matrix, font, y, color, text, max_width):
    """
    Draw a single line of text centered horizontally. If the total width of the text
    exceeds max_width, reduce the spacing between letters dynamically so that the text fits.
    """
    original_width = sum(font.CharacterWidth(ord(ch)) for ch in text)
    if original_width <= max_width:
        x = (max_width - original_width) // 2
        graphics.DrawText(matrix, font, x, y, color, text)
    else:
        scale = max_width / original_width
        x = 0
        for ch in text:
            ch_width = font.CharacterWidth(ord(ch))
            graphics.DrawText(matrix, font, int(x), y, color, ch)
            x += ch_width * scale


def render_ride_info(matrix, ride_info):
    """Render Disney ride name and wait time in separate blocks with vertical centering and dynamic letter spacing."""
    logging.debug(f"Rendering ride info: {ride_info}")
    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} mins"

    # Load separate fonts.
    logging.info(f"Matrix height: {matrix.height}")
    logging.info(f"Matrix width: {matrix.width}")
    if matrix.height == 64:
        name_font_default = 9
        waittime_font_default = 8
        rideFont = graphics.Font()
        rideFont.LoadFont("assets/fonts/patched/6x9.bdf")
        waittimeFont = graphics.Font()
        waittimeFont.LoadFont("assets/fonts/patched/5x8.bdf")
    elif matrix.height == 32:
        name_font_default = 6
        waittime_font_default = 6
        rideFont = graphics.Font()
        rideFont.LoadFont("assets/fonts/patched/4x6-legacy.bdf")
        waittimeFont = graphics.Font()
        waittimeFont.LoadFont("assets/fonts/patched/4x6-legacy.bdf")
    else:
        logging.error("Unsupported matrix height. Please use 32 or 64.")
        return

    name_line_height = getattr(rideFont, "height", name_font_default)
    waittime_line_height = getattr(waittimeFont, "height", waittime_font_default)
    baseline_offset = 5
    gap = 2
    max_width = matrix.width

    wrapped_ride_name = wrap_text(rideFont, ride_name, max_width)
    wrapped_wait_time = wrap_text(waittimeFont, wait_time, max_width)
    ride_name_height = len(wrapped_ride_name) * name_line_height
    wait_time_height = len(wrapped_wait_time) * waittime_line_height
    total_height = ride_name_height + gap + wait_time_height
    start_y = (matrix.height - total_height) // 2 + baseline_offset

    logging.debug(f"Name Font height: {name_line_height}")
    logging.debug(f"Wait Time Font height: {waittime_line_height}")
    logging.debug(f"Ride Name Lines: {len(wrapped_ride_name)} => {ride_name_height} px")
    logging.debug(f"Wait Time Lines: {len(wrapped_wait_time)} => {wait_time_height} px")
    logging.debug(f"Total text block height: {total_height}")
    logging.debug(f"Starting Y position (with offset): {start_y}")

    color_white = graphics.Color(255, 255, 255)
    y_position_ride = start_y
    for i, line in enumerate(wrapped_ride_name):
        draw_text_with_dynamic_spacing(matrix, rideFont, y_position_ride + i * name_line_height, color_white, line, max_width)
    y_position_wait = start_y + ride_name_height + gap
    for i, line in enumerate(wrapped_wait_time):
        draw_text_with_dynamic_spacing(matrix, waittimeFont, y_position_wait + i * waittime_line_height, color_white, line, max_width)


def render_park_name(matrix, park_name):
    """Render the park name centered on the board, wrapping onto multiple lines if needed."""
    # Load the font.
    font = graphics.Font()
    font.LoadFont("assets/fonts/patched/6x9.bdf")
    color_red = graphics.Color(255, 0, 0)

    max_width = matrix.width
    # Get the font's height (fallback to 9 if not available)
    line_height = getattr(font, "height", 9)

    # Wrap the park name into multiple lines if needed.
    wrapped_lines = wrap_text(font, park_name, max_width)

    # Compute the total height of the block.
    total_height = len(wrapped_lines) * line_height
    # Center the block vertically (adjust baseline_offset if needed).
    baseline_offset = 6  # adjust this if text appears too high or too low
    start_y = (matrix.height - total_height) // 2 + baseline_offset

    # Draw each line centered horizontally.
    for i, line in enumerate(wrapped_lines):
        # Compute the width of this line.
        line_width = sum(font.CharacterWidth(ord(ch)) for ch in line)
        x = (max_width - line_width) // 2
        y = start_y + i * line_height
        graphics.DrawText(matrix, font, x, y, color_red, line)

def update_parks_live_data(parks):
    """
    For each park in parks, update its attractions with live data.
    Each park object in parks has a key 'attractions' that is a list of rides.
    """
    for park in parks:
        if park.get("attractions"):
            updated_attractions = asyncio.run(fetch_live_data(park["attractions"]))
            park["attractions"] = updated_attractions

    logging.debug(f"JSON: {logJSONPrettyPrint(parks)}")
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
            parks_holder[:] = updated_parks
            logging.info("Parks live data updated in background.")
        else:
            logging.warning("No parks found during live data update.")
        time.sleep(update_interval)


def main():
    logo_path = os.path.abspath("./assets/MK.png")
    from driver import RGBMatrixOptions
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)
    matrix = RGBMatrix(options=matrixOptions)
    logging.info("Starting Disney Ride Wait Time Display...")

    # If a logo exists, you might display it here.
    if os.path.exists(logo_path) and False:
        logging.info("Logo found. Displaying...")
        from PIL import Image
        logo = Image.open(logo_path)
        matrix.SetImage(logo.convert("RGB"))
        logo.close()

    disney_park_list = fetch_disney_world_parks()
    if not disney_park_list:
        logging.error("No Disney parks found. Exiting.")
        return

    # parks_holder is now a list of park objects (each with its attractions list).
    parks_holder = []
    update_interval = 300  # seconds
    update_thread = threading.Thread(
        target=live_data_updater,
        args=(disney_park_list, update_interval, parks_holder),
        daemon=True
    )
    update_thread.start()

    try:
        # Main display loop: iterate over parks and their attractions.
        while True:
            logging.debug(f"LLL Park Data: {logJSONPrettyPrint(parks_holder)}")
            if parks_holder:
                for park in parks_holder:
                    # Display the park name centered on the board.
                    matrix.Clear()
                    render_park_name(matrix, park["name"])
                    # Allow the park name to be displayed for a few seconds.
                    time.sleep(5)
                    for ride_info in park.get("attractions", []):
                        matrix.Clear()
                        logging.info(f"Displaying ride: {ride_info['name']} (Park: {park['name']}) | Wait Time: {ride_info['waitTime']} min | Status: {ride_info['status']}")
                        if (ride_info.get("status") not in ["CLOSED", "REFURBISHMENT"]
                                and ride_info.get("waitTime") is not None):
                            render_ride_info(matrix, ride_info)
                            time.sleep(15)
            else:
                logging.info("No parks data yet, waiting...")
                time.sleep(5)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        matrix.Clear()


def logJSONPrettyPrint(jsonObj):
    return "\n%s" + json.dumps(jsonObj, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
