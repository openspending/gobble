"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
`from future import standard_library

standard_library.install_aliases()

from datapackage import DataPackage
import responses

from gobble.user import User
from gobble.uploader import Uploader
# noinspection PyUnresolvedReferences
from tests.fixtures import (get_mock_request,
                            dummy_requests,
                            ROOT_DIR,
                            PACKAGE_FILE,
                            UPLOADER_PAYLOAD)


# # noinspection PyShadowingNames
# def test_build_payloads(dummy_requests):
#     with dummy_requests:
#         user = User()
#         package = DataPackage(PACKAGE_FILE)
#         uploader = Uploader(user, package)
#         with open(UPLOADER_PAYLOAD) as json:
#             assert uploader.payload == loads(json.read())


@responses.activate
def test_sending_payload_info_returns_mock_upload_url():
    for request_id in ('authenticate', 'get-permissions', 'request-upload'):
        verb, url, status, json = get_mock_request(request_id)
        responses.add(verb, url, status=status, json=json)

    user = User()
    package = DataPackage(PACKAGE_FILE)
    uploader = Uploader(user, package)

    assert uploader.request_upload().status_code == 200
