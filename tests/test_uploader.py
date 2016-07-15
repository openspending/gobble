"""Tests for the uploader module"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open

from future import standard_library

standard_library.install_aliases()

from os.path import join
from datapackage import DataPackage
from pytest import fixture
from json import loads

from gobble.config import ASSETS_DIR
from gobble.uploader import Uploader
from gobble.user import User


@fixture
def user():
    return User()


@fixture
def package():
    filepath = join(ASSETS_DIR, 'mexican-budget-samples', 'datapackage.json')
    return DataPackage(filepath)


# noinspection PyShadowingNames
def test_build_payloads(user, package):
    uploader = Uploader(user, package)
    expected = join(ASSETS_DIR, 'mexican-budget-samples', 'payload.json')
    with open(expected) as json:
        assert uploader.payload == loads(json.read())
