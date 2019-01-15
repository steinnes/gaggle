from unittest import mock

from gaggle import Client


def test_client_creates_credentials_if_none_are_passed_in():
    with mock.patch('gaggle.client.Client._make_credentials') as mock_maker:
        Client(mock.Mock())
        assert mock_maker.called


@mock.patch('gaggle.client.discovery')
def test_client_service_builder(mock_discovery):
    c = Client(mock.Mock(), token='')
    srv = c.some_fake_service()
    assert c._services['some_fake_service:None'] == srv
    assert mock_discovery.build.called

    srv2 = c.some_fake_service()
    assert srv2 == srv
    assert mock_discovery.build.call_count == 1

    srv3 = c.some_fake_service('v2')
    assert c._services['some_fake_service:v2'] == srv3
    assert srv3 != srv2
    assert mock_discovery.build.call_count == 2
