"""The lightsaber duels: Luke, Obi-Wan or Yoda against Darth Vader, and Rey against Kylo Ren."""

import random

import pytest

import display.animation as animation

from tests.display.animation.support import FakeCanvas

OLD, NEW = (90, 0, 90), (0, 140, 0)
Duel = animation.SaberDuelReveal
DUELS = animation.DUELS


def _duel(height, cls=Duel):
    duel = cls(64, height, random.Random(1))
    duel.prev_px = {(x, y): OLD for x in range(64) for y in range(height) if x % 2}  # half lit, half black
    return duel


def _frame(duel, t):
    canvas = FakeCanvas(64, duel.height)
    for x in range(64):
        for y in range(duel.height):
            canvas.SetPixel(x, y, *NEW)
    more = duel.overlay(canvas, t)
    return canvas.px, more


def _xs(px, colors):
    return [x for (x, _), rgb in px.items() if rgb in colors]


def _hits(duel):
    return [duel.WALK_S + i * duel.EXCHANGE_S + (duel.HIT_S[0] + duel.HIT_S[1]) / 2 for i in range(3)]


def _arts(cls):
    return [art for f in cls.FIGHTERS.values() for art in (f["art"], f.get("cape_art")) if art]


@pytest.mark.parametrize("name, cls", [("saber_duel_luke", animation.SaberDuelReveal),
                                       ("saber_duel_obiwan", animation.ObiWanDuelReveal),
                                       ("saber_duel_yoda", animation.YodaDuelReveal),
                                       ("saber_duel_kylo", animation.KyloReyDuelReveal)])
def test_each_duel_is_registered_and_takes_the_old_screen(name, cls):
    assert animation.TRANSITIONS[name] is cls
    assert cls in DUELS and cls.wants_prev


def test_the_duel_roll_picks_one_of_the_duels_at_random():
    picked = {type(animation.TRANSITIONS["saber_duel"](64, 32, random.Random(seed))) for seed in range(40)}
    assert picked == set(DUELS)


@pytest.mark.parametrize("cls", DUELS)
def test_the_blades_are_drawn_not_left_in_the_art(cls):
    blades = {rgb for pair in cls.BLADES.values() for rgb in pair}
    for art in _arts(cls):
        assert len({len(row) for row in art}) == 1
        used = {ch for row in art for ch in row} - {"."}
        assert used <= set(cls.COLORS)
        assert not {cls.COLORS[ch] for ch in used} & blades


@pytest.mark.parametrize("cls", DUELS)
def test_everyone_stands_as_tall_as_luke_but_yoda(cls):
    luke = len(Duel.LUKE_ART)
    for name, f in cls.FIGHTERS.items():
        for art in (f["art"], f.get("cape_art")):
            if art:
                assert len(art) < luke if name == "yoda" else len(art) == luke, name


@pytest.mark.parametrize("cls", DUELS)
@pytest.mark.parametrize("height", [32, 64])
def test_they_walk_in_from_either_side_and_stand_on_the_bottom_row(cls, height):
    duel = _duel(height, cls)
    left, right = cls.FIGHTERS[cls.LEFT], cls.FIGHTERS[cls.RIGHT]
    pose = duel.pose(0)
    assert pose[cls.LEFT][0] + len(left["art"][0]) - left["anchor"][0] < 0, "the left fighter starts off the left edge"
    assert pose[cls.RIGHT][0] - right["anchor"][0] > 63, "the right one off the right"
    px, _ = _frame(duel, duel.WALK_S)
    ours, red = _xs(px, duel.BLADES[left["blade"]]), _xs(px, duel.BLADES["red"])
    assert ours and red and min(ours) < min(red) and max(ours) < max(red), "his blade on the left, red on the right"
    for name, f in cls.FIGHTERS.items():
        assert duel.pose(duel.WALK_S)[name][1] - f["anchor"][1] + len(f["art"]) == height, f"{name} stands on the bottom row"


@pytest.mark.parametrize("cls", DUELS)
@pytest.mark.parametrize("height", [32, 64])
def test_three_blows_land_each_with_a_spark_where_the_blades_meet(cls, height):
    duel = _duel(height, cls)
    assert list(duel.attackers) == [cls.LEFT, cls.RIGHT, cls.LEFT]
    for i, t in enumerate(_hits(duel)):
        assert duel.contact(t), f"blow {i + 1} meets the other blade"
        px, _ = _frame(duel, t)
        assert set(px.values()) & set(duel.SPARKS), f"blow {i + 1} sparks"
        assert duel.pose(t)[duel.attackers[i]][2] < 45, "the attacker cuts down onto the guard"
    between = duel.WALK_S + duel.EXCHANGE_S - 0.01
    assert not duel._clashing(between), "no spark between blows"


@pytest.mark.parametrize("cls", DUELS)
@pytest.mark.parametrize("height", [32, 64])
def test_they_lock_blades_over_the_old_screen_then_are_thrown_apart(cls, height):
    duel = _duel(height, cls)
    lock = duel.WALK_S + duel.DUEL_S
    px, _ = _frame(duel, lock + duel.LOCK_S / 2)
    assert duel.contact(lock + duel.LOCK_S / 2), "blades locked"
    assert NEW not in set(px.values()), "the old screen stays up, black pixels included"
    assert duel.gap(lock + duel.LOCK_S - 0.01) is None

    t = lock + duel.LOCK_S + duel.PUSH_S * 0.32  # just upright
    px, _ = _frame(duel, t)
    assert px[(32, 0)] == NEW, "the new ride opens between them"
    assert px[(0, 0)] == (0, 0, 0) and px[(63, 0)] == OLD, "the old one outside"
    pose = duel.pose(t)
    assert pose[cls.LEFT][0] < 32 - duel.LOCKED and pose[cls.RIGHT][0] > 32 + duel.LOCKED, "thrown apart"
    assert pose[cls.LEFT][2] == pose[cls.RIGHT][2] == 90, "blades upright"

    px, more = _frame(duel, duel.duration - 0.01)
    assert more and set(px.values()) <= {NEW, *duel.SPARKS}, "both off the board"
    _, more = _frame(duel, duel.duration)
    assert not more


@pytest.mark.parametrize("cls, name", [(cls, name) for cls in DUELS for name in (cls.LEFT, cls.RIGHT)])
def test_the_arm_swings_with_the_blade(cls, name):
    duel = _duel(32, cls)
    fighter = cls.FIGHTERS[name]
    i = duel.attackers.index(name)
    start = duel.WALK_S + i * duel.EXCHANGE_S
    raised, cut = start + 0.25, start + duel.HIT_S[0]
    (_, sy), (_, high), _ = duel.arm(name, raised)
    (_, sy_cut), (_, low), _ = duel.arm(name, cut)
    assert high < sy - 2, "raising the blade lifts the fist up by his head"
    assert low > sy_cut, "cutting down brings it out in front and low"
    _, (fx, fy), _ = duel.arm(name, cut)
    bx, by, _ = duel.blade(name, cut)
    assert abs(bx - fx) < 5 and abs(by - fy) < 5, "the blade leaves the hilt in his fist"
    px, _ = _frame(duel, cut)
    assert px[(int(round(fx)), int(round(fy)))] in {cls.COLORS[k] for k in fighter["fist"]}
    assert cls.COLORS[fighter["sleeve"]] in px.values()


@pytest.mark.parametrize("cls", [cls for cls in DUELS if "back_shoulder" in cls.FIGHTERS[cls.LEFT]])
@pytest.mark.parametrize("t", [0.85, 1.15, 1.25, 3.0])
def test_the_left_fighters_free_arm_is_held_out_behind_him(cls, t):
    duel = _duel(32, cls)
    assert duel.back_arm(cls.RIGHT, t) is None, "the right fighter's reference shows one arm"
    (bsx, bsy), (bx, by) = duel.back_arm(cls.LEFT, t)
    (sx, _), _, _ = duel.arm(cls.LEFT, t)
    assert bsx < sx and bx < bsx, "from his far shoulder, out behind him, away from his opponent"
    assert by >= bsy, "level or lower, for balance"
    px, _ = _frame(duel, t)
    hand = [px.get((x, y)) for x in (bx, bx + 1) for y in (by, by + 1)]
    fist = cls.COLORS[cls.FIGHTERS[cls.LEFT]["fist"][0]]
    assert hand.count(fist) == 4, "the free hand shows, on its own"


def test_the_free_arm_swings_against_the_saber_arm():
    duel = _duel(32)
    start = duel.WALK_S  # Luke attacks first
    _, (_, raised) = duel.back_arm("luke", start + 0.25)
    _, (_, cut) = duel.back_arm("luke", start + duel.HIT_S[0])
    assert raised > cut, "tucked lower as he raises his blade, flung back up as he cuts"


def test_the_attacker_leans_into_the_blow_and_the_defender_is_knocked_back():
    duel = _duel(32)
    start = duel.WALK_S  # Luke attacks first
    assert duel.nudges(start + 0.1) == {"luke": (0, 0), "vader": (0, 0)}
    assert duel.nudges(start + duel.HIT_S[0] + 0.01) == {"luke": (1, 0), "vader": (0, 1)}
    assert duel.nudges(start + duel.HIT_S[0] + duel.RECOIL_S + 0.01)["vader"] == (0, 0), "the recoil is short"
    vader = start + duel.EXCHANGE_S
    assert duel.nudges(vader + duel.HIT_S[0] + 0.01) == {"luke": (0, 1), "vader": (1, 0)}
    # Vader knocked back moves him away from Luke, to the right.
    still, hit = duel._art_origin("vader", 40, 20, 0), duel._art_origin("vader", 40, 20, 1)
    assert hit[0] == still[0] + 1


def test_yoda_leaps_into_his_attacks_and_hops_in():
    duel = _duel(32, animation.YodaDuelReveal)
    ground = duel.anchor_y["yoda"]
    start = duel.WALK_S  # Yoda attacks first
    assert duel.pose(start + 0.22)["yoda"][1] < ground - 4, "up in the air as he raises his blade"
    assert duel.pose(start + duel.EXCHANGE_S + 0.22)["yoda"][1] == ground, "on the ground while Vader attacks"
    assert duel.pose(start + 2 * duel.EXCHANGE_S + 0.5)["yoda"][1] == ground, "landed after the blow"
    assert min(duel.pose(t / 30)["yoda"][1] for t in range(27)) <= ground - 2, "he hops in"
    luke = _duel(32)
    assert luke.pose(start + 0.22)["luke"][1] == luke.anchor_y["luke"], "Luke keeps his feet"


def test_reys_other_arm_stays_as_drawn_and_kylos_blade_has_a_crossguard_and_crackles():
    duel = _duel(32, animation.KyloReyDuelReveal)
    assert duel.back_arm("rey", 1.0) is None, "her other arm hangs at her side in the art"
    x, y, e = duel.blade("kylo", 0.95)

    def blade(frame, crackle, crossguard=True):
        px, kylo = {}, duel.FIGHTERS["kylo"]
        kylo["crackle"], kylo["crossguard"] = crackle, crossguard
        duel._blade_pixels(px, "kylo", x, y, e, (255, 0, 0), frame)
        kylo["crackle"] = kylo["crossguard"] = True
        return set(px)

    assert len(blade(3, False)) == len(blade(3, False, crossguard=False)) + 4, "two side blades of two pixels at the hilt"
    frames = [blade(f, True) for f in range(4)]
    assert all(len(f) > len(blade(0, False)) for f in frames), "pixels spit off its edges"
    assert len({frozenset(f) for f in frames}) > 1, "and they change from frame to frame"


def test_yoda_looks_at_vader_with_both_ears_showing():
    art = animation.YodaDuelReveal.YODA_ART
    whites = [(x, y) for y, row in enumerate(art) for x, ch in enumerate(row) if ch == "W"]
    assert len(whites) == 4, "two eyes, two rows each; no background white round his head"
    assert all(art[y][x + 1] == "y" for x, y in whites), "each pupil on the right of its white, toward Vader"
    ear_row = art[4]  # his ears' middle row
    assert ear_row.startswith("KYYY"), "his near ear reaches out to the left edge"
    far = ear_row[ear_row.rindex("K", 0, len(ear_row) - 1):]  # past the outline behind his head
    assert far.count("Y") >= 3, "and his far one, long enough to read"


def test_vaders_cape_sways():
    duel = _duel(32)
    t = duel.WALK_S + 0.05
    frames = [_frame(duel, t + k * duel.CAPE_S)[0] for k in range(2)]
    cape = [sum(1 for rgb in px.values() if rgb == Duel.COLORS["D"]) for px in frames]
    assert cape[0] != cape[1], "the cape's edge swings out and back"


@pytest.mark.parametrize("cls", DUELS)
@pytest.mark.parametrize("t", [0.85, 1.15, 1.25, 3.0])
def test_the_arms_outlines_never_cut_into_the_left_fighters_clothes(cls, t):
    duel = _duel(32, cls)
    name = cls.LEFT
    fighter = cls.FIGHTERS[name]
    x, y, _ = duel.pose(t)[name]
    lean, recoil = duel.nudges(t)[name]
    ox, oy = duel._art_origin(name, x, y, recoil)
    px, _ = _frame(duel, t)
    for row, line in enumerate(fighter["art"]):
        for col, ch in enumerate(line):
            if ch not in ".K" and cls.COLORS[ch] != (0, 0, 0):
                xy = (ox + col + (lean if row < fighter["waist"] else 0), oy + row)
                if 0 <= xy[1] < 32:
                    assert px[xy] != (0, 0, 0), f"black over his clothes at art ({col}, {row})"


def test_with_no_old_screen_they_fight_over_black():
    duel = Duel(64, 32, random.Random(1))
    px, _ = _frame(duel, _hits(duel)[0])
    assert NEW not in set(px.values())
