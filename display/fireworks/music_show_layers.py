"""
The layers of a music show's frame: the sky (stars, sparks, rockets, lanterns, embers, the wishing
star, Tink's dust), the castle, Tink and the white flash, each drawn onto the {(x, y): rgb} dict that
MusicShow.frame_pixels builds. Split out of music_show.py, whose MusicShow takes them as methods.
"""

import math

from display.animation.characters.tink import TinkReveal
from display.motion import smooth

_STAINED_GLASS = ((255, 200, 60), (70, 120, 255), (220, 50, 60), (255, 230, 140))
_FLICKERS = {"fire"}
CASTLE_FADE_S = 1.5
# "wipe_down": the scene's castle change runs from the spire down to the base over WIPE_S instead
# (the theme chorus's slow fade to blue): the top row is done halfway through, the bottom row starts then.
WIPE_S = 8.0
_LIT_KINDS = {"W", "R"}
WISH_RGB, WISH_GLOW_RGB = (255, 255, 230), (255, 220, 120)
LANTERN_RGB = (255, 150, 40)
EMBER_RGB = (255, 70, 20)


def _plotter(out, width, height):
    """A put(x, y, rgb) that lights a pixel of `out`, keeping the brighter channels where two meet."""
    seen = out.get

    # Called for every lit LED of every frame, so it's written out long-hand: a Pi Zero spends
    # most of a frame here.
    def put(x, y, rgb):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < width and 0 <= yi < height:
            prev = seen((xi, yi))
            if prev:
                rgb = (max(prev[0], rgb[0]), max(prev[1], rgb[1]), max(prev[2], rgb[2]))
            out[(xi, yi)] = rgb

    return put


class _CastleFrame:
    """This frame's castle: its colours, stage level (`shown`), stained-glass blend, whether it
    flickers, and how far through a wipe it is (None when not wiping). A lit colour and a dimmed one
    depend only on the colour going in (and this frame's flash and stage level), so each is worked
    out once a frame, not once an LED: the castle is most of a frame's LEDs."""

    def __init__(self, flash, shown, colours, glass, flicker, wipe):
        self.flash, self.shown = flash, shown
        self.colours, self.glass, self.flicker, self.wipe = colours, glass, flicker, wipe
        self._lit, self._dimmed = {}, {}

    def glowing(self, base):
        glow = self._lit.get(base)
        if glow is None:
            fr, fg, fb = self.flash
            glow = self._lit[base] = (
                min(255, int(base[0] * 0.75 + 110 * fr)),
                min(255, int(base[1] * 0.75 + 110 * fg)),
                min(255, int(base[2] * 0.75 + 110 * fb)),
            )
        return glow

    def dim(self, base):
        low = self._dimmed.get(base)
        if low is None:
            shown = self.shown
            low = self._dimmed[base] = (int(base[0] * shown), int(base[1] * shown), int(base[2] * shown))
        return low


class FrameLayers:
    """MusicShow's drawing methods: each takes the frame's put (and out) and adds its layer."""

    def _draw_stars(self, put):
        for sx, sy in self.stars:
            twinkle = 25 + int(25 * self.rng.random())
            put(sx, sy, (twinkle, twinkle, twinkle + 10))

    def _draw_sparks(self, put):
        for s in self.sparks:
            f = s.life / s.max_life
            hot = max(0.0, (f - 0.8) / 0.2)
            r, g, b = s.color
            put(
                s.x,
                s.y,
                (int((r + (255 - r) * hot) * f), int((g + (255 - g) * hot) * f), int((b + (255 - b) * hot) * f)),
            )
            if f > 0.5:
                put(s.x - s.vx * 1.5, s.y - s.vy * 1.5, (int(r * f * 0.35), int(g * f * 0.35), int(b * f * 0.35)))

    def _draw_rockets(self, put):
        for r in self.rockets:
            put(r.x, r.y, (255, 230, 180))
            put(r.x, r.y + 1, (140, 90, 40))
            put(r.x, r.y + 2, (50, 30, 10))

    def _draw_lanterns(self, put):
        # A lantern is a glowing body (2 LEDs tall, 2x2 on a 64-row board) over a dim halo.
        size = 2 if self.height >= 64 else 1
        for x, y, _, phase in self.lanterns:
            glow = 0.8 + 0.2 * math.sin(self.frame * 0.2 + phase)
            lx = int(round(x + 0.6 * math.sin(self.frame * 0.05 + phase)))
            ly = int(round(y))
            halo = tuple(int(c * glow * 0.25) for c in LANTERN_RGB)
            for dx in range(-1, size + 1):
                for dy in range(-1, 3):
                    put(lx + dx, ly + dy, halo)
            body = tuple(int(c * glow) for c in LANTERN_RGB)
            for dx in range(size):
                for dy in range(2):
                    put(lx + dx, ly + dy, body)

    def _draw_embers(self, put):
        for x, y, _, _, life, max_life in self.embers:
            put(x, y, tuple(int(c * life / max_life) for c in EMBER_RGB))

    def _draw_wishing_star(self, put):
        if "wishing_star" not in self.effects or self.cue is None:
            return
        p = self.cue.progress(self.t)
        for k in range(6, 0, -1):  # a fading trail behind it
            tx, ty = self._wish_path(max(0.0, p - k * 0.02))
            put(tx, ty, tuple(int(c * (1 - k / 7) * 0.5) for c in WISH_GLOW_RGB))
        x, y = self._wish_path(p)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            put(x + dx, y + dy, WISH_GLOW_RGB)
        put(x, y, WISH_RGB)

    def _draw_dust(self, put):
        for x, y, _, _, life, max_life, rgb in self.dust:
            put(x, y, tuple(int(c * life / max_life) for c in rgb))

    def _draw_castle(self, put, out):
        """The castle hides anything launched from behind it; Tink and the effects' fronts don't. Dimmed
        for a stage, it's a ghost the sky shows through; gone, it hides nothing."""
        shown = self.castle_level()
        colours = self._castle_now()
        flicker = self.castle_look in _FLICKERS
        wipe = (self.t - self.castle_change_t) / WIPE_S if self.castle_wipe else 1.0
        wiping = 0 <= wipe < 1
        glass = smooth((self.t - self.castle_change_t) / CASTLE_FADE_S) if self.castle_look == "stained_glass" else 0
        castle = _CastleFrame(self.flash, shown, colours, glass, flicker, wipe if wiping else None)
        if shown > 0.01 and not flicker and not wiping:
            self._draw_kept_castle(out, castle)
        else:
            self._draw_live_castle(put, out, castle)

    def _draw_kept_castle(self, out, castle):
        colours, shown, glass, tints = castle.colours, castle.shown, castle.glass, castle
        # Without the fire's flicker every LED of a kind (or of a stained-glass tile) is one colour,
        # and from one frame to the next usually the same one: the finished castle is kept and
        # reused while its colours hold.
        finals = {}
        for kind, base in colours.items():
            finals[kind] = tints.glowing(base) if kind in _LIT_KINDS else base
        if glass:
            for i, tile in enumerate(_STAINED_GLASS):
                base = tuple(int(a + (b - a) * glass) for a, b in zip(colours["W"], tile))
                finals[("W", i)] = tints.glowing(base) if "W" in _LIT_KINDS else base
        if shown < 1:
            finals = {k: tints.dim(rgb) for k, rgb in finals.items()}
        key = (tuple(sorted((str(k), rgb) for k, rgb in finals.items())), shown < 1, id(self.castle_shape))
        if key != self._castle_key:
            self._castle_key, self._castle_layer = key, self._castle_layer_for(finals, glass)
        if shown < 1:
            seen = out.get
            for xy, rgb in self._castle_layer.items():
                prev = seen(xy)
                out[xy] = (max(prev[0], rgb[0]), max(prev[1], rgb[1]), max(prev[2], rgb[2])) if prev else rgb
        else:
            out.update(self._castle_layer)

    def _castle_layer_for(self, finals, glass):
        """The castle's pixels in their finished colours, {(x, y): rgb}."""
        layer = {}
        for dx, dy, kind in self.castle_shape or self.castle_pixels:
            x, y = self.castle_x + dx, self.castle_y + dy
            if 0 <= x < self.width and 0 <= y < self.height:
                if kind == "W" and glass:
                    kind = ("W", (dx // (2 * self.scale) * 3 + dy // (2 * self.scale)) % 4)
                layer[(x, y)] = finals[kind]
        return layer

    def _draw_live_castle(self, put, out, castle):
        """The castle worked out LED by LED: while it flickers or wipes, no two frames match."""
        colours, shown, glass, tints = castle.colours, castle.shown, castle.glass, castle
        flicker, wipe = castle.flicker, castle.wipe
        rows = {}  # a wipe's colours for each row of the castle, worked out once a frame
        for dx, dy, kind in (self.castle_shape or self.castle_pixels) if shown > 0.01 else ():
            x, y = self.castle_x + dx, self.castle_y + dy
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue
            base = self._wipe_row(rows, dy, wipe)[kind] if wipe is not None else colours[kind]
            if kind == "W" and glass:
                tile = _STAINED_GLASS[(dx // (2 * self.scale) * 3 + dy // (2 * self.scale)) % 4]
                base = tuple(int(a + (b - a) * glass) for a, b in zip(base, tile))
            if kind in _LIT_KINDS and flicker:
                # Each LED on its own phase (a hash of its spot), so the fire doesn't band.
                level = 0.75 + 0.25 * math.sin(self.frame * 0.7 + (dx * 7919 + dy * 104729) % 628 / 100)
                base = tints.glowing((int(base[0] * level), int(base[1] * level), int(base[2] * level)))
            elif kind in _LIT_KINDS:
                base = tints.glowing(base)
            if shown < 1:
                put(x, y, tints.dim(base))
            else:
                out[(x, y)] = base

    def _wipe_row(self, rows, dy, wipe):
        row = rows.get(dy)
        if row is None:
            f = smooth(wipe * 2 - dy / self.castle_h)
            row = rows[dy] = {
                k: tuple(int(a + (b - a) * f) for a, b in zip(self.castle_from[k], to))
                for k, to in self.castle_to.items()
            }
        return row

    def _draw_tink(self, out):
        tink = self.tink_at()
        if not tink:
            return
        left = int(round(tink[0] - self.tink_w / 2))
        top = int(round(tink[1] - self.tink_h / 2))
        for row, line in enumerate(TinkReveal.art):
            for col, key in enumerate(line):
                if key == ".":
                    continue
                for oy in range(self.tink_scale):
                    for ox in range(self.tink_scale):
                        x, y = left + col * self.tink_scale + ox, top + row * self.tink_scale + oy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            out[(x, y)] = TinkReveal.colors[key]

    def _draw_white(self, out):
        level = int(255 * min(1.0, self.white))
        # Every pixel at least `level` on each channel. Written as plain loops, not a tuple(max(...)
        # for ...) per pixel: this is the biggest frame of the show, and the Pi's build time was in it.
        for pos, (r, g, b) in out.items():
            out[pos] = (r if r > level else level, g if g > level else level, b if b > level else level)
        blank = (level, level, level)
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in out:
                    out[(x, y)] = blank
