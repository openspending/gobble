"""Test the conductor REST module."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from _pytest.python import raises
from future import standard_library

standard_library.install_aliases()

from responses import activate, GET, POST, add
from pytest import mark

from gobble.config import OS_URL
from gobble.conductor import API, build_api_request


request_functions = [
    ('authorize_user', '/user/authorize', GET),
    ('oauth_callback', '/oauth/callback', GET),
    ('update_user', '/user/update', POST),
    ('search_users', '/search/user', GET),
    ('search_packages', '/search/package', GET),
    ('prepare_upload', '/datastore/', POST)
]


@activate
@mark.parametrize('function, endpoint, verb', request_functions)
def test_api_requests_hit_correct_endpoints(function, endpoint, verb):
    endpoint_url = OS_URL + endpoint
    add(verb, endpoint_url, status=200)  # Mock the request
    response = getattr(API, function)(endpoint_url)
    assert response.status_code == 200


def test_passing_endpoint_items_not_strings_raises_type_error():
    with raises(TypeError):
        build_api_request('string', 1000, True)(foo='bar')


def test_build_api_request_with_invalid_verb_raise_assertion_error():
    with raises(AssertionError):
        build_api_request('foo', verb='BAR')
