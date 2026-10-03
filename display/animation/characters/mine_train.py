import random
from functools import lru_cache

from display.animation.drawing import _blackout


class MineTrainReveal:
    """
    The Seven Dwarfs Mine Train rolls across, left to right, on the Mine Train's own screen: three
    dwarfs picked at random, each in his own wooden mine car from the shoulders up and facing us,
    with a car heaped with gems at the back. Drawbars link the cars, the wheels turn as they roll,
    and a lit lantern hangs off the lead car. The new ride is uncovered behind the train.
    """

    RIDERS = 3  # dwarfs picked at random; None takes all seven
    SNOW_WHITE = False  # Snow White rides the lead car
    SCALE = 1  # 1x on both boards: the train needs the board's width to roll through
    SPEED = 40  # pixels a second, steady
    GAP = 31  # one car's left edge to the next
    CAR_W = 28
    LANTERN_X = 26  # hangs off the lead car's front, past CAR_W
    SHOW = 29  # rows of a rider drawn; the last two sit behind the rim (shoulders up)
    SNOW_SHOW = 30
    # The full train outlasts a ride screen's usual 8s; show_screen keeps the ride up this long after it's gone.
    hold_after_s = 3.0

    # Each dwarf straight from the pattern sheet (docs/references/dwarfs.jpg), facing us; the photo's stray
    # specks cleaned out. Only the top rows show above the car's rim.
    DWARFS = [
        # Dopey
        [
            "...........KKKKK.....",
            "........KKKVVVVVKK...",
            ".......KVVVVVVVVVVK..",
            "......KVVVVVVVKKVVK..",
            ".....KVVVVVVVVVKVVK..",
            ".....KVVVVVVVVVVKK...",
            "....KVVVKKKKKVVVK....",
            "...KVVVKVVVVVKVVK....",
            "...KVVKVVKKKKVKVVK...",
            "...KVKVKKSSSSKVKVK...",
            "..KVKVKSSSSSSSKVVK.K.",
            "..KVKVKSKSSSSKSKVKKSK",
            "..KVVKSKSSSSSSKSKKSSK",
            ".KKVVKSSSKSSSKSSKSTSK",
            "KSSKVKSSKWSSKWSSKSSSK",
            "KSTSKKSSKKSSKKSSKKSK.",
            "KSSSSKSSKKPPKKSSKSK..",
            ".KSSKSPPKPPPPbPPSK...",
            "..KSKPPPSPPPPSPPTK...",
            "...KKTPSKKPPKTSPSK...",
            "...gVKSSSKBBKSSSK....",
            "....KVKKSSRRSSKK.....",
            ".....KKGKSSSSKK......",
            ".....KGKGKKKKGGK.....",
            "....KGGGKGGGGGKGK....",
            "...KGGGGGKGGGKGGGK...",
            "...KGGGKGGBBKGKGGGK..",
            "...KGGKGGGYYGGGKGGK..",
            "..KGGGGKGGGGGGGKGGK..",
            "..KGGKKKGGGYGGKTKGK..",
            "..KGKSSKKBBBBKKSSK...",
            "...KSSSKKKYbBKKKbK...",
            "....KSKKKKYBBKKKK....",
            ".....KGGGKBBBGGGK....",
            "....KgGGGGGKGGGKK....",
            "..KKKKGGKGKKGGGGKKKK.",
            ".BKbBKKGGGKVGGgBKBbBK",
            ".KBBBBKKKKKVKKBBBBBBK",
            ".KBBBBBBKK..KKBBBBBBK",
            "..KKKKKK......KKKKKK.",
        ],
        # yellow hat, orange coat
        [
            "..........BKKK.....",
            "........KKbYYYK....",
            "......KKYYYYYYYK...",
            ".....KBYYYKKYYYK...",
            "....KYYYYYYYKKK....",
            "...KYYYYYYYYYYK....",
            "...KYYYYKKKKYYYK...",
            "..KYYYKKYYYYKYYK...",
            "..KYYKYYKKKKYKYYK..",
            ".KYYKYYKSSSSKYKYK..",
            ".KYKYYKSSSSSSKYYK..",
            ".KYYYKSKSSSKKSKYYK.",
            ".KYYKSKSSSSSSKSKYK.",
            ".KYYKSSKSSSKSSSKYK.",
            ".KYKSSTWKSSWKSSKK..",
            ".KK.SSSKKSSKKSSWK..",
            ".K..STSKKSSKKSSWK..",
            ".K.SPPPSPPPBSPPTWK.",
            "...SPPPSPPPPTPPPWK.",
            "....SPSKBPPKKSSSWK.",
            "...KKSSSKKKKSSSWWK.",
            "..KSSKWWTRrSSWWWWK.",
            ".KKSSSKWWSSWWWWWK..",
            ".OKSSSSKWWWWWWWKK..",
            "KOKSSTKWWWWWWWKOOK.",
            "KOOKKKKWWWWWWKOOOK.",
            "KOOOOKOKWWWWKOOOOOK",
            "KOOOOKOOKWWKOOOKOOK",
            ".KbOKOOOOKKOOOOKOOK",
            "..KKKOOOOYOOOOKSKOK",
            "..BBBKKKYBYKKKSSSK.",
            ".KOOOBBKYKYKbBBSSK.",
            ".KOOOOOOBBbOOOBBTK.",
            "..KBbOOOKKKOOOBKK..",
            "...KKKKKKBBKKKBK...",
            "..KKKBBBBKBBBKKKK..",
            ".KKbBbKBBKBBKBBBBB.",
            ".KbBbBBKKKKKBBBBBK.",
            ".KBBBBBKK.KBBBBBBK.",
            "..KKKKK....KKKKKK..",
        ],
        # Doc
        [
            "...........KKKK.....",
            ".........KKBBBBKK...",
            "........KBBBBBBBBK..",
            ".......KBBBBBBKBBK..",
            "......KBBBBBbbBKBK..",
            ".....KBBBBBBBbBBK...",
            "....KBBBKKKKKBBBK...",
            "....KBBKBBBBBKBBBK..",
            "...KBBKBBKKKBBKBBK..",
            "...KBKBKKSSSKKBKBK..",
            "...KBBKSSSSSSSKBKK..",
            "..KBBKSSKSSSKSSKBBK.",
            "..KBBKSKSSSSSKSKKBK.",
            "..KBKSSSKSSSKSSSKBK.",
            "..KKKSSKWSSKWKSSKKK.",
            "..KWKSTKKSSKKKbSKWK.",
            "..KWKKLLKKKKKLLKWWK.",
            ".KWTSKLLKPPPKLLKSWWK",
            ".KWSSKLLPPPPKLLKSWWK",
            ".KWWSSKKKPPPKKKTSWWK",
            "..KWWSSSSKKKSSSSWWK.",
            "..KWWWWSTRRSSWWWWWK.",
            "...KWWWWWSSTWWWWWK..",
            "..KRKWWWWWWWWWWKKR..",
            ".KRRKKWWWWWWWWKKrRK.",
            ".KRKSTKWWWWWWKTTKRK.",
            "KKRSSSTKKWWWKTTSTRK.",
            "KKBSSTKRRKWKRKSSSrK.",
            "K.KKTSKRRRBRRKTSKK..",
            "K...KKRRRrbrRRKKK...",
            "...KBBKKKYYYKKKBK...",
            "...KRRBBKYKYKBRRB...",
            "...KRRRRKYYYKRRRRK..",
            "...KKrRRRKKKRRRrKK..",
            "....KKKBrKKKRRKBK...",
            "...KKBBBBBKBBBKKKK..",
            "...BBBBKBBKBBKBBBBB.",
            "..KBBBBBKKKKKBBBBBK.",
            "..KBBBBBBK.KBBBBBBK.",
            "...KKKKKK...KKKKKK..",
        ],
        # green hat, brown coat
        [
            "........KKKK........",
            "......KKGGGgKK......",
            ".....KGGGGGGGGK.....",
            "....KGGGGGGGGGGK....",
            "...KGGKKKGGGGGGGK...",
            "..KGGGGGGKKGGGGGGK..",
            "..KGGKKKGGGKgGGGGGK.",
            ".KGGKSSSKKGGKGGGGGGK",
            ".KGKSSSSSSKGGKGGGGGK",
            ".KGSSKSSSKSKGGGGGGGG",
            "KGKSKSSSSSKSKGKGKGGG",
            "KGKSSSSSSSSSKGGGGKGG",
            "KGSSKSSSSKSSSKGKGKGG",
            "KGSKWKSSWWKSSKGGGKKK",
            ".KSSKKSSWKKSSSKGGK..",
            ".KSWKKSSWKKSSSKGGGK.",
            "KWSPKPPPWKKPSSWKGGK.",
            "KWPPPPPPPSPPPTWWKGK.",
            ".KSPPPPPPKPPPSWWKK..",
            ".BKSSPPPKBSPPSWWK...",
            "KSSKSSKKBSSSSWWKK...",
            "KSSSKWTRRSSWWWWKb...",
            "bTTSKWWSSTWWWWKbbK..",
            "bKSKWWWWWWWWWKbbbbK.",
            "bbKKWWWWWWWWKBbbbbbK",
            "bbbKKWWWWWWKbKbbbbbK",
            "KbbKbKWWWWKbbbKbbbbK",
            ".KKbbbKWWKbbbbKbbbbK",
            "..KbbbbKKbbbbbKKbbK.",
            "...KbbbbbbbbbKSSKbK.",
            "...KKKKYYYKKKKSSSK..",
            "..gbbBKYKYKBBBKTTK..",
            "..KbbbKYYYKbbbbKKK..",
            "..gKbbbKBKbbbbbKKK..",
            "...KKKKKBKbbKKBBK...",
            "..KKKKBBBKBBBKKKKK..",
            "..KBBBBBBKBBKBKKBBg.",
            ".KBbBBBKKKKKBBBBBBK.",
            ".KBBBBBBK.KBBBBBBBK.",
            "..KKKKKK...KKKKKKK..",
        ],
        # teal hat, yellow coat
        [
            ".........KKKKK.......",
            ".......KKCCCCCKK.....",
            "......KCCCCCCCCCK....",
            ".....KCCCCCCCKKKCK...",
            "....KCCCCCCKKCCCKCK..",
            "....KCCCCCKCCKKKKCCK.",
            "...KCCCCCKCCKSSSSKCK.",
            "...KCKCCKCCKSSSSSSKK.",
            "...KKCCCKCKSKSSSKSKK.",
            "..KCCCCKCKSKSSSSSKSK.",
            ".KCCCCKCCSSSSSSSKSSK.",
            "KCCCCKCCKSSSSWSSKKSK.",
            "KCCCCKCCKSSWWKSSKKSWK",
            "KCCCKKCKWSSWKKSSKKSWW",
            ".KKK.KCWWSPTKKPPPKPTW",
            ".....BKWWPPPSTPPPPPPW",
            "......KWWSPTSKPPbKPSW",
            ".....KYKWWSSTSbBKKTWW",
            "....KYYKWWWWWSSSKSKKW",
            "...KYYYYKWWWWWWKSTTKK",
            "...KYYYYYKWWWWWKSTSKB",
            "...KYYYYKYKWWWWKSSSYY",
            "...KYYYYKYYKWWWKSTSYY",
            "...KKYYKYYYYKWWWKKKYY",
            "..KSPKKKKYYYBKKKBKKYK",
            "..KSSKbbKKKKYYYKKKKY.",
            "..KTSKYYKKKKYKYKKYK..",
            "...KKYYYYYYKYbYKbYYK.",
            "....KKKYYYYYKKKYYYK..",
            "....KBBKKYYYKBYYKK...",
            "...KBKKbBKKKBKKBKBK..",
            "..KBBBBKKBBKKBBKBBBK.",
            "..KBBBBbBKK.KKKBBBbB.",
            "..KBBBBBBK..KBBBBBBK.",
            "...KKKKKK....KKKKKK..",
            ".....................",
        ],
        # blue hat, brown coat
        [
            ".........KKKKK......",
            ".......KKUUUUUKK....",
            "......KUUUUUUUUUK...",
            ".....KUUUUUUUUKUUK..",
            "....KUKKKKKUUUUKUK..",
            "...KUKUUUUUKUUUUKK..",
            "...KKUKKKKUUKUUUUK..",
            "..KUUKSSSSKUUKUUUUK.",
            "..KUKSSSSSSKUUKUUUUK",
            "..KUKSKSSSbWKUUKUKUK",
            "..KKSKPSSSbKSKUUKUUK",
            "..KKSSBSSWWSSSKUUKUK",
            "..KWSKKSTKKWSSKUUUK.",
            ".KWWSKKbSKKWTSWKUUK.",
            "KKWTPKPPPKKPPTSWKUUK",
            "KWWPPBPPPPSPPPTWWKUK",
            "KWWSTBPPPbSSPTSWWKUK",
            "KWWWSSKKKKbTSWWWWKK.",
            ".WWWWWSWBTSWWWWKbb..",
            ".KKWWWWSSSWWWWKbbbK.",
            "BbbKWWWWWSKKKKbbbbK.",
            "KbbKTSKBKbSTSSKbbbK.",
            "KbbbbbKKKSSSTbKbbbK.",
            "KBbbbbbbKSKKSKbbbK..",
            ".KKKbbbbKKKbKbbbKK..",
            "..KKKKKKYYYKbbbKKbK.",
            ".KbbbKKKYKYKKKKBbbK.",
            ".KbbbbbKYbYKKbbbbK..",
            "..KKKbbbKKKbbbbKKK..",
            "..KUUKKKUKUKKKUUUK..",
            ".KBKKUUUUKUUUUUKKBK.",
            "KBBBbKUUK.KUUKKBBbBK",
            "KbBBBBKKK.KKKBbBBBBK",
            "KbBBBBBB...BBBBBBBBK",
            ".KKKKKK.....KKKKKKK.",
            "....................",
        ],
        # red hat, red coat
        [
            "...........KKKKKK......",
            ".........KKRRRRRRKK....",
            "........KRRRRRRRRRRK...",
            ".......KRKKKKRRRRRRRK..",
            "......KRKRRRRKRRRRRRRK.",
            ".....KRrRKKKRRKRRRKRRRK",
            ".....KRRKSSSKKRKRRRKRRR",
            ".....KRKSSSSSSKRKRRRKRR",
            ".....KKSKSSSKSSKRKRRRKR",
            ".....KSKSSSSSKSKRRKRRKR",
            "....KKSSSSSSSSSSKRRKRKR",
            "...KTPSSKSSSKSSSWKRRKKK",
            "..KSKKSKTKTKSKSSSWKrRK.",
            ".KSSSKSTKPPTSSSSSWWKRRK",
            ".KSTKSPPPPPPSTSPPSWWKRK",
            "KRSSKSPPPPPPSTPPPSWWKRK",
            "KRKKWWSTSPKKKKTTTWWWKKK",
            "KRRRKWWSSSKKKTSSWWWKRRK",
            "KrRRKWWWWSWRPSWWWKBRRRR",
            ".KRRRKWWWWWTSWWWWKRRRRR",
            ".BrRRRrBWWWWWWWWKRRRKRR",
            "..KBrrRRBWWWWWKBRRRKRRR",
            "...KKKKRRKWWWWKRRRRKrRR",
            "......KKRRKKKKRRRRKBBBB",
            "......KKBRRrKRRRBKKSSbb",
            "......KRKKKYYYKKKKKKSSS",
            ".....KRRRKKYKYKKRRRrBKK",
            ".....KRRRRKYbYKrRRRRRRR",
            "......KKRRRKKKRRRRRRKKK",
            "......KBKKRKBKrRRRKKBBK",
            ".....KBKKBKBKBBKKKBBKKB",
            "....KBBBBKKBK.KBBbBKBBB",
            "....KBBBBbBKK.KBBKKBBbB",
            "....KBBBBBBK...KKBBBBBB",
            ".....KKKKKK......KKKKKK",
            ".......................",
        ],
    ]
    BUCKLE = [10, 9, 10, 8, 13, 9, 12]  # column of each dwarf's belt buckle: he's centred on it, not his outline

    # Snow White, redrawn at car size from docs/references/snow_white_stitched.png; her hair is lifted off
    # black so it shows on the board. Rides only with the whole train (MineTrainSnowReveal).
    SNOW_ART = [
        ".....qq.....qq.......",
        "....qhkqaaaqkhq......",
        "....qkkkqqqkkkqa.....",
        "....qkkkqkqkkkqka....",
        "...aqkkkqqqkkkqqka...",
        "..aaaqqqaaaqqqaaqka..",
        "..aaaAAaaaaaaaaaaqk..",
        ".aaAaaaaaaaaaaaaakja.",
        ".aaaaaaaasaaaaaaakja.",
        ".aaaaaaasssaaaaaaaka.",
        ".aaaaasssssssssaaaja.",
        ".aaaastttssstttsaaaa.",
        ".aaasssssssssssssaaa.",
        ".aaassEEEsssEEEssaaa.",
        ".aaassWiisssWiissaaa.",
        ".aaassiiisssiiissaaa.",
        ".aaasssssssssssssaaa.",
        ".aaasssssstssssssaaa.",
        ".aaaccsssssssssccaaa.",
        ".aaaacsssxsxssscaaaa.",
        ".aaaaatsssxssstaaaaa.",
        ".aaaaaattsssttaaaaaa.",
        "..aaaaaatssstaaaaaa..",
        ".aaa....tssst....aaa.",
        "....IIIWWWWWWWIII....",
        "..IIIkIIWWWWWIIkIII..",
        ".IIkkIIIIIJIIIIIkkII.",
        ".IkkIIIIIIJIIIIIIkkI.",
        ".IIIIsIIIIJIIIIsIIII.",
        "..IIssIIIIJIIIIssII..",
        "...ssIIIIIJIIIIIss...",
    ]

    # The wooden mine car: log rim, orange end bands with rivets. 64x64 has 4 more rows of planks.
    CAR_ART = [
        ".KKKKKKKKKKKKKKKKKKKKKKKKKK.",
        ".KddddddddddddddddddddddddK.",
        ".KKKKKKKKKKKKKKKKKKKKKKKKKK.",
        ".KOOKDDDDDDDDDDDDDDDDDKOOK..",
        ".KOYKDDdddDDDDDDDDDdDDKOYK..",
        ".KOOKDDDDDDDDdddDDDDDDKOOK..",
        ".KOOKDDDDDDdddDDDDDDDDKOOK..",
        ".KOYKDDDDDDDDDDDDddDDDKOYK..",
        ".KOOKDdddDDDDDDDDDDDDDKOOK..",
        ".KOOKDDDDDDdddDDDDDDDDKOOK..",
        ".KOYKDdDDDDDDDDDDDDdddKOYK..",
        ".KOOKDDDDDDDDDDDDDDDDDKOOK..",
        ".KKKKKKKKKKKKKKKKKKKKKKKKKK.",
    ]

    CAR_SHORT_ART = [
        ".KKKKKKKKKKKKKKKKKKKKKKKKKK.",
        ".KddddddddddddddddddddddddK.",
        ".KKKKKKKKKKKKKKKKKKKKKKKKKK.",
        ".KOOKDDDDDDDDDDDDDDDDDKOOK..",
        ".KOYKDDdddDDDDDDDDDdDDKOYK..",
        ".KOOKDDDDDDDDdddDDDDDDKOOK..",
        ".KOYKDdDDDDDDDDDDDDdddKOYK..",
        ".KOOKDDDDDDDDDDDDDDDDDKOOK..",
        ".KKKKKKKKKKKKKKKKKKKKKKKKKK.",
    ]

    # The gem car's heap, drawn without outlines: black ones vanish on the board.
    GEMS_ART = [
        "............w.............",
        "...........LLL............",
        "..........LLwLL...........",
        "....pp...LLLLLLL...RR.....",
        "...pwpp.lLLLLLLLl.RwRR....",
        "..ppppUUlLLLLLLLlGGRRRY...",
        "..YYUUwUUlLLLLLlGGwGGYYY..",
        ".YYwYUUUuGGllLGGGGgVVwYV..",
        ".RRYYYuuGGwGGVVVgGVwVVVRR.",
        "RRwRRVVVGGGGVwVVYYYVVRRwRR",
        "RRRRVVwVVgGUUUUYYwYYUUURRR",
        "RRRVVVVVGGGUwUUYYYYUUUURRR",
    ]

    LANTERN_ART = [
        ".KKK.",
        "K...K",
        "KKKKK",
        "KoWoK",
        "KoooK",
        "KoooK",
        "KKKKK",
    ]

    DRAWBAR_ART = [
        ".mm..mm.",
        "MMMMMMMM",
        ".mm..mm.",
    ]

    # A wheel, one frame per eighth of a turn: the two bolt marks step round as it rolls right.
    WHEEL_ART = [
        [
            "..KKK..",
            ".KOOOK.",
            "KOOHOOK",
            "KOOoOOK",
            "KOOHOOK",
            ".KOOOK.",
            "..KKK..",
        ],
        [
            "..KKK..",
            ".KOOOK.",
            "KOOOHOK",
            "KOOoOOK",
            "KOHOOOK",
            ".KOOOK.",
            "..KKK..",
        ],
        [
            "..KKK..",
            ".KOOOK.",
            "KOOOOOK",
            "KOHoHOK",
            "KOOOOOK",
            ".KOOOK.",
            "..KKK..",
        ],
        [
            "..KKK..",
            ".KOOOK.",
            "KOHOOOK",
            "KOOoOOK",
            "KOOOHOK",
            ".KOOOK.",
            "..KKK..",
        ],
    ]
    # Snow White has her own keys (lowercase and a few capitals) so one palette serves the whole train.
    COLORS = {
        "K": (10, 5, 5), "W": (240, 240, 240), "S": (245, 200, 175), "T": (240, 195, 145), "P": (240, 125, 100),
        "R": (220, 20, 30), "r": (160, 0, 0), "B": (115, 50, 5), "b": (155, 100, 30), "G": (40, 200, 70),
        "g": (20, 120, 40), "Y": (245, 195, 10), "O": (230, 120, 25), "U": (40, 90, 230), "u": (20, 50, 150),
        "V": (150, 70, 210), "v": (90, 40, 140), "C": (10, 145, 130), "L": (150, 220, 255), "l": (80, 150, 210),
        "y": (180, 130, 0), "D": (105, 60, 28), "d": (150, 92, 42), "o": (255, 190, 70), "w": (255, 255, 255),
        "p": (255, 90, 170), "M": (150, 150, 160), "m": (90, 90, 100), "H": (70, 35, 10), "a": (58, 58, 88),
        "A": (100, 100, 140), "E": (40, 22, 12), "i": (130, 70, 30), "h": (255, 120, 120), "q": (110, 0, 15),
        "s": (250, 222, 200), "t": (205, 150, 105), "c": (245, 160, 160), "x": (225, 70, 80), "k": (225, 40, 40),
        "j": (170, 15, 20), "I": (50, 110, 200), "J": (40, 55, 150),
    }
    COLORS_KEY = tuple(sorted(COLORS.items()))

    def __init__(self, width, height, rng=None):
        self.width, self.height = width, height
        rng = rng or random.Random()
        dwarfs = list(range(len(self.DWARFS)))
        rng.shuffle(dwarfs)
        if self.RIDERS is not None:
            dwarfs = dwarfs[:self.RIDERS]
        # Back to front: the gem car always rides last.
        self.cars = ["gems"] + dwarfs + (["snow"] if self.SNOW_WHITE else [])
        # 64x32 has no room for the taller car under a rider's shoulders, so it gets the short one.
        self.car_art = self.CAR_ART if height >= 64 else self.CAR_SHORT_ART
        self.base = height - 1 if height >= 64 else height  # one row under the wheels on the big board
        self.top = self.base - len(self.car_art) - 3
        self.extra = len(self.car_art) - len(self.CAR_SHORT_ART)
        # As much of each rider as fits above the car: shoulders up on 64x64, hat to nose on 64x32.
        self.show = min(self.SHOW, self.top + 2)
        self.snow_show = min(self.SNOW_SHOW, self.top + 2)
        self.snow_x = self.CAR_W // 2 - round(_middle(self.SNOW_ART[:self.snow_show][-5:]))
        self.length = (len(self.cars) - 1) * self.GAP + self.LANTERN_X + len(self.LANTERN_ART[0])
        self.duration = (width + self.length) / self.SPEED

    def back_x(self, t):
        """The gem car's left edge at t: from just off the left edge until the lantern is off the right."""
        return -self.length + self.SPEED * min(t, self.duration)

    def overlay(self, canvas, t):
        if t >= self.duration:
            return False
        x = int(round(self.back_x(t)))
        front = x + (len(self.cars) - 1) * self.GAP + self.CAR_W
        _blackout(canvas, front, self.width, self.height)  # ahead of the train, still dark
        spoke = (x // 3) % len(self.WHEEL_ART)  # a wheel turns an eighth every 3px it rolls
        for i, kind in enumerate(self.cars):
            car_x = x + i * self.GAP
            # Only the two or three cars on the board are drawn: the whole train is too many pixels for a Pi Zero.
            if car_x + self.LANTERN_X + len(self.LANTERN_ART[0]) > 0 and car_x < self.width:
                self._car(canvas, car_x, kind, spoke, lead=i == len(self.cars) - 1)
        return True

    def _car(self, canvas, x, kind, spoke, lead):
        top = self.top
        # The load first, so the car covers all but what's above its rim.
        if kind == "gems":
            self._paint(canvas, self.GEMS_ART, x + 1, top - len(self.GEMS_ART) + 3)
        else:
            if kind == "snow":
                art, ax, show = self.SNOW_ART, x + self.snow_x, self.snow_show
            else:
                art, ax, show = self.DWARFS[kind], x + self.CAR_W // 2 - self.BUCKLE[kind], self.show
            self._paint(canvas, art[:show], ax, top - show + 2)
        self._paint(canvas, self.car_art, x, top)
        if not lead:
            self._paint(canvas, self.DRAWBAR_ART, x + self.CAR_W - 3, top + 5 + self.extra)
        for wx in (x + 5, x + 17):
            self._paint(canvas, self.WHEEL_ART[spoke], wx, self.base - len(self.WHEEL_ART[0]))
        if lead:
            self._paint(canvas, self.LANTERN_ART, x + self.LANTERN_X, top + 2)

    def _paint(self, canvas, art, x, y):
        for dx, dy, rgb in _cells(tuple(art), self.COLORS_KEY):
            px, py = x + dx, y + dy
            if 0 <= px < self.width and 0 <= py < self.height:
                canvas.SetPixel(px, py, *rgb)


class MineTrainAllReveal(MineTrainReveal):
    """The whole Mine Train: all seven dwarfs, in a random order, then the gem car."""

    RIDERS = None


class MineTrainSnowReveal(MineTrainAllReveal):
    """All seven dwarfs and Snow White, who rides the lead car with the lantern."""

    SNOW_WHITE = True


@lru_cache(maxsize=None)
def _cells(art, colors_key):
    """Each lit cell of a sprite as (dx, dy, rgb), worked out once rather than every frame."""
    colors = dict(colors_key)
    return [(dx, dy, colors[kind]) for dy, row in enumerate(art) for dx, kind in enumerate(row) if kind != "."]


def _middle(rows):
    """The middle column of what's drawn in these rows."""
    cols = [x for row in rows for x, kind in enumerate(row) if kind != "."]
    return (min(cols) + max(cols) + 1) / 2
