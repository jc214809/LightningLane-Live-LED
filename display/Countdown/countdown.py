import time
from datetime import datetime
from driver import graphics
from display.display import get_text_width

def wrap_text(font, text, max_width):
    """Wrap text to fit within the specified max_width."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if current_line:
            test_line = current_line + " " + word
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


def draw_text(matrix, font, text, color, y):
    """Draws wrapped text centered at a specific y position."""
    max_width = matrix.width
    wrapped_lines = wrap_text(font, text, max_width)

    total_height = len(wrapped_lines) * font.height
    start_y = y - total_height // 2  # Center the text vertically around the provided y position

    for line in wrapped_lines:
        width = get_text_width(font, line)
        x = (matrix.width - width) // 2  # Center horizontally
        graphics.DrawText(matrix, font, x, start_y, color, line)
        start_y += font.height  # Move down for the next line


def render_countdown_to_disney(matrix, trip_date):
    """Displays countdown to Disney on the LED matrix."""
    font = graphics.Font()
    font.LoadFont("assets/fonts/patched/6x9.bdf")
    text_color = graphics.Color(255, 255, 255)  # White text

    now = datetime.now()
    time_remaining = trip_date - now

    # Calculate the countdown string
    if time_remaining.days < 0:
        countdown_string = "Trip has already started!"
    else:
        countdown_string = f"{time_remaining.days} Days"

    # Combine title and countdown
    combined_string = f"COUNTDOWN TO DISNEY {countdown_string}"

    # Draw the title and countdown together
    draw_text(matrix, font, combined_string, text_color, ((matrix.height // 2) + 5))  # Position below title

