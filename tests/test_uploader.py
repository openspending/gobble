"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from pytest import fixture
from json import dumps
from datapackage import DataPackage

from gobble.user import User
from gobble.uploader import Uploader, Batch
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
def test_sending_datapackage_info_returns_dict(mock_endpoints):
    user_ = User()
    package_ = DataPackage(PACKAGE_FILE)
    batch_ = Batch(user_, package_).prepare()
    uploader = Uploader(batch_)
    uploader.push()
    uploader.pull()
    assert uploader.close()


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
