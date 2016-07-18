""" Upload to Open-Spending"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

from builtins import str
from base64 import b64encode
from hashlib import md5
from os.path import join
from io import open

from gobble.config import DATAFILE_HASHING_BLOCK_SIZE
from gobble.conductor import API


def _get_datafile_stats(filepath, block_size=DATAFILE_HASHING_BLOCK_SIZE):
    """Get stats on a file via iteration over its contents"""

    hasher = md5()
    length = 0

    with open(filepath, mode='rb') as stream:
        chunk = stream.read(block_size)

        while len(chunk) > 0:
            hasher.update(chunk)
            length += len(chunk)
            chunk = stream.read(block_size)

    md5_binary = hasher.digest()
    md5_string = b64encode(md5_binary).decode('utf-8')

    return md5_string, str(length)


class Uploader(object):
    def __init__(self, user, package):
        self.package = package
        self.user = user

    @property
    def payload(self):
        return {
            'metadata': {
                'owner': self.user.profile['idhash'],
                'name': self.package.metadata['name']
            },
            'filedata': list(self._datafile_info)
        }

    @property
    def _datafile_info(self):
        for resource in self.package.metadata['resources']:
            filepath = join(self.package.base_path, resource['path'])
            md5_hash, length = _get_datafile_stats(filepath)

            yield {
                resource['path']: {
                    'length': length,
                    'md5': md5_hash,
                    'type': "text/csv",
                    'name': resource['name']
                }
            }

    def request_upload(self):
        token = self.user.permissions['os.datastore']
        return API.request_upload(jwt=token)
