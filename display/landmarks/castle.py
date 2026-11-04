from display.fireworks.fireworks import _CASTLE_COLORS, castle_sprite

from display.landmarks.scene import LANDMARK_S, Landmark


class CastleLandmark(Landmark):
    """The castle under a starry sky, with a shooting star crossing overhead."""

    def build(self):
        pixels, w, h = castle_sprite(self.height)
        x0, y0 = (self.width - w) // 2, self.height - h
        for dx, dy, kind in pixels:
            self.put(self.base, x0 + dx, y0 + dy, _CASTLE_COLORS[kind])
        self.sky_bottom = y0

    def animate(self, out, t):
        p = (t % LANDMARK_S) / 1.4
        if p > 1:
            return
        # A shooting star from upper right to lower left above the spires, with a fading tail.
        for i in range(6 * self.scale):
            q = p - i * 0.02
            if q < 0:
                continue
            x = int(self.width * (0.95 - 0.8 * q))
            y = int(self.height * 0.05 + self.sky_bottom * 0.5 * q)
            f = 1 - i / (6 * self.scale)
            self.put(out, x, y, (int(255 * f), int(250 * f), int(200 * f)))
