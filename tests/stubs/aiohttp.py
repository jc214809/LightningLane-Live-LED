class FakeResponse:
    def __init__(self, status=200, data=None):
        self.status = status
        self._data = data or {}

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

class ClientWSTimeout:
    def __init__(self, ws_receive=None, ws_close=None):
        self.ws_receive = ws_receive
        self.ws_close = ws_close

class ClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get(self, *args, **kwargs):
        return FakeResponse()
