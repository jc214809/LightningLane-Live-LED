import math
from datetime import date

from display.animation import ease_out
from display.display import draw_text, get_text_width, loaded_fonts, color_dict
from display.fireworks.fireworks import castle_sprite, _CASTLE_COLORS

# The castle stays 1x on 64-row boards too: doubled it leaves no room for the number.
CASTLE_PIXELS, CASTLE_W, CASTLE_H = castle_sprite(32)
# Rows between stacked lines: roomier when the box allows, tighter when it doesn't.
LINE_GAPS = (2, 1)
COUNT_UP_S = 1.0
TWINKLE_PERIOD_S = 1.6
TWINKLE_MIN = 0.35


def countdown_message(trip, today=None):
    """
    What the countdown says, as (number, lines): big text with a label under it, or
    number None and a message on the days that deserve one. A trip's name, when it
    has one, stands in for "DISNEY" under the day count (render falls back to
    "DISNEY" if the name doesn't fit).
    """
    today = today or date.today()
    days = (trip.start - today).days
    if days > 1:
        return str(days), ("DAYS TO", (trip.name or "DISNEY").upper())
    if days == 1:
        return None, ("DISNEY", "TOMORROW")
    if days == 0:
        return None, ("IT'S", "DISNEY", "DAY!")
    if trip.end is None:
        return None, ("HAVE A", "MAGICAL", "TRIP!")
    if today <= trip.end:
        return f"DAY {1 - days}", (f"OF {(trip.end - trip.start).days + 1}",)
    return None, ("WELCOME", "HOME!")


def layout(width, height):
    """
    (castle_xy, text_box) for the board: the castle beside the text on 32-row boards
    and above it on 64-row ones. text_box is (x, y, w, h), the area the text centers in.
    """
    if height >= 64:
        castle = ((width - CASTLE_W) // 2, 3)
        top = castle[1] + CASTLE_H + 3
        return castle, (0, top, width, height - top - 2)
    castle = (0, height - CASTLE_H - 2)
    left = castle[0] + CASTLE_W + 1
    return castle, (left, 0, width - left, height)


def draw_castle(canvas, x0, y0, t):
    """The castle, its lit windows twinkling out of step with each other."""
    for i, (dx, dy, kind) in enumerate(CASTLE_PIXELS):
        r, g, b = _CASTLE_COLORS[kind]
        if kind == "Y":
            wave = 0.5 + 0.5 * math.sin(2 * math.pi * t / TWINKLE_PERIOD_S + i * 2.4)
            k = TWINKLE_MIN + (1 - TWINKLE_MIN) * wave
            r, g, b = int(r * k), int(g * k), int(b * k)
        canvas.SetPixel(x0 + dx, y0 + dy, r, g, b)


def counted(number, t):
    """The day count rolling up from zero over COUNT_UP_S; anything else as-is."""
    if not number.isdigit():
        return number
    return str(round(int(number) * ease_out(t / COUNT_UP_S)))


def _space(font):
    # The fonts' own space is a full cell; "DAY 3" reads as two words at half that.
    return max(2, font.CharacterWidth(ord(" ")) // 2)


def _width(font, text):
    return get_text_width(font, text, _space(font))


def _ink_height(font):
    # Capitals and digits sit on the baseline and reach up to about the font's ascent;
    # the descent below is empty for everything drawn here.
    return font.baseline


def _stack_height(rows, gap):
    return sum(_ink_height(font) for font, _, _ in rows) + gap * (len(rows) - 1)


def _fits(rows, box):
    _, _, w, h = box
    return (_stack_height(rows, LINE_GAPS[-1]) <= h
            and all(_width(font, text) <= w for font, _, text in rows))


def _fitting_font(fonts, lines, max_width):
    """The first (largest) font every line fits in, else the last one."""
    for font in fonts:
        if all(_width(font, line) <= max_width for line in lines):
            return font
    return fonts[-1]


def _stack(canvas, box, rows):
    """Draw rows of (font, color, text) centered as a block in box."""
    x, y, w, h = box
    gap = next((g for g in LINE_GAPS if _stack_height(rows, g) <= h), LINE_GAPS[-1])
    top = y + (h - _stack_height(rows, gap)) // 2
    for font, color, text in rows:
        baseline = top + _ink_height(font)
        draw_text(canvas, font, x + (w - _width(font, text)) // 2, baseline, color, text, _space(font))
        top = baseline + gap


def _number_rows(number, lines, box):
    big, label = loaded_fonts["countdown_number"], loaded_fonts["countdown_label"]
    rows = [(big, color_dict["gold"], number)]
    rows += [(label, color_dict["mickey_mouse_red"], line) for line in lines]
    if not _fits(rows, box) and len(lines) > 1:
        # A trip name too long for the box gives way to plain "DISNEY".
        rows[-1] = (label, color_dict["mickey_mouse_red"], "DISNEY")
    return rows


def render_countdown_to_disney(canvas, trip, t=0.0, today=None):
    """
    Draw the trip countdown t seconds in: the twinkling castle, then the days left
    rolling up in big gold digits over a small label. Always animating (the twinkle).
    """
    castle, box = layout(canvas.width, canvas.height)
    draw_castle(canvas, *castle, t)
    number, lines = countdown_message(trip, today)
    if number is not None:
        # Fit is judged on the final number, so the label never changes mid-count.
        rows = _number_rows(number, lines, box)
        font, color, _ = rows[0]
        rows[0] = (font, color, counted(number, t))
    else:
        font = _fitting_font([loaded_fonts["countdown_message"], loaded_fonts["countdown_label"]], lines, box[2])
        rows = [(font, color_dict["gold"], line) for line in lines]
    _stack(canvas, box, rows)
    return True
