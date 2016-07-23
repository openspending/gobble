"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
from requests_mock import Adapter

standard_library.install_aliases()


from json import dumps
from requests_mock import Mocker
from datapackage import DataPackage
import responses

from gobble.user import User
from gobble.uploader import Uploader
from gobble.configuration import config
# noinspection PyUnresolvedReferences
from tests.fixtures import (get_mock_request,
                            ROOT_DIR,
                            PACKAGE_FILE,
                            UPLOADER_PAYLOAD)

REAL_HTTP = not config.MOCK_REQUESTS


def test_sending_payload_info_returns_mock_upload_url2():
    with Mocker(real_http=REAL_HTTP) as mock:
        endpoints = ('authenticate', 'get-permissions', 'request-upload')
        for endpoints in endpoints:
            method, url, status, json = get_mock_request(endpoints)
            getattr(mock, method.lower())(url, text=dumps(json))

        user = User()
        package = DataPackage(PACKAGE_FILE)
        uploader = Uploader(user, package)

        assert uploader.request_upload().status_code == 200


@responses.activate
def test_sending_payload_info_returns_mock_upload_url():
    for request_id in ('authenticate', 'get-permissions', 'request-upload'):
        verb, url, status, json = get_mock_request(request_id)
        responses.add(verb, url, status=status, json=json)

    user = User()
    package = DataPackage(PACKAGE_FILE)
    uploader = Uploader(user, package)

    assert uploader.request_upload().status_code == 200
