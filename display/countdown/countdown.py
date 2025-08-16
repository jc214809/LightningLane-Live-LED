from datetime import datetime

from display.display import get_text_width, loaded_fonts, color_dict
from driver import graphics


def wrap_text_in_lines(font, text, max_width):
    """Wrap a line of text into multiple lines that fit within the specified max_chars_per_line."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if current_line:
            test_line = f"{current_line} {word}"
        else:
            test_line = word

        if get_text_width(font, test_line) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def draw_countdown_text(matrix, y_position, text):
    """Draws wrapped text centered at a specific y position."""
    font = loaded_fonts["countdown"]
    wrapped_lines = wrap_text_in_lines(font, text, matrix.width)

    total_height = len(wrapped_lines) * font.height
    center_y = y_position - total_height // 2  # Center the text vertically around the provided y position

    for idx, line in enumerate(wrapped_lines):
        line_width = get_text_width(font, line)
        center_x = (matrix.width - line_width) // 2  # Center horizontally
        graphics.DrawText(matrix, font, center_x, center_y + (idx * font.height), color_dict["mickey_mouse_red"], line)


def render_countdown_to_disney(matrix, trip_date):
    """Displays countdown to Disney on the LED matrix."""
    time_remaining = trip_date.date() - datetime.now().date()
    countdown_string = "Have a Magical Trip!"

    if time_remaining.days > 0:
        days_remaining = f"{time_remaining.days} Day{'s' if time_remaining.days > 1 else ''}"
        countdown_string = f"COUNTDOWN TO DISNEY {days_remaining}"

    draw_countdown_text(matrix, matrix.height // 2 + 7, countdown_string)
