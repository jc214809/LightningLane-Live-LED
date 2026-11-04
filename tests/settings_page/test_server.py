"""The settings server over real HTTP, on a free port, with config.json and comitup's state in a
temp folder. The file is "board-config.json": tests/stubs/conftest.py fakes every "config.json"."""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from urllib.parse import urlencode

import pytest

import settings_page.server as server
from settings_page.park_names import ParkNames
from settings_page.pins import PinGate
from settings_page.server import Settings, make_server

CONFIG = {"parks": ["EPCOT"], "websocket": {"enabled": False, "api_key": "tp-secret-1234", "protocol": "legacy"},
          "weather": {"apikey": "owm-secret-9876"}, "trip_countdown": {"enabled": False, "trip_dates": []},
          "keep_me": 1}
SAVE = {"park": "EPCOT", "ws_protocol": "legacy", "trip_start_0": "2027-05-05", "trip_name_0": "May"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Board:
    def __init__(self, tmp_path, monkeypatch):
        self.config = tmp_path / "board-config.json"
        self.config.write_text(json.dumps(CONFIG))
        os.chmod(self.config, 0o600)
        self.state = tmp_path / "comitup-state"
        self.cards = tmp_path / "cards"
        self.cards.write_text(" 0 [Headphones     ]: bcm2835_headpho - bcm2835 Headphones\n"
                              "                      bcm2835 Headphones\n"
                              " 1 [Device         ]: USB-Audio - USB Audio Device\n")
        self.gate = PinGate(str(tmp_path / "pin"))
        self.restarts = []
        # A fresh list on disk, so nothing is fetched
        names = tmp_path / "park_names.json"
        names.write_text(json.dumps({"fetched": time.time(), "parks": [["EPCOT", "Walt Disney World® Resort"],
                                                                      ["Cedar Point", "Cedar Point"]]}))
        self.model = tmp_path / "model"
        self.model.write_bytes(b"Raspberry Pi 4 Model B Rev 1.5\0")
        self.settings = Settings(str(self.config), self.gate, state_file=str(self.state), cards_file=str(self.cards),
                                 park_names=ParkNames(str(names), fetch=self.no_fetch),
                                 model_file=str(self.model))
        monkeypatch.setattr(self.settings, "restart_app", lambda: self.restarts.append(1) or "restarted")
        self.httpd = make_server(self.settings, "127.0.0.1", 0)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    @staticmethod
    def no_fetch():
        raise AssertionError("the list was fresh: no fetch")

    def hotspot(self, client_on_it=True):
        """comitup's hotspot is up, and this test's browser (127.0.0.1) counts as on it or not."""
        self.state.write_text("HOTSPOT Disneypi-setup\n")
        if client_on_it:
            server.HOTSPOT_NETWORK = server.ip_network("127.0.0.0/8")

    def request(self, path, form=None, headers=None):
        data = urlencode(form, doseq=True).encode() if form is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers=headers or {})
        try:
            with self.opener.open(req, timeout=5) as response:
                return response.status, dict(response.headers), response.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read().decode()

    def sign_in(self):
        self.request("/pin/show", {})
        with open(self.gate.pin_file) as f:
            pin = f.read().split()[0]
        status, headers, _ = self.request("/pin", {"pin": pin})
        assert status == 303 and "HttpOnly" in headers["Set-Cookie"] and "SameSite=Strict" in headers["Set-Cookie"]

    def saved(self):
        return json.loads(self.config.read_text())


@pytest.fixture
def board(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "HOTSPOT_NETWORK", server.HOTSPOT_NETWORK)
    b = Board(tmp_path, monkeypatch)
    yield b
    b.httpd.shutdown()
    b.httpd.server_close()


def test_on_the_home_network_the_page_asks_for_the_boards_pin_first(board):
    status, _, html = board.request("/")
    assert status == 200 and "type in the PIN it shows" in html
    assert "tp-secret" not in html
    status, _, _ = board.request("/save", SAVE)
    assert status == 303 and board.saved() == CONFIG, "not signed in: nothing saved"


def test_a_wrong_pin_says_so(board):
    board.request("/pin/show", {})
    status, headers, _ = board.request("/pin", {"pin": "x"})
    assert status == 303 and headers["Location"] == "/?wrong"
    assert "the PIN on the board. Try again" in board.request("/?wrong")[2]
    assert "on the board for the next 2 minutes" in board.request("/?shown")[2]


def test_signed_in_the_form_shows_masked_keys_and_saves(board):
    board.sign_in()
    status, _, html = board.request("/")
    assert status == 200 and 'action="/save"' in html
    assert "1234" in html and "tp-secret" not in html and "owm-secret" not in html
    assert "plughw:CARD=Device,DEV=0" in html and "plughw:CARD=Headphones,DEV=0" in html
    status, headers, _ = board.request("/save", SAVE)
    assert status == 303 and headers["Location"] == "/?saved=restarted"
    saved = board.saved()
    assert saved["trip_countdown"]["trip_dates"] == [{"start": "2027-05-05", "name": "May"}]
    assert saved["websocket"]["api_key"] == "tp-secret-1234" and saved["keep_me"] == 1
    assert board.restarts == [1]
    assert oct(os.stat(board.config).st_mode & 0o777) == "0o600", "keeps the file's mode"
    assert json.loads((board.config.parent / "board-config.json.bak").read_text()) == CONFIG
    assert "restarting with the new settings" in board.request("/?saved=restarted")[2]


def test_problems_are_shown_and_nothing_is_saved(board):
    board.sign_in()
    status, _, html = board.request("/save", dict(SAVE, park=[]))
    assert status == 400 and "Not saved." in html and "Pick at least one park." in html
    assert board.saved() == CONFIG and board.restarts == []


def test_the_park_picker_suggests_the_cached_names_and_refuses_others(board):
    board.sign_in()
    html = board.request("/")[2]
    assert '<option value="Cedar Point">Cedar Point</option>' in html
    status, _, html = board.request("/save", dict(SAVE, park_add="Cedar Pointe"))
    assert status == 400 and "&#x27;Cedar Pointe&#x27; isn&#x27;t a ThemeParks.wiki park" in html
    assert board.saved() == CONFIG
    assert board.request("/save", dict(SAVE, park_add="cedar point"))[0] == 303
    assert board.saved()["parks"] == ["EPCOT", "Cedar Point"]


def test_the_park_list_is_kept_beside_config_json(tmp_path):
    settings = Settings(str(tmp_path / "board-config.json"))
    assert settings.park_names.path == str(tmp_path / "park_names.json")


def test_on_the_setup_hotspot_no_pin_is_needed(board):
    board.hotspot()
    status, _, html = board.request("/")
    assert 'action="/save"' in html and "Setup mode" in html and "Disneypi-setup" in html
    assert 'action="/signout"' not in html, "no PIN session to end"
    assert board.request("/save", SAVE)[0] == 303
    assert board.saved()["trip_countdown"]["trip_dates"]


def test_while_the_hotspot_is_up_a_browser_off_it_still_needs_the_pin(board):
    board.hotspot(client_on_it=False)
    assert "type in the PIN it shows" in board.request("/")[2]


def test_a_form_posted_from_another_site_is_turned_away(board):
    board.hotspot()
    status, _, _ = board.request("/save", SAVE, {"Origin": "http://evil.example"})
    assert status == 403 and board.saved() == CONFIG


def test_the_pages_own_forms_are_let_in_as_a_browser_posts_them(board):
    # A browser sends the page's origin with its forms, unless the page's referrer policy is
    # no-referrer: then it sends "Origin: null", which is turned away (a board said "Not allowed").
    status, headers, _ = board.request("/")
    assert headers["Referrer-Policy"] == "same-origin"
    host = board.url.removeprefix("http://")
    status, headers, _ = board.request("/pin/show", {}, {"Origin": "http://" + host.upper()})
    assert status == 303 and headers["Location"] == "/?shown"
    assert board.request("/pin/show", {}, {"Origin": "null"})[0] == 403


def test_a_broken_config_can_still_be_fixed_from_the_page(board):
    board.hotspot()
    board.config.write_text("{not json")
    status, _, html = board.request("/")
    assert status == 200 and "be read (" in html
    assert board.request("/save", SAVE)[0] == 303
    assert board.saved()["parks"] == ["EPCOT"]
    assert (board.config.parent / "board-config.json.bak").read_text() == "{not json"


def test_only_known_save_outcomes_are_shown(board):
    board.hotspot()
    html = board.request("/?saved=<script>alert(1)</script>")[2]
    assert "alert(1)" not in html and "notice good" not in html and "notice bad" not in html


def test_a_body_too_big_is_refused(board):
    board.hotspot()
    status, _, _ = board.request("/save", {"force_surprise": "x" * (server.MAX_BODY + 1)})
    assert status == 413 and board.saved() == CONFIG


def test_unknown_paths_are_not_found(board):
    assert board.request("/config.json")[0] == 404
    board.hotspot()
    assert board.request("/elsewhere", {})[0] == 404


# --- restarting the app

def test_restart_uses_try_restart_so_a_board_on_another_app_stays_on_it(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(server.shutil, "which", lambda name: "/bin/systemctl")
    monkeypatch.setattr(server.subprocess, "run", lambda args, **kw: calls.append(args) or
                        type("Done", (), {"returncode": 0, "stderr": ""})())
    assert Settings(str(tmp_path / "c.json")).restart_app() == "restarted"
    assert calls == [["systemctl", "try-restart", "LightningLane-Live-LED.service"]]


def test_a_failed_restart_is_logged_and_reported(monkeypatch, tmp_path):
    errors = []
    monkeypatch.setattr(server.debug, "error", errors.append)
    monkeypatch.setattr(server.shutil, "which", lambda name: "/bin/systemctl")
    monkeypatch.setattr(server.subprocess, "run", lambda args, **kw: type(
        "Done", (), {"returncode": 5, "stderr": "Unit not found."})())
    assert Settings(str(tmp_path / "c.json")).restart_app() == "failed"
    assert "Unit not found." in errors[0]

    def hang(args, **kw):
        raise server.subprocess.TimeoutExpired(args, kw["timeout"])
    monkeypatch.setattr(server.subprocess, "run", hang)
    assert Settings(str(tmp_path / "c.json")).restart_app() == "failed"


def test_no_systemd_or_no_unit_just_saves(monkeypatch, tmp_path):
    monkeypatch.setattr(server.shutil, "which", lambda name: None)
    assert Settings(str(tmp_path / "c.json")).restart_app() == "saved"
    assert Settings(str(tmp_path / "c.json"), restart_unit="").restart_app() == "saved"


def test_no_sound_cards_file_means_an_empty_list(tmp_path):
    assert Settings(cards_file=str(tmp_path / "none")).sound_cards() == []


def test_the_pi_model_and_size_are_picked_from_the_pi_and_saved(board):
    board.sign_in()
    html = board.request("/")[2]
    assert '<option value="auto" selected>Automatic (Pi 4)</option>' in html
    assert re.search(r'id="matrix_led_slowdown_gpio"[^>]*><option value="" selected>Pi 4 default: 4</option>', html)
    assert board.request("/save", dict(SAVE, pi_model="pizero2w", panel_size="64x64"))[0] == 303
    saved = board.saved()
    assert saved["pi_model"] == "pizero2w" and (saved["matrix"]["led_cols"], saved["matrix"]["led_rows"]) == (64, 64)
    status, _, html = board.request("/save", dict(SAVE, pi_model="pi5"))
    assert status == 400 and "Pi model: &#x27;pi5&#x27; isn&#x27;t one of" in html


def test_a_volume_only_save_sets_the_speaker_now_without_a_restart(board, monkeypatch):
    set_to = []
    monkeypatch.setattr(server, "set_volume", lambda settings: set_to.append(settings.volume) or True)
    board.sign_in()
    status, headers, _ = board.request("/save", SAVE)  # trips change: a restart
    assert headers["Location"] == "/?saved=restarted" and board.restarts == [1]
    status, headers, _ = board.request("/save", dict(SAVE, sound_volume="55"))
    assert status == 303 and headers["Location"] == "/?saved=volume"
    assert set_to == [55] and board.restarts == [1], "no second restart"
    assert board.saved()["sound"]["volume"] == 55
    assert "no restart needed" in board.request("/?saved=volume")[2]
    monkeypatch.setattr(server, "set_volume", lambda settings: False)
    assert board.request("/save", dict(SAVE, sound_volume="60"))[1]["Location"] == "/?saved=volume_failed"
    assert "the speaker didn't change" in board.request("/?saved=volume_failed")[2]


def test_volume_only_is_true_only_when_nothing_else_changed():
    old = {"sound": {"enabled": True, "volume": 80}, "parks": ["EPCOT"]}
    assert server.volume_only(old, {"sound": {"enabled": True, "volume": 50}, "parks": ["EPCOT"]})
    assert server.volume_only(old, {"sound": {"enabled": True}, "parks": ["EPCOT"]}), "back to the default"
    assert not server.volume_only(old, old)
    assert not server.volume_only(old, {"sound": {"enabled": False, "volume": 50}, "parks": ["EPCOT"]})
    assert not server.volume_only(old, {"sound": {"enabled": True, "volume": 50}, "parks": ["MK"]})
    assert not server.volume_only({}, {})


def _volume(board, **fields):
    status, _, body = board.request("/volume", dict(SAVE, **fields), {"Accept": "application/json"})
    return status, json.loads(body)


def test_set_volume_sets_the_speaker_and_saves_only_the_volume_with_no_restart(board, monkeypatch):
    set_to = []
    monkeypatch.setattr(server, "set_volume", lambda settings: set_to.append((settings.volume, settings.device)) or True)
    board.sign_in()
    status, reply = _volume(board, volume_action="set", sound_volume="45", sound_device="plughw:CARD=Device,DEV=0",
                            park="Cedar Point")
    assert status == 200 and reply == {"ok": True, "message": "Volume set to 45% and saved."}
    assert set_to == [(45, "plughw:CARD=Device,DEV=0")], "on the speaker the form picks"
    assert board.saved() == dict(CONFIG, sound={"volume": 45}), "the parks and the rest stay as saved"
    assert board.restarts == []


def test_set_volume_says_when_the_speaker_didnt_change_or_the_volume_is_bad(board, monkeypatch):
    monkeypatch.setattr(server, "set_volume", lambda settings: False)
    board.sign_in()
    assert _volume(board, volume_action="set", sound_volume="45")[1] == \
        {"ok": False, "message": "Saved 45%, but the speaker didn't change: the board's log says why."}
    assert _volume(board, volume_action="set", sound_volume="loud")[1] == \
        {"ok": False, "message": "Volume should be 0 to 100, not 'loud'."}
    assert board.saved()["sound"] == {"volume": 45}


def test_a_test_sound_plays_at_the_forms_volume_and_saves_nothing(board, monkeypatch):
    played = []
    monkeypatch.setattr(server, "play_test",
                        lambda settings: played.append((settings.volume, settings.device)) or (True, "Played a chime at 30%."))
    board.sign_in()
    assert _volume(board, volume_action="test", sound_volume="30") == (200, {"ok": True, "message": "Played a chime at 30%."})
    assert played == [(30, None)] and board.saved() == CONFIG and board.restarts == []


def test_the_volume_buttons_need_sign_in_and_a_known_action(board):
    status, headers, _ = board.request("/volume", dict(SAVE, volume_action="set", sound_volume="45"))
    assert status == 303 and headers["Location"] == "/", "signed out: back to the PIN"
    assert board.saved() == CONFIG
    board.sign_in()
    assert _volume(board, volume_action="louder") == (400, {"ok": False, "message": "That isn't a volume button."})
    status, _, _ = board.request("/volume", dict(SAVE, volume_action="set"), {"Origin": "http://evil.example"})
    assert status == 403 and board.saved() == CONFIG


def test_with_pushover_keys_the_sign_in_page_sends_the_pin_to_a_phone(board, monkeypatch):
    assert "/pin/send" not in board.request("/")[2], "no keys: the page stays as it was"
    assert board.request("/pin/send", {})[1]["Location"] == "/", "and the button does nothing"
    board.config.write_text(json.dumps(dict(CONFIG, pushover={"user_key": "u-1", "app_token": "t-2"})))
    sent, logs = [], []
    board.settings.send_pushover = lambda keys, pin, name, left: sent.append((keys, pin, left))
    for level in ("log", "info", "warning", "error"):  # the request log and the gate's
        monkeypatch.setattr(server.debug, level, logs.append)
    status, _, html = board.request("/")
    assert status == 200 and 'action="/pin/send"' in html
    status, headers, _ = board.request("/pin/send", {})
    assert status == 303 and headers["Location"] == "/?sent=sent"
    with open(board.gate.pin_file) as f:
        pin = f.read().split()[0]
    assert len(sent) == 1 and sent[0][:2] == (("u-1", "t-2"), pin) and 0 < sent[0][2] <= server.PIN_SHOWN_S
    assert "on its way to your phone" in board.request("/?sent=sent")[2]
    assert board.request("/pin/send", {})[1]["Location"] == "/?sent=wait" and len(sent) == 1
    assert not any(pin in line for line in logs)
    status, headers, _ = board.request("/pin", {"pin": pin})
    assert status == 303 and "Set-Cookie" in headers, "the sent PIN signs in"


def test_an_unknown_send_outcome_in_the_address_shows_nothing(board):
    assert board.request("/?sent=<b>hi</b>")[2] == board.request("/")[2]


def test_signing_out_clears_the_cookie_and_the_session_so_the_page_asks_for_a_pin_again(board):
    board.sign_in()
    token = next(c.value for c in board.jar if c.name == server.COOKIE)
    status, _, html = board.request("/")
    assert 'action="/signout"' in html and "Signed in" in html
    status, headers, _ = board.request("/signout", {})
    assert status == 303 and headers["Location"] == "/?signedout"
    assert "Max-Age=0" in headers["Set-Cookie"] and "HttpOnly" in headers["Set-Cookie"]
    assert not list(board.jar) and not board.gate.signed_in(token), "the old cookie is no good even if kept"
    status, _, html = board.request("/?signedout")
    assert "Signed out." in html and 'action="/save"' not in html
    assert board.request("/save", SAVE)[0] == 303 and board.saved() == CONFIG, "nothing saved"
