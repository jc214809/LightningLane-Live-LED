"""The settings server over real HTTP, on a free port, with config.json and comitup's state in a
temp folder. The file is "board-config.json": tests/stubs/conftest.py fakes every "config.json"."""
import json
import os
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from urllib.parse import urlencode

import pytest

import settings_page.server as server
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
        self.settings = Settings(str(self.config), self.gate, state_file=str(self.state), cards_file=str(self.cards))
        monkeypatch.setattr(self.settings, "restart_app", lambda: self.restarts.append(1) or "restarted")
        self.httpd = make_server(self.settings, "127.0.0.1", 0)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

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


def test_on_the_setup_hotspot_no_pin_is_needed(board):
    board.hotspot()
    status, _, html = board.request("/")
    assert 'action="/save"' in html and "Setup mode" in html and "Disneypi-setup" in html
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
