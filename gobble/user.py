"""Authenticate the user in Open-Spending."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

from gobble.elasticsearch import ElasticSearch

standard_library.install_aliases()

from logging import getLogger, basicConfig, DEBUG
from os import mkdir
from os.path import isdir, isfile
from requests_oauthlib import OAuth2Session

from gobble.session import APISession
from gobble.config import (GOOGLE_OAUTH_CLIENT_ID,
                           SCOPE, GOOGLE_API_URL,
                           TOKEN_FILEPATH, USER_CONFIG_DIR, USER_EMAIL)

# TO DO: Find way to get and refresh the token
# TO DO: Write tests
# TO DO: Refactor

basicConfig(format='[%(module)s] %(message)s', level=DEBUG)


class TokenRequired(Exception):
    pass


class User(object):
    services = [
        'os-datastore'
    ]

    def __init__(self, email=USER_EMAIL):
        self.session = APISession
        self.token = self._get_user_token()
        self.profile = None
        self.log = getLogger('user')
        self.email = email

        self._soft_install()
        self._authenticate()

    @staticmethod
    def _soft_install():
        if not isdir(USER_CONFIG_DIR):
            mkdir(USER_CONFIG_DIR)

    @staticmethod
    def _get_user_token():
        if isfile(TOKEN_FILEPATH):
            with open(TOKEN_FILEPATH) as cache:
                return cache.read()

    def _authenticate(self):
        response = self.session.check_user(jwt=self.token)
        user = response.json()

        if user['authenticated']:
            self.profile = user['profile']
        else:
            oauth_url = user['providers']['google']['url']
            raise TokenRequired('Please go to %s' % oauth_url)

        self.log.debug(user)

    @property
    def permissions(self):
        for service in self.services:
            response = self.session.check_permission(
                jwt=self.token,
                service=service
            )
            yield response.json()

    def can_upload(self):
        response = self.session.check_permission(
            jwt=self.token,
            service='os.datastore'
        ).json()
        permissions = response['permissions']
        return permissions['datapackage-upload']

    def info(self):
        return {
            'token': self.token,
            'user': ElasticSearch().search('user', email=self.email),
            'permissions': list(self.permissions)
        }


def check_authentication():
    # This is for sandboxing purposes
    oauth = OAuth2Session(
        GOOGLE_OAUTH_CLIENT_ID,
        redirect_uri=APISession.oauth_callback().url,
        scope=SCOPE
    )
    authorization_url, state = oauth.authorization_url(
        GOOGLE_API_URL,
        access_type='offline',  # google specific
        approval_prompt='force',  # google specific
    )
    print('Please go to %s and authorize access' % authorization_url)


if __name__ == '__main__':
    u = User()
    u.has_permission('os.datastore')
    print(u.can_upload())
