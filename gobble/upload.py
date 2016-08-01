""" This modules uploads data-packages to the Open-Spending datastore"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
from base64 import b64encode
from hashlib import md5
from os.path import getsize, join
from sys import stdout
from time import sleep

from datapackage import DataPackage
from datapackage.exceptions import DataPackageException, ValidationError
from future import standard_library
from petl import fromcsv
from pip.utils import cached_property
from requests import HTTPError
from requests_futures.sessions import FuturesSession

from gobble.api import (handle, upload_package, request_upload,
                        toggle_publish, upload_status)
from gobble.logger import log
from gobble.user import User

standard_library.install_aliases()


OS_DATA_FORMATS = ['csv']
user = User()


def upload_datapackage(filepath, publish=True):
    """Upload a datapackage to the Open-Spending datastore.

    :param publish: toggle the datapackage to "published" after upload

    :param filepath: can be `dict`, `str` or file-like object (see the docs
           for the `datapackage.DataPackage` class)
    """
    package = DataPackage(filepath)
    batch = Batch(package)

    batch.collect_datafiles()

    for target in batch.request_s3_targets():
        promise = batch.push_to_s3(*target)
        batch.handle_promise(*promise)

    batch.insert_into_postgres()

    while batch.in_progress:
        sleep(10)

    log.info('Congratuations, %s was uploaded successfully!', batch)

    if publish:
        toggle_public_access(batch.name)


def toggle_public_access(package_id, public=True):
    to_state = 'public' if public else 'private'

    token = user.permissions['os.datastore']
    query = dict(jwt=token, id=package_id, public=public)
    answer = handle(toggle_publish(params=query))

    if not answer['success']:
        raise ValueError('Unable to toggle datapackage to %s', to_state)

    log.info('%s is now %s', package_id, to_state)
    return to_state


def check_datapackage_schema(filepath, raise_error=True):
    """Validate a datapackage.

    :param filepath: can be `dict`, `str` or file-like object (see the docs
           for the `datapackage.DataPackage` class)

    :param raise_error: a 'bool' flag

    :return By default, return true if the package is valid, else return
            a list of error messages. If the `raise_error` flag is True,
            however, raise a `datapackage.exceptions.ValidatioError`.

    """
    package = DataPackage(filepath)
    name = package.descriptor.get('name') or 'datapackage'

    try:
        package.validate()
        log.info('%s is a valid datapackage', name)
        return True

    except ValidationError:
        messages = []

        for error in package.iter_errors():
            messages.append(error.message)

        log.warn('%s has ERRORS!' % name)
        for message in messages:
            log.warn(message)
        log.warn('end of errors')

        if raise_error:
            message = 'Cannot upload %s because it has %s errors'
            raise ValidationError(message % (name, len(messages)))
        else:
            return messages


class OSResource(object):
    """A wrapper around the datapackage Resource class.

    The class computes the md5 hash of the datafile and exposes the
    info required to request an upload to S3. As a bonus it provides
    a PETL Table object with handy diagnostic and viewing capabilities.
    """
    HASHING_BLOCK_SIZE = 65536

    # TODO: subclass the `datapackage.Resource` class
    # TODO: Run the resource through Goodtables ?

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
            chunk = stream.read(self.HASHING_BLOCK_SIZE)
            while len(chunk) > 0:
                hasher.update(chunk)
                chunk = stream.read(self.HASHING_BLOCK_SIZE)

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
        return '<OSResource [{size} bytes]: {path}>'.format(**params)

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


class Batch(object):
    """This class uploads a datdpackage to the datastore."""

    # TODO: subclass the `datapackage.DataPackage` class

    def __init__(self, package):
        # Fail if the package is not valid
        package.validate()

        self._package = package
        self.package_url = None
        self.datafiles = []
        self._session = FuturesSession()
        self.responses = []

        self.name = package.descriptor['name']
        self.token = user.permissions['os.datastore']['token']
        self.owner_id = user.authentication['profile']['idhash']

        log.info('Starting uploading process for %s', self)

    @property
    def payload(self):
        return {
            'filedata': {datafile.path: datafile.info
                         for datafile in self.datafiles},
            'metadata': {
                'owner': self.owner_id,
                'name': self.name
            }
        }

    def request_s3_targets(self):
        """S3 urls for uploading datafiles"""

        query = dict(jwt=self.token)
        response = request_upload(params=query, json=self.payload)
        json = handle(response)['filedata']

        for resource in self:
            params = json[resource.path]['upload_query']
            query = {k: v[0] for k, v in params.items()}
            url = json[resource.path]['upload_url']

            message = '%s is ready for upload: %s'
            log.info(message, resource, url)

            # I see no way other than dissecting a datafile url
            self.package_url = self._extract_package_url(url)

            yield url, resource.path, query, resource.header

    @staticmethod
    def _extract_package_url(url):
        return '/'.join(url.split('/')[:6])

    def collect_datafiles(self):
        """Collect all the datafiles belonging to the batch"""

        for resource in self._package.resources:
            datafile = OSResource(resource)
            log.debug('Ingested %s into %s', datafile, self.name)
            self.datafiles.append(datafile)

    def push_to_s3(self, url, path, headers, query):
        """Send data files for upload to the S3 bucket
        """
        log.debug('Started uploading %s to %s', path, url)

        absolute_path = join(self._package.base_path, path)
        stream = io.open(absolute_path, mode='rb')
        future = self._session.put(url,
                                   headers=headers,
                                   data=stream,
                                   params=query,
                                   background_callback=self._s3_callback)

        return [future, stream]

    @staticmethod
    def _s3_callback(_, response):
        """Report a succesfully S3 upload or fail """
        # Will raise an HTTPError if 400 < code < 599:
        handle(response)
        log.info('Successful S3 upload: %s', response.url)

    def handle_promise(self, future, stream):
        """Collect a promise from S3 uploads
        """
        exception = future.exception()
        if exception:
            raise exception

        response = future.result()

        if response.status_code != 200:
            message = 'Something went wrong uploading %s to S3: %s'
            log.error(message, response.url, response.text)
            raise HTTPError(message)

        self.responses.append(response)
        stream.close()

    def insert_into_postgres(self):
        """Upload datafiles into the postgres datastore
        """
        query = dict(jwt=self.token, datapackage=self.package_url)
        response = upload_package(params=query)
        return handle(response)

    @property
    def in_progress(self):
        query = dict(datapackage=self.package_url)
        response = upload_status(params=query).json()

        if response.status_code == 404:
            message = response['error']
            answer = False
        else:
            message = 'status'
            answer = True if response['progress'] == len(self) else False

        stdout.flush()
        args = message, response['progress'], len(self)
        stdout.write('Loading (%s) %s/%s', *args)

        return answer

    def __len__(self):
        return len(self.datafiles)

    def __repr__(self):
        return '<Batch [%s files]: %s>' % (len(self), self.name)

    def __str__(self):
        return self.name

    def __iter__(self):
        for datafile in self.datafiles:
            yield datafile

    def __getitem__(self, index):
        return self.datafiles[index]


if __name__ == '__main__':
    upload_datapackage('/home/loic/repos/gobble/assets/datapackage/datapackage.json')
