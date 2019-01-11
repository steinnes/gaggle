from apiclient import discovery
import aiohttp

import httplib2


class MemoryCache:
    _CACHE = {}

    def get(self, key):
        hit = self._CACHE.get(key)
        if hit is not None:
            print("Cache hit!")
        return self._CACHE.get(key)

    def set(self, key, value):
        self._CACHE[key] = value



class Service:
    def __init__(self, discovery_client, gaggle_client):
        self._disco_client = discovery_client
        self._gaggle_client = gaggle_client

    def _request(self, name):
        async def inner(*args, **kwargs):
            cooked_request = getattr(self._disco_client, name)(*args, **kwargs)
            headers = {'Authorization': f'Bearer {self._gaggle_client.access_token}', **cooked_request.headers}
            async with aiohttp.ClientSession(headers=headers) as session:
                if cooked_request.method == 'GET':
                    return await session.get(cooked_request.uri)
                elif cooked_request.method == 'POST':
                    return await session.post(cooked_request.uri, data=cooked_request.body)
        return inner

    def __getattribute__(self, attr):
        if attr.startswith('_'):
            # my own attributes
            return object.__getattribute__(self, attr)
        else:
            # an attribute on self._disco_client, can either be a resource, in which case we need to
            # re-wrap it as a Service object
            # OR:
            # it's a method which will elicit a request, which we pass into self._request(..)
            subject = getattr(self._disco_client, attr)
            if subject.__func__.__name__ == 'methodResource':
                return Service(subject(), self._gaggle_client)
            elif subject.__func__.__name__ == 'method':
                return self._request(attr)


class Client:
    def __init__(self, access_token, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.http = httplib2.Http()
        self._reals = ['access_token', 'refresh_token', 'http']
        self._services = {}

    def _builder(self, service_name):
        def inner(version=None):
            srv_key = f'{service_name}:{version}'
            if srv_key not in self._services:
                args = [service_name,]
                if version is not None:
                    args.append(version)
                srv = discovery.build(*args, http=self.http, cache=MemoryCache())
                self._services[srv_key] = Service(srv, self)
            return self._services[srv_key]

        return inner

    def __getattribute__(self, attr):
        real = object.__getattribute__(self, '_reals')
        if attr.startswith('_') or attr in real:
            return object.__getattribute__(self, attr)
        # let's treat this attribute as a google service like 'drive'
        return self._builder(attr)

