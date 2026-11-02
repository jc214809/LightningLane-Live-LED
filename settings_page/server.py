"""The settings page's web server: python3 -m settings_page.server, run by board-setup.sh's
lll-settings.service from the app's folder, as root (it writes config.json and restarts the app).

Its own service, not part of disney.py, so a config.json that stops the app can still be fixed
here. While comitup's setup hotspot is up, anyone on it gets the page (they're in the room, with
the board); on the home network it asks for the PIN the board shows (pins.py), which Pushover can
also send to a phone (pushover.py). Standard library
and certifi (the app's own requirement) only, so it runs on any board the app runs on.
"""
import argparse
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import threading
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address, ip_network
from urllib.parse import parse_qs, urlsplit

import cli
from settings_page import page, pushover
from settings_page.form import apply_form, chosen_device, panel_choices, volume_from_form
from settings_page.park_names import ParkNames
from settings_page.pins import PIN_SHOWN_S, SESSION_S, PinGate
from utils import debug
from utils.config import CONFIG_FILE, pushover_keys, save_config, sound_settings
from utils.sound import play_test, set_volume
from utils.wifi_setup import hotspot_name

PORT = 8080  # comitup's own page has port 80 while the hotspot is up
APP_UNIT = "LightningLane-Live-LED.service"
# comitup's hotspot hands out addresses here (its page is http://10.41.0.1/).
HOTSPOT_NETWORK = ip_network("10.41.0.0/16")
SOUND_CARDS = "/proc/asound/cards"
MAX_BODY = 64 * 1024
COOKIE = "lll_settings"
RESTART_TIMEOUT_S = 30
PARK_NAMES_FILE = "park_names.json"


class Settings:
    """What the handlers share: where config.json is, the PIN gate, the park names (kept in
    park_names.json beside config.json), and one save at a time. send_pushover: pushover.send_pin."""

    def __init__(self, config_path=CONFIG_FILE, gate=None, restart_unit=APP_UNIT,
                 state_file=None, cards_file=SOUND_CARDS, park_names=None, model_file=cli.MODEL_FILE,
                 send_pushover=pushover.send_pin):
        self.config_path, self.restart_unit, self.cards_file = config_path, restart_unit, cards_file
        self.model_file, self.send_pushover = model_file, send_pushover
        self.gate = gate or PinGate()
        self.park_names = park_names or ParkNames(
            os.path.join(os.path.dirname(os.path.abspath(config_path)), PARK_NAMES_FILE))
        self.state_file = state_file
        self.save_lock = threading.Lock()

    def hotspot(self):
        return hotspot_name(self.state_file) if self.state_file else hotspot_name()

    def load(self):
        """config.json, or {} with the reason when it's missing or broken (the page can still fix it)."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)
        except FileNotFoundError:
            return {}, f"{self.config_path} doesn't exist yet: saving makes it."
        except (OSError, ValueError) as e:
            return {}, f"{self.config_path} can't be read ({e}): saving replaces it (the old one is kept as .bak)."
        if not isinstance(config, dict):
            return {}, f"{self.config_path} isn't a settings object: saving replaces it (the old one is kept as .bak)."
        return config, None

    def save(self, config):
        """config.json, written whole with a .bak and its owner and mode kept (utils.config.save_config)."""
        save_config(config, self.config_path)

    def restart_app(self):
        """"restarted", "saved" (nothing to restart: no unit set, or no systemd) or "failed" (logged).
        try-restart only restarts the app if it's running, so a board running another app stays on it."""
        if not self.restart_unit or not shutil.which("systemctl"):
            return "saved"
        try:
            done = subprocess.run(["systemctl", "try-restart", self.restart_unit], capture_output=True,
                                  text=True, timeout=RESTART_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as e:
            debug.error(f"Settings page: restarting {self.restart_unit} failed: {e}")
            return "failed"
        if done.returncode:
            problem = done.stderr.strip() or f"systemctl exited {done.returncode}"
            debug.error(f"Settings page: restarting {self.restart_unit} failed: {problem}")
            return "failed"
        debug.info(f"Settings page: restarted {self.restart_unit}.")
        return "restarted"

    def pushover_keys(self):
        """config.json's Pushover keys, or None: the sign-in page offers to send the PIN only with them."""
        return pushover_keys(self.load()[0])

    def send_pin(self):
        """The sign-in page's Send button: PinGate.send_pin's outcome, or "off" with no keys."""
        keys = self.pushover_keys()
        if not keys:
            return "off"
        return self.gate.send_pin(lambda pin, left: self.send_pushover(keys, pin, board_name(), left))

    def panel_choices(self, config):
        """The Pi model and Panel size dropdowns for this Pi (form.panel_choices)."""
        return panel_choices(config, *cli.pi_model(self.model_file))

    def set_volume(self, config):
        """Set the speaker to config's volume now, as the app does before each show: "volume" if
        amixer took it, "volume_failed" if not (logged)."""
        return "volume" if set_volume(sound_settings(config)) else "volume_failed"

    def keep_volume(self, form):
        """The Set volume button: set the form's volume on its speaker now and save only that to
        config.json, with no restart. (ok, message), or (False, the problem) with nothing saved."""
        volume, problem = volume_from_form(form)
        if problem:
            return False, problem
        with self.save_lock:
            config, _ = self.load()
            if not isinstance(config.get("sound"), dict):
                config["sound"] = {}
            config["sound"]["volume"] = volume
            try:
                self.save(config)
            except OSError as e:
                debug.error(f"Settings page: can't save {self.config_path}: {e}")
                return False, f"Couldn't save: {e}"
        debug.info(f"Settings page: volume {volume}% saved.")
        if not set_volume(sound_settings(config)._replace(device=chosen_device(form))):
            return False, f"Saved {volume}%, but the speaker didn't change: the board's log says why."
        return True, f"Volume set to {volume}% and saved."

    def test_sound(self, form):
        """The Play test sound button: a few seconds at the form's volume on its speaker, saving
        nothing. (ok, message)."""
        volume, problem = volume_from_form(form)
        if problem:
            return False, problem
        config, _ = self.load()
        return play_test(sound_settings(config)._replace(device=chosen_device(form), volume=volume))

    def sound_cards(self):
        """Each ALSA card as an aplay device, by name so it survives renumbering ("plughw:CARD=Device,DEV=0")."""
        try:
            with open(self.cards_file, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return []
        return [f"plughw:CARD={name},DEV=0" for name in re.findall(r"^\s*\d+\s+\[(\S+)\s*\]", text, re.M)]


class Handler(BaseHTTPRequestHandler):
    settings: Settings  # set on the subclass make_server builds
    timeout = 15  # a client that stalls mid-request doesn't hold a thread

    def log_message(self, fmt, *args):
        debug.log(f"Settings page: {self.address_string()} {fmt % args}")

    # --- who may see the page

    def _in_setup(self):
        """The hotspot's name while it's up and this browser is on it, else None."""
        name = self.settings.hotspot()
        try:
            on_hotspot = ip_address(self.client_address[0]) in HOTSPOT_NETWORK
        except ValueError:
            on_hotspot = False
        return name if name and on_hotspot else None

    def _token(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        return jar[COOKIE].value if COOKIE in jar else None

    def _allowed(self):
        return bool(self._in_setup()) or self.settings.gate.signed_in(self._token())

    def _same_origin(self):
        """A form posted from another site (a page open in the same browser) is turned away."""
        origin = self.headers.get("Origin")
        return origin is None or urlsplit(origin).netloc.lower() == (self.headers.get("Host") or "").lower()

    # --- responses

    def _send(self, status, html, headers=()):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        # Not no-referrer: with it, browsers send "Origin: null" with the page's own forms, which
        # _same_origin then turns away.
        self.send_header("Referrer-Policy", "same-origin")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, where, headers=()):
        self.send_response(303)
        self.send_header("Location", where)
        self.send_header("Content-Length", "0")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _form(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if not 0 <= length <= MAX_BODY:
            return None
        return parse_qs(self.rfile.read(length).decode("utf-8", "replace"), keep_blank_values=True)

    def _page(self, problems=(), saved=None, config=None):
        loaded, problem = self.settings.load()
        config = config if config is not None else loaded
        return page.settings_page(config, self.settings.sound_cards(), self._in_setup(), problems, saved,
                                  board_name(), problem, self.settings.park_names.names(),
                                  self.settings.panel_choices(config))

    # --- routes

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != "/":
            return self._send(404, page.message_page("Not found", "There's nothing at this address."))
        query = parse_qs(url.query, keep_blank_values=True)  # "?wrong", "?shown", "?sent=..."
        if not self._allowed():
            sent = query.get("sent", [None])[0]
            return self._send(200, page.pin_page(PIN_SHOWN_S if "shown" in query else None, "wrong" in query,
                                                 board_name(), bool(self.settings.pushover_keys()),
                                                 sent if sent in page.SENT else None))
        saved = query.get("saved", [None])[0]
        self._send(200, self._page(saved=saved if saved in page.SAVED else None))

    def _volume(self, form):
        """POST /volume, the page script's Volume buttons: volume_action "set" or "test"; answers
        {"ok": ..., "message": ...}."""
        action = (form.get("volume_action") or [""])[0]
        if action == "set":
            ok, message = self.settings.keep_volume(form)
        elif action == "test":
            ok, message = self.settings.test_sound(form)
        else:
            return self._send_json(400, {"ok": False, "message": "That isn't a volume button."})
        self._send_json(200, {"ok": ok, "message": message})

    def do_POST(self):
        path = urlsplit(self.path).path
        if not self._same_origin():
            return self._send(403, page.message_page("Not allowed", "That form came from another site."))
        form = self._form()
        if form is None:
            return self._send(413, page.message_page("Too big", "That's too much to save."))
        if path == "/pin/show":
            self.settings.gate.show_pin()
            return self._redirect("/?shown")
        if path == "/pin/send":
            outcome = self.settings.send_pin()
            return self._redirect("/" if outcome == "off" else f"/?sent={outcome}")
        if path == "/pin":
            token = self.settings.gate.try_pin((form.get("pin") or [""])[0])
            if not token:
                return self._redirect("/?wrong")
            return self._redirect("/", [("Set-Cookie", f"{COOKIE}={token}; Max-Age={SESSION_S}; Path=/; "
                                                       f"HttpOnly; SameSite=Strict")])
        if path not in ("/save", "/volume"):
            return self._send(404, page.message_page("Not found", "There's nothing at this address."))
        if not self._allowed():
            return self._redirect("/")
        if path == "/volume":
            return self._volume(form)
        with self.settings.save_lock:
            config, _ = self.settings.load()
            new, problems = apply_form(config, form, self.settings.park_names.names())
            if problems:
                debug.info(f"Settings page: not saved: {'; '.join(problems)}")
                return self._send(400, self._page(problems, config=new))
            try:
                self.settings.save(new)
            except OSError as e:
                debug.error(f"Settings page: can't save {self.settings.config_path}: {e}")
                return self._send(500, self._page([f"Couldn't save: {e}"], config=new))
        debug.info(f"Settings page: saved {self.settings.config_path} (from {self.client_address[0]}).")
        # Volume alone needs no restart: set it now (the app rereads it before each show), so a
        # show that's playing carries on at the new volume.
        outcome = self.settings.set_volume(new) if volume_only(config, new) else self.settings.restart_app()
        self._redirect(f"/?saved={outcome}")


def volume_only(old, new):
    """True if the only change from old to new config is sound.volume."""
    def without_volume(config):
        config = dict(config)
        if isinstance(config.get("sound"), dict):
            config["sound"] = {k: v for k, v in config["sound"].items() if k != "volume"}
        return config
    volume = lambda config: (config.get("sound") or {}).get("volume") if isinstance(config.get("sound"), dict) else None
    return volume(old) != volume(new) and without_volume(old) == without_volume(new)


def board_name():
    """The board's hostname, for the page's header."""
    return socket.gethostname().split(".")[0]


def make_server(settings, host="", port=PORT):
    handler = type("SettingsHandler", (Handler,), {"settings": settings})
    return ThreadingHTTPServer((host, port), handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="The board's settings page.")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--config", default=CONFIG_FILE, help="config.json's path (default: in the working folder)")
    parser.add_argument("--restart-unit", default=APP_UNIT, help="the app's systemd unit, restarted after a save; "
                                                                 "'' for none")
    args = parser.parse_args(argv)
    debug.logger.setLevel(logging.INFO)
    # To the journal only: the app's logs/app.log rotates in the app's process, and two writers
    # rotating one file lose lines.
    if debug.file_handler is not None:
        debug.logger.removeHandler(debug.file_handler)
    settings = Settings(args.config, restart_unit=args.restart_unit)
    settings.park_names.refresh_if_due()  # at boot, so the list is ready before anyone opens the page
    server = make_server(settings, port=args.port)
    debug.info(f"Settings page on port {args.port}, for {os.path.abspath(args.config)}.")
    server.serve_forever()


if __name__ == "__main__":
    main()
