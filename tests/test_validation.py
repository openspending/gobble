"""Test the validation module"""

from pytest import mark
from json import loads

from gobble.collection import Collection
from gobble.config import EXAMPLES_DIR
from gobble.validation import Validator


collection = Collection(EXAMPLES_DIR, flavour='fiscal')
packages = collection.packages
is_valid = map(lambda path: 'invalid' not in path, collection.filepaths)


# noinspection PyShadowingNames
@mark.parametrize('package, is_valid', zip(packages, is_valid))
def test_assert_validation_correct(package, is_valid):
    assert Validator(package).is_valid is is_valid


# noinspection PyShadowingNames
@mark.parametrize('package', packages)
def test_assert_validation_report_has_timestamp(package):
    assert 'timestamp' in Validator(package).report.keys()
    assert 'is_valid' in Validator(package).report.keys()


# noinspection PyShadowingNames
@mark.parametrize('package', packages)
def test_assert_validation_report_is_saved_as_json(package):
    Validator(package).save('/tmp/test.json')
    assert isinstance(loads(open('/tmp/test.json').read()), dict)
