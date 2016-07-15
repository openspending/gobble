"""This module defines all os-conductor REST API endpoints"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

from requests import Session
from requests.compat import urljoin

from gobble.config import OS_URL

# Initialize one session for all API calls
session = Session()


def build_api_request(verb, *endpoint):
    """Return a request function pointing to an endpoint"""

    assert endpoint
    assert verb in ('GET', 'POST')

    def build_url(endpoint_=None):
        path = '/'.join(endpoint_)
        return urljoin(OS_URL, path)

    def request_endpoint(payload=None, headers=None, **query):

        assert not payload or isinstance(payload, dict)
        assert not headers or isinstance(headers, dict)

        request_method = getattr(session, verb.lower())
        endpoint_url = build_url(endpoint_=endpoint)
        return request_method(endpoint_url,
                              headers=headers,
                              params=query,
                              json=payload)

    return request_endpoint


class API(object):
    """All os-conductor REST API endpoints are defined here"""

    authenticate_user = build_api_request('GET', 'user', 'check')
    authorize_user = build_api_request('GET', 'user', 'authorize')
    oauth_callback = build_api_request('GET', 'oauth', 'callback')
    update_user = build_api_request('POST', 'user', 'update')
    search_users = build_api_request('GET', 'search', 'user')
    search_packages = build_api_request('GET', 'search', 'package')
    prepare_upload = build_api_request('POST', 'datastore/')
