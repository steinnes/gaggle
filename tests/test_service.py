from unittest import mock

from gaggle.client import Retries, Service


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
