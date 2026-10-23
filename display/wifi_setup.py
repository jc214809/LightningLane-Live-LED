from display.countdown.countdown import _fitting_font, _stack
from display.display import color_dict, get_text_width, loaded_fonts, wrap_text

TITLE = "Wi-Fi setup"
# Each line takes the first of its fonts it fits in.
TITLE_FONTS = ("countdown_message", "countdown_label", "info")
NAME_FONTS = ("ride", "info")
MARGIN = 1


def render_wifi_setup(canvas, name):
    """The Wi-Fi setup screen: what the board is doing and the open hotspot to join, centred."""
    width = canvas.width - 2 * MARGIN
    title = _fitting_font([loaded_fonts[f] for f in TITLE_FONTS], [TITLE], width)
    small = loaded_fonts["info"]
    font = _fitting_font([loaded_fonts[f] for f in NAME_FONTS], [name], width)
    rows = [(title, color_dict["gold"], TITLE), (small, color_dict["white"], "Join")]
    rows += [(font, color_dict["wait"], line) for line in name_lines(font, name, width)]
    _stack(canvas, (MARGIN, 0, width, canvas.height), rows)


def name_lines(font, name, width):
    """The hotspot name in lines that fit: broken after its hyphens ("Disneypi-" / "setup"), and
    a piece still too wide wherever it has to be (a hotspot name is at most 32 letters)."""
    lines = []
    for piece in wrap_text(font, name, width, 0):
        line = ""
        for ch in piece:
            if line and get_text_width(font, line + ch) > width:
                lines.append(line)
                line = ""
            line += ch
        lines.append(line)
    return lines
