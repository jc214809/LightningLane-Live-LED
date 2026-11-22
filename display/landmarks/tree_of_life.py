import math

from display.landmarks.scene import Landmark, _noise


class TreeOfLifeLandmark(Landmark):
    """The Tree of Life: a broad clumped canopy on a flared, carved trunk, with fireflies."""

    CANOPY = [(40, 95, 45), (60, 125, 55), (85, 155, 75), (120, 180, 105)]

    def build(self):
        self.cx = self.width // 2
        self.trunk_top = int(self.height * 0.6)
        self._draw_trunk()
        self._draw_canopy()
        self._draw_branches()
        self.flies = [
            (self.rng.uniform(0, 2 * math.pi), self.rng.uniform(0.7, 1.25), self.rng.uniform(0, 2 * math.pi))
            for _ in range(10 * self.scale)
        ]

    def _draw_trunk(self):
        """Short and massive, flaring into wide roots at the ground."""
        s, w, h = self.scale, self.width, self.height
        top_half, base_half = w * 0.1, w * 0.27
        for y in range(self.trunk_top, h):
            p = (y - self.trunk_top) / max(1, h - 1 - self.trunk_top)
            half = top_half + (base_half - top_half) * p**2.2
            for x in range(int(self.cx - half), int(self.cx + half) + 1):
                twist = int(2 * s * math.sin(y / (3 * s) + x / (5 * s)))
                groove = (x + twist) % (3 * s) == 0
                self.put(self.base, x, y, self._trunk_rgb(p, groove, x // s, y // s))

    @staticmethod
    def _trunk_rgb(p, groove, noise_x, noise_y):
        """One trunk pixel: rocky at the roots (p is how far down the trunk, 0 to 1), grooved, or bark."""
        if p > 0.8 and _noise(noise_x, noise_y) > 0.55:
            return (175, 155, 130)
        if groove:
            return (125, 90, 62)
        shade = 0.85 + 0.25 * _noise(noise_x, noise_y)
        return tuple(min(255, int(c * shade)) for c in (200, 160, 118))

    def _draw_canopy(self):
        """A wide dome with a bumpy edge; clumps of greens, brighter on top."""
        s, w, h = self.scale, self.width, self.height
        self.canopy_c = (self.cx, int(h * 0.36))
        self.rx, self.ry = w * 0.46, h * 0.3
        cx, cy = self.canopy_c
        for y in range(0, int(cy + self.ry * 1.2) + 1):
            for x in range(w):
                nx, ny = (x - cx) / self.rx, (y - cy) / self.ry
                theta = math.atan2(ny, nx)
                edge = 1 + 0.07 * math.sin(5 * theta) + 0.05 * math.sin(11 * theta + 1)
                if ny > 0.55 - 0.25 * abs(nx):
                    continue  # ragged underside, so the branches show
                if nx * nx + ny * ny > edge * edge:
                    continue
                clump = _noise(x // (2 * s), y // (2 * s))
                level = min(3, max(0, int(clump * 3 + (0.6 - ny) * 1.0)))
                rgb = self.CANOPY[level]
                if _noise(x, y) > 0.93:
                    rgb = (170, 210, 150)
                self.put(self.base, x, y, rgb)

    def _draw_branches(self):
        """From the top of the trunk up into the canopy."""
        cx, cy = self.canopy_c
        branch = (105, 75, 50)
        for spread, rise in ((-0.75, 0.22), (-0.4, 0.3), (0.4, 0.3), (0.75, 0.22)):
            x_end, y_end = cx + spread * self.rx, cy + self.ry * rise
            steps = int(abs(x_end - self.cx) + self.trunk_top - y_end) + 1
            for i in range(steps):
                q = i / steps
                x = int(self.cx + (x_end - self.cx) * q)
                y = int(self.trunk_top + (y_end - self.trunk_top) * q)
                for d in range(self.scale):
                    self.put(self.base, x, y + d, branch)

    def animate(self, out, t):
        cx, cy = self.canopy_c
        for angle, dist, phase in self.flies:
            a = angle + t * 0.4
            x = int(cx + math.cos(a) * self.rx * dist)
            y = int(cy + math.sin(a * 1.3) * self.ry * dist * 1.2)
            level = (1 + math.sin(t * 6 + phase)) / 2
            if level > 0.3:
                self.put(out, x, y, (int(255 * level), int(240 * level), int(90 * level)))
