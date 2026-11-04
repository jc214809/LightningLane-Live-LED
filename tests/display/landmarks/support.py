"""Helpers the landmark tests share."""

import display.landmarks as landmarks


def _scene_s(cls):
    """Scene time a landmark gets: its screen minus the sweep, and minus the wipe unless it plays under it."""
    import display.animation as animation
    wipe = 0 if cls.PLAYS_UNDER_WIPE else animation.TRANSITIONS["wipe"].duration
    return cls.SCREEN_S - animation.COVER_S - wipe


def _pinned(motion):
    return type(f"{motion}Pumpkin", (landmarks.FriendlyJackOLanternLandmark,), {"MOTION": motion})


TITLE_CHAR_W = 4  # the 4x6 landmark font both boards use
