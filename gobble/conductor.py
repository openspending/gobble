"""This module defines all OS-Conductor API endpoints"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

from munch import Munch
from requests import Session
from urllib.parse import urlencode, urlunsplit, urlsplit, urljoin

from gobble.configuration import config
from gobble.logger import log


# One session for all API calls
session = Session()


def build_request_caller(verb, *path):
    """Return a function that calls an API endpoint"""

    def send_request(headers=None, json=None, **query):
        """Send a request to an API endpoint"""

        method = verb.lower()
        caller = getattr(session, method)
        endpoint = urljoin(config.OS_URL, '/'.join(path))
        parts = urlsplit(endpoint)

        parameters = tuple(query.items())
        safe_query = urlencode(parameters)
        updated_parts = parts._replace(query=safe_query)

        url = urlunsplit(updated_parts)

        log.debug('Request url: %s', url)
        log.debug('Request payload: %s', json)
        log.debug('Request headers: %s', headers)

        return caller(url, json=json, headers=headers)

    return send_request


API = Munch()

API.authenticate_user = build_request_caller('GET', 'user', 'check')
API.authorize_user = build_request_caller('GET', 'user', 'authorize')
API.oauth_callback = build_request_caller('GET', 'oauth', 'callback')
API.update_user = build_request_caller('POST', 'user', 'update')
API.search_users = build_request_caller('GET', 'search', 'user')
API.search_packages = build_request_caller('GET', 'search', 'package')
API.prepare_upload = build_request_caller('POST', 'datastore/')
