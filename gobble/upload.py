""" This modules uploads data-packages to the Open-Spending datastore"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io

from base64 import b64encode
from hashlib import md5
from os.path import getsize, join, basename
from time import sleep
from datapackage import DataPackage
from datapackage.exceptions import ValidationError
from future import standard_library
from requests import HTTPError
from requests_futures.sessions import FuturesSession

from gobble.configuration import settings
from gobble.logger import log
from gobble.user import user
from gobble.api import (handle, upload_package, request_upload,
                        toggle_publish, upload_status)

standard_library.install_aliases()


HASHING_BLOCK_SIZE = 65536
OS_DATA_FORMATS = ['csv']
POLL_PERIOD = 5


token = user.permissions['os.datastore']['token']
owner_id = user.authentication['profile']['idhash']


def upload_datapackage(filepath, publish=True):
    """Upload a datapackage to the Open-Spending datastore.

    :param publish: toggle the datapackage to "published" after upload

    :param filepath: can be `dict`, `str` or file-like object (see the docs
           for the `datapackage.DataPackage` class)
    """
    batch = Batch(filepath)

    for target in batch.request_s3_urls():
        promise = batch.push_to_s3(*target)
        batch.handle_promise(*promise)

    batch.insert_into_postgres()

    while batch.in_progress:
        sleep(POLL_PERIOD)

    log.info('Congratuations, %s was uploaded successfully!', batch)

    if publish:
        toggle_public_access(batch.name)


def toggle_public_access(package_name, public=True):
    to_state = 'public' if public else 'private'

    toggle = str(public).lower()
    package_id = owner_id + ':' + package_name
    query = dict(jwt=token, id=package_id, publish=toggle)
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


def compute_hash(filepath):
    """Return the md5 hash of a file"""
    hasher = md5()

    with io.open(filepath, 'rb') as stream:
        chunk = stream.read(HASHING_BLOCK_SIZE)
        while len(chunk) > 0:
            hasher.update(chunk)
            chunk = stream.read(HASHING_BLOCK_SIZE)

    md5_binary = hasher.digest()
    md5_bytes = b64encode(md5_binary)
    md5_unicode = md5_bytes.decode('utf-8')

    return md5_unicode


class Batch(DataPackage):
    """This class uploads a datdpackage to the datastore."""

    def __init__(self, filepath):
        super(Batch, self).__init__(filepath, schema='fiscal')

        self.validate()
        self.check_file_formats()

        self.responses = []
        self._session = FuturesSession()
        self.name = self.descriptor['name']
        self.path = basename(filepath)
        self.filepath = filepath

        log.info('Starting uploading process for %s', self)

    def check_file_formats(self):
        for resource in self:
            if resource.descriptor['mediatype'] != 'text/csv':
                message = 'Usupported format: %s, valid formats are %s'
                raise NotImplemented(message, resource.path, OS_DATA_FORMATS)

    @property
    def files(self):
        filedata = {
            resource.descriptor['path']: {
                'name': resource.descriptor['name'],
                'length': getsize(resource.local_data_path),
                'md5': compute_hash(resource.local_data_path),
                'type': resource.descriptor['mediatype'],
            } for resource in self
        }
        descriptor_file = {
            basename(self.filepath): {
                'name': self.name,
                'length': getsize(self.filepath),
                'md5': compute_hash(self.filepath),
                'type': 'text/json',
            }
        }
        filedata.update(descriptor_file)
        return {
            'filedata': filedata,
            'metadata': {
                'owner': owner_id,
                'name': self.name
            }
        }

    def get_header(self, path):
        """The request header for the upload.
        """
        filepath = join(self.base_path, path)
        return {
            'Content-Length': getsize(filepath),
            'Content-MD5': compute_hash(filepath)
        }

    @property
    def package_url(self):
        return join(settings.S3_BUCKET_URL, owner_id, self.name, self.path)

    def request_s3_urls(self):
        """S3 urls for uploading datafiles"""

        response = request_upload(params=dict(jwt=token), json=self.files)
        files = handle(response)['filedata']

        for path, info in files.items():
            query = {k: v[0] for k, v in info['upload_query'].items()}
            message = '%s is ready for upload to %s'
            log.info(message, path, info['upload_url'])

            yield info['upload_url'], path, query, self.get_header(path)

    def push_to_s3(self, url, path, headers, query):
        """Send data files for upload to the S3 bucket.
        """
        log.debug('Started uploading %s to %s', path, url)

        absolute_path = join(self.base_path, path)
        stream = io.open(absolute_path, mode='rb')
        future = self._session.put(url,
                                   headers=headers,
                                   data=stream,
                                   params=query,
                                   background_callback=self._s3_callback)

        return [future, stream]

    @staticmethod
    def _s3_callback(_, response):
        """Report a succesfully S3 upload or fail.
        """
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
        """Transfer datafiles from S3 into the postgres datastore.
        """
        query = dict(jwt=token, datapackage=self.package_url)
        response = upload_package(params=query)
        return handle(response)

    @property
    def in_progress(self):
        """Return true when the upload status is 'done'.
        """
        query = dict(datapackage=self.package_url)
        answer = upload_status(params=query).json()
        args = self, answer['status'], answer['progress'], len(self)
        log.debug('%s is loading (%s) %s/%s', *args)

        return answer['status'] != 'done'

    def __len__(self):
        return len(self.resources)

    def __repr__(self):
        return '<Batch [%s files]: %s>' % (len(self), self.name)

    def __str__(self):
        return self.name

    def __iter__(self):
        for datafile in self.resources:
            yield datafile

    def __getitem__(self, index):
        return self.resources[index]
