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

from gobble.config import settings
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


def push(target, publish=False):
    """Upload a fiscal datapackage to Open-Spending.

    The target is the full path to the fiscal datapackage JSON descriptor,
    but it can also be a dictionary representing the schema itself or a url
    pointing to a descriptor (for more information please refer to the
    documentation for the :class:`datapackage.DataPackage` class.

    By default, newly uploaded packages are kept private, but you can change
    that. Also note that if you upload a datapackage twice, the first one will
    be overwritten. For now, the only valid datafile format is CSV.

    :param publish: toggle the datapackage to "published" after upload
    :param target: absolute path to package descriptor or url or schema
    """
    batch = Batch(target)

    for target in batch.request_s3_urls():
        batch.push_to_s3(*target)

    batch.handle_promises()
    batch.insert_into_datastore()

    while batch.in_progress:
        sleep(POLL_PERIOD)

    if publish:
        toggle(batch.name)

    return batch


class ToggleError(Exception):
    pass


def toggle(package_name, public=True):
    """Toggle public access to a fiscal datapackage

    Change the status of a fiscal data package from public to private or
    vice-versa. If something went wrong, whilst changing the status, you will
    get a :class:`upload.ToggleError`.

    :param package_name: the unique name of the datapackage
    :param public: whether the package should be public or private
    :return: the new state of the package, i.e. "public" or "private"
    """
    to_state = 'public' if public else 'private'

    publish = str(public).lower()
    package_id = owner_id + ':' + package_name
    query = dict(jwt=token, id=package_id, publish=publish)

    answer = handle(toggle_publish(params=query))

    if not answer['success']:
        message = 'Unable to toggle datapackage to %s'
        raise ToggleError(message, to_state)

    log.info('%s is now %s', package_id, to_state)
    return to_state


def validate(target, raise_error=True, schema='fiscal'):
    """Validate a datapackage schema.

    :param target: A valid datapackage target (`datapackage.DataPackage`).
    :param raise_error: raise a `datapackage.Validation` error if invalid
    :param schema: the schema to validate against:

    :return By default, return true if the package is valid, else return
            a list of error messages. If the `raise_error` flag is True,
            however, raise a `datapackage.exceptions.ValidatioError`.

    """
    package = DataPackage(target, schema=schema)
    name = package.descriptor.get('name') or 'datapackage'

    try:
        package.validate()
        log.info('%s is a valid datapackage', name)
        return True

    except ValidationError:
        messages = []

        for error in package.iter_errors():
            messages.append(error.message)
            log.warn('Validation error: %s', error.message)

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
    """This class uploads a datapackage to Open-Spending.

    It does this in 3 steps:
        * request urls for AWS S3 storage
        * upload all files to the owner's S3 bucket
        * insert the data into the Open-Spending datastore (PostgreSQL)

    This class is a subclass of the :class:`datapackage.DataPackage` class.
    The constructor takes the same arguments as its parent class, except that
    the default schema is "fiscal".
    """

    def __init__(self, target, schema='fiscal', **kwargs):
        super(Batch, self).__init__(target, schema=schema, **kwargs)

        validate(target)
        self._check_file_formats()

        self.streams = []
        self._session = FuturesSession()
        self.futures = []
        self.responses = []

        self.name = self.descriptor['name']
        self.path = basename(target)
        self.filepath = target

        log.info('Starting uploading process for %s', self)

    def _check_file_formats(self):
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

    def _get_header(self, path):
        filepath = join(self.base_path, path)
        return {'Content-Length': getsize(filepath),
                'Content-MD5': compute_hash(filepath)}

    @property
    def _descriptor_s3_url(self):
        return join(settings.S3_BUCKET_URL, owner_id, self.name, self.path)

    def request_s3_urls(self):
        """Request AWS S3 upload urls for all files.

        :return : a generator of tuples: (url, realtive path, query, header)
                  for the method `push_to_s3` to iterate on.
        """

        response = request_upload(params=dict(jwt=token), json=self.files)
        files = handle(response)['filedata']

        for path, info in files.items():
            message = '%s is ready for upload to %s'
            log.info(message, path, info['upload_url'])
            query = {k: v[0] for k, v in info['upload_query'].items()}
            yield info['upload_url'], path, query, self._get_header(path)

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

        self.streams.append(stream)
        self.futures.append(future)

    @staticmethod
    def _s3_callback(_, response):
        handle(response)
        log.info('Successful S3 upload: %s', response.url)

    def handle_promises(self):
        """Collect all promises from S3 uploads.
        """
        for stream, future in zip(self.streams, self.futures):
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

    def insert_into_datastore(self):
        """Transfer datafiles from S3 into the postgres datastore.

        :return: the url of the fiscal datapackage on Open-Spending
        """
        query = dict(jwt=token, datapackage=self._descriptor_s3_url)
        response = upload_package(params=query)
        handle(response)

        log.info('Congratuations, %s was uploaded successfully!', self)
        log.info('You can find you fiscal datapackage here: %s', self.os_url)

        return self.os_url

    @property
    def os_url(self):
        return join(settings.OS_URL, owner_id + ':' + self.name)

    @property
    def in_progress(self):
        """Return true when the upload finished."""

        query = dict(datapackage=self._descriptor_s3_url)
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
