from gaggle.client import Retries


def test_retries():
    r = Retries(0)
    assert r() is False

    r = Retries(1)
    assert r(), r() == (True, False)
