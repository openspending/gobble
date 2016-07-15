"""Configuration parameters for Gobble"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library

standard_library.install_aliases()

from logging import basicConfig, getLogger, DEBUG
from os.path import expanduser, join, abspath, dirname
from os import getenv
from pprint import pprint


basicConfig(format='[%(name)s] [%(module)s] %(message)s', level=DEBUG)
log = getLogger('Gobble')


# Assign "dev.openspending.org" for development mode
OS_URL = getenv('GOBBLE_OPENSPENDING_URL', 'http://next.openspending.org')

# The URL where the token lands
OAUTH_NEXT_SERVER = ('127.0.0.1', 8000)
OAUTH_NEXT_URL = 'http://%s:%s' % OAUTH_NEXT_SERVER

# User information
USER_CONFIG_DIR = join(expanduser('~'), '.gobble')
USER_TOKEN_FILEPATH = join(USER_CONFIG_DIR, 'token.txt')
USER_PROFILE_FILEPATH = join(USER_CONFIG_DIR, 'profile.json')

# Test assets
ASSETS_DIR = abspath(join(dirname(__file__), '..', 'assets'))
EXAMPLES_DIR = abspath(join(ASSETS_DIR, 'fiscal-packages'))

# User unable parameters
DATAPACKAGE_DETECTION_THRESHOLD = 1
VALIDATION_FEEDBACK_OPTIONS = {'message'}
OPENSPENDING_SERVICES = ['os.datastore']
DATAFILE_HASHING_BLOCK_SIZE = 65536


if __name__ == '__main__':
    pprint({k: v for k, v in locals().items() if k == k.upper()})
