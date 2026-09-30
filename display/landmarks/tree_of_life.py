import math

from display.landmarks.scene import Landmark, _noise


class TreeOfLifeLandmark(Landmark):
    """The Tree of Life: a broad clumped canopy on a flared, carved trunk, with fireflies."""

    CANOPY = [(40, 95, 45), (60, 125, 55), (85, 155, 75), (120, 180, 105)]

    def build(self):
        s = self.scale
        w, h = self.width, self.height
        self.cx = w // 2
        self.trunk_top = int(h * 0.6)
        # Trunk: short and massive, flaring into wide roots at the ground.
        top_half, base_half = w * 0.1, w * 0.27
        for y in range(self.trunk_top, h):
            p = (y - self.trunk_top) / max(1, h - 1 - self.trunk_top)
            half = top_half + (base_half - top_half) * p ** 2.2
            for x in range(int(self.cx - half), int(self.cx + half) + 1):
                twist = int(2 * s * math.sin(y / (3 * s) + x / (5 * s)))
                groove = (x + twist) % (3 * s) == 0
                if p > 0.8 and _noise(x // s, y // s) > 0.55:
                    rgb = (175, 155, 130)  # rocky roots at the base
                elif groove:
                    rgb = (125, 90, 62)
                else:
                    shade = 0.85 + 0.25 * _noise(x // s, y // s)
                    rgb = tuple(min(255, int(c * shade)) for c in (200, 160, 118))
                self.put(self.base, x, y, rgb)
        # Canopy: a wide dome with a bumpy edge; clumps of greens, brighter on top.
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
        # Branches from the top of the trunk up into the canopy.
        branch = (105, 75, 50)
        for spread, rise in ((-0.75, 0.22), (-0.4, 0.3), (0.4, 0.3), (0.75, 0.22)):
            x_end, y_end = cx + spread * self.rx, cy + self.ry * rise
            steps = int(abs(x_end - self.cx) + self.trunk_top - y_end) + 1
            for i in range(steps):
                q = i / steps
                x = int(self.cx + (x_end - self.cx) * q)
                y = int(self.trunk_top + (y_end - self.trunk_top) * q)
                for d in range(s):
                    self.put(self.base, x, y + d, branch)
        self.flies = [(self.rng.uniform(0, 2 * math.pi), self.rng.uniform(0.7, 1.25), self.rng.uniform(0, 2 * math.pi))
                      for _ in range(10 * s)]

    def animate(self, out, t):
        cx, cy = self.canopy_c
        for angle, dist, phase in self.flies:
            a = angle + t * 0.4
            x = int(cx + math.cos(a) * self.rx * dist)
            y = int(cy + math.sin(a * 1.3) * self.ry * dist * 1.2)
            level = (1 + math.sin(t * 6 + phase)) / 2
            if level > 0.3:
                self.put(out, x, y, (int(255 * level), int(240 * level), int(90 * level)))
