import math
import random

from display.animation.characters.saber import BLADES, SPARKS, burst_pixels, spark_pixels, throw_sparks
from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS
from display.motion import ease_out, progress
from display.pixels import art_pixels, put


def _keyed(keys, t):
    """The value at t along [(t, value)] keyframes, straight between them, held past either end."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return keys[-1][1]

VADER_COLORS = {
    "K": (0, 0, 0), "D": (72, 72, 80), "G": (100, 100, 108), "g": (128, 128, 136), "P": (50, 50, 58),
    "B": (152, 152, 152), "C": (127, 127, 127), "R": (202, 3, 5), "b": (3, 102, 200), "W": (246, 249, 244),
}


class _SaberDuel(CapturesScreens):
    """
    The fight every duel shares, over the old ride screen. The LEFT fighter walks in from the
    left and the RIGHT one from the right. They trade three blows (left, right, left), each
    attacker raising his blade (his fist comes up by his head: the front arm swings from the
    shoulder with the blade), stepping in and leaning into the cut onto the other's guard,
    with a spark where they hit and the defender knocked back a pixel. Then they step in and
    lock blades, sparks pouring off the crossing, until the lock bursts and throws them apart
    to the edges, blades upright, the new ride opening between them like the blades-only
    clash (saber.py).

    A matchup sets LEFT, RIGHT, COLORS and FIGHTERS. The fight plays over the old screen, so
    it opts into wants_prev.
    """

    wants_prev = True
    WALK_S, DUEL_S, LOCK_S, PUSH_S = 0.9, 1.8, 0.8, 1.0
    duration = WALK_S + DUEL_S + LOCK_S + PUSH_S
    SCALE = 1  # 1x on both boards: doubled, the two of them are wider than 64x64
    BLADES, SPARKS = BLADES, SPARKS
    LEFT, RIGHT = "", ""
    COLORS = {}
    # Per fighter, in art coordinates: the art (and, for a cape, a second frame it alternates
    # with), the anchor (the fighter's position on the board is this point; it sits 3.5 px
    # behind and below the front shoulder), the front shoulder the arm swings from, the back
    # shoulder of a free arm drawn out behind him (if he has one), the arm's length, the rows
    # above the waist that lean into a blow, the colours of the sleeve and the fist (its top row
    # and bottom row), the blade's colour, and how high he leaps into an attack (0: he doesn't).
    FIGHTERS = {}
    HILT_LEN = 2  # grey hilt pixels between the fist and the blade

    BLADE_LEN, BLADE_W = 14, 2
    STANCE, LUNGE, LOCKED = 15, 12, 12  # each anchor's distance from the centre: fighting, striking, locked
    EXCHANGE_S = DUEL_S / 3
    ATTACKERS = ("left", "right", "left")
    # One exchange, as (seconds in, elevation in degrees) keyframes: the attacker raises his
    # blade, cuts down onto the defender's guard and holds the bind a beat; the defender
    # brings his blade across, out in front, to block. A blade at rest stands at 45 degrees.
    # The cut and the guard are set so the blades cross for every fighter's reach.
    ATTACK = ((0, 45), (0.25, 85), (0.33, 35), (0.45, 35), (0.6, 45))
    GUARD = ((0, 45), (0.25, 35), (0.45, 35), (0.6, 45))
    STEP = ((0, STANCE), (0.25, STANCE), (0.33, LUNGE), (0.45, LUNGE), (0.6, STANCE))
    HIT_S = (0.33, 0.45)  # when, in an exchange, the blades are in contact
    LEAN_S = (0.25, 0.45)  # when the attacker's upper body tips into the blow
    LEAP_S = (0.05, 0.4)  # when a leaping attacker is in the air, landing just after the hit
    RECOIL_S = 0.12  # how long a defender is knocked back when a blow lands
    LOCK_ANGLE, SHIVER = 50, 3
    CAPE_S = 0.2  # a cape swings out and back this often

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.prev_px = {}
        self.scale = self.SCALE
        self.cx = (width - 1) / 2
        self.offstage = self.cx + 14  # an anchor this far from the centre has its fighter off the board
        self.names = (self.LEFT, self.RIGHT)
        self.attackers = tuple(self.LEFT if side == "left" else self.RIGHT for side in self.ATTACKERS)
        self.anchor_y = {name: height - len(f["art"]) + f["anchor"][1] for name, f in self.FIGHTERS.items()}
        hits = [self.WALK_S + i * self.EXCHANGE_S + self.HIT_S[0] for i in range(len(self.ATTACKERS))]
        lock = self.WALK_S + self.DUEL_S
        waves = [(t, *self.contact(t)) for t in hits + [lock + 0.15, lock + self.LOCK_S / 2, lock + self.LOCK_S - 0.01]]
        self.sparks = throw_sparks(self.rng, waves, 8 if height >= 64 else 6, height / 32)

    def pose(self, t):
        """{name: (anchor x, anchor y, elevation in degrees)}; the left fighter's blade points right."""
        if t < self.WALK_S:
            d = self.offstage + ease_out(t / self.WALK_S) * (self.STANCE - self.offstage)
            step = int(t * 8) % 2
            return self._at({name: (d, 45) for name in self.names},
                            {name: -(self.FIGHTERS[name].get("leap", 0) // 3 or 1) * step for name in self.names})
        t -= self.WALK_S
        if t < self.DUEL_S:
            i = int(t / self.EXCHANGE_S)
            s = t - i * self.EXCHANGE_S
            stance, lift = {}, {}
            for name in self.names:
                attacking = self.attackers[i] == name
                stance[name] = (_keyed(self.STEP, s) if attacking else self.STANCE,
                                _keyed(self.ATTACK if attacking else self.GUARD, s))
                leap = self.FIGHTERS[name].get("leap", 0) if attacking else 0
                lift[name] = -round(leap * math.sin(math.pi * progress(s, *self.LEAP_S)))
            return self._at(stance, lift)
        t -= self.DUEL_S
        if t < self.LOCK_S:
            d = self.STANCE + progress(t, 0, 0.15) * (self.LOCKED - self.STANCE)
            angle = 45 + progress(t, 0, 0.15) * (self.LOCK_ANGLE - 45)
            shiver = self.SHIVER if int(t * FPS) // 2 % 2 else -self.SHIVER
            return self._at({self.LEFT: (d, angle + shiver), self.RIGHT: (d, angle - shiver)}, {})
        p = progress(t - self.LOCK_S, 0, self.PUSH_S)
        d = self.LOCKED + ease_out(p) * (self.offstage + self.STANCE)
        angle = self.LOCK_ANGLE + progress(p, 0, 0.3) * (90 - self.LOCK_ANGLE)
        return self._at({name: (d, angle) for name in self.names}, {})

    def _at(self, stance, lift):
        return {name: (self.cx - self._forward(name) * d, self.anchor_y[name] + lift.get(name, 0), e)
                for name, (d, e) in stance.items()}

    def nudges(self, t):
        """{name: (lean, recoil)}: pixels the upper body tips forward, and the whole fighter is knocked back."""
        out = {name: (0, 0) for name in self.names}
        since = t - self.WALK_S
        if 0 <= since < self.DUEL_S:
            i = int(since / self.EXCHANGE_S)
            s = since - i * self.EXCHANGE_S
            attacker = self.attackers[i]
            defender = self.RIGHT if attacker == self.LEFT else self.LEFT
            out[attacker] = (1 if self.LEAN_S[0] <= s < self.LEAN_S[1] else 0, 0)
            out[defender] = (0, 1 if self.HIT_S[0] <= s < self.HIT_S[0] + self.RECOIL_S else 0)
        return out

    def _forward(self, name):
        return 1 if name == self.LEFT else -1

    def _art_origin(self, name, x, y, recoil):
        """The art's top-left on the board for a fighter whose anchor is at (x, y)."""
        ax, ay = self.FIGHTERS[name]["anchor"]
        return int(round(x - ax)) - recoil * self._forward(name), int(round(y - ay))

    def arm(self, name, t):
        """((shoulder x, y), (fist x, y), elevation): the arm swings with the blade, the fist high when it's raised."""
        x, y, elevation = self.pose(t)[name]
        lean, recoil = self.nudges(t)[name]
        fighter, fwd = self.FIGHTERS[name], self._forward(name)
        ox, oy = self._art_origin(name, x, y, recoil)
        sx, sy = ox + fighter["shoulder"][0] + lean * fwd, oy + fighter["shoulder"][1]
        # Raised (85) the fist is up by his head; at rest (45) straight out at shoulder height;
        # cutting down (25) it's out in front and low.
        a = math.radians(25 - (elevation - 25) * 85 / 60)
        return (sx, sy), (sx + fwd * math.cos(a) * fighter["arm"], sy + math.sin(a) * fighter["arm"]), elevation

    def blade(self, name, t):
        """(x, y, elevation): where the blade leaves the hilt, past the fist."""
        _, (fx, fy), elevation = self.arm(name, t)
        dx, dy = self._direction(name, elevation)
        # From the middle of the 2x2 fist, along the hilt; the blade's first pixel is a step on.
        cx, cy = int(round(fx)) + 0.5, int(round(fy)) + 0.5
        return cx + dx * (self.HILT_LEN + 0.5), cy + dy * (self.HILT_LEN + 0.5), elevation

    def _direction(self, name, elevation):
        a = math.radians(elevation)
        return self._forward(name) * math.cos(a), -math.sin(a)

    def contact(self, t):
        """(x, y) where the two blades cross at t, or None while they're apart."""
        (lx, ly, le), (vx, vy, ve) = self.blade(self.LEFT, t), self.blade(self.RIGHT, t)
        (ldx, ldy), (vdx, vdy) = self._direction(self.LEFT, le), self._direction(self.RIGHT, ve)
        det = ldx * -vdy + vdx * ldy
        if abs(det) < 1e-9:
            return None
        # Solve root_l + s * dir_l == root_r + u * dir_r for the distances along each blade.
        ex, ey = vx - lx, vy - ly
        s = (ex * -vdy + vdx * ey) / det
        u = (ldx * ey - ldy * ex) / det
        if 0 <= s <= self.BLADE_LEN and 0 <= u <= self.BLADE_LEN:
            return lx + s * ldx, ly + s * ldy
        return None

    def gap(self, t):
        """(left, right): the columns strictly between show the new ride, opening from the centre once the lock breaks."""
        since = t - (self.WALK_S + self.DUEL_S + self.LOCK_S)
        if since < 0:
            return None
        g = ease_out(progress(since, 0, self.PUSH_S)) * self.offstage
        return self.cx - g, self.cx + g

    def _blade_pixels(self, pixels, name, x0, y0, elevation, rgb, frame=0):
        """The blade, BLADE_W thick; a crossguard adds two short side blades at its base, and a
        crackling blade throws off pixels along both edges that change every frame."""
        fighter = self.FIGHTERS[name]
        dx, dy = self._direction(name, elevation)
        steep = abs(dy) >= abs(dx)
        for i in range(2, 2 * self.BLADE_LEN + 1):
            x, y = int(round(x0 + dx * i / 2)), int(round(y0 + dy * i / 2))
            for k in range(self.BLADE_W):
                put(pixels, x + k if steep else x, y if steep else y + k, rgb, self.width, self.height)
            if fighter.get("crackle") and i > 3 and (i * 7919 + frame * 104729) % 5 == 0:
                k = -1 if (i + frame) % 2 else self.BLADE_W
                put(pixels, x + k if steep else x, y if steep else y + k, rgb, self.width, self.height)
        if fighter.get("crossguard"):
            # Square to the blade, a pixel up from the hilt, two pixels out each side.
            bx, by = x0 + dx, y0 + dy
            for k in (-2, -1, 2, 3):
                put(pixels, int(round(bx - dy * k)), int(round(by + dx * k)), rgb, self.width, self.height)

    def back_arm(self, name, t):
        """(shoulder, fist) of a fighter's free back arm, or None: held out behind him for balance,
        flung back and up as he cuts, tucked lower as he raises his blade."""
        fighter = self.FIGHTERS[name]
        if "back_shoulder" not in fighter:
            return None
        x, y, elevation = self.pose(t)[name]
        lean, recoil = self.nudges(t)[name]
        ox, oy = self._art_origin(name, x, y, recoil)
        fwd = self._forward(name)
        sx, sy = ox + fighter["back_shoulder"][0] + lean * fwd, oy + fighter["back_shoulder"][1]
        # Degrees below straight back: 45 with the blade raised (85), 25 at rest (45), 20 on the cut (35).
        a = math.radians(20 + max(0, elevation - 35) * 0.5)
        return (sx, sy), (int(round(sx - fwd * math.cos(a) * fighter["arm"])) - (1 if fwd > 0 else 0),
                          int(round(sy + math.sin(a) * fighter["arm"])))

    def _limb_pixels(self, pixels, fighter, shoulder, fist, body):
        """A 2px sleeve from the shoulder to a 2x2 fist at `fist` (its top-left), outlined in black
        where it's out past the body; over the body, an outline would cut lines into his clothes."""
        (sx, sy), (fx, fy) = shoulder, fist
        steps = max(1, int(math.hypot(fx - sx, fy - sy) * 2))
        sleeve = set()
        for i in range(steps + 1):
            x, y = int(round(sx + (fx - sx) * i / steps)), int(round(sy + (fy - sy) * i / steps))
            sleeve |= {(x, y), (x, y + 1)}
        hand = {(fx + dx, fy + dy) for dx in (0, 1) for dy in (0, 1)}
        drawn = sleeve | hand
        for x, y in drawn:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) not in drawn and (x + dx, y + dy) not in body:
                        pixels[(x + dx, y + dy)] = self.COLORS["K"]
        for xy in sleeve:
            pixels[xy] = self.COLORS[fighter["sleeve"]]
        top, bottom = fighter["fist"]
        for x, y in hand:
            pixels[(x, y)] = self.COLORS[top if y == fy else bottom]

    def _arm_pixels(self, pixels, name, t, body):
        """The arms (the free back one first, behind), the fists and the hilt between the front fist and the blade."""
        fighter = self.FIGHTERS[name]
        back = self.back_arm(name, t)
        if back:
            self._limb_pixels(pixels, fighter, *back, body)
        shoulder, (fx, fy), elevation = self.arm(name, t)
        fx, fy = int(round(fx)), int(round(fy))
        self._limb_pixels(pixels, fighter, shoulder, (fx, fy), body)
        dx, dy = self._direction(name, elevation)
        for i in range(1, self.HILT_LEN + 1):
            pixels[(int(round(fx + 0.5 + dx * (i + 0.5))), int(round(fy + 0.5 + dy * (i + 0.5))))] = self.COLORS["B"]

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        gap = self.gap(t)
        # The old screen, every pixel of it, black included, except where it's opened: show_screen
        # has already drawn the new screen underneath.
        frame = {}
        for x in range(self.width):
            if gap and gap[0] < x < gap[1]:
                continue
            for y in range(self.height):
                frame[(x, y)] = self.prev_px.get((x, y), (0, 0, 0))
        pose, nudges = self.pose(t), self.nudges(t)
        shade = int(t * FPS) % 2
        cape_out = int(t / self.CAPE_S) % 2
        # The right fighter first, so the left one's blade crosses in front of him.
        for name in (self.RIGHT, self.LEFT):
            x, y, _ = pose[name]
            lean, recoil = nudges[name]
            fighter = self.FIGHTERS[name]
            art = fighter["cape_art"] if cape_out and "cape_art" in fighter else fighter["art"]
            ox, oy = self._art_origin(name, x, y, recoil)
            waist = fighter["waist"]
            body = dict(art_pixels(art[:waist], ox + lean * self._forward(name), oy, self.COLORS, self.scale))
            body.update(art_pixels(art[waist:], ox, oy + waist, self.COLORS, self.scale))
            # Its own outline doesn't count: an arm crossing it out past the body is outlined as usual.
            inside = {xy for xy, rgb in body.items() if rgb != self.COLORS["K"]}
            frame.update(body)
            self._arm_pixels(frame, name, t, inside)
            self._blade_pixels(frame, name, *self.blade(name, t), self.BLADES[fighter["blade"]][shade], int(t * FPS))
        frame = {xy: rgb for xy, rgb in frame.items() if 0 <= xy[0] < self.width and 0 <= xy[1] < self.height}
        point = self.contact(t)
        if point and self._clashing(t):
            burst_pixels(frame, *point, int(t * FPS), 1, self.width, self.height)
        spark_pixels(frame, self.sparks, t, self.height / 32, self.width, self.height)
        for (x, y), rgb in frame.items():
            canvas.SetPixel(x, y, *rgb)
        return True

    def _clashing(self, t):
        """Whether the blades are pressed together (a hit's bind or the lock), not just passing."""
        since = t - self.WALK_S
        if since < 0:
            return False
        if since < self.DUEL_S:
            s = since % self.EXCHANGE_S
            return self.HIT_S[0] <= s < self.HIT_S[1]
        return since < self.DUEL_S + self.LOCK_S

class SaberDuelReveal(_SaberDuel):
    """
    Luke and Darth Vader, from the user's two pixel-art references: Luke on the left with his
    blue lightsaber, his free arm out behind him for balance, and Vader on the right with his
    red one, his cape swinging. Only on the Star Wars rides (disney.RIDE_VISITORS), never in the
    random rotation; one of the duels random_saber_duel picks from.
    """

    LEFT, RIGHT = "luke", "vader"

    # From skywalker-saber.jpg cell for cell, with his fists, hilt and blade taken out (the
    # arms, hilt and blade are drawn in code so they can swing). The left sleeve that hung down
    # to his hands is gone too, so his tunic is narrower there, and the cream trousers show
    # between its hem and his boots where his fists were. '.' empty, K outline, O hair, I skin, c eyes, W robe, w robe shadow,
    # o boot tops, A boots.
    LUKE_ART = [
        ".......KKKKKKKK......",
        "......KOOOOOOOOK.....",
        ".....KOOOOOOOOOOK....",
        "....KOOOOOOOOOOOOK...",
        "....KOOOOOIOOIOOOK...",
        "....KOOOOIKKKIKKOK...",
        "...KOOOIOIWccIcWK....",
        "....KOOIIIWccIcWK....",
        ".....KOIIIIWWIWIK....",
        ".....KKKIIKKIIIK.....",
        "....KWWWKIIIIIKK.....",
        "...KWWWWwKKKKKWWK....",
        "...KWWWWWIIwKWWWK....",
        "...KWWWWWWIWWWWWK....",
        "...KWWWWWWWWWWWWK....",
        "...KWWWWWwWWWWWWK....",
        "...KWWWWWWWWWWWK.....",
        "....KWWWWWWWWWK......",
        ".....KWWWWWWWWWK.....",
        "....KwwwwKKwwwwwK....",
        "...KoowKKKKKwwwooK...",
        ".KKoooooK...KoooooKK.",
        "KAAAAAAAK...KAAAAAAAK",
        "KKKKKKKKK...KKKKKKKKK",
    ]

    # From Darth-Vader-2.jpg cell for cell, with his glove, hilt and blade taken out, then
    # stretched to Luke's 24 rows by doubling two helmet rows, two body rows and a column each
    # side of his helmet (columns 3 and 12 of the reference). The
    # board shows black as off, so his greys are lifted (TRON's charcoal) or his helmet and
    # cape would vanish. '.' empty, K outline, D dark armour, G mid grey, g light grey, P cape,
    # C chest box, R and b its lights.
    VADER_ART = [
        ".....KKKKKKKK.......",
        "...KKDDDGDDDDKK.....",
        "..KDDDDDGDDDDDDK....",
        "..KDDDDDGDDDDDDK....",
        "..KDDDDDGDDDDDDK....",
        "..KDDGGDGDGGDDDK....",
        "..KGGDDGGGDDGDDK....",
        "..KGGKKKDKKKGDDK....",
        "..KGGKKDgDKKGDDK....",
        ".KGDDDDGDGDDDGGDK...",
        ".KGDDDGDDDGDDGGDK...",
        ".KGDDDGDDDGDDGGDK...",
        ".KGKKDgGGGgDDGGDK...",
        ".KKKKKKKKKKKKKKKK...",
        "...KKGgGgGgGgKKK....",
        ".....KgDgGgGKDDKK...",
        ".....KDCDbDDKGGKPK..",
        ".....KDDCRDDKGGKPK..",
        ".....KDGGGGGKKKPDDK.",
        ".....KDGGGGGKKKPDDK.",
        "...KKKDDDDDDKPPDDDK.",
        "...KKKDDDDDDKPPDDDK.",
        ".....KDGKKDGKPPDDKK.",
        ".....KKK..KKKKKKK...",
    ]
    # His cape's back edge swung out a pixel; he alternates between the two as he moves.
    VADER_CAPE_ART = VADER_ART[:16] + [
        ".....KDCDbDDKGGKPPK.",
        ".....KDDCRDDKGGKPPK.",
        ".....KDGGGGGKKKPDDDK",
        ".....KDGGGGGKKKPDDDK",
        "...KKKDDDDDDKPPDDDDK",
        "...KKKDDDDDDKPPDDDDK",
        ".....KDGKKDGKPPDDDKK",
        ".....KKK..KKKKKKKK..",
    ]

    COLORS = dict(VADER_COLORS, **{
        "O": (168, 138, 50), "I": (254, 201, 184), "c": (33, 112, 146), "W": (246, 249, 244),
        "w": (222, 227, 194), "o": (205, 183, 166), "A": (184, 165, 150),
    })
    VADER = {"art": VADER_ART, "cape_art": VADER_CAPE_ART, "anchor": (0.5, 14.5), "shoulder": (5, 15),
             "arm": 5, "waist": 15, "sleeve": "D", "fist": ("W", "K"), "blade": "red"}
    FIGHTERS = {
        "luke": {"art": LUKE_ART, "anchor": (10.5, 15.5), "shoulder": (14, 12), "back_shoulder": (4, 12),
                 "arm": 5, "waist": 16, "sleeve": "W", "fist": ("I", "I"), "blade": "blue"},
        "vader": VADER,
    }


class ObiWanDuelReveal(_SaberDuel):
    """
    Obi-Wan Kenobi against Darth Vader: the same fight as Luke's, Obi-Wan on the left with his
    blue blade and his free arm out behind him. One of the duels random_saber_duel picks from.
    """

    LEFT, RIGHT = "obiwan", "vader"

    # From "hans- solo.jpg" (Obi-Wan despite the name) cell for cell, 24 rows like Luke, with
    # his raised sword arm, his blade held over his head and his pointing arm taken out (his
    # arms are drawn in code). The blade hid the top of his head, so rows 2-4 are his hair
    # filled in, and the background showing between his arm and his head is gone. '.' empty,
    # K outline, A hair and beard, O skin and light robe, o robe, W his eyes' whites, k belt,
    # S its buckle, r boots (the reference's R, moved off Vader's red).
    OBIWAN_ART = [
        "...........KKKKKKKK.....",
        "..........KAAAAAAAAK....",
        ".........KAAAAAAAAAAK...",
        "........KAAAAAAAAAAAK...",
        "........KAAAAAAAAAAAK...",
        "........KAOAOrrOOOrAK...",
        "........KAOAOOOrOrOK....",
        "........KAOAOWKKOKWK....",
        "........KKAAOOOOOOOK....",
        "......KoooKAAOAAAOK.....",
        "......KoooOKAAOOOAooK...",
        ".......KoooOKKAAAooOK...",
        "........KoooOOOoooOK....",
        ".........KooOOOooK......",
        ".........KoooOoooK......",
        ".........KoooooooK......",
        ".........KkkSSkkkK......",
        ".........KkkkkkkkK......",
        "........KOoooOoooOK.....",
        ".......KoOOOOKOOOOoK....",
        "......KrroooK.KooorrK...",
        "....KKrrrrrK...KrrrrrKK.",
        "...KrrrrrrrK...KrrrrrrrK",
        "...KKKKKKKKK...KKKKKKKKK",
    ]
    COLORS = dict(VADER_COLORS, **{
        "A": (161, 88, 34), "O": (238, 212, 189), "o": (206, 194, 160), "k": (39, 24, 22),
        "S": (165, 165, 165), "r": (123, 39, 35),
    })
    FIGHTERS = {
        "obiwan": {"art": OBIWAN_ART, "anchor": (15.5, 13.5), "shoulder": (19, 10), "back_shoulder": (8, 10),
                   "arm": 5, "waist": 16, "sleeve": "O", "fist": ("O", "O"), "blade": "blue"},
        "vader": SaberDuelReveal.VADER,
    }


class YodaDuelReveal(_SaberDuel):
    """
    Yoda against Darth Vader. Yoda stays small, as in the films (21 rows to Vader's 24), and
    makes up for it the way he fights: he hops in, and on each of his attacks he leaps and comes
    down on Vader's guard from above. One of the duels random_saber_duel picks from.
    """

    LEFT, RIGHT = "yoda", "vader"

    # From Yoda-saber.jpg cell for cell, his blade and both arms taken out (the arms are drawn
    # in code). Not mirrored: his head is turned to his right, toward Vader. The reference's
    # white background showing round his head is gone (the outline moved in to meet it), his far
    # ear is three cells longer so it reads on the board, and both pupils look at Vader.
    # '.' empty, K outline, Y skin, y its shadow, W his eyes, O robe, N its brown middle,
    # o toenail, k a fold.
    YODA_ART = [
        ".......KKKKKK........",
        "......KyYyYyYK.......",
        "......KYyYyYyYK......",
        ".KKKKKYYYyYyYyYKKKKK.",
        "KYYYYYYYYYYYYYYKYYYYK",
        ".KKyyYYYYyyYYYyKyyKK.",
        "...KKYYYYWyyYWyKK....",
        ".....KYYYWyyYWyK.....",
        ".....KYYYYYYYYYK.....",
        "....KKKYYKKKYYK......",
        "....KKKKYYYYYKK......",
        ".....KOOKKKKOK.......",
        ".....KOONNNOOK.......",
        ".....KOONNNOOK.......",
        ".....KOONNNOOk.......",
        ".....KOONNNOOK.......",
        ".....KOONNNOOK.......",
        "....KOOONNNOOOK......",
        "...KOOOONKNOOOOK.....",
        "..KoYYYYK.KYYYYOK....",
        "..KKKKKKK.KKKKKKK....",
    ]
    COLORS = dict(VADER_COLORS, **{
        "Y": (134, 159, 76), "y": (97, 131, 55), "O": (176, 157, 125), "N": (90, 60, 11),
        "o": (209, 179, 106), "k": (27, 27, 29),
    })
    FIGHTERS = {
        "yoda": {"art": YODA_ART, "anchor": (9.5, 15.5), "shoulder": (13, 12), "back_shoulder": (6, 12),
                 "arm": 4, "waist": 11, "sleeve": "O", "fist": ("Y", "Y"), "blade": "green", "leap": 7},
        "vader": SaberDuelReveal.VADER,
    }


class KyloReyDuelReveal(_SaberDuel):
    """
    Rey against Kylo Ren, both from KidKinobi's pixel art (the same artist, so they match): Rey
    on the left with her yellow blade, Kylo on the right with his red crossguard saber, which
    crackles, its edges spitting pixels, like the unstable blade in the films. One of the
    duels random_saber_duel picks from.
    """

    LEFT, RIGHT = "rey", "kylo"

    # From rey-saber.jpg cell for cell, her blade and saber arm taken out; her other arm stays,
    # hanging at her side as drawn. '.' empty, K outline, N hair, boots and belt, O skin,
    # W wraps, S trousers and sash, k a fold.
    REY_ART = [
        "......KK.............",
        ".....KNNKKKKKK.......",
        ".....KNKNNNNNNK......",
        "....KNKNNNNNNNNK.....",
        "....KNKNNNNNNNNNK....",
        "...KNKNNNNOOOOOOK....",
        "...KNKONNONNOOONK....",
        "....KKOONOWKKOKWK....",
        "......KONOWKKOKWK....",
        ".....KKOOOOOOOOOK....",
        "....KWWKOOOKKKOKK....",
        "...KNNWWKOOOOOK......",
        "..KOOONWSKKKKKOK.....",
        ".KWWOOKWWSOSWWWK.....",
        ".KWWKKKWWWSWWWWK.....",
        ".KOOOKWKWWSWWKWK.....",
        ".KOOOKWKNNNNNKWK.....",
        "..KKKWKWWWWWWWK......",
        ".....KWSSSSSSSWK.....",
        "....KSSSSSKSSSSSK....",
        "...KKNNSSK.KSSNNKK...",
        ".KKNNNNNK...KNNNNNKK.",
        "KNNNNNNNK...KNNNNNNNK",
        "KKKKKKKKK...KKKKKKKKK",
    ]
    # From kylo-saber.jpg cell for cell, his saber and saber arm taken out, mirrored to face Rey,
    # and his near-black greys lifted (as on Vader) so he doesn't vanish into the board. His cape
    # runs off the back of the reference and ends there. '.' empty, K outline, D robe and helmet,
    # d its shadow, v the visor.
    KYLO_ART = [
        "........KKK............",
        ".......KDDDKK..........",
        "......KDDDDDDK.........",
        ".....KDDDDDDDDK........",
        "....KDDDDDDDDDK........",
        "....KDdDddDDDDDK.......",
        "....KdvvvvddDDDK.......",
        "....KdvvvvvvdDDK.......",
        "....KdKKKKvvdDDK.......",
        "....KdKKKKKdddDK.......",
        "...KKKKKKKKddKDDKK.....",
        "..KdddKKKKKdKDDDddK....",
        "..KdddKKKKKKDDDdddK....",
        "..KdddKDDDDDDDKddddK...",
        "..KdKKKDDDDDDDKKKddKK..",
        "...KDKKDDDDDDDKKDDDKDK.",
        ".....KKdddddddKKDDDKDDK",
        "......KdddddddKDKKKDDDD",
        ".....KDDDDDDDDDKDDDDDDD",
        "....KDDDDDDDDDDDKDDDDDD",
        "...KKDDDDDDDDDDDKKDDDDD",
        ".KKdddDDDDDDDDDdddKKDDD",
        "KdddddddKKKKKdddddddKDD",
        "KKKKKKKKK.KDKKKKKKKKKDD",
    ]
    COLORS = {
        "K": (0, 0, 0), "N": (83, 49, 3), "O": (255, 187, 128), "W": (255, 255, 219), "S": (211, 211, 204),
        "k": (45, 45, 45), "D": (80, 80, 88), "d": (58, 58, 64), "v": (185, 185, 185), "B": (152, 152, 152),
    }
    FIGHTERS = {
        "rey": {"art": REY_ART, "anchor": (10.5, 15.5), "shoulder": (14, 12), "arm": 5, "waist": 17,
                "sleeve": "W", "fist": ("O", "O"), "blade": "yellow"},
        "kylo": {"art": KYLO_ART, "anchor": (0.5, 11.5), "shoulder": (5, 12), "arm": 5, "waist": 16,
                 "sleeve": "D", "fist": ("d", "d"), "blade": "red", "crossguard": True, "crackle": True},
    }


DUELS = (SaberDuelReveal, ObiWanDuelReveal, YodaDuelReveal, KyloReyDuelReveal)


def random_saber_duel(width, height, rng=None):
    """One of the DUELS, chosen at random: what the Star Wars rides' duel roll plays."""
    rng = rng or random.Random()
    return rng.choice(DUELS)(width, height, rng)
