"""This module exposes user configurable settings"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from logging import DEBUG, INFO
from os import getenv
from os.path import join, abspath, dirname, expanduser
from sys import modules
from future import standard_library

standard_library.install_aliases()

HOME = abspath(join(expanduser('~')))
ROOT_DIR = abspath(join(dirname(__file__), '..'))
GOBBLE_MODE = getenv('GOBBLE_MODE', 'Production')


class Production(object):
    OS_URL = 'http://next.openspending.org'
    S3_BUCKET_URL = 'https://s3.amazonaws.com:443/datastore.openspending.org'
    LOCALHOST = ('127.0.0.1', 8001)
    USER_DIR = join(HOME, '.gobble')
    LOG_FILE = join(HOME, '.gobble', 'gobble.log')
    EXPANDED_LOG_STYLE = False
    CONSOLE_LOG_LEVEL = INFO
    FILE_LOG_LEVEL = DEBUG
    CONSOLE_LOG_FORMAT = '[%(name)s] [%(levelname)s] %(message)s'
    FILE_LOG_FORMAT = ('[%(name)s] '
                       '[%(asctime)s] '
                       '[%(module)s] '
                       '[%(funcName)s] '
                       '[%(levelname)s] '
                       '%(message)s')


class Development(Production):
    S3_BUCKET_URL = 'http://fakes3/fake-bucket'
    OS_URL = 'http://dev.openspending.org'
    USER_DIR = join(HOME, '.gobble.dev')
    FILE_LOG_LEVEL = None
    LOG_FILE = None
    EXPANDED_LOG_STYLE = True
    CONSOLE_LOG_LEVEL = DEBUG
    CONSOLE_LOG_FORMAT = ('[%(name)s] '
                          '[%(module)s] '
                          '[%(funcName)s] '
                          '[%(levelname)s] '
                          '%(message)s')


settings = getattr(modules[__name__], GOBBLE_MODE)

