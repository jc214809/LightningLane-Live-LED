"""
Merida's poses for the synced show's Touch the Sky (actors/merida.py plays them): the archer's art
(display/animation/characters/archer.py) taken apart into layers (skirt, body, bow arm, bow), patched for
the poses the art doesn't draw, and turned with pixels.rotate_cells. Turning sprites is far too slow for a
Pi Zero to do live, so tools/build_merida_poses.py bakes every frame the scene needs into
merida_poses.json; build(key) makes one, frame_key(e) says which one a moment in the scene shows. A test
fails until the baked file matches build(). All coordinates are her art's (31x57, feet on row 56).

The scene, in seconds from its start (settled with the user from mocks, 2026-10-19):
- until WIND: says her line, holding her bow by its top limb, its foot planted at her side, string out
  (the bow mirrored), her other hand on her hip; her face a column wider each side, so a 5 px mouth fits.
- WIND to THROW: winds up; THROW to CATCH: the bow in the air, rising APEX and spinning SPIN degrees
  (landing string toward her, the art's way round), easing upright before her hand; CATCH to DIP: her
  hand dips with its weight.
- DRAW: nocks and draws (the art as drawn); LEAN_AT for LEAN_S: leans back to AIM degrees as a curve
  (her waist turns TORSO_SHARE of it, her chest, arms and bow the rest, her head HEAD_BACK of it back
  toward level, her hips forward up to HIP_PX with her skirt sheared after them), a touch past and back.
- RELEASE ("touch"): the string snaps and rings (the archer's), her hand flies back past her ear
  (FOLLOW_PX in FOLLOW_S), drops through one in-between frame at DROP_AT and hangs at her side from
  DROP_AT + DROP_S; she eases out of the lean to AIM - RELAX.
"""
import json
import math
import os

from display.animation.characters.archer import ArcherReveal as Archer
from display.motion import smooth
from display.pixels import rotate_cells, turn

BAKED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merida_poses.json")

# The archer's palette, and what the poses add: the string (S), the nocked arrow (a shaft, f fletching,
# t tip; the shaft edged K so it shows over her hair), and the inside of her open mouth (X).
COLORS = dict(Archer.COLORS, S=Archer.STRING_RGB, a=Archer.SHAFT_RGB, f=Archer.FLETCH_RGB, t=Archer.TIP_RGB,
              X=(110, 35, 40))

ART = Archer.ART
H = len(ART)
GROUND, WAIST = H - 1, 33
# The bow's cells, per art row (inclusive), and her bow arm's (from her shoulder to her hand).
BOW = {0: (18, 18), 1: (17, 19), 2: (17, 19), 3: (17, 20), 4: (18, 22), 5: (18, 23), 6: (20, 24), 7: (22, 25),
       8: (23, 25), 9: (23, 26), 10: (24, 26), 11: (24, 27), 12: (25, 27), 13: (25, 28), 14: (26, 28),
       15: (26, 28), 16: (26, 29), 17: (27, 29), 18: (27, 28), 19: (27, 28), 20: (27, 28), 21: (27, 29),
       22: (27, 29), 23: (27, 30), 24: (27, 30), 25: (26, 30), 26: (25, 29), 27: (27, 28), 28: (27, 29),
       29: (26, 29), 30: (26, 28), 31: (26, 28), 32: (25, 28), 33: (25, 27), 34: (24, 27), 35: (24, 26),
       36: (23, 26), 37: (23, 25), 38: (22, 25), 39: (20, 24), 40: (19, 23), 41: (18, 22), 42: (17, 20),
       43: (17, 19), 44: (17, 19)}
ARM = {24: (13, 26), 25: (14, 25), 26: (14, 24), 27: (20, 24)}
REST_ARM_ROWS = {**ARM, 24: (17, 26), 25: (16, 25)}  # past her wider chin and her bodice beside it
SHOULDER = (15.5, 25.5)      # her bow arm's
HAND = (28.5, 24.5)          # her bow hand, on the grip
DRAW_SHOULDER = (8.5, 25.0)  # her drawing arm's
PIVOT = (12.5, 33.5)         # her waist
NECK, CHEST = (12.5, 24.0), (12.5, 27.5)
BOW_CENTRE = (18.5, 22.5)
MIRROR = 36  # the bow string-out: mirrored about x = 18 (a cell x goes to MIRROR - 1 - x, a point to MIRROR - x)

# Her other arm where the art has it drawing (rows 23-35, cols 0-15): on her hip while she talks; hanging
# relaxed, hand by her quiver, after the shot. Her bodice fills in under her chin.
ARM_PATCHES = {
    "hip": [
        "..KROORRRKFFmmFK",
        "..KRORKKKKKFFFFK",
        "...KKYTTTyKKKKKD",
        "..KYTTDDDYDDDDDD",
        ".KTTDDDDKyDDDDDD",
        "KTDDDDKKKNNNyyND",
        "KTDDDKNKNNNNNNNN",
        "KDDDKNNNKNNNNNNN",
        ".KDDDKNNKNNNNNNN",
        "..KyDDKKKNNNNNNK",
        "...KyYFFFKDDDDPP",
        "....KKFFKKPPPPDK",
        "....KK.KPPDDDDDK",
    ],
    "relaxed": [
        "..KROORRRKFFmmFK",
        "..KRORKKKKKFFFFK",
        "...KKYTTTyKKKKKD",
        "..KYTTDDDYDDDDDD",
        "..KTDDDDDyDDDDDD",
        ".KTDDDDDKNNNyyND",
        ".KTDDDDKNNNNNNNN",
        ".KDDDDKKKNNNNNNN",
        "..KDDDK.KNNNNNNN",
        "..KyYyK..KNNNNNK",
        "...KFFK..KDDDDPP",
        "...KFFK.KKPPPPDK",
        "....KK.KPPDDDDDK",
    ],
}
# Her face a column wider each side (cols 8-16, centred on her nose at col 12): rows 19-22 in every pose;
# her chin (rows 23-26) only while her drawing hand is off it.
FACE_ROWS = {
    19: {9: "F", 16: "F"},
    20: {9: "F", 16: "F"},
    21: {8: "h", 9: "F", 16: "F", 17: "K"},
    22: {8: "h", 9: "F", 16: "F", 17: "K"},
}
CHIN_ROWS = {
    23: {8: "K", 9: "F", 10: "F", 11: "F", 12: "F", 13: "F", 14: "F", 15: "F", 16: "F", 17: "K"},
    24: {9: "K", 10: "F", 11: "F", 12: "F", 13: "F", 14: "F", 15: "K", 16: "K"},
    25: {10: "K", 11: "F", 12: "F", 13: "F", 14: "K", 15: "D"},
    26: {11: "K", 12: "K", 13: "K"},
}
# Her mouth by the score's shape: 0 a closed smile, 1 half open, 2 open.
MOUTHS = {
    0: {(11, 23): "m", (12, 23): "m", (13, 23): "m", (10, 22): "m", (14, 22): "m"},
    1: {(11, 23): "X", (12, 23): "X", (13, 23): "X"},
    2: {(10, 23): "X", (11, 23): "X", (12, 23): "X", (13, 23): "X", (14, 23): "X",
        (11, 24): "X", (12, 24): "X", (13, 24): "X"},
}
# Her skirt where the bow's lower limb covered it (rows 40-44): its edge runs on from row 39's to row 45's.
SKIRT_BEHIND_BOW = {
    (19, 40): "K",
    (18, 41): "D", (19, 41): "K",
    (17, 42): "D", (18, 42): "D", (19, 42): "D", (20, 42): "K",
    (17, 43): "D", (18, 43): "D", (19, 43): "N",
    (17, 44): "D", (18, 44): "D", (19, 44): "N",
}

# Her bow hand as a fist (the art's is two 1px fingers round the grip, black between them and her cuff, so
# off the grip it read as a gap and a claw): its wrist meets her cuff (col 25); the bow passes behind it.
FIST = {
    21: {27: "K", 28: "K", 29: "K"},
    22: {26: "K", 27: "F", 28: "F", 29: "F", 30: "K"},
    23: {26: "K", 27: "F", 28: "F", 29: "F", 30: "K"},
    24: {26: "F", 27: "F", 28: "F", 29: "F", 30: "K"},
    25: {26: "F", 27: "h", 28: "h", 29: "h", 30: "K"},
    26: {26: "K", 27: "K", 28: "K", 29: "K"},
}
# Her drawing hand's wrist, at her chin: skin where the art had an outline between it and her cuff.
DRAW_WRIST = {24: {10: "F"}, 25: {10: "F"}, 26: {10: "F"}}

# The scene (seconds from its start).
WIND, THROW, CATCH, DIP, DRAW = 24.0, 24.3, 25.1, 25.25, 25.4
LEAN_AT, LEAN_S, AIM = 25.9, 0.8, 20.0
RELEASE = 27.36  # 295.36: "touch"
FOLLOW_S, FOLLOW_PX = 0.1, (-3, -2)
DROP_AT, DROP_S = 0.3, 0.12
LOOSE_S = 0.6     # baked frame by frame this long after the release (the string rings, her arm drops)
RELAX = 8.0
TORSO_SHARE, HEAD_BACK, HIP_PX = 0.35, 0.3, 1.5
REST_HOLD = (23.5, 8.5)  # where she holds the planted bow's top limb (bow coords)
REST_ARM, REST_LEAN = 10.0, 9.2  # her bow arm raised, the bow leaning in toward her, its foot on the ground
WIND_ARM, WIND_LEAN = 30.0, -10.0
SPIN, APEX = 550.0, 12.0  # from WIND_LEAN to 540: a turn and a half, so the string-out bow lands string in
FPS = 30  # the moving parts' baked frame rate
TOSS_FRAMES = int(math.ceil((DIP - WIND) * FPS))


def _lerp(a, b, k):
    return a + (b - a) * k


def _in(ranges, x, y):
    r = ranges.get(y)
    return r is not None and r[0] <= x <= r[1]


def _shift(cells, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in cells.items()}


def _mirror(bow):
    return {(MIRROR - 1 - x, y): k for (x, y), k in bow.items()}


def tension(s):
    """The string's pull s seconds after the release (the archer's): it swings past straight and dies away."""
    return math.cos(2 * math.pi * Archer.RING_HZ * s) * math.exp(-s / Archer.RING_DECAY_S)


def _drawing_arm(cells):
    """Her drawing arm and the hand at her chin, in the drawn pose."""
    return {p for p in cells if 23 <= p[1] <= 27
            and (p[0] <= 9 or (p[0] <= 14 and p[1] >= 24) or p in ((10, 23), (11, 23)))}


def _patch(cells, rows, top=23):
    for dy, row in enumerate(rows):
        for x, k in enumerate(row):
            if k == ".":
                cells.pop((x, top + dy), None)
            else:
                cells[(x, top + dy)] = k


def _apply(cells, rows):
    for y, row in rows.items():
        for x, k in row.items():
            cells[(x, y)] = k


def split(pose, release=None):
    """
    Her layers {(x, y): kind} for 'rest' (her bow arm free, her other hand on her hip) or 'draw' (the art as
    drawn), release seconds after she lets go: (skirt, body, bow arm, bow and string).
    """
    g = {(x, y): k for y, row in enumerate(ART) for x, k in enumerate(row) if k != "."}
    if pose == "draw":
        _apply(g, DRAW_WRIST)
    if pose == "rest":
        _patch(g, ARM_PATCHES["hip"])
        for x in range(2):  # the drawing arm's far end is gone
            for y in range(23, 28):
                g.pop((x, y), None)
    elif release is not None and release >= DROP_AT + DROP_S:  # her drawing arm hangs at her side
        for p in _drawing_arm(g):
            g.pop(p)
        _patch(g, ARM_PATCHES["relaxed"])
        for x in range(2):
            for y in range(23, 28):
                g.pop((x, y), None)
        _apply(g, CHIN_ROWS)
        g.update(MOUTHS[0])
    elif release is not None:
        r = smooth(release / FOLLOW_S)
        dx, dy = int(round(FOLLOW_PX[0] * r)), int(round(FOLLOW_PX[1] * r))
        if dx or dy:  # her hand flies back past her ear, uncovering her chin and her shoulder
            hand = {p: g.pop(p) for p in _drawing_arm(g)}
            for dy_row, row in enumerate(ARM_PATCHES["relaxed"][:5]):
                for x, k in enumerate(row):
                    if k != "." and (x, 23 + dy_row) not in g:
                        g[(x, 23 + dy_row)] = k
            _apply(g, CHIN_ROWS)
            g.update(MOUTHS[0])
            hand = _shift(hand, dx, dy)
            if release >= DROP_AT:  # on its way down
                hand = rotate_cells(hand, (DRAW_SHOULDER[0] + dx, DRAW_SHOULDER[1] + dy), 55)
            g.update(hand)
    rows = dict(FACE_ROWS)
    if pose == "rest":
        rows.update(CHIN_ROWS)
    _apply(g, rows)
    lower, body, arm, bow = {}, {}, {}, {}
    arm_rows = REST_ARM_ROWS if pose == "rest" else ARM
    for (x, y), k in g.items():
        if _in(BOW, x, y):
            bow[(x, y)] = k
        elif _in(arm_rows, x, y):
            arm[(x, y)] = k
        elif y >= WAIST:
            lower[(x, y)] = k
        else:
            body[(x, y)] = k
    lower.update(SKIRT_BEHIND_BOW)
    # Her bow hand (a fist) goes with her arm; the grip it covered is wood.
    for p in [p for p in bow if 21 <= p[1] <= 26 and p[0] >= 26]:
        bow.pop(p)
    for p in [p for p in arm if 21 <= p[1] <= 26 and p[0] >= 26]:
        arm.pop(p)
    for y, row in FIST.items():
        for x, k in row.items():
            arm[(x, y)] = k
    for y in range(18, 28):
        bow[(27, y)], bow[(28, y)], bow[(29, y)] = "K", "P", "K"
    # The string: a V at full draw, ringing after the release, straight at rest.
    pull = 0.0 if pose == "rest" else 1.0 if release is None else tension(release)
    for row, col in Archer.STRING_COLS.items():
        x = Archer.TIP_COL - int(round(pull * (Archer.TIP_COL - col)))
        if pose == "draw" and release is None and x == Archer.NOCK[0] and 24 <= row <= 26:
            continue  # behind her hand
        bow[(x, row)] = "S"
    return lower, body, arm, bow


def _fill_behind_arm(body, arm):
    """Where her bow arm swings away: her bodice by her shoulder, her hair further out."""
    for (x, y) in arm:
        if (x, y) in body:
            continue
        if x <= 17:
            body[(x, y)] = "D"
        elif x == 18:
            body[(x, y)] = "K"
        elif x <= 26:
            body[(x, y)] = "O" if (x + 2 * y) % 3 == 0 else "R"


def _outline(cells, blocked):
    """Outline cells' open edges, never over a cell another layer fills (`blocked`)."""
    out = dict(cells)
    for (x, y), k in cells.items():
        if k in "KS":
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in cells and q not in blocked:
                out[q] = "K"
    return out


def _rest_layers(mouth):
    lower, body, arm, bow = split("rest")
    _fill_behind_arm(body, arm)
    body.update(MOUTHS[mouth])
    return _outline(lower, body), _outline(body, lower), arm, bow


def held(arm_up, bow_angle, hold, mirrored, mouth=0):
    """Her bow arm raised arm_up degrees, the bow (mirrored: string out) held at `hold` (bow coords) in her
    hand and turned bow_angle about it."""
    lower, body, arm, bow = _rest_layers(mouth)
    if mirrored:
        bow, hold = _mirror(bow), (MIRROR - hold[0], hold[1])
    hand = turn(HAND, SHOULDER, arm_up)
    bow = _shift(rotate_cells(bow, hold, bow_angle), int(round(hand[0] - hold[0])), int(round(hand[1] - hold[1])))
    g = dict(lower)
    g.update(body)
    g.update(bow)
    g.update(rotate_cells(arm, SHOULDER, arm_up))
    return g


def held_centre(arm_up, bow_angle, hold, mirrored=True):
    """Where the bow's centre is while held (held()'s placement), so the toss starts where she lets go."""
    hand = turn(HAND, SHOULDER, arm_up)
    c = BOW_CENTRE
    if mirrored:
        hold, c = (MIRROR - hold[0], hold[1]), (MIRROR - c[0], c[1])
    cx, cy = turn(c, hold, bow_angle)
    return cx - hold[0] + hand[0], cy - hold[1] + hand[1]


def airborne(arm_up, centre, angle):
    """The bow (string out) in the air, its centre at `centre` turned angle; her arm wherever it is."""
    lower, body, arm, bow = _rest_layers(0)
    c = (MIRROR - BOW_CENTRE[0], BOW_CENTRE[1])
    bow = _shift(rotate_cells(_mirror(bow), c, angle), int(round(centre[0] - c[0])), int(round(centre[1] - c[1])))
    g = dict(lower)
    g.update(body)
    g.update(bow)
    g.update(rotate_cells(arm, SHOULDER, arm_up))
    return g


def chest_transform(phi):
    """Where a point on her drawn pose goes with her leant back phi degrees (bend()'s chest, arms and bow)."""
    hip = HIP_PX * phi / AIM
    a = TORSO_SHARE * phi
    pivot = (PIVOT[0] + hip, PIVOT[1])

    def torso(p):
        return turn((p[0] + hip, p[1]), pivot, a)

    def chest(p):
        return turn(torso(p), torso(CHEST), phi - a)

    return torso, chest


def bend(phi, release=None):
    """The drawn pose leant back phi degrees as a curve (see the module), release seconds after she lets go
    (None: the arrow still on the string)."""
    hip = HIP_PX * phi / AIM
    lower, body, arm, bow = split("draw", release)
    head, chest, torso = {}, {}, {}
    for (x, y), k in body.items():
        if y <= 23 and not (y == 23 and x <= 9):
            head[(x, y)] = k
        elif y <= 27 or x >= 19:
            chest[(x, y)] = k
        else:
            torso[(x, y)] = k
    a, h = TORSO_SHARE * phi, HEAD_BACK * phi
    torso_t, chest_t = chest_transform(phi)

    def head_t(p):
        return turn(chest_t(p), chest_t(NECK), -h)

    def place(layer, t, angle):
        o = t(PIVOT)
        return rotate_cells(layer, PIVOT, angle, offset=(o[0] - PIVOT[0], o[1] - PIVOT[1]))

    g = {}
    for (x, y), k in lower.items():  # her skirt follows her hips, sheared to her planted feet
        g[(x + int(round(hip * (GROUND - y) / (GROUND - WAIST))), y)] = k
    g.update(place(torso, torso_t, a))
    g.update(place(chest, chest_t, phi))
    g.update(place(head, head_t, phi - h))
    g.update(place(bow, chest_t, phi))
    g.update(place(arm, chest_t, phi))
    if release is None:
        g.update(nocked_arrow(chest_t((Archer.NOCK[0] + 0.5, Archer.NOCK[1] + 0.5)), phi, g))
    return g


def arrow_cells(tail, phi, length=Archer.ARROW_LEN):
    """The arrow's cells from its tail along the aim: [((x, y), i)], i counting from the tail."""
    ux, uy = math.cos(math.radians(phi)), -math.sin(math.radians(phi))
    return [((int(math.floor(tail[0] + ux * i)), int(math.floor(tail[1] + uy * i))), i) for i in range(length)]


EDGED = set("ORP")  # her hair: the nocked arrow's shaft gets a dark edge over it (and over open sky)


def nocked_arrow(nock, phi, under):
    """The drawn arrow over her (only her bow hand, the art's HAND_COLS along it, covers it): red fletching,
    a pale shaft, a white head. Its shaft is edged dark each side where it crosses her hair or open sky
    (`under`, her cells), so it shows; never over her sleeve or skin."""
    out = {}
    for (x, y), i in arrow_cells(nock, phi):
        if Archer.HAND_COLS[0] - Archer.NOCK[0] <= i <= Archer.HAND_COLS[1] - Archer.NOCK[0]:
            continue
        out[(x, y)] = "t" if i == Archer.ARROW_LEN - 1 else "f" if i < 3 else "a"
        if 0 < i < 3:
            out[(x, y - 1)] = out[(x, y + 1)] = "f"
    for (x, y), k in list(out.items()):
        if k == "a":
            for q in ((x, y - 1), (x, y + 1)):
                if q not in out and (q not in under or under[q] in EDGED):
                    out[q] = "K"
    return out


def fill_small_holes(cells, most=4):
    """Fill each enclosed gap of up to `most` cells (a seam between layers turned by different angles) with
    its neighbours' commonest colour; bigger enclosed spaces (inside the bow) stay open."""
    xs, ys = [p[0] for p in cells], [p[1] for p in cells]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    seen, out = set(), dict(cells)
    for sx in range(x0, x1 + 1):
        for sy in range(y0, y1 + 1):
            if (sx, sy) in cells or (sx, sy) in seen:
                continue
            gap, todo, edge = [], [(sx, sy)], False
            while todo:
                p = todo.pop()
                if p in seen or p in cells:
                    continue
                if not (x0 < p[0] < x1 and y0 < p[1] < y1):
                    edge = True
                    continue
                seen.add(p)
                gap.append(p)
                x, y = p
                todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if edge or len(gap) > most:
                continue
            for x, y in gap:
                near = [cells[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in cells]
                kinds = [k for k in near if k not in "KS"] or near
                out[(x, y)] = max(sorted(set(kinds)), key=kinds.count)
    return out


def aim_tip(e):
    """Her lean e seconds into the scene while she aims: up to AIM, a touch past and back."""
    return (AIM + 1.0) * smooth((e - LEAN_AT) / LEAN_S) - 1.0 * smooth((e - LEAN_AT - 0.7) / 0.4)


def after_tip(s):
    """Her lean s seconds after the release: holds her form a moment, then eases out by RELAX."""
    return AIM - RELAX * smooth((s - 0.3) / 0.8)


def frame_key(e, mouth=None):
    """The baked frame e seconds into the scene shows (mouth: the score's shape while she talks)."""
    if e < WIND:
        return "talk/%d" % (mouth or 0)
    if e < DIP:
        return "toss/%d" % min(int((e - WIND) * FPS), TOSS_FRAMES - 1)
    if e < DRAW:
        return "held"
    if e < RELEASE:
        return "aim/%d" % int(round(aim_tip(e)))
    s = e - RELEASE
    if s < LOOSE_S:
        return "loose/%d" % int(s * FPS)
    return "after/%d" % int(round(after_tip(s)))


def frame_keys():
    """Every frame the scene can show, in order."""
    return (["talk/%d" % m for m in MOUTHS] + ["toss/%d" % i for i in range(TOSS_FRAMES)] + ["held"]
            + ["aim/%d" % d for d in range(int(AIM) + 2)] + ["loose/%d" % i for i in range(int(LOOSE_S * FPS))]
            + ["after/%d" % d for d in range(int(AIM - RELAX), int(AIM) + 1)])


def _toss(e):
    """The bow in her hand or in the air e seconds into the scene, WIND <= e < DIP."""
    if e < THROW:  # winds up: the bow swings off the ground, her arm rising
        k = smooth((e - WIND) / (THROW - WIND))
        return held(_lerp(REST_ARM, WIND_ARM, k), _lerp(REST_LEAN, WIND_LEAN, k), REST_HOLD, True)
    if e < CATCH:  # in the air, spinning; her arm follows through, then comes down to catch it
        k = (e - THROW) / (CATCH - THROW)
        x0, y0 = held_centre(WIND_ARM, WIND_LEAN, REST_HOLD)
        x1, y1 = BOW_CENTRE  # caught where she holds it drawn (the spin has turned it the art's way round)
        centre = (_lerp(x0, x1, smooth(k) ** 2), _lerp(y0, y1, k) - APEX * 4 * k * (1 - k))
        arm = _lerp(WIND_ARM, 45, smooth(k / 0.3)) if k < 0.3 else _lerp(45, 0, smooth((k - 0.3) / 0.6))
        return airborne(arm, centre, WIND_LEAN + SPIN * (1 - (1 - min(1.0, k / 0.75)) ** 2))
    k = (e - CATCH) / (DIP - CATCH)  # caught: its weight dips her hand a touch
    return held(-6 * math.sin(math.pi * k), 0, HAND, False)


def build(key):
    """One baked frame's cells {(x, y): kind}, her art's coordinates."""
    kind, _, n = key.partition("/")
    if kind == "talk":
        g = held(REST_ARM, REST_LEAN, REST_HOLD, True, mouth=int(n))
    elif kind == "toss":
        g = _toss(WIND + int(n) / FPS)
    elif kind == "held":
        g = held(0, 0, HAND, False)
    elif kind == "aim":
        g = bend(float(n))
    elif kind == "loose":
        s = int(n) / FPS
        g = bend(after_tip(s), release=s)
    elif kind == "after":
        g = bend(float(n), release=LOOSE_S + 10.0)
    else:
        raise KeyError(key)
    return fill_small_holes(g)


def pack(cells):
    """Cells as {"x", "y", "rows"}: the top-left and rows of kinds ('.' empty, trailing ones dropped)."""
    xs, ys = [p[0] for p in cells], [p[1] for p in cells]
    x0, y0 = min(xs), min(ys)
    rows = ["".join(cells.get((x, y), ".") for x in range(x0, max(xs) + 1)).rstrip(".")
            for y in range(y0, max(ys) + 1)]
    return {"x": x0, "y": y0, "rows": rows}


def bake():
    """Every frame packed, for merida_poses.json."""
    return {key: pack(build(key)) for key in frame_keys()}


def load():
    """The baked frames, or {} without the file (the actor builds what's missing)."""
    try:
        with open(BAKED) as f:
            return json.load(f)["frames"]
    except (OSError, ValueError, KeyError):
        return {}
