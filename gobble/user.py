"""Manage user authentication and authorization"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
from pip.utils import cached_property

standard_library.install_aliases()

from future.backports.http.server import HTTPServer, SimpleHTTPRequestHandler
from logging import getLogger, basicConfig, DEBUG
from collections import defaultdict
from os.path import isdir, isfile
from json import dumps
from os import mkdir


from gobble.session import APISession
from gobble.config import (USER_TOKEN_FILEPATH,
                           USER_CONFIG_DIR,
                           USER_PROFILE_FILEPATH,
                           OPENSPENDING_SERVICES, OAUTH_CALLBACK_URL)


basicConfig(format='[%(module)s] %(message)s', level=DEBUG)


class OpenSpendingException(Exception):
    pass


class _LocalServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        print(self.request)
        # TODO: grab the token, cache it and shutdown


def _listen_for_callback():
    httpd = HTTPServer(('127.0.0.1', 8000), _LocalServer)
    httpd.serve_forever()


class User(object):
    def __init__(self):
        self._conductor = APISession
        self._log = getLogger('Open-Spending')
        self.is_authenticated = False
        self.profile = defaultdict(lambda: None)
        self.permissions = {}

        if not self.token:
            self._get_new_token()
        else:
            self._authenticate()

        self._get_permissions()

    def update(self, **field):
        response = self._conductor.update_user(jwt=self.token, **field)
        confirmation = response.json()
        self._log.debug('Response: %s', confirmation)
        if not confirmation['success']:
            raise OpenSpendingException('%s' % confirmation['error'])

    def _install(self):
        if not isdir(USER_CONFIG_DIR):
            mkdir(USER_CONFIG_DIR)
            self._cache_profile()
            self._cache_token()

    @cached_property
    def token(self):
        if isfile(USER_TOKEN_FILEPATH):
            with open(USER_TOKEN_FILEPATH) as cache:
                return cache.read()

    def _get_permissions(self):
        for service in OPENSPENDING_SERVICES:
            self.permissions[service] = {}
            query = dict(jwt=self.token, service=service)
            response = self._conductor.authorize(**query)
            self._log.debug('Response: %s', response.json())
            self._register_permissions(response, service)

    def _authenticate(self):
        response = self._conductor.authenticate(jwt=self.token)
        self._log.debug('Response: %s', response.json())
        user = response.json()

        if user['authenticated']:
            self.profile = user['profile']
            self.is_authenticated = user['authenticated']
            self._cache_profile()
            self._log.info("Welcome to Open-Spending %s", self)
        else:
            self._log.warn('Token has expired: %s', self.token)
            self._get_new_token()

    def _get_new_token(self):
        query = dict(callback_url=OAUTH_CALLBACK_URL)
        response = self._conductor.authenticate(**query)
        self._log.debug('Response: %s', response.json())

        _listen_for_callback()

        self._log.debug('Response: %s', response.json())
        callback_url = response.json()['providers']['google']['url']
        print('Please click on this link: %s' % callback_url)

    def _register_permissions(self, response, service):
        permissions = response.json()['permissions']
        for role, has_permission in permissions.items():
            self.permissions[service][role] = has_permission

    def _cache_profile(self):
        with open(USER_PROFILE_FILEPATH, 'w+') as json:
            json.write(dumps(self.profile))

    def _cache_token(self):
        with open(USER_TOKEN_FILEPATH, 'w+') as text:
            text.write(self.token)

    def __str__(self):
        return self.profile.get('name', 'unauthenticated')

    def __repr__(self):
        status = 'is' if self.is_authenticated else 'is not'
        template = '<User: {name} is {status} authenticated>'
        return template.format(name=self, status=status)


if __name__ == '__main__':
    u = User()
