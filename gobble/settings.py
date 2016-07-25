"""User configurable settings"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library

standard_library.install_aliases()

from os import getenv
from logging import DEBUG, INFO
from os.path import expanduser, join, abspath


_home = abspath(join(expanduser('~')))


class Production(object):
    CONSOLE_LOG_LEVEL = INFO
    FILE_LOG_LEVEL = DEBUG
    FILE_LOG_FORMAT = '[%(asctime)s] [%(module)s] [%(levelname)s] %(message)s'
    CONSOLE_LOG_FORMAT = '[%(name)s] [%(module)s] [%(levelname)s] %(message)s'
    OS_URL = 'http://next.openspending.org'
    OAUTH_NEXT_SERVER = ('next.openspending.org', None)
    DATAPACKAGE_DETECTION_THRESHOLD = 1
    VALIDATION_FEEDBACK_OPTIONS = ['message']
    DATAFILE_HASHING_BLOCK_SIZE = 65536
    CONFIG_FILE = join(_home, '.gobble', 'settings.json')
    TOKEN_FILE = join(_home, 'token.json')
    LOG_FILE = join(_home, '.gobble', 'user.log')
    MOCK_REQUESTS = False


class Development(Production):
    CONSOLE_LOG_LEVEL = DEBUG
    FILE_LOG_LEVEL = None
    LOG_FILE = None
    OS_URL = 'http://dev.openspending.org'
    OAUTH_NEXT_SERVER = ('127.0.0.1', 8000)
    CONFIG_FILE = join(_home, '.gobble.dev', 'config.json')
    TOKEN_FILE = join(_home, '.gobble.dev', 'token.json')
    MOCK_REQUESTS = bool(getenv('GOBBLE_MOCK_REQUESTS', False))


class Testing(Production):
    MOCK_REQUESTS = True
