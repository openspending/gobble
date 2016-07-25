""" Upload to Open-Spending"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
from requests_futures.sessions import FuturesSession

standard_library.install_aliases()

from builtins import str
from base64 import b64encode
from hashlib import md5
from os.path import join
import io

from gobble.conductor import API, handle
from gobble.configuration import to_console, config


def _get_datafile_stats(filepath):
    """Get stats on a file via iteration over its contents"""
    block_size = config.DATAFILE_HASHING_BLOCK_SIZE

    hasher = md5()
    length = 0

    with io.open(filepath, mode='rb') as stream:
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
        self.in_shell = user.in_shell
        self.session = FuturesSession()

    @property
    def payload(self):
        return {
            'metadata': {
                'owner': self.user.profile['idhash'],
                'name': self.package.descriptor['name']
            },
            'filedata': dict(self.resources)
        }

    @property
    def resources(self):
        for resource in self.package.descriptor['resources']:
            filepath = join(self.package.base_path, resource['path'])
            md5_hash, length = _get_datafile_stats(filepath)

            resource_info = {
                'length': length,
                'md5': md5_hash,
                'type': "text/csv",
                'name': resource['name']
            }

            yield resource['path'], resource_info

    @to_console
    def prepare(self):
        token = self.user.permissions['os.datastore']['token']
        response = API.request_upload(json=self.payload, jwt=token)
        return handle(response)

    # def upload(self, payload):
    #     """Asyncronously upload a datapackage"""
    #
    #     responses = []
    #     futures = []
    #     files = []
    #
    #     # Start uploading
    #     for path, metadata in payload['filedata'].items():
    #         fullpath = os.path.join(self.path, path)
    #         headers = {
    #             'Content-Length': metadata['length'],
    #             'Content-MD5': metadata['md5'],
    #         }
    #         file = io.open(fullpath, mode='rb')
    #         files.append(file)
    #         future = self.session.put(
    #             metadata['upload_url'],
    #             data=file,
    #             headers=headers,
    #             params=metadata['upload_query'],
    #             background_callback=self.__notify)
    #         futures.append(future)
    #
    #     # Wait uploading
    #     for future in futures:
    #         exception = future.exception()
    #         if exception:
    #             raise exception
    #         response = future.result()
    #         responses.append(response)
    #
    #     # Raise if errors
    #     for response in responses:
    #         if response.status_code != 200:
    #             url = self.__clean_url(response.url)
    #             message = (
    #                 'Something went wrong with "%s" file.\n\n'
    #                 'Here is response we\'ve received:\n\n%s' %
    #                 (url, response.text))
    #             raise RuntimeError(message)
    #
    #     # Close files
    #     for file in files:
    #         file.close()


if __name__ == '__main__':
    from gobble.user import User
    from datapackage import DataPackage
    from tests.fixtures import PACKAGE_FILE

    user_ = User(in_shell=True)
    package_ = DataPackage(PACKAGE_FILE)
    uploader = Uploader(user_, package_)
    uploader.prepare()
