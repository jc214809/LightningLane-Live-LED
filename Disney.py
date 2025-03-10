#!/usr/bin/sudo
import sys
import time
import os
import requests
import logging
import re
from driver import RGBMatrix
from driver import graphics
import debug

from utils import args, led_matrix_options

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def sanitize_text(text):
    """Remove special characters from a given text."""
    return re.sub(r'[^a-zA-Z0-9 ]', '', text)


def fetch_disney_world_park_ids():
    """Fetch and return a list of Disney World parks with their respective IDs."""
    api_url = "https://queue-times.com/parks.json"
    response = requests.get(api_url)
    parks_data = response.json()

    disney_attractions = next(
        (company for company in parks_data if company["name"] == "Walt Disney Attractions"),
        None
    )

    if not disney_attractions:
        return []

    disney_world_park_names = {
        "Disney Magic Kingdom",
        "Disney Hollywood Studios",
        # "Animal Kingdom",
        "Epcot"
    }

    return [
        (park["name"], park["id"])
        for park in disney_attractions["parks"]
        if park["name"] in disney_world_park_names
    ]


def fetch_wait_times(disney_park_list, exclude_closed=False):
    """Fetch and return an array containing park, land, ride, wait time, category, and open status."""
    wait_times_data = []
    #API to get only Attractions from Walt Disney World Magic Kingdom
    #https://api.themeparks.wiki/preview/parks/WaltDisneyWorldMagicKingdom/waittime?type=ATTRACTION

    #Attractions Details - example TRON
    #https://api.themeparks.wiki/v1/entity/5a43d1a7-ad53-4d25-abfe-25625f0da304/live
    for park_name, park_id in disney_park_list:
        api_url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
        response = requests.get(api_url)
        park_wait_times = response.json()

        logging.debug(f"Fetched wait times JSON: {park_wait_times}")

        if "lands" not in park_wait_times:
            continue

        for park_area in park_wait_times["lands"]:
            for attraction in park_area["rides"]:
                if exclude_closed and not attraction["is_open"]:
                    continue

                category = "Character Meet and Greet" if "Meet" in attraction["name"] else "Attraction"
                sanitized_ride_name = sanitize_text(attraction["name"])

                wait_times_data.append({
                    "Park": park_name,
                    "Land": park_area["name"],
                    "Ride": sanitized_ride_name,
                    "Wait Time": attraction["wait_time"],
                    "Category": category,
                    "Open": attraction["is_open"]
                })

    return wait_times_data


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

    ride_name = ride_info["Ride"]
    wait_time = f"{ride_info['Wait Time']} mins"

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


def main():
    from driver import RGBMatrixOptions
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)
    matrix = RGBMatrix(options=matrixOptions)

    try:
        disney_park_list = fetch_disney_world_park_ids()

        if disney_park_list:
            exclude_closed = True  # Set this flag to True to exclude closed rides
            disney_wait_times = fetch_wait_times(disney_park_list, exclude_closed)

            if not disney_wait_times:
                logging.info("No rides available.")
                return

            while True:
                for ride_info in disney_wait_times:
                    matrix.Clear()
                    render_ride_info(matrix, ride_info)
                    time.sleep(15)
        time.sleep(60)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        matrix.Clear()


if __name__ == "__main__":
    main()
