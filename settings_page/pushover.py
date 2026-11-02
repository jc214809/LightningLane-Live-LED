"""Sends the settings page's PIN to a phone through Pushover (pushover.net), for signing in to a
board you can't see. Optional: only with config.json's "pushover" keys (utils.config.pushover_keys).
The PIN goes only in the message, never in a log or an error.
"""
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request

import certifi

MESSAGES_URL = "https://api.pushover.net/1/messages.json"
TIMEOUT_S = 10


class PushoverError(Exception):
    """Pushover turned the message down; the text is its reason (a bad key, the month's limit)."""


def send_pin(keys, pin, board, seconds_left):
    """Send the PIN. keys: (user_key, app_token). The message deletes itself from the phone when
    the PIN runs out (Pushover's ttl). Raises OSError (network), ValueError (a bad reply) or
    PushoverError."""
    user, token = keys
    minutes = max(1, round(seconds_left / 60))
    data = urllib.parse.urlencode({
        "token": token, "user": user, "title": f"{board} settings",
        "message": f"PIN for {board}'s settings page: {pin}\nIt works for {minutes} minute{'s' if minutes > 1 else ''}.",
        "ttl": max(1, int(seconds_left)),
    }).encode()
    request = urllib.request.Request(MESSAGES_URL, data=data,
                                     headers={"User-Agent": "LightningLane-Live-LED settings page"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S,
                                    context=ssl.create_default_context(cafile=certifi.where())) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as e:  # 4xx: Pushover says why in the body
        raise PushoverError(_reason(e) or f"HTTP {e.code}") from None
    if not isinstance(reply, dict) or reply.get("status") != 1:
        raise PushoverError(_errors(reply) or "it didn't accept the message")


def _reason(error):
    try:
        return _errors(json.load(error))
    except (OSError, ValueError):
        return None


def _errors(reply):
    errors = reply.get("errors") if isinstance(reply, dict) else None
    return "; ".join(str(e) for e in errors) if isinstance(errors, list) else None
