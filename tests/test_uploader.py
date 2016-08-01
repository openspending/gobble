"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from logging import INFO

from datapackage import DataPackage
from future import standard_library
from pytest import mark

from gobble.configuration import GOBBLE_MODE, settings
# noinspection PyUnresolvedReferences
from tests.fixtures import mock_package, mock_user, permissions
from gobble.upload import Batch, report_validation_errors
from tests.parameters import s3_bucket_test_cases
from gobble.api import request_upload

standard_library.install_aliases()


def test_report_validation_returns_list_of_messages_for_invalid_package():
    bad_package = DataPackage({'foo': 'bar'})
    report = report_validation_errors(bad_package)
    assert isinstance(report, list)
    assert report[0] == "'name' is a required property"


def test_report_validation_returns_none_for_valid_package():
    bad_package = DataPackage({'name': 'foo'})
    report = report_validation_errors(bad_package)
    assert not report


def test_report_validation_errors_logs_error_messages(capsys):
    bad_package = DataPackage({'foo': 'bar'})
    report_validation_errors(bad_package)
    stdout, stderr = capsys.readouterr()
    print('validating')
    print(settings.CONSOLE_LOG_LEVEL)
    print('yo', stdout)
    if settings.CONSOLE_LOG_LEVEL <= INFO:
        assert 'validating' in stdout
        assert 'required property' in stdout
