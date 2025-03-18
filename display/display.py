
import logging
from datetime import datetime

from driver import graphics


def wrap_text(font, text, max_width, max_height, side_padding=1, top_padding=1):
    """
    Wrap text to fit within the specified max_width and max_height, leaving horizontal padding on the sides
    and a top padding. This function packs as many words into a line as possible. If a single word exceeds the
    available width, it is placed on its own line.

    :param font: The font object, which must have a CharacterWidth method and a 'height' attribute.
    :param text: The text to wrap.
    :param max_width: The total width (in pixels) of the board.
    :param max_height: The total height (in pixels) of the board.
    :param side_padding: The horizontal padding (in pixels) to leave on each side.
    :param top_padding: The vertical padding (in pixels) to leave at the top.
    :return: A list of strings, each representing a line of text.
    """
    available_width = max_width -  side_padding
    available_height = max_height - top_padding  # Only subtracting top padding.
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Calculate the width of the word.
        word_width = sum(font.CharacterWidth(ord(ch)) for ch in word)
        # If the word is wider than the available width, place it on its own line.
        if word_width > available_width:
            if current_line:
                lines.append(current_line)
                current_line = ""
            lines.append(word)
            continue

        # Try adding the word to the current line.
        test_line = f"{current_line} {word}".strip() if current_line else word
        test_line_width = sum(font.CharacterWidth(ord(ch)) for ch in test_line)
        if test_line_width <= available_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Calculate how many lines can fit vertically in the available height.
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

def format_iso_time(iso_str):
    """
    Convert an ISO 8601 formatted time (e.g. '2025-03-17T09:00:00-04:00')
    into a simple string like '9am'. Adjust the formatting as needed.
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        # Format as 12-hour time (e.g. "9am") using %I for hour, then remove any leading zero.
        return dt.strftime("%I%p").lstrip("0").lower()
    except Exception:
        return iso_str  # Fallback if parsing fails.


def render_park_Information_screen(matrix, park_obj):
    """
    Renders the park name at the top and the hours/price at the bottom.
    - For a 64x32 board, uses the existing approach (single-line is centered, multi-line from top).
    - For a 64x64 board, centers the entire name block (single or multi-line) in the top region.

    Bottom text (hours & price) always goes at the bottom-left and bottom-right.

    park_obj is expected to have:
      'name', 'openingTime', 'closingTime', 'llmpPrice'
    """

    # -------------------------------------------------------------------
    # 1) LOAD FONTS & COLORS
    # -------------------------------------------------------------------
    name_font = graphics.Font()
    name_font.LoadFont("assets/fonts/patched/6x9.bdf")
    info_font = graphics.Font()
    info_font.LoadFont("assets/fonts/patched/4x6-legacy.bdf")

    name_color = graphics.Color(255, 255, 255)
    info_color = graphics.Color(255, 255, 255)

    # -------------------------------------------------------------------
    # 2) DETERMINE PADDING & AVAILABLE SPACE BASED ON BOARD SIZE
    # -------------------------------------------------------------------
    board_width = matrix.width
    board_height = matrix.height

    if board_height == 32:
        # Settings for 64x32
        top_padding = 2
        bottom_padding = 2
        info_font_height = getattr(info_font, "height", 6)
        bottom_area_height = info_font_height + bottom_padding + 2
    elif board_height == 64:
        # Settings for 64x64
        top_padding = 4
        bottom_padding = 4
        info_font_height = getattr(info_font, "height", 6)
        bottom_area_height = info_font_height + bottom_padding + 2
    else:
        logging.warning("Unsupported board height; defaulting to 64x32 settings.")
        top_padding = 2
        bottom_padding = 2
        info_font_height = getattr(info_font, "height", 6)
        bottom_area_height = info_font_height + bottom_padding + 2

    available_top_height = board_height - bottom_area_height - top_padding
    name_font_height = getattr(name_font, "height", 9)

    # -------------------------------------------------------------------
    # 3) WRAP THE PARK NAME TO FIT THE TOP REGION
    # -------------------------------------------------------------------
    park_name_text = park_obj.get("name", "Unknown")
    wrapped_name = wrap_text(
        name_font,
        park_name_text,
        max_width=board_width,
        max_height=available_top_height
    )

    # -------------------------------------------------------------------
    # 4) RENDER THE PARK NAME (DIFFERENT LOGIC FOR 64x32 vs. 64x64)
    # -------------------------------------------------------------------
    if board_height == 32:
        # 64x32 approach: single-line => center vertically, multi-line => from top
        if len(wrapped_name) == 1:
            # single-line
            single_line_text = wrapped_name[0]
            single_line_width = sum(name_font.CharacterWidth(ord(ch)) for ch in single_line_text)
            top_region_height = available_top_height
            single_line_baseline = top_padding + (top_region_height - name_font_height) // 2 + name_font_height
            x = (board_width - single_line_width) // 2
            graphics.DrawText(matrix, name_font, x, single_line_baseline, name_color, single_line_text)
        else:
            # multi-line
            current_y = top_padding + name_font_height
            for line in wrapped_name:
                line_width = sum(name_font.CharacterWidth(ord(ch)) for ch in line)
                x = (board_width - line_width) // 2
                graphics.DrawText(matrix, name_font, x, current_y, name_color, line)
                current_y += name_font_height

    elif board_height == 64:
        # 64x64 approach: always center the entire block (single or multi-line)
        total_lines = len(wrapped_name)
        block_height = total_lines * name_font_height
        # top_of_block is the top of that text block
        top_of_block = top_padding + (available_top_height - block_height) // 2
        # We'll treat each line's baseline as top_of_block + line_index * name_font_height + name_font_height
        # If your library uses baseline coords, the first line's baseline is top_of_block + name_font_height
        current_y = top_of_block + name_font_height
        for line in wrapped_name:
            line_width = sum(name_font.CharacterWidth(ord(ch)) for ch in line)
            x = (board_width - line_width) // 2
            graphics.DrawText(matrix, name_font, x, current_y, name_color, line)
            current_y += name_font_height

    else:
        # Fallback logic if it's some other size
        if len(wrapped_name) == 1:
            single_line_text = wrapped_name[0]
            single_line_width = sum(name_font.CharacterWidth(ord(ch)) for ch in single_line_text)
            top_region_height = available_top_height
            single_line_baseline = top_padding + (top_region_height - name_font_height) // 2 + name_font_height
            x = (board_width - single_line_width) // 2
            graphics.DrawText(matrix, name_font, x, single_line_baseline, name_color, single_line_text)
        else:
            current_y = top_padding + name_font_height
            for line in wrapped_name:
                line_width = sum(name_font.CharacterWidth(ord(ch)) for ch in line)
                x = (board_width - line_width) // 2
                graphics.DrawText(matrix, name_font, x, current_y, name_color, line)
                current_y += name_font_height

    # -------------------------------------------------------------------
    # 5) RENDER OPERATING HOURS & PRICE AT THE BOTTOM
    # -------------------------------------------------------------------
    baseline_y = board_height - 1
    # Format hours
    opening_time = park_obj.get("openingTime", "")
    closing_time = park_obj.get("closingTime", "")
    if opening_time and closing_time:
        hours_text = f"{format_iso_time(opening_time)}-{format_iso_time(closing_time)}"
    else:
        hours_text = "??-??"

    left_padding = 2
    graphics.DrawText(matrix, info_font, left_padding, baseline_y, info_color, hours_text)

    llmp_price = park_obj.get("llmpPrice", "")
    if llmp_price and not llmp_price.startswith("$"):
        llmp_price = "$" + llmp_price
    price_width = sum(info_font.CharacterWidth(ord(ch)) for ch in llmp_price)
    right_padding = 1
    price_x = board_width - price_width - right_padding
    graphics.DrawText(matrix, info_font, price_x, baseline_y, info_color, llmp_price)

    # -------------------------------------------------------------------
    # 6) DEBUG LOGGING (optional)
    # -------------------------------------------------------------------
    logging.debug(f"Wrapped park name: {wrapped_name}")
    logging.debug(f"Baseline Y: {baseline_y}, Hours: '{hours_text}', Price: '{llmp_price}'")