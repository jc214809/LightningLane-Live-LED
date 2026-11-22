"""The Santa train's turning wheels: where each piece's wheels are (found from the rims along its bottom row) and
every wheel position drawn over the art, including the engine's side rod."""

import math

from display.landmarks.santa_train_art import COLORS

SPIN_STEPS = 16  # wheel positions per turn: the spoke bar repeats every half turn, the rod every turn
CRANK = {True: 1.5, False: 1}  # how far the side rod swings round each driver's hub
RIM_32 = [(1, 0), (2, 0), (3, 1), (2, 2), (1, 2), (0, 1)]  # a 64x32 wheel's rim, clockwise from the top left


def wheels(piece, big):
    """[(cx, cy, r)] of a piece's wheels in its own coordinates (a centre can fall between pixels), found
    from the rims along its bottom row."""
    h, out, start = len(piece), [], None
    for c, ch in enumerate(piece[-1] + "."):
        if ch in "SW" and start is None:
            start = c
        if ch not in "SW" and start is not None:
            w = c - start
            if big and w >= 5:  # 7 wide (6 where the rim's shine is off the row), the engine's drivers 8 wide
                r = 4 if w >= 7 else 3
                out.append(((start + c - 1) / 2 + (0.5 if w == 6 else 0), h - 1 - r, r))
            elif not big and w >= 2:  # the 4x3 wheels' ".SS." bottom
                out.append(((start + c - 1) / 2, h - 2, 1.5))
            start = None
    return out


def spin_pixels(piece, big, step, engine=False):
    """{(x, y): rgb} drawn over a piece with its wheels at `step` of SPIN_STEPS turned clockwise. 64x64: a spoke
    bar through each hub, only on the wheel's dark inside (its rim and shine stay put); 64x32: one rim pixel
    lit white. The engine's side rod joins its drivers through cranks at the same angle."""
    phase = 2 * math.pi * step / SPIN_STEPS
    hub, rim, shine = COLORS["Y"], COLORS["S"], COLORS["W"]
    out, found = {}, wheels(piece, big)
    for cx, cy, r in found:
        if big:
            for s in range(-r + 1, r):
                x, y = round(cx + s * math.cos(phase) - 0.01), round(cy + s * math.sin(phase))
                if piece[y][x] == "k":
                    out[(x, y)] = rim
        else:
            lit = step * len(RIM_32) // SPIN_STEPS
            for i, (dx, dy) in enumerate(RIM_32):
                out[(int(cx - 1.5) + dx, int(cy - 1) + dy)] = shine if i == lit else rim
        out[(round(cx - 0.01), round(cy))] = hub
    if engine:
        crank = CRANK[big]
        dx, dy = crank * math.cos(phase), crank * math.sin(phase) if big else 0
        y = round(found[0][1] + dy)
        for x in range(round(found[0][0] + dx), round(found[-1][0] + dx) + 1):
            out[(x, y)] = COLORS["R"]
        for cx, _, _ in found:
            out[(round(cx + dx), y)] = hub
    return out
