class RequestException(Exception):
    pass


def get(*args, **kwargs):
    class Response:
        def json(self):
            return {}

        def raise_for_status(self):
            pass

    return Response()
