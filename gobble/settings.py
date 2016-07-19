"""User configurable settings"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library

standard_library.install_aliases()

from logging import DEBUG, INFO
from os.path import expanduser, join, abspath


_user_dir = abspath(join(expanduser('~')))


class Production(object):
    LOG_LEVEL_CONSOLE = INFO
    LOG_LEVEL_FILE = DEBUG
    LOG_FORMAT_FILE = '[%(asctime)s] [%(module)s] [%(levelname)s] %(message)s'
    LOG_FORMAT_CONSOLE = '[%(name)s] [%(module)s] [%(levelname)s] %(message)s'
    OS_URL = 'http://next.openspending.org'
    OAUTH_NEXT_SERVER = ('127.0.0.1', 8000)
    DATAPACKAGE_DETECTION_THRESHOLD = 1
    VALIDATION_FEEDBACK_OPTIONS = ['message']
    DATAFILE_HASHING_BLOCK_SIZE = 65536
    CONFIG_FILE = join(_user_dir, '.gobble', 'settings.json')
    LOG_FILE = join(_user_dir, '.gobble', 'user.log')


class Development(Production):
    LOG_LEVEL_STREAM = DEBUG
    LOG_LEVEL_FILE = None
    LOG_FILE = None
    OS_URL = 'http://dev.openspending.org'
    CONFIG_FILE = join(_user_dir, '.gobble.dev', 'config.json')
