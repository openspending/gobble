""" This modules uploads data-packages to the Open-Spending datastore"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io

from base64 import b64encode
from hashlib import md5
from os.path import getsize, join, basename, isfile
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


class ToggleError(Exception):
    pass


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


class FiscalDataPackage(DataPackage):
    """This class represents a fiscal data package.

    The class is a subclass of the :class:`datapackage.DataPackage` class.
    The constructor takes the same arguments as its parent class, except that
    the schema is "fiscal".

    :param target: The target is the full path to the fiscal datapackage JSON
    descriptor, but it can also be a dictionary representing the schema itself
    or a url pointing to a descriptor (for more information please refer to the
    documentation for the :class:`datapackage.DataPackage` class.
    """

    def __init__(self, filepath, **kw):
        if not isfile(filepath):
            raise NotImplemented('%s is not a local path', filepath)

        super(FiscalDataPackage, self).__init__(filepath,
                                                schema='fiscal', **kw)
        self._check_file_formats()

        self._streams = []
        self._session = FuturesSession()
        self._futures = []
        self._responses = []

        self.name = self.descriptor.get('name')
        self.path = basename(filepath)
        self.filepath = filepath

    def validate(self, raise_error=True):
        """Validate a datapackage schema.

        :param raise_error: raise error on failure or not (default: True)
        :raise: :class:`ValidationError` if the schema is invalid
        :return True or a list of error messages (if `raise_error` is False).
        """
        if raise_error:
            super(FiscalDataPackage, self).validate()

        else:
            try:
                super(FiscalDataPackage, self).validate()
                log.info('%s is a valid datapackage', self.name)
                return True

            except ValidationError:
                messages = []

                for error in self.iter_errors():
                    messages.append(error.message)
                    log.warn('ValidationError: %s', error.message)

                return messages

    def upload(self, publish=False):
        """Upload a fiscal datapackage to Open-Spending.

        It does this in 3 steps:
            * request upload urls for AWS S3 storage
            * upload all files to the owner's S3 bucket
            * insert the data into the Open-Spending datastore (PostgreSQL)

        By default, newly uploaded packages are kept private, but you can
        change that with the `publish` flag. Also note that if you upload the
        same fiscal data package again, the previous version will be
        overwritten.

        For now, the only valid datafile format is CSV.

        :param publish: toggle the datapackage to "published" after upload
        """
        self.validate()
        log.info('Starting uploading process for %s', self)

        for s3_target in self._request_s3_upload():
            self._push_to_s3(*s3_target)

        self._handle_promises()
        self._insert_into_datastore()

        while self.in_progress:
            sleep(POLL_PERIOD)

        if publish:
            self.toggle('public')

        return self.url

    @property
    def url(self):
        return join(settings.OS_URL, owner_id + ':' + self.name)

    @property
    def in_progress(self):
        """Return true when the upload finished."""

        query = dict(datapackage=self._descriptor_s3_url)
        answer = upload_status(params=query).json()
        args = self, answer['status'], answer['progress'], len(self)
        log.debug('%s is loading (%s) %s/%s', *args)
        return answer['status'] != 'done'

    def toggle(self, to_state):
        """Toggle public access to a fiscal datapackage

        Change the status of a fiscal data package from public to private or
        vice-versa. If something went wrong, whilst changing the status, you
        will get a :class:`upload.ToggleError`.

        :param to_state: the unique name of the datapackage
        :return: the new state of the package, i.e. "public" or "private"
        """
        publish = True if to_state == 'public' else False
        package_id = owner_id + ':' + self.name
        query = dict(jwt=token, id=package_id, publish=publish)

        answer = handle(toggle_publish(params=query))

        if not answer['success']:
            message = 'Unable to toggle datapackage to %s'
            raise ToggleError(message, to_state)

        log.info('%s is now %s', package_id, to_state)
        return to_state

    def _check_file_formats(self):
        for resource in self:
            if resource.descriptor['mediatype'] != 'text/csv':
                message = 'Usupported format: %s, valid formats are %s'
                raise NotImplemented(message, resource.path, OS_DATA_FORMATS)

    @property
    def filedata(self):
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

    def _request_s3_upload(self):
        """Request AWS S3 upload urls for all files.
        """
        response = request_upload(params=dict(jwt=token), json=self.filedata)
        files = handle(response)['filedata']

        for path, info in files.items():
            message = '%s is ready for upload to %s'
            log.info(message, path, info['upload_url'])
            query = {k: v[0] for k, v in info['upload_query'].items()}
            yield info['upload_url'], path, query, self._get_header(path)

    def _push_to_s3(self, url, path, query, headers):
        """Send data files for upload to the S3 bucket.
        """
        headers.update({'Content-Type': 'application/octet-stream'})

        log.debug('Started uploading %s to %s', path, url)
        log.debug('Headers: %s', headers)
        log.debug('Query parameters: %s', query)

        absolute_path = join(self.base_path, path)
        stream = io.open(absolute_path, mode='rb')
        future = self._session.put(url,
                                   headers=headers,
                                   data=stream,
                                   params=query,
                                   background_callback=self._s3_callback)

        self._streams.append(stream)
        self._futures.append(future)

    @staticmethod
    def _s3_callback(_, response):
        handle(response)
        log.info('Successful S3 upload: %s', response.url)

    def _handle_promises(self):
        """Collect all promises from S3 uploads.
        """
        for stream, future in zip(self._streams, self._futures):
            exception = future.exception()
            if exception:
                raise exception
            response = future.result()

            if response.status_code != 200:
                message = 'Something went wrong uploading %s to S3: %s'
                log.error(message, response.url, response.text)
                raise HTTPError(message)

            self._responses.append(response)
            stream.close()

    def _insert_into_datastore(self):
        """Transfer datafiles from S3 into the postgres datastore.

        :return: the url of the fiscal datapackage on Open-Spending
        """
        query = dict(jwt=token, datapackage=self._descriptor_s3_url)
        response = upload_package(params=query)
        handle(response)

        log.info('Congratuations, %s was uploaded successfully!', self)
        log.info('You can find you fiscal datapackage here: %s', self.url)

        return self.url

    def __len__(self):
        return len(self.resources)

    def __repr__(self):
        return '<FiscalDataPackage [%s files]: %s>' % (len(self), self.name)

    def __str__(self):
        return self.name

    def __iter__(self):
        for resource in self.resources:
            yield resource

    def __getitem__(self, index):
        return self.resources[index]


if __name__ == '__main__':
    package = FiscalDataPackage('/home/loic/repos/gobble/assets/datapackage/datapackage.json')
    package.upload()
