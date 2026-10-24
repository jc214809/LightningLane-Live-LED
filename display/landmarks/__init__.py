"""
Short animated landmark scenes shown before each park's title screen.

Split by landmark: scene.py (the Landmark base), castle.py, spaceship_earth.py,
tower_of_terror.py, tree_of_life.py, pumpkins.py (the Halloween-party jack-o'-lanterns),
wine_and_dine.py (the Wine & Dine 5K's Marie, for its race day),
three_caballeros.py (the Wine & Dine 10K's Three Caballeros, for theirs), and
screen.py (landmark_for and landmark_screen). Everything is re-exported here, so
`from display import landmarks` and `landmarks.X` work as they did when this was one file.
"""

from display.landmarks.scene import (  # noqa: F401
    LANDMARK_S,
    SKY_RGB,
    TITLE_SHADOW_RGB,
    Landmark,
    _noise,
)

from display.landmarks.castle import (  # noqa: F401
    CastleLandmark,
)

from display.landmarks.spaceship_earth import (  # noqa: F401
    SpaceshipEarthLandmark,
)

from display.landmarks.tower_of_terror import (  # noqa: F401
    TowerOfTerrorLandmark,
)

from display.landmarks.tree_of_life import (  # noqa: F401
    TreeOfLifeLandmark,
)

from display.landmarks.pumpkins import (  # noqa: F401
    ScaryJackOLanternLandmark,
    FriendlyJackOLanternLandmark,
)

from display.landmarks.wine_and_dine import (  # noqa: F401
    WineAndDine5KLandmark,
)

from display.landmarks.three_caballeros import (  # noqa: F401
    ThreeCaballeros10KLandmark,
)

from display.landmarks.screen import (  # noqa: F401
    LANDMARKS,
    landmark_for,
    landmark_screen,
)

# Shared objects the tests patch attributes of (graphics.DrawText, loaded_fonts[...]).
from driver import graphics  # noqa: F401,E402
from display.display import loaded_fonts  # noqa: F401,E402
from utils.special_events import DATED_LANDMARKS, SPECIAL_EVENTS  # noqa: F401,E402  (tests check every party's and day's landmark exists)
