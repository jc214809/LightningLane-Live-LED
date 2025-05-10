import os
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from RGBMatrixEmulator import graphics

from display.display import get_text_width, wrap_text, color_dict, fonts
from utils import debug

# Icon cache for storing loaded weather icons
icon_cache = {}
def render_park_information_screen(matrix, park_obj):
    """
    Renders the park name at the top and the hours/price at the bottom.
    Uses board-specific fonts based on board size.
    """
    board_width = matrix.width
    board_height = matrix.height

    info_font = graphics.Font()
    absolute_path = os.path.abspath(fonts()[board_height]["info"])
    info_font.LoadFont(absolute_path)
    park_font = graphics.Font()
    absolute_path = os.path.abspath(fonts()[board_height]["park"])
    park_font.LoadFont(absolute_path)

    # Determine bottom area height using info_font's height.
    info_font_height = getattr(info_font, "height")
    bottom_area_height = info_font_height

    available_top_height = board_height - bottom_area_height
    baseline_y = board_height - 1
    # Wrap park name
    wrapped_name = wrap_text(park_font, park_obj.get("name"), board_width, 1)

    # Draw the park name based on board size.
    draw_multi_line_park_name_text_block(matrix, park_font, wrapped_name)
    if park_obj.get("weather"):
        display_weather_icon_and_description(matrix, park_obj.get("weather", ""), info_font_height, info_font)
    llmp_price = park_obj.get("llmpPrice", "")
    if board_height == 32:
        render_park_hours(baseline_y, 1, matrix, park_obj, info_font)
        render_lightning_lane_multi_pass_price(baseline_y - info_font_height, 1, matrix, llmp_price, info_font)
    else:
        render_lightning_lane_multi_pass_price(baseline_y, matrix.width - get_text_width(info_font, llmp_price), matrix, llmp_price, info_font)
        render_park_hours(baseline_y, 1, matrix, park_obj, info_font)

def render_special_ticketed_events(vertical_start, matrix, hours_text, info_font):
    graphics.DrawText(matrix, info_font, 1 + get_text_width(info_font, hours_text), vertical_start, color_dict["gold"], "*")

def render_lightning_lane_multi_pass_price(vertical_start, horizontal_start, matrix, llmp_price, info_font):
    if llmp_price and not llmp_price.startswith("$"):
        llmp_price = "$" + llmp_price
    graphics.DrawText(matrix, info_font, horizontal_start, vertical_start, color_dict["disney_blue"], llmp_price)


def render_park_hours(vertical_start, horizontal_start, matrix, park_obj, info_font):
    # Render operating hours & price at the bottom.
    opening_time = park_obj.get("openingTime", "")
    closing_time = park_obj.get("closingTime", "")
    if opening_time and closing_time:
        hours_text = f"{format_iso_time(opening_time)}-{format_iso_time(closing_time)}"
        if park_obj.get("specialTicketedEvent", False):
            render_special_ticketed_events(vertical_start, matrix, hours_text, info_font)
    else:
        hours_text = "??-??"
    graphics.DrawText(matrix, info_font, horizontal_start, vertical_start, color_dict["disney_blue"], hours_text)

def render_weather_icon(icon_code):
    # Construct the URL for the weather icon
    # Check if the icon is already cached
    debug.log(f"Fetching cache: {icon_cache}")
    if icon_code in icon_cache:
        debug.info(f"Fetching icon from cache for code: {icon_code}")
        return icon_cache[icon_code]

    icon_url = f"https://openweathermap.org/img/wn/{icon_code}.png"

    try:
        # Fetch the icon image from the URL
        response = requests.get(icon_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        img = Image.open(BytesIO(response.content))
        img = img.resize((15, 15))  # Resize the image to a smaller display size for the matrix
        icon_cache[icon_code] = img

        return img
    except requests.RequestException as e:
        debug.error(f"Failed to fetch icon from URL: {icon_url} - {e}")  # Log any issues
        return None
    except Exception as e:
        debug.error(f"Failed to load icon: {e}")  # Log other errors
        return None

def display_weather_icon_and_description(matrix, weather_info, font_height, info_font, show_icon=True):
    """Display the weather icon and its description in the top right corner."""
    debug.info(f"Weather Info: {weather_info}")

    temp = weather_info.get("temperature", "?")

    padding = 7
    if show_icon and "icon" in weather_info:
        img = render_weather_icon(weather_info['icon'])

        if img:
            icon_width = img.width
            if matrix.height == 32:
                matrix.SetImage(img.convert("RGB"), matrix.width - icon_width - 1, 1)
                graphics.DrawText(matrix, info_font, matrix.width - get_text_width(info_font, temp), img.height + padding, color_dict["white"], temp)
                weather_text = "T-Storm" if "thunderstorm" in weather_info['short_description'].lower() else weather_info['short_description']
                graphics.DrawText(matrix, info_font, matrix.width - get_text_width(info_font, weather_text), (img.height + font_height + padding), color_dict["white"],weather_text)
            if matrix.height >= 64:
                weather_text_width = temp + ' ' + weather_info['short_description']
                horizontal_point = int((matrix.width - img.width - get_text_width(info_font, weather_text_width)) / 2)
                vertical_point = int(matrix.height - (info_font.height * 2.5))
                matrix.SetImage(img.convert("RGB"), horizontal_point, vertical_point - img.height)
                graphics.DrawText(matrix, info_font, horizontal_point + img.width, vertical_point - 3, color_dict["white"], weather_text_width)
        else:
            debug.warning("Icon could not be rendered, only displaying text.")

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


def draw_multi_line_park_name_text_block(matrix, font, text_lines):
    """Draws multiple lines of text centered vertically in a region."""
    font_height = getattr(font, "height", 9)
    x = 1
    # Start baseline so the entire block is vertically centered.
    debug.log(f"font_height: {font_height}")
    current_y =  font_height
    for line in text_lines:
        if len(text_lines) is 1:
            if matrix.height == 32:
                current_y = int(current_y * 1.5)
            else:
                current_y = int(current_y * 2)
        if matrix.height == 64:
            line_width = get_text_width(font, line)
            x = (matrix.width - line_width) // 2
        graphics.DrawText(matrix, font, x, current_y, color_dict["mickey_mouse_red"], line)
        current_y += font_height


def draw_single_line_park_name_text(matrix, font, text, region_width, region_height):
    """Draws a single line of text centered vertically in a region."""
    font_height = getattr(font, "height", 9)
    line_width = get_text_width(font, text)
    baseline = (region_height - font_height) // 2 + font_height
    x = (region_width - line_width) // 2
    graphics.DrawText(matrix, font, x, baseline, color_dict["mickey_mouse_red"], text)
