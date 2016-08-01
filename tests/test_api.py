"""Test the API module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import responses
from future import standard_library
from pytest import mark, raises
from requests import HTTPError

from gobble.api import handle
from tests.parameters import api_calls

standard_library.install_aliases()


@responses.activate
@mark.parametrize('api_call', api_calls)
def test_api_calls_hit_correct_endpoints(api_call):
    responses.add(api_call.method, api_call.url)
    assert api_call().status_code == 200


@responses.activate
@mark.parametrize('api_call', api_calls)
def test_handle_returns_json_if_status_is_200(api_call):
    responses.add(api_call.method, api_call.url, body='{"foo": "bar"}')
    assert handle(api_call()) == {'foo': 'bar'}


@responses.activate
@mark.parametrize('api_call', api_calls)
def test_handle_raises_error_if_status_is_400(api_call):
    responses.add(api_call.method, api_call.url, body=HTTPError())
    with raises(HTTPError):
        handle(api_call())


# @responses.activate
# @mark.parametrize('api_call', api_calls)
# def test_call_endpoint_with_query_parameters(api_call):
#     responses.add(
#         api_call.method,
#         api_call.url + '?spam=eggs&foo=bar',
#         match_querystring=False
#     )
#     params = dict(foo='bar', spam='eggs')
#     assert api_call(params=params).status_code == 200
