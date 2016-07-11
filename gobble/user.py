"""Manage user authentication and authorization on Open-Spending"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from collections import defaultdict
from json import dumps
from logging import getLogger, basicConfig, DEBUG
from os import mkdir
from os.path import isdir, isfile

from gobble.session import APISession
from gobble.config import (USER_TOKEN_FILEPATH,
                           USER_CONFIG_DIR,
                           USER_PROFILE_FILEPATH,
                           OPENSPENDING_SERVICES)


basicConfig(format='[%(module)s] %(message)s', level=DEBUG)


class TokenRequired(Exception):
    pass


class OpenSpendingException(Exception):
    pass


class User(object):
    def __init__(self):
        self._conductor = APISession
        self._log = getLogger('Open-Spending')

        self.token = None
        self.is_authenticated = False
        self.profile = defaultdict(lambda: None)
        self.permissions = {}

        self._uncache_user_token()
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
            self._save_profile()
            self._save_token()

    def _uncache_user_token(self):
        if isfile(USER_TOKEN_FILEPATH):
            with open(USER_TOKEN_FILEPATH) as cache:
                self.token = cache.read()

    def _authenticate(self):
        response = self._conductor.authenticate(jwt=self.token)
        user = response.json()

        if user['authenticated']:
            self.profile = user['profile']
            self.is_authenticated = user['authenticated']
            self._save_profile()
            self._log.debug("Authentication success: %s", self)
        else:
            message = 'Please save your token manually in %s'
            raise TokenRequired(message, USER_TOKEN_FILEPATH)

    def _get_permissions(self):
        for service in OPENSPENDING_SERVICES:
            self.permissions[service] = {}
            query = dict(jwt=self.token, service=service)
            response = self._conductor.authorize(**query)
            self._log.debug('Response: %s', response.json())
            self._register_permissions(response, service)

    def _register_permissions(self, response, service):
            permissions = response.json()['permissions']
            message = '%s permissions for %s are %s'
            self._log.debug(message, service, self, permissions)
            for role, has_permission in permissions.items():
                self.permissions[service][role] = has_permission

    def _save_profile(self):
        with open(USER_PROFILE_FILEPATH, 'w+') as json:
            json.write(dumps(self.profile))

    def _save_token(self):
        with open(USER_TOKEN_FILEPATH, 'w+') as cache:
            cache.write(self.token)

    def __str__(self):
        return self.profile['name']

    def __repr__(self):
        status = 'is' if self.is_authenticated else 'is not'
        template = '<User: {name} is {status} authenticated>'
        return template.format(name=self, status=status)


if __name__ == '__main__':
    user_ = User()
    new_name = str(user_)[::-1]
    user_.update(username=new_name)
    print(user_.profile)
