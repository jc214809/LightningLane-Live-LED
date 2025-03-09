#!/usr/bin/sudo
import sys
import time
import os
import requests
from driver import RGBMatrix
from driver import graphics
import debug


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
        "Animal Kingdom",
        "Disney Hollywood Studios",
        "Disney Magic Kingdom",
        "Epcot"
    }

    return [
        (park["name"], park["id"])
        for park in disney_attractions["parks"]
        if park["name"] in disney_world_park_names
    ]


def fetch_wait_times(disney_park_list):
    """Fetch and return an array containing park, land, ride, wait time, category, and open status."""
    wait_times_data = []

    for park_name, park_id in disney_park_list:
        api_url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
        response = requests.get(api_url)
        park_wait_times = response.json()

        if "lands" not in park_wait_times:
            continue

        for park_area in park_wait_times["lands"]:
            for attraction in park_area["rides"]:
                # Determine category based on ride name
                category = "Character Meet and Greet" if "Meet" in attraction["name"] else "Attraction"

                # Append ride information to list
                wait_times_data.append({
                    "Park": park_name,
                    "Land": park_area["name"],
                    "Ride": attraction["name"],
                    "Wait Time": attraction["wait_time"],
                    "Category": category,
                    "Open": attraction["is_open"]
                })

    return wait_times_data


def render_ride_info(matrix, ride_info):
    """Render Disney ride and wait time on the matrix."""
    # Set the text and position to render
    ride_name = ride_info["Ride"]
    wait_time = f"{ride_info['Wait Time']} mins"

    # Calculate vertical position based on the matrix size (center the text)
    x_position = 5  # Set horizontal position (you can adjust as needed)
    y_position_ride = 8  # Set vertical position for ride name (adjust as needed)
    y_position_time = 18  # Set vertical position for wait time (adjust as needed)

    # Create a font object
    font = graphics.Font()  # Adjust based on how the font should be initialized in the library
    font.LoadFont("C:/Users/Xxjcl/Documents/GitHub/Disney-LED-QueueVision/assets/fonts/patched/4x6.bdf")  # Adjust this path

    # Draw the ride name at the top
    graphics.DrawText(matrix, font=font, x=x_position, y=y_position_ride, color=(255, 255, 255), text=ride_name)

    # Draw the wait time centered below the ride name
    graphics.DrawText(matrix, font=font, x=x_position, y=y_position_time, color=(255, 255, 255), text=wait_time)


def main():
    # Initialize the matrix options using the appropriate object type
    from driver import RGBMatrixOptions

    # Define the options in an object rather than a dictionary
    options = RGBMatrixOptions()
    options.cols = 64  # Set the matrix width
    options.rows = 32  # Set the matrix height
    options.chain_length = 1  # Adjust based on your setup
    options.hardware_mapping = 'adafruit-hat'  # Adjust this based on your setup

    # Initialize the matrix with the options object
    matrix = RGBMatrix(options=options)

    try:
        # Fetch Disney World parks and their wait times
        disney_park_list = fetch_disney_world_park_ids()

        if disney_park_list:
            disney_wait_times = fetch_wait_times(disney_park_list)

            # If there are no rides to display, exit the program
            if not disney_wait_times:
                print("No rides available.")
                return

            # Rotate through the rides every 15 seconds
            while True:
                for ride_info in disney_wait_times:
                    matrix.Clear()  # Clear the matrix before displaying the next ride's info
                    render_ride_info(matrix, ride_info)  # Display the ride's info
                    time.sleep(15)  # Wait 15 seconds before displaying the next ride

        time.sleep(60)  # Optional: sleep 60 seconds to allow the display to show rides properly
    except Exception as e:
        debug.exception(f"An error occurred: {e}")
    finally:
        matrix.Clear()  # Clear the matrix after rendering


if __name__ == "__main__":
    main()
