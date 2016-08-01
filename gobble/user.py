"""Manage user authentication and authorization"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import io

from builtins import dict

from click import command
from future import standard_library
from future.backports.http.server import HTTPServer, SimpleHTTPRequestHandler
from pip.utils import cached_property
from os.path import join
from json import loads
from os import mkdir
from threading import Thread
from json import dumps

from gobble.logger import log
from gobble.configuration import settings
from gobble.api import authenticate_user, authorize_user, update_user, handle

standard_library.install_aliases()


OS_SERVICES = ['os.datastore']
TOKEN_FILE = join(settings.USER_DIR, 'token.json')
PERMISSIONS_FILE = 'permission.json'
AUTHENTICATION_FILE = 'authentication.json'


class TokenExpired(Exception):
    pass


class User(object):
    """A contributor on the Open-Spending platform."""

    def __init__(self):
        self.authentication = self._get_authentication()
        self._permissions = list(self._get_permissions())
        self.name = None

    @property
    def permissions(self):
        return {p.get('service'): p for p in self._permissions}

    @cached_property
    def token(self):
        with io.open(TOKEN_FILE) as cache:
            json = loads(cache.read())
            log.debug('Your token is %s', json['token'])
            return json['token']

    def _get_authentication(self):
        query = dict(jwt=self.token)
        response = authenticate_user(params=query)
        authentication = handle(response)
        self.name = authentication['profile']['name']

        if not authentication['authenticated']:
            message = 'Token has expired: request a new one'
            log.error(message)
            raise TokenExpired(message)

        log.info('Hello %s! You are logged in Open-Spending', self)

        return authentication

    def _get_permissions(self):
        for service in OS_SERVICES:
            query = dict(jwt=self.token, service=service)
            response = authorize_user(params=query)
            permission = handle(response)
            yield permission

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<User: ' + str(self) + '>'


class LocalHost(SimpleHTTPRequestHandler):
    """A local server to catch and save the token"""

    def do_GET(self):
        log.debug('Callback received: %s', self.path)
        token = self.path[6:]

        with io.open(TOKEN_FILE, 'w+', encoding='utf-8') as file:
            file.write(dumps({'token': token}, ensure_ascii=False))

        log.info('Saved your token in %s', TOKEN_FILE)


# @command(name='start')
def create_user():
    """Get the new user a token and cache """

    def install_user_folder():
        try:
            mkdir(settings.USER_DIR)
        except FileExistsError:
            pass

    def request_new_token():
        localhost = 'http://%s:%s' % settings.LOCALHOST
        next_url = dict(next=localhost)

        response = authenticate_user(params=next_url)
        authorization = handle(response)
        prompt_user(authorization)

        new_thread = Thread(target=listen_for_token)
        local_server = new_thread.run()
        local_server.join()

    def prompt_user(authorization):
        sign_up_url = authorization['providers']['google']['url']
        message = ('Please open a new private browsing window '
                   'and paste this link to get a token: %s')
        log.critical(message, sign_up_url)

    def listen_for_token():
        server = HTTPServer(settings.LOCALHOST, LocalHost)
        server.serve_forever()

    def cache(info_, file):
        with io.open(file, 'w+', encoding='utf-8') as json:
            json.write(dumps(info_, ensure_ascii=False))

    install_user_folder()
    request_new_token()

    user = User()

    cached_info = (
        (user.token, TOKEN_FILE),
        (user._permissions, PERMISSIONS_FILE),
        (user.authentication, AUTHENTICATION_FILE)
    )
    for info in cached_info:
        cache(*info)

    return user


if __name__ == '__main__':
    u = User()
