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
    EXPANDED_LOG_STYLE = False
    CONSOLE_LOG_LEVEL = INFO
    FILE_LOG_LEVEL = DEBUG
    CONSOLE_LOG_FORMAT = '[%(name)s] [%(levelname)s] %(message)s'
    OS_URL = 'http://next.openspending.org'
    USER_DIR = join(HOME, '.gobble')
    LOG_FILE = join(HOME, '.gobble', 'gobble.log')
    LOCALHOST = ('127.0.0.1', 8001)
    FILE_LOG_FORMAT = ('[%(name)s] '
                       '[%(asctime)s] '
                       '[%(module)s] '
                       '[%(funcName)s] '
                       '[%(levelname)s] '
                       '%(message)s')


class Development(Production):
    EXPANDED_LOG_STYLE = True
    CONSOLE_LOG_LEVEL = DEBUG
    FILE_LOG_LEVEL = None
    LOG_FILE = None
    OS_URL = 'http://dev.openspending.org'
    USER_DIR = join(HOME, '.gobble.dev')
    CONSOLE_LOG_FORMAT = ('[%(name)s] '
                          '[%(module)s] '
                          '[%(funcName)s] '
                          '[%(levelname)s] '
                          '%(message)s')


class Testing(Production):
    USER_DIR = join(HOME, '.gobble.test')
    LOG_FILE = None
    CONSOLE_LOG_LEVEL = DEBUG
    FILE_LOG_LEVEL = DEBUG


settings = getattr(modules[__name__], GOBBLE_MODE)

