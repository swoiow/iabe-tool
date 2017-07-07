from collections import defaultdict

import requests
from suds.transport import Transport

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO

    StringIO = BytesIO  # PATCH: Case py3


class Requests2Transport(Transport):
    def __init__(self, session=None, **kwargs):
        super(Requests2Transport, self).__init__()
        self._session = session or requests.session()
        self.default_kw = {k: v for k, v in kwargs.items()}

    def open(self, request):
        response = self._session.get(request.url, params=request.message, **self.default_kw)
        return StringIO(response.content)

    def send(self, request):
        kwargs = defaultdict(dict, **self.default_kw)
        kwargs["headers"].update(request.headers)

        response = self._session.post(request.url, data=request.message, **kwargs)
        response.headers = response.headers
        response.message = response.content
        return response

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        if not isinstance(value, requests.Session):
            raise TypeError("session must be requests.Session class!")
        self._session = value
