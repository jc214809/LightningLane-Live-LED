import math

from display.landmarks.scene import Landmark
from display.motion import ramp
from display.pixels import art_pixels, blend


class SpaceshipEarthLandmark(Landmark):
    """
    Spaceship Earth at night, lit by Tinker Bell. The sphere starts dark; Tink spirals up it
    from its legs in three even laps, passing behind it and in front, and each facet lights up in the Beacons
    of Magic colours (EPCOT's purples, blues, teals and pinks) as her pixie dust passes it.
    Then she flits to its shoulder, lands in a puff of sparkles and poses while the colours
    roll around the sphere.

    The facets are a triangle lattice wrapped onto the sphere (they shrink toward the rim,
    which is what makes it read as a ball of triangles, not grey noise), alternating lit and
    shaded like the photo's pyramid faces. Its leaning slab legs go behind it so it stays a
    perfect sphere. On 64x32 the sphere fills the board's height; on 64x64 it's big and low
    with the legs just peeking out. It plays under the wipe, like the pumpkin.
    """

    SCREEN_S = 4.5
    PLAYS_UNDER_WIPE = True
    SPIRAL_S = 2.8  # Tink's spiral from the legs to the top
    # Three even laps, whole ones, so she finishes right above where she started.
    TURNS = 3
    FLIT_S = 0.35  # from the top of her spiral to her perch on its shoulder
    FADE_S = 0.15  # a facet's fade-in as her dust reaches it
    LIGHT_S = SPIRAL_S + FADE_S  # by now every facet is lit
    DUST_LIFE, DUST_STEP = 0.5, 0.02  # how long a mote of pixie dust lasts, and how often she sheds a pair
    WAVE_HZ = 0.35  # turns of the colour wave around the sphere per second
    FACETS = {32: 7, 64: 9}  # facets across the sphere's diameter, per board
    PALETTE = ((150, 60, 230), (40, 100, 255), (0, 205, 200), (255, 70, 185))
    UNLIT_RGB = (26, 28, 44)  # the sphere before her dust reaches it: a dark silhouette
    LEG_RGB, LEG_LIT_RGB = (48, 54, 78), (110, 120, 160)
    PERCH_DEG = 50  # where she lands: this far from the top, on the sphere's right shoulder
    def build(self):
        from display.animation import TinkReveal
        tall = self.height >= 64
        if tall:
            # Big and low, like 64x32: the legs just peek out below it (about four rows).
            # Any taller and a sphere on legs reads as a water tower.
            self.r, self.cy = 28.5, 31.0
        else:
            self.r, self.cy = 15.6, 15.5  # fills the height; only the legs' tops show
        self.cx = self.width / 2 - 0.5
        # The park-title fly-by's Tink, at 1x on both boards: doubled she'd crowd the sphere.
        self.tink_art, self.tink_colors, self.tink_scale = TinkReveal.art, TinkReveal.colors, 1
        self.dust_colors = TinkReveal.dust_colors
        self.tink_w = len(self.tink_art[0]) * self.tink_scale
        self.tink_h = len(self.tink_art) * self.tink_scale
        self.a0 = math.pi / 3  # she starts, and after whole laps ends, front-right, below her perch
        k = self.FACETS[64 if tall else 32]
        facets = {}
        for y in range(self.height):
            for x in range(self.width):
                nx, ny = (x - self.cx) / self.r, (y - self.cy) / self.r
                d2 = nx * nx + ny * ny
                if d2 > 1:
                    continue
                nz = math.sqrt(1 - d2)
                lon = math.atan2(nx, nz)
                u = lon * k / math.pi  # across, in facet widths
                v = math.asin(ny) * k / math.pi * 1.15  # down, in facet heights
                row = math.floor(v)
                key = (row, math.floor(u + v / 2), math.floor(u - v / 2))
                facets.setdefault(key, []).append((x, y, nz, lon))
        self.facets = []
        for (row, a, b), cells in facets.items():
            up = (row + a + b) % 2 == 0
            n = len(cells)
            mean_y = sum(c[1] for c in cells) / n
            lon = sum(c[3] for c in cells) / n
            shade = 0.45 + 0.55 * sum(c[2] for c in cells) / n
            rise = (self.cy + self.r - mean_y) / (2 * self.r)  # 0 at the base, 1 at the top
            # When her dust reaches it: once she's climbed to its height, the next time she
            # comes round the front to its longitude.
            here = self.a0 + self.TURNS * 2 * math.pi * rise
            lit_at = min(1.0, rise + ((lon - here) % (2 * math.pi)) / (self.TURNS * 2 * math.pi))
            # About two-thirds of the palette spans the visible face, so the colours read as
            # bands rolling around the sphere rather than the whole ball changing at once.
            around = lon / math.pi * 0.65
            self.facets.append((cells, up, around, rise, shade, lit_at * self.SPIRAL_S))
        self.legs = self._build_legs()
        self.perch = self._perch()

    def _build_legs(self):
        """
        The two front legs: slanted slabs of even width leaning out from under the sphere to
        the ground (widening them made them read as searchlight beams), uplit on the outer edge.
        """
        s, r = self.scale, self.r
        out = {}
        ground = self.height - 1
        width = r * 0.3
        for side in (-1, 1):
            top_x, top_y = self.cx + side * r * 0.5, self.cy + r * 0.7
            foot_x = self.cx + side * r * 0.95
            for y in range(int(top_y), ground + 1):
                p = (y - top_y) / max(1.0, ground - top_y)
                outer = top_x + (foot_x - top_x) * p
                inner = outer - side * width
                lo, hi = sorted((outer, inner))
                for x in range(int(round(lo)), int(round(hi)) + 1):
                    lit = abs(x - outer) < 1.2 * s
                    self.put(out, x, y, self.LEG_LIT_RGB if lit else self.LEG_RGB)
        return out

    def _perch(self):
        """Her centre when she's standing on the sphere's right shoulder, feet on its rim."""
        a = math.radians(self.PERCH_DEG)
        rim_x, rim_y = self.cx + self.r * math.sin(a), self.cy - self.r * math.cos(a)
        return rim_x, max(self.tink_h / 2, rim_y - self.tink_h / 2 + 1)

    def angle(self, p):
        """Her angle round the sphere at spiral progress p: 0 faces us, positive to the right."""
        return self.a0 + self.TURNS * 2 * math.pi * p

    def tink_at(self, t):
        """(x, y, in_front) of Tink's centre at scene time t."""
        if t < self.SPIRAL_S:
            p = max(0.0, t / self.SPIRAL_S)
            angle = self.angle(p)
            lat = 1 - 2 * p  # +1 at the base, -1 at the top
            y = self.cy + self.r * 0.92 * lat + self.r * 0.08 * math.cos(angle)  # a slightly tilted orbit
            reach = self.r * 1.15 * max(0.35, math.sqrt(max(0.0, 1 - (0.92 * lat) ** 2)))
            return self.cx + reach * math.sin(angle), y, math.cos(angle) > 0
        top = self.tink_at(self.SPIRAL_S - 1e-6)
        p = min(1.0, (t - self.SPIRAL_S) / self.FLIT_S)
        e = 1 - (1 - p) ** 2
        x = top[0] + (self.perch[0] - top[0]) * e
        y = top[1] + (self.perch[1] - top[1]) * e - math.sin(p * math.pi) * 3 * self.scale  # a little hop over
        if p >= 1:
            y += round(math.sin((t - self.SPIRAL_S - self.FLIT_S) * 5)) * 0.8  # bobbing as she poses
        return x, y, True

    def _palette(self, h):
        h %= 1.0
        n = len(self.PALETTE)
        # Wrap the index too: a hair below zero, h % 1.0 is exactly 1.0 (the facet dead centre
        # of the sphere does that on some platforms), which would index past the palette.
        i, f = int(h * n) % n, (h * n) % 1
        a, b = self.PALETTE[i], self.PALETTE[(i + 1) % n]
        return tuple(int(x + (y - x) * f) for x, y in zip(a, b))

    def _on_sphere(self, x, y):
        return (x - self.cx) ** 2 + (y - self.cy) ** 2 <= self.r * self.r

    def animate(self, out, t):
        # The legs go behind the sphere: they come out from under it and never cut into
        # its outline, so it stays a perfect sphere.
        out.update(self.legs)
        for facet in self.facets:
            rgb = self.facet_rgb(facet, t)
            for x, y, _, _ in facet[0]:
                out[(x, y)] = rgb
        self._draw_dust(out, t)
        self._draw_landing_burst(out, t)
        x, y, front = self.tink_at(t)
        self._draw_tink(out, x, y, front)

    def facet_rgb(self, facet, t):
        """A facet's colour at t: dark until her dust reaches it, then its place in the colour wave."""
        cells, up, around, rise, shade, lit_at = facet
        on = ramp(t, lit_at, self.FADE_S)
        colour = self._palette(around + t * self.WAVE_HZ)
        k = shade * (1.0 if up else 0.38)  # lit and shaded pyramid faces, as in the photo
        lit = tuple(int(c * k) for c in colour)
        dark = tuple(int(c * shade) for c in self.UNLIT_RGB)
        return tuple(int(d + (l - d) * on) for d, l in zip(dark, lit))

    def _draw_dust(self, out, t):
        """
        Pixie dust shed along her path, drifting down and fading. Each mote is placed from
        the moment it was shed, so a frame depends only on t.
        """
        last = min(t, self.SPIRAL_S + self.FLIT_S)
        k = int(max(0.0, t - self.DUST_LIFE) / self.DUST_STEP)
        while k * self.DUST_STEP <= last:
            born = k * self.DUST_STEP
            age = t - born
            if 0 <= age < self.DUST_LIFE:
                bx, by, front = self.tink_at(born)
                for j in (0, 1):  # a pair of motes each time, scattered differently
                    seed = 2 * k + j
                    jx = ((seed * 7919) % 11 - 5) / 5 * self.tink_w * 0.45
                    jy = ((seed * 104729) % 7 - 3) / 3 * self.tink_h * 0.35
                    x = int(round(bx + jx))
                    y = int(round(by + jy + age * 6 * self.scale))
                    if front or not self._on_sphere(x, y):
                        self._blend(out, x, y, self.dust_colors[seed % len(self.dust_colors)], 1 - age / self.DUST_LIFE)
            k += 1

    def _draw_landing_burst(self, out, t):
        """A ring of sparkles as she lands on her perch."""
        landed = t - self.SPIRAL_S - self.FLIT_S
        if not 0 <= landed < 0.5:
            return
        px, py = self.perch
        radius = (2 + landed * 14) * self.scale
        for i in range(8):
            a = i * math.pi / 4
            self._blend(out, int(round(px + radius * math.cos(a))), int(round(py + radius * math.sin(a))),
                        self.dust_colors[i % len(self.dust_colors)], 1 - landed / 0.5)

    def _draw_tink(self, out, cx, cy, front):
        x0, y0 = int(round(cx - self.tink_w / 2)), int(round(cy - self.tink_h / 2))
        for (x, y), rgb in art_pixels(self.tink_art, x0, y0, self.tink_colors, self.tink_scale):
            if front or not self._on_sphere(x, y):  # hidden while she's behind it
                self.put(out, x, y, rgb)

    def _blend(self, out, x, y, rgb, alpha):
        if 0 <= x < self.width and 0 <= y < self.height and alpha > 0:
            out[(x, y)] = blend(rgb, out.get((x, y), (0, 0, 0)), alpha)
