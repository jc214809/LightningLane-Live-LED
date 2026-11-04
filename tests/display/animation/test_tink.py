"""Tinker Bell."""

import random

import display.animation as animation


def test_tink_is_a_fairy_not_a_glyph_and_doubles_on_64x64():
    art = animation.TinkReveal.art
    assert (len(art[0]), len(art)) == (9, 8)
    cells = "".join(art)
    assert {"W", "Y", "S", "G"} <= set(cells), "wings, her bun, a face and the green dress"
    assert art[0].strip(".") == "Y", "her bun on top"
    for height, size in ((32, (9, 8)), (64, (18, 16))):
        tink = animation.TinkReveal(64, height, random.Random(1))
        assert (tink.sprite_w, tink.sprite_h) == size
