""" This modules uploads data-packages to the Open-Spending datastore"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import sys

from base64 import b64encode
from hashlib import md5
from io import StringIO
from os.path import getsize, join, basename, isfile
from time import sleep
from json import dumps
from datapackage import DataPackage
from datapackage.exceptions import ValidationError
from future import standard_library
from gobble.user import User
from goodtables.pipeline import Pipeline
from requests import HTTPError
from requests_futures.sessions import FuturesSession

from gobble.config import settings
from gobble.logger import log
from gobble.api import (handle,
                        upload_package,
                        request_upload,
                        toggle_publish,
                        upload_status)

standard_library.install_aliases()


HASHING_BLOCK_SIZE = 65536
OS_DATA_FORMATS = ['.csv']
POLL_PERIOD = 5
REPORT_FILENAME = 'goodtables.report.json'


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
    :param user: a `gobble.user.user` object.
    """

    def __init__(self, filepath, user=None, **kw):
        if not isfile(filepath):
            raise NotImplemented('%s is not a local path', filepath)

        super(FiscalDataPackage, self).__init__(filepath,
                                                schema='fiscal', **kw)
        self._check_file_formats()

        self._streams = []
        self._session = FuturesSession()
        self._futures = []
        self._responses = []

        self.user = user
        self.name = self.descriptor.get('name')
        self.path = basename(filepath)
        self.filepath = filepath

    def validate(self, raise_on_error=True, schema_only=False):
        """Validate a datapackage schema.

        By default, only the data-package schema is validated. To validate the
        data files too, set the `data` flag to `True`. The method fails if an
        error is found, unless the `raise_error` flag is explicitely set to
        `False`.

        :param raise_on_error: raise error on failure or not (default: True)
        :param schema_only: only validate the schema (default: True)
        :raise: :class:`ValidationError` if the schema is invalid

        :return A list of error messages or an empty list.
        """
        messages = []

        if raise_on_error:
            super(FiscalDataPackage, self).validate()
        else:
            try:
                super(FiscalDataPackage, self).validate()
                message = '%s (%s) is a valid fiscal data-package schema'
                log.info(message, self.path, self)

            except ValidationError:
                for error in self.iter_errors():
                    message = 'SCHEMA ERROR in %s: %s'
                    args = self.path, error.message
                    messages.append(message % args)
                    log.warn(message, *args)

        if messages:
            messages.append('Aborting data validation due to invalid schema')
            return messages

        if not schema_only:
            return self._validate_data(raise_on_error)
        else:
            return messages

    def upload(self, publish=True, skip_validation=False):
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

        :param skip_validation: use only if you have already done so
        :param publish: toggle the datapackage to "published" after upload
        """
        self.descriptor['author'] = self.user.name
        self.descriptor['owner'] = self.user.id

        with io.open(self.filepath, 'w') as descriptor:
            descriptor.write(self.to_json())

        if not skip_validation:
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
        return join(settings.OS_URL, self.user.id + ':' + self.name)

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
        package_id = self.user.id + ':' + self.name
        query = dict(
            jwt=self.user.permissions['os.datastore']['token'],
            id=package_id,
            publish=publish
        )
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

    def _validate_data(self, raise_on_error):
        """Validate the package resources with GoodTables."""

        def summarize(feedback_, path_):
            intro = 'GoodTables has detected some errors in %s.' % path_
            hint = 'Please check out the full report: %s.' % REPORT_FILENAME

            info = feedback_['meta']
            summary = (
                'There are {bad_rows} (out of {total_rows}) bad rows '
                'and {bad_cols} (out of {total_cols}) bad columns. '
            ).format(
                bad_rows=info['bad_row_count'],
                total_rows=info['row_count'],
                bad_cols=info['bad_column_count'],
                total_cols=len(info['columns'])
            )

            log.debug(intro + summary)
            return [intro, summary, hint]

        for resource in self:
            schema = resource.descriptor['schema']
            path = resource.descriptor['path']
            filepath = join(self._base_path, path)

            pipeline = Pipeline(filepath, report_stream=StringIO())
            pipeline.register_processor('schema', options={'schema': schema})
            is_valid, report = pipeline.run()

            if is_valid:
                return []

            if raise_on_error:
                raise ValidationError('%s is invalid' % filepath)
            else:
                feedback = report.generate()
                with open(REPORT_FILENAME, 'w+') as json:
                    json.write(dumps(feedback, indent=4, ensure_ascii=False))
                return summarize(feedback, path)

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
                'type': 'application/octet-stream',
            }
        }
        filedata.update(descriptor_file)
        return {
            'filedata': filedata,
            'metadata': {
                'owner': self.user.id,
                'name': self.name
            }
        }

    @property
    def bytes(self):
        return sum([file['length']
                    for file in self.filedata['filedata'].values()])

    def _get_header(self, path, content_type):
        filepath = join(self.base_path, path)
        return {'Content-Length': str(getsize(filepath)),
                'Content-MD5': compute_hash(filepath),
                'Content-Type': content_type}

    @property
    def _descriptor_s3_url(self):
        return join(settings.S3_BUCKET_URL, self.user.id, self.name, self.path)

    def _request_s3_upload(self):
        """Request AWS S3 upload urls for all files.
        """
        response = request_upload(
            params=dict(jwt=self.user.permissions['os.datastore']['token']),
            json=self.filedata
        )
        files = handle(response)['filedata']

        for path, info in files.items():
            message = '%s is ready for upload to %s'
            log.info(message, path, info['upload_url'])
            query = {k: v[0] for k, v in info['upload_query'].items()}
            yield (info['upload_url'],
                   path,
                   query,
                   self._get_header(path, info['type']))

    def _push_to_s3(self, url, path, query, headers):
        """Send data files for upload to the S3 bucket.
        """

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
        query = {
            'jwt': self.user.permissions['os.datastore']['token'],
            'datapackage': self._descriptor_s3_url
        }
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
    user_ = User()
    filepath_ = sys.argv[1]
    package_ = FiscalDataPackage(filepath_, user=user_)
    package_.upload(publish=True)
