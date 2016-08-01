"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
from pytest import mark

from gobble.settings import GOBBLE_MODE
# noinspection PyUnresolvedReferences
from tests.fixtures import mock_package, mock_user, permissions
from gobble.uploader import Batch
from tests.parameters import s3_bucket_test_cases
from gobble.api import request_upload_urls

standard_library.install_aliases()


# noinspection PyShadowingNames
@mark.skipif(GOBBLE_MODE == 'Testing', reason='Requires Docker container')
def test_request_upload_urls_returns_correct_json(mock_user,
                                                  mock_package,
                                                  permissions):

    # This is an example of how NOT to test.
    # I'm leaving it here as a reminder.
    mock_user.permissions = permissions
    batch = Batch(mock_user, mock_package)
    response = batch._request_upload_urls()
    assert response.json() == request_upload_urls.snapshot['response_json']


# noinspection PyShadowingNames
@mark.parametrize(['upload_url', 's3_bucket_url'], s3_bucket_test_cases)
def test_s3_bucket_urls_are_parsed_correctly(upload_url,
                                             s3_bucket_url,
                                             mock_user,
                                             mock_package):
    batch = Batch(mock_user, mock_package)
    batch.upload_urls = {'foo': upload_url}
    assert batch.s3_bucket == s3_bucket_url
