"""Test the snapshot module."""

from pytest import mark


# noinspection PyShadowingNames
from gobble.snapshot import freeze
from tests.parameters import json_objects


@mark.parametrize('unsecure_json, secure_json', json_objects)
def test_remove_secrets_does_its_job(unsecure_json, secure_json):
    freeze(unsecure_json)
    assert unsecure_json == secure_json


# @responses.activate
# @mark.parametrize('function', api_functions)
# def test_endpoint_saves_request_snapshot_to_file(function):
#     function()
#     assert isfile(function.snapshot._filepath)
#     assert function.snapshot._filepath.endswith('json')
# # noinspection PyShadowingNames,PyUnusedLocal
