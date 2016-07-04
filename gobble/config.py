"""Configuration parameters for the package."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from os import getenv
from pprint import pprint

GOOGLE_OAUTH_CLIENT_ID = getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_API_URL = 'https://accounts.google.com/o/oauth2/auth'
REDIRECT_URL = 'http://127.0.0.1:5000/oauth/check'
SCOPE = ['https://www.googleapis.com/auth/userinfo.email',
         'https://www.googleapis.com/auth/userinfo.profile']


HOST = '0.0.0.0'
PORT = '5000'


if __name__ == '__main__':
    pprint({k: v for k, v in locals().items() if k == k.upper()})
