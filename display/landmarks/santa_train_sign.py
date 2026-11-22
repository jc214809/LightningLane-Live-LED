"""The Santa train's billboard car: the sign saying the party's name and tonight's hours, in a red frame with a ring
of bulbs chasing round it."""

from display import capture
from display.landmarks.santa_train_art import COLORS
from display.landmarks.three_caballeros import SMALL_FONT, TINY_FONT
from display.landmarks.wine_and_dine import _text_pixels

FRAME_PX = {True: 2, False: 1}
# A midnight-blue board with bright lettering, white, red and green line by line from the top: red and
# green on the old light grey board (170, 170, 176) were hard to read on a real panel (Disneypi, 2026-11-08).
SIGN_RGB = (8, 12, 45)
SIGN_INK = ((235, 235, 240), (255, 70, 70), (60, 220, 80))
NAME = {
    True: ["MICKEY'S", "VERY MERRY", "CHRISTMAS", "PARTY"],  # 5x8: one word or two a line
    False: ["MICKEY'S", "VERY MERRY", "CHRISTMAS PARTY"],
}  # 4x6: "CHRISTMAS PARTY" is 60 of 62 px
# 64x32's sign puts the hours first, "TONIGHT 7PM-12AM", above the name. A space is 4 px, which makes that
# line 63 px, one more than fits inside the frame, so its space is 2 px. Hours too wide even so (a 10PM
# start) show alone.
TONIGHT, TONIGHT_SPACE_PX = "TONIGHT", 2


def ring(width, height):
    """The (x, y) round a width x height box's edge, clockwise from the top left."""
    top = [(x, 0) for x in range(width)]
    right = [(width - 1, y) for y in range(1, height)]
    bottom = [(x, height - 1) for x in range(width - 2, -1, -1)]
    left = [(0, y) for y in range(height - 2, 0, -1)]
    return top + right + bottom + left


def text_width(font, text, space_px=None):
    """The px a line of text takes in a font (its glyphs' advances), with each space `space_px` wide if given."""
    glyphs = capture._glyphs(font[0])
    return sum(space_px if ch == " " and space_px is not None else glyphs[ord(ch)][0] for ch in text)


def sign_lines(big, hours, inside_w, font):
    """The billboard's lines, top to bottom: the party's name then the hours on 64x64; on 64x32 "TONIGHT" and
    the hours first, then the name (the hours alone if that line won't fit `inside_w`). No hours: the name."""
    if not hours:
        return list(NAME[big])
    hours = "-".join(hours)
    if big:
        return NAME[big] + [hours]
    tonight = f"{TONIGHT} {hours}"
    fits = text_width(font, tonight, TONIGHT_SPACE_PX) - 1 <= inside_w  # less the last glyph's blank column
    return [tonight if fits else hours] + NAME[big]


def line_pixels(font, text, center_x, top, rgb, space_px=None):
    """{(x, y): rgb} for a line of sign lettering centred on center_x, each space `space_px` wide if given."""
    if space_px is None:
        return _text_pixels(font, text, center_x, top, rgb, shadow=False)
    words = text.split(" ")
    x = round(center_x - text_width(font, text, space_px) / 2)
    out = {}
    for word in words:
        width = text_width(font, word)
        out.update(_text_pixels(font, word, x + width / 2, top, rgb, shadow=False))
        x += width + space_px
    return out


def sign_pixels(width, height, lines, frame):
    """{(x, y): rgb} of the billboard: a red frame `frame` px wide round the board, and `lines`
    [(font, text, rgb)] or [(font, text, rgb, space px)] centred on it, spaced evenly down it."""
    out = {
        (x, y): COLORS["R"] if min(x, y, width - 1 - x, height - 1 - y) < frame else SIGN_RGB
        for x in range(width)
        for y in range(height)
    }
    inside = height - 2 * frame
    ink = sum(line[0][1] for line in lines)
    gap = max(1, (inside - ink) // (len(lines) + 1))
    top = frame + (inside - ink - gap * (len(lines) - 1)) // 2
    for font, text, rgb, *space in lines:
        out.update(line_pixels(font, text, width / 2, top, rgb, space[0] if space else None))
        top += font[1] + gap
    return out


def billboard(width, height, big, hours):
    """{(x, y): rgb} of the sign for a width x height board: the lines for `hours` (None: the name alone) in the
    board's font, inked white, red and green down it, 64x32's "TONIGHT" line with its tight space."""
    font = SMALL_FONT if big else TINY_FONT
    names = [(text, None) for text in sign_lines(big, hours, width - 2 * FRAME_PX[big], font)]
    if not big and hours and names[0][0].startswith(TONIGHT):
        names[0] = (names[0][0], TONIGHT_SPACE_PX)
    lines = [(font, text, SIGN_INK[i % len(SIGN_INK)], space) for i, (text, space) in enumerate(names)]
    return sign_pixels(width, height, lines, FRAME_PX[big])
