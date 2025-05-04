import sys
import os
import time
import logging
import threading
import json
from datetime import datetime

from display.park.park_details import render_park_information_screen
from display.display import initialize_fonts
from display.startup import render_mickey_logo
from utils.utils import args, led_matrix_options
from api.disney_api import fetch_list_of_disney_world_parks
from display.attractions.attraction_info import render_attraction_info
from updater.data_updater import live_data_updater
from display.countdown.countdown import render_countdown_to_disney

from utils import debug

import driver
from driver import RGBMatrix, RGBMatrixOptions

# Configure logging
def load_config(file_path):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

def get_logging_level():
    if load_config('config.json')['debug']:
        return logging.DEBUG
    else:
        return logging.INFO

logging.basicConfig(level=get_logging_level(), format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(funcName)s - %(message)s')

use_image_logo = False

def main():
    # Load configuration
    config = load_config('config.json')
    next_trip_time = validate_date(config['trip_countdown']['trip_date'])
    parks_data = []
    update_interval = 300  # 5 minutes (300 seconds)

    # Check Python version.
    if sys.version_info <= (3, 5):
        debug.error("Please run with python3")
        sys.exit(1)

    # Use your helper functions to get proper options.
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)

    matrix = RGBMatrix(options=matrixOptions)
    initialize_fonts(matrix.height)

    disney_park_list = fetch_list_of_disney_world_parks()
    if not disney_park_list:
        logging.error("No Disney parks found. Exiting.")
        return

    update_thread = threading.Thread(
        target=live_data_updater,
        args=(disney_park_list, update_interval, parks_data),
        daemon=True
    )
    update_thread.start()

    try:
        while True:
            render_logo(matrix)
            show_trip_countdown(matrix, next_trip_time) if (config['trip_countdown']['enabled']) else logging.info("Trip countdown is not enabled.")
            if parks_data:
                for park in parks_data:
                    if not park.get("operating"):
                        logging.info(f"Skipping {park['name']} because no attractions are operating.")
                        continue
                    initialize_park_information_screen(matrix, park)
                    loop_through_attractions(matrix, park)
                    matrix.Clear()
            else:
                logging.info("No parks data yet, waiting...")
                time.sleep(5)
            matrix.Clear()
    except Exception as e:
        matrix.Clear()
        logging.error(f"An error occurred: {e}")
    finally:
        matrix.Clear()

def validate_date(date_string):
    """Validate the date string and convert it to a datetime object."""
    try:
        # Attempt to create a datetime object from the string
        date = datetime.fromisoformat(date_string)
        return date
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Please use YYYY-MM-DD.")

def render_logo(matrix):
    matrix.Clear()
    logo_path = os.path.abspath("./assets/MK.png")
    if os.path.exists(logo_path) and use_image_logo:
        logging.info("Logo found. Displaying...")
        from PIL import Image
        logo = Image.open(logo_path)
        matrix.SetImage(logo.convert("RGB"))
        time.sleep(10)
        logo.close()
    else:
        # If no logo is available, render the Mickey silhouette as an intro.
        logging.info("No logo found. Rendering Mickey silhouette as intro...")
        render_mickey_logo(matrix)
        time.sleep(8)


def initialize_park_information_screen(matrix, park):
    matrix.Clear()
    logging.info(f"Rendering {park['name']} Title Screen.")
    render_park_information_screen(matrix, park)
    time.sleep(5)

def loop_through_attractions(matrix, park):
    for attraction_info in park.get("attractions", []):
        matrix.Clear()
        logging.info(
            f"Displaying ride: {attraction_info['name']} (Park: {park['name']}) | "f"Wait Time: {attraction_info['waitTime']} min | Status: {attraction_info['status']}")
        if (attraction_info.get("status") not in ["CLOSED", "REFURBISHMENT"]
            and attraction_info.get("waitTime") is not None):
            render_attraction_info(matrix, attraction_info)
            time.sleep(8)

def show_trip_countdown(matrix, next_trip_time):
    # Render the next trip count down
    matrix.Clear()
    render_countdown_to_disney(matrix, next_trip_time)
    time.sleep(8)

if __name__ == "__main__":
    main()
