"""Test the conductor REST module."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

from responses import RequestsMock
from pytest import mark, raises

from gobble.configuration import config
from gobble.conductor import API, build_request_caller


GET = RequestsMock.GET
POST = RequestsMock.POST


api_endpoints = [
    ('authorize_user', '/user/authorize', GET),
    ('oauth_callback', '/oauth/callback', GET),
    ('update_user', '/user/update', POST),
    ('search_users', '/search/user', GET),
    ('search_packages', '/search/package', GET),
    ('prepare_upload', '/datastore/', POST)
]


@mark.parametrize('call, endpoint, verb', api_endpoints)
def test_api_calls_hit_correct_endpoints(call, endpoint, verb):
    with RequestsMock() as mock:
        mock.add(verb, config.OS_URL + endpoint, status=200)
        response = getattr(API, call)()
        assert response.status_code == 200


def test_passing_endpoint_item_not_string_raises_type_error():
    with raises(TypeError):
        build_request_caller('GET', 1000)()


def test_call_endpoint_with_query_parameters():
    with RequestsMock() as mock:
        url = config.OS_URL + '/baz?foo=bar&spam=eggs'
        mock.add(GET, url, status=200, match_querystring=True)
        response = build_request_caller(GET, 'baz')(foo='bar', spam='eggs')
        assert response.status_code == 200
