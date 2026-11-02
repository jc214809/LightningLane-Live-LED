import io
import json
import urllib.error
from urllib.parse import parse_qs

import pytest

import settings_page.pushover as pushover
from settings_page.pushover import PushoverError, send_pin

KEYS = ("u-user", "t-token")


class Urlopen:
    """A fake urllib.request.urlopen: records the request, answers with reply (bytes) or raises it."""
    def __init__(self, reply=b'{"status":1,"request":"abc"}'):
        self.reply, self.requests = reply, []

    def __call__(self, request, timeout=None, context=None):
        self.requests.append((request, timeout))
        if isinstance(self.reply, Exception):
            raise self.reply
        return io.BytesIO(self.reply)

    def fields(self):
        return {k: v[0] for k, v in parse_qs(self.requests[0][0].data.decode()).items()}


@pytest.fixture
def urlopen(monkeypatch):
    fake = Urlopen()
    monkeypatch.setattr(pushover.urllib.request, "urlopen", fake)
    return fake


def test_the_pin_goes_in_the_message_and_it_deletes_itself_when_the_pin_runs_out(urlopen):
    send_pin(KEYS, "4821", "DonaldPi", 120)
    request, timeout = urlopen.requests[0]
    assert request.full_url == pushover.MESSAGES_URL and request.get_method() == "POST" and timeout
    fields = urlopen.fields()
    assert fields["user"] == "u-user" and fields["token"] == "t-token"
    assert "4821" in fields["message"] and "2 minutes" in fields["message"]
    assert fields["title"] == "DonaldPi settings" and fields["ttl"] == "120"
    assert "4821" not in request.full_url and "t-token" not in request.full_url


def test_a_refusal_says_pushovers_reason(urlopen):
    body = json.dumps({"status": 0, "errors": ["application token is invalid"]}).encode()
    urlopen.reply = urllib.error.HTTPError(pushover.MESSAGES_URL, 400, "Bad Request", {}, io.BytesIO(body))
    with pytest.raises(PushoverError, match="application token is invalid"):
        send_pin(KEYS, "4821", "DonaldPi", 120)


def test_a_refusal_with_no_reason_names_the_status(urlopen):
    urlopen.reply = urllib.error.HTTPError(pushover.MESSAGES_URL, 429, "Too Many", {}, io.BytesIO(b"<html>"))
    with pytest.raises(PushoverError, match="HTTP 429"):
        send_pin(KEYS, "4821", "DonaldPi", 120)


@pytest.mark.parametrize("reply", [b'{"status":0}', b'{"errors":["user key is invalid"]}', b"[]"])
def test_a_reply_that_isnt_status_1_is_a_failure(urlopen, reply):
    urlopen.reply = reply
    with pytest.raises(PushoverError):
        send_pin(KEYS, "4821", "DonaldPi", 30)


def test_bad_json_and_network_errors_are_raised(urlopen):
    urlopen.reply = b"not json"
    with pytest.raises(ValueError):
        send_pin(KEYS, "4821", "DonaldPi", 30)
    urlopen.reply = urllib.error.URLError("no internet")
    with pytest.raises(OSError):
        send_pin(KEYS, "4821", "DonaldPi", 30)
