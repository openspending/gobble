"""Authenticate the user in Open-Spending."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from requests_oauthlib import OAuth2Session
from gobble.config import GOOGLE_OAUTH, REDIRECT_URL, SCOPE, GOOGLE_API_URL


if __name__ == '__main__':
    oauth = OAuth2Session(
        GOOGLE_OAUTH['client_id'],
        redirect_uri=REDIRECT_URL,
        scope=SCOPE
    )
    # access_type and approval_prompt are Google specific extra parameters.
    authorization_url, state = oauth.authorization_url(
        GOOGLE_API_URL,
        access_type='offline',
        approval_prompt='force',
    )

    print('Please go to %s and authorize access.' % authorization_url)
