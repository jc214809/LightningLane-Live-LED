"""The Santa train's riders: what each does at a moment (bob in its seat, blink, wave, wag, pant) and the art that
shows it, the poses laid over the rider's chart (a rider's pose is its art with the changes written over it)."""

from display.landmarks.santa_train_art import SANTA_WAVE_64, SANTA_WAVE_AT

BOB_PX = {True: 15, False: 9}  # px travelled per bob: about 3 a second at cruising speed
BOB_DOWN = 0.35  # the share of each bob a rider spends sunk 1px into the car
BOB_STAGGER = 0.37  # each car a little out of step with the one ahead
BLINK_S, BLINK_GAP = 0.15, (2.0, 4.0)  # eyes shut this long, this often (s)
WAVE_HZ = 6  # glove positions a second
MICKEY_WAVE_S = (2.0, 1.0)  # waving, then resting
WAG_HZ = 8  # tail positions a second: left, middle, right, middle
PANT_HZ = 6  # tongue tip out, in
PANT_TONGUE = {True: {(22, 34): "v", (23, 34): "v"}, False: {(7, 15): "v"}}  # Pluto's tongue tip, out


def blink_times(rng, until_s):
    """When a rider's eyes shut, in scene seconds up to `until_s`: the first soon, then every BLINK_GAP s."""
    blinks, at = [], rng.uniform(0.3, BLINK_GAP[0])
    while at < until_s:
        blinks.append(at)
        at += rng.uniform(*BLINK_GAP)
    return blinks


def rider_state(kind, big, t, travelled, order, blinks):
    """What a rider is doing at scene time t, as a hashable (bob, blink, wave, wag, pant): order counts cars from
    the engine, for the bob's ripple."""
    bob = kind in RIM_EDGE and (travelled / BOB_PX[big] + order * BOB_STAGGER) % 1 < BOB_DOWN
    blink = any(at <= t < at + BLINK_S for at in blinks) if (big or kind != "santa") else False
    wave = None
    if big and kind == "santa":
        wave = int(t * WAVE_HZ) % 2
    elif big and kind == "mickey" and t % sum(MICKEY_WAVE_S) < MICKEY_WAVE_S[0]:
        wave = int(t * WAVE_HZ) % 2
    wag = [0, 1, 2, 1][int(t * WAG_HZ) % 4] if kind == "pluto" else None
    pant = int(t * PANT_HZ) % 2 == 0 if kind == "pluto" else None
    return bob, blink, wave, wag, pant




def rider_patch(piece, kind, big, state):
    """The rider's art in `state` (rider_state's): the wave, blink, tail and tongue laid over it, then the bob."""
    rows = [list(row) for row in piece]
    for changes in _overlays(piece, kind, big, state):
        _lay(rows, changes)
    art = ["".join(r) for r in rows]
    return _sunk(art, kind, big) if state[0] else art


def _overlays(piece, kind, big, state):
    """The {(x, y): ch} changes a state lays over a rider's art, in the order they go down: wave, blink, tail, tongue."""
    _, blink, wave, wag, pant = state
    if wave is not None:
        yield santa_wave(wave) if kind == "santa" else mickey_wave(piece, wave)
    if blink:
        yield BLINKS[big, kind](piece)
    if wag is not None:
        yield pluto_tail(piece, big, wag)
    if pant:
        yield PANT_TONGUE[big]


def _lay(rows, changes):
    """Write `changes` into the mutable `rows`, leaving out what falls off them."""
    for (x, y), ch in changes.items():
        if 0 <= y < len(rows) and 0 <= x < len(rows[0]):
            rows[y][x] = ch


def _sunk(art, kind, big):
    """`art` sunk 1px into the car: everything above its rim moves down, the car's raised ends stay."""
    rim, edge = RIM_ROW[big], RIM_EDGE[kind]
    sunk = [list(r) for r in art]
    for y in range(rim - 1, 0, -1):
        for x in range(len(art[0])):
            if not (y == rim - 1 and art[y][x] == edge):
                sunk[y][x] = art[y - 1][x]
    sunk[0] = ["."] * len(art[0])
    return ["".join(r) for r in sunk]


def santa_wave(frame):
    """Santa's cab with his arm at wave frame 0 or 1, as changes over the engine's art."""
    x0, y0 = SANTA_WAVE_AT
    return {(x0 + x, y0 + y): ch for y, row in enumerate(SANTA_WAVE_64[frame]) for x, ch in enumerate(row)}


def _where(piece, ch, x0, x1, y0, y1):
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if piece[y][x] == ch]


def _line(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(round(max(abs(x1 - x0), abs(y1 - y0))), 1)
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def _outline_sky(piece, changes, body):
    """Outline `body` in K wherever it meets sky in the piece, without covering anything already changed."""
    for x, y in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if (q not in body and q not in changes and 0 <= q[1] < len(piece) and 0 <= q[0] < len(piece[0])
                        and piece[q[1]][q[0]] == "."):
                    changes[q] = "K"


# Eyes shut: {(x, y): ch} over each rider's art.
BLINKS = {
    (True, "mickey"): lambda p: {**{q: "a" for q in _where(p, "W", 13, 19, 21, 24) + _where(p, "K", 15, 16, 21, 24)},
                                 **{q: "K" for q in _where(p, "W", 13, 19, 25, 25)}},  # skin lids, a lash line
    (True, "donald"): lambda p: {**{q: "W" for q in _where(p, "K", 8, 12, 17, 23) + _where(p, "K", 15, 19, 17, 23)},
                                 **{(x, 22): "K" for x in [*range(7, 13), *range(14, 20)]}},  # white lids, lash lines
    (True, "goofy"): lambda p: {q: "K" for q in _where(p, "W", 16, 24, 20, 24)},
    (True, "pluto"): lambda p: {**{q: "y" for q in _where(p, "W", 17, 25, 18, 21)},
                                **{q: "K" for q in _where(p, "W", 17, 25, 22, 23)}, **{(x, 21): "K" for x in range(18, 25)}},
    (True, "santa"): lambda p: {q: "d" for q in _where(p, "k", 9, 15, 32, 32)},
    (False, "mickey"): lambda p: {(6, 13): "i", (8, 13): "i"},
    (False, "donald"): lambda p: {**{q: "m" for q in _where(p, "K", 5, 9, 13, 14)}, **{(x, 13): "K" for x in (5, 6, 8, 9)}},
    (False, "goofy"): lambda p: {q: "K" for q in _where(p, "W", 4, 10, 11, 12)},
    (False, "pluto"): lambda p: {**{q: "o" for q in _where(p, "K", 6, 8, 10, 10) + _where(p, "W", 5, 9, 10, 11)},
                                 **{(x, 11): "K" for x in (5, 6, 8, 9)}},
}
RIM_ROW = {True: 41, False: 21}  # the first row of the cars' sides: a bob moves only what's above it
RIM_EDGE = {"mickey": "G", "donald": "R", "goofy": "R", "pluto": "R"}  # the colour of each car's raised ends
# Pluto's 64x64 tail, base (on his back) last; it wags by shearing, so it keeps its curl.
PLUTO_TAIL_64 = [(6, 26), (6, 27), (6, 28), (6, 29), (7, 29), (7, 30), (8, 30), (8, 31), (8, 32), (9, 32), (9, 33),
                 (9, 34), (8, 35), (9, 35), (7, 36), (8, 36)]
PLUTO_TAIL_32 = [{(3, 19): "o", (2, 18): "o", (2, 17): "o"}, {(3, 19): "o", (3, 18): "o", (3, 17): "o"},
                 {(3, 19): "o", (2, 18): "o", (1, 18): "o"}]  # his bead head has none: a short one on his car
MICKEY_GLOVE_OFF = {(8, 39): ".", (9, 39): "K", (10, 39): "x", (11, 39): "X", (8, 40): "G", (9, 40): "K",
                    (10, 40): "x", (11, 40): "X", (12, 40): "X"}  # his back glove up off the rim: sweater and rim show


def pluto_tail(piece, big, wag):
    """Pluto's tail at wag 0, 1 or 2 (left, middle, right)."""
    if not big:
        return PLUTO_TAIL_32[wag]
    swing = (wag - 1) * 3  # px at the tip
    out = {q: "." for q in PLUTO_TAIL_64}
    top = min(y for _, y in PLUTO_TAIL_64)
    pts = [(x + swing * (36 - y) / (36 - top), y) for x, y in PLUTO_TAIL_64]
    for a, b in zip(pts, pts[1:]):
        for q in _line(a, b):
            out[q] = "K"
    return out


def mickey_wave(piece, frame):
    """Mickey's back glove up beside his cheek on a green sleeve from his shoulder, rocking 1px (frame 0 or 1);
    the sleeve stays put."""
    out = dict(MICKEY_GLOVE_OFF)
    gx = 2 - frame
    glove = {(gx + dx, 29 + dy) for dx in range(3) for dy in range(3)}
    sleeve = set()
    for x, y in _line((9, 36), (3, 32)):
        sleeve |= {(x + dx, y + dy) for dx in (0, 1, 2) for dy in (0, 1)}
    sleeve -= glove
    out.update({q: "W" for q in glove})
    _outline_sky(piece, out, sleeve | glove)
    out.update({q: "X" if (q[0] - 1, q[1]) in sleeve else "x" for q in sleeve})
    return out
