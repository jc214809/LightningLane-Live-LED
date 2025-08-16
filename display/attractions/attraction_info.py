from display.display import wrap_text, get_text_width, color_dict, loaded_fonts
from driver import graphics
from utils import debug


def render_attraction_info(matrix, ride_info):
    """
    Renders ride name at the top and wait time at the bottom in a single draw call.
    The combined text block is drawn from the center of the screen.
    Each line is vertically centered, with a dynamic gap between ride name and wait time.
    Padding is added only if the text fits within the width and height of the board.
    """
    debug.log(f"Rendering ride info: {ride_info}")
    ride_name = ride_info["name"]
    wait_time = f"{ride_info['waitTime']} Mins"


    # waittime_font = loaded_fonts["waittime"]

    # Wrap the text for both ride name and wait time
    wrapped_ride_name = wrap_text(loaded_fonts["ride"],ride_name, matrix.width,1)
    if get_max_lines(matrix.height) - 1 < len(wrapped_ride_name):
        if "Meet " in ride_name:
            ride_name = ride_name.rsplit(" at ", 1)[0]
            wrapped_ride_name = wrap_text(loaded_fonts["ride"], ride_name, matrix.width, 1)
        else:
            wrapped_ride_name = wrap_text(loaded_fonts["ride"], ride_name, matrix.width, 0)
    wrapped_wait_time = wrap_text(loaded_fonts["waittime"], wait_time, matrix.width, 1)

    # Combine wrapped ride name and wait time into one list of lines
    combined_lines = wrapped_ride_name + wrapped_wait_time
    combined_lines = [line for line in combined_lines if line.strip() != ""]  # Remove blank lines

    # Calculate the total height of all lines
    total_lines_height, line_heights = calculate_text_height(combined_lines, wrapped_ride_name, getattr(loaded_fonts["ride"], "height"),
                                                             getattr(loaded_fonts["waittime"], "height"))

    # Calculate x and y positions for centering the text
    y_position = calculate_y_position(matrix, total_lines_height)

    # Render each line of text
    render_lines(matrix, combined_lines, y_position, line_heights, wrapped_ride_name, wrapped_wait_time)

def render_lines(matrix, combined_lines, y_position, line_heights, wrapped_ride_name, wrapped_wait_time):
    """
    Render each line of text at the specified position on the matrix.
    """
    current_y_position = y_position + 5  # Add any necessary offset to center properly
    gap_between_ride_and_wait_time = 2  # Default gap between the sections

    for idx, line in enumerate(combined_lines):
        line_width = get_text_width(loaded_fonts["ride"], line) if line in wrapped_ride_name else get_text_width(loaded_fonts["waittime"], line)

        # Center horizontally with or without padding
        line_x_position = (matrix.width - line_width) // 2

        # Draw the text on the matrix
        text_color = (
            color_dict["white"]
            if line in wrapped_ride_name
            else color_dict["down"]
            if "down" in line.lower() or (any("down" in item.lower() for item in wrapped_wait_time) and line in wrapped_wait_time)
            else color_dict["white"]
        )
        graphics.DrawText(matrix, loaded_fonts["ride"], line_x_position, current_y_position, text_color, line)

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
