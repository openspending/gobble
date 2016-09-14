"""This module exposes user configurable settings"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from logging import DEBUG
from os import getenv
from os import mkdir
from os.path import isdir
from os.path import join, abspath, dirname, expanduser
from sys import modules

from future import standard_library

standard_library.install_aliases()

HOME_DIR = abspath(join(expanduser('~')))
ROOT_DIR = abspath(join(dirname(__file__), '..'))
GOBBLE_MODE = getenv('GOBBLE_MODE', 'Production')


class Production(object):
    OS_URL = 'http://next.openspending.org'
    S3_BUCKET_URL = 'https://s3.amazonaws.com/datastore.openspending.org'
    LOCALHOST = ('127.0.0.1', 8001)
    USER_DIR = join(HOME_DIR, '.gobble')
    LOG_FILE = join(HOME_DIR, '.gobble', 'gobble.log')
    EXPANDED_LOG_STYLE = True
    CONSOLE_LOG_LEVEL = None
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
    USER_DIR = join(HOME_DIR, '.gobble.dev')
    FILE_LOG_LEVEL = DEBUG
    EXPANDED_LOG_STYLE = True
    CONSOLE_LOG_LEVEL = None
    CONSOLE_LOG_FORMAT = ('[%(name)s] '
                          '[%(module)s] '
                          '[%(funcName)s] '
                          '[%(levelname)s] '
                          '%(message)s')


settings = getattr(modules[__name__], GOBBLE_MODE)

if not isdir(settings.USER_DIR):
    mkdir(settings.USER_DIR)
