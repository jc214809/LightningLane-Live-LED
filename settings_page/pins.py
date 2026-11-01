"""The settings page's PIN, on the home network: asking for one puts a 4-digit PIN on the LED
board (the app reads PIN_FILE; utils/settings_pin.py) for PIN_SHOWN_S, and typing it in gives that
browser a session for SESSION_S. A PIN takes TRIES_PER_PIN guesses, and a new one comes only once
the last has run out, so guessing is slow and lights up the board. Nothing is saved: a restart of
the server signs everyone out.
"""
import os
import secrets
import threading
import time

from utils import debug

PIN_FILE = "/run/lll-settings-pin"  # /run is cleared at boot, so a PIN never outlives the server
PIN_DIGITS = 4
PIN_SHOWN_S = 120
SESSION_S = 60 * 60
TRIES_PER_PIN = 5
MAX_SESSIONS = 20  # a few phones and laptops; the oldest goes first


class PinGate:
    def __init__(self, pin_file=PIN_FILE, clock=time.time):
        self.pin_file, self.clock = pin_file, clock
        self._lock = threading.Lock()
        self._pin, self._expires, self._tries = None, 0.0, 0
        self._sessions = {}  # token: when it runs out

    def show_pin(self):
        """Put a PIN on the board, or keep the one that's up (or used up) until it runs out.
        Returns its seconds left."""
        with self._lock:
            now = self.clock()
            if now >= self._expires:
                self._pin = "".join(secrets.choice("0123456789") for _ in range(PIN_DIGITS))
                self._expires, self._tries = now + PIN_SHOWN_S, 0
                self._write(f"{self._pin} {self._expires:.0f}\n")
                debug.info("Settings page: a PIN is on the board.")
            return self._expires - now

    def try_pin(self, pin):
        """A session token for the right PIN while it's up, else None."""
        with self._lock:
            now = self.clock()
            if self._pin is None or now >= self._expires or self._tries >= TRIES_PER_PIN:
                return None
            if not secrets.compare_digest(str(pin).strip(), self._pin):
                self._tries += 1
                debug.warning(f"Settings page: wrong PIN ({self._tries} of {TRIES_PER_PIN} tries).")
                if self._tries >= TRIES_PER_PIN:
                    self._remove()  # off the board; no new one until this one's time is up
                return None
            self._pin = None
            self._remove()
            token = secrets.token_urlsafe(24)
            self._sessions = {t: end for t, end in self._sessions.items() if end > now}
            while len(self._sessions) >= MAX_SESSIONS:
                self._sessions.pop(min(self._sessions, key=self._sessions.get))
            self._sessions[token] = now + SESSION_S
            debug.info("Settings page: signed in with the PIN.")
            return token

    def signed_in(self, token):
        with self._lock:
            return bool(token) and self._sessions.get(token, 0) > self.clock()

    def _write(self, text):
        temp = self.pin_file + ".new"
        try:
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(temp, self.pin_file)
        except OSError as e:
            debug.error(f"Settings page: can't put the PIN on the board ({self.pin_file}): {e}")

    def _remove(self):
        try:
            os.remove(self.pin_file)
        except FileNotFoundError:
            pass
        except OSError as e:
            debug.error(f"Settings page: can't take the PIN off the board ({self.pin_file}): {e}")
