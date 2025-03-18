import sys
import os
import time
import logging
import threading

from display.startup import render_mickey_classic
from utils.utils import logJSONPrettyPrint, args, led_matrix_options
from api.disney_api import fetch_disney_world_parks
from display.display import render_park_name, render_ride_info
from updater.data_updater import live_data_updater

from utils import debug

import driver
from driver import RGBMatrix, RGBMatrixOptions

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(funcName)s - %(message)s')


def main():
    # Check Python version.
    if sys.version_info <= (3, 5):
        debug.error("Please run with python3")
        sys.exit(1)

    logo_path = os.path.abspath("./assets/MK.png")

    # Use your helper functions to get proper options.
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)

    matrix = RGBMatrix(options=matrixOptions)
    logging.info("Starting Disney Ride Wait Time Display...")

    # Optional: Display a logo if available.
    if os.path.exists(logo_path) and False:
        logging.info("Logo found. Displaying...")
        from PIL import Image
        logo = Image.open(logo_path)
        matrix.SetImage(logo.convert("RGB"))
        # time.sleep(30)
        logo.close()
    else:
        # If no logo is available, render the Mickey silhouette as an intro.
        logging.info("No logo found. Rendering Mickey silhouette as intro...")
        render_mickey_classic(matrix)
        # time.sleep(30)

    disney_park_list = fetch_disney_world_parks()
    if not disney_park_list:
        logging.error("No Disney parks found. Exiting.")
        return

    parks_holder = []
    update_interval = 300  # seconds

    update_thread = threading.Thread(
        target=live_data_updater,
        args=(disney_park_list, update_interval, parks_holder),
        daemon=True
    )
    update_thread.start()

    try:
        while True:
            logging.debug(f"Parks Data: {logJSONPrettyPrint(parks_holder)}")
            if parks_holder:
                for park in parks_holder:
                    if not park.get("operating"):
                        logging.info(f"Skipping park {park['name']} because no attractions are operating.")
                        continue
                    matrix.Clear()
                    logging.info(f"Rendering {park['name']} Title Screen.")
                    render_park_name(matrix, park["name"])
                    time.sleep(5)
                    for ride_info in park.get("attractions", []):
                        matrix.Clear()
                        logging.info(
                            f"Displaying ride: {ride_info['name']} (Park: {park['name']}) | "
                            f"Wait Time: {ride_info['waitTime']} min | Status: {ride_info['status']}"
                        )
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


if __name__ == "__main__":
    main()
