import math

from display.animation.characters.ralph import RalphReveal
from display.fireworks.actors.base import Actor, stamp
from display.motion import ease_out


class RalphSmashes(Actor):
    """
    Friendship mash-up, elapsed 0-14 s: Wreck-It Ralph (his ride-reveal art, 1x on both boards) walks in
    from the left to the bottom centre in the first second, then 8-bit bricks fall from the top, one at a
    time, alternately over each fist. As one reaches him he throws his fists up (UP_ART on 64x64,
    SHOULDER_ART on 64x32, as in his reveal) and it bursts into pieces that fall away. In his last second
    he drops off the bottom of the board. Everything, pieces included, is placed by the clock.
    """
    NAME = "Ralph"
    START_S, END_S = 0.0, 14.0
    ENTERS_S = START_S
    WALK_S = 1.0
    DROP_S = 1.0  # he drops away at the end of his window
    FIRST_HIT_S, HIT_EVERY_S = 1.8, 1.0
    FALL_S = 0.9  # each brick's fall, top of the board to his fist
    SWING_BEFORE_S, SWING_AFTER_S = 0.18, 0.22  # fists up around each hit
    PIECES_S = 1.4
    BRICK = ["RRD", "DRR"]  # a 3x2 8-bit brick: shirt red with dark mortar
    BRICK_COLORS = [
        {"R": RalphReveal.COLORS["R"], "D": RalphReveal.COLORS["D"]},
        {"R": RalphReveal.COLORS["H"], "D": RalphReveal.COLORS["K"]},
        {"R": RalphReveal.COLORS["P"], "D": RalphReveal.COLORS["R"]},
    ]

    def __init__(self, show):
        super().__init__(show)
        self.stand = RalphReveal.STAND_ART
        self.raised = RalphReveal.UP_ART if self.big else RalphReveal.SHOULDER_ART
        self.w, self.h = len(self.stand[0]), len(self.stand)
        # His feet on the bottom row; on 64x32 the outline under them hangs off it, as in his reveal.
        self.ground = show.height - self.h + (0 if self.big else 1)
        self.mid = (show.width - self.w) // 2
        rw, rh = len(self.raised[0]), len(self.raised)
        self.raised_left = self.mid - (rw - self.w) // 2
        self.raised_top = self.ground - (rh - self.h)
        fist_row = 0 if self.big else 8  # the fists' top row in the raised art
        fist_cols = (3.5, rw - 4.5)
        self.gravity = 60.0 * show.height / 32  # px/s^2 for the pieces
        bw, bh = len(self.BRICK[0]), len(self.BRICK)
        self.land_top = self.raised_top + fist_row - bh
        # Each brick: (hit time, left, colours, pieces as (dx, dy, rgb, vx, vy)), fixed up front.
        self.bricks = []
        hit, i = self.FIRST_HIT_S, 0
        while hit < self.END_S - self.DROP_S - 0.3:
            left = int(round(self.raised_left + fist_cols[i % 2] - bw / 2))
            colors = self.BRICK_COLORS[i % len(self.BRICK_COLORS)]
            pieces = []
            for row, line in enumerate(self.BRICK):
                for col, kind in enumerate(line):
                    side = -1 if i % 2 == 0 else 1  # thrown outward, away from his head
                    pieces.append((col, row, colors[kind], side * self.rng.uniform(6, 22) + (col - 1) * 4,
                                   -self.rng.uniform(10, 28) * show.height / 32))
            self.bricks.append((hit, left, colors, pieces))
            hit += self.HIT_EVERY_S
            i += 1

    def on(self, e):
        return self.START_S <= e < self.END_S

    def left_top(self, e):
        """His standing art's top-left e seconds in: walking in, at the bottom centre, then dropping away."""
        left = self.mid
        if e < self.WALK_S:
            left = -self.w + ease_out(e / self.WALK_S) * (self.mid + self.w)
        top = self.ground
        drop = e - (self.END_S - self.DROP_S)
        if drop > 0:
            p = drop / self.DROP_S
            top += p * p * (self.show.height - self.ground + 1)
        return int(round(left)), int(round(top))

    def swinging(self, e):
        return any(hit - self.SWING_BEFORE_S <= e < hit + self.SWING_AFTER_S for hit, *_ in self.bricks)

    def draw(self, put, out, active):
        if not active:
            return
        e = self.elapsed()
        if not self.on(e):
            return
        show = self.show
        W, H = show.width, show.height
        left, top = self.left_top(e)
        if self.swinging(e):
            stamp(out, self.raised, RalphReveal.COLORS, left - (self.mid - self.raised_left),
                  top - (self.ground - self.raised_top), 1, W, H)
        else:
            stamp(out, self.stand, RalphReveal.COLORS, left, top, 1, W, H)
        for hit, bx, colors, pieces in self.bricks:
            if hit - self.FALL_S <= e < hit:
                p = (e - (hit - self.FALL_S)) / self.FALL_S
                by = -len(self.BRICK) + p * p * (self.land_top + len(self.BRICK))
                stamp(out, self.BRICK, colors, bx, by, 1, W, H)
            elif hit <= e < hit + self.PIECES_S:
                dt = e - hit
                for dx, dy, rgb, vx, vy in pieces:
                    x = math.floor(bx + dx + vx * dt + 0.5)
                    y = math.floor(self.land_top + dy + vy * dt + 0.5 * self.gravity * dt * dt + 0.5)
                    if 0 <= x < W and 0 <= y < H:
                        out[(x, y)] = rgb
