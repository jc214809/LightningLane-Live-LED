import random

from display.animation.mechanics import CapturesScreens
from display.animation.motion import ease_out
from display.pixels import blend, set_pixel


class FalconReveal(CapturesScreens):
    """
    The Millennium Falcon, top-down with her nose to the right, drawn from a reference photo.
    She drops out of hyperspace over the old ride screen (the stars' streaks snap back into
    points as she brakes in from the left), cruises a beat, then her engine band flares and
    she jumps to lightspeed: she and the whole old screen stretch into streaks running off
    the right edge, a blue-white flash fills the board, and it fades to the new ride.

    Only on the Galaxy's Edge rides (disney.RIDE_VISITORS), never in the random rotation.
    Needs the old screen to stretch and the new one to fade up through the flash, so it
    opts into both wants_prev and wants_new.
    """

    wants_prev = True
    wants_new = True
    ARRIVE_S, CRUISE_S, CHARGE_S, JUMP_S, FLASH_S = 0.8, 0.9, 0.35, 0.55, 0.4
    PHASES = (("arrive", ARRIVE_S), ("cruise", CRUISE_S), ("charge", CHARGE_S),
              ("jump", JUMP_S), ("flash", FLASH_S))
    duration = sum(sec for _, sec in PHASES)

    # Traced from the photo turned nose-right, then only the bold features kept (the
    # panelling came out as grey noise): the gap between the mandibles, the turret ring,
    # the docking arms above and below it, rear spokes, a few red patches, the cockpit tube
    # hanging off the bottom edge (her starboard side, seen from above), and the engine
    # band along the back. '.' empty, K outline, H hull, L light hull, M panel seam,
    # D dark, R red, W cockpit window, E engine.
    ART = [
        ".......KKKKKKK..............",
        ".....KKHHHMDMHKK............",
        "....KHHHHHMDMHHHKK..........",
        "..KKMMHHHHMDMHHHHHK.........",
        "..EHHMMHHHMDMHHHHHHKK.......",
        ".EHHHHMMHHMDMHHHHHHHHKK.....",
        ".EMHHHHMMHMDMHHHHHHHRRHKK...",
        "EHMMMMHHMMHHHHHHHHHHHHHHHKK.",
        "EHHHHMMMHMDDDDHHHHHHHHHHHHHK",
        "EHHHRHHHMHDLLDHMMMMKKKKKKKK.",
        "EHHHHHHHHDDLLDDLLLK.........",
        "EHHHHHHHMHDLLDHMMMMKKKKKKKK.",
        "EHHHHMMMHMDDDDHHHHHHHHHHHHHK",
        "EHMMMMHHMMHHHHHHHHHHHHHHHKK.",
        ".EMHHHHRMHMDMHHHHHHHHHHKK...",
        ".EHHHHMMHHMDMHHHRHHHHKK.....",
        "..EHHMMHHHMDMHHHHHHKK.......",
        "...KMMHHHHMDMHHHHHK.........",
        "....KKHHHHMDMHHHHHHKKK......",
        "......KKKKKKKKHHHHHHWWK.....",
        "..............KKKKKKKKK.....",
    ]
    COLORS = {
        "K": (85, 85, 92), "H": (170, 170, 165), "L": (215, 215, 210), "M": (120, 120, 118),
        "D": (62, 62, 68), "R": (200, 55, 45), "W": (120, 170, 230), "E": (70, 150, 255),
    }
    ENGINE_HOT = (210, 240, 255)  # the engine band at full burn, as she jumps
    STREAK_RGB = (200, 220, 255)  # stars and her arrival trail
    FLASH_RGB = (225, 238, 255)
    STARS = 14

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        # Doubled on 64x64, where she fills the board without swamping it.
        self.scale = s = 2 if height >= 64 else 1
        self.ship_w, self.ship_h = len(self.ART[0]) * s, len(self.ART) * s
        self.y0 = (height - self.ship_h) // 2
        self.cruise_dx = 4 * s
        # Where she comes to a stop: her nose must still be on the board at the end of
        # the cruise, or the mandibles (half her silhouette) get clipped.
        self.hold_x = max(0, min(int(width * 0.1), width - 1 - self.ship_w - self.cruise_dx))
        self.prev_px, self.new_px = {}, {}
        self._base = {}
        # The rows her engine band sits on, for her arrival trail and the glow outside it.
        self.engine_rows = [r for r, row in enumerate(self.ART) if "E" in row]
        self.stars = [(self.rng.randrange(width), self.rng.randrange(height)) for _ in range(self.STARS)]

    def phase(self, t):
        """(name, 0..1 through it) for the part of the visit at t."""
        for name, sec in self.PHASES:
            if t < sec:
                return name, t / sec
            t -= sec
        return self.PHASES[-1][0], 1.0

    def phase_start(self, name):
        start = 0.0
        for n, sec in self.PHASES:
            if n == name:
                return start
            start += sec
        raise KeyError(name)

    def ship_span(self, t):
        """(rear x, nose x) of her drawn span: braking in, cruising, backing off, then stretching away."""
        name, p = self.phase(t)
        stop = self.hold_x + self.cruise_dx
        if name == "arrive":
            # The jump in reverse: her nose shoots in from the left edge and brakes hard,
            # while the long streak behind it snaps down to her own length.
            nose = self.ship_w + (self.hold_x) * (1 - (1 - p) ** 4)
            nose = int(nose * min(1.0, p / 0.12)) if p < 0.12 else int(nose)
            stretch = 1 + 9 * (1 - min(1.0, p / 0.6)) ** 3
            return int(nose - self.ship_w * stretch), nose
        elif name == "cruise":
            x = self.hold_x + self.cruise_dx * p
        elif name == "charge":
            x = stop - 2 * self.scale * ease_out(p)  # a little settle back before the jump
        else:
            base = stop - 2 * self.scale
            if name == "flash":
                return self.width, self.width
            # The nose leaves far faster than the tail: she stretches into a streak.
            rear = base + (self.width + 1 - base) * p ** 3
            nose = base + self.ship_w + (self.width + 8 * self.ship_w) * p ** 2
            return int(rear), int(nose)
        return int(x), int(x) + self.ship_w

    def engine_rgb(self, t):
        name, p = self.phase(t)
        heat = {"charge": p, "jump": 1.0, "flash": 1.0}.get(name, 0.0)
        cool = self.COLORS["E"]
        return tuple(int(c + (h - c) * heat) for c, h in zip(cool, self.ENGINE_HOT))

    def old_stretch(self, t):
        """(shift, stretch) of the old screen: nothing until she jumps, then it streaks off to the right."""
        name, p = self.phase(t)
        if name == "jump":
            return self.width * 1.3 * p ** 3, 1 + 7 * p ** 2
        if name == "flash":
            return float(self.width * 2), 8.0
        return 0.0, 1.0

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        name, p = self.phase(t)
        if name == "flash":
            self._draw_flash(canvas, p)
            return True
        self._draw_old_screen(canvas, t)
        if name == "arrive":
            self._draw_stars(canvas, p)
        self._draw_ship(canvas, t)
        return True

    def _draw_old_screen(self, canvas, t):
        """
        Every pixel, black included, so the new screen show_screen drew underneath can't
        show through. Once she jumps, each row is stretched and shifted right, so every
        pixel becomes a streak running off the edge.
        """
        shift, stretch = self.old_stretch(t)
        get = self.prev_px.get
        self._base = base = {}  # what's on the board now, for blending soft light over it
        for y in range(self.height):
            for x in range(self.width):
                sx = int((x - shift) / stretch)
                rgb = get((sx, y), (0, 0, 0)) if sx >= 0 else (0, 0, 0)
                base[(x, y)] = rgb
                canvas.SetPixel(x, y, *rgb)

    def _draw_stars(self, canvas, p):
        """Coming out of hyperspace: streaks snapping back into points, then fading."""
        snap = min(1.0, p / 0.55)
        length = int(round(22 * self.scale * (1 - snap) ** 2))
        alpha = 0.85 if p < 0.55 else 0.85 * max(0.0, 1 - (p - 0.55) / 0.45)
        for x, y in self.stars:
            for i in range(length + 1):
                self._blend(canvas, x - i, y, self.STREAK_RGB, alpha * (1 - i / (length + 1)))

    def _draw_ship(self, canvas, t):
        rear, nose = self.ship_span(t)
        w = nose - rear
        if w <= 0:
            return
        src_w = len(self.ART[0])
        engine = self.engine_rgb(t)
        # Stretched out at lightspeed she's a streak of light, not a long grey hull.
        streak = min(0.85, max(0.0, (w / self.ship_w - 1) / 4))
        for py in range(self.ship_h):
            row = self.ART[py // self.scale]
            y = self.y0 + py
            for px in range(w):
                kind = row[min(src_w - 1, px * src_w // w)]
                if kind != ".":
                    rgb = engine if kind == "E" else self.COLORS[kind]
                    if streak:
                        rgb = tuple(int(c + (h - c) * streak) for c, h in zip(rgb, self.STREAK_RGB))
                    self._px(canvas, rear + px, y, rgb)
        name, p = self.phase(t)
        if name in ("charge", "jump"):
            # The burn spills out behind the engine band.
            glow = p if name == "charge" else 1.0
            for r in self.engine_rows:
                for sy in range(self.scale):
                    y = self.y0 + r * self.scale + sy
                    edge = rear + self.ART[r].index("E") * w // src_w
                    for i in range(1, 3 * self.scale + 1):
                        self._blend(canvas, edge - i, y, engine, 0.7 * glow * (1 - i / (3 * self.scale + 1)))

    def _draw_flash(self, canvas, p):
        """The jump's flash, fading to the new screen beneath it."""
        alpha = (1 - p) ** 2
        get = self.new_px.get
        for y in range(self.height):
            for x in range(self.width):
                under = get((x, y), (0, 0, 0))
                canvas.SetPixel(x, y, *(int(u + (f - u) * alpha) for f, u in zip(self.FLASH_RGB, under)))

    def _blend(self, canvas, x, y, rgb, alpha):
        """Soft light over the (possibly stretched) old screen, never a black hole in it."""
        if 0 <= x < self.width and 0 <= y < self.height and alpha > 0:
            canvas.SetPixel(x, y, *blend(rgb, self._base.get((x, y), (0, 0, 0)), alpha))

    def _px(self, canvas, x, y, rgb):
        set_pixel(canvas, x, y, rgb, self.width, self.height)
