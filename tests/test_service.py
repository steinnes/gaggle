import asyncio
import pytest
from collections import defaultdict

from unittest import mock

from googleapiclient.http import HttpRequest

from gaggle.client import AccessDenied, GaggleServiceError, Retries, Service


class FakeDiscoClient:
    def method(self, *args, **kwargs):
        return HttpRequest(None, None, uri='https://we-will-we-will.mock/you', method='GET')


class CallCounter:
    def __init__(self):
        self.calls = defaultdict(int)

    def __getattribute__(self, attr):
        if attr != 'calls':
            object.__getattribute__(self, 'calls')[attr] += 1
        return object.__getattribute__(self, attr)


def test_service_getattr_returns_actual_attr_if_private():
    s = Service(mock.Mock(), mock.Mock(), mock.Mock())
    with mock.patch('gaggle.client.Service._wrap') as mock_wrap:
        assert isinstance(s._retry, Retries)
    assert not mock_wrap.called


def test_service_wrapper_returns_service_for_resources_requests_for_methods():
    class FakeDiscoveredAPIService:
        def method(self, *args, **kwargs):
            return {'args': args, 'kwargs': kwargs}

        @classmethod
        def methodResource(cls):
            return cls()

        @property
        def a_method(self):
            return self.method

        @property
        def a_method_resource(self):
            return self.methodResource

    srv = Service(mock.Mock(), FakeDiscoveredAPIService(), mock.Mock())
    assert isinstance(srv.a_method_resource, Service)
    assert callable(srv.a_method)


@pytest.mark.asyncio
async def test_service_request_retries():

    class TimeoutingSession(CallCounter):
        async def get(self, *args, **kwargs):
            raise asyncio.TimeoutError("test")

    sess = TimeoutingSession()
    s = Service(sess, FakeDiscoClient(), mock.Mock(), retries=1)
    with pytest.raises(GaggleServiceError):
        await s.method()
    assert sess.calls['get'] == 2
    assert s._retry.remaining == 0

    sess = TimeoutingSession()
    s = Service(sess, FakeDiscoClient(), mock.Mock(), retries=0)
    with pytest.raises(GaggleServiceError):
        await s.method()
    assert sess.calls['get'] == 1
    assert s._retry.remaining == 0


@pytest.mark.asyncio
async def test_service_request_refresh_token():
    class UnauthorizedResponse:
        status = 401

        async def content(self):
            return "User not authorized to access this mock data"

    class UnauthorizingSession(CallCounter):
        async def get(self, *args, **kwargs):
            return UnauthorizedResponse()

    sess = UnauthorizingSession()
    gaggle_client = mock.Mock()
    s = Service(sess, FakeDiscoClient(), gaggle_client, retries=0)
    with pytest.raises(AccessDenied):
        await s.method()
    assert gaggle_client.refresh_token.called
    assert sess.calls['get'] == 2