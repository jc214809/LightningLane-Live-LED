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
            "countdown": "assets/fonts/patched/6x9.bdf",
            "title": "assets/fonts/patched/4x6-legacy.bdf"
        },
        64: {
            "park": "assets/fonts/patched/6x13.bdf",
            "info": "assets/fonts/patched/4x6-legacy.bdf",
            "waittime": "assets/fonts/patched/5x8.bdf",
            "ride": "assets/fonts/patched/5x8.bdf",
            "countdown": "assets/fonts/patched/6x9.bdf",
            "title": "assets/fonts/patched/4x6-legacy.bdf"
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

DOWN_RGB = (250, 0, 0)


def colors():
    # Return a dictionary of colors
    return {
        "mickey_mouse_red": graphics.Color(242, 5, 5),
        "disney_blue": graphics.Color(17, 60, 207),
        "white": graphics.Color(255, 255, 255),
        "down": graphics.Color(*DOWN_RGB),
        "gold": graphics.Color(255, 215, 0),
        "wait": graphics.Color(90, 210, 255)
    }

color_dict = colors()

def get_text_width(font, text, space_px=None):
    """Helper to calculate total width of text in pixels; space_px overrides the font's space width."""
    if space_px is None:
        return sum(font.CharacterWidth(ord(ch)) for ch in text)
    return sum(space_px if ch == " " else font.CharacterWidth(ord(ch)) for ch in text)


def draw_text(canvas, font, x, y, color, text, space_px=None):
    """graphics.DrawText, but with spaces space_px wide when given (fonts' own spaces are a full cell)."""
    if space_px is None:
        return graphics.DrawText(canvas, font, x, y, color, text)
    for i, word in enumerate(text.split(" ")):
        if i:
            x += space_px
        if word:
            graphics.DrawText(canvas, font, x, y, color, word)
            x += get_text_width(font, word)


# Typographic characters the board fonts don't have; they'd draw as a wide placeholder box.
_PLAIN_CHARS = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "®": None, "™": None, "©": None,
})


def plain_text(text):
    """Replace curly quotes, dashes and trademark symbols with characters the fonts can draw."""
    return " ".join(text.translate(_PLAIN_CHARS).split())


def wrap_text(font, text, max_width, padding, space_px=None):
    """
    Wrap text to fit within the specified max_width (ignoring max_height here for brevity).
    Returns a list of lines (strings).
    """
    words = []
    for word in text.split():
        # A hyphenated word wider than the board ("Circle-Vision") breaks after its hyphens.
        if get_text_width(font, word, space_px) > max_width and "-" in word.strip("-"):
            parts = word.split("-")
            words.extend(part + "-" for part in parts[:-1])
            words.append(parts[-1])
        else:
            words.append(word)
    lines = []
    current_line = ""

    for word in words:
        word_width = get_text_width(font, word, space_px)
        if word_width > max_width:
            # Word alone doesn't fit; put it on its own line
            if current_line:
                lines.append(current_line)
                current_line = ""
            lines.append(word)
            continue

        test_line = (current_line + " " + word).strip() if current_line else word
        test_line_width = get_text_width(font, test_line, space_px)
        if test_line_width <= max_width - padding:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines