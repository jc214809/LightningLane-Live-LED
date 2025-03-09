#!/usr/bin/sudo
import sys
import time
import os
import requests
from driver import RGBMatrix
from driver import graphics
import debug

from utils import args, led_matrix_options


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


def wrap_text(font, text, max_width):
    """Wrap text to fit within the specified max_width."""
    lines = []
    current_line = ""
    for word in text.split():
        # Check if adding the next word would exceed the max_width
        test_line = f"{current_line} {word}".strip() if current_line else word
        line_width = sum([font.CharacterWidth(ord(char)) for char in test_line])

        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word  # Start new line with the current word

    # Add the last line if there's any remaining text
    if current_line:
        lines.append(current_line)

    return lines


def render_ride_info(matrix, ride_info):
    """Render Disney ride and wait time on the matrix with text wrapping."""
    # Set the text and position to render
    ride_name = ride_info["Ride"]
    wait_time = f"{ride_info['Wait Time']} mins"

    # Create a font object
    font = graphics.Font()  # Adjust based on how the font should be initialized in the library
    font.LoadFont("assets/fonts/patched/4x6-legacy.bdf")  # Adjust this path

    # Calculate the max width of the display
    max_width = matrix.width

    # Wrap the text for the ride name and wait time
    wrapped_ride_name = wrap_text(font, ride_name, max_width)
    wrapped_wait_time = wrap_text(font, wait_time, max_width)

    # Calculate vertical position for the first line of the ride name
    y_position_ride = 8  # Starting position for ride name
    y_position_time = y_position_ride + len(wrapped_ride_name) * 8  # Set the wait time's y position below the ride name

    # Draw the wrapped ride name lines
    for i, line in enumerate(wrapped_ride_name):
        ride_name_width = sum([font.CharacterWidth(ord(char)) for char in line])
        x_position = (matrix.width - ride_name_width) // 2  # Center the text
        graphics.DrawText(matrix, font=font, x=x_position, y=y_position_ride + i * 8, color=(255, 255, 255), text=line)

    # Draw the wrapped wait time lines
    for i, line in enumerate(wrapped_wait_time):
        wait_time_width = sum([font.CharacterWidth(ord(char)) for char in line])
        x_position_time = (matrix.width - wait_time_width) // 2  # Center the wait time
        graphics.DrawText(matrix, font=font, x=x_position_time, y=y_position_time + i * 8, color=(255, 255, 255), text=line)


def main():
    # Initialize the matrix options using the appropriate object type
    from driver import RGBMatrixOptions
    # Check for led configuration arguments
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)

    # Initialize the matrix
    matrix = RGBMatrix(options=matrixOptions)

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
