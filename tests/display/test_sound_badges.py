import pytest

import display.sound_badges as badges
from tests.display.test_network import FakeCanvas
from utils.sound import CANT_PLAY, NO_MUSIC


RED, WHITE = (255, 0, 0), (255, 255, 255)


@pytest.mark.parametrize("art", [badges.NO_MUSIC_ART, badges.CANT_PLAY_ART])
def test_badges_are_red_squares_in_the_bottom_left_corner_on_both_boards(art):
    assert len(art) == 9 and all(len(line) == 9 for line in art)
    for height in (32, 64):
        canvas = FakeCanvas(64, height)
        badges.draw_sound_badge(canvas, art)
        assert set(canvas.px) == {(x, y) for x in range(9) for y in range(height - 9, height)}, "a solid square"
        border = [xy for xy in canvas.px if xy[0] in (0, 8) or xy[1] in (height - 9, height - 1)]
        assert {canvas.px[xy] for xy in border} == {RED}, "a red border all round"
        assert set(canvas.px.values()) == {RED, WHITE}


def test_no_music_is_a_white_note_with_an_x_bottom_right():
    canvas = FakeCanvas(64, 32)
    badges.draw_sound_badge(canvas, badges.NO_MUSIC_ART)
    assert [canvas.px[(3, y)] for y in range(24, 28)] == [WHITE] * 4, "the stem"
    assert canvas.px[(1, 28)] == WHITE, "the note's head, bottom-left"
    assert [canvas.px[xy] for xy in [(5, 28), (7, 28), (6, 29), (5, 30), (7, 30)]] == [WHITE] * 5, "the X"
    assert [canvas.px[(4, y)] for y in range(27, 31)] == [RED] * 4, "a gap between the note and the X"


def test_cant_play_is_a_white_speaker_with_an_x():
    canvas = FakeCanvas(64, 32)
    badges.draw_sound_badge(canvas, badges.CANT_PLAY_ART)
    assert canvas.px[(1, 27)] == WHITE and canvas.px[(3, 24)] == WHITE, "the speaker, its cone up to the top"
    assert [canvas.px[xy] for xy in [(5, 26), (7, 26), (6, 27), (5, 28), (7, 28)]] == [WHITE] * 5, "the X"
    assert [canvas.px[(4, y)] for y in range(24, 31)] == [RED] * 7, "a gap between the speaker and the X"


@pytest.mark.parametrize("problem, art", [(NO_MUSIC, badges.NO_MUSIC_ART), (CANT_PLAY, badges.CANT_PLAY_ART)])
def test_draws_the_badge_for_the_problem(monkeypatch, problem, art):
    monkeypatch.setattr(badges, "current_problem", lambda: problem)
    drawn, expected = FakeCanvas(64, 32), FakeCanvas(64, 32)
    badges.draw_if_sound_problem(drawn)
    badges.draw_sound_badge(expected, art)
    assert drawn.px == expected.px


def test_draws_nothing_without_a_problem():
    canvas = FakeCanvas(64, 32)
    badges.draw_if_sound_problem(canvas)
    assert canvas.px == {}
