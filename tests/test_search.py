"""Test the ElasticSearch module"""


import responses
from pytest import raises
from requests import Response

from gobble.search import _check_keys, _quote_values, _prefix_keys
from gobble.api import search_packages


def test_validate_bad_query_raises_exception():
    with raises(ValueError):
        bad_query = dict(foo='bar', name='mickey mouse')
        _check_keys(bad_query)


def test_quote_values_adds_double_quotes():
    original = {'author': 'mickey', 'title': 'fantasia'}
    validated = {'author': '"mickey"', 'title': '"fantasia"'}
    assert _quote_values(original) == validated


def test_prefix_keys_adds_prefixes():
    original = {'author': 'mickey', 'title': 'fantasia'}
    validated = {'package.author': 'mickey', 'package.title': 'fantasia'}
    assert _prefix_keys(original) == validated


def test_numbers_get_quoted_too():
    original = {'int': 1, 'float': 99.99}
    validated = {'int': '"1"', 'float': '"99.99"'}
    assert _quote_values(original) == validated


@responses.activate
def test_calling_search_function_hits_correct_api_endpoint():
    responses.add(
        search_packages.method,
        search_packages.url,
        body='{"it": "worked"}',
    )
    assert isinstance(search_packages(), Response)
    assert search_packages().status_code == 200
    assert search_packages().json() == {'it': 'worked'}
