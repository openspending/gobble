"""Tests for the user maodule"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import responses
from future import standard_library
from requests import Response

from gobble.user import
from gobble.api import authenticate_user

standard_library.install_aliases()


@responses.activate
def test_create_user_hits_correct_api_endpoint():
    responses.add(
        authenticate_user.method,
        authenticate_user.url,
    )
    assert isinstance(authenticate_user(), Response)
    assert authenticate_user().status_code == 200
