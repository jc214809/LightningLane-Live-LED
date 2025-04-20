import time
from datetime import datetime
from driver import graphics
from display.display import get_text_width

def wrap_text_in_lines(font, text, max_chars_per_line):
    """Wrap a line of text into multiple lines that fit within the specified max_chars_per_line."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if current_line:
            test_line = f"{current_line} {word}"
        else:
            test_line = word

        if get_text_width(font, test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def draw_centered_text(matrix, font, text, color, y_position):
    """Draws wrapped text centered at a specific y position."""
    max_width = matrix.width
    wrapped_lines = wrap_text_in_lines(font, text, max_width)

    total_height = len(wrapped_lines) * font.height
    center_y = y_position - total_height // 2  # Center the text vertically around the provided y position

    for idx, line in enumerate(wrapped_lines):
        line_width = get_text_width(font, line)
        center_x = (matrix.width - line_width) // 2  # Center horizontally
        graphics.DrawText(matrix, font, center_x, center_y + (idx * font.height), color, line)


def render_countdown_to_disney(matrix, trip_date):
    """Displays countdown to Disney on the LED matrix."""
    font = graphics.Font()
    font.LoadFont("assets/fonts/patched/6x9.bdf")
    text_color = graphics.Color(255, 255, 255)  # White text

    time_remaining = trip_date - datetime.now()

    if time_remaining.days < 0:
        days_remaining = "Trip has already started!"
    else:
        days_remaining = f"{time_remaining.days} Days"

    title = "COUNTDOWN TO DISNEY"
    countdown_string = f"{title} {days_remaining}"

    draw_centered_text(matrix, font, countdown_string, text_color, matrix.height // 2 + 7)
