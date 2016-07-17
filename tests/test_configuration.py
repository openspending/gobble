"""Test the configuration module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

from json import loads
from os.path import isfile
from io import open

# noinspection PyUnresolvedReferences
from tests.fixtures import dummy_config, CONFIG_FILE


# noinspection PyShadowingNames
def test_config_object_is_not_empty(dummy_config):
        assert dummy_config


# noinspection PyShadowingNames
def test_config_object_is_correct_length(dummy_config):
        assert len(dummy_config) == 1


# noinspection PyShadowingNames
def test_config_object_is_instance_of_munch_class(dummy_config):
    assert isinstance(dummy_config, dict)


# noinspection PyShadowingNames
def test_config_object_is_accessible_by_keyword(dummy_config):
    assert 'CONFIG_FILE' in dummy_config


# noinspection PyShadowingNames
def test_setting_object_is_accessible_by_attribute(dummy_config):
    assert dummy_config.CONFIG_FILE


# noinspection PyShadowingNames
def test_config_file_has_been_created(dummy_config):
    assert isfile(dummy_config.CONFIG_FILE)


# noinspection PyShadowingNames
def test_loading_config_file_returns_original_data(dummy_config):
    with open(dummy_config.CONFIG_FILE) as file:
        config_dict = loads(file.read())
        assert config_dict == {'CONFIG_FILE': '/tmp/gobble-dummy/dummy.json'}
