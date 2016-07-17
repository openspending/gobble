"""Tests for the uploader module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from datapackage import DataPackage
from future import standard_library

from gobble.user import User

standard_library.install_aliases()

from json import loads
from io import open

from gobble.uploader import Uploader
# noinspection PyUnresolvedReferences
from tests.fixtures import (dummy_requests,
                            ROOT_DIR,
                            PACKAGE_FILE,
                            UPLOADER_PAYLOAD)


# noinspection PyShadowingNames
def test_build_payloads(dummy_requests):
    with dummy_requests:
        user = User()
        package = DataPackage(PACKAGE_FILE)
        uploader = Uploader(user, package)
        with open(UPLOADER_PAYLOAD) as json:
            assert uploader.payload == loads(json.read())
