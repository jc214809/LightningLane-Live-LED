import logging
from array import ArrayType
from datetime import datetime
from driver import graphics

def get_text_width(font, text):
    """Helper to calculate total width of text in pixels."""
    return sum(font.CharacterWidth(ord(ch)) for ch in text)

def wrap_text(font, text, max_width, max_height):
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
        if test_line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def render_ride_info(matrix, ride_info):
    """
    Renders ride name at the top and wait time at the bottom in a single draw call.
    The combined text block is drawn from the center of the screen.
    """
    logging.debug(f"Rendering ride info: {ride_info}")
    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} Mins"

    # Load fonts based on board height.
    if matrix.height == 64:
        rideFont = graphics.Font()
        rideFont.LoadFont("assets/fonts/patched/6x9.bdf")
        waittimeFont = graphics.Font()
        waittimeFont.LoadFont("assets/fonts/patched/5x8.bdf")
        logging.info("Matrix height: 64.")
    elif matrix.height == 32:
        rideFont = graphics.Font()
        rideFont.LoadFont("assets/fonts/patched/4x6-legacy.bdf")
        waittimeFont = graphics.Font()
        waittimeFont.LoadFont("assets/fonts/patched/4x6-legacy.bdf")
        logging.info("Matrix height: 32.")
    else:
        logging.error("Unsupported matrix height. Please use 32 or 64.")
        return

    # Wrap the text for both ride name and wait time.
    name_line_height = getattr(rideFont, "height", 9)
    waittime_line_height = getattr(waittimeFont, "height", 6)

    wrapped_ride_name = wrap_text(rideFont, ride_name, matrix.width, matrix.height)
    wrapped_wait_time = wrap_text(waittimeFont, wait_time, matrix.width, matrix.height)

    # Combine wrapped ride name and wait time into one list of lines
    combined_lines = wrapped_ride_name + wrapped_wait_time

    # Remove blank lines from combined_lines
    combined_lines = [line for line in combined_lines if line.strip() != ""]

    # Log the combined lines to ensure the correct lines are present
    logging.info(f"Combined and filtered lines: {combined_lines}")

    color_white = graphics.Color(255, 255, 255)

    # Calculate the total height of all lines
    total_lines_height = len(combined_lines) * max(name_line_height, waittime_line_height)

    # Vertical centering
    y_position = (matrix.height - total_lines_height) // 2
    logging.info(f"y_position calculated: {y_position}")

    # Start drawing from the center, center each line horizontally
    for line in combined_lines:
        # Get the width of the line based on the font
        line_width = get_text_width(rideFont, line) if line in wrapped_ride_name else get_text_width(waittimeFont, line)

        # Calculate x_position to center each line horizontally
        x_position = (matrix.width - line_width) // 2

        # Log the line details
        logging.info(f"Drawing line: '{line}' at position ({x_position}, {y_position})")

        # Directly use graphics.DrawText instead of dynamic spacing
        if line in wrapped_ride_name:
            graphics.DrawText(matrix, rideFont, x_position, y_position, color_white, line)
        else:
            graphics.DrawText(matrix, waittimeFont, x_position, y_position, color_white, line)

        # Move the y_position down for the next line
        y_position += name_line_height if line in wrapped_ride_name else waittime_line_height

    logging.debug(f"Total text height: {total_lines_height}, Final Y position: {y_position}")

def format_iso_time(iso_str):
    """
    Convert an ISO 8601 formatted time (e.g. '2025-03-17T09:00:00-04:00')
    into a simple string like '9am'.
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%I%p").lstrip("0").lower()
    except Exception:
        return iso_str  # Fallback if parsing fails.

def render_park_information_screen(matrix, park_obj):
    """
    Renders the park name at the top and the hours/price at the bottom.
    For a 64x32 board, if the park name is a single line, it is centered;
    if multi-line, the lines are drawn from the top. For a 64x64 board,
    the park name block is vertically centered.
    Hours are rendered at the bottom-left and price at the bottom-right.
    """
    # Load fonts.
    name_font = graphics.Font()
    name_font.LoadFont("assets/fonts/patched/6x9.bdf")
    info_font = graphics.Font()
    info_font.LoadFont("assets/fonts/patched/4x6-legacy.bdf")

    name_color = graphics.Color(242, 5, 5)     # Mickey Mouse Red
    info_color = graphics.Color(17, 60, 207)   # Disney Blue

    board_width = matrix.width
    board_height = matrix.height

    # Set padding and bottom area height based on board size.
    if board_height == 32:
        top_padding = 0
        bottom_padding = 0
        info_font_height = getattr(info_font, "height", 6)
        bottom_area_height = info_font_height  # no extra padding
    elif board_height == 64:
        top_padding = 0
        bottom_padding = 0
        info_font_height = getattr(info_font, "height", 6)
        bottom_area_height = info_font_height  # no extra padding
    else:
        logging.warning("Unsupported board height; defaulting to 64x32 settings.")
        top_padding = 0
        bottom_padding = 0
        info_font_height = getattr(info_font, "height", 6)
        bottom_area_height = info_font_height

    available_top_height = board_height - bottom_area_height
    name_font_height = getattr(name_font, "height", 9)

    # Wrap park name.
    park_name_text = park_obj.get("name", "Unknown")
    wrapped_name = wrap_text(name_font, park_name_text, max_width=board_width, max_height=available_top_height)

    # For 32-pixel boards, either center one line or center the entire block if multiple lines
    if board_height == 32:
        if len(wrapped_name) == 1:
            single_line_text = wrapped_name[0]
            single_line_width = get_text_width(name_font, single_line_text)
            top_region_height = available_top_height
            single_line_baseline = (top_region_height - name_font_height) // 2 + name_font_height
            x = (board_width - single_line_width) // 2
            graphics.DrawText(matrix, name_font, x, single_line_baseline, name_color, single_line_text)
        else:
            # Center the entire block
            total_lines = len(wrapped_name)
            block_height = total_lines * name_font_height
            top_of_block = (available_top_height - block_height) // 2
            current_y = top_of_block + name_font_height
            for line in wrapped_name:
                line_width = get_text_width(name_font, line)
                x = (board_width - line_width) // 2
                graphics.DrawText(matrix, name_font, x, current_y, name_color, line)
                current_y += name_font_height

    elif board_height == 64:
        # For 64-pixel boards, always center the entire block
        total_lines = len(wrapped_name)
        block_height = total_lines * name_font_height
        top_of_block = (available_top_height - block_height) // 2
        current_y = top_of_block + name_font_height
        for line in wrapped_name:
            line_width = get_text_width(name_font, line)
            x = (board_width - line_width) // 2
            graphics.DrawText(matrix, name_font, x, current_y, name_color, line)
            current_y += name_font_height
    else:
        # Fallback for any unexpected board size
        if len(wrapped_name) == 1:
            single_line_text = wrapped_name[0]
            single_line_width = get_text_width(name_font, single_line_text)
            top_region_height = available_top_height
            single_line_baseline = (top_region_height - name_font_height) // 2 + name_font_height
            x = (board_width - single_line_width) // 2
            graphics.DrawText(matrix, name_font, x, single_line_baseline, name_color, single_line_text)
        else:
            current_y = name_font_height
            for line in wrapped_name:
                line_width = get_text_width(name_font, line)
                x = (board_width - line_width) // 2
                graphics.DrawText(matrix, name_font, x, current_y, name_color, line)
                current_y += name_font_height

    # Render operating hours & price at the bottom.
    baseline_y = board_height - 1
    opening_time = park_obj.get("openingTime", "")
    closing_time = park_obj.get("closingTime", "")
    hours_text = f"{format_iso_time(opening_time)}-{format_iso_time(closing_time)}" \
                 if opening_time and closing_time else "??-??"
    left_padding = 0
    graphics.DrawText(matrix, info_font, left_padding, baseline_y, info_color, hours_text)

    llmp_price = park_obj.get("llmpPrice", "")
    if llmp_price and not llmp_price.startswith("$"):
        llmp_price = "$" + llmp_price
    price_width = get_text_width(info_font, llmp_price)
    right_padding = 0
    price_x = board_width - price_width - right_padding
    graphics.DrawText(matrix, info_font, price_x, baseline_y, info_color, llmp_price)

    logging.debug(f"Wrapped park name: {wrapped_name}")
    logging.debug(f"Baseline Y: {baseline_y}, Hours: '{hours_text}', Price: '{llmp_price}'")
