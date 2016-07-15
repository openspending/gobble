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


def build_api_request(*endpoint, verb='GET'):
    """Return a request function pointing to an endpoint"""

    assert endpoint, 'API request must have an endpoint path'
    assert verb in ('GET', 'POST'), 'verb must be GET or POST'

    def build_url(endpoint_=None):
        path = '/'.join(endpoint_)
        return urljoin(OS_URL, path)

    def request_endpoint(payload=None, headers=None, **query):
        request_method = getattr(session, verb.lower())
        endpoint_url = build_url(endpoint_=endpoint)
        return request_method(endpoint_url,
                              headers=headers,
                              params=query,
                              json=payload)

    return request_endpoint


class API(object):
    """All os-conductor REST API endpoints are defined here"""

    # FIXME: the "datastore/" endpoint is not consistent with others

    authenticate_user = build_api_request('user', 'check')
    authorize_user = build_api_request('user', 'authorize')
    oauth_callback = build_api_request('oauth', 'callback')
    update_user = build_api_request('user', 'update', verb='POST')
    search_users = build_api_request('search', 'user')
    search_packages = build_api_request('search', 'package')
    prepare_upload = build_api_request('datastore/', verb='POST')
