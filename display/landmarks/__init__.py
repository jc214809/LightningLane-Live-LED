"""
Short animated landmark scenes shown before each park's title screen.

Split by landmark: scene.py (the Landmark base), castle.py, spaceship_earth.py,
tower_of_terror.py, tree_of_life.py, pumpkins.py (the Halloween-party jack-o'-lanterns), and
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

from display.landmarks.screen import (  # noqa: F401
    LANDMARKS,
    landmark_for,
    landmark_screen,
)

# Shared objects the tests patch attributes of (graphics.DrawText, loaded_fonts[...]).
from driver import graphics  # noqa: F401,E402
from display.display import loaded_fonts  # noqa: F401,E402
from utils.special_events import SPECIAL_EVENTS  # noqa: F401,E402  (tests check every party's landmark exists)
