"""Who visits on the board's screens and how often: the odds tables disney.py rolls against and the
settings page's Surprise characters page shows as its defaults. Plain data, no art, so the
settings server can import it. config.json's "surprises" (utils.config.surprise_settings)
turns characters off and overrides these chances.
"""
PARK_REVEALS = ("tink", "buzz")
# Rare visitors on ride screens, and each one's chance per screen. Genie erupts from his
# lamp and sweeps the next ride in; Baymax peeks over it so the wait stays readable;
# Slinky walks off the right edge and his spring wraps round the back of the board;
# WALL-E, in profile, bales the old ride into a cube and drives off with it (his
# three-quarter view, "walle", is kept for force_surprise but isn't in the rotation);
# Mike Wazowski pops up, looks around and scares (and visits the Laugh Floor more often).
# Two TRON light cycles race across, blue on top and red below, their trails the wipe.
# Olaf stacks himself up out of snowballs while it snows, waves, and walks off.
# Goofy flies his biplane through a loop-the-loop, towing a YAHOOEY! banner.
# The Pixar Ball bounces in with Luxo Jr., in one of three little stories.
# Lightning McQueen zooms in, skids, Ka-chows and peels out; Mater drives across backwards.
# (WALL-E and Baymax were trimmed to make room for the Cars pair under 10% in all.)
# Chip 'n' Dale run in and meet nose to nose, or swing in on ropes, Dale bonking into Chip
# (the Army Men were trimmed to make room).
# Tigger bounces across on his tail. Stitch surfs the new ride in on a wave that washes
# the old one away. Wreck-It Ralph stomps in and smashes the old ride into falling pixels.
# Pooh floats up on his balloon, uncovering the ride below him (Baymax was trimmed to make
# room; Pooh also visits his own ride more often).
# Forky waddles in, spots the old ride (TRASH!) and dives through the bottom of the board,
# taking it down the hole after him.
# Kevin struts across with Dug chasing her, his balloons lifting him higher as he goes.
# An archer rises at full draw, looses an arrow across the board and sinks away, the new ride
# uncovered behind the arrow (64x64 boards only; the Army Men were trimmed again to make room).
# Surprises may fill up to 13% of ride screens.
# Ride screens run 8s each, about 400 an hour while parks are open, so 1% is roughly
# four visits an hour.
SURPRISES = {"genie": 0.005, "baymax": 0.007, "slinky_wrap": 0.01, "walle_side": 0.012, "army_men": 0.005,
             "mike": 0.008, "tron": 0.008, "archer": 0.005,
             "olaf": 0.005, "goofy": 0.008,
             "luxo_ball": 0.005, "mcqueen": 0.005, "mater": 0.005,
             "chip_dale": 0.005, "tigger": 0.005, "stitch_surf": 0.005,
             "ralph": 0.005, "grannies": 0.005,
             "keepy_uppy": 0.001, "pooh": 0.005, "forky": 0.005,
             "kevin": 0.005}
# Visitors too tall for a 64x32 board: there the roll gives the plain wipe.
TALL_ONLY = ("archer",)
# Visitors who only turn up on their own rides, and how often on those rides. Matched by
# a piece of the ride's name, ignoring case. The Falcon keeps to Galaxy's Edge, and a red and
# a blue lightsaber clash over its rides and Star Tours, then sweep apart to the next; on the
# same rides Luke and Vader fight a duel, lock blades and are thrown apart to the edges. Mike is
# in the rotation too, but drops in on his own Laugh Floor far more often. Jack, Sally and
# Zero turn up on their own meet, which is only listed on Halloween party nights ("jack
# skellington", not "jack": Captain Jack's Buccaneer Bash is a party show too). The Mine Train
# brings a few dwarfs in their cars now and then; at a short wait the whole train comes every
# time (see _mine_train_for_wait). Rex stomps through Toy Story Land, and the claw chooses one of
# the Aliens on their own rides; at a wait of 5 or less it's Buzz, every time, with Woody hanging on.
# Pooh floats through his own ride's screens.
RIDE_VISITORS = {
    "falcon": {"rides": ("smugglers run", "rise of the resistance"), "chance": 0.10},
    "saber_clash": {"rides": ("smugglers run", "rise of the resistance", "star tours"), "chance": 0.10},
    "saber_duel": {"rides": ("smugglers run", "rise of the resistance", "star tours"), "chance": 0.10},
    "mike": {"rides": ("laugh floor",), "chance": 0.10},
    "jack_sally": {"rides": ("meet jack skellington",), "chance": 0.5},
    "mine_train": {"rides": ("seven dwarfs mine train",), "chance": 0.10},
    "rex": {"rides": ("slinky dog dash", "toy story mania", "alien swirling saucers"), "chance": 0.10},
    "aliens": {"rides": ("toy story mania", "alien swirling saucers"), "chance": 0.10},
    "pooh": {"rides": ("winnie the pooh",), "chance": 0.10},
}
# The chance on its own rides for a character the settings page adds to rides it has none of by default.
DEFAULT_RIDE_CHANCE = 0.10
