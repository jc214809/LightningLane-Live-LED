"""Fakes for aiohttp's WebSocket session and connection, shared by the legacy and preview loop tests."""


# --- connection settings ---

class _FakeWS:
    """Minimal stand-in for aiohttp's ClientWebSocketResponse: connects,
    accepts subscriptions, yields no messages, then closes."""

    close_code = 1000

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    sent_frames = None  # ws_connect hands it the captured list

    async def send_json(self, payload):
        if self.sent_frames is not None:
            self.sent_frames.append(payload)

    def exception(self):
        return None


class _FakeSession:
    def __init__(self, captured):
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def ws_connect(self, url, **kwargs):
        self._captured.update(kwargs, url=url)
        ws = _FakeWS()
        ws.sent_frames = self._captured.setdefault("sent", [])
        return ws


class _RefusingSession(_FakeSession):
    def __init__(self, error):
        super().__init__({})
        self._error = error

    def ws_connect(self, url, **kwargs):
        raise self._error
