"""The Santa train's palette, what rides where and Santa's wave. Each piece's art is in santa_train_cars_64.py and
santa_train_cars_32.py."""

from display.landmarks.santa_train_cars_32 import (
    DONALD_32, ENGINE_32, GIFT_32, GOOFY_32, MICKEY_32, PLUTO_32, TREE_32,
)
from display.landmarks.santa_train_cars_64 import (
    DONALD_64, ENGINE_64, GIFT_64, GOOFY_64, MICKEY_64, PLUTO_64, TREE_64,
)

# The art: each piece's rows, all the same height on a board, joined side by side.
COLORS = {  # the unnamed shades come from the riders' charts
    "A": (160, 15, 25),
    "B": (70, 130, 255),  # blue cars
    "C": (0, 128, 0),
    "G": (30, 145, 50),  # green: cars, the cab, the tree
    "H": (215, 25, 32),  # Santa hats, red sweaters
    "I": (75, 75, 90),  # iron grey
    "K": (58, 56, 72),  # outlines (black lifted to charcoal so it lights)
    "N": (110, 60, 25),  # brown: the cab's wood, the teddy
    "O": (245, 144, 38),  # Donald's bill
    "R": (235, 30, 30),  # red: cars, the engine, Santa
    "S": (185, 190, 200),  # silver: wheel rims, smoke shade
    "T": (245, 245, 250),  # sweater bands
    "W": (255, 255, 255),  # white: gloves, smoke, beards, eyes
    "X": (30, 150, 60),  # green sweaters
    "Y": (255, 195, 30),  # gold: hubs, trim, the star
    "a": (234, 207, 183),
    "b": (30, 70, 200),  # the blue cars' shade
    "c": (200, 200, 210),
    "d": (250, 195, 160),
    "e": (176, 195, 216),
    "f": (247, 189, 145),
    "g": (10, 85, 28),  # dark green
    "h": (150, 15, 22),  # the hats' and red sweaters' shade
    "i": (236, 180, 140),
    "j": (182, 171, 148),
    "k": (40, 40, 52),  # iron: wheels, smokestack
    "l": (230, 140, 120),
    "m": (150, 150, 160),
    "n": (135, 135, 145),
    "o": (230, 140, 40),
    "p": (200, 120, 20),
    "q": (185, 110, 45),
    "r": (150, 15, 20),  # dark red
    "s": (190, 70, 30),
    "t": (200, 42, 45),
    "u": (247, 4, 5),
    "v": (255, 0, 0),
    "w": (80, 80, 90),
    "x": (15, 95, 35),  # the green sweaters' shade
    "y": (238, 183, 0),  # Pluto's yellow
    "z": (139, 69, 19),
}

BULBS = [COLORS["Y"], COLORS["G"], COLORS["W"], COLORS["B"]]  # round the billboard, chasing

# Left to right: the train drives right, so the engine leads; the billboard car goes on behind Pluto.
TRAIN_64 = [PLUTO_64, GOOFY_64, TREE_64, DONALD_64, GIFT_64, MICKEY_64, ENGINE_64]
TRAIN_32 = [PLUTO_32, GOOFY_32, TREE_32, DONALD_32, GIFT_32, MICKEY_32, ENGINE_32]
RIDERS = {  # who rides in which piece, by board
    True: {id(PLUTO_64): "pluto", id(GOOFY_64): "goofy", id(DONALD_64): "donald", id(MICKEY_64): "mickey",
           id(ENGINE_64): "santa"},
    False: {id(PLUTO_32): "pluto", id(GOOFY_32): "goofy", id(DONALD_32): "donald", id(MICKEY_32): "mickey",
            id(ENGINE_32): "santa"},
}

# Santa waving (not drawn yet): his forearm up out of his coat sleeve to a white mitten by his cheek, rocking
# between these two frames. Each is ENGINE_64's cab, rows 22-44 and columns 0-25, and replaces it whole.
SANTA_WAVE_AT = (0, 22)
SANTA_WAVE_64 = [
    [
        "..GGGGGGGGGGGGGGGGGGGGG...",
        ".GGGGGGGGGGGGGGGGGGGGGGG..",
        "RRRRRRRRRRRRRRRRRRRRRRRRRR",
        "rrrrrrrrrrrrrrrrrrrrrrrrr.",
        "..gGNNNNNrRRRRRRNNNNpYGg..",
        "..gGNNNNrRRRRRRRRNNNpYGg..",
        "..gGNNNrRrWWWWWSRNNNpYGg..",
        "..gGNNNNSWWWWWWWSrNNpYGg..",
        "..gGWWWnWSllddSnWwNNpYGg..",
        "..gGWWWnndddddddnnNNpYGg..",
        "..gGWWWIldkdddkdlINNpYGg..",
        "..gGrRNnSllnlNllSSNNpYGg..",
        "..gGRRNSSSWWwnSSWWNNpYGgpY",
        "..gGRRRnSSWWWSSSSSNNpYGgrp",
        "..gGRRRRWWWWWWWWWrrNpYGgNY",
        "..gGNRRRSWWWWWWWSrRRpYGgYY",
        "..gGNNRRrnWWWWWSrRRRpYGgYr",
        "..gGNNNRRrwWWWnrRrrRpYGgYR",
        ".ggGNNNRRRrnnRRRRSwRpYGgYR",
        ".ggGNNNrRRRWSRrHHSWrpYGgYr",
        ".ggpppppppppppppppppGGGgYr",
        ".ggGGGGGGGGGGGGGGGGGGGGgYr",
        ".ggGGgggggggggggggggGGGgYr",
    ],
    [
        "..GGGGGGGGGGGGGGGGGGGGG...",
        ".GGGGGGGGGGGGGGGGGGGGGGG..",
        "RRRRRRRRRRRRRRRRRRRRRRRRRR",
        "rrrrrrrrrrrrrrrrrrrrrrrrr.",
        "..gGNNNNNrRRRRRRNNNNpYGg..",
        "..gGNNNNrRRRRRRRRNNNpYGg..",
        "..gGNNNrRrWWWWWSRNNNpYGg..",
        "..gGNNNNSWWWWWWWSrNNpYGg..",
        "..gWWWNnWSllddSnWwNNpYGg..",
        "..gWWWNnndddddddnnNNpYGg..",
        "..gWWWNIldkdddkdlINNpYGg..",
        "..grRRNnSllnlNllSSNNpYGg..",
        "..gRRRNSSSWWwnSSWWNNpYGgpY",
        "..gRRRRnSSWWWSSSSSNNpYGgrp",
        "..gGRRRRWWWWWWWWWrrNpYGgNY",
        "..gGNRRRSWWWWWWWSrRRpYGgYY",
        "..gGNNRRrnWWWWWSrRRRpYGgYr",
        "..gGNNNRRrwWWWnrRrrRpYGgYR",
        ".ggGNNNRRRrnnRRRRSwRpYGgYR",
        ".ggGNNNrRRRWSRrRRSWrpYGgYr",
        ".ggpppppppppppppppppGGGgYr",
        ".ggGGGGGGGGGGGGGGGGGGGGgYr",
        ".ggGGgggggggggggggggGGGgYr",
    ],
]
