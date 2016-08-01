"""This module handles all API calls"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
from requests import Session
from urllib.parse import (urlencode,
                          urljoin,
                          urlunsplit,
                          urlsplit)

from gobble.configuration import settings
from gobble.snapshot import SnapShot


class EndPoint(object):
    """This class represents an API endpoint"""

    _session = Session()

    def __init__(self, method, *path, trailing_slash=False):
        self.has_slash = trailing_slash
        self.method = method
        self._path = path

    @property
    def target(self):
        return urljoin(settings.OS_URL, '/'.join(self.path))

    @property
    def path(self):
        # Deal with trailing slashes
        path = list(self._path)
        if self.has_slash:
            path[-1] += '/'
        return path

    def _build_url(self, params):
        """Encode the query string"""
        query = urlencode(tuple(params.items()))
        parts = urlsplit(self.target)._replace(query=query)
        return urlunsplit(parts)

    def __call__(self, **kwargs):
        """Fire, take a snapshot and return the response"""
        fire = getattr(self._session, self.method.lower())

        params = kwargs.pop('params')
        request_url = self._build_url(params) if params else self.target
        response = fire(request_url, **kwargs)
        info = request_url, response, params

        SnapShot(self, *info, **kwargs)
        return response

    def __str__(self):
        return '%s: /%s' % (self.method, '/'.join(self.path))

    def __repr__(self):
        return '<EndPoint ' + str(self) + '>'

    def __dict__(self):
        return {
            'method': self.method,
            'path': self.path,
            'endslash': self.has_slash,
            "url": self.target
        }


# Expose callable endpoint objects to other modules
# -----------------------------------------------------------------------------
authenticate_user = EndPoint('GET', 'user', 'check')
authorize_user = EndPoint('GET', 'user', 'authorize')
oauth_callback = EndPoint('GET', 'oauth', 'callback')
update_user = EndPoint('POST', 'user', 'update')
search_users = EndPoint('GET', 'search', 'user')
search_packages = EndPoint('GET', 'search', 'package')
upload_package = EndPoint('POST', 'datastore', 'upload')
request_upload_urls = EndPoint('POST', 'datastore', trailing_slash=True)
# -----------------------------------------------------------------------------
