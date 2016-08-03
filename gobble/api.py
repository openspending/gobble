"""This module handles all API calls"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
from requests import HTTPError
from requests import Session
from urllib.parse import (urlencode,
                          urljoin,
                          urlunsplit,
                          urlsplit)

from gobble.config import settings
from gobble.logger import log
from gobble.snapshot import SnapShot, to_json


# One session for all queries
_session = Session()


class EndPoint(object):
    """An API endpoint served by the os-conductor app"""

    def __init__(self, method, *path,
                 trailing_slash=False,
                 session=_session):

        self.has_slash = trailing_slash
        self.method = method
        self._path = path
        self._session = session
        self.snapshot = None

    @property
    def fire(self):
        return getattr(self._session, self.method.lower())

    @property
    def url(self):
        return urljoin(settings.OS_URL, '/'.join(self.path))

    @property
    def path(self):
        """Deal with trailing slashes
        """
        path = list(self._path)
        if self.has_slash:
            path[-1] += '/'
        return path

    def _append(self, params):
        """Encode the query string and append it to the endpoint
        """
        query = urlencode(tuple(params.items()))
        parts = urlsplit(self.url)._replace(query=query)
        return urlunsplit(parts)

    def __call__(self, params=None, **request):
        """Fire, take a snapshot and return the response
        """
        request_url = self._append(params) if params else self.url
        response = self.fire(request_url, **request)
        summary = request_url, response, params
        self.snapshot = SnapShot(self, *summary, **request)
        return response

    def __str__(self):
        return '%s: /%s' % (self.method, '/'.join(self.path))

    def __repr__(self):
        return '<EndPoint ' + str(self) + '>'

    @property
    def info(self):
        return {
            'method': self.method,
            'path': self.path,
            'endslash': self.has_slash,
            "url": self.url
        }


# Expose callable endpoint objects to other modules
# -----------------------------------------------------------------------------
authenticate_user = EndPoint('GET', 'user', 'check')
authorize_user = EndPoint('GET', 'user', 'authorize')
oauth_callback = EndPoint('GET', 'oauth', 'callback')
update_user = EndPoint('POST', 'user', 'update')
search_packages = EndPoint('GET', 'search', 'package')
upload_package = EndPoint('POST', 'package', 'upload')
upload_status = EndPoint('GET', 'package', 'status')
request_upload = EndPoint('POST', 'datastore', trailing_slash=True)
toggle_publish = EndPoint('POST', 'package', 'publish')
# -----------------------------------------------------------------------------


def handle(response):
    """Handle a response and return its payload

    If all is okay, return the json payload of the response
    as a dict. If the status code is in the range 400 to 599,
    raise an HTTPError.
    """
    try:
        response.raise_for_status()
    except HTTPError as error:
        log.error(error)
        raise error

    return to_json(response)
