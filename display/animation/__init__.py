"""
Screen transitions and the characters that play them. Every screen after the intro plays
through show_screen (player.py); TRANSITIONS (characters/__init__.py) names them all.

The package is split by job: motion.py (time and easing), drawing.py (pixels on the
board), mechanics.py (the kinds of reveal), player.py (playing a screen) and one file per
character under characters/. Everything is re-exported here, so `from display import
animation` and `animation.X` work as they did when this was one file.
"""

from display.animation.motion import (  # noqa: F401
    COVER_S,
    FLYBY_S,
    FPS,
    WIPE_S,
    _hops,
    ease_out,
    progress,
)

from display.animation.drawing import (  # noqa: F401
    EDGE_RGB,
    _blackout,
    _blackout_rows,
    _edge,
    _letters,
    _rotate_art,
    WALK_CYCLE,
    art_pixels,
    paint,
    walking_pixels,
)

from display.animation.mechanics import (  # noqa: F401
    CapturesScreens,
    FlyByReveal,
    PeekReveal,
    Wipe,
)

from display.animation.player import (  # noqa: F401
    _canvases,
    _last_screen,
    forget_screen,
    frame_canvas,
    present,
    run_frames,
    show_screen,
)

from display.animation.characters import (  # noqa: F401
    TRANSITIONS,
)

from display.animation.characters.army_men import (  # noqa: F401
    ArmyMenReveal,
)

from display.animation.characters.baymax import (  # noqa: F401
    BaymaxReveal,
)

from display.animation.characters.buzz import (  # noqa: F401
    BuzzReveal,
)

from display.animation.characters.chip_dale import (  # noqa: F401
    ChipDaleReveal,
)

from display.animation.characters.dumbo import (  # noqa: F401
    DumboReveal,
)

from display.animation.characters.falcon import (  # noqa: F401
    FalconReveal,
)

from display.animation.characters.figment import (  # noqa: F401
    FigmentReveal,
)

from display.animation.characters.genie import (  # noqa: F401
    GenieReveal,
)

from display.animation.characters.goofy import (  # noqa: F401
    GoofyReveal,
)

from display.animation.characters.luxo_ball import (  # noqa: F401
    LuxoBallReveal,
)

from display.animation.characters.mater import (  # noqa: F401
    MaterReveal,
)

from display.animation.characters.mcqueen import (  # noqa: F401
    McQueenReveal,
)

from display.animation.characters.mickey import (  # noqa: F401
    MickeyReveal,
)

from display.animation.characters.mike import (  # noqa: F401
    MikeReveal,
)

from display.animation.characters.olaf import (  # noqa: F401
    OlafReveal,
)

from display.animation.characters.ralph import (  # noqa: F401
    RalphReveal,
)

from display.animation.characters.slinky import (  # noqa: F401
    SlinkyReveal,
    SlinkyWrapReveal,
)

from display.animation.characters.stitch import (  # noqa: F401
    StitchSurfReveal,
)

from display.animation.characters.tink import (  # noqa: F401
    TinkReveal,
)

from display.animation.characters.tigger import (  # noqa: F401
    TiggerReveal,
)

from display.animation.characters.donald import (  # noqa: F401
    DonaldReveal,
)

from display.animation.characters.tron import (  # noqa: F401
    TronReveal,
)

from display.animation.characters.walle import (  # noqa: F401
    WallEReveal,
    WallESideReveal,
)

# time and debug are the shared modules the player uses; tests patch their attributes through
# here (animation.time.sleep, animation.debug.info), which reaches every file. graphics is left
# out on purpose: patching it here wouldn't reach drawing.py, so patch animation.drawing.graphics.
import time  # noqa: F401,E402
from utils import debug  # noqa: F401,E402
