"""Tests for the uploader module"""
import datapackage
from os.path import join
from pytest import raises

# noinspection PyUnresolvedReferences
from tests.fixtures import fiscal_package, invalid_fiscal_package
from gobble.config import ROOT_DIR
from gobble.fiscal import compute_hash


DATA_FILE = join(ROOT_DIR, 'assets', 'datapackage', 'data', 'data.csv')


def test_compute_hash_returns_correct_hash():
    assert compute_hash(DATA_FILE) == '+uqBmwvQLi0M2W2enNxD/A=='


# noinspection PyShadowingNames
def test_validate_bad_package_with_raise_error_false():
    report = invalid_fiscal_package().validate(
        raise_on_error=False,
        schema_only=True
    )
    assert isinstance(report, list)
    assert len(report) > 0


# noinspection PyShadowingNames
def test_validate_bad_package_raises_error_by_default():
    with raises(datapackage.exceptions.ValidationError):
        invalid_fiscal_package().validate()


# noinspection PyShadowingNames
def test_validate_returns_true_for_valid_package():
    report = fiscal_package().validate(
        raise_on_error=False,
        schema_only=True
    )
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
