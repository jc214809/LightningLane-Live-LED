import sys
import os
import time
import logging
import threading
import json
import traceback
from datetime import datetime, timedelta

import driver
from driver import RGBMatrix, __version__

from display.park.park_details import render_park_information_screen
from display.display import initialize_fonts
from display.startup import render_mickey_logo
from utils.utils import args, led_matrix_options
from api.disney_api import fetch_list_of_disney_world_parks
from display.attractions.attraction_info import render_attraction_info
from updater.data_updater import live_data_updater
from display.countdown.countdown import render_countdown_to_disney

from utils import debug
import io


def test_load_config_with_dummy(monkeypatch):
    # Define a dummy JSON configuration string.
    dummy_config = '{"debug": true, "trip_countdown": {"trip_date": "2023-10-01", "enabled": true}}'

    # Monkeypatch builtins.open to return a StringIO object with dummy_config content.
    monkeypatch.setattr("builtins.open", lambda file, mode='r': io.StringIO(dummy_config))

    # Call load_config which will read from our dummy configuration.
    config = load_config('config.json')

    # Assert that the configuration is loaded as expected.
    assert config["debug"] is True
    assert config["trip_countdown"]["trip_date"] == "2023-10-01"
    assert config["trip_countdown"]["enabled"] is True

# Configure logging
def load_config(file_path):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

logger = logging.getLogger("disney-lll")
if load_config('config.json')['debug']:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

use_image_logo = False

def main():
    # Load configuration
    config = load_config('config.json')
    parks_data = []
    update_interval = 300  # 5 minutes (300 seconds)

    # Check Python version.
    if sys.version_info <= (3, 5):
        debug.error("Please run with python3")
        sys.exit(1)

    if driver.is_emulated():
        if driver.hardware_load_failed:
            debug.log("rgbmatrix not installed, falling back to emulator!")

        debug.log("Using RGBMatrixEmulator version %s", __version__)
    else:
        debug.log("Using rgbmatrix version %s", __version__)

    # Use your helper functions to get proper options.
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)

    matrix = RGBMatrix(options=matrixOptions)
    initialize_fonts(matrix.height)

    disney_park_list = fetch_list_of_disney_world_parks()
    if not disney_park_list:
        debug.error("No Disney parks found. Exiting.")
        return

    update_thread = threading.Thread(
        target=live_data_updater,
        args=(disney_park_list, update_interval, parks_data),
        daemon=True
    )
    update_thread.start()

    # Log configured trip dates at startup
    configured_dates = [d.date().isoformat() for d in parse_trip_dates(config)]
    if configured_dates:
        debug.info(f"Configured trip dates: {configured_dates}")
    else:
        debug.info("No trip dates configured.")

    last_active_trip_logged = None
    try:
        while True:
            render_logo(matrix)
            # Determine active trip date each cycle to handle week-after window and upcoming trips
            if config.get('trip_countdown', {}).get('enabled'):
                trip_list = parse_trip_dates(config)
                active_trip = get_active_trip_date(trip_list)
                if active_trip is not None:
                    # Log when the active trip changes
                    if (last_active_trip_logged is None) or (last_active_trip_logged.date() != active_trip.date()):
                        today = datetime.now().date()
                        mode = "Countdown" if active_trip.date() > today else "Magical trip (within 7 days after)"
                        debug.info(f"Trip countdown active date: {active_trip.date().isoformat()} | Mode: {mode}")
                        last_active_trip_logged = active_trip
                    show_trip_countdown(matrix, active_trip)
                else:
                    logging.info("No upcoming trips; countdown hidden.")
            else:
                logging.info("Trip countdown is not enabled.")
            if parks_data:
                for park in parks_data:
                    if not park.get("operating"):
                        logging.info(f"Skipping {park['name']} because no attractions are operating.")
                        continue
                    initialize_park_information_screen(matrix, park)
                    loop_through_attractions(matrix, park)
                    matrix.Clear()
            else:
                debug.info("No parks data yet, waiting...")
                time.sleep(5)
            matrix.Clear()
    except Exception as e:
        matrix.Clear()
        debug.error(f"An error occurred: {e}")
        debug.error(traceback.format_exc())
    finally:
        matrix.Clear()

def validate_date(date_string):
    """Validate the date string and convert it to a datetime object (date-only if needed)."""
    try:
        # Support YYYY-MM-DD (date-only)
        if len(date_string) == 10:
            return datetime.fromisoformat(date_string)
        # Fallback for full ISO strings
        return datetime.fromisoformat(date_string)
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Please use YYYY-MM-DD.")

def parse_trip_dates(config):
    """Return a list of datetime objects from config trip_countdown.
    Supports both legacy "trip_date" (single string) and new "trip_dates" (array of strings).
    """
    tc = config.get('trip_countdown', {})
    dates = []
    if 'trip_dates' in tc and isinstance(tc['trip_dates'], list):
        for s in tc['trip_dates']:
            try:
                dates.append(validate_date(str(s)))
            except Exception:
                debug.warning(f"Ignoring invalid trip date: {s}")
    elif 'trip_date' in tc and tc['trip_date']:
        try:
            dates.append(validate_date(str(tc['trip_date'])))
        except Exception:
            debug.warning(f"Ignoring invalid legacy trip date: {tc['trip_date']}")
    return dates

def get_active_trip_date(trip_dates):
    """Select the active trip date to display.
    - If there are upcoming trips (today or future), choose the closest upcoming date.
    - Otherwise, if we are within 7 days AFTER the most recent past trip, keep showing that trip ("Have a Magical Trip!").
    - If neither, return None.
    """
    if not trip_dates:
        return None
    today = datetime.now().date()
    # Normalize to date (ignore time component)
    date_list = [d.date() for d in trip_dates]
    # If we are within a week after the most recent past trip, keep showing that first
    past = [d for d in date_list if d < today]
    if past:
        last_past = max(past)
        if (today - last_past) <= timedelta(days=7):
            return datetime.combine(last_past, datetime.min.time())
    # Otherwise, pick the closest upcoming (today or future)
    future_or_today = [d for d in date_list if d >= today]
    if future_or_today:
        return datetime.combine(min(future_or_today), datetime.min.time())
    return None

def render_logo(matrix):
    matrix.Clear()
    logo_path = os.path.abspath("./assets/MK.png")
    if os.path.exists(logo_path) and use_image_logo:
        debug.info("Logo found. Displaying...")
        from PIL import Image
        logo = Image.open(logo_path)
        matrix.SetImage(logo.convert("RGB"))
        time.sleep(8)
        logo.close()
    else:
        # If no logo is available, render the Mickey silhouette as an intro.
        debug.info("No logo found. Rendering Mickey silhouette as intro...")
        render_mickey_logo(matrix)
        time.sleep(8)


def initialize_park_information_screen(matrix, park):
    matrix.Clear()
    debug.info(f"Rendering {park['name']} Title Screen.")
    render_park_information_screen(matrix, park)
    time.sleep(8)

def loop_through_attractions(matrix, park):
    for attraction_info in park.get("attractions", []):
        matrix.Clear()
        debug.info(
            f"Displaying ride: {attraction_info['name']} (Park: {park['name']}) | "f"Wait Time: {attraction_info['waitTime']} min | Status: {attraction_info['status']}")
        if (attraction_info.get("status") not in ["CLOSED", "REFURBISHMENT"]
            and attraction_info.get("waitTime") is not None):
            render_attraction_info(matrix, attraction_info)
            time.sleep(8)

def show_trip_countdown(matrix, next_trip_time):
    # Render the next trip count down
    if next_trip_time is None:
        return
    matrix.Clear()
    render_countdown_to_disney(matrix, next_trip_time)
    time.sleep(7)

if __name__ == "__main__":
    main()
