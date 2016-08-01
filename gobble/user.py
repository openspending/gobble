"""Manage user authentication and authorization"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import io

from builtins import dict
from future import standard_library
from future.backports.http.server import HTTPServer, SimpleHTTPRequestHandler
from pip.utils import cached_property
from os.path import join
from json import loads
from os import mkdir
from threading import Thread

from gobble.logger import log
from gobble.configuration import settings, OPENSPENDING_SERVICES, local
from gobble.api import authenticate_user, authorize_user, update_user
from gobble.utilities import (dumps23,
                              handle,
                              wopen23,
                              TokenExpired,
                              UserUpdateError)

standard_library.install_aliases()


class User(object):
    """A contributor on the Open-Spending platform."""

    def __init__(self):
        self._authentication = {}
        self._permissions = []

    @cached_property
    def token(self):
        filepath = join(settings.USER_DIR, local.TOKEN_FILE)
        with io.open(filepath) as cache:
            json = loads(cache.read())
            log.debug('Your token is %s', json['token'])
            return json['token']

    def authenticate(self):
        query = dict(jwt=self.token)
        response = authenticate_user(params=query)
        self._authentication = handle(response)

        if not self._authentication['authenticated']:
            message = 'Token has expired: request a new one'
            log.error(message)
            raise TokenExpired(message)

        log.info('Hello %s! You are logged in Open-Spending', self)
        return self._authentication

    def request_permissions(self):
        for service in OPENSPENDING_SERVICES:
            query = dict(jwt=self.token, service=service)
            response = authorize_user(params=query)
            json = handle(response)
            self._permissions.append(json)
            return self._permissions

    @property
    def permissions(self):
        return {p.get('service'): p for p in self._permissions}

    def update(self, **field):
        response = update_user(jwt=self.token, **field)
        confirmation = handle(response)
        if not confirmation['success']:
            raise UserUpdateError(confirmation['error'])

    def __str__(self):
        return self._authentication['profile']['name']

    def __repr__(self):
        return '<User: ' + str(self) + '>'

    def info(self):
        user = self._authentication
        user.update(self._permissions)
        user.update(self.token)
        return user


class LocalHost(SimpleHTTPRequestHandler):
    """A local server to catch and save the token"""

    def do_GET(self):
        log.debug('Callback received: %s', self.path)
        token = self.path[6:]

        filepath = join(settings.USER_DIR, local.TOKEN_FILE)
        with wopen23(filepath) as file:
            file.write(dumps23({'token': token}))

        log.info('Saved your token in %s', filepath)


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

    def cache(info, file):
        filepath = join(settings.USER_DIR, file)
        with wopen23(filepath) as json:
            json.write(dumps23(info))

    install_user_folder()
    request_new_token()

    user = User()
    user.authenticate()
    user.request_permissions()

    cache(user.token, local.TOKEN_FILE)
    cache(user._permissions, local.PERMISSIONS_FILE)
    cache(user._authentication, local.AUTHENTICATION_FILE)

    return user
