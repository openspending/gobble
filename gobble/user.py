"""Manage user authentication and authorization"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import dict
from future import standard_library
standard_library.install_aliases()

from future.backports.http.server import HTTPServer, SimpleHTTPRequestHandler
from pip.utils import cached_property
from collections import defaultdict
from os.path import isdir, isfile, join
from json import dumps, loads
from os import mkdir
from threading import Thread
import io

from gobble.configuration import config
from gobble.logger import log
from gobble.conductor import API


OPENSPENDING_SERVICES = ['os.datastore']


class OpenSpendingException(Exception):
    pass


class _LocalServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        token = self.path[6:]
        with io.open(config.TOKEN_FILE) as text:
            text.write(token)
        raise SystemExit


def _listen_for_token():
    httpd = HTTPServer(config.LOCALHOST, _LocalServer)
    httpd.serve_forever()


class User(object):
    def __init__(self):
        self._conductor = API
        self.is_authenticated = False
        self.profile = defaultdict(lambda: None)
        self.permissions = {}

        if not self.token:
            self._request_new_token()
        else:
            self._authenticate()

        self._get_permissions()

    def update(self, **field):
        response = self._conductor.update_user(jwt=self.token, **field)
        confirmation = response.json()
        log.debug('Response: %s', confirmation)
        if not confirmation['success']:
            raise OpenSpendingException('%s' % confirmation['error'])

    def _install(self):
        if not isdir(config.CONFIG_DIR):
            mkdir(config.CONFIG_DIR)
            self._cache('profile')
            self._cache_token()

    @cached_property
    def token(self):
        if isfile(config.TOKEN_FILE):
            with io.open(config.TOKEN_FILE) as cache:
                token_ = loads(cache.read())['token']
                log.debug('Token: %s', token_)
                return token_

    def _get_permissions(self):
        for service in OPENSPENDING_SERVICES:
            self.permissions[service] = {}
            query = dict(jwt=self.token, service=service)
            response = self._conductor.authorize_user(**query)
            log.debug('Response: %s', response.json())
            self.permissions.update({service: response.json()})
        self._cache('permissions')

    def _authenticate(self):
        response = self._conductor.authenticate_user(jwt=self.token)

        if response.status_code != 200:
            log.debug('Response %s: %s', response.status_code, response.reason)
            raise OpenSpendingException

        user = response.json()

        if user['authenticated']:
            self.profile = user['profile']
            self.is_authenticated = user['authenticated']
            self._cache('profile')
            log.info('%s is authenticated', self)
        else:
            log.warn('Token has expired: %s', self.token)
            self._request_new_token()

        log.debug('Response: %s', response.json())
        return user

    def _request_new_token(self):
        query = {'next': config.OS_URL}
        response = self._conductor.authenticate_user(**query)
        log.debug('Response: %s', response.json())
        sign_in_url = response.json()['providers']['google']['url']
        log.info('Please click on %s' % sign_in_url)
        local_server = Thread(target=_listen_for_token).run()
        local_server.join()
        self._authenticate()

    def _cache(self, attribute):
        filepath = join(config.CONFIG_DIR, attribute + '.json')
        with io.open(filepath, 'w+', encoding='utf-8') as cache:
            cache.write(dumps(getattr(self, attribute),
                              ensure_ascii=False,
                              indent=2))

    def _cache_token(self):
        with io.open(config.TOKEN_FILE, 'w+') as text:
            text.write(self.token)

    def __str__(self):
        return self.profile.get('name', 'unauthenticated')

    def __repr__(self):
        status = 'is' if self.is_authenticated else 'is not'
        template = '<User: {name} {status} authenticated>'
        return template.format(name=self, status=status)


if __name__ == '__main__':
    u = User()
