"""
Which landmark a park gets (landmark_for) and how one plays as a screen (landmark_screen).
"""

from display.display import get_text_width, loaded_fonts
from driver import graphics
from utils.special_events import SPECIAL_EVENTS

from display.landmarks.scene import TITLE_SHADOW_RGB
from display.landmarks.castle import CastleLandmark
from display.landmarks.spaceship_earth import SpaceshipEarthLandmark
from display.landmarks.tower_of_terror import TowerOfTerrorLandmark
from display.landmarks.tree_of_life import TreeOfLifeLandmark
from display.landmarks.pumpkins import FriendlyJackOLanternLandmark, ScaryJackOLanternLandmark  # looked up by class name for parties (landmark_for)


LANDMARKS = {
    "magic kingdom": CastleLandmark,
    "epcot": SpaceshipEarthLandmark,
    "hollywood studios": TowerOfTerrorLandmark,
    "animal kingdom": TreeOfLifeLandmark,
}


def landmark_for(park_name, party=None):
    """The landmark scene class for a park, matched loosely on its name, or None. A party
    (a SPECIAL_EVENTS key the park is holding today) swaps in that party's own landmark, if it has one."""
    if SPECIAL_EVENTS.get(party, {}).get("landmark"):
        return globals()[SPECIAL_EVENTS[party]["landmark"]]
    name = (park_name or "").lower()
    for key, cls in LANDMARKS.items():
        if key in name:
            return cls
    return None


def landmark_screen(landmark):
    """Adapt a Landmark to show_screen's draw(canvas, t) contract; it animates for its whole hold."""
    def draw(canvas, t):
        for (x, y), (r, g, b) in landmark.frame(t).items():
            canvas.SetPixel(x, y, r, g, b)
        lines = landmark.title(t)
        if lines:
            font = loaded_fonts["landmark_title"]
            shadow = graphics.Color(*TITLE_SHADOW_RGB)
            for text, center_x, top, rgb in lines:
                x = round(center_x - get_text_width(font, text) / 2)
                y = top + font.baseline
                # A one-pixel drop shadow keeps the letters off the sky, the mist and the pumpkin.
                graphics.DrawText(canvas, font, x + 1, y + 1, shadow, text)
                graphics.DrawText(canvas, font, x, y, graphics.Color(*rgb), text)
        return True
    draw.plays_under_reveal = landmark.PLAYS_UNDER_WIPE
    return draw
