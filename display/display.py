import os

from driver import graphics
from utils import debug

loaded_fonts = {}


def fonts():
    """Define font paths for different board sizes."""
    return {
        32: {
            "park": "assets/fonts/patched/5x8.bdf",
            "info": "assets/fonts/patched/4x6-legacy.bdf",
            "waittime": "assets/fonts/patched/4x6-legacy.bdf",
            "ride": "assets/fonts/patched/4x6-legacy.bdf",
            "countdown": "assets/fonts/patched/6x9.bdf"
        },
        64: {
            "park": "assets/fonts/patched/6x13.bdf",
            "info": "assets/fonts/patched/4x6-legacy.bdf",
            "waittime": "assets/fonts/patched/5x8.bdf",
            "ride": "assets/fonts/patched/5x8.bdf",
            "countdown": "assets/fonts/patched/6x9.bdf"
        }
    }


def initialize_fonts(matrix_height):
    """Load and return all fonts based on the board height."""
    global loaded_fonts
    # loaded_fonts = {}  # Reset the loaded_fonts dictionary

    # Log font paths for clarity
    # matrix_height = 64  # Replace with the actual height if needed
    font_dict = fonts().get(matrix_height)

    if font_dict is None:
        debug.error(f"No font definitions found for height {matrix_height}.")
        return None  # Handle case where no fonts are defined

    # Load each font and log the process
    for name, path in font_dict.items():
        font = graphics.Font()
        absolute_path = os.path.abspath(path)
        try:
            font.LoadFont(absolute_path)  # Attempt to load the font
            loaded_fonts[name] = font  # Cache the loaded font
            debug.info(f"Successfully loaded font '{name}' from '{absolute_path}'")
        except Exception as e:
            debug.error(f"Error loading font from path {absolute_path}: {e}")

    debug.info(f"Loaded fonts: {list(loaded_fonts.keys())}")  # Show successfully loaded fonts
    return loaded_fonts  # Return the loaded fonts dictionary

def colors():
    # Return a dictionary of colors
    return {
        "mickey_mouse_red": graphics.Color(242, 5, 5),
        "disney_blue": graphics.Color(17, 60, 207),
        "white": graphics.Color(255, 255, 255),
        "down": graphics.Color(250, 0, 0),
        "gold": graphics.Color(255, 215, 0)
    }

color_dict = colors()

def get_text_width(font, text):
    """Helper to calculate total width of text in pixels."""
    return sum(font.CharacterWidth(ord(ch)) for ch in text)


def wrap_text(font, text, max_width, padding):
    """
    Wrap text to fit within the specified max_width (ignoring max_height here for brevity).
    Returns a list of lines (strings).
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        word_width = get_text_width(font, word)
        if word_width > max_width:
            # Word alone doesn't fit; put it on its own line
            if current_line:
                lines.append(current_line)
                current_line = ""
            lines.append(word)
            continue

        test_line = (current_line + " " + word).strip() if current_line else word
        test_line_width = get_text_width(font, test_line)
        if test_line_width <= max_width - padding:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines