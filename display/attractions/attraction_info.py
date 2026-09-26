import math

from display.animation import ease_out
from display.display import DOWN_RGB, draw_text, plain_text, wrap_text, get_text_width, color_dict, loaded_fonts
from driver import graphics
from utils import debug

COUNT_UP_S = 0.8
PULSE_PERIOD_S = 1.6
# Minutes at which the wait bar is full, and the color bands along it.
BAR_FULL_MINUTES = 90
BAR_BANDS = [(20, (40, 200, 60)), (45, (255, 190, 0)), (float("inf"), (255, 90, 20))]
FORECAST_TICK_RGB = (255, 255, 255)
GAP_BETWEEN_RIDE_AND_WAIT = 2
# Narrow word spaces: the fonts' own space is a full cell, which pushes "Down 100 Mins" onto two lines.
SPACE_PX = 2


def _format_wait_time(raw_wait):
    if isinstance(raw_wait, str) and raw_wait.startswith("Group"):
        return raw_wait
    return f"{raw_wait} Mins"


def is_down(wait):
    return isinstance(wait, str) and wait.lower().startswith("down")


def counted_wait(wait, t):
    """Minutes to show t seconds into the count-up; non-numeric waits show as-is."""
    if not isinstance(wait, int) or isinstance(wait, bool):
        return wait
    return round(wait * ease_out(t / COUNT_UP_S))


def pulse_level(t):
    """0.5..1.0 brightness for a slow breathing pulse."""
    return 0.75 + 0.25 * math.cos(2 * math.pi * t / PULSE_PERIOD_S)


def wait_bar_color(minutes):
    for limit, rgb in BAR_BANDS:
        if minutes <= limit:
            return rgb
    return BAR_BANDS[-1][1]


def _bar_length(minutes, width):
    return round(min(minutes, BAR_FULL_MINUTES) / BAR_FULL_MINUTES * width)


def draw_wait_bar(canvas, minutes, expected=None):
    """
    A bar along the bottom edge whose length and color track the wait, with a white
    tick at the forecast wait for this hour (when there is one) standing 1px taller.
    """
    height = 2 if canvas.height >= 64 else 1
    length = _bar_length(minutes, canvas.width)
    color = graphics.Color(*wait_bar_color(minutes))
    for row in range(height):
        y = canvas.height - 1 - row
        if length > 0:
            graphics.DrawLine(canvas, 0, y, length - 1, y, color)
    if expected is not None:
        x = min(canvas.width - 1, max(0, _bar_length(expected, canvas.width) - 1))
        graphics.DrawLine(canvas, x, canvas.height - 1 - height, x, canvas.height - 1, graphics.Color(*FORECAST_TICK_RGB))


def draw_attraction_frame(canvas, ride_info, t, expected=None):
    """One frame of the animated attraction screen; returns True while it is still moving."""
    wait = ride_info["waitTime"]
    shown = counted_wait(wait, t)
    down = is_down(wait)
    down_color = None
    if down:
        level = pulse_level(t)
        down_color = graphics.Color(*(int(c * level) for c in DOWN_RGB))
    has_bar = isinstance(wait, int) and not isinstance(wait, bool)
    # Laid out against the final wait so the text doesn't jump while the number counts up.
    reserve, gap = bar_layout(canvas, ride_info) if has_bar else (0, GAP_BETWEEN_RIDE_AND_WAIT)
    overflow = overflow_rows(canvas, ride_info)
    scroll = scroll_offset(t, overflow) if overflow > 0 else None
    render_attraction_info(canvas, {**ride_info, "waitTime": shown}, down_color=down_color,
                           reserve_bottom=reserve, scroll_px=scroll, gap=gap)
    if reserve:
        draw_wait_bar(canvas, shown, expected)
    return down or overflow > 0 or (has_bar and t < COUNT_UP_S)


SCROLL_PX_PER_S = 8
SCROLL_PAUSE_S = 1.0


def overflow_rows(matrix, ride_info):
    """How many rows taller than the board the text block is (0 when it fits)."""
    *_, total_lines_height, _ = _layout(matrix, ride_info)
    return max(0, total_lines_height + GAP_BETWEEN_RIDE_AND_WAIT - matrix.height)


def scroll_offset(t, overflow):
    """Pause at the top, scroll down to the end, pause, scroll back up; repeat."""
    travel = overflow / SCROLL_PX_PER_S
    cycle = 2 * (SCROLL_PAUSE_S + travel)
    t = t % cycle
    if t < SCROLL_PAUSE_S:
        return 0
    t -= SCROLL_PAUSE_S
    if t < travel:
        return round(t * SCROLL_PX_PER_S)
    t -= travel
    if t < SCROLL_PAUSE_S:
        return overflow
    return round(overflow - (t - SCROLL_PAUSE_S) * SCROLL_PX_PER_S)


def bar_reserve_rows(board_height, tight=False):
    """
    Rows kept clear for the wait bar: the bar, the forecast tick above it, and a blank
    row. `tight` drops the blank row — used only for names that would otherwise lose
    the bar entirely.
    """
    return (2 if board_height >= 64 else 1) + (1 if tight else 2)


def _layout(matrix, ride_info):
    ride_name = plain_text(ride_info["name"])
    wait_time = _format_wait_time(ride_info["waitTime"])

    # Wrap the text for both ride name and wait time
    wrapped_wait_time = wrap_text(loaded_fonts["waittime"], wait_time, matrix.width, 1, SPACE_PX)
    wrapped_ride_name = wrap_text(loaded_fonts["ride"], ride_name, matrix.width, 1, SPACE_PX)
    name_h, wait_h = loaded_fonts["ride"].height, loaded_fonts["waittime"].height
    wait_block = len(wrapped_wait_time) * wait_h + GAP_BETWEEN_RIDE_AND_WAIT
    # Shorten when the whole block (gap included) is taller than the board; scrolling is the last resort.
    if len(wrapped_ride_name) * name_h + wait_block > matrix.height:
        if "Meet " in ride_name:
            ride_name = ride_name.rsplit(" at ", 1)[0]
            wrapped_ride_name = wrap_text(loaded_fonts["ride"], ride_name, matrix.width, 1, SPACE_PX)
        else:
            wrapped_ride_name = wrap_text(loaded_fonts["ride"], ride_name, matrix.width, 0, SPACE_PX)

    # Combine wrapped ride name and wait time into one list of lines
    combined_lines = wrapped_ride_name + wrapped_wait_time
    combined_lines = [line for line in combined_lines if line.strip() != ""]  # Remove blank lines

    # Calculate the total height of all lines
    total_lines_height, line_heights = calculate_text_height(combined_lines, wrapped_ride_name, getattr(loaded_fonts["ride"], "height"),
                                                             getattr(loaded_fonts["waittime"], "height"))
    return combined_lines, wrapped_ride_name, wrapped_wait_time, total_lines_height, line_heights


def bar_layout(matrix, ride_info):
    """
    How to fit the wait bar under this ride, as (reserve_rows, gap). Normal spacing
    first; a name that only just overflows falls back to tight spacing (no blank row
    above the bar, no gap above the wait) rather than losing the bar. Returns
    (0, GAP_BETWEEN_RIDE_AND_WAIT) when even that won't fit and the text wins.
    """
    *_, total_lines_height, _ = _layout(matrix, ride_info)
    for tight in (False, True):
        reserve = bar_reserve_rows(matrix.height, tight)
        gap = 0 if tight else GAP_BETWEEN_RIDE_AND_WAIT
        if total_lines_height + gap <= matrix.height - reserve:
            return reserve, gap
    return 0, GAP_BETWEEN_RIDE_AND_WAIT


def text_fits_above_bar(matrix, ride_info):
    return bar_layout(matrix, ride_info)[0] > 0


def render_attraction_info(matrix, ride_info, down_color=None, reserve_bottom=0, scroll_px=None, gap=None):
    """
    Renders ride name at the top and wait time at the bottom in a single draw call.
    The combined text block is drawn from the center of the screen.
    Each line is vertically centered, with a dynamic gap between ride name and wait time.
    Padding is added only if the text fits within the width and height of the board.
    reserve_bottom keeps that many rows clear at the bottom (for the wait bar); gap
    overrides the space between the ride name and the wait time.
    """
    debug.log(f"Rendering ride info: {ride_info}")
    gap_px = GAP_BETWEEN_RIDE_AND_WAIT if gap is None else gap
    combined_lines, wrapped_ride_name, wrapped_wait_time, total_lines_height, line_heights = _layout(matrix, ride_info)

    # Calculate x and y positions for centering the text
    if scroll_px is not None:
        # Too tall for the board: top-align the block and slide it up by scroll_px.
        # The taller 64-row font sits a row higher than its line height suggests.
        y_position = (1 if matrix.height >= 64 else 0) - scroll_px
    elif reserve_bottom:
        # Center the whole block, gap included, in the rows above the bar.
        y_position = (matrix.height - reserve_bottom - total_lines_height - gap_px) // 2
    else:
        y_position = calculate_y_position(matrix, total_lines_height)

    # Render each line of text
    render_lines(matrix, combined_lines, y_position, line_heights, wrapped_ride_name, wrapped_wait_time, down_color, gap_px)

def render_lines(matrix, combined_lines, y_position, line_heights, wrapped_ride_name, wrapped_wait_time, down_color=None, gap_px=None):
    """
    Render each line of text at the specified position on the matrix.
    """
    current_y_position = y_position + 5  # Add any necessary offset to center properly
    gap_between_ride_and_wait_time = GAP_BETWEEN_RIDE_AND_WAIT if gap_px is None else gap_px

    for idx, line in enumerate(combined_lines):
        line_width = get_text_width(loaded_fonts["ride"], line, SPACE_PX) if line in wrapped_ride_name else get_text_width(loaded_fonts["waittime"], line, SPACE_PX)

        # Center horizontally with or without padding
        line_x_position = (matrix.width - line_width) // 2

        # Draw the text on the matrix
        text_color = (
            color_dict["white"]
            if line in wrapped_ride_name
            else (down_color or color_dict["down"])
            if "down" in line.lower() or (any("down" in item.lower() for item in wrapped_wait_time) and line in wrapped_wait_time)
            else color_dict["wait"]
        )
        draw_text(matrix, loaded_fonts["ride"], line_x_position, current_y_position, text_color, line, SPACE_PX)

        # Move the y_position down for the next line
        current_y_position += line_heights[idx]

        # Add a gap after the ride name section to the wait time section
        if idx == len(wrapped_ride_name) - 1:
            current_y_position += gap_between_ride_and_wait_time


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

    return total_lines_height, line_heights


def get_longest_line_width(wrapped_ride_name, combined_lines, ride_font, waittime_font):
    """
    Calculate the width of the longest line in the combined lines.
    """
    longest_line_width = max(
        get_text_width(ride_font, line) if line in wrapped_ride_name else get_text_width(waittime_font, line)
        for line in combined_lines
    )
    return longest_line_width


def get_max_lines(board_height):
    """
    Calculates the maximum number of lines that can fit on the board.

    Args:
        board_height (int): The height of the matrix board.

    Returns:
        int: The maximum number of lines that can fit on the board.
    """
    # Get the height of one line in the specified font
    line_height = getattr(loaded_fonts["ride"], "height", 8)  # Default to 8 if height attribute is not available

    # Calculate the maximum number of lines the board can support
    max_lines = board_height // line_height

    return max_lines


def calculate_x_position(matrix, longest_line_width, padding):
    """
    Calculate the x_position for centering the text.
    """
    total_width_with_padding = longest_line_width + 2 * padding  # 1 unit on left and right
    if total_width_with_padding <= matrix.width:
        x_position = (matrix.width - total_width_with_padding) // 2
    else:
        x_position = (matrix.width - longest_line_width) // 2

    return x_position


def calculate_y_position(matrix, total_lines_height):
    """
    Calculate the y_position to center the text vertically on the board.
    """
    y_position = (matrix.height - total_lines_height) // 2
    return y_position
