class RequestException(Exception):
    pass

class Response:
    def __init__(self, status_code=200, json_data=None, content=b''):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException(f'Status code: {self.status_code}')

def get(*args, **kwargs):
    return Response()
