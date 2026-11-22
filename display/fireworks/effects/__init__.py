"""
Scene looks for the synced show (music_show.py), one class each, turned on by name in a scene's
"effects" in the show's JSON. An effect steps every frame but only starts new things while its
scene is on, so what it left (bubbles, smoke, blocks, the moon) drifts or fades off rather than
vanishing on the cut. Effects draw behind the castle unless they draw in front (draw_front).

The classes live in modules by kind of look: base (Effect and the shared bases), searchlights,
castle, comets, particles, sky. EFFECTS, the name-to-class registry the show reads, is built here.
"""

from display.fireworks.effects.castle import (
    Bells,
    DimKeyholeGlow,
    FlameJets,
    GoldTrace,
    GreenFire,
    KeyholeGlow,
    KeyholeMagic,
    KeyholeOpen,
    TeFiti,
    Torches,
    Water,
)
from display.fireworks.effects.comets import CometFan, CrossingComets
from display.fireworks.effects.particles import (
    Balloons,
    Blocks,
    Bubbles,
    Fountains,
    GoldBurst,
    GoldStream,
    GroundFountains,
    Smoke,
    Snow,
    Waterfalls,
)
from display.fireworks.effects.searchlights import (
    FanfareSearchlights,
    GreenSearchlights,
    PartySearchlights,
    Searchlights,
    TealSearchlights,
)
from display.fireworks.effects.sky import Bolts, EveningStar, MoonRise, Starfield, Stingray

EFFECTS = {
    "searchlights": Searchlights,
    "searchlights_fanfare": FanfareSearchlights,
    "searchlights_green": GreenSearchlights,
    "searchlights_teal": TealSearchlights,
    "searchlights_party": PartySearchlights,
    "comet_fan": CometFan,
    "crossing_comets": CrossingComets,
    "balloons": Balloons,
    "te_fiti": TeFiti,
    "fountains": Fountains,
    "ground_fountains": GroundFountains,
    "snow": Snow,
    "flame_jets": FlameJets,
    "keyhole_glow": KeyholeGlow,
    "keyhole_glow_dim": DimKeyholeGlow,
    "keyhole_open": KeyholeOpen,
    "keyhole_magic": KeyholeMagic,
    "gold_trace": GoldTrace,
    "gold_stream": GoldStream,
    "gold_burst": GoldBurst,
    "starfield": Starfield,
    "evening_star": EveningStar,
    "bubbles": Bubbles,
    "bells": Bells,
    "water": Water,
    "torches": Torches,
    "stingray": Stingray,
    "smoke": Smoke,
    "blocks": Blocks,
    "moon_rise": MoonRise,
    "waterfalls": Waterfalls,
    "bolts": Bolts,
    "green_fire": GreenFire,
}
