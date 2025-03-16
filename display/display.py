import logging
from driver import graphics


def wrap_text(font, text, max_width, max_height):
    """
    Wrap text to fit within the specified max_width and max_height, packing as many words
    into a line as possible. If a single word exceeds max_width, it is placed on its own line.
    After wrapping, if the total number of lines exceeds what can fit in max_height, the
    output is truncated with an ellipsis on the last line.

    :param font: The font object, which must have a CharacterWidth method and a 'height' attribute.
    :param text: The text to wrap.
    :param max_width: The maximum width (in pixels) that a line can occupy.
    :param max_height: The maximum height (in pixels) available for the text block.
    :return: A list of strings, each representing a line of text.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Calculate the width of the current word.
        word_width = sum(font.CharacterWidth(ord(ch)) for ch in word)
        # If the word is wider than max_width, place it on its own line.
        if word_width > max_width:
            if current_line:
                lines.append(current_line)
                current_line = ""
            lines.append(word)
            continue

        # Try adding the word to the current line.
        test_line = f"{current_line} {word}".strip() if current_line else word
        test_line_width = sum(font.CharacterWidth(ord(ch)) for ch in test_line)
        if test_line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Determine how many lines can fit given max_height.
    line_height = getattr(font, "height", 9)
    max_lines = max_height // line_height
    if len(lines) > max_lines:
        # Truncate extra lines and add an ellipsis to the last visible line.
        lines = lines[:max_lines]
        # Append ellipsis if not already present.
        if not lines[-1].endswith("..."):
            lines[-1] = lines[-1] + "..."
    return lines

def draw_text_with_dynamic_spacing(matrix, font, y, color, text, max_width):
    """
    Draw a single line of text centered horizontally.
    If the total width exceeds max_width, reduce spacing dynamically.
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
    """Render Disney ride name and wait time with vertical centering and dynamic spacing."""
    logging.debug(f"Rendering ride info: {ride_info}")
    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} Mins"

    # Load fonts based on matrix height.
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

    wrapped_ride_name = wrap_text(rideFont, ride_name, matrix.width, matrix.height)
    wrapped_wait_time = wrap_text(waittimeFont, wait_time, matrix.width, matrix.height)
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
        draw_text_with_dynamic_spacing(matrix, rideFont, y_position_ride + i * name_line_height, color_white, line, matrix.width)
    y_position_wait = start_y + ride_name_height + gap
    for i, line in enumerate(wrapped_wait_time):
        draw_text_with_dynamic_spacing(matrix, waittimeFont, y_position_wait + i * waittime_line_height, color_white, line, matrix.width)

def render_park_name(matrix, park_name):
    """Render the park name centered on the board, wrapping onto multiple lines if needed."""
    font = graphics.Font()
    font.LoadFont("assets/fonts/patched/6x9.bdf")
    color_red = graphics.Color(255, 0, 0)

    max_width = matrix.width
    line_height = getattr(font, "height", 9)
    wrapped_lines = wrap_text(font, park_name, matrix.width, matrix.height)
    total_height = len(wrapped_lines) * line_height
    baseline_offset = 6  # Adjust if text appears too high or too low
    start_y = (matrix.height - total_height) // 2 + baseline_offset

    for i, line in enumerate(wrapped_lines):
        line_width = sum(font.CharacterWidth(ord(ch)) for ch in line)
        x = (max_width - line_width) // 2
        y = start_y + i * line_height
        graphics.DrawText(matrix, font, x, y, color_red, line)
