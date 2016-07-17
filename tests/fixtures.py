"""Fixtures for test modules"""

from os.path import abspath, join, dirname, splitext
from sys import modules
from os import listdir
from pytest import fixture
from shutil import rmtree
from responses import RequestsMock

from gobble.configuration import Config, config


ROOT_DIR = abspath(join(dirname(modules['gobble'].__file__), '..'))
PACKAGE_FILE = join(ROOT_DIR, 'assets', 'datapackage', 'datapackage.json')
CONFIG_FILE = '/tmp/gobble-dummy/dummy.json'
UPLOADER_PAYLOAD = join(ROOT_DIR, 'assets', 'datapackage', 'payload.json')


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


@fixture
def dummy_requests():
    """Return mock responses build from the specs folder"""

    mock = RequestsMock(assert_all_requests_are_fired=False)
    specs = join(ROOT_DIR, 'specs')

    def parse(filename_):
        base, _ = splitext(filename_)
        parts = base.split('.')
        verb_ = parts.pop()
        endpoint_ = '/' + '/'.join(parts)
        url_ = config.OS_URL + endpoint_
        return verb_, url_

    def read(filename_):
        filepath = join(specs, filename_)
        with open(filepath) as json_:
            return json_.read()

    for filename in listdir(specs):
        verb, url = parse(filename)
        json = read(filename)
        mock.add(verb, url, body=json)

    return mock
