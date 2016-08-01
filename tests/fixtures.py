"""Fixtures for test modules"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from json import loads
from os import makedirs
from os.path import join, expanduser
from shutil import rmtree
from unittest.mock import patch
from future import standard_library
from pytest import fixture
from pytest import yield_fixture
from requests_mock import Mocker
import io

from gobble.configuration import settings, GOBBLE_MODE, DUMMY_DIR, \
    SNAPSHOTS_DIR
from gobble.logger import log

standard_library.install_aliases()


# Sanity check
# -----------------------------------------------------------------------------
class BadTestingConfiguration(Exception):
    pass


if GOBBLE_MODE not in ('Testing', 'Development'):
    sanity = (
        'Please run the tests in Testing or Development mode '
        'or bad things will happen and you will hate yourself'
    )
    raise BadTestingConfiguration(sanity)

if settings.FREEZE_MODE:
    sanity = (
        "You can't run tests with FREEZE_MODE = True"
    )
    raise BadTestingConfiguration(sanity)


# Mock API responses
# -----------------------------------------------------------------------------
@yield_fixture(scope='session')
def mock_requests():
    """Toggle mock requests ON/OFF."""

    request_type = 'mock' if settings.MOCK_MODE else 'real'
    log.debug('Sending %s requests', request_type)

    if settings.MOCK_MODE:
        with Mocker() as mock:
            yield mock
    else:
        yield None


# Fake the user's local set-up
# -----------------------------------------------------------------------------
@fixture
def tmp_user_dir(request):
    original = settings.USER_DIR
    settings.USER_DIR = join(expanduser('~'), '.gobble.tmp')
    try:
        makedirs(settings.USER_DIR)
    except IOError:
        pass

    def switch_back():
        settings.USER_DIR = original
        try:
            rmtree(settings.USER_DIR)
        except IOError:
            pass

    request.addfinalizer(switch_back)


# User authentication and permission
# -----------------------------------------------------------------------------
@fixture
def token():
    filepath = join(DUMMY_DIR, 'token.json')
    with io.open(filepath) as file:
        return loads(file.read())


@fixture
def permissions():
    filepath = join(DUMMY_DIR, 'permissions.json')
    with io.open(filepath) as file:
        return loads(file.read())


# Mock Gobble and site-package classes
# -----------------------------------------------------------------------------
@fixture
def mock_package():
    package = patch('datapackage.DataPackage', autospec=True)
    package.descriptor = {'name': 'mexican-budget-samples'}
    snapshot_file = join(SNAPSHOTS_DIR, 'POST.datastore.json')
    with io.open(snapshot_file) as file:
        package.payload = loads(file.read())['request_json']
    return package


# noinspection PyShadowingNames
@fixture
def mock_user():
    return patch('gobble.user.User', autospec=True)


@fixture
def mock_batch():
    return patch('gobble.uploader.Batch', autospec=True)


@fixture
def mock_uploader():
    return patch('gobble.uploader.Uploder', autospec=True)
