"""Test the validation module"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()

from os import walk
from os.path import join
from fnmatch import filter
from datapackage import DataPackage
from pytest import mark
from json import loads

from gobble.config import EXAMPLES_DIR
from gobble.validation import Validator


def collect_packages():
    for root, folders, files in walk(EXAMPLES_DIR):
        for filename in filter(files, '*.json'):
            filepath = join(root, filename)
            package = DataPackage(filepath, schema='fiscal')
            package.__setattr__('filepath', filepath)
            yield package

packages = list(collect_packages())


# noinspection PyShadowingNames
@mark.parametrize('package', packages)
def test_validation_result_is_correct(package):
    expected = 'invalid' not in package.filepath
    assert Validator(package).is_valid is expected


@mark.parametrize('package', packages)
def test_validation_report_has_timestamp(package):
    assert 'timestamp' in Validator(package).report.keys()
    assert 'is_valid' in Validator(package).report.keys()


@mark.parametrize('package', packages)
def test_validation_report_is_saved_as_json(package):
    Validator(package).save('/tmp/test.json')
    assert isinstance(loads(open('/tmp/test.json').read()), dict)


# def test_validate_no_title_no_model_reports_correct_errors():
#     bad = join(EXAMPLES_DIR, 'invalid-no-title-no-model', 'datapackage.json')
#     package = DataPackage(bad, schema='fiscal')
#     errors = Validator(package).report['errors']
#     assert errors == [r"'title' is a required property",
#                       r"'model' is a required property"]
