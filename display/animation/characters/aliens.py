import os
import random

from display.animation.drawing import _blackout, art_pixels, paint
from display.capture import _glyphs
from display.motion import ease_out, progress

_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "fonts", "patched")


def _text_cells(text, font):
    """The lit pixels of text in a BDF font, from its top-left, and its (width, height)."""
    glyphs, cells, x = _glyphs(os.path.join(_FONTS, font)), [], 0
    for ch in text:
        advance, h, x_off, y_off, rows, _ = glyphs.get(ord(ch), glyphs.get(ord("?")))
        for r, bits in enumerate(rows):
            cells += [(x + x_off + c, r - h - y_off) for c, bit in enumerate(bits) if bit == "1"]
        x += advance
    top = min(y for _, y in cells)
    cells = [(cx, cy - top) for cx, cy in cells]
    return cells, (x, max(y for _, y in cells) + 1)


def _looking_up(art):
    """The alien with his pupils in the top of his eyes: looking up at the claw."""
    rows = [list(row) for row in art]
    for r in range(1, len(rows)):
        for c, k in enumerate(rows[r]):
            if k == "K" and rows[r - 1][c] == "W":
                rows[r][c], rows[r - 1][c] = "W", "K"
    return ["".join(row) for row in rows]


class AliensReveal:
    """
    The Little Green Men from Pizza Planet's claw machine. A crowd of them shuffles in from both
    sides onto the dark board; the claw comes down from the top and they all look up at it. It
    opens over one of them, picked at random each time, shuts on his head and lifts him off the
    top of the board. YOU'VE BEEN CHOSEN! Then the rest shuffle off the sides, and the new ride is
    uncovered between them as they go.
    """

    SCALE = 1  # small on both boards, so there's a crowd
    TEXT = ("YOU'VE BEEN", "CHOSEN!")
    HANGING_BELOW = 0  # rows of anything hanging under the chosen one as he's lifted
    hold_after_s = 3.0  # the ride screen, after they leave
    ENTER_S, WAIT_S, CLAW_S, GRAB_S, LIFT_S, TEXT_S, EXIT_S = 1.0, .3, 1.0, .35, 1.0, 1.6, 1.0
    STEP_S = .12  # each bob of their shuffle
    TEXT_RGB, EDGE_RGB = (255, 230, 60), (0, 0, 0)

    # Redrawn small from the Toy Story 4 sheet's alien (docs/references/toy_story_4_sheet.png):
    # antenna, three eyes, pointed ears, smile, purple collar, blue suit with green hands, dark
    # legs. '.' empty, g outline green, G green, W white, K pupil, m mouth, P purple, B blue,
    # b dark blue.
    ART = [
        "......gg......",
        "......GG......",
        "......gg......",
        "....gGGGGg....",
        "..gGGGGGGGGg..",
        "ggGGGGGGGGGGgg",
        "gGGWWGWWGWWGGg",
        "gGGWKGWKGWKGGg",
        ".ggGGGGGGGGgg.",
        "..gGGmmmmGGg..",
        "...gGGGGGGg...",
        "...PPPPPPPP...",
        ".GBBBBBBBBBBG.",
        ".GBBBBBBBBBBG.",
        "..BBBBBBBBBB..",
        "..bbbbbbbbbb..",
        "...BBB..BBB...",
        "..bbbb..bbbb..",
    ]
    colors = {"g": (40, 140, 40), "G": (120, 206, 75), "W": (240, 248, 244), "K": (10, 10, 10),
              "m": (15, 100, 30), "P": (110, 60, 170), "B": (20, 70, 190), "b": (10, 30, 110)}
    # The claw, open and shut: k hub, S steel prongs.
    CLAW_OPEN_ART = [
        "....kkk....",
        "..kSSSSSk..",
        ".kSSSSSSSk.",
        ".S..S.S..S.",
        "S...S.S...S",
        "S....S....S",
        ".S.......S.",
    ]
    CLAW_SHUT_ART = [
        "....kkk....",
        "..kSSSSSk..",
        "..kSSSSSk..",
        "...S.S.S...",
        "...S.S.S...",
        "....SSS....",
        "....S.S....",
    ]
    CLAW_COLORS = {"k": (90, 90, 100), "S": (200, 200, 210)}
    CABLE_RGB = (150, 150, 160)
    CLAW_GRIP = 4  # rows of the alien's head inside the shut claw

    # Where the crowd stands, as (top row, left of the first alien) per row, back to front; 16
    # columns apart. 64x32: a back row of heads peeking over the front row. 64x64: three rows.
    ROWS = [(0, -7), (14, 1)]
    BIG_ROWS = [(6, -7), (26, 1), (46, -7)]
    PITCH = 16

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.w, self.h = len(self.ART[0]), len(self.ART)
        rows = self.BIG_ROWS if height >= 64 else self.ROWS
        self.spots = [(off + i * self.PITCH, y) for y, off in rows
                      for i in range(width // self.PITCH + 2) if -self.w // 2 <= off + i * self.PITCH <= width - self.w // 2]
        # A different one each time: any wholly on the board, and low enough that the whole claw is in
        # sight when it grabs him (on 64x32, the front row).
        grab_low = len(self.CLAW_OPEN_ART) - 1 - self.CLAW_GRIP
        self.choices = [s for s in self.spots if 0 <= s[0] <= width - self.w and s[1] >= grab_low and self.can_choose(s)]
        self.chosen = self.rng.choice(self.choices)
        self.up = _looking_up(self.ART)
        big = height >= 64
        self.lines = [_text_cells(self.TEXT[0], "5x8.bdf"), _text_cells(self.TEXT[1], "7x13B.bdf" if big else "5x8.bdf")]
        t = 0.0
        self.claw_at = t = t + self.ENTER_S + self.WAIT_S
        self.grab_at = t = t + self.CLAW_S
        self.lift_at = t = t + self.GRAB_S
        self.text_at = t = t + self.LIFT_S
        self.exit_at = t = t + self.TEXT_S
        self.duration = t + self.EXIT_S
        # Far enough for the whole crowd to be off the board on its side.
        self.away = width // 2 + self.w + 1

    def shift(self, t):
        """How far each half of the crowd is out to its side: in at the start, out at the end."""
        if t < self.ENTER_S:
            return round(self.away * (1 - ease_out(progress(t, 0, self.ENTER_S))))
        if t >= self.exit_at:
            p = progress(t, self.exit_at, self.duration)
            return round(self.away * p * p)
        return 0

    def claw_tip(self, t):
        """The row the claw's prongs reach down to, or None while it's off the board."""
        open_h = len(self.CLAW_OPEN_ART)
        down = self.chosen[1] + self.CLAW_GRIP
        if t < self.claw_at or t >= self.text_at:
            return None
        if t < self.grab_at:
            return round(-1 + (down + 1) * ease_out(progress(t, self.claw_at, self.grab_at)))
        if t < self.lift_at:
            return down
        # Up and off the top, with him (and anything hanging from him) under it.
        off = -(self.h - self.CLAW_GRIP) - open_h - self.HANGING_BELOW
        return round(down + (off - down) * progress(t, self.lift_at, self.text_at) ** 1.5)

    def chosen_y(self, t):
        """The chosen alien's top row: where he stands until the claw lifts him."""
        tip = self.claw_tip(t)
        if t < self.lift_at:
            return self.chosen[1]
        return None if tip is None else tip - self.CLAW_GRIP

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        mid, shift = self.width // 2, self.shift(t)
        if t < self.exit_at:
            _blackout(canvas, 0, self.width, self.height)
        else:
            # The ride shows between the two halves as they go.
            _blackout(canvas, 0, max(0, mid - shift), self.height)
            _blackout(canvas, min(self.width, mid + shift), self.width, self.height)
        moving = shift > 0
        looking = self.claw_at <= t < self.exit_at
        pixels = []
        for i, (x, y) in enumerate(self.spots):
            art = self.figure((x, y), t, looking)
            if art is None:
                continue
            side = -1 if x + self.w / 2 < mid else 1
            bob = -1 if moving and (int(t / self.STEP_S) + i) % 2 else 0
            pixels += list(art_pixels(art, x + side * shift, y + bob, self.colors))
        if t >= self.lift_at and self.chosen_y(t) is not None:
            pixels += self.carried(t)
        tip = self.claw_tip(t)
        if tip is not None:
            pixels += self._claw(tip, t >= self.grab_at)
        paint(canvas, pixels, self.width, self.height)
        if self.text_at <= t < self.exit_at:
            self._text(canvas)
        return True

    def can_choose(self, spot):
        """Whether the claw may pick whoever stands here."""
        return True

    def figure(self, spot, t, looking):
        """The art standing at spot in the crowd at t, or None once he's gone."""
        if spot == self.chosen and t >= self.lift_at:
            return None
        return self.up if looking else self.ART

    def carried(self, t):
        """What the claw is lifting at t, as pixels: the chosen alien."""
        return list(art_pixels(self.ART, self.chosen[0], self.chosen_y(t), self.colors))

    def _claw(self, tip, shut):
        art = self.CLAW_SHUT_ART if shut else self.CLAW_OPEN_ART
        cx, top = self.chosen[0] + self.w // 2, tip - len(art) + 1
        cable = [((cx, y), self.CABLE_RGB) for y in range(0, top)]
        return cable + list(art_pixels(art, cx - len(art[0]) // 2, top, self.CLAW_COLORS))

    def _text(self, canvas):
        """TEXT's two lines in yellow with a black edge, centred over the crowd."""
        (first, (w1, h1)), (second, (w2, h2)) = self.lines
        gap = 2
        y0 = (self.height - (h1 + gap + h2)) // 2
        lit = [(x + (self.width - w1) // 2, y + y0) for x, y in first]
        lit += [(x + (self.width - w2) // 2, y + y0 + h1 + gap) for x, y in second]
        on = set(lit)
        edge = {(x + dx, y + dy) for x, y in lit for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))} - on
        paint(canvas, [(p, self.EDGE_RGB) for p in edge] + [(p, self.TEXT_RGB) for p in lit], self.width, self.height)


class AliensToysReveal(AliensReveal):
    """
    The claw scene from Toy Story, for a short wait: Buzz and Woody are in the crowd of aliens, side
    by side. The claw chooses Buzz; as it lifts him, Woody leaps and grabs his boot, and the claw
    hauls them both up off the top of the board. THE CLAW CHOOSES. Then the aliens shuffle off.
    """

    TEXT = ("THE CLAW", "CHOOSES")
    LIFT_S = 1.4  # a longer haul, with Woody hanging on
    LEAP_S = .2  # Woody's jump up to Buzz's boot, once it's within his reach
    # Redrawn alien-sized from the Toy Story 4 sheet: Buzz in his dome helmet and purple hood, white
    # suit with a green and purple chest; Woody's hat and wide brim, bandana, cow-spot vest, jeans.
    # Woody also hangs by his right hand, raised past his hat. c helmet, P purple, O skin, o mouth,
    # W white, K eyes, G green, R red, V blue button, S grey; A hat, N hair, Y shirt, D boots and
    # belt, b jeans.
    BUZZ_ART = [
        "...cccccccc...",
        "..cPPPPPPPPc..",
        ".cPPOOOOOOPPc.",
        ".cPOOOOOOOOPc.",
        ".cPOWKOOWKOPc.",
        ".cPOOOOOOOOPc.",
        ".cPPOOooOOPPc.",
        "..cPPOOOOPPc..",
        "...cPPPPPPc...",
        "GWWWWGPPGWWWWG",
        "GWWGGRGVGGGWWG",
        ".WWPPGGGGPPWW.",
        "..WPPWWWWPPW..",
        "...WSSSSSSW...",
        "...WWWWWWWW...",
        "...WWW..WWW...",
        "...WWW..WWW...",
        "..PGGG..GGGP..",
    ]
    WOODY_ART = [
        ".....AAAA.....",
        "....AAAAAA....",
        ".AAAAAAAAAAAA.",
        "..NNNNNNNNNN..",
        "..NOOOOOOOON..",
        "..NOWKOOWKON..",
        "...OOOOOOOO...",
        "...OOooooOO...",
        "....OOOOOO....",
        "..YYYRRRRYYY..",
        ".OYWKYRRYKWYO.",
        ".OYKWYYYYWKYO.",
        "...YWKYYKWY...",
        "...DDDDDDDD...",
        "...bbbbbbbb...",
        "...bbb..bbb...",
        "...bbb..bbb...",
        "..DDDD..DDDD..",
    ]
    WOODY_HANGING_ART = [
        "............O.",
        "............Y.",
        ".....AAAA...Y.",
        "....AAAAAA..Y.",
        ".AAAAAAAAAAAY.",
        "..NNNNNNNNNNY.",
        "..NOOOOOOOONY.",
        "..NOWKOOWKONY.",
        "...OOOOOOOO.Y.",
        "...OOooooOO.Y.",
        "....OOOOOO..Y.",
        "..YYYRRRRYYYY.",
        ".OYWKYRRYKWY..",
        "..YKWYYYYWKY..",
        "...YWKYYKWY...",
        "...DDDDDDDD...",
        "...bbbbbbbb...",
        "...bbb..bbb...",
        "....bb..bb....",
        "....DD..DD....",
    ]
    colors = {**AliensReveal.colors, "c": (150, 200, 230), "O": (240, 205, 175), "o": (190, 110, 90),
              "R": (220, 30, 30), "V": (60, 120, 230), "S": (150, 150, 160), "A": (130, 75, 35),
              "N": (80, 40, 20), "Y": (245, 210, 40), "D": (90, 50, 25)}
    HAND = (0, 12)  # (row, column) of Woody's raised hand in WOODY_HANGING_ART
    BOOT = 10  # the column of Buzz's boot he grabs
    HANGING_BELOW = len(WOODY_HANGING_ART) - 1  # his hand overlaps Buzz's boot by a row

    def can_choose(self, spot):
        # Buzz needs Woody beside him, wholly on the board too.
        return bool(self._beside(spot))

    def _beside(self, spot):
        x, y = spot
        return [(nx, y) for nx in (x - self.PITCH, x + self.PITCH) if 0 <= nx <= self.width - self.w and (nx, y) in self.spots]

    def __init__(self, width, height, rng=None):
        super().__init__(width, height, rng)
        self.woody = self.rng.choice(self._beside(self.chosen))
        # Hanging, his feet where they stood; he jumps once Buzz's boot is up within his reach.
        self.reach = (self.woody[0], self.woody[1] + self.h - len(self.WOODY_HANGING_ART))
        frame = 1 / 60
        self.jump_at = self.lift_at
        while self.jump_at < self.text_at and self._hang(self.jump_at)[1] > self.reach[1]:
            self.jump_at += frame

    def figure(self, spot, t, looking):
        if spot == self.chosen:
            return None if t >= self.lift_at else self.BUZZ_ART
        if spot == self.woody:
            return None if t >= self.jump_at else self.WOODY_ART
        return super().figure(spot, t, looking)

    def _hang(self, t):
        """Where Woody's top-left is when he hangs from Buzz's boot at t."""
        return self.chosen[0] + self.BOOT - self.HAND[1], self.chosen_y(t) + self.h - 1 - self.HAND[0]

    def woody_at(self, t):
        """Woody's top-left once he's jumped: up to Buzz's boot, then hanging from it."""
        hang = self._hang(t)
        p = ease_out(progress(t, self.jump_at, self.jump_at + self.LEAP_S))
        return (round(self.reach[0] + (hang[0] - self.reach[0]) * p),
                round(self.reach[1] + (hang[1] - self.reach[1]) * p))

    def carried(self, t):
        buzz = list(art_pixels(self.BUZZ_ART, self.chosen[0], self.chosen_y(t), self.colors))
        if t < self.jump_at:
            return buzz
        # His hand over Buzz's boot, Buzz over the rest of him.
        wx, wy = self.woody_at(t)
        woody = list(art_pixels(self.WOODY_HANGING_ART, wx, wy, self.colors))
        hand = [p for p in woody if p[0][1] <= self.chosen_y(t) + self.h - 1]
        return woody + buzz + hand
