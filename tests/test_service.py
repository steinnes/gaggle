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


class BadResponse:
    def __init__(self, status_code, error_message):
        self.status = status_code
        self.error_message = error_message

    async def text(self):
        return self.error_message


class FailingSession(CallCounter):
    def __init__(self, errors):
        self.errors = errors
        super().__init__()

    async def get(self, *args, **kwargs):
        if len(self.errors) > 1:
            print("popping!")
            return self.errors.pop()
        return self.errors[0]


@pytest.mark.asyncio
async def test_service_request_refreshes_token_on_unauthorized():
    sess = FailingSession(errors=[BadResponse(status_code=401, error_message="Invalid credentials")])
    gaggle_client = mock.Mock()
    s = Service(sess, FakeDiscoClient(), gaggle_client, retries=0)
    with pytest.raises(AccessDenied):
        await s.method()
    assert gaggle_client.refresh_token.called
    assert sess.calls['get'] == 2


@pytest.mark.asyncio
async def test_service_request_raises_access_denied_on_bad_request_after_refresh():
    sess = FailingSession(
        errors=[
            BadResponse(status_code=401, error_message="Invalid credentials"),
            BadResponse(status_code=400, error_message="invalid_grant: Token has been expired or revoked.")
        ]
    )
    gaggle_client = mock.Mock()
    s = Service(sess, FakeDiscoClient(), gaggle_client, retries=0)
    with pytest.raises(AccessDenied):
        await s.method()


@pytest.mark.asyncio
async def test_service_request_raises_access_denied_on_immediate_bad_request():
    sess = FailingSession(
        errors=[BadResponse(status_code=400, error_message="invalid_grant: Token has been expired or revoked.")]
    )
    gaggle_client = mock.Mock()
    s = Service(sess, FakeDiscoClient(), gaggle_client, retries=0)
    with pytest.raises(AccessDenied):
        await s.method()
