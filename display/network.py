from updater.shared import network_issues

# A red square with a white "!" in the bottom-right corner, after the network badge
# on mlb-led-scoreboard: small enough to leave the wait readable, bright enough to
# spot from across the room. The same size on both boards.
BADGE_ART = [
    "RRRRRRR",
    "RRRWRRR",
    "RRRWRRR",
    "RRRWRRR",
    "RRRRRRR",
    "RRRWRRR",
    "RRRRRRR",
]
COLORS = {"R": (255, 0, 0), "W": (255, 255, 255)}


def draw_network_badge(canvas):
    x0 = canvas.width - len(BADGE_ART[0])
    y0 = canvas.height - len(BADGE_ART)
    for row, line in enumerate(BADGE_ART):
        for col, key in enumerate(line):
            canvas.SetPixel(x0 + col, y0 + row, *COLORS[key])


def draw_if_offline(canvas):
    if network_issues():
        draw_network_badge(canvas)
