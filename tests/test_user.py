"""Tests for the user maodule"""

import responses
from requests import Response

from gobble.api import authenticate_user


@responses.activate
def test_create_user_hits_correct_api_endpoint():
    responses.add(
        authenticate_user.method,
        authenticate_user.url,
    )
    assert isinstance(authenticate_user(), Response)
    assert authenticate_user().status_code == 200
