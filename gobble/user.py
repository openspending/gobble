"""Manage user authentication and authorization"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import io

from builtins import dict
from future import standard_library
from future.backports.http.server import HTTPServer, SimpleHTTPRequestHandler
from os.path import join
from json import loads
from os import mkdir
from threading import Thread
from json import dumps

from gobble.logger import log
from gobble.config import settings
from gobble.api import (handle,
                        authenticate_user,
                        authorize_user,
                        oauth_callback)

standard_library.install_aliases()


OS_SERVICES = ['os.datastore']
TOKEN_FILE = join(settings.USER_DIR, 'token.json')
PERMISSIONS_FILE = join(settings.USER_DIR, 'permission.json')
AUTHENTICATION_FILE = join(settings.USER_DIR, 'authentication.json')


class InvalidToken(Exception):
    pass


class User(object):
    """A contributor on Open-Spending.

    Note: you don't need to instantiate or even import this class yourself.
    The correlation is that Gobble only supports a single user for now.

    If you use Gobble for the first time, run the :method:`user.start` function
    first. It will help you obtain your authentication token. Open-Spending
    uses Google OAuth2, so you will need a valid Google email to make it work.

    Logs, tokens, permissions and snapshots of the latest API requests are
    saved in the user directory, which by default is :data:`~/.gobble`.
    """

    def __init__(self):
        self.folder = settings.USER_DIR
        self.token = self._uncache_token()
        self.authentication = self._request_authentication()
        self.permissions = self._request_permissions()
        self.token = self.permissions['os.datastore']['token']
        self.id = self.authentication['profile']['idhash']
        self.name = self.authentication['profile']['name']

    @classmethod
    def _uncache(cls, key):
        filepath = join(settings.USER_DIR, key + '.json')
        try:
            with io.open(filepath) as cache:
                json = loads(cache.read())
                log.debug('Your %s is %s', key, json)
                return json
        except FileNotFoundError:
            return

    @staticmethod
    def _uncache_token():
        """Read the token from the cache.
        """
        with io.open(TOKEN_FILE) as cache:
            json = loads(cache.read())
            log.debug('Your token is %s', json['token'])

            return json['token']

    def _request_authentication(self):
        """Ask Open-Spending if the token is valid.
        """
        query = dict(jwt=self.token)
        response = authenticate_user(params=query)
        authentication = handle(response)

        if not authentication['authenticated']:
            message = 'Token has expired: request a new one'
            log.error(message)
            raise InvalidToken(message)

        name = authentication['profile']['name']
        log.info('Hello %s! You are logged into Open-Spending', name)
        return authentication

    def _request_permissions(self):
        """Request permissions for Open-Spending services.
        """
        permissions = {}

        for service in OS_SERVICES:
            query = dict(jwt=self.token, service=service)
            response = authorize_user(params=query)
            permission = handle(response)
            permissions.update({service: permission})

            return permissions

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<User: ' + str(self) + '>'


class LocalHost(SimpleHTTPRequestHandler):
    """A local server to catch and save the token."""

    def do_GET(self):
        log.debug('Callback received: %s', self.path)
        token = self.path[6:]

        if token:
            with io.open(TOKEN_FILE, 'w+', encoding='utf-8') as file:
                file.write(dumps({'token': token}, ensure_ascii=False))
                log.info('Saved your token in %s', TOKEN_FILE)


def create_user():
    """Obtain the new user a token.

    Open-Spending uses Google OAuth2 for authentication, so you will need a
    valid Google email address to make this work. When you click on the link
    provided, you will be redirected to your browser to sign up. That's it.
    """

    def install_user_folder():
        try:
            mkdir(settings.USER_DIR)
        except FileExistsError:
            pass

    def request_new_token():
        localhost = 'http://%s:%s' % settings.LOCALHOST
        query = dict(next=localhost, callback_url=oauth_callback.url)
        response = authenticate_user(query)
        authorization = handle(response)
        new_thread = Thread(target=listen_for_token)
        prompt_user(authorization)
        local_server = new_thread.run()
        local_server.join()
        log.info('Well done, you have a now token!')

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
            json.write(dumps(info_, ensure_ascii=False, indent=4))

    install_user_folder()
    request_new_token()

    user_ = User()

    cached_info = (
        (user_.token, TOKEN_FILE),
        (user_.permissions, PERMISSIONS_FILE),
        (user_.authentication, AUTHENTICATION_FILE)
    )
    for info in cached_info:
        cache(*info)
        log.debug('Cached %s to %s', *info)

    return user_


# Expose a user object for use in other modules
# user = User()
