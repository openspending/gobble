"""Configuration module for pytests"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from pytest import yield_fixture
from requests_mock import Mocker

from gobble.configuration import config


@yield_fixture(scope='session')
def mock_requests():
    if config.MOCK_REQUESTS:
        with Mocker() as mock:
            yield mock
    else:
        yield None
