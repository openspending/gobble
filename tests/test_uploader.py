"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
from pytest import fixture

standard_library.install_aliases()


from json import dumps
from datapackage import DataPackage
from pytest import mark

from gobble.user import User
from gobble.uploader import Uploader
from gobble.configuration import config
from gobble.logger import log
from tests.fixtures import get_mock_request, PACKAGE_FILE

log.debug('Mock tests requests: %s', config.MOCK_REQUESTS)


@fixture
def mock_endpoints(mock_requests):
    if mock_requests:
        endpoints = ('authenticate', 'get-permissions', 'request-upload')
        for endpoints in endpoints:
            method, url, status, json = get_mock_request(endpoints)
            getattr(mock_requests, method.lower())(url, text=dumps(json))


# noinspection PyUnusedLocal,PyShadowingNames
@mark.xfail(reason='not implemented yet')
def test_sending_datapackage_info_returns_json(mock_endpoints):
    user = User()
    package = DataPackage(PACKAGE_FILE)
    uploader = Uploader(user, package)
    json = uploader.request_upload()
    assert isinstance(json, dict)

# @responses.activate
# def test_sending_payload_info_returns_mock_upload_url():
#     for request_id in ('authenticate', 'get-permissions', 'request-upload'):
#         verb, url, status, json = get_mock_request(request_id)
#         responses.add(verb, url, status=status, json=json)
#
#     user = User()
#     package = DataPackage(PACKAGE_FILE)
#     uploader = Uploader(user, package)
#
#     assert uploader.request_upload().status_code == 200
