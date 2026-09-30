import math

from display.animation.drawing import art_pixels, paint
from display.animation.mechanics import FlyByReveal
from display.animation.motion import FLYBY_S


class DumboReveal(FlyByReveal):
    """
    TODO (art): his back half is missing — he reads as a head, ears and trunk with no
    body or rear behind them. Extend the sprite so he has a hindquarters and legs.

    Dumbo flies across the board the only way he knows how — by flapping those ears.
    Two poses alternate on FLAP_S, and the same flap phase drives a gentle bob, so he
    lifts on the upstroke and settles on the down. He trails little white feather-puffs
    from the circus act rather than dust or flame.
    """

    duration = FLYBY_S * 1.9
    FLAP_S = 0.22  # seconds per half-flap (ears up, then ears down)

    # Three-quarter view flying right: enormous pink-lined ears either side of a small
    # head, trunk curling down and forward, yellow-and-blue circus hat, white collar.
    # '.' empty, P inner ear pink, D shaded outer ear, G body grey, L lit grey (trunk),
    # K outline, E eye white, B pupil, W collar, Y hat yellow, U hat blue.
    EARS_UP = [
        "............KKYYKK..........",
        "............KUUUUK..........",
        "............KYYYYK..........",
        "...KKKK....KKYYYYKK....KKKK.",
        "..KPPPPKK..KKKKKKKKK..KPPPPK",
        ".KPPPPPPPKKKGGGGGGGKKKPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGEEGGEEGGPPPPPPPP",
        "KPPPPPPPPPPGBEGGBEGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        ".KPPPPPPPPKGGGGGGGGGKPPPPPPP",
        ".KDPPPPPPK.KGGGKLLGK.KPPPPPD",
        "..KDDPPPK..KGGGKLLGK..KPPPDK",
        "...KDDPK...KWWWKLLGK...KPDK.",
        "....KKK...KWWWWWKLLGK...KK..",
        "..........KGGGGGKLLLK.......",
        "..........KGGGGGKKLLLK......",
        "..........KGGKGGGKKLLLK.....",
        "..........KGGKKGGGK.KLLLK...",
        "...........KK..KKK...KKKK...",
    ]

    # The downstroke: the same elephant with both ears swept low, tips curling under.
    EARS_DOWN = [
        "............KKYYKK..........",
        "............KUUUUK..........",
        "............KYYYYK..........",
        "...........KKYYYYKK.........",
        "....KKK....KKKKKKKKK....KKK.",
        "...KPPPKKKKKGGGGGGGKKKKPPPK.",
        "..KPPPPPPPPGGGGGGGGGPPPPPPPK",
        "..KPPPPPPPPGEEGGEEGGPPPPPPPK",
        ".KPPPPPPPPPGBEGGBEGGPPPPPPPP",
        ".KPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPPGGGGGGGGGPPPPPPPP",
        "KPPPPPPPPPK.KGGKLLGK.PPPPPPP",
        "KDPPPPPPPK.KGGGKLLGK.KPPPPPP",
        "KDDPPPPPK..KWWWKLLGK..KPPPPD",
        ".KDDPPPK..KWWWWWKLLGK..KPPDD",
        "..KDDPK...KGGGGGKLLLK..KPDDK",
        "...KDK....KGGGGGKKLLLK..KDK.",
        "....K.....KGGKGGGKKLLLK..KK.",
        "..........KGGKKGGGK.KLLLK...",
        "...........KK..KKK...KKKK...",
    ]

    # `art` stays a single pose — the framework and the shared fly-by tests measure it —
    # while `poses` is what actually gets drawn, alternating on the flap.
    art = EARS_UP
    poses = [EARS_UP, EARS_DOWN]
    colors = {
        "P": (238, 170, 182), "D": (176, 132, 142), "G": (150, 158, 172),
        "L": (196, 204, 218), "K": (30, 32, 42), "E": (252, 252, 252),
        "B": (30, 34, 52), "W": (252, 252, 252), "Y": (250, 206, 60), "U": (55, 110, 215),
    }
    feather_colors = [(255, 255, 255), (238, 240, 250), (255, 235, 170)]

    def flap_phase(self, t):
        """0..1 through one full flap cycle (ears up, ears down, back again)."""
        return (t / (2 * self.FLAP_S)) % 1.0

    def flap_frame(self, t):
        """Index into self.poses: 0 while the ears are up, 1 while they are down."""
        return int(t / self.FLAP_S) % len(self.poses)

    def position(self, t):
        # He bobs with the flap — lifting on the upstroke, settling on the down — inside
        # whatever vertical room the sprite leaves, so he never clips off either board.
        room = max(0.0, self.height - self.sprite_h)
        amp = min(room / 2, self.height * 0.09)
        y = room / 2 - math.cos(self.flap_phase(t) * 2 * math.pi) * amp
        return self.progress_x(t), y

    def spawn(self, x, y):
        # Feather-puffs shed off the trailing (left) ear, drifting back and down.
        r = self.rng
        return [[x + r.uniform(0, self.sprite_w * 0.35),
                 y + self.sprite_h * r.uniform(0.25, 0.75),
                 r.uniform(-0.45, -0.05), r.uniform(-0.05, 0.25),
                 r.randint(10, 22), r.choice(self.feather_colors)]
                for _ in range(2 * self.scale)]

    def _draw_sprite(self, canvas, t):
        """Same as the base draw, but picks the flap pose for this moment."""
        art = self.poses[self.flap_frame(t)]
        x0, y0 = self.position(t)
        paint(canvas, art_pixels(art, int(round(x0)), int(round(y0)), self.colors, self.scale),
              self.width, self.height)
