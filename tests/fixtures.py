"""Fixtures for test modules"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from json import loads, dumps
from os.path import abspath, join, dirname
from sys import modules
from future.backports.urllib.parse import urljoin
from pytest import fixture
from shutil import rmtree
import io

from gobble.configuration import Config, config
from gobble.logger import log


ROOT_DIR = abspath(join(dirname(modules['gobble'].__file__), '..'))
PACKAGE_FILE = join(ROOT_DIR, 'assets', 'datapackage', 'datapackage.json')
CONFIG_FILE = '/tmp/gobble-dummy/dummy.json'
UPLOADER_PAYLOAD = join(ROOT_DIR, 'assets', 'datapackage', 'payload.json')
RESPONSES_FILE = join(ROOT_DIR, 'assets', 'responses.json')


@fixture
def dummy_config(request):
    """Return a dummy configuration object pointing to a dummy file"""
    dummy_defaults = {'CONFIG_FILE': CONFIG_FILE}

    def delete():
        try:
            rmtree('/tmp/gobble-dummy')
        except OSError:
            pass

    request.addfinalizer(delete)
    return Config(dummy_defaults).save()


def get_mock_request(slug):
    """Return """
    with io.open(RESPONSES_FILE) as json:
        specs = loads(json.read())

    verb = specs[slug]['method']
    url = urljoin(config.OS_URL, specs[slug]['endpoint'])
    status = specs[slug]['response']['status']
    json = specs[slug]['response']['json']

    log.debug('Mocking %s %s', verb, url)
    log.debug('Expecting back [%s] %s', status, dumps(json))

    return verb, url, status, json
