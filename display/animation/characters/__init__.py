"""
Every transition by name. disney.py picks from these.
"""

from display.animation.characters.aliens import AliensReveal, AliensToysReveal
from display.animation.characters.army_men import ArmyMenReveal
from display.animation.characters.baymax import BaymaxReveal
from display.animation.characters.bluey import GranniesReveal, KeepyUppyReveal
from display.animation.characters.buzz import BuzzReveal
from display.animation.characters.chip_dale import ChipDaleReveal
from display.animation.characters.donald import DonaldReveal
from display.animation.characters.dumbo import DumboReveal
from display.animation.characters.falcon import FalconReveal
from display.animation.characters.figment import FigmentReveal
from display.animation.characters.genie import GenieReveal
from display.animation.characters.jack_sally import JackSallyReveal
from display.animation.characters.goofy import GoofyReveal
from display.animation.characters.luxo_ball import LuxoBallReveal
from display.animation.characters.mater import MaterReveal
from display.animation.characters.mcqueen import McQueenReveal
from display.animation.characters.mickey import MickeyReveal
from display.animation.characters.mine_train import MineTrainAllReveal, MineTrainReveal, MineTrainSnowReveal
from display.animation.characters.mike import MikeReveal
from display.animation.characters.olaf import OlafReveal
from display.animation.characters.ralph import RalphReveal
from display.animation.characters.rex import RexReveal
from display.animation.characters.slinky import SlinkyReveal, SlinkyWrapReveal
from display.animation.characters.stitch import StitchSurfReveal
from display.animation.characters.tink import TinkReveal
from display.animation.characters.tigger import TiggerReveal
from display.animation.characters.tron import TronReveal
from display.animation.characters.walle import WallEReveal, WallESideReveal
from display.animation.mechanics import Wipe


TRANSITIONS = {
    "wipe": Wipe, "tink": TinkReveal, "buzz": BuzzReveal,
    "figment": FigmentReveal, "ralph": RalphReveal,
    "mickey": MickeyReveal, "slinky": SlinkyReveal, "baymax": BaymaxReveal,
    "dumbo": DumboReveal,
    "genie": GenieReveal,
    "slinky_wrap": SlinkyWrapReveal,
    "walle": WallEReveal,
    "walle_side": WallESideReveal,
    "army_men": ArmyMenReveal,
    "falcon": FalconReveal,
    "mike": MikeReveal,
    "tron": TronReveal,
    "olaf": OlafReveal,
    "goofy": GoofyReveal,
    "luxo_ball": LuxoBallReveal,
    "mcqueen": McQueenReveal,
    "mater": MaterReveal,
    "chip_dale": ChipDaleReveal,
    "tigger": TiggerReveal,
    "donald": DonaldReveal,
    "stitch_surf": StitchSurfReveal,
    "jack_sally": JackSallyReveal,
    "mine_train": MineTrainReveal,
    "mine_train_all": MineTrainAllReveal,
    "mine_train_snow": MineTrainSnowReveal,
    "grannies": GranniesReveal,
    "keepy_uppy": KeepyUppyReveal,
    "rex": RexReveal,
    "aliens": AliensReveal,
    "aliens_toys": AliensToysReveal,
}
