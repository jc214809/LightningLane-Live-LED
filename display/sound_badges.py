from utils.sound import CANT_PLAY, NO_MUSIC, current_problem

# Bottom-left, opposite the network "!" (display/network.py), so both can show at once: a red
# square with a white icon, like that one, a pixel bigger all round to fit the icon. A red gap keeps
# the X off the icon. The same size on both boards.
# A music note with an X: sound is on, but a show's music isn't in sounds/.
NO_MUSIC_ART = [
    "RRRRRRRRR",
    "RRRWWWRRR",
    "RRRWRWWRR",
    "RRRWRRRRR",
    "RRWWRRRRR",
    "RWWWRWRWR",
    "RRWRRRWRR",
    "RRRRRWRWR",
    "RRRRRRRRR",
]
# A speaker with an X: the music is there, but there's no player or sound card to play it.
CANT_PLAY_ART = [
    "RRRRRRRRR",
    "RRRWRRRRR",
    "RRWWRRRRR",
    "RWWWRWRWR",
    "RWWWRRWRR",
    "RWWWRWRWR",
    "RRWWRRRRR",
    "RRRWRRRRR",
    "RRRRRRRRR",
]
BADGES = {NO_MUSIC: NO_MUSIC_ART, CANT_PLAY: CANT_PLAY_ART}
COLORS = {"R": (255, 0, 0), "W": (255, 255, 255)}


def draw_sound_badge(canvas, art):
    y0 = canvas.height - len(art)
    for row, line in enumerate(art):
        for col, key in enumerate(line):
            canvas.SetPixel(col, y0 + row, *COLORS[key])


def draw_if_sound_problem(canvas):
    art = BADGES.get(current_problem())
    if art:
        draw_sound_badge(canvas, art)
