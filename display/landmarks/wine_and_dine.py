"""
The runDisney Wine & Dine 5K (The Aristocats): Marie on a purple Paris night, a big pink "5K" and
"Wine & Dine" beside her, and a second glass rising from behind the tablecloth to clink hers.
It replaces Spaceship Earth on race day (utils/special_events.py DATED_LANDMARKS).
"""

import math

from display import capture
from display.motion import ease_out, progress
from display.pixels import art_pixels

from display.landmarks.scene import TITLE_SHADOW_RGB, Landmark


GOLD, PINK = (255, 200, 60), (255, 90, 170)
SPARKLE = ((255, 240, 160), (255, 180, 60))  # near the rims, then further out
CLOTH, CLOTH_EDGE = (110, 10, 35), (150, 20, 50)

# The title is baked into the scene from these fonts (path, ascent) rather than drawn with the
# shared landmark title font, which only comes in 4x6.
BIG_FONT = ("assets/fonts/patched/9x18B.bdf", 14)
SMALL_FONT = ("assets/fonts/patched/5x8.bdf", 7)

# Marie for 64x64: sitting tall, read from docs/references/Marie tall seated outline.png
# (BraceletBook #20619) with the white outside her outline cleared. Drawn facing left; flipped to
# face the title. Her outline is grey rather than the chart's near-black so it shows on the night sky.
TALL_MARIE = [
    ".................S........",
    "................SWS.......",
    "..............SSSWS.......",
    ".......S.....SIISSWSS.....",
    "......SSS...SIIISISIIS....",
    ".....SIIS.SSSSIISISIIS....",
    "....SIIISSWWWWSSWSIIS.....",
    "....SIIIISWWWWWWWSSS......",
    "....SIIISWWWWWWWWWS.......",
    "....SIISWWWWWWWWWWWS......",
    ".SSSWSSWWWWSSWWWWWWS......",
    "SWWWWWWWWWSWWWWWSSWWS.....",
    ".SWWWWWWSWWWWWWWWWSWWSSS..",
    ".SWWWWWWWWSSWWWWWWWWSIIIS.",
    ".SWWWWWWWSSBSWWWWWWSSIIIS.",
    ".SWWWWWWSSBSWWWWWSSWSIIS..",
    "..SWWWWWWSSWWWWWSBSWWSIS..",
    "...SWWWWWSWWWSWSBSSWWWS...",
    "..SISWWWWWWWSISWSSWWWWS...",
    ".SIISSWWWSSWWSWWWWWWWWSS..",
    ".SIISISWWWWSWWWSSWWWWWS...",
    ".SIISIISSWWWSSSWWWWWSS....",
    "..SSSIIIISSWWWWWSSSS......",
    "..SWWSIIIIISSSSSIIIS......",
    ".SWWWWSSIIIISWSIIIIS......",
    ".SWWWWWWSSSSWWWSIIS.......",
    ".SWWWWWWWWSWWWWSSIS.......",
    ".SWWWWWWWSSWWWWWWS........",
    ".SWWWWWWWSSWWWWWWWS.......",
    ".SWWWWWWWSWWWWWWWWWS......",
    "..SWWWWWSWWWWWWWWWWS......",
    "..SWWWWWSWWWWWWWWWWWS.....",
    "..SSWWWSWWWWWWWWWWWWS.....",
    "..SWWWWSWWWWWWWWWWWWS.....",
    "..SWSWWSWWWWWWWWWWWWS.....",
    "..SWWSWSWWWWWWWWWWWWS.....",
    "...SWWSWWWWWWSWWWWWWS.....",
    "...SWWSWWWWWWSWWWWWWS.....",
    "...SWWSWWWWSWWWWWWWWS.....",
    "..SSWWSWWWWSWWWWWWWSWSSS..",
    ".SWWWWSWWWSWWWWWWWWSWWWWS.",
    "SWSWSSWWWSSWWWWWWWSWWWWWWS",
    ".SWSWWWWWSSSWWWWWWSWWWWWWS",
    "..SSWWWWSWWWSWSSSS.SWWWWWS",
    "....SSSS.SSSSS.....SWWWWS.",
    "...................SWWSS..",
    "...................SWS....",
    "....................S.....",
]
OUTLINE = (0, 0, 0)  # painted black, so the purple sky and the stars can't show through it
TALL_COLORS = {"W": (255, 255, 255), "S": OUTLINE, "I": (255, 40, 170), "B": (1, 169, 244)}

# Marie for 64x32: head and paws peeking over the table, read from docs/references/Marie head and
# paws.png (Pixilart, HoldMyFlower). Its pastel pinks are deepened: on LEDs they read as white.
PEEK_MARIE = [
    ".............SSSSS...........",
    "............SWWWS............",
    "............SWWWS............",
    ".....S.....iiWWSii.....S.....",
    "....ISS...iIIiiiIIi...SSI....",
    "...IISWS..iIIiIiIIi..SWSII...",
    "...IISWWS.iIIiiiIIi.SWWSII...",
    "...IIISWS..iiWWWii..SWSIII...",
    "..IIIISWWSSWWWWWWWSSWWSIIII..",
    "..IIIIISWWWWWWWWWWWWWSIIIII..",
    "..IIIIISWWWWWWWWWWWWWSIIIII..",
    "..IIIIISWWWWWWWWWWWWWSIIIII..",
    "..IIIISWWWWWWWWWWWWWWWSIIII..",
    "..IIIISWWWWWWWWWWWWWWWSIIII..",
    "...IISWWWWWWWWWWWWWWWWWSII...",
    "...ISWWWWWWWWWWWWWWWWWWWSI...",
    "...SWWWSKKSWWWWWWWSKKSWWWS...",
    ".SSWWWWKWCKSWWWWWSKCWKWWWWSS.",
    "SWWWWWWWCKKKWWWWWKKKCWWWWWWWS",
    ".SWWWWWWCKKKWWWWWKKKCWWWWWWS.",
    "..SWWWSSSKKWWIIIWWKKSSSWWWS..",
    "...SWWWWWSWWWWIWWWWSWWWWWS...",
    "..IISWWSSWWSWWSWWSWWSSWWSII..",
    "..IISSSWWWWWSSWSSWWWWWSSSII..",
    "..ISWWWSSSWWWWWWWWWSSSWWWSI..",
    "...SWWWWWWSSSSSSSSSWWWWWWS...",
    "....SWWWWWS.......SWWWWWS....",
    ".....SSSSS.........SSSSS.....",
]
PEEK_COLORS = {
    "W": (255, 255, 255), "S": OUTLINE, "I": (255, 120, 170), "i": (230, 40, 110),
    "K": (0, 0, 0),  # pupils
    "C": (1, 169, 244),
}

WINE_GLASS = [
    "g...g",
    "gRRRg",
    "grRRg",
    ".gRg.",
    "..g..",
    "..g..",
    ".ggg.",
]
GLASS_COLORS = {"g": (170, 200, 230), "R": (170, 10, 40), "r": (230, 40, 70)}

RISE = (1.0, 1.8)  # scene seconds: the second glass rises from behind the tablecloth
CLINK_S = 0.8  # the sparkle where the rims meet, from the end of the rise
SETTLE_S = 0.2  # then the glass sinks the row it rose over hers


def _text_pixels(font, text, center_x, top, rgb):
    """{(x, y): rgb} for text in a BDF font, centred on center_x, with the landmarks' drop shadow."""
    path, ascent = font
    glyphs = capture._glyphs(path)
    width = sum(glyphs[ord(ch)][0] for ch in text)
    out = {}
    for dx, colour in ((1, TITLE_SHADOW_RGB), (0, rgb)):
        x = round(center_x - width / 2) + dx
        baseline = top + ascent + dx
        for ch in text:
            advance, height, x_offset, y_offset, rows, glyph_w = glyphs[ord(ch)]
            for r, bits in enumerate(rows):
                for c in range(min(glyph_w, len(bits))):
                    if bits[c] == "1":
                        out[(x + x_offset + c, baseline - height - y_offset + r)] = colour
            x += advance
    return out


class WineAndDine5KLandmark(Landmark):
    """Wine & Dine 5K: Marie on a purple Paris night clinks glasses beside a big pink 5K."""

    SCREEN_S = 5.0

    def build(self):
        w, h = self.width, self.height
        lay = self._layout()
        self.glass_scale, self.hers_x, self.friend_x, self.glass_y = (
            lay["glass_scale"], lay["hers_x"], lay["friend_x"], lay["glass_y"])
        self.glass_h = len(WINE_GLASS) * self.glass_scale
        # Where the rims meet: the sparkle's centre.
        left, right = sorted((self.hers_x, self.friend_x))
        self.meet = ((left + right + len(WINE_GLASS[0]) * self.glass_scale) // 2, self.glass_y + 1 + self.glass_scale)
        self.sky = {}
        for y in range(h):
            f = y / (h - 1)
            rgb = (round(70 - 45 * f), round(25 - 12 * f), round(120 - 60 * f))  # the 5K poster's purple
            for x in range(w):
                self.sky[(x, y)] = rgb
        self.table = {}
        for y in range(h - lay["table_rows"], h):
            for x in range(w):
                self.table[(x, y)] = CLOTH_EDGE if y == h - lay["table_rows"] else CLOTH
        art, colors = lay["marie"]
        self.marie_box = (lay["marie_x"], lay["marie_y"], len(art[0]), len(art))
        self.base.update(art_pixels(art, lay["marie_x"], lay["marie_y"], colors))
        self.base.update(self._glass(self.hers_x, self.glass_y))
        self.text = {}
        for font, text, center_x, top, rgb in lay["title"]:
            self.text.update(_text_pixels(font, text, center_x, top, rgb))

    def _layout(self):
        """64x64: the tall Marie on the right facing in, the title stacked on the left, 2x glasses.
        64x32: the peeking Marie on the right, the title on the left, 1x glasses between."""
        w, h = self.width, self.height
        if h >= 64:
            marie = [row[::-1] for row in TALL_MARIE]
            return {
                "marie": (marie, TALL_COLORS), "marie_x": w - len(marie[0]), "marie_y": h - 2 - len(marie),
                "table_rows": 2, "glass_scale": 2, "hers_x": 24, "friend_x": 11,
                "glass_y": h - 2 - 2 * len(WINE_GLASS),
                "title": [(BIG_FONT, "5K", 18, 0, PINK), (SMALL_FONT, "WINE &", 18, 20, GOLD),
                          (SMALL_FONT, "DINE", 18, 28, GOLD)],
            }
        return {
            "marie": (PEEK_MARIE, PEEK_COLORS), "marie_x": w - len(PEEK_MARIE[0]),
            "marie_y": h - 1 - len(PEEK_MARIE),
            "table_rows": 1, "glass_scale": 1, "hers_x": 29, "friend_x": 23, "glass_y": h - 1 - len(WINE_GLASS),
            "title": [(BIG_FONT, "5K", 17, 0, PINK), (SMALL_FONT, "WINE &", 17, 15, GOLD),
                      (SMALL_FONT, "DINE", 11, 23, GOLD)],
        }

    def _glass(self, x, y):
        return dict(art_pixels(WINE_GLASS, x, y, GLASS_COLORS, self.glass_scale))

    def friend_glass_y(self, t):
        """Top row of the rising glass at scene time t: below the board, up to a row above hers for
        the clink, then down level with it."""
        start = self.height + 1
        clink_y = self.glass_y - 1
        y = start + (clink_y - start) * ease_out(progress(t, *RISE))
        settle_from = RISE[1] + CLINK_S
        return round(y + progress(t, settle_from, settle_from + SETTLE_S))

    def sparkle(self, t):
        """{(x, y): rgb} of the clink's sparkle: rays growing out from where the rims meet."""
        age = t - RISE[1]
        if not 0 <= age < CLINK_S:
            return {}
        reach = (2 if self.glass_scale > 1 else 1) + int(age * 4) * self.glass_scale // 2
        mx, my = self.meet
        out = {}
        for d in range(1, reach + 1):
            rgb = SPARKLE[0] if d < 3 else SPARKLE[1]
            for dx, dy in ((d, 0), (-d, 0), (0, -d), (d, -d), (-d, -d)):
                out[(mx + dx, my + dy)] = rgb
        return out

    def frame(self, t):
        out = dict(self.sky)
        for x, y, phase in self.stars:  # brighter than the base twinkle so they show on purple
            level = 90 + int(60 * (1 + math.sin(t * 3 + phase)))
            out[(x, y)] = (level, level, min(255, level + 30))
        out.update(self.base)
        # The rising glass goes under the tablecloth, so it comes up from behind it.
        for (x, y), rgb in self._glass(self.friend_x, self.friend_glass_y(t)).items():
            if 0 <= x < self.width and 0 <= y < self.height:
                out[(x, y)] = rgb
        out.update(self.table)
        out.update(self.text)
        out.update(self.sparkle(t))
        return out
