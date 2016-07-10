""" A utility class to help make API calls. """

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
# noinspection PyCompatibility
from builtins import str

from requests import Session
from gobble.config import OS_HOST

# TO DO: Simplify the request module


def optional(method):
    def new_method(self):
        private_method = '_' + method.__name__
        if getattr(self, private_method):
            return method(self)
        else:
            return ''
    return new_method


class APIRequest(object):
    def __init__(self,
                 host,
                 session=Session(),
                 verb='get',
                 schema='https',
                 path=None,
                 query=None,
                 port=None):

        self.host = host
        self.session = session
        self.verb = verb

        self._schema = schema
        self._port = port
        self._path = path
        self._query = query or {}

    @property
    def schema(self):
        return self._schema + '://'

    @property
    def url(self):
        return self.schema + self.host + self.port + self.path + self.query

    @property
    @optional
    def port(self):
        return ':' + str(self._port)

    @property
    @optional
    def query(self):
        parameters = ['%s=%s' % (k, v) for k, v in self._query.items()]
        return '?' + '&'.join(parameters)

    @property
    @optional
    def path(self):
        if self._path:
            return '/' + '/'.join(self._path)

    def __call__(self, **parameters):
        if parameters:
            self._query.update(parameters)
        return getattr(self.session, self.verb)(self.url)


class APISession(object):
    session = Session()

    check_user = APIRequest(
        OS_HOST,
        session=session,
        path=['oauth', 'check'],
        schema='http'
    )
    check_permission = APIRequest(
        OS_HOST,
        session=session,
        path=['permit', 'check'],
        schema='http'
    )
    oauth_callback = APIRequest(
        OS_HOST,
        session=session,
        path=['oauth', 'callback'],
        schema='http'
    )
    search_users = APIRequest(
        OS_HOST,
        session=session,
        path=['search', 'user'],
        schema='http'
    )

    search_packages = APIRequest(
        OS_HOST,
        session=session,
        path=['search', 'package'],
        schema='http'
    )
