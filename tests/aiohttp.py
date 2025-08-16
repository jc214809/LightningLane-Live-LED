class ClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        class Response:
            async def json(self):
                return {}

            def raise_for_status(self):
                pass

        return Response()
