from display.animation.characters.mike import MikeReveal
from display.motion import ease_out
from display.fireworks.actors.base import Actor


class MikePeeks(Actor):
    """
    That's What Friends Are For: Mike Wazowski (drawn by his ride reveal's MikeReveal, smaller) pops up
    from behind the castle's left side turret, blinks, looks left and right, grins wider, blinks again and
    ducks back down; halfway through he does it again from the right turret. He's behind the turret: only
    the part of him above its walls is drawn, and its roof and the castle cover him where they are.
    """
    # His body's half-width by board height: a size smaller than his ride reveal (8 and 12), so his eye
    # and grin clear the turret roof without his shoulders swallowing the centre tower.
    NAME = "Mike"
    SIZES = {32: 6, 64: 10}
    VISIT_S = 6.0  # one peek, up to down; the second starts at VISIT_S + GAP_S
    GAP_S = 0.5
    UP_S, DOWN_S = 0.5, 0.6
    # Offsets that slide MikeReveal's own BLINK/LOOK/GRIN windows into a peek.
    BLINK_AT = (0.45, 3.5)  # his blink (0.55 s in) shifted later, twice
    LOOK_AT = 0.75  # his look (0.95-1.85) starts at 1.7
    GRIN_AT = 0.95  # his grin widens at 2.8-3.1 and stays wide

    def __init__(self, show):
        super().__init__(show)
        self.reveal = MikeReveal(show.width, show.height, self.rng)
        self.reveal.r = self.SIZES[64 if self.big else 32]
        self.reveal.ry = self.reveal.r * 1.08
        self.castle = {(show.castle_x + dx, show.castle_y + dy) for dx, dy, _ in show.castle_pixels}
        self.turrets = self._turrets()
        self.bodies = {}

    def _turrets(self):
        """(x, wall top y) of the side turrets nearest the spire, left then right: under each of their
        gold finials, the first row below its roof."""
        show = self.show
        kinds = {(dx, dy): k for dx, dy, k in show.castle_pixels}
        spire_dx = show.spire[0] - show.castle_x
        golds = sorted({dx for (dx, dy), k in kinds.items() if k == "G" and abs(dx - spire_dx) > 2})
        found = []
        for side in (-1, 1):
            cols = [dx for dx in golds if (dx - spire_dx) * side > 0]
            dx = max(cols) if side < 0 else min(cols)
            # A 64-row castle doubles each cell: take the finial's left column on both sides.
            if side < 0 and self.big and (dx - 1) in golds:
                dx -= 1
            dy = min(y for (x, y), k in kinds.items() if x == dx and k == "G")
            while kinds.get((dx, dy)) in ("G", "R"):
                dy += 1
            wide = 2 if self.big else 1  # the doubled finial's centre sits between its two columns
            found.append((show.castle_x + dx + (wide - 1) / 2, show.castle_y + dy))
        return found

    def visit(self, e):
        """(turret index, seconds into that peek), or None between and after peeks."""
        for i in range(2):
            tau = e - i * (self.VISIT_S + self.GAP_S)
            if 0 <= tau < self.VISIT_S:
                return i, tau
        return None

    def rise(self, tau):
        """0 hidden behind the turret, 1 all the way up."""
        if tau < self.UP_S:
            return ease_out(tau / self.UP_S)
        down = tau - (self.VISIT_S - self.DOWN_S)
        return 1.0 if down < 0 else max(0.0, 1.0 - ease_out(down / self.DOWN_S))

    def pose(self, tau):
        """(look, lid, grin) as MikeReveal's, rounded so a few bodies are cached."""
        m = self.reveal
        lid = max(m.lid(tau - at) for at in self.BLINK_AT)
        return round(m.look(tau - self.LOOK_AT) * 4) / 4, round(lid * 4) / 4, round(m.grin(tau - self.GRIN_AT) * 4) / 4

    def pixels(self):
        """His visible pixels now, {(x, y): rgb}: above the turret's walls, not where the castle is."""
        at = self.visit(self.elapsed())
        if at is None:
            return {}
        i, tau = at
        rise = self.rise(tau)
        if rise <= 0:
            return {}
        x, line = self.turrets[i]
        m = self.reveal
        # Up: his grin's bottom just above the roof's foot; down: his horns below it.
        up_cy = line - m.r * 0.95
        down_cy = line + m.ry + 4
        cy = round(down_cy + (up_cy - down_cy) * rise)
        cx = round(x)
        key = self.pose(tau)
        body = self.bodies.get(key)
        if body is None:
            body = self.bodies[key] = m._body(False, *key)
        w, h = self.show.width, self.show.height
        out = {}
        for (bx, by), rgb in body.items():
            px, py = cx + bx, cy + by
            if py < line and 0 <= px < w and 0 <= py < h and (px, py) not in self.castle:
                out[(px, py)] = rgb
        return out

    def draw(self, put, out, active):
        if active:
            out.update(self.pixels())
