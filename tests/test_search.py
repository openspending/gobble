"""Test the ElasticSearch module"""


import responses
from pytest import raises
from requests import Response

from gobble.search import _validate, _sanitize
from gobble.api import search_packages


def test_validate_bad_query_raises_exception():
    with raises(ValueError):
        bad_query = dict(foo='bar', name='mickey mouse')
        _validate(bad_query)


def test_validate_query_adds_double_quotesand_prefixes():
    original = {'author': 'mickey', 'title': 'fantasia'}
    validated = {'package.author': '"mickey"', 'package.title': '"fantasia"'}
    assert _sanitize(original) == validated


def test_numbers_get_quoted_too():
    original = {'int': 1, 'float': 99.99}
    validated = {'package.int': '"1"', 'package.float': '"99.99"'}
    assert _sanitize(original) == validated


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
