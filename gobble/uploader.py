""" Upload to Open-Spending"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

from base64 import b64encode
from hashlib import md5
from os.path import join
from io import open


class Uploader(object):
    def __init__(self, user, package):
        self.package = package
        self.user = user
        self.base_path = package.base_path

    @property
    def payload(self):
            return {
                'metadata': {
                    'owner': self.user.profile['idhash'],
                    'name': str(self.user)
                },
                'filedata': list(self._filedata_specs)
            }

    @property
    def _filedata_specs(self):
        for resource in self.package.metadata['resources']:
            relative_filepath = resource['path']
            md5_hash, length = self._get_data_stats(relative_filepath)

            yield {
                join(self.package.base_path, relative_filepath): {
                    resource['name']: {
                        'length': length,
                        'md5': md5_hash,
                        'type': "text/csv",
                        'name': resource['path']
                    }
                }
            }

    def _get_data_stats(self, relative_filepath, block_size=65536):
        """Get stats on a file via iteration over its contents"""

        hasher = md5()
        length = 0

        filepath = join(self.base_path, relative_filepath)

        with open(filepath, mode='rb') as stream:
            chunk = stream.read(block_size)
            while len(chunk) > 0:
                hasher.update(chunk)
                length += len(chunk)
                chunk = stream.read(block_size)

        md5_binary = hasher.digest()
        md5_string = b64encode(md5_binary).decode('utf-8')

        return md5_string, str(length)
