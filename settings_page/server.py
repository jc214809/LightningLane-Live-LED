"""The settings page's web server: python3 -m settings_page.server, run by board-setup.sh's
lll-settings.service from the app's folder, as root (it writes config.json and restarts the app).

Its own service, not part of disney.py, so a config.json that stops the app can still be fixed
here. While comitup's setup hotspot is up, anyone on it gets the page (they're in the room, with
the board); on the home network it asks for the PIN the board shows (pins.py). Standard library
only, so it runs on any board the app runs on.
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

from settings_page import page
from settings_page.form import apply_form
from settings_page.pins import PIN_SHOWN_S, SESSION_S, PinGate
from utils import debug
from utils.config import CONFIG_FILE
from utils.wifi_setup import hotspot_name

PORT = 8080  # comitup's own page has port 80 while the hotspot is up
APP_UNIT = "LightningLane-Live-LED.service"
# comitup's hotspot hands out addresses here (its page is http://10.41.0.1/).
HOTSPOT_NETWORK = ip_network("10.41.0.0/16")
SOUND_CARDS = "/proc/asound/cards"
MAX_BODY = 64 * 1024
COOKIE = "lll_settings"
RESTART_TIMEOUT_S = 30


class Settings:
    """What the handlers share: where config.json is, the PIN gate, and one save at a time."""

    def __init__(self, config_path=CONFIG_FILE, gate=None, restart_unit=APP_UNIT,
                 state_file=None, cards_file=SOUND_CARDS):
        self.config_path, self.restart_unit, self.cards_file = config_path, restart_unit, cards_file
        self.gate = gate or PinGate()
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
        """Write config.json whole or not at all, keeping the last one as config.json.bak, with the
        old file's owner and mode (the user's, 600, as board-setup.sh made it)."""
        path = self.config_path
        temp = path + ".new"
        try:
            old = os.stat(path)
        except FileNotFoundError:
            old = None
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, old.st_mode & 0o777 if old else 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        if old:
            try:
                os.chown(temp, old.st_uid, old.st_gid)
            except PermissionError:  # not root (a dev machine): it's ours already
                pass
            shutil.copy2(path, path + ".bak")
        os.replace(temp, path)

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
        return origin is None or urlsplit(origin).netloc == self.headers.get("Host")

    # --- responses

    def _send(self, status, html, headers=()):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
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
        return page.settings_page(config if config is not None else loaded, self.settings.sound_cards(),
                                  self._in_setup(), problems, saved, board_name(), problem)

    # --- routes

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != "/":
            return self._send(404, page.message_page("Not found", "There's nothing at this address."))
        query = parse_qs(url.query, keep_blank_values=True)  # "?wrong", "?shown"
        if not self._allowed():
            return self._send(200, page.pin_page(PIN_SHOWN_S if "shown" in query else None, "wrong" in query,
                                                 board_name()))
        saved = query.get("saved", [None])[0]
        self._send(200, self._page(saved=saved if saved in page.SAVED else None))

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
        if path == "/pin":
            token = self.settings.gate.try_pin((form.get("pin") or [""])[0])
            if not token:
                return self._redirect("/?wrong")
            return self._redirect("/", [("Set-Cookie", f"{COOKIE}={token}; Max-Age={SESSION_S}; Path=/; "
                                                       f"HttpOnly; SameSite=Strict")])
        if path != "/save":
            return self._send(404, page.message_page("Not found", "There's nothing at this address."))
        if not self._allowed():
            return self._redirect("/")
        with self.settings.save_lock:
            config, _ = self.settings.load()
            new, problems = apply_form(config, form)
            if problems:
                debug.info(f"Settings page: not saved: {'; '.join(problems)}")
                return self._send(400, self._page(problems, config=new))
            try:
                self.settings.save(new)
            except OSError as e:
                debug.error(f"Settings page: can't save {self.settings.config_path}: {e}")
                return self._send(500, self._page([f"Couldn't save: {e}"], config=new))
        debug.info(f"Settings page: saved {self.settings.config_path} (from {self.client_address[0]}).")
        self._redirect(f"/?saved={self.settings.restart_app()}")


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
    server = make_server(Settings(args.config, restart_unit=args.restart_unit), port=args.port)
    debug.info(f"Settings page on port {args.port}, for {os.path.abspath(args.config)}.")
    server.serve_forever()


if __name__ == "__main__":
    main()
