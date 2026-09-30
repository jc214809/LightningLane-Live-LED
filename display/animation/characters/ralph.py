import random

from display.animation.drawing import art_pixels, paint
from display.animation.mechanics import CapturesScreens
from display.animation.motion import FPS, ease_out


class RalphReveal(CapturesScreens):
    """
    Wreck-It Ralph rises at the bottom, swings a fist, and the old screen shatters
    into falling pixels, leaving the new one behind. Needs the previous screen's
    pixels, so it opts in via wants_prev.
    """

    wants_prev = True
    RISE_S, WIND_S, FALL_S = 0.45, 0.35, 1.25
    duration = RISE_S + WIND_S + FALL_S
    GRAVITY = 0.055

    # Ralph mid-swing: spiky dark-red hair, big pink fists, red shirt, overalls.
    # '.' empty, H hair, F face/skin, E eye, A teeth, M mouth, S shirt, O overalls,
    # B buckle, K outline.
    ART = [
        ".......KHKHKHKHK.......",
        ".......KHHHHHHHK.......",
        "KKKKKK.KHHHHHHHK.KKKKKK",
        "KFFFFK.KHFFFFFHK.KFFFFK",
        "KFFFFK.KFFEFEFFK.KFFFFK",
        "KFFFFK.KFFFFFFFK.KFFFFK",
        ".KFFFK.KFFAAAFFK.KFFFK.",
        "..KFFK.KKFFFFFKK.KFFK..",
        "..KFFKKKKSSSSSK..KFFK..",
        "..KFFFFFSSSSSSSFFFFFK..",
        "...KFFFFSSSSSSSFFFFK...",
        "....KSSSSSSSSSSSSSK....",
        "....KSSSSOBBBOSSSSK....",
        ".....KSSOOBBBOOSSK.....",
        ".....KOOOOOOOOOOOK.....",
        ".....KOOOOOOOOOOOK.....",
        ".....KOOOOKKKOOOOK.....",
        ".....KFFFK...KFFFK.....",
        ".....KFFK.....KFFK.....",
        ".....KKKK.....KKKK.....",
    ]
    COLORS = {
        "H": (140, 25, 30),
        "F": (240, 180, 160),
        "E": (20, 20, 25),
        "M": (90, 30, 35),
        "S": (200, 40, 45),
        "O": (255, 220, 170),
        "B": (190, 120, 50),
        "K": (25, 15, 20),
        "A": (250, 250, 250),
    }

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.scale = 2 if height >= 64 else 1
        self.sprite_w = len(self.ART[0]) * self.scale
        self.sprite_h = len(self.ART) * self.scale
        self.debris = []
        self.shattered = False
        self._frames_stepped = 0
        self.prev_px = {}

    def _shatter(self):
        """Turn the captured screen into debris, thrown outward from the impact point."""
        self.shattered = True
        # The fists land centre-bottom; everything is flung away from that point.
        impact_x, impact_y = self.width / 2, self.height - self.sprite_h * 0.55
        for (x, y), rgb in self.prev_px.items():
            dx, dy = x - impact_x, y - impact_y
            dist = max(2.0, (dx * dx + dy * dy) ** 0.5)
            power = self.rng.uniform(1.2, 2.4) / dist * 14
            self.debris.append([
                float(x), float(y),
                dx / dist * power + self.rng.uniform(-0.2, 0.2),
                dy / dist * power - self.rng.uniform(0.2, 0.8),
                rgb,
            ])

    def ralph_y(self, t):
        """His top edge: rises into frame, holds through the swing, then drops away."""
        if t < self.RISE_S:
            return self.height - ease_out(t / self.RISE_S) * self.sprite_h
        if t < self.RISE_S + self.WIND_S:
            return self.height - self.sprite_h
        gone = (t - self.RISE_S - self.WIND_S) / self.FALL_S
        return self.height - self.sprite_h + ease_out(gone) * self.sprite_h

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        impact_at = self.RISE_S + self.WIND_S
        if not self.shattered and t >= impact_at:
            self._shatter()
        if t < impact_at:
            # Old screen still whole, with Ralph rising in front of it.
            paint(canvas, self.prev_px, self.width, self.height)
        else:
            self._step_debris(t - impact_at)
            for x, y, _, _, rgb in self.debris:
                px, py = int(round(x)), int(round(y))
                if 0 <= px < self.width and 0 <= py < self.height:
                    canvas.SetPixel(px, py, *rgb)
        self._draw_ralph(canvas, t)
        return True

    def _step_debris(self, since_impact):
        """Advance the falling pixels to the frame matching `since_impact` seconds."""
        target = int(since_impact * FPS)
        while self._frames_stepped < target:
            self._frames_stepped += 1
            for d in self.debris:
                d[0] += d[2]
                d[1] += d[3]
                d[3] += self.GRAVITY

    def _draw_ralph(self, canvas, t):
        y0 = self.ralph_y(t)
        x0 = int(self.width / 2 - self.sprite_w / 2)
        paint(canvas, art_pixels(self.ART, x0, int(round(y0)), self.COLORS, self.scale), self.width, self.height)
