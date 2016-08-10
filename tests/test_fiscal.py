"""Tests for the uploader module"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from datapackage.exceptions import ValidationError
from future import standard_library
from os.path import join
from pytest import raises

# noinspection PyUnresolvedReferences
from tests.fixtures import fiscal_package, invalid_fiscal_package
from gobble.config import ROOT_DIR
from gobble.fiscal import compute_hash


standard_library.install_aliases()


DATA_FILE = join(ROOT_DIR, 'assets', 'datapackage', 'data', 'data.csv')


def test_compute_hash_returns_correct_hash():
    assert compute_hash(DATA_FILE) == '+uqBmwvQLi0M2W2enNxD/A=='


# noinspection PyShadowingNames
def test_validate_bad_package_with_raise_error_false(invalid_fiscal_package):
    report = invalid_fiscal_package.validate(raise_error=False)
    assert isinstance(report, list)
    assert report[0] == "'name' is a required property"


# noinspection PyShadowingNames
def test_validate_bad_package_raises_error_by_default(invalid_fiscal_package):
    with raises(ValidationError):
        invalid_fiscal_package.validate()


# noinspection PyShadowingNames
def test_validate_returns_true_for_valid_package(fiscal_package):
    report = fiscal_package.validate(raise_error=False)
    assert isinstance(report, list)


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
