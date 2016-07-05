"""Test the ElasticSearch module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from pytest import raises
from gobble.search import Contributors, BadSearchKey, Packages


def test_validate_bad_query_raises_exception():
    with raises(BadSearchKey):
        Contributors().validate_query(foo='bar', name='mickey mouse')


def test_validate_good_query_adds_double_quotes():
    original = {'author': 'mickey mouse', 'title': 'fantasia'}
    validated = {'author': '"mickey mouse"', 'title': '"fantasia"'}
    assert Packages().validate_query(**original) == validated
