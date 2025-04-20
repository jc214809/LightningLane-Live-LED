import os

from PIL import Image
import requests
from io import BytesIO
import logging

from datetime import datetime
from driver import graphics
from utils.utils import logJSONPrettyPrint


def get_text_width(font, text):
    """Helper to calculate total width of text in pixels."""
    return sum(font.CharacterWidth(ord(ch)) for ch in text)


def wrap_text(font, text, max_width, max_height, padding):
    """
    Wrap text to fit within the specified max_width (ignoring max_height here for brevity).
    Returns a list of lines (strings).
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        word_width = get_text_width(font, word)
        if word_width > max_width:
            # Word alone doesn't fit; put it on its own line
            if current_line:
                lines.append(current_line)
                current_line = ""
            lines.append(word)
            continue

        test_line = (current_line + " " + word).strip() if current_line else word
        test_line_width = get_text_width(font, test_line)
        if test_line_width <= max_width - padding:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def load_fonts(matrix_height):
    """Load fonts based on the board height."""
    if matrix_height == 64:
        rideFont = graphics.Font()
        rideFont.LoadFont("assets/fonts/patched/5x8.bdf")
        waittimeFont = graphics.Font()
        waittimeFont.LoadFont("assets/fonts/patched/5x8.bdf")
        logging.info("Matrix height: 64.")
    elif matrix_height == 32:
        rideFont = graphics.Font()
        rideFont.LoadFont("assets/fonts/patched/4x6-legacy.bdf")
        waittimeFont = graphics.Font()
        waittimeFont.LoadFont("assets/fonts/patched/4x6-legacy.bdf")
        logging.info("Matrix height: 32.")
    else:
        logging.error("Unsupported matrix height. Please use 32 or 64.")
        return None, None

    return rideFont, waittimeFont


def calculate_text_height(combined_lines, wrapped_ride_name, name_line_height, waittime_line_height):
    """
    Calculate total height for the combined text and the individual line heights.
    """
    total_lines_height = 0
    line_heights = []  # Store individual line heights
    for line in combined_lines:
        line_height = name_line_height if line in wrapped_ride_name else waittime_line_height
        line_heights.append(line_height)
        total_lines_height += line_height
        logging.debug(f"Line: '{line}' has height: {line_height}")

    return total_lines_height, line_heights


def get_longest_line_width(wrapped_ride_name, combined_lines, rideFont, waittimeFont):
    """
    Calculate the width of the longest line in the combined lines.
    """
    longest_line_width = max(
        get_text_width(rideFont, line) if line in wrapped_ride_name else get_text_width(waittimeFont, line)
        for line in combined_lines
    )
    return longest_line_width


def get_max_lines(board_height, font):
    """
    Calculates the maximum number of lines that can fit on the board.

    Args:
        board_height (int): The height of the matrix board.
        font (graphics.Font): The font used for rendering text.

    Returns:
        int: The maximum number of lines that can fit on the board.
    """
    # Get the height of one line in the specified font
    line_height = getattr(font, "height", 8)  # Default to 8 if height attribute is not available

    # Calculate the maximum number of lines the board can support
    max_lines = board_height // line_height

    logging.debug(f"Board height: {board_height}, Line height: {line_height}, Max lines: {max_lines}")

    return max_lines

def calculate_x_position(matrix, longest_line_width, padding):
    """
    Calculate the x_position for centering the text.
    """
    total_width_with_padding = longest_line_width + 2 * padding  # 1 unit on left and right
    if total_width_with_padding <= matrix.width:
        x_position = (matrix.width - total_width_with_padding) // 2
        logging.debug(f"Padding applied. x_position: {x_position}")
    else:
        x_position = (matrix.width - longest_line_width) // 2
        logging.debug(f"No padding applied. x_position: {x_position}")

    return x_position


def calculate_y_position(matrix, total_lines_height):
    """
    Calculate the y_position to center the text vertically on the board.
    """
    y_position = (matrix.height - total_lines_height) // 2
    logging.debug(f"y_position calculated: {y_position}")
    return y_position


def render_lines(matrix, combined_lines, rideFont, waittimeFont, x_position, y_position, line_heights,
                 wrapped_ride_name):
    """
    Render each line of text at the specified position on the matrix.
    """
    current_y_position = y_position + 5  # Add any necessary offset to center properly
    gap_between_ride_and_wait_time = 2  # Default gap between the sections

    for idx, line in enumerate(combined_lines):
        line_width = get_text_width(rideFont, line) if line in wrapped_ride_name else get_text_width(waittimeFont, line)

        # Center horizontally with or without padding
        line_x_position = (matrix.width - line_width) // 2
        logging.debug(f"Drawing line: '{line}' at position ({line_x_position}, {current_y_position})")

        # Draw the text on the matrix
        text_color = graphics.Color(255, 255, 255)

        if line in wrapped_ride_name:
            graphics.DrawText(matrix, rideFont, line_x_position, current_y_position, text_color,
                              line)
        else:
            if "down" in line.lower():
                text_color = graphics.Color(242, 5, 5)
            graphics.DrawText(matrix, waittimeFont, line_x_position, current_y_position, text_color,
                              line)

        # Move the y_position down for the next line
        current_y_position += line_heights[idx]

        # Add a gap after the ride name section to the wait time section
        if idx == len(wrapped_ride_name) - 1:
            current_y_position += gap_between_ride_and_wait_time


def render_ride_info(matrix, ride_info):
    """
    Renders ride name at the top and wait time at the bottom in a single draw call.
    The combined text block is drawn from the center of the screen.
    Each line is vertically centered, with a dynamic gap between ride name and wait time.
    Padding is added only if the text fits within the width and height of the board.
    """
    logging.debug(f"Rendering ride info: {ride_info}")
    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} Mins"

    # Load fonts based on board height
    rideFont, waittimeFont = load_fonts(matrix.height)
    if not rideFont or not waittimeFont:
        return

    # Wrap the text for both ride name and wait time
    name_line_height = getattr(rideFont, "height")
    waittime_line_height = getattr(waittimeFont, "height")
    wrapped_ride_name = wrap_text(rideFont, ride_name, matrix.width, matrix.height, 1)
    if get_max_lines(matrix.height, rideFont) - 1 < len(wrapped_ride_name):
        wrapped_ride_name = wrap_text(rideFont, ride_name, matrix.width, matrix.height, 0)
    wrapped_wait_time = wrap_text(waittimeFont, wait_time, matrix.width, matrix.height, 1)

    # Combine wrapped ride name and wait time into one list of lines
    combined_lines = wrapped_ride_name + wrapped_wait_time
    combined_lines = [line for line in combined_lines if line.strip() != ""]  # Remove blank lines

    # Calculate the total height of all lines
    total_lines_height, line_heights = calculate_text_height(combined_lines, wrapped_ride_name, name_line_height,
                                                             waittime_line_height)

    # Get the width of the longest line
    longest_line_width = get_longest_line_width(wrapped_ride_name, combined_lines, rideFont, waittimeFont)

    # Calculate x and y positions for centering the text
    padding = 1
    x_position = calculate_x_position(matrix, longest_line_width, padding)
    y_position = calculate_y_position(matrix, total_lines_height)

    # Render each line of text
    render_lines(matrix, combined_lines, rideFont, waittimeFont, x_position, y_position, line_heights,
                 wrapped_ride_name)

    logging.debug(f"Total text height: {total_lines_height}, Final Y position: {y_position}")


def format_iso_time(iso_str):
    """
    Convert an ISO 8601 formatted time (e.g. '2025-03-17T09:00:00-04:00')
    into a simple string like '9am'.
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%I%p").lstrip("0").upper()
    except Exception:
        return iso_str  # Fallback if parsing fails.

def draw_centered_text_block(matrix, font, text_lines, region_width, region_height, color):
    """Draws multiple lines of text centered vertically in a region."""
    font_height = getattr(font, "height", 9)
    block_height = len(text_lines) * font_height
    # Start baseline so the entire block is vertically centered.
    current_y = (region_height - block_height) // 2 + font_height
    for line in text_lines:
        line_width = get_text_width(font, line)
        x = (region_width - line_width) // 2
        graphics.DrawText(matrix, font, x, current_y, color, line)
        current_y += font_height

def draw_single_line_centered(matrix, font, text, region_width, region_height, color):
    """Draws a single line of text centered vertically in a region."""
    font_height = getattr(font, "height", 9)
    line_width = get_text_width(font, text)
    baseline = (region_height - font_height) // 2 + font_height
    x = (region_width - line_width) // 2
    graphics.DrawText(matrix, font, x, baseline, color, text)

def render_park_information_screen(matrix, park_obj):
    """
    Renders the park name at the top and the hours/price at the bottom.
    Uses board-specific fonts based on board size.
    """
    board_width = matrix.width
    board_height = matrix.height

    # Define font paths for different board sizes.
    font_paths = {
        32: {
            "name": "assets/fonts/patched/6x9.bdf",
            "info": "assets/fonts/patched/4x6-legacy.bdf"
        },
        64: {
            "name": "assets/fonts/patched/6x13.bdf",
            "info": "assets/fonts/patched/4x6-legacy.bdf"
        }
    }

    # Choose fonts based on board size; default to 32x settings if not recognized.
    if board_height in font_paths:
        name_font_path = font_paths[board_height]["name"]
        info_font_path = font_paths[board_height]["info"]
    else:
        logging.warning("Unsupported board height; defaulting to 32x settings.")
        name_font_path = font_paths[32]["name"]
        info_font_path = font_paths[32]["info"]

    # Load fonts.
    name_font = graphics.Font()
    name_font.LoadFont(name_font_path)
    info_font = graphics.Font()
    info_font.LoadFont(info_font_path)

    name_color = graphics.Color(242, 5, 5)  # Mickey Mouse Red
    info_color = graphics.Color(17, 60, 207)  # Disney Blue

    # Determine bottom area height using info_font's height.
    info_font_height = getattr(info_font, "height")
    bottom_area_height = info_font_height

    available_top_height = board_height - bottom_area_height

    # Wrap park name
    wrapped_name = wrap_text(name_font, park_obj.get("name"), board_width, available_top_height, 1)

    # Draw the park name based on board size.
    if board_height == 32:
        if len(wrapped_name) == 1:
            draw_single_line_centered(matrix, name_font, wrapped_name[0], board_width, available_top_height, name_color)
        else:
            draw_centered_text_block(matrix, name_font, wrapped_name, board_width, available_top_height, name_color)
    elif board_height == 64:
        # Always center the entire block for 64-pixel boards.
        draw_centered_text_block(matrix, name_font, wrapped_name, board_width, available_top_height, name_color)
    else:
        # Fallback for any unexpected board size.
        if len(wrapped_name) == 1:
            draw_single_line_centered(matrix, name_font, wrapped_name[0], board_width, available_top_height, name_color)
        else:
            draw_centered_text_block(matrix, name_font, wrapped_name, board_width, available_top_height, name_color)

    baseline_y = board_height - 1
    rendar_park_hours(baseline_y, info_color, info_font, matrix, park_obj)
    render_lightning_lane_multi_pass_price(baseline_y, board_width, info_color, info_font, matrix, park_obj.get("llmpPrice", ""))
    logging.debug(f"{park_obj.get("name")} Park Dude Data: {logJSONPrettyPrint(park_obj)}")
    display_icon_in_upper_left(matrix, park_obj.get("weather", ""))


def render_lightning_lane_multi_pass_price(baseline_y, board_width, info_color, info_font, matrix, llmp_price):
    if llmp_price and not llmp_price.startswith("$"):
        llmp_price = "$" + llmp_price
    price_width = get_text_width(info_font, llmp_price)
    right_padding = 1
    price_x = board_width - price_width - right_padding
    graphics.DrawText(matrix, info_font, price_x, baseline_y, info_color, llmp_price)


def rendar_park_hours(baseline_y, info_color, info_font, matrix, park_obj):
    # Render operating hours & price at the bottom.
    opening_time = park_obj.get("openingTime", "")
    closing_time = park_obj.get("closingTime", "")
    if opening_time and closing_time:
        hours_text = f"{format_iso_time(opening_time)}-{format_iso_time(closing_time)}"
    else:
        hours_text = "??-??"
    left_padding = 1
    graphics.DrawText(matrix, info_font, left_padding, baseline_y, info_color, hours_text)


def render_weather_icon(matrix, icon_code):
    icon_filename = f"{icon_code}@2x.png"  # Adjust this based on your naming convention
    icon_path = os.path.join("assets", "weather", icon_filename)  # Path to the icon in the assets folder

    try:
        # Open the icon image from the local path
        img = Image.open(icon_path)
        img = img.resize((16, 16))  # Resize the image to a smaller size

        matrix.Clear()  # Clear the matrix before drawing
        matrix.SetImage(img.convert("RGB"))  # Draw the image on the matrix
    except FileNotFoundError:
        logging.error(f"Icon not found: {icon_path}")  # Log if the file does not exist
    except Exception as e:
        logging.error(f"Failed to load icon: {e}")


def icon_filename(self):
    return os.path.abspath("./assets/weather/{}.png".format(self))


def display_icon_in_upper_left(matrix, weather_info):
    """Display only the weather icon in the upper left corner."""
    # logging.info("123456", {weather_info and "icon" in weather_info})
    logging.info(f"Weather Info: {weather_info}")
    if weather_info and "icon" in weather_info:
        logging.info(f"1234567890")
        render_weather_icon(matrix, weather_info['icon'])
