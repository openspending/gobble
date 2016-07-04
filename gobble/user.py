"""Authenticate the user in Open-Spending."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

from gobble.api_requests import APIRequest

standard_library.install_aliases()

from requests_oauthlib import OAuth2Session
from gobble.config import (GOOGLE_OAUTH_CLIENT_ID,
                           SCOPE, GOOGLE_API_URL, HOST)


if __name__ == '__main__':
    request_check_oauth = APIRequest(HOST, port=5000, path=['oauth', 'check'])

    oauth = OAuth2Session(
        GOOGLE_OAUTH_CLIENT_ID,
        redirect_uri=request_check_oauth,
        scope=SCOPE
    )
    # access_type and approval_prompt are Google specific extra parameters.
    authorization_url, state = oauth.authorization_url(
        GOOGLE_API_URL,
        access_type='offline',
        approval_prompt='force',
    )

    print('Please go to %s and authorize access.' % authorization_url)
