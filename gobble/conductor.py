"""This module defines all OS-Conductor API endpoints"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()

from collections import OrderedDict
from munch import Munch
from requests import HTTPError
from requests import Session
from urllib.parse import (urlencode,
                          urljoin,
                          urlunsplit,
                          parse_qs,
                          urlsplit,
                          urlparse)
try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from gobble.configuration import config
from gobble.logger import log, sdumps


# One session for all API calls
_session = Session()


def build_request(verb, *path):
    """Return a function that calls an API endpoint"""

    def send_request(headers=None,
                     json=None,
                     data=None,
                     params=None,
                     **query):
        """Send a request to an API endpoint"""

        if params:
            assert not query
        if query:
            assert not params

        method = verb.lower()
        caller = getattr(_session, method)
        endpoint = urljoin(config.OS_URL, '/'.join(path))
        parts = urlsplit(endpoint)

        parameters = tuple(query.items())
        safe_query = urlencode(parameters)
        updated_parts = parts._replace(query=safe_query)

        url = urlunsplit(updated_parts)

        request = {
            'endpoint': endpoint,
            'query': dict(parameters),
            'payload': json,
            'headers': headers,
        }
        log.debug('Sending request: %s', sdumps(request))

        return caller(url,
                      json=json,
                      headers=headers,
                      data=data,
                      params=params)

    return send_request


# I would like to expose the function with an ordinary class
# but it fails in python2. The Munch class is just a dirty hack.
API = Munch()

API.authenticate_user = build_request('GET', 'user', 'check')
API.authorize_user = build_request('GET', 'user', 'authorize')
API.oauth_callback = build_request('GET', 'oauth', 'callback')
API.update_user = build_request('POST', 'user', 'update')
API.search_users = build_request('GET', 'search', 'user')
API.search_packages = build_request('GET', 'search', 'package')
API.request_upload = build_request('POST', 'datastore/')
API.upload = build_request('POST', 'datastore', 'upload')


def handle(response):
    """Handle a response from the os-conductor API

    If all is okay, return the json payload of the response
    as a dictionary. If the status code is in the range 400 to 599,
    raise an HTTPError. Log the response, whatever happens.
    """
    try:
        response.raise_for_status()
    except HTTPError as error:
        log.error(error)
        log.error('Failed request: %s', to_json(response))
        raise error
    else:
        log.debug('Received response %s', to_json(response))
        try:
            return response.json()
        except JSONDecodeError:
            return {}


def to_json(response):
    """Return a JSON representation of a response object"""

    url_parts = urlparse(response.url)
    properties = OrderedDict()

    properties['ok'] = bool(response)
    properties['status_code'] = response.status_code
    properties['reason'] = response.reason
    properties['encoding'] = response.encoding
    properties['headers'] = {k: str(v) for k, v in response.headers.items()}
    properties['url'] = response.url
    properties['scheme'] = str(url_parts.scheme)
    properties['host'] = str(url_parts.netloc)
    properties['path'] = str(url_parts.path)
    properties['query'] = parse_qs(url_parts.query)
    properties['json'] = None

    try:
        properties['json'] = response.json()
    except JSONDecodeError:
        properties['json'] = None

    return sdumps(properties)
