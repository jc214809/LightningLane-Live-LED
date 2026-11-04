import time
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image

from display.display import get_text_width, wrap_text, color_dict, loaded_fonts
from driver import graphics
from utils import debug
from utils.special_events import DEFAULT_STAR_RGB, star_rgb

ICON_TIMEOUT_S = 5
ICON_RETRY_S = 300

# Icon cache for storing loaded weather icons
icon_cache = {}
icon_failures = {}
def render_park_information_screen(matrix, park_obj):
    """
    Renders the park name at the top and the hours/price at the bottom.
    Uses board-specific fonts based on board size.
    """
    board_width = matrix.width
    board_height = matrix.height

    # Determine bottom area height using info_font's height.
    info_font_height = getattr(loaded_fonts["info"], "height")

    baseline_y = board_height - 1
    # Wrap park name
    wrapped_name = wrap_text(loaded_fonts["park"], park_obj.get("name"), board_width, 1)

    # Draw the park name based on board size.
    draw_multi_line_park_name_text_block(matrix, wrapped_name)
    if park_obj.get("weather"):
        display_weather_icon_and_description(matrix, park_obj.get("weather", ""), info_font_height)
    llmp_price = park_obj.get("llmpPrice", "")
    if board_height == 32:
        render_park_hours(baseline_y, 1, matrix, park_obj)
        render_lightning_lane_multi_pass_price(baseline_y - info_font_height, 1, matrix, llmp_price)
    else:
        render_lightning_lane_multi_pass_price(baseline_y, matrix.width - get_text_width(loaded_fonts["info"], llmp_price), matrix, llmp_price)
        render_park_hours(baseline_y, 1, matrix, park_obj)

# The dots of the "info" font's "*" (4x6-legacy on both boards), as (x, y) from the left edge and
# the baseline, in the order a multicoloured star lists its colours.
STAR_DOTS = [(0, -5), (2, -5), (1, -4), (0, -3), (2, -3)]


def render_special_ticketed_events(vertical_start, matrix, hours_text, rgb=DEFAULT_STAR_RGB):
    x = 1 + get_text_width(loaded_fonts["info"], hours_text)
    if isinstance(rgb[0], tuple):
        # A multicoloured star can't go through DrawText: set its dots one by one.
        for (dx, dy), dot in zip(STAR_DOTS, rgb):
            matrix.SetPixel(x + dx, vertical_start + dy, *dot)
        return
    graphics.DrawText(matrix, loaded_fonts["info"], x, vertical_start, graphics.Color(*rgb), "*")

def render_lightning_lane_multi_pass_price(vertical_start, horizontal_start, matrix, llmp_price):
    if llmp_price and not llmp_price.startswith("$"):
        llmp_price = "$" + llmp_price
    graphics.DrawText(matrix, loaded_fonts["info"], horizontal_start, vertical_start, color_dict["disney_blue"], llmp_price)


def render_park_hours(vertical_start, horizontal_start, matrix, park_obj):
    # Render operating hours & price at the bottom.
    opening_time = park_obj.get("openingTime", "")
    closing_time = park_obj.get("closingTime", "")
    if opening_time and closing_time:
        hours_text = f"{format_iso_time(opening_time)}-{format_iso_time(closing_time)}"
        star = star_rgb(park_obj)
        if star:
            render_special_ticketed_events(vertical_start, matrix, hours_text, star)
    else:
        hours_text = "??-??"
    graphics.DrawText(matrix, loaded_fonts["info"], horizontal_start, vertical_start, color_dict["disney_blue"], hours_text)

def render_weather_icon(icon_code):
    # Construct the URL for the weather icon
    # Check if the icon is already cached
    # Called every animation frame: no logging on this path (a cache hit is the normal case).
    if icon_code in icon_cache:
        return icon_cache[icon_code]
    # The park screen is redrawn every animation frame; don't re-download a failing icon each time.
    failed_at = icon_failures.get(icon_code)
    if failed_at is not None and time.monotonic() - failed_at < ICON_RETRY_S:
        return None

    icon_url = f"https://openweathermap.org/img/wn/{icon_code}.png"

    try:
        # Fetch the icon image from the URL
        response = requests.get(icon_url, timeout=ICON_TIMEOUT_S)
        response.raise_for_status()  # Raise an exception for HTTP errors
        img = Image.open(BytesIO(response.content))
        img = img.resize((15, 15))  # Resize the image to a smaller display size for the matrix
        icon_cache[icon_code] = img
        icon_failures.pop(icon_code, None)
        debug.log(f"Downloaded weather icon {icon_code}")  # once per new icon, not per frame

        return img
    except requests.RequestException as e:
        debug.error(f"Failed to fetch icon from URL: {icon_url} - {e}")  # Log any issues
    except Exception as e:
        debug.error(f"Failed to load icon: {e}")  # Log other errors
    icon_failures[icon_code] = time.monotonic()
    return None

def display_weather_icon_and_description(matrix, weather_info, font_height,show_icon=True):
    """Display the weather icon and its description in the top right corner."""

    temp = weather_info.get("temperature", "?")

    padding = 7
    if show_icon and "icon" in weather_info:
        img = render_weather_icon(weather_info['icon'])

        if img:
            icon_width = img.width
            if matrix.height == 32:
                matrix.SetImage(img.convert("RGB"), matrix.width - icon_width - 1, 1)
                graphics.DrawText(matrix, loaded_fonts["info"], matrix.width - get_text_width(loaded_fonts["info"], temp), img.height + padding, color_dict["white"], temp)
                graphics.DrawText(matrix, loaded_fonts["info"], matrix.width - get_text_width(loaded_fonts["info"], weather_info['short_description']), (img.height + font_height + padding), color_dict["white"],weather_info['short_description'])
            if matrix.height >= 64:
                weather_text = temp + ' ' + weather_info['short_description']
                horizontal_point = int((matrix.width - img.width - get_text_width(loaded_fonts["info"], weather_text)) / 2)
                vertical_point = int(matrix.height - (loaded_fonts["info"].height * 2.5))
                matrix.SetImage(img.convert("RGB"), horizontal_point, vertical_point - img.height)
                graphics.DrawText(matrix, loaded_fonts["info"], horizontal_point + img.width, vertical_point - 3, color_dict["white"], weather_text)
        # No icon: the fetch already logged why, once per retry window; this runs every frame.

def format_iso_time(iso_str):
    """
    Convert an ISO 8601 formatted time (e.g. '2025-03-17T09:00:00-04:00')
    into a simple string like '9am'.
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%I%p").lstrip("0").upper()
    except Exception as e:
        debug.error(f"Error formatting ISO time: {e}")
        return iso_str  # Fallback if parsing fails.


def draw_multi_line_park_name_text_block(matrix, text_lines):
    """Draws multiple lines of text centered vertically in a region."""
    font_height = getattr(loaded_fonts["park"], "height", 9)
    x = 1
    # Start baseline so the entire block is vertically centered.
    current_y =  font_height
    for line in text_lines:
        if len(text_lines) == 1:
            if matrix.height == 32:
                current_y = int(current_y * 1.5)
            else:
                current_y = int(current_y * 2)
        if matrix.height == 64:
            line_width = get_text_width(loaded_fonts["park"], line)
            x = (matrix.width - line_width) // 2
        graphics.DrawText(matrix, loaded_fonts["park"], x, current_y, color_dict["mickey_mouse_red"], line)
        current_y += font_height


def draw_single_line_park_name_text(matrix, font, text, region_width, region_height):
    """Draws a single line of text centered vertically in a region."""
    font_height = getattr(font, "height", 9)
    line_width = get_text_width(font, text)
    baseline = (region_height - font_height) // 2 + font_height
    x = (region_width - line_width) // 2
    graphics.DrawText(matrix, font, x, baseline, color_dict["mickey_mouse_red"], text)
