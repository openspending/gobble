"""Configuration parameters for the package."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
# noinspection PyCompatibility
from builtins import open

from json import loads
from os.path import join
from pprint import pprint


SECRETS_DIR = '/secrets'
GOOGLE_FILEPATH = join(SECRETS_DIR, 'google.json')
GOOGLE_OAUTH = loads(open(GOOGLE_FILEPATH).read())['installed']
GOOGLE_API_URL = 'https://accounts.google.com/o/oauth2/auth'
REDIRECT_URL = 'http://127.0.0.1:5000/oauth/check'
SCOPE = ['https://www.googleapis.com/auth/userinfo.email',
         'https://www.googleapis.com/auth/userinfo.profile']


HOST = '0.0.0.0'
PORT = '5000'


if __name__ == '__main__':
    pprint({k: v for k, v in locals().items() if k == k.upper()})
