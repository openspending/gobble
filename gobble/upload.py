""" This modules uploads data-packages to the Open-Spending datastore"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import io

from datapackage import DataPackage
from datapackage.exceptions import DataPackageException
from future import standard_library
from petl import fromcsv
from pip.utils import cached_property
from requests_futures.sessions import FuturesSession
from os.path import getsize, join
from base64 import b64encode
from hashlib import md5

from gobble.api import upload_package, request_upload
from gobble.configuration import settings, OS_DATA_FORMATS
from gobble.logger import log
from gobble.utilities import gob
from gobble.user import User

standard_library.install_aliases()


class DataFile(object):
    """A wrapper around the datapackage Resource class.

    The class computes the md5 hash of the datafile and exposes the
    info required to request an upload to S3. As a bonus it provides
    a PETL Table object with handy diagnostic and viewing capabilities.
    """
    block_size = settings.HASHING_BLOCK_SIZE

    def __init__(self, resource):
        self._descriptor = resource.descriptor
        self._stream = None

        self.absolute_path = resource.local_data_path
        self.format = self._descriptor['format']
        self.path = self._descriptor['path']
        self.name = self._descriptor['name']
        self.mediatype = self._descriptor['mediatype']

        if self.format not in OS_DATA_FORMATS:
            msg = 'Gobble does yet support %s'
            raise NotImplemented(msg % self.format)
        if resource.remote_data_path:
            msg = 'Gooble does not support remote data files'
            raise NotImplemented(msg)

        log.debug('Hashed %s', self.info)

    @property
    def hash(self):
        hasher = md5()

        with io.open(self.absolute_path, 'rb') as stream:
            chunk = stream.read(self.block_size)
            while len(chunk) > 0:
                hasher.update(chunk)
                chunk = stream.read(self.block_size)

        md5_binary = hasher.digest()
        md5_bytes = b64encode(md5_binary)
        md5_unicode = md5_bytes.decode('utf-8')

        return md5_unicode

    @property
    def bytes(self):
        # Sanity check for people who fiddle with files and descriptors
        if self._descriptor['bytes'] != getsize(self.absolute_path):
            msg = 'Specs does not match file contents: %s'
            raise DataPackageException(msg % self._descriptor)
        else:
            return self._descriptor['bytes']

    @cached_property
    def table(self):
        """A PETL Table object (http://petl.readthedocs.io)

        This object is especially useful in the python shell
        and the notebook: it has nide tabular text and html
        representation built in. Just type the name of the variable
        to show the table. It also has nifty tools to inspect the data.
        """
        # PETL supports other common formarts if needed
        return fromcsv(self.absolute_path)

    @property
    def header(self):
        """The request header for the upload"""
        return {
            'Content-Length': self.bytes,
            'Content-MD5': self.hash
        }

    @property
    def info(self):
        """The fields required to obtain an upload url"""
        return {
            'name': self.name,
            'length': self.bytes,
            'md5': self.hash,
            'type': self.mediatype,
        }

    def __str__(self):
        return self.path

    def __repr__(self):
        params = {'path': str(self), 'size': self.bytes}
        return '<DataFile [{size} bytes]: {path}>'.format(**params)


class Batch(object):
    """This class prepares a data-package for upload"""

    def __init__(self, package, user):
        # Fail if the package is not valid
        package.validate()

        self.package = package
        self.user = user

        self.name = package.descriptor['name']
        self.token = user.permissions['os.datastore']['token']
        self.owner_id = user.profile['idhash']

        self.s3_targets = {}
        self.resources = []

        self.urls = []
        self.queries = []
        self.paths = []  # relative
        self.infos = []
        self.headers = []
        self.names = []

        self._collect_datafiles()

    @property
    def payload(self):
        return {
            'filedata': {file: info for file, info
                         in zip(self.paths, self.infos)},
            'metadata': {
                'owner': self.owner_id,
                'name': str(self)
            }
        }

    def get_upload_details(self):
        """Yield the information needed to upload a file to S3"""

        details = zip(self.paths, self.urls, self.queries, self.headers)
        for path, url, query, header in details:
            yield path, url, query, header

    def _collect_datafiles(self):
        """Collect and hash the data files of a data-package"""

        for resource in self.package.resources:
            resource = DataFile(resource)
            self.resources.append(resource)
            self.infos.append(resource.info)
            self.paths.append(resource.absolute_path)
            self.headers.append(resource.header)
            self.names.append(resource.name)

            log.debug('Ingested %s into %s', resource, self.name)

    def request_s3_upload(self):
        """Obtain upload urls for data files"""

        query = dict(jwt=self.token)
        response = request_upload(params=query, json=self.payload)
        s3_targets = gob(response)['filedata']
        self._unwrap_s3_targets(s3_targets)

        message = '%s is ready for upload: %s'
        log.debug(message, self, self.paths)

        return s3_targets

    def _unwrap_s3_targets(self, s3_targets):
        for i in range(len(self)):
            file = self.paths[i]
            params = s3_targets[file]['upload_query']
            self.queries.append({k: v[0] for k, v in params.items()})
            self.urls.append(s3_targets[file]['upload_url'])

    def __len__(self):
        return len(self.resources)

    def __repr__(self):
        return '<Batch [%s files]: %s>' % (len(self), self.name)

    def __str__(self):
        return '%s (%s files)' % (self.name, len(self))

    def __getitem__(self, index):
        return self.resources[index]

    def __iter__(self):
        for resource in self.resources:
            yield resource

    def __contains__(self, item):
        return True if item in self.paths else False


class S3Bucket(object):
    def __init__(self, batch):
        self.session = FuturesSession()
        self.batch = batch
        self.payload = None
        self.futures = []
        self.responses = []
        self.streams = []
        self.exceptions = None
        self.permission = {
            'datapackage': self.bucket_url,
            'jwt': self.batch.token
        }
        # We have to dissect the url of the 1st datafile
        self.bucket_url = '/'.join(self.batch.urls[0].split('/')[:5])

    def start_uploads(self):
        """Queue data files for upload to the S3 bucket
        """
        for path, url, query, headers in self.batch.get_upload_details():
            log.debug('Started uploading %s to %s', path, url)

            absolute_path = join(self.batch.package.base_path, path)
            stream = io.open(absolute_path, mode='rb')
            future = self.session.put(
                url,
                headers=headers,
                data=stream,
                params=query,
                background_callback=self._notify_s3_success
            )

            self.streams.append(stream)
            self.futures.append(future)

    def collect_s3_results(self):
        for i, future in enumerate(self.futures):
            exception = future.exception()
            if exception:
                raise exception
            response = future.result()
            self.responses.append(response)

    @staticmethod
    def _notify_s3_success(_, response):
        return gob(response)

    def _close_file_streams(self):
        for stream in self.streams:
            stream.close()
        return True

    def load_to_postgres(self):
        """Load a datapackage into the postgres datastore
        """
        response = upload_package(params=self.permission)
        return gob(response)

    def __repr__(self):
        return self.batch.__repr__().replace('Batch', 'S3Bucket')

    def __str__(self):
        return self.batch.__str__().replace('Batch', 'S3Bucket')

    def poll(self):
        """Check the upload status of a datapackage
        """
        response = upload_package(params=self.permission)
        return gob(response)

if __name__ == '__main__':
    u = User()
    dp = DataPackage('/home/loic/repos/gobble/assets/'
                     'datapackages/datapackage.1.json')
    b = Batch(dp, u)
    b.request_s3_upload()

    s3 = S3Bucket(b)
    s3.start_uploads()
