"""Test the configuration module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from urllib.parse import urlparse

from future import standard_library
from os.path import isdir, dirname
from pytest import mark

standard_library.install_aliases()

from gobble.config import ROOT_DIR, HOME_DIR, GOBBLE_MODE
from tests.parameters import configurations


@mark.parametrize('settings', configurations)
def test_log_levels_are_set(settings):
    assert isinstance(settings.CONSOLE_LOG_LEVEL, (int, None))


def test_global_constants_are_correct():
    assert GOBBLE_MODE in ('Production', 'Development', 'Testing')
    assert isdir(HOME_DIR)
    assert isdir(ROOT_DIR)


@mark.parametrize('settings', configurations)
def test_user_and_log_folders_exist(settings):
    assert isdir(settings.USER_DIR)
    if settings.LOG_FILE:
        assert isdir(dirname(settings.LOG_FILE)) or None


@mark.parametrize('settings', configurations)
def test_os_url_is_parsable(settings):
    assert urlparse(settings.OS_URL).scheme
    assert urlparse(settings.OS_URL).netloc


@mark.parametrize('settings', configurations)
def test_log_formats_are_strings(settings):
    assert isinstance(settings.CONSOLE_LOG_FORMAT, str)
    assert isinstance(settings.FILE_LOG_FORMAT, str)


@mark.parametrize('settings', configurations)
def test_localhost_is_a_netloc_tuple(settings):
    assert isinstance(settings.LOCALHOST[0], str)
    assert isinstance(settings.LOCALHOST[1], int)


@mark.parametrize('settings', configurations)
def test_expanded_log_style_setting_is_set(settings):
    assert isinstance(settings.EXPANDED_LOG_STYLE, bool)

