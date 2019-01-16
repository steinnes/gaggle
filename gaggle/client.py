import asyncio

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from apiclient import discovery

import httplib2


DEFAULT_GOOGLE_TOKEN_URI = 'https://oauth2.googleapis.com/token'


class GaggleServiceError(Exception):
    pass


class AccessDenied(GaggleServiceError):
    pass


class MemoryCache:
    _CACHE = {}

    def get(self, key):
        hit = self._CACHE.get(key)
        if hit is not None:
            print("Cache hit!")
        return self._CACHE.get(key)

    def set(self, key, value):
        self._CACHE[key] = value


class Retries:
    def __init__(self, num):
        self.count = num
        self.remaining = num

    def __call__(self):
        if self.remaining > 0:
            self.remaining -= 1
            return True
        return False


class Service:
    def __init__(self, session, discovery_client, gaggle_client, retries=None):
        if retries is None:
            retries = 5
        self._session = session
        self._retry = Retries(retries)
        self._disco_client = discovery_client
        self._gaggle_client = gaggle_client

    def _request(self, name):
        async def inner(*args, **kwargs):
            async def doit():
                cooked_request = getattr(self._disco_client, name)(*args, **kwargs)
                headers = {'Authorization': f'Bearer {self._gaggle_client.access_token}', **cooked_request.headers}
                if cooked_request.method == 'GET':
                    return await self._session.get(cooked_request.uri, headers=headers)
                elif cooked_request.method == 'POST':
                    return await self._session.post(cooked_request.uri, data=cooked_request.body, headers=headers)
            while True:
                if self._retry():
                    try:
                        response = await doit()
                        if response.status == 401:
                            self._gaggle_client.refresh_token()
                            response = await doit()
                            if response.status == 401:
                                raise AccessDenied("Access denied even after refreshing token")
                        break
                    except asyncio.TimeoutError as e:
                        # XXX: logging.log...
                        print("timeout:", e)
                else:
                    raise GaggleServiceError("Exhausted retries ({})".format(self._retry.count))

            return response
        return inner

    def _wrap(self, attr):
        # an attribute on self._disco_client, can either be a resource, in which case we need to
        # re-wrap it as a Service object
        # OR:
        # it's a method which will elicit a request, which we pass into self._request(..)
        subject = getattr(self._disco_client, attr)
        if subject.__func__.__name__ == 'methodResource':
            return Service(self._session, subject(), self._gaggle_client)
        elif subject.__func__.__name__ == 'method':
            return self._request(attr)

    def __getattribute__(self, attr):
        if attr.startswith('_'):
            # my own attributes
            return object.__getattribute__(self, attr)
        else:
            return self._wrap(attr)


class Client:
    _reals = ['access_token', 'credentials', 'refresh_token', 'http']

    def __init__(self, session, credentials: Credentials = None, **kwargs):
        if credentials is None:
            credentials = self._make_credentials(**kwargs)
        self.credentials = credentials
        self.access_token = credentials.token
        self.http = httplib2.Http()
        self._session = session
        self._services = {}

    @staticmethod
    def _make_credentials(*, token, refresh_token=None, id_token=None, token_uri=None, client_id=None, client_secret=None):  # noqa
        if token_uri is None:
            token_uri = DEFAULT_GOOGLE_TOKEN_URI
        return Credentials(token, refresh_token, id_token, token_uri, client_id, client_secret)

    def refresh_token(self):
        request = google.auth.transport.requests.Request()
        self.credentials.refresh(request)
        self.access_token = self.credentials.token

    def _builder(self, service_name):
        def inner(version=None):
            srv_key = f'{service_name}:{version}'
            if srv_key not in self._services:
                args = [service_name, ]
                if version is not None:
                    args.append(version)
                srv = discovery.build(*args, http=self.http, cache=MemoryCache())
                self._services[srv_key] = Service(self._session, srv, self)
            return self._services[srv_key]

        return inner

    def __getattribute__(self, attr):
        real = object.__getattribute__(self, '_reals')
        if attr.startswith('_') or attr in real:
            return object.__getattribute__(self, attr)
        # let's treat this attribute as a google service like 'drive'
        return self._builder(attr)
