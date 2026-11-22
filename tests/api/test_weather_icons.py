from io import BytesIO

import pytest
import requests
from PIL import Image

from api import weather_icons


def _png():
    buf = BytesIO()
    Image.new("RGB", (50, 50), (10, 20, 30)).save(buf, "PNG")
    return buf.getvalue()


class Response:
    def __init__(self, content=b"", status_error=None):
        self.content = content
        self._error = status_error

    def raise_for_status(self):
        if self._error:
            raise self._error


def _timeout():
    raise requests.exceptions.Timeout("slow")


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    weather_icons._reset()
    monkeypatch.setattr(weather_icons.debug, "log", lambda m: None)
    yield
    weather_icons._reset()


def _get(monkeypatch, behaviour):
    calls = []

    def fake_get(url, timeout=None):
        calls.append((url, timeout))
        return behaviour()

    monkeypatch.setattr(weather_icons.requests, "get", fake_get)
    return calls


def test_success_resizes_caches_and_logs_once(monkeypatch):
    logged = []
    monkeypatch.setattr(weather_icons.debug, "log", logged.append)
    calls = _get(monkeypatch, lambda: Response(_png()))
    img = weather_icons.fetch_icon("01d")
    assert img.size == (15, 15)
    assert weather_icons.fetch_icon("01d") is img
    assert calls == [("https://openweathermap.org/img/wn/01d.png", weather_icons.ICON_TIMEOUT_S)]
    assert logged == ["Downloaded weather icon 01d"]


@pytest.mark.parametrize(
    "behaviour",
    [
        _timeout,
        lambda: Response(status_error=requests.exceptions.HTTPError("404")),
        lambda: Response(b"not an image"),
    ],
)
def test_failures_return_none_and_log(monkeypatch, behaviour):
    errors = []
    monkeypatch.setattr(weather_icons.debug, "error", errors.append)
    _get(monkeypatch, behaviour)
    assert weather_icons.fetch_icon("10d") is None
    assert len(errors) == 1


def test_failed_icon_backs_off_then_retries(monkeypatch):
    monkeypatch.setattr(weather_icons.debug, "error", lambda m: None)
    calls = _get(monkeypatch, _timeout)
    now = [1000.0]
    monkeypatch.setattr(weather_icons.time, "monotonic", lambda: now[0])
    for _ in range(30):
        assert weather_icons.fetch_icon("10d") is None
    assert len(calls) == 1
    now[0] += weather_icons.ICON_RETRY_S
    weather_icons.fetch_icon("10d")
    assert len(calls) == 2


def test_recovery_after_failure_caches(monkeypatch):
    monkeypatch.setattr(weather_icons.debug, "error", lambda m: None)
    state = {"ok": False}

    def behaviour():
        if not state["ok"]:
            _timeout()
        return Response(_png())

    calls = _get(monkeypatch, behaviour)
    now = [0.0]
    monkeypatch.setattr(weather_icons.time, "monotonic", lambda: now[0])
    assert weather_icons.fetch_icon("02d") is None
    state["ok"] = True
    now[0] += weather_icons.ICON_RETRY_S
    assert weather_icons.fetch_icon("02d") is not None
    weather_icons.fetch_icon("02d")
    assert len(calls) == 2
