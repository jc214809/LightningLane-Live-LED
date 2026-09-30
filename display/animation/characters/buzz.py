from display.animation.drawing import _blackout_rows
from display.animation.mechanics import FlyByReveal
from display.animation.motion import ease_out


class BuzzReveal(FlyByReveal):
    """
    Buzz Lightyear launches, to infinity: drawn front-on from a photo of the toy, he rises
    from below the board on a rocket flame under his feet, hovers while his wings snap open
    with a flash at their tips (his wing-release button), then blasts off the top. The new
    screen is uncovered from the bottom up behind him. Front-on he read as a cutout sliding
    sideways when he crossed the board like the other fly-bys; rising, facing us is natural.
    """

    RISE_S, HOVER_S, BLAST_S = 0.5, 0.3, 0.8
    duration = RISE_S + HOVER_S + BLAST_S
    FLASH_S = 0.15
    HOVER_AT = 0.55  # his centre while he hovers, as a fraction of the board's height
    SIZES = {
        "big": [
            "......DDD......",
            ".....DPPPD.....",
            ".....PSSSP.....",
            ".....PSSSP.....",
            "......PSP......",
            "RWRWRWGGGWRWRWR",
            "PPPPPWWBWWPPPPP",
            ".PPPPWGWGWPPPP.",
            "....WWWWWWW....",
            "....W.KKK.W....",
            ".....WW.WW.....",
            ".....WW.WW.....",
            ".....GP.PG.....",
        ],
        "small": [
            "....DDD....",
            "....PSP....",
            "....PSP....",
            "RWRWGGGWRWR",
            "PPPPWBWPPPP",
            ".PP.WGW.PP.",
            "....WWW....",
            "....W.W....",
            "....G.G....",
        ],
    }
    # Big on 64x32; on 64x64 the small one, doubled (22x18): the big one doubled is 30x26
    # and fills too much of the board. Set SIZE to "big" or "small" to pin one everywhere.
    SIZE = None
    art = SIZES["big"]
    colors = {"D": (130, 180, 235), "P": (160, 90, 235), "S": (255, 205, 170), "R": (235, 45, 45),
              "W": (235, 235, 245), "G": (60, 210, 60), "B": (60, 130, 255), "K": (70, 70, 80)}
    flame_colors = [(255, 240, 150), (255, 170, 30), (255, 90, 20), (230, 40, 20)]
    FLASH_RGB = (255, 250, 220)

    def __init__(self, width, height, rng=None):
        self.art = self.SIZES[self.SIZE or ("small" if height >= 64 else "big")]
        super().__init__(width, height, rng)
        # Wings tucked behind him: only what's within a column of his body shows.
        body = [c for row in self.art for c, ch in enumerate(row) if ch in "SDBK"]
        lo, hi = min(body) - 1, max(body) + 1
        self.folded = ["".join(ch if lo <= c <= hi else "." for c, ch in enumerate(row)) for row in self.art]
        self.wing_tips = [(c, r) for r, row in enumerate(self.art) for c, ch in enumerate(row)
                          if ch in "PR" and (c == 0 or c == len(row) - 1 or row[c - 1] == "." or row[c + 1] == ".")
                          and not lo <= c <= hi]

    def wings_open(self, t):
        return t >= self.RISE_S

    def position(self, t):
        """Top-left of his sprite: up from below the board, a hover, then accelerating off the top."""
        x = (self.width - self.sprite_w) / 2
        hover = self.height * self.HOVER_AT - self.sprite_h / 2
        if t < self.RISE_S:
            start = self.height
            return x, start + (hover - start) * ease_out(t / self.RISE_S)
        if t < self.RISE_S + self.HOVER_S:
            return x, hover
        p = min(1.0, (t - self.RISE_S - self.HOVER_S) / self.BLAST_S)
        return x, hover + (-self.sprite_h - hover) * p * p

    def spawn(self, x, y):
        """Rocket flame from under his feet, streaming down; heavier once he blasts off."""
        r = self.rng
        blasting = y < self.height * self.HOVER_AT - self.sprite_h / 2 - 0.5
        feet = y + self.sprite_h
        return [[x + self.sprite_w * r.uniform(0.38, 0.62), feet,
                 r.uniform(-0.25, 0.25) * self.scale, r.uniform(0.4, 1.0) * self.scale,
                 r.randint(10, 18), r.choice(self.flame_colors)]
                for _ in range((6 if blasting else 4) * self.scale)]

    def overlay(self, canvas, t):
        self._step_particles(t)
        if t < self.duration:
            # Uncovered from the bottom up: everything above his feet is still dark.
            _, y = self.position(t)
            _blackout_rows(canvas, 0, min(self.height, int(y + self.sprite_h)), self.width)
        for px, py, _, _, life, rgb in self.particles:
            f = min(1.0, life / 12)
            px, py = int(round(px)), int(round(py))
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *(int(c * f) for c in rgb))
        if t < self.duration:
            self._draw_sprite(canvas, t)
        return t < self.duration or bool(self.particles)

    def _draw_sprite(self, canvas, t):
        art = self.art
        if not self.wings_open(t):
            self.art = self.folded
        super()._draw_sprite(canvas, t)
        self.art = art
        since = t - self.RISE_S
        if 0 <= since < self.FLASH_S:
            # The snap: a burst of light off each wing tip.
            x0, y0 = (int(round(v)) for v in self.position(t))
            reach = 1 + int(3 * since / self.FLASH_S)
            for c, r in self.wing_tips:
                cx, cy = x0 + c * self.scale + self.scale // 2, y0 + r * self.scale + self.scale // 2
                for dx, dy in ((reach, 0), (-reach, 0), (0, reach), (0, -reach)):
                    px, py = cx + dx * self.scale, cy + dy * self.scale
                    if 0 <= px < self.width and 0 <= py < self.height:
                        canvas.SetPixel(px, py, *self.FLASH_RGB)
