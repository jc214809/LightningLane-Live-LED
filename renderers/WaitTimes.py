from driver import graphics
from data.config.color import Color
from data.config.layout import Layout
from renderers import scrollingtext
from utils import center_text_position

def render_ride_info(canvas, layout: Layout, colors: Color, ride_name: str, wait_time: str):
    """
    Renders the ride name and wait time on the display.
    """
    text_len = _render_ride_text(canvas, layout, colors, ride_name, wait_time)
    _render_wait_time(canvas, layout, colors, wait_time)
    return text_len

def _render_ride_text(canvas, layout, colors, ride_name, wait_time):
    """
    Renders the scrolling text for the ride information.
    """
    coords = layout.coords("ride.scrolling_text")
    font = layout.font("ride.scrolling_text")
    color = colors.graphics_color("ride.scrolling_text")
    bgcolor = colors.graphics_color("default.background")

    ride_info_text = f"{ride_name} - Wait Time: {wait_time} mins"

    return scrollingtext.render_text(
        canvas, coords["x"], coords["y"], coords["width"], font, color, bgcolor, ride_info_text
    )

def _render_wait_time(canvas, layout, colors, wait_time):
    """
    Renders the static wait time separately if needed.
    """
    time_text = f"{wait_time} mins"
    coords = layout.coords("ride.wait_time")
    font = layout.font("ride.wait_time")
    color = colors.graphics_color("ride.wait_time")

    time_x = center_text_position(time_text, coords["x"], font["size"]["width"])
    graphics.DrawText(canvas, font["font"], time_x, coords["y"], color, time_text)
