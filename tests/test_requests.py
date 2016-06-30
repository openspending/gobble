"""Test the api_requests module."""

from pytest import mark
from gobble.api_requests import APIRequest


SIMPLE = ('foo.bar', dict(), ['https://foo.bar'])
LOCAL = ('0.0.0.0', dict(port=5000, schema='http'), ['http://0.0.0.0:5000'])
LONG = (
    'foo.bar',
    dict(
        path=['spam', 'eggs'],
        query={'foo': 'bar', 'spam': 'eggs'}
    ),
    [
        'https://foo.bar/spam/eggs?spam=eggs&foo=bar',
        'https://foo.bar/spam/eggs?foo=bar&spam=eggs'
    ]
)

TEST_CASES = [SIMPLE, LONG, LOCAL]


# noinspection PyShadowingNames
@mark.parametrize('host, parameters, urls', TEST_CASES)
def test_url(host, parameters, urls):
    assert APIRequest(host, **parameters).url in urls
