#!/usr/bin/sudo
import sys
import time
import os
import logging
import re
import asyncio
import aiohttp
from driver import RGBMatrix
from driver import graphics
from utils import args, led_matrix_options

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL_TEMPLATE = "https://api.themeparks.wiki/v1/entity/{}/live"

def sanitize_text(text):
    """Remove special characters from a given text."""
    return re.sub(r'[^a-zA-Z0-9 ]', '', text)

def fetch_disney_world_parks():
    """Fetch and return a list of Walt Disney World parks with their respective IDs."""
    api_url = "https://api.themeparks.wiki/v1/destinations"
    logging.info("Fetching Disney World park data...")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        parks_data = response.json()

        logging.debug(f"API Response (Parks): {parks_data}")

        # Ensure parks_data is a dictionary
        if not isinstance(parks_data, dict):
            logging.error(f"Unexpected API response format: {parks_data}")
            return []

        # Ensure the 'destinations' key exists and is a list
        destinations = parks_data.get("destinations", [])
        if not isinstance(destinations, list):
            logging.error(f"Unexpected format for 'destinations' key: {destinations}")
            return []

        # Find Walt Disney World in the destinations list
        disney_world = next(
            (destination for destination in destinations if isinstance(destination, dict) and "Walt Disney World" in destination.get("name", "")),
            None
        )

        if not disney_world:
            logging.warning("Walt Disney World data not found in API response.")
            return []

        # Ensure "parks" key exists and is a list
        disney_parks = disney_world.get("parks", [])
        if not isinstance(disney_parks, list):
            logging.error(f"Unexpected format for 'parks' key: {disney_parks}")
            return []

        logging.info(f"Found {len(disney_parks)} parks under Walt Disney World.")

        # Extract park names and IDs
        filtered_parks = [(park.get("name", "Unknown"), park.get("id", "Unknown")) for park in disney_parks if isinstance(park, dict)]
        logging.debug(f"Filtered Parks: {filtered_parks}")

        return filtered_parks

    except requests.RequestException as e:
        logging.error(f"Failed to fetch park data: {e}")
        return []


import requests
import logging

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

        # Check if the park is an attraction (only attractions will have children)
        if "entityType" in park_data and park_data["entityType"] == "ATTRACTION":
            if "children" not in park_data:
                logging.warning(f"No 'children' section found for attraction {park_name} (ID: {park_id}).")
                continue

        # Iterate over each item in the 'children' section
        for item in park_data["children"]:
            # Ensure the item is a dictionary and check if it's an attraction
            if item["entityType"] == "ATTRACTION":
                # logging.warning(f"Item {item} (ID: {item.get("id")}).")
                attraction = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "entityType": item.get("entityType"),
                    "parkId": park_id,
                    "waitTime": '',  # Assuming API might return wait time
                    "status": '',  # Assuming API might return status
                    "lastUpdatedTs": '',  # Assuming API might return timestamp
                }
                logging.info(f"attraction {attraction}")
                attractions.append(attraction)

            # else:
            #     # Log non-attraction data or unexpected structure in 'children'
            #     logging.warning(f"Skipping non-attraction or invalid data in 'children': {item}")

        # logging.debug(f"Found {len(attractions)} attractions for park {park_name}")

    # logging.info(f"Total attractions fetched: {len(attractions)}")
    return attractions



async def fetch_live_data(attractions):
    """Fetch and map live data for attractions, matching by ID and extracting waitTime."""
    live_data = []

    async with aiohttp.ClientSession() as session:
        # Loop through the attractions to fetch live data
        for attraction in attractions:
            api_url = f"https://api.themeparks.wiki/v1/entity/{attraction['id']}/live"
            logging.info(f"Fetching live data for attraction: {attraction['name']} (ID: {attraction['id']})")

            try:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logging.debug(f"Live Data for {attraction['name']}: {data}")

                        # Check if there is any liveData
                        live_data_info = data.get('liveData', [])
                        if live_data_info:
                            # Assuming waitTime is a part of liveData

                            live_data_entry = live_data_info[0]  # Assuming we're interested in the first liveData entry
                            logging.debug(f"Live Data for {live_data_entry}")
                            if live_data_entry.get("status") not in ["CLOSED", "REFURBISHMENT"]:
                                attraction["waitTime"] = live_data_entry.get("queue", {}).get("STANDBY", {}).get("waitTime", None)  # Defaulting to "N/A" if no waitTime
                            attraction["status"] = live_data_entry.get("status", None)
                            attraction["lastUpdatedTs"] = live_data_entry.get("lastUpdated", None)

                        # Add the updated attraction to live_data list
                        live_data.append(attraction)

                    else:
                        logging.error(f"Failed to fetch live data for {attraction['name']}, Status Code: {response.status}")

            except Exception as e:
                logging.error(f"Error occurred while fetching live data for {attraction['name']}: {e}")

    logging.info(f"Total live data fetched: {len(live_data)}")
    return live_data


async def fetch_live_data_for_attractions(attractions, max_concurrent_requests=10):
    """Fetch live wait times for all attractions asynchronously."""
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(limited_fetch(semaphore, session, attraction)) for attraction in attractions]
        await asyncio.gather(*tasks)


async def limited_fetch(semaphore, session, attraction):
    """Wrap fetch function with semaphore to limit concurrent requests."""
    async with semaphore:
        await fetch_live_data(session, attraction)


def update_attractions_with_live_data(attractions):
    """Run the async live data fetcher in a synchronous environment."""
    logging.info("Updating attractions with live wait times...")
    asyncio.run(fetch_live_data_for_attractions(attractions))

def wrap_text(font, text, max_width):
    """Wrap text to fit within the specified max_width."""
    lines = []
    current_line = ""
    for word in text.split():
        test_line = f"{current_line} {word}".strip() if current_line else word
        line_width = sum([font.CharacterWidth(ord(char)) for char in test_line])

        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def render_ride_info(matrix, ride_info):
    """Render Disney ride and wait time on the matrix with text wrapping and centering."""
    logging.debug(f"Rendering ride info: {ride_info}")

    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} mins"

    font = graphics.Font()
    font.LoadFont("assets/fonts/patched/4x6-legacy.bdf")

    max_width = matrix.width

    wrapped_ride_name = wrap_text(font, ride_name, max_width)
    wrapped_wait_time = wrap_text(font, wait_time, max_width)

    ride_name_width = sum([font.CharacterWidth(ord(char)) for char in ride_name])
    total_ride_name_height = len(wrapped_ride_name) * 8

    wait_time_width = sum([font.CharacterWidth(ord(char)) for char in wait_time])
    total_wait_time_height = len(wrapped_wait_time) * 8

    logging.debug(f"Ride Name: '{ride_name}' | Width: {ride_name_width} pixels")
    logging.debug(f"Total Ride Name Height: {total_ride_name_height} pixels")
    logging.debug(f"Wait Time: '{wait_time}' | Width: {wait_time_width} pixels")
    logging.debug(f"Total Wait Time Height: {total_wait_time_height} pixels")

    total_height = total_ride_name_height + total_wait_time_height
    y_position_start = (matrix.height - total_height) // 2
    logging.debug(f"Total Text Block Height: {total_height} pixels")
    logging.debug(f"Starting Vertical Position (y): {y_position_start} pixels")

    y_position_ride = y_position_start
    y_position_time = y_position_ride + total_ride_name_height

    for i, line in enumerate(wrapped_ride_name):
        ride_name_line_width = sum([font.CharacterWidth(ord(char)) for char in line])
        x_position = (matrix.width - ride_name_line_width) // 2
        graphics.DrawText(matrix, font=font, x=x_position, y=y_position_ride + i * 8, color=(255, 255, 255), text=line)

    for i, line in enumerate(wrapped_wait_time):
        wait_time_line_width = sum([font.CharacterWidth(ord(char)) for char in line])
        x_position_time = (matrix.width - wait_time_line_width) // 2
        graphics.DrawText(matrix, font=font, x=x_position_time, y=y_position_time + i * 8, color=(255, 255, 255),
                          text=line)


def update_attractions_with_live_data(attractions):
    logging.info("Updating attractions with live wait times...")
    # This will update all attractions at once and return the updated list.
    live_data = asyncio.run(fetch_live_data(attractions))
    return live_data

def main():
    from driver import RGBMatrixOptions
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)
    matrix = RGBMatrix(options=matrixOptions)

    logging.info("Starting Disney Ride Wait Time Display...")

    try:
        disney_park_list = fetch_disney_world_parks()
        if not disney_park_list:
            logging.error("No Disney parks found. Exiting.")
            return

        attractions = fetch_attractions(disney_park_list)
        if not attractions:
            logging.error("No attractions found. Exiting.")
            return

        while True:
            logging.info("Refreshing live wait times...")
            # Update attractions with live data and assign the updated list back.
            attractions = update_attractions_with_live_data(attractions)

            for ride_info in attractions:
                matrix.Clear()
                logging.info(f"Displaying ride: {ride_info['name']} | Wait Time: {ride_info['waitTime']} min | Status: {ride_info['status']}")
                # logging.info(f"Is a digit: {ride_info.get("waitTime").isdigit()}")
                if ride_info.get("status") not in ["CLOSED", "REFURBISHMENT"] and ride_info.get("waitTime") is not None:
                    render_ride_info(matrix, ride_info)
                    time.sleep(15)

            time.sleep(20)  # Refresh data every minute

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        matrix.Clear()

if __name__ == "__main__":
    main()

