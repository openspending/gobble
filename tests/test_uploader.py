"""Tests for the uploader module"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datapackage import DataPackage
from datapackage.exceptions import ValidationError
from future import standard_library
from pytest import raises

from gobble.upload import check_datapackage_schema

standard_library.install_aliases()


def test_validating_bad_package_returns_list_of_messages_if_flag_false():
    bad_package = {'foo': 'bar'}
    report = check_datapackage_schema(bad_package, raise_error=False)
    assert isinstance(report, list)
    assert report[0] == "'name' is a required property"


def test_validating_bad_package_raise_error_by_default():
    bad_package = {'foo': 'bar'}
    with raises(ValidationError):
        check_datapackage_schema(bad_package)


def test_report_validation_returns_true_for_valid_package():
    bad_package = {'name': 'foo'}
    report = check_datapackage_schema(bad_package)
    assert report


# def test_report_validation_errors_logs_error_messages(capsys):
#     bad_package = DataPackage({'foo': 'bar'})
#     report_validation_errors(bad_package)
#     stdout, stderr = capsys.readouterr()
#     print('validating')
#     print(settings.CONSOLE_LOG_LEVEL)
#     print('yo', stdout)
#     if settings.CONSOLE_LOG_LEVEL <= INFO:
#         assert 'validating' in stdout
#         assert 'required property' in stdout
